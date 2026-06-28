import asyncio
from io import BytesIO

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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


class NewItemStates(StatesGroup):
    title = State()
    description = State()


class RespondStates(StatesGroup):
    item = State()


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
        "/my_offers - посмотреть мои офферы\n"
        "/new_item - создать предмет для обмена\n"
        "/my_items - посмотреть мои предметы\n"
        "/respond <offer_id> - откликнуться на оффер\n"
        "/my_deals - посмотреть мои сделки"
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
        status = offer.get("status_label") or offer["status"]
        lines.append(
            f"- {offer['title']} | {city} | {status} | {public_state}"
        )

    await message.answer("\n".join(lines))


@router.message(Command("new_item"))
async def new_item(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NewItemStates.title)
    await message.answer(
        "Введите название предмета, который хотите предложить в обмен.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(NewItemStates.title)
async def collect_item_title(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Название должно быть хотя бы из 2 символов.")
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(NewItemStates.description)
    await message.answer("Опишите предмет подробнее.")


@router.message(NewItemStates.description)
async def collect_item_description(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Описание должно быть хотя бы из 2 символов.")
        return

    data = await state.get_data()

    try:
        user = await get_or_create_backend_user(message)

        async with BackendClient(settings.backend_api_url) as backend:
            item = await backend.create_item(
                {
                    "user_id": user["id"],
                    "title": data["title"],
                    "description": message.text.strip(),
                }
            )
    except (BackendClientError, ValueError):
        await message.answer("Не удалось создать предмет. Проверьте backend и попробуйте позже.")
        return

    await state.clear()
    await message.answer(
        "Предмет создан.\n"
        f"id: {item['id']}\n"
        f"status: {item['status']}",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("my_items"))
async def my_items(message: Message):
    try:
        user = await get_or_create_backend_user(message)

        async with BackendClient(settings.backend_api_url) as backend:
            items = await backend.get_user_items(user["id"])
    except (BackendClientError, ValueError):
        await message.answer("Не удалось получить предметы. Попробуйте позже.")
        return

    if not items:
        await message.answer("У вас пока нет предметов. Создайте первый через /new_item.")
        return

    lines = ["Ваши предметы:"]

    for item in items:
        lines.append(f"- {item['title']} | {item['status']} | {item['id']}")

    await message.answer("\n".join(lines))


@router.message(Command("my_deals"))
async def my_deals(message: Message):
    try:
        user = await get_or_create_backend_user(message)

        async with BackendClient(settings.backend_api_url) as backend:
            deals = await backend.get_user_deals(user["id"])
    except (BackendClientError, ValueError):
        await message.answer("Не удалось получить сделки. Попробуйте позже.")
        return

    if not deals:
        await message.answer("У вас пока нет сделок.")
        return

    lines = ["Ваши сделки:"]

    for deal in deals:
        status = deal.get("status_label") or deal["status"]
        offer_title = deal.get("offer_title") or "оффер без названия"
        lines.append(f"- {offer_title} ← {deal['item_title']} | {status}")

    await message.answer("\n".join(lines))


@router.message(Command("respond"))
async def respond(message: Message, command: CommandObject, state: FSMContext):
    offer_id = command.args.strip() if command.args else ""

    if not offer_id:
        await message.answer("Укажите offer_id: /respond <offer_id>")
        return

    try:
        user = await get_or_create_backend_user(message)

        async with BackendClient(settings.backend_api_url) as backend:
            items = await backend.get_user_items(user["id"])
    except (BackendClientError, ValueError):
        await message.answer("Не удалось получить ваши предметы. Попробуйте позже.")
        return

    if not items:
        await message.answer("У вас пока нет предметов. Сначала создайте предмет через /new_item.")
        return

    await state.clear()
    await state.set_state(RespondStates.item)
    await state.update_data(offer_id=offer_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=item["title"],
                    callback_data=f"respond_item:{item['id']}",
                )
            ]
            for item in items[:10]
        ]
    )

    await message.answer("Выберите предмет для обмена.", reply_markup=keyboard)


@router.callback_query(RespondStates.item, F.data.startswith("respond_item:"))
async def choose_response_item(callback: CallbackQuery, state: FSMContext):
    item_id = callback.data.split(":", 1)[1] if callback.data else ""
    data = await state.get_data()
    offer_id = data.get("offer_id")

    if not offer_id or not item_id:
        await callback.message.answer("Не удалось определить offer или item. Запустите /respond заново.")
        await state.clear()
        await callback.answer()
        return

    try:
        async with BackendClient(settings.backend_api_url) as backend:
            deal = await backend.create_deal(
                {
                    "offer_id": offer_id,
                    "item_id": item_id,
                }
            )
    except BackendClientError as error:
        await callback.message.answer(f"Не удалось отправить отклик: {error}")
        await callback.answer()
        return

    await state.clear()
    await callback.message.answer(
        "Отклик отправлен.\n"
        f"id: {deal['id']}\n"
        f"status: {deal.get('status_label') or deal['status']}"
    )
    await callback.answer()


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
    if not settings.telegram_bot_token or settings.telegram_bot_token == "change_me":
        print("TELEGRAM_BOT_TOKEN is not configured; Telegram bot service is idle.")
        return

    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
