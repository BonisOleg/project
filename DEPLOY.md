# Деплой Oyra на DigitalOcean Droplet

Стек: Docker Compose → nginx → gunicorn → Django → PostgreSQL.

## Передумови

- Droplet Ubuntu 24.04, ≥ 2 GB RAM
- Шлях проєкту: `/var/www/oyra` (не вкладений `/var/www/oyra/oyra`)
- Firewall: `ufw allow OpenSSH`, `ufw allow 80/tcp`, `ufw allow 443/tcp`

## 1. Перший HTTP-деплой

```bash
mkdir -p /var/www && cd /var/www
git clone <REPO_URL> oyra && cd oyra

bash deploy/docker/install-docker.sh
cp .env.example .env
nano .env
```

У `.env` обов'язково:

- `SECRET_KEY` — згенеруйте унікальний ключ
- `POSTGRES_PASSWORD` — надійний пароль
- `ALLOWED_HOSTS` — IP Droplet, `web`, `127.0.0.1`, `localhost`
- `USE_HTTPS=false`

```bash
systemctl stop nginx gunicorn-* 2>/dev/null || true
systemctl disable nginx gunicorn-* 2>/dev/null || true

bash deploy/docker/deploy.sh
curl -sf http://127.0.0.1/healthz/
```

## 2. Ініціалізація даних (один раз)

```bash
docker compose exec web python manage.py seed_data
docker compose exec web python manage.py seed_hero_product_images
docker compose exec web python manage.py createsuperuser
```

## 3. SSL (після надання домену)

### 3.1 DNS

A-записи `@` і `www` → IP Droplet. Дочекайтеся propagation.

### 3.2 Оновити конфіг nginx

У [`deploy/nginx/docker.prod.conf`](deploy/nginx/docker.prod.conf) замініть `your-domain.com` на реальний домен (у `server_name` і `ssl_certificate*`).

Закомітьте зміни, `git push`, `git pull` на сервері.

### 3.3 Certbot на хості

```bash
apt install -y certbot
docker compose stop nginx

certbot certonly --standalone \
  -d your-domain.com -d www.your-domain.com \
  --agree-tos -m admin@your-domain.com
```

### 3.4 Оновити `.env`

```env
DOMAIN=your-domain.com
USE_HTTPS=true
SITE_URL=https://your-domain.com
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,DROPLET_IP,127.0.0.1,localhost,web
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com
SECURE_SSL_REDIRECT=True
LIQPAY_SANDBOX=False
```

### 3.5 HTTPS-деплой

```bash
git pull origin main
bash deploy/docker/deploy.sh
curl -sI https://your-domain.com/ | head -5
```

## 4. Оновлення на prod

```bash
cd /var/www/oyra
git pull origin main
bash deploy/docker/deploy.sh
```

`deploy.sh` завжди виконує `--build` — без rebuild код у контейнері не оновиться.

## 5. Локальна перевірка (розробка)

```bash
cp .env.example .env.docker
# Заповнити SECRET_KEY, POSTGRES_PASSWORD, ALLOWED_HOSTS

ENV_FILE=.env.docker docker compose --env-file .env.docker up -d --build
curl -sf http://127.0.0.1/healthz/

docker compose exec web python manage.py seed_data
docker compose exec web python manage.py seed_hero_product_images
```

> Локальний `.env` для develop не чіпаємо — Docker використовує окремий файл через `ENV_FILE`.

## 6. Дебаг

```bash
docker compose ps
docker compose logs --tail=50 web nginx
docker compose exec web python manage.py check --deploy
curl -sf http://127.0.0.1/healthz/
```

## Критичні правила

| Правило | Чому |
|---------|------|
| `SECURE_SSL_REDIRECT=False` у `config/settings/docker.py` | Healthcheck отримує 301 → unhealthy |
| `web` у `ALLOWED_HOSTS` | Internal healthcheck |
| TLS у nginx, не в gunicorn | Django redirect ламає healthcheck |
| Зміни через git | Не патчити nginx/settings на сервері вручну |
| `.env` не в git | Секрети лише на сервері |

## Renew SSL

```bash
certbot renew
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload
```
