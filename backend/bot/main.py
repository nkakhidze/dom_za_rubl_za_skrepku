import asyncio
from io import BytesIO

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from app.core.config import settings
from bot.backend_client import BackendClient, BackendClientError


router = Router()


class NewOfferStates(StatesGroup):
    title = State()
    description = State()
    city = State()
    declared_value = State()
    exchange_preference = State()
    participant_public_name = State()
    participant_visible = State()
    photos = State()


def display_name_from_message(message: Message) -> str | None:
    user = message.from_user

    if user is None:
        return None

    full_name = user.full_name.strip()

    if full_name:
        return full_name

    return user.username


def telegram_id_from_message(message: Message) -> str:
    if message.from_user is None:
        raise ValueError("Telegram user is missing")

    return str(message.from_user.id)


async def get_or_create_backend_user(message: Message) -> dict:
    async with BackendClient(settings.backend_api_url) as backend:
        return await backend.create_or_get_user_by_telegram_id(
            telegram_id=telegram_id_from_message(message),
            display_name=display_name_from_message(message),
        )


@router.message(Command("start"))
async def start(message: Message):
    try:
        user = await get_or_create_backend_user(message)
    except (BackendClientError, ValueError):
        await message.answer("Не удалось связаться с backend. Попробуйте позже.")
        return

    await message.answer(
        "Привет! Я помогу подать предложение для обмена.\n\n"
        f"Ваш backend user_id: {user['id']}\n"
        "Команды:\n"
        "/new_offer - подать оффер\n"
        "/my_offers - посмотреть мои офферы"
    )


@router.message(Command("my_offers"))
async def my_offers(message: Message):
    try:
        user = await get_or_create_backend_user(message)

        async with BackendClient(settings.backend_api_url) as backend:
            offers = await backend.get_my_offers(user["id"])
    except (BackendClientError, ValueError):
        await message.answer("Не удалось получить офферы. Попробуйте позже.")
        return

    if not offers:
        await message.answer("У вас пока нет офферов.")
        return

    lines = ["Ваши офферы:"]

    for offer in offers:
        public_state = "опубликован" if offer["is_public"] else "не опубликован"
        city = offer["city"] or "город не указан"
        lines.append(
            f"- {offer['title']} | {city} | {offer['status']} | {public_state}"
        )

    await message.answer("\n".join(lines))


@router.message(Command("new_offer"))
async def new_offer(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NewOfferStates.title)
    await message.answer(
        "Введите название оффера.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(NewOfferStates.title)
async def collect_title(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Название должно быть хотя бы из 2 символов.")
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(NewOfferStates.description)
    await message.answer("Опишите предмет или услугу подробнее.")


@router.message(NewOfferStates.description)
async def collect_description(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 10:
        await message.answer("Описание должно быть хотя бы из 10 символов.")
        return

    await state.update_data(description=message.text.strip(), offer_type="physical_item")
    await state.set_state(NewOfferStates.city)
    await message.answer("Укажите город.")


@router.message(NewOfferStates.city)
async def collect_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip() if message.text else None)
    await state.set_state(NewOfferStates.declared_value)
    await message.answer("Укажите примерную стоимость числом, например: 1500.")


@router.message(NewOfferStates.declared_value)
async def collect_declared_value(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Стоимость нужно указать числом.")
        return

    await state.update_data(declared_value=int(message.text.strip()))
    await state.set_state(NewOfferStates.exchange_preference)
    await message.answer(
        "Какой обмен рассматриваете?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Любое предложение")],
                [KeyboardButton(text="Только сопоставимая ценность")],
            ],
            resize_keyboard=True,
        ),
    )


@router.message(NewOfferStates.exchange_preference)
async def collect_exchange_preference(message: Message, state: FSMContext):
    if message.text == "Только сопоставимая ценность":
        exchange_preference = "comparable_value_only"
    elif message.text == "Любое предложение":
        exchange_preference = "any_offer"
    else:
        await message.answer("Выберите один из вариантов на клавиатуре.")
        return

    await state.update_data(exchange_preference=exchange_preference)
    await state.set_state(NewOfferStates.participant_public_name)
    await message.answer(
        "Какое имя показывать публично? Можно отправить своё имя или псевдоним.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(NewOfferStates.participant_public_name)
async def collect_participant_public_name(message: Message, state: FSMContext):
    participant_public_name = message.text.strip() if message.text else None

    if not participant_public_name:
        participant_public_name = display_name_from_message(message)

    await state.update_data(participant_public_name=participant_public_name)
    await state.set_state(NewOfferStates.participant_visible)
    await message.answer(
        "Показывать это имя в публичном списке?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Показывать имя")],
                [KeyboardButton(text="Не показывать имя")],
            ],
            resize_keyboard=True,
        ),
    )


@router.message(NewOfferStates.participant_visible)
async def collect_participant_visible(message: Message, state: FSMContext):
    if message.text == "Показывать имя":
        participant_visible = True
    elif message.text == "Не показывать имя":
        participant_visible = False
    else:
        await message.answer("Выберите один из вариантов на клавиатуре.")
        return

    await state.update_data(participant_visible=participant_visible, photos=[])
    await state.set_state(NewOfferStates.photos)
    await message.answer(
        "Пришлите от 1 до 3 фотографий. Когда закончите, нажмите Готово.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Готово")]],
            resize_keyboard=True,
        ),
    )


@router.message(NewOfferStates.photos, F.photo)
async def collect_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    photos = data.get("photos", [])

    if len(photos) >= 3:
        await message.answer("Можно загрузить не больше 3 фотографий.")
        return

    if not message.photo:
        await message.answer("Пришлите фото файлом Telegram.")
        return

    image = BytesIO()
    await bot.download(message.photo[-1], destination=image)
    photos.append(image.getvalue())
    await state.update_data(photos=photos)
    await message.answer(f"Фото принято: {len(photos)}/3.")


@router.message(NewOfferStates.photos, F.text == "Готово")
async def finish_offer(message: Message, state: FSMContext):
    data = await state.get_data()
    photos: list[bytes] = data.get("photos", [])

    if not photos:
        await message.answer("Для физического предмета нужно хотя бы одно фото.")
        return

    try:
        user = await get_or_create_backend_user(message)

        async with BackendClient(settings.backend_api_url) as backend:
            photo_urls = []

            for index, photo in enumerate(photos, start=1):
                uploaded = await backend.upload_image(
                    content=photo,
                    filename=f"offer-{index}.jpg",
                    content_type="image/jpeg",
                )
                photo_urls.append(uploaded["photo_url"])

            offer = await backend.create_offer(
                {
                    "messenger_type": "telegram",
                    "external_user_id": telegram_id_from_message(message),
                    "username": message.from_user.username if message.from_user else None,
                    "first_name": message.from_user.first_name if message.from_user else None,
                    "last_name": message.from_user.last_name if message.from_user else None,
                    "title": data["title"],
                    "description": data["description"],
                    "offer_type": data["offer_type"],
                    "city": data["city"],
                    "declared_value": data["declared_value"],
                    "photo_urls": photo_urls,
                    "exchange_preference": data["exchange_preference"],
                    "consent_accepted": True,
                    "participant_visible": data["participant_visible"],
                    "participant_public_name": data["participant_public_name"],
                }
            )
    except (BackendClientError, ValueError):
        await message.answer("Не удалось создать оффер. Проверьте данные и попробуйте позже.")
        return

    await state.clear()
    await message.answer(
        "Оффер создан и отправлен на модерацию.\n"
        f"id: {offer['id']}\n"
        f"status: {offer['status']}",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(NewOfferStates.photos)
async def photos_fallback(message: Message):
    await message.answer("Пришлите фото или нажмите Готово.")


async def main():
    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
