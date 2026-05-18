# 🤖 Telegram Bot: Turner CRM (Токарные работы)
[![Website](https://img.shields.io/website?label=akulov-dev.ru&style=for-the-badge&url=https%3A%2F%2Fakulov-dev.ru)](https://akulov-dev.ru) [![Telegram](https://img.shields.io/badge/Telegram-Channel-2CA5E0?style=for-the-badge&logo=telegram)](https://t.me/Serg_Akulov_tg) [![Developer](https://img.shields.io/badge/Developer-Sergey%20Akulov-blue?style=for-the-badge)](https://github.com/serg-akulov) [![Profile Views](https://komarev.com/ghpvc/?username=serg-akulov-turner-bot&label=Project%20Views&color=0e75b6&style=for-the-badge)](https://github.com/serg-akulov)

<img width="1166" height="735" alt="11111111111111111111111111111" src="https://github.com/user-attachments/assets/6d8b5782-3fc8-444b-a128-52281845ed8" />

---
Простой и мощный бот для приема заказов на токарные/фрезерные работы с удобной админ-панелью. Клиент проходит опрос (фото, тип работы, размеры), а вы получаете структурированный заказ.

### ✨ Возможности
*   📸 **Прием фото и чертежей** (файлы сохраняются в Telegram, не занимают место на сервере).
*   🏗 **Конструктор опроса** (можно менять тексты вопросов и кнопок через админку).
*   📋 **CRM-система** для управления статусами (Новый -> В работе -> Готов).
*   💬 **Чат с клиентом** (ответы на сообщения бота пересылаются пользователю).
*   🌍 **Мультиязычность** — бот и админ-панель на 3 языках (RU / EN / UK).
*   🐳 **Docker** — развёртывание одной командой.

---

<img width="1638" height="1312" alt="333333333333333333" src="https://github.com/user-attachments/assets/630d607f-e51a-496a-8327-0da0e4a04499" />
<img width="1636" height="582" alt="222222222222222222222222" src="https://github.com/user-attachments/assets/f745dfb8-a063-4c3b-867d-98164ca6b9eb" />
<img width="1333" height="760" alt="44444444444444" src="https://github.com/user-attachments/assets/45f0ded2-cc06-470d-917a-1e0f96e4b8a0" />

---

## 🐳 Установка через Docker (рекомендуется)

### Требования
*   Docker + Docker Compose

### Шаг 1. Клонирование
```bash
git clone https://github.com/serg-akulov/turner-telegram-bot.git
cd turner-telegram-bot
```

### Шаг 2. Настройка
Скопируйте `.env.example` в `.env` и заполните:
```bash
cp .env.example .env
```

Основные параметры:
```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_PANEL_PASSWORD=admin123       # пароль для веб-админки
BOT_ADMIN_PASSWORD=botadmin123      # пароль для /iamadmin в боте
FRONTEND_PORT=45554                 # порт веб-админки
API_PORT=45556                      # порт API
```

### Шаг 3. Запуск
```bash
docker compose up -d --build
```

Готово! Бот, API, фронтенд и MySQL запустятся автоматически.

- **Админ-панель:** `http://localhost:45554` (пароль из `ADMIN_PANEL_PASSWORD`)
- **Бот:** найдите вашего бота в Telegram и нажмите `/start`

### Полезные команды
```bash
docker compose logs -f bot          # логи бота
docker compose restart bot          # перезапуск бота
docker compose down                 # остановить всё
docker compose up -d --build        # пересобрать и запустить
```

---

## 💻 Установка без Docker (классическая)

### Требования
*   VPS/VDS с **Ubuntu 20.04** или **22.04** (можно и Debian).
*   Установленный **MySQL** (или MariaDB) и **Web-сервер** (Apache/Nginx + PHP) для админки.

### Шаг 1. Подготовка Базы Данных
Зайдите в MySQL и создайте пустую базу данных:
```sql
CREATE DATABASE turner_db;
CREATE USER 'turner_user'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON turner_db.* TO 'turner_user'@'localhost';
FLUSH PRIVILEGES;
```

### Шаг 2. Скачивание и запуск
```bash
chmod +x install.sh
./install.sh
```

Скрипт попросит ввести:
*   Токен бота (получить у @BotFather).
*   Данные от БД (хост, имя базы, логин, пароль).
*   Пароль для входа в веб-админку.
*   Цифровой пароль для администрирования внутри бота.

**Готово!** Бот сам установит библиотеки, создаст таблицы и запустится как системная служба.

---

## 🌐 Настройка Админки (без Docker)

1.  **Установите веб-сервер и PHP:**
    ```bash
    sudo apt install apache2 php libapache2-mod-php php-mysql
    ```

2.  **Скопируйте файлы:**
    ```bash
    sudo mkdir -p /var/www/html/crm
    sudo cp admin.php /var/www/html/crm/index.php
    sudo cp php_config.php /var/www/html/crm/
    ```

3.  **Настройте права:**
    ```bash
    sudo chown -R www-data:www-data /var/www/html/crm
    sudo chmod -R 755 /var/www/html/crm
    ```

4.  Откройте `http://IP-СЕРВЕРА/crm` и войдите с паролем из установки.

---

## 🤖 Управление ботом

### Через Web-админку (Docker)
*   **Заказы:** просмотр, фото, смена статусов — клиент получит уведомление.
*   **Настройки бота:** меняйте тексты вопросов, кнопок и логику без редактирования кода.
*   **Язык:** переключатель в шапке админки (RU / EN / UK).

### Через Telegram (администратор)
1.  Введите `/iamadmin ВАШ_ПАРОЛЬ` (из `BOT_ADMIN_PASSWORD`).
2.  Бот начнёт пересылать уведомления о новых заказах.
3.  Используйте `Reply` на сообщение с заказом — ответ уйдёт клиенту.
4.  Команда `/lang` — смена языка бота.

### Смена языка
**Бот:** отправьте `/lang` и выберите язык из меню.
**Админка:** нажмите иконку 🌐 в правом верхнем углу.

---

## 🛠 Серверные команды (без Docker)

```bash
sudo systemctl restart turner_bot    # перезапуск
sudo systemctl stop turner_bot       # остановка
sudo journalctl -u turner_bot -f     # логи
```

---

## 📂 Структура проекта

```
├── bot.py              # Основной код бота (Aiogram 3)
├── i18n.py             # Модуль интернационализации бота
├── config.py           # Конфигурация (переменные окружения)
├── database.py         # Работа с MySQL
├── schema.sql          # Структура БД
├── locales/            # Переводы бота (ru.json, en.json, uk.json)
├── install.sh          # Автоустановщик (без Docker)
├── admin.php           # Админка на PHP (без Docker)
├── docker-compose.yml
├── Dockerfile          # Dockerfile бота
├── backend/            # FastAPI — API для React-админки
│   ├── main.py
│   ├── database.py
│   └── config.py
└── frontend/           # React + Ant Design — админ-панель
    ├── src/
    │   ├── i18n.js          # Настройка react-i18next
    │   ├── locales/         # Переводы фронтенда (ru, en, uk)
    │   └── components/
    └── Dockerfile
```

---

## 🌍 Интернационализация (i18n)

Бот и фронтенд поддерживают 3 языка:
- 🇷🇺 **Русский** (по умолчанию)
- 🇬🇧 **English**
- 🇺🇦 **Українська**

**Как это работает:**
- Переводы бота хранятся в `locales/*.json`, приоритет — тексты из BotConfig (БД) > файл перевода > русский.
- Переводы фронтенда — `frontend/src/locales/*.json`, язык определяется автоматически и сохраняется в localStorage.
- Язык пользователя сохраняется в таблице `user_prefs` (бот) / localStorage (фронтенд).

---

👨‍💻 Автор: Сергей Акулов

Инди-разработчик и Токарь.

🛠️ Больше полезного софта на моем сайте: [akulov-dev.ru](https://akulov-dev.ru)

GitHub: [@serg-akulov](https://github.com/serg-akulov)

## Благодарности

Огромное спасибо [@dedkovd](https://github.com/dedkovd) за реализацию Docker-контейнеризации — это сделало проект значительно удобнее для развертывания.
Отдельная благодарность [@vionaaru](https://github.com/vionaaru) за помощь с Docker-контейнеризацией и обновлением документации.

Copyright © 2025. Released under the MIT License.
