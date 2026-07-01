import asyncio
import logging
import uuid
from io import BytesIO
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

try:
    from bot.backend_client import (
        BackendClientError,
        BackendConflictError,
        BackendLinkExpiredError,
        BackendUnavailableError,
        TelegramBackendClient,
        TelegramUserData,
    )
    from bot.config import settings
    from bot import texts
except ModuleNotFoundError:
    from backend_client import (
        BackendClientError,
        BackendConflictError,
        BackendLinkExpiredError,
        BackendUnavailableError,
        TelegramBackendClient,
        TelegramUserData,
    )
    from config import settings
    import texts


logger = logging.getLogger(__name__)
router = Router()

BTN_ABOUT = "🏠 О проекте"
BTN_NEW_OFFER = "📎 Предложить предмет"
BTN_MY_OFFERS = "📋 Мои предложения"
BTN_LINK_SITE = "🔗 Связать с сайтом"
BTN_OPEN_SITE = "🌐 Открыть сайт"
BTN_DONE = "Готово"
BTN_CANCEL = "Отменить"


class NewOfferStates(StatesGroup):
    title = State()
    description = State()
    city = State()
    declared_value = State()
    participant_public_name = State()
    photos = State()
    confirm = State()


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ABOUT), KeyboardButton(text=BTN_NEW_OFFER)],
            [KeyboardButton(text=BTN_MY_OFFERS), KeyboardButton(text=BTN_LINK_SITE)],
            [KeyboardButton(text=BTN_OPEN_SITE)],
        ],
        resize_keyboard=True,
    )


def is_telegram_button_url(url: str) -> bool:
    parsed_url = urlparse(url)
    host = (parsed_url.hostname or "").lower()
    return (
        parsed_url.scheme in {"http", "https"}
        and bool(host)
        and host not in {"localhost", "127.0.0.1", "::1"}
    )


def site_keyboard(text: str = "Открыть сайт") -> InlineKeyboardMarkup | None:
    if not is_telegram_button_url(settings.public_site_url):
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, url=settings.public_site_url)]
        ]
    )


def site_message(prefix: str) -> str:
    if is_telegram_button_url(settings.public_site_url):
        return prefix
    return f"{prefix}\n\nЛокальный адрес сайта: {settings.public_site_url}"


def user_data_from_message(message: Message) -> TelegramUserData:
    if message.from_user is None:
        raise ValueError("Telegram user is missing")

    return TelegramUserData(
        telegram_user_id=str(message.from_user.id),
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language_code=message.from_user.language_code,
    )


def backend_client() -> TelegramBackendClient:
    return TelegramBackendClient(
        base_url=settings.backend_url,
        internal_token=settings.telegram_internal_api_token,
    )


async def resolve_user(message: Message) -> None:
    async with backend_client() as backend:
        await backend.resolve_user(user_data_from_message(message))


async def show_menu(message: Message) -> None:
    await message.answer(texts.MENU_TEXT, reply_markup=main_keyboard())


@router.message(Command("start"))
async def start(message: Message, command: CommandObject):
    try:
        await resolve_user(message)
    except (BackendClientError, ValueError):
        await message.answer(texts.SERVICE_UNAVAILABLE)
        return

    args = (command.args or "").strip()
    if args.startswith("link_"):
        await consume_link(message, args.removeprefix("link_"))
        return

    await message.answer(
        "Привет! Я помогу предложить предмет для проекта «Дом за рубль за скрепку».",
        reply_markup=main_keyboard(),
    )


@router.message(Command("menu"))
async def menu(message: Message):
    await show_menu(message)


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_keyboard())


@router.message(F.text == BTN_ABOUT)
async def about(message: Message):
    await message.answer(site_message(texts.PROJECT_TEXT), reply_markup=site_keyboard())


@router.message(F.text == BTN_OPEN_SITE)
async def open_site(message: Message):
    await message.answer(site_message("Сайт проекта:"), reply_markup=site_keyboard())


@router.message(F.text == BTN_LINK_SITE)
async def link_site(message: Message):
    await message.answer(
        site_message(texts.LINK_HELP),
        reply_markup=site_keyboard("Открыть личный кабинет"),
    )


async def consume_link(message: Message, token: str) -> None:
    try:
        async with backend_client() as backend:
            await backend.consume_account_link(
                token=token,
                user=user_data_from_message(message),
            )
    except BackendConflictError:
        await message.answer(texts.LINK_CONFLICT, reply_markup=main_keyboard())
        return
    except BackendLinkExpiredError:
        await message.answer(texts.LINK_EXPIRED, reply_markup=main_keyboard())
        return
    except BackendClientError:
        await message.answer(texts.SERVICE_UNAVAILABLE, reply_markup=main_keyboard())
        return

    await message.answer(texts.LINK_SUCCESS, reply_markup=main_keyboard())


@router.message(F.text == BTN_MY_OFFERS)
@router.message(Command("my_offers"))
async def my_offers(message: Message):
    try:
        user = user_data_from_message(message)
        async with backend_client() as backend:
            await backend.resolve_user(user)
            offers = await backend.get_user_offers(user.telegram_user_id)
    except (BackendClientError, ValueError):
        await message.answer(texts.SERVICE_UNAVAILABLE)
        return

    if not offers:
        await message.answer("У вас пока нет предложений.", reply_markup=main_keyboard())
        return

    lines = ["Ваши предложения:"]
    for offer in offers[:10]:
        lines.append(
            f"• {offer['title']}\n"
            f"  Статус: {offer.get('status_label') or offer['status']}"
        )

    await message.answer("\n".join(lines), reply_markup=main_keyboard())


