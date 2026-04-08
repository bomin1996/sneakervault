import logging
from abc import ABC, abstractmethod

import httpx

from app.tasks.worker import celery_app
from app.config import get_settings
from app.database import SessionLocal
from app.models.product import Product
from app.models.price_history import PriceHistory, PriceSource
from app.models.notification import Notification, NotificationType
from app.services.notification_service import create_price_notification

logger = logging.getLogger(__name__)

PRICE_COLLECT_RETRY_SECONDS = 60
PRICE_COLLECT_BATCH_SIZE = 50
MIN_PRICE_KRW = 1000


class PriceProvider(ABC):
    @abstractmethod
    def fetch_price(self, model_number: str) -> int | None:
        pass


class ExternalAPIPriceProvider(PriceProvider):
    def __init__(self):
        settings = get_settings()
        self.api_url = getattr(settings, "PRICE_API_URL", "")
        self.api_key = getattr(settings, "PRICE_API_KEY", "")

    def fetch_price(self, model_number: str) -> int | None:
        if not self.api_url:
            return None
        try:
            response = httpx.get(
                f"{self.api_url}/prices/{model_number}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("price")
        except (httpx.HTTPError, KeyError, ValueError) as e:
            logger.warning(f"External API failed for {model_number}: {e}")
            return None


def _get_price_provider() -> PriceProvider:
    return ExternalAPIPriceProvider()


@celery_app.task(bind=True, max_retries=3)
def collect_market_prices(self):
    """Collect market prices from external data source."""
    db = SessionLocal()
    provider = _get_price_provider()
    try:
        products = db.query(Product).filter(Product.is_active == True).all()
        updated_count = 0
        skipped_count = 0

        for product in products:
            new_price = provider.fetch_price(product.model_number)

            if new_price is None:
                skipped_count += 1
                continue

            new_price = max(new_price, MIN_PRICE_KRW)

            if new_price == product.current_price:
                continue

            old_price = product.current_price

            history = PriceHistory(
                product_id=product.id,
                price=new_price,
                previous_price=old_price,
                source=PriceSource.CRAWL,
            )
            db.add(history)

            product.current_price = new_price
            updated_count += 1

            create_price_notification(db, product, old_price, new_price)

            if updated_count % PRICE_COLLECT_BATCH_SIZE == 0:
                db.flush()

        db.commit()
        logger.info(
            f"Price collection complete: updated={updated_count}, "
            f"skipped={skipped_count}, total={len(products)}"
        )
        return {"updated": updated_count, "skipped": skipped_count, "total": len(products)}

    except Exception as exc:
        db.rollback()
        logger.error(f"Price collection failed: {exc}")
        raise self.retry(exc=exc, countdown=PRICE_COLLECT_RETRY_SECONDS)
    finally:
        db.close()


@celery_app.task
def generate_daily_price_report():
    """Generate daily price report and notify partners."""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta, timezone

        yesterday = datetime.now(timezone.utc) - timedelta(days=1)

        stats = (
            db.query(
                Product.partner_id,
                func.count(PriceHistory.id).label("changes"),
                func.avg(PriceHistory.price).label("avg_price"),
            )
            .join(PriceHistory, Product.id == PriceHistory.product_id)
            .filter(PriceHistory.recorded_at >= yesterday)
            .group_by(Product.partner_id)
            .all()
        )

        for partner_id, changes, avg_price in stats:
            notification = Notification(
                partner_id=partner_id,
                type=NotificationType.SYSTEM,
                title="일간 시세 리포트",
                message=f"어제 {changes}건의 시세 변동이 있었습니다. 평균 거래가: {int(avg_price):,}원",
            )
            db.add(notification)

        db.commit()
        logger.info(f"Generated daily report for {len(stats)} partners")
        return {"partners_reported": len(stats)}

    except Exception as exc:
        db.rollback()
        logger.error(f"Daily report generation failed: {exc}")
        raise
    finally:
        db.close()
