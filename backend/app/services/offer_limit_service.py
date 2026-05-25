from datetime import datetime, timedelta, timezone


class OfferLimitResult:
    def __init__(self, allowed: bool, next_allowed_date=None, message: str | None = None):
        self.allowed = allowed
        self.next_allowed_date = next_allowed_date
        self.message = message


class OfferLimitService:
    def check_limit(
        self,
        user_created_at: datetime,
        total_user_offers: int,
        today_user_offers: int,
        last_offer_at: datetime | None,
    ) -> OfferLimitResult:
        now = datetime.now(timezone.utc)
        days_from_registration = (now.date() - user_created_at.date()).days

        if days_from_registration == 0:
            if today_user_offers < 2:
                return OfferLimitResult(allowed=True)

            next_date = now.date() + timedelta(days=1)
            return self._limit_reached(next_date)

        if days_from_registration == 1:
            if today_user_offers < 1:
                return OfferLimitResult(allowed=True)

            next_date = now.date() + timedelta(days=2)
            return self._limit_reached(next_date)

        if last_offer_at is None:
            return OfferLimitResult(allowed=True)

        next_allowed_datetime = last_offer_at + timedelta(days=3)

        if now >= next_allowed_datetime:
            return OfferLimitResult(allowed=True)

        return self._limit_reached(next_allowed_datetime.date())

    def _limit_reached(self, next_date):
        formatted_date = next_date.strftime("%d.%m.%Y")

        return OfferLimitResult(
            allowed=False,
            next_allowed_date=next_date,
            message=(
                "Мы сильно благодарны за активность, но пока не справляемся "
                "обрабатывать такое количество предложений :) "
                f"Направьте Ваше предложение {formatted_date}, пожалуйста"
            ),
        )