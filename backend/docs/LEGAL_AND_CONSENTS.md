# Legal Documents And User Consents

## Legal Storage

Юридические документы лежат в `legal/`.

- `legal/manifest.json` хранит активные версии.
- Тексты документов лежат отдельными Markdown-файлами с версией в имени.
- Старые редакции нельзя удалять или перезаписывать.

Активные версии на 2026-06-28:

- `user_agreement`: `2026-06-28`, обязательный.
- `privacy_policy`: `2026-06-28`, обязательное ознакомление, informational.
- `personal_data_consent`: `2026-06-28`, обязательный.
- `public_data_consent`: `2026-06-28`, добровольный.
- `marketing_consent`: `2026-06-28`, добровольный.

## user_consents

Таблица `user_consents` фиксирует историю согласий пользователя.

Ключевые поля:

- `id`
- `user_id`
- `document_code`
- `document_version`
- `status`: `accepted` или `revoked`
- `accepted_at`
- `revoked_at`
- `source`: `web`, `telegram`, `max`, `admin`
- `ip_address`
- `user_agent`
- `consent_payload`
- `created_at`
- `updated_at`

Связь:

- `users 1:N user_consents`

## Registration Rules

`POST /api/auth/register` создаёт только обычного пользователя с ролью `user`.

Телефон сохраняется с `phone_verified=false`.

Обязательные условия регистрации:

- подтверждение 18+;
- принятие `user_agreement`;
- принятие `personal_data_consent`;
- фиксация версии ознакомления с `privacy_policy`.

Маркетинговые каналы независимы:

```json
{
  "channels": {
    "email": false,
    "telegram": false,
    "max": false
  }
}
```

Отключение одного канала не меняет остальные.

## Revocation

Отзыв добровольного согласия не удаляет старую запись. Старая запись получает:

- `status=revoked`
- `revoked_at=<timestamp>`

Новая настройка создаётся новой записью.

## Account Linking

Telegram/MAX/site аккаунты не объединяются автоматически.

Запрещено объединять аккаунты:

- по `display_name`;
- по неподтверждённому телефону;
- без отдельного подтверждённого сценария связывания.
