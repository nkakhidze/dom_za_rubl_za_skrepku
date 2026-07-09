# MVP Flow

Этот документ описывает ручную проверку основного сценария проекта.

## 1. Смысл сущностей

- `offers` — входящие заявки пользователей. Заявка ещё не является предметом цепочки.
- `items` — реальные предметы цепочки: стартовый, текущий, прошлые и будущие.
- `deals` — переходы между предметами: какой предмет проект отдал и какой получил.

Основная публичная история строится не из `offers`, а из цепочки `items`, соединённых `deals`.

```text
current item + selected offer
        ↓
new received item
        ↓
completed deal: given_item -> received_item
```

## 2. Создание super_admin и вход

Создать первого super_admin:

```powershell
python -m scripts.create_super_admin --login admin --password change_me
```

Войти:

```http
POST /api/auth/login
```

```json
{
  "login": "admin",
  "password": "change_me"
}
```

Админские запросы используют:

```text
Authorization: Bearer <access_token>
```

В Swagger `/docs` после `POST /api/auth/login` нажмите **Authorize** и вставьте только `access_token` без слова `Bearer`.

## 3. Стартовый предмет цепочки

Перед первым обменом админ создаёт текущий предмет:

```http
POST /api/admin/items
```

Пример:

```json
{
  "title": "Скрепка",
  "description": "Стартовый предмет цепочки",
  "item_type": "physical_item",
  "owner_type": "tom_sawyer_fest",
  "owner_name": "Дом за скрепку",
  "is_current": true,
  "is_public": true,
  "sequence_number": 0
}
```

## 4. Пользователь подаёт заявку

Загрузка фото:

```http
POST /api/files/images
```

Backend синхронно оптимизирует изображение: проверяет JPEG/PNG/WebP через Pillow, сохраняет основную WebP-версию и `thumbnail_url`. В `POST /api/offers` frontend передаёт `photo_urls` и metadata/thumbnail-поля; старые фото без thumbnail отображаются через fallback на `photo_url`.

Создание заявки:

```http
POST /api/offers
```

Новая заявка получает:

- `status=new`
- `is_public=false`
- `visibility_status=normal`
- `sort_priority=0`

## 5. Админская работа с заявками

Список заявок:

```http
GET /api/admin/offers
```

Поддерживаются фильтры:

- `offer_status`
- `visibility_status`
- `sort=created_at_desc`
- `sort=moderated_value_desc`
- `sort=priority`

Модерация заявки:

```http
PATCH /api/admin/offers/{offer_id}/moderation
```

Пример:

```json
{
  "moderated_value": 3000,
  "valuation_source": "Авито, похожие предложения",
  "visibility_status": "normal",
  "sort_priority": 10,
  "public_comment": "Хороший кандидат для следующего обмена",
  "participant_visible": true
}
```

MVP-статусы заявок:

- `new` — новая заявка.
- `reviewed` — просмотрена/оценена админом.
- `selected` — выбрана в цепочку.
- `hidden` — скрыта из рабочего списка.
- `rejected` — отклонена.

Legacy-статусы `published`, `approved`, `moderation`, `archived` сохранены для обратной совместимости.

## 6. Выбор следующего предмета цепочки

Когда админ выбирает заявку:

```http
POST /api/admin/offers/{offer_id}/select-next
```

Пример:

```json
{
  "public_story": "Поменяли скрепку на ручку",
  "video_url": null,
  "photo_url": "/uploads/images/pen.jpg",
  "is_public": true
}
```

Backend делает одну атомарную операцию:

1. Берёт текущий `item`.
2. Создаёт новый `item` из выбранной заявки.
3. Помечает старый текущий предмет как `past`.
4. Помечает новый предмет как `current`.
5. Создаёт `deal` со связями `given_item_id -> old item` и `received_item_id -> new item`.
6. Помечает заявку как `selected`.

Статус `selected` нельзя корректно получить простым ручным изменением статуса: для этого нужен `select-next`, иначе не появятся новый предмет и переход в истории.

## 7. Публичная история обменов

Публичная страница читает:

```http
GET /api/public/exchange-chain
```

В ответе приходят публичные завершённые `deals`, отсортированные по `step_number ASC`, с двумя предметами:

- `given_item`
- `received_item`

Frontend превращает эти переходы в односвязную цепочку предметов:

```text
Стартовый предмет
  ↓
Получили следующий предмет
  ↓
Получили следующий предмет
```

Пользовательский интерфейс не обязан показывать “Шаг №1”, потому что второй предмет одного обмена становится первым предметом следующего.

## 8. Legacy-сценарий откликов

Эти endpoint’ы сохранены для совместимости и экспериментов, но не являются основной механикой публичной истории:

- `POST /api/items`
- `GET /api/users/{user_id}/items`
- `POST /api/deals`
- `GET /api/users/{user_id}/deals`

## 9. Telegram-уведомления

Backend отправляет Telegram-уведомления, если:

- у пользователя есть `messenger_accounts` с `messenger_type=telegram`;
- задан `TELEGRAM_BOT_TOKEN`;
- статус заявки или сделки реально изменился.

Ошибки Telegram API не откатывают основную операцию.
