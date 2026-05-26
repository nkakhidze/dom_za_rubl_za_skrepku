import unittest
import uuid

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routers.admin_offers import update_offer_status
from app.api.routers.offers import get_public_offer, get_public_offers
from app.api.routers.users import get_user_offers
from app.db.database import Base
from app.db.models.offer import Offer
from app.db.models.user import User
from app.schemas.offer import (
    AdminOfferModerationUpdateRequest,
    AdminOfferStatusUpdateRequest,
    OfferCreateRequest,
    PublicOfferDetail,
    PublicOfferListItem,
    UserOfferListItem,
)
from app.services.offer_service import OfferService
from app.services.offer_moderation_service import OfferModerationService


class OfferModerationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.testing_session_local = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
        )

        Base.metadata.create_all(self.engine)
        self.db: Session = self.testing_session_local()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def create_offer(
        self,
        title: str = "Vintage chair",
        participant_visible: bool = True,
        participant_public_name: str | None = "Public Participant",
        external_user_id: str | None = None,
    ) -> Offer:
        request = OfferCreateRequest(
            messenger_type="telegram",
            external_user_id=external_user_id or f"user-{title}",
            username="participant",
            first_name="Test",
            last_name="User",
            title=title,
            description="A useful item for the next exchange step.",
            offer_type="physical_item",
            city="Tomsk",
            declared_value=3000,
            photo_urls=["http://127.0.0.1:8000/uploads/images/photo.jpg"],
            exchange_preference="any_offer",
            consent_accepted=True,
            participant_visible=participant_visible,
            participant_public_name=participant_public_name,
        )

        offer = OfferService(self.db).create_offer(request)
        self.assertIsInstance(offer, Offer)
        return offer

    def test_admin_can_moderate_publish_and_update_status(self) -> None:
        offer = self.create_offer()

        moderated_offer = OfferModerationService(self.db).moderate_offer(
            offer.id,
            AdminOfferModerationUpdateRequest(
                moderated_value=2500,
                public_value=2400,
                moderation_comment="Looks realistic after checking similar listings.",
                is_public=True,
                public_comment="Good story and easy to exchange further.",
            ),
        )

        self.assertEqual(moderated_offer.moderated_value, 2500)
        self.assertEqual(moderated_offer.public_value, 2400)
        self.assertEqual(
            moderated_offer.moderation_comment,
            "Looks realistic after checking similar listings.",
        )
        self.assertIs(moderated_offer.is_public, True)

        status_offer = update_offer_status(
            offer.id,
            AdminOfferStatusUpdateRequest(status="shortlisted"),
            self.db,
        )

        self.assertEqual(status_offer.status, "shortlisted")

    def test_public_offers_only_include_allowed_fields_after_publication(self) -> None:
        offer = self.create_offer()

        self.assertEqual(get_public_offers(self.db), [])

        OfferModerationService(self.db).moderate_offer(
            offer.id,
            AdminOfferModerationUpdateRequest(
                moderated_value=2500,
                public_value=2400,
                moderation_comment="Internal note.",
                is_public=True,
                public_comment="Public note.",
            ),
        )

        public_offers = get_public_offers(self.db)
        self.assertEqual(len(public_offers), 1)

        public_offer = PublicOfferListItem.model_validate(public_offers[0]).model_dump(
            mode="json"
        )
        self.assertEqual(public_offer["id"], str(offer.id))
        self.assertEqual(
            public_offer["photo_urls"],
            ["http://127.0.0.1:8000/uploads/images/photo.jpg"],
        )
        self.assertEqual(public_offer["public_value"], 2400)
        self.assertEqual(public_offer["public_comment"], "Public note.")

        forbidden_fields = {
            "user_id",
            "declared_value",
            "moderated_value",
            "valuation_source",
            "moderation_comment",
            "participant_visible",
            "status",
            "consent_accepted",
            "consent_accepted_at",
            "consent_text_version",
            "requires_contract",
            "contract_status",
            "contract_file_key",
        }
        self.assertTrue(forbidden_fields.isdisjoint(public_offer))

        detail = get_public_offer(offer.id, self.db)
        detail_offer = PublicOfferDetail.model_validate(detail).model_dump(mode="json")
        self.assertEqual(detail_offer, public_offer)
        self.assertTrue(forbidden_fields.isdisjoint(detail_offer))

    def test_non_public_offer_detail_returns_404(self) -> None:
        offer = self.create_offer()

        with self.assertRaises(HTTPException) as context:
            get_public_offer(offer.id, self.db)

        self.assertEqual(context.exception.status_code, 404)

    def test_service_keeps_offer_private_when_is_public_is_false(self) -> None:
        offer = self.create_offer()

        moderated_offer = OfferModerationService(self.db).moderate_offer(
            offer.id,
            AdminOfferModerationUpdateRequest(
                moderated_value=2500,
                public_value=2400,
                is_public=False,
            ),
        )

        self.assertEqual(moderated_offer.moderated_value, 2500)
        self.assertEqual(moderated_offer.public_value, 2400)
        self.assertIs(moderated_offer.is_public, False)

        with self.assertRaises(HTTPException) as context:
            get_public_offer(offer.id, self.db)

        self.assertEqual(context.exception.status_code, 404)

    def test_service_raises_for_missing_offer(self) -> None:
        with self.assertRaises(ValueError) as context:
            OfferModerationService(self.db).moderate_offer(
                uuid.uuid4(),
                AdminOfferModerationUpdateRequest(is_public=True),
            )

        self.assertEqual(str(context.exception), "Offer not found")

    def test_service_ignores_fields_not_allowed_for_moderation(self) -> None:
        class UnsafeModerationRequest(BaseModel):
            title: str = "Unexpected title"
            status: str = "completed"
            is_public: bool = True

        offer = self.create_offer(title="Original title")

        moderated_offer = OfferModerationService(self.db).moderate_offer(
            offer.id,
            UnsafeModerationRequest(
                title="Unexpected title",
                status="completed",
                is_public=True,
            ),
        )

        self.assertEqual(moderated_offer.title, "Original title")
        self.assertEqual(moderated_offer.status, "new")
        self.assertIs(moderated_offer.is_public, True)

    def test_public_list_hides_participant_name_when_participant_is_not_visible(
        self,
    ) -> None:
        offer = self.create_offer(
            title="Hidden participant list offer",
            participant_visible=False,
            participant_public_name="Hidden Participant",
        )
        OfferModerationService(self.db).moderate_offer(
            offer.id,
            AdminOfferModerationUpdateRequest(is_public=True),
        )

        public_offer = PublicOfferListItem.model_validate(
            get_public_offers(self.db)[0]
        ).model_dump(mode="json")

        self.assertIsNone(public_offer["participant_public_name"])
        self.assertNotIn("participant_visible", public_offer)

    def test_public_detail_hides_participant_name_when_participant_is_not_visible(
        self,
    ) -> None:
        offer = self.create_offer(
            title="Hidden participant detail offer",
            participant_visible=False,
            participant_public_name="Hidden Participant",
        )
        OfferModerationService(self.db).moderate_offer(
            offer.id,
            AdminOfferModerationUpdateRequest(is_public=True),
        )

        public_offer = PublicOfferDetail.model_validate(
            get_public_offer(offer.id, self.db)
        ).model_dump(mode="json")

        self.assertIsNone(public_offer["participant_public_name"])
        self.assertNotIn("participant_visible", public_offer)

    def test_public_list_shows_participant_name_when_participant_is_visible(
        self,
    ) -> None:
        offer = self.create_offer(
            title="Visible participant list offer",
            participant_visible=True,
            participant_public_name="Visible Participant",
        )
        OfferModerationService(self.db).moderate_offer(
            offer.id,
            AdminOfferModerationUpdateRequest(is_public=True),
        )

        public_offer = PublicOfferListItem.model_validate(
            get_public_offers(self.db)[0]
        ).model_dump(mode="json")

        self.assertEqual(public_offer["participant_public_name"], "Visible Participant")
        self.assertNotIn("participant_visible", public_offer)

    def test_user_gets_two_own_offers(self) -> None:
        first_offer = self.create_offer(
            title="First user offer",
            external_user_id="same-user",
        )
        second_offer = self.create_offer(
            title="Second user offer",
            external_user_id="same-user",
        )

        user_offers = get_user_offers(first_offer.user_id, self.db)
        user_offer_ids = {offer.id for offer in user_offers}

        self.assertEqual(first_offer.user_id, second_offer.user_id)
        self.assertEqual(user_offer_ids, {first_offer.id, second_offer.id})

    def test_user_does_not_get_other_users_offers(self) -> None:
        own_offer = self.create_offer(
            title="Own offer",
            external_user_id="own-user",
        )
        other_offer = self.create_offer(
            title="Other offer",
            external_user_id="other-user",
        )

        user_offers = get_user_offers(own_offer.user_id, self.db)
        user_offer_ids = {offer.id for offer in user_offers}

        self.assertIn(own_offer.id, user_offer_ids)
        self.assertNotIn(other_offer.id, user_offer_ids)

    def test_missing_user_offers_returns_404(self) -> None:
        with self.assertRaises(HTTPException) as context:
            get_user_offers(uuid.uuid4(), self.db)

        self.assertEqual(context.exception.status_code, 404)

    def test_user_without_offers_gets_empty_list(self) -> None:
        user = User(display_name="No offers user")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self.assertEqual(get_user_offers(user.id, self.db), [])

    def test_user_offer_response_contains_status_is_public_and_photos(self) -> None:
        offer = self.create_offer()

        user_offer = UserOfferListItem.model_validate(
            get_user_offers(offer.user_id, self.db)[0]
        ).model_dump(mode="json")

        self.assertEqual(user_offer["photo_urls"], ["http://127.0.0.1:8000/uploads/images/photo.jpg"])
        self.assertEqual(user_offer["status"], "new")
        self.assertIs(user_offer["is_public"], False)
        self.assertNotIn("moderation_comment", user_offer)
        self.assertNotIn("valuation_source", user_offer)
        self.assertNotIn("user_id", user_offer)

    def test_public_detail_shows_participant_name_when_participant_is_visible(
        self,
    ) -> None:
        offer = self.create_offer(
            title="Visible participant detail offer",
            participant_visible=True,
            participant_public_name="Visible Participant",
        )
        OfferModerationService(self.db).moderate_offer(
            offer.id,
            AdminOfferModerationUpdateRequest(is_public=True),
        )

        public_offer = PublicOfferDetail.model_validate(
            get_public_offer(offer.id, self.db)
        ).model_dump(mode="json")

        self.assertEqual(public_offer["participant_public_name"], "Visible Participant")
        self.assertNotIn("participant_visible", public_offer)


if __name__ == "__main__":
    unittest.main()
