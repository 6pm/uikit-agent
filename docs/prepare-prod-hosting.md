# Інструкція як задеплоїти цей проект для прода

Ми будемо використовуват Hetzner для хостингу. Треба купити віртуалку там спочатку і отримати всі доступи.
Але Hetzner дає тільки віртуалку з ІР адресою, але нам треба домен щоб налаштувати https.
Але щоб не купувати домен ми скористаємося сервісом https://www.duckdns.org. Цей сервіс дозволяє користуватися його сабдоменами щоб отримати SSL сертифікат на саб домен.


Запускаємо віртуалку на Hetzner і заходимо на неї:
```sh
# логінимось з паролем чи ssh ключем
ssh root@<YOUR_SERVER_IP>

# Оновлення пакетів
apt update && apt upgrade -y

# Встановлення Docker та Docker Compose плагіну
apt install -y docker.io docker-compose-v2

# встановити uv для python
curl -LsSf https://astral.sh/uv/install.sh | sh

```


## 2. Налаштування Firewall (UFW)
Traefik використовує порти 80 та 443.
```sh
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## 3. Налаштування проекту
Створіть папку для проекту:
```sh
mkdir /opt/uikit-agent # папка opt має бути вже не сервері, це системна папка
cd /opt/uikit-agent
```

Зклонувати проект з Github:
```sh
git clone https://github.com/6pm/uikit-agent.git
```

Добавити .env ключі:
```sh
cd /opt/uikit-agent/uikit-agent
nano .env
```

Ставимо всі модулі:
```sh
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies from pyproject.toml
uv sync
```

# Добавити ip сервера на Hetzner в docker-compose.yml замість цього ip:
```sh
- "traefik.http.routers.api.rule=Host(`myapp.159.69.248.114.nip.io`)"
```