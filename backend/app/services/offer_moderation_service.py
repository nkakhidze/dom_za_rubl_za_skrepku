from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.offer import Offer
from app.schemas.offer import AdminOfferModerationUpdateRequest


class OfferModerationService:
    ALLOWED_MODERATION_FIELDS = {
        "moderated_value",
        "public_value",
        "valuation_source",
        "moderation_comment",
        "is_public",
        "public_comment",
        "participant_visible",
        "participant_public_name",
    }

    def __init__(self, db: Session):
        self.db = db

    def moderate_offer(
        self,
        offer_id: UUID,
        request: AdminOfferModerationUpdateRequest,
    ) -> Offer:
        offer = self.db.get(Offer, offer_id)

        if offer is None:
            raise ValueError("Offer not found")

        update_data = request.model_dump(exclude_unset=True)
        allowed_update_data = {
            field_name: field_value
            for field_name, field_value in update_data.items()
            if field_name in self.ALLOWED_MODERATION_FIELDS
        }

        for field_name, field_value in allowed_update_data.items():
            setattr(offer, field_name, field_value)

        self.db.commit()
        self.db.refresh(offer)

        return offer
