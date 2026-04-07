import logging
import random

from app.tasks.worker import celery_app
from app.database import SessionLocal
from app.models.product import Product
from app.models.price_history import PriceHistory, PriceSource
from app.services.notification_service import create_price_notification

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def collect_market_prices(self):
    """Collect market prices from external sources.

    In production, this would crawl real market data.
    Here we simulate price fluctuation for demonstration.
    """
    db = SessionLocal()
    try:
        products = db.query(Product).filter(Product.is_active == True).all()
        updated_count = 0

        for product in products:
            # Simulate market price fluctuation (-5% ~ +5%)
            fluctuation = random.uniform(-0.05, 0.05)
            new_price = int(product.current_price * (1 + fluctuation))
            new_price = max(new_price, 1000)  # Minimum price guard

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

            # Trigger notification if significant change
            create_price_notification(db, product, old_price, new_price)

        db.commit()
        logger.info(f"Updated prices for {updated_count}/{len(products)} products")
        return {"updated": updated_count, "total": len(products)}

    except Exception as exc:
        db.rollback()
        logger.error(f"Price collection failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task
def generate_daily_price_report():
    """Generate daily price report for all active partners."""
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

        logger.info(f"Generated daily report for {len(stats)} partners")
        return {"partners_reported": len(stats)}

    finally:
        db.close()
