# Caddy deploy notes

This project uses Caddy as the public HTTPS reverse proxy.

Expected routing:

- `https://tomsk-dom-za-skrepku.space/api/*` -> backend on `127.0.0.1:8000`
- `https://tomsk-dom-za-skrepku.space/uploads/*` -> backend on `127.0.0.1:8000`
- `https://tomsk-dom-za-skrepku.space/*` -> frontend on `127.0.0.1:3000`

The production Caddyfile lives in:

```text
deploy/Caddyfile
```

It includes:

- automatic HTTPS for `tomsk-dom-za-skrepku.space`;
- request body limit: `20MB`;
- Caddy access log file: `/var/log/caddy/paperclip-house-access.log`;
- access log rotation: `10MiB`, 4 rotated files plus the current file, 7 days.

## Apply on server

From the repository backend directory:

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

If Caddy is not running yet:

```bash
sudo systemctl enable --now caddy
```

## Check logs

Backend app logs:

```bash
tail -f logs/backend.log
```

Caddy access logs:

```bash
sudo tail -f /var/log/caddy/paperclip-house-access.log
```

Caddy service logs:

```bash
journalctl -u caddy -f
```

## Request body limit

The default max request body is `20MB`.

The backend image upload limit should stay lower or equal to this boundary:

```env
IMAGE_MAX_FILE_SIZE_MB=15
```

This way Caddy rejects oversized uploads before they reach Python.

## Important

`docker-compose.yml` binds backend and frontend ports to localhost:

```text
127.0.0.1:8000:8000
127.0.0.1:3000:80
```

This prevents public traffic from bypassing Caddy request limits by calling
`:8000` or `:3000` directly.
