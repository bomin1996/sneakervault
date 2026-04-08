from app.models.notification import Notification, NotificationType


def test_list_notifications_empty(client, partner_headers):
    res = client.get("/api/v1/notifications", headers=partner_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_list_notifications(client, partner_headers, db):
    from app.models.partner import Partner
    partner = db.query(Partner).first()
    notification = Notification(
        partner_id=partner.id,
        type=NotificationType.PRICE_DROP,
        title="시세 하락 알림",
        message="Nike Dunk Low의 시세가 5% 하락했습니다.",
    )
    db.add(notification)
    db.commit()

    res = client.get("/api/v1/notifications", headers=partner_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "시세 하락 알림"


def test_list_notifications_unread_only(client, partner_headers, db):
    from app.models.partner import Partner
    partner = db.query(Partner).first()
    db.add(Notification(partner_id=partner.id, type=NotificationType.SYSTEM, title="Read", message="msg", is_read=True))
    db.add(Notification(partner_id=partner.id, type=NotificationType.SYSTEM, title="Unread", message="msg"))
    db.commit()

    res = client.get("/api/v1/notifications?unread_only=true", headers=partner_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "Unread"


def test_mark_as_read(client, partner_headers, db):
    from app.models.partner import Partner
    partner = db.query(Partner).first()
    notification = Notification(
        partner_id=partner.id, type=NotificationType.SYSTEM, title="Test", message="msg"
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    res = client.post(f"/api/v1/notifications/{notification.id}/read", headers=partner_headers)
    assert res.status_code == 200
    assert res.json()["is_read"] is True


def test_mark_all_as_read(client, partner_headers, db):
    from app.models.partner import Partner
    partner = db.query(Partner).first()
    db.add(Notification(partner_id=partner.id, type=NotificationType.SYSTEM, title="N1", message="msg"))
    db.add(Notification(partner_id=partner.id, type=NotificationType.SYSTEM, title="N2", message="msg"))
    db.commit()

    res = client.post("/api/v1/notifications/read-all", headers=partner_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/notifications?unread_only=true", headers=partner_headers)
    assert len(res.json()) == 0


def test_notification_settings_crud(client, partner_headers):
    res = client.put("/api/v1/notifications/settings", json={
        "type": "price_drop",
        "is_enabled": True,
        "threshold_percent": 10,
    }, headers=partner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "price_drop"
    assert data["threshold_percent"] == 10

    res = client.get("/api/v1/notifications/settings", headers=partner_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1
