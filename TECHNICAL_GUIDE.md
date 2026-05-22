# 🏗 Технічний Посібник (Technical Guide)

Цей документ призначений для розробників та системних адміністраторів для підтримки та розгортання проекту.

---

## 1. Архітектура системи

Проект складається з 4 основних компонентів, що працюють у Docker:

1.  **Bot (Python/aiogram)**: Telegram-бот для взаємодії з клієнтами.
2.  **Backend (Python/FastAPI)**: REST API для адмін-панелі.
3.  **Frontend (React/Ant Design)**: Інтерфейс адміністратора.
4.  **Database (MySQL 8)**: Зберігання замовлень, налаштувань та клієнтів.

---

## 2. Розгортання (Deployment)

### Вимоги:
*   Docker & Docker Compose
*   Telegram Bot Token (від @BotFather)

### Кроки запуску:
1. Створіть файл `.env` на основі `.env.example`.
2. Заповніть `BOT_TOKEN`, `DB_PASS`, `ADMIN_PANEL_PASSWORD`.
3. Запустіть контейнери:
   ```bash
   docker-compose up -d --build
   ```

### Порти за замовчуванням:
*   Frontend: `3000` (або замаплений у compose)
*   Backend API: `8000`
*   MySQL: `3306`

---

## 3. Робота з базою даних

### Основні таблиці:
*   `orders`: Замовлення. Поле `order_data` (JSON) зберігає динамічні відповіді з опитування.
*   `bot_config`: Тексти бота та структура опитування (ключ `survey_flow`).
*   `customers`: CRM дані клієнтів.
*   `admins`: Список chat_id адміністраторів.

### Оновлення структури опитування:
Структура опитування зберігається як JSON-масив у таблиці `bot_config` (ключ `survey_flow`). Кожен об'єкт має:
*   `id`: Ключ у JSON замовлення.
*   `type`: `text`, `choice` або `photo`.
*   `label`: Текст питання.
*   `options`: (для choice) Варіанти відповідей.

---

## 4. Обслуговування та логи

Перегляд логів конкретного сервісу:
```bash
docker logs turner-bot --tail 50 -f
docker logs turner-backend --tail 50 -f
```

Перезапуск системи:
```bash
docker-compose restart
```

### Резервне копіювання бази:
```bash
docker exec turner-mysql mysqldump -u turner_user -p turner_db > backup.sql
```

---

## 5. Безпека
*   Токени доступу (JWT) видаються на 24 години.
*   Додано `Axios Interceptor` на фронтенді для автоматичного виходу при 401 помилці.
*   Бот захищений паролем (`/iamadmin`).