@router.message(F.text == BTN_NEW_OFFER)
@router.message(Command("new_offer"))
async def new_offer(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NewOfferStates.title)
    await message.answer(
        "Введите название предмета.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(NewOfferStates.title)
async def collect_title(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Название должно быть не короче 2 символов.")
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(NewOfferStates.description)
    await message.answer("Опишите предмет. Минимум 10 символов.")


@router.message(NewOfferStates.description)
async def collect_description(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 10:
        await message.answer("Описание должно быть не короче 10 символов.")
        return

    await state.update_data(description=message.text.strip())
    await state.set_state(NewOfferStates.city)
    await message.answer("Укажите город.")


@router.message(NewOfferStates.city)
async def collect_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip() if message.text else None)
    await state.set_state(NewOfferStates.declared_value)
    await message.answer("Укажите примерную стоимость числом. Если не знаете, отправьте 0.")


@router.message(NewOfferStates.declared_value)
async def collect_declared_value(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Стоимость нужно указать числом.")
        return

    await state.update_data(declared_value=int(message.text.strip()))
    await state.set_state(NewOfferStates.participant_public_name)
    await message.answer("Какое имя можно показывать публично? Можно отправить псевдоним.")


@router.message(NewOfferStates.participant_public_name)
async def collect_public_name(message: Message, state: FSMContext):
    public_name = message.text.strip() if message.text else None
    await state.update_data(
        participant_public_name=public_name,
        participant_visible=bool(public_name),
        photos=[],
    )
    await state.set_state(NewOfferStates.photos)
    await message.answer(
        "Пришлите 1-3 фотографии. Когда закончите, нажмите «Готово».",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=BTN_DONE), KeyboardButton(text=BTN_CANCEL)]],
            resize_keyboard=True,
        ),
    )


@router.message(NewOfferStates.photos, F.text == BTN_CANCEL)
async def cancel_offer_from_photos(message: Message, state: FSMContext):
    await cancel(message, state)


@router.message(NewOfferStates.photos, F.photo)
async def collect_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photos: list[bytes] = data.get("photos", [])

    if len(photos) >= 3:
        await message.answer("Можно добавить не больше 3 фотографий.")
        return

    image = BytesIO()
    await bot.download(message.photo[-1], destination=image)
    photos.append(image.getvalue())
    await state.update_data(photos=photos)
    await message.answer(f"Фото принято: {len(photos)}/3.")


@router.message(NewOfferStates.photos, F.text == BTN_DONE)
async def show_offer_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    photos: list[bytes] = data.get("photos", [])

    if not photos:
        await message.answer("Нужна хотя бы одна фотография.")
        return

    await state.set_state(NewOfferStates.confirm)
    await message.answer(
        "Проверьте предложение:\n\n"
        f"Название: {data['title']}\n"
        f"Описание: {data['description']}\n"
        f"Фотографий: {len(photos)}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Отправить")],
                [KeyboardButton(text="✏️ Изменить"), KeyboardButton(text=BTN_CANCEL)],
            ],
            resize_keyboard=True,
        ),
    )


@router.message(NewOfferStates.photos)
async def photos_fallback(message: Message):
    await message.answer("Пришлите фото или нажмите «Готово».")


@router.message(NewOfferStates.confirm, F.text == BTN_CANCEL)
async def cancel_offer_from_confirm(message: Message, state: FSMContext):
    await cancel(message, state)


@router.message(NewOfferStates.confirm, F.text == "✏️ Изменить")
async def restart_offer(message: Message, state: FSMContext):
    await new_offer(message, state)


@router.message(NewOfferStates.confirm, F.text == "✅ Отправить")
async def submit_offer(message: Message, state: FSMContext):
    data = await state.get_data()
    photos: list[bytes] = data.get("photos", [])

    try:
        user = user_data_from_message(message)
        async with backend_client() as backend:
            offer = await backend.create_offer(
                user=user,
                title=data["title"],
                description=data["description"],
                city=data.get("city"),
                declared_value=data.get("declared_value"),
                participant_public_name=data.get("participant_public_name"),
                participant_visible=data.get("participant_visible", False),
                idempotency_key=f"telegram:{user.telegram_user_id}:{uuid.uuid4()}",
                photos=photos,
            )
    except BackendUnavailableError:
        await message.answer(texts.SERVICE_UNAVAILABLE, reply_markup=main_keyboard())
        return
    except BackendClientError as exc:
        await message.answer(f"Не удалось отправить предложение: {exc}", reply_markup=main_keyboard())
        return

    logger.info("Telegram offer created: %s", offer.get("offer_id"))
    await state.clear()
    await message.answer(texts.OFFER_CREATED, reply_markup=main_keyboard())


async def main():
    logging.basicConfig(level=logging.INFO)

    if not settings.telegram_bot_token or settings.telegram_bot_token == "change_me":
        print("TELEGRAM_BOT_TOKEN is not configured; Telegram bot service is idle.")
        return

    if not settings.telegram_internal_api_token or settings.telegram_internal_api_token == "change_me":
        print("TELEGRAM_INTERNAL_API_TOKEN is not configured; Telegram bot service is idle.")
        return

    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    logger.info("Starting Telegram bot polling")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
