SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Таблица настроек подключения (системная)
CREATE TABLE IF NOT EXISTS `settings` (
  `key_name` varchar(50) NOT NULL,
  `value_text` text DEFAULT NULL,
  PRIMARY KEY (`key_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Таблица заказов
CREATE TABLE IF NOT EXISTS `orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(20) NOT NULL,
  `username` varchar(100) DEFAULT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `status` varchar(50) DEFAULT 'filling',
  `order_data` JSON DEFAULT NULL,
  `photo_file_id` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `internal_note` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Таблица текстов бота (Конструктор)
CREATE TABLE IF NOT EXISTS `bot_config` (
  `cfg_key` varchar(100) NOT NULL,
  `cfg_value` text NOT NULL,
  `description` varchar(255) DEFAULT '',
  PRIMARY KEY (`cfg_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Заполняем дефолтные тексты (чтобы бот не молчал)
INSERT IGNORE INTO `bot_config` (`cfg_key`, `cfg_value`, `description`) VALUES
('welcome_msg', 'Привет! 👋 Я принимаю заказы на токарные работы. Опишите заказ и я отвечу вам здесь по срокам и цене.', 'Приветствие'),
('step_photo_text', '📷 *Шаг 1.* Загрузите фото детали ИЛИ чертеж/набросок от руки', 'Текст вопроса про фото'),
('btn_skip_photo', 'Нет фото / Пропустить', 'Кнопка пропуска фото'),
('is_photo_required', '1', '1 = Фото обязательно, 0 = Можно пропустить'),
('step_type_text', '🛠 *Шаг 2.* Что нужно сделать?', 'Вопрос про тип работы'),
('btn_type_repair', '🛠 Восстановление детали', 'Кнопка: Ремонт'),
('btn_type_copy', '⚙️ Копия по образцу', 'Кнопка: Копия'),
('btn_type_drawing', '📐 Деталь по чертежу (эскизу)', 'Кнопка: Чертеж'),
('step_dim_text', '📏 *Шаг 3. Размеры*\nНапишите размеры (хотя бы примерно) и КОЛИЧЕСТВО деталей.\n\n👉Пример: Вал диам. 20мм, длина 100мм, 2 штуки.', 'Вопрос про размеры'),
('step_cond_text', '⚙️ *Шаг 4. Специфика детали*\nГде работает деталь? (Нужно для выбора материала).', 'Вопрос про условия'),
('btn_cond_rotation', '💫 Вращение', 'Кнопка условия 1'),
('btn_cond_static', '🧱 Неподвижно', 'Кнопка условия 2'),
('btn_cond_impact', '🔨 Ударная нагрузка', 'Кнопка условия 3'),
('btn_cond_unknown', '🤷‍♂️ Не знаю', 'Кнопка условия 4'),
('step_urgency_text', '⏳ *Шаг 5. Срочность*', 'Вопрос про сроки'),
('btn_urgency_high', '🔥 СРОЧНО (Цена x2)', 'Кнопка: Срочно'),
('btn_urgency_med', '🗓 Стандарт (2-3 дня)', 'Кнопка: Стандарт'),
('btn_urgency_low', '🐢 Не к спеху', 'Кнопка: Долго'),
('step_final_text', '✍️ *Финал.*\nНапишите комментарий если Вам есть что добавить и уточнить к заказу.', 'Вопрос в конце'),
('msg_done', '✅ *Заказ принят!* Я отвечу в этот чат в ближайшее время.', 'Сообщение об успехе'),
('err_photo_required', '⚠️ Я не могу принять заказ без фото. Пожалуйста, пришлите фото.', 'Ошибка: нет фото'),
('admin_chat_id', '0', 'ID админа (заполнится само)'),
('msg_order_canceled', '❌ Заказ отменен. Отправьте /start для нового.', 'Сообщение об отмене'),
('err_admin_not_set', '⚠️ Администратор еще не настроен.', 'Ошибка: админ не задан'),
('err_no_active_order', 'У вас нет активных заказов. Отправьте /start для нового.', 'Ошибка: нет активного заказа'),
('step_extra_text', '📝 *Дополнительно*\nЕсть ли еще что-то важное по детали?', 'Дополнительный вопрос'),
('step_extra_enabled', '0', '1 = Доп. вопрос включен, 0 = Выключен');

-- Таблица языковых предпочтений пользователей
CREATE TABLE IF NOT EXISTS `user_prefs` (
  `user_id` bigint(20) NOT NULL,
  `language` varchar(5) NOT NULL DEFAULT 'ru',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;