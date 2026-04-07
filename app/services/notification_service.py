from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationSetting, NotificationType
from app.models.product import Product


def create_price_notification(
    db: Session,
    product: Product,
    old_price: int,
    new_price: int,
) -> None:
    change_rate = (new_price - old_price) / old_price * 100 if old_price > 0 else 0

    if abs(change_rate) < 1:
        return

    notification_type = NotificationType.PRICE_SURGE if change_rate > 0 else NotificationType.PRICE_DROP

    # Check partner's notification settings
    setting = db.query(NotificationSetting).filter(
        NotificationSetting.partner_id == product.partner_id,
        NotificationSetting.type == notification_type,
    ).first()

    if setting and not setting.is_enabled:
        return

    threshold = (setting.threshold_percent if setting and setting.threshold_percent else 5)
    if abs(change_rate) < threshold:
        return

    notification = Notification(
        partner_id=product.partner_id,
        type=notification_type,
        title=f"{'시세 상승' if change_rate > 0 else '시세 하락'} 알림",
        message=(
            f"{product.name}의 시세가 {abs(change_rate):.1f}% "
            f"{'상승' if change_rate > 0 else '하락'}했습니다. "
            f"({old_price:,}원 → {new_price:,}원)"
        ),
    )
    db.add(notification)
    db.commit()
