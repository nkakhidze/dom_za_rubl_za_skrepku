from datetime import datetime, timezone

from app.services.offer_limit_service import OfferLimitService


def test_first_day_allows_three_offers():
    service = OfferLimitService()
    now = datetime.now(timezone.utc)

    result = service.check_limit(
        user_created_at=now,
        total_user_offers=2,
        today_user_offers=2,
        last_offer_at=now,
    )

    assert result.allowed is True


def test_first_day_fourth_offer_returns_user_facing_message():
    service = OfferLimitService()
    now = datetime.now(timezone.utc)

    result = service.check_limit(
        user_created_at=now,
        total_user_offers=3,
        today_user_offers=3,
        last_offer_at=now,
    )

    assert result.allowed is False
    assert result.message is not None
    assert result.message.startswith("Мы сильно благодарны за активность")
    assert "Направьте Ваше предложение" in result.message
