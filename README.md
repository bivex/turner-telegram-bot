# 🤖 Turner CRM: Бот для токарных работ

[![Telegram](https://img.shields.io/badge/Telegram-Channel-2CA5E0?style=flat-square&logo=telegram)](https://t.me/Serg_Akulov_tg) [![Developer](https://img.shields.io/badge/Developer-Sergey%20Akulov-blue?style=flat-square)](https://github.com/serg-akulov) [![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

Бот для приема и управления заказами на металлообработку. Клиент заполняет опрос (фото, тип работы, размеры), вы управляете заказами через CRM-панель.

---

### ✨ Ключевые функции
*   📦 **Прием заказов:** Сбор фото, чертежей и параметров через Telegram.
*   ⚙️ **Конструктор:** Настройка вопросов и кнопок опроса через админку.
*   📊 **CRM:** Управление статусами заказов (Новый -> В работе -> Готов).
*   💬 **Обратная связь:** Чат с клиентом напрямую через бота.
*   🌐 **i18n:** Полная поддержка RU, EN, UK.
*   🐳 **Docker:** Быстрое развёртывание всей инфраструктуры.

---

## 🐳 Быстрый старт (Docker)

1. **Клонирование:**
   ```bash
   git clone https://github.com/serg-akulov/turner-telegram-bot.git
   cd turner-telegram-bot
   ```

2. **Настройка:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env: укажите BOT_TOKEN и пароли
   ```

3. **Запуск:**
   ```bash
   docker compose up -d --build
   ```

**Доступ:**
- **Админка (React):** `http://localhost:45554`
- **Бот:** найдите вашего бота в Telegram и нажмите `/start`

---

## 🤖 Администрирование

### Web-панель
- Управление заказами и смена статусов (с уведомлением клиента).
- Настройка текстов и логики опроса.
- Статистика и переключение языков.

### Telegram
1. Авторизуйтесь: `/iamadmin ВАШ_ПАРОЛЬ`.
2. Получайте уведомления о новых заказах.
3. Отвечайте на сообщения заказа через `Reply`.
4. Команда `/lang` для смены языка.

---

## 📂 Структура проекта

*   `bot.py` — Ядро бота (Aiogram 3).
*   `backend/` — API для админ-панели (FastAPI).
*   `frontend/` — CRM-панель (React + Ant Design).
*   `locales/` — Файлы локализации.
*   `admin.php` — Устаревшая PHP-админка (legacy).

---

## 🛠 Установка без Docker (Legacy)

1. Настройте MySQL базу данных.
2. Запустите `./install.sh` и следуйте инструкциям.
3. Для PHP-админки скопируйте `admin.php` и `php_config.php` в корень веб-сервера.

---

👨‍💻 **Автор:** [Сергей Акулов](https://akulov-dev.ru)
Благодарность [@dedkovd](https://github.com/dedkovd) и [@vionaaru](https://github.com/vionaaru) за помощь с Docker.

MIT License © 2025
