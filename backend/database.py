# Author: Sergey Akulov
# GitHub: https://github.com/serg-akulov

import pymysql
import config
import json

def get_connection():
    return pymysql.connect(
        host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASS,
        database=config.DB_NAME, cursorclass=pymysql.cursors.DictCursor, autocommit=True
    )

def get_bot_config():
    conn = get_connection()
    cfg = {}
    with conn.cursor() as cursor:
        cursor.execute("SELECT key_name, value_text FROM settings")
        for row in cursor.fetchall(): cfg[row['key_name']] = row['value_text']
        cursor.execute("SELECT cfg_key, cfg_value FROM bot_config")
        for row in cursor.fetchall(): cfg[row['cfg_key']] = row['cfg_value']
    conn.close()
    return cfg

def update_setting(key, val):
    conn = get_connection()
    with conn.cursor() as cur: cur.execute("UPDATE settings SET value_text=%s WHERE key_name=%s", (val, key))
    conn.close()

def create_order(user_id, username, full_name):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO orders (user_id, username, full_name, status) VALUES (%s, %s, %s, 'filling')", 
            (user_id, username, full_name)
        )
        oid = cur.lastrowid
    conn.close()
    return oid

def update_order_field(oid, field, val):
    conn = get_connection()
    with conn.cursor() as cur: cur.execute(f"UPDATE orders SET {field}=%s WHERE id=%s", (val, oid))
    conn.close()

def update_order_data_json(oid, key, val):
    """Обновляет значение в JSON-поле order_data"""
    conn = get_connection()
    with conn.cursor() as cur:
        # Проверяем, не пустой ли JSON
        cur.execute("SELECT order_data FROM orders WHERE id=%s", (oid,))
        current_data = cur.fetchone()['order_data']
        if current_data is None:
            cur.execute("UPDATE orders SET order_data = JSON_OBJECT(%s, %s) WHERE id=%s", (key, val, oid))
        else:
            cur.execute(
                "UPDATE orders SET order_data = JSON_SET(order_data, %s, %s) WHERE id=%s", 
                (f"$.{key}", val, oid)
            )
    conn.close()

def finish_order_creation(oid):
    conn = get_connection()
    with conn.cursor() as cur: cur.execute("UPDATE orders SET status='new' WHERE id=%s", (oid,))
    conn.close()

def get_order(oid):
    conn = get_connection()
    with conn.cursor() as cur: 
        cur.execute("SELECT * FROM orders WHERE id=%s", (oid,))
        res = cur.fetchone()
    conn.close()
    if res:
        data = res.get('order_data')
        if data:
            if isinstance(data, (str, bytes)):
                try:
                    res['order_data'] = json.loads(data)
                except Exception:
                    res['order_data'] = {}
            elif isinstance(data, dict):
                pass
            else:
                res['order_data'] = {}
        else:
            res['order_data'] = {}
    return res

def get_active_order_id(user_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM orders WHERE user_id=%s AND status='filling' ORDER BY id DESC LIMIT 1", (user_id,))
        res = cur.fetchone()
    conn.close()
    return res['id'] if res else None

def get_user_last_active_order(user_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM orders WHERE user_id=%s AND status IN "
            "('new','discussion','approved','work') ORDER BY id DESC LIMIT 1", 
            (user_id,)
        )
        res = cur.fetchone()
    conn.close()
    return res['id'] if res else None

# --- ИСПРАВЛЕННАЯ ФУНКЦИЯ ---
def cancel_old_filling_orders(user_id):
    """Помечает все старые черновики как rejected (отменен/отказ)"""
    conn = get_connection()
    with conn.cursor() as cur:
        # БЫЛО: status='canceled' (Ошибка!)
        # СТАЛО: status='rejected' (Правильно!)
        cur.execute("UPDATE orders SET status='rejected' WHERE user_id=%s AND status='filling'", (user_id,))
    conn.close()

# --- НОВЫЕ ФУНКЦИИ ДЛЯ FASTAPI ---
DEFAULT_LIMIT = 20

def get_orders_paginated(limit=DEFAULT_LIMIT, offset=0, status_filter=None):
    """Получить заказы с пагинацией"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if status_filter:
                cur.execute("""
                    SELECT * FROM orders
                    WHERE status = %s
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                """, (status_filter, limit, offset))
            else:
                cur.execute("""
                    SELECT * FROM orders
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
            orders = cur.fetchall()
            
            # Парсим JSON для каждого заказа
            for order in orders:
                data = order.get('order_data')
                if data:
                    if isinstance(data, (str, bytes)):
                        try:
                            order['order_data'] = json.loads(data)
                        except Exception:
                            order['order_data'] = {}
                    elif isinstance(data, dict):
                        pass # Already a dict
                    else:
                        order['order_data'] = {}
                else:
                    order['order_data'] = {}
            
            return orders
    finally:
        conn.close()

def get_order_statistics():
    """Получить статистику заказов"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Всего заказов
            cur.execute("SELECT COUNT(*) as total FROM orders")
            total = cur.fetchone()['total']

            # Новых заказов
            cur.execute("SELECT COUNT(*) as new FROM orders WHERE status = 'new'")
            new = cur.fetchone()['new']

            # Активных заказов (новые + в работе + обсуждение)
            cur.execute("""
                SELECT COUNT(*) as active FROM orders
                WHERE status IN ('new', 'discussion', 'approved', 'work')
            """)
            active = cur.fetchone()['active']

            return {
                "total_orders": total,
                "new_orders": new,
                "active_orders": active
            }
    finally:
        conn.close()

def delete_all_orders():
    """Удалить все заказы"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE orders")
    finally:
        conn.close()

def update_bot_config(key, value):
    """Обновить настройку бота в таблице bot_config"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bot_config (cfg_key, cfg_value, description)
                VALUES (%s, %s, '')
                ON DUPLICATE KEY UPDATE cfg_value = %s
            """, (key, value, value))
    finally:
        conn.close()

def get_user_language(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT language FROM user_prefs WHERE user_id=%s", (user_id,))
            res = cur.fetchone()
        return res['language'] if res else 'ru'
    except Exception:
        return 'ru'
    finally:
        conn.close()

def set_user_language(user_id, lang):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user_prefs (user_id, language) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE language=%s",
                (user_id, lang, lang)
            )
    finally:
        conn.close()

# --- ФУНКЦИИ ДЛЯ БИЗНЕС-ФИЧ ---

def set_order_price(order_id, price, currency='UAH'):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE orders SET price=%s, price_currency=%s, price_status='pending' WHERE id=%s",
                (price, currency, order_id)
            )
    finally:
        conn.close()

def update_price_status(order_id, status):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE orders SET price_status=%s WHERE id=%s", (status, order_id))
    finally:
        conn.close()

def set_order_deadline(order_id, deadline_date):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE orders SET deadline=%s WHERE id=%s", (deadline_date, order_id))
    finally:
        conn.close()

def get_upcoming_deadlines(days_ahead=1):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM orders
                WHERE deadline IS NOT NULL
                AND deadline <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
                AND deadline >= CURDATE()
                AND status NOT IN ('done', 'rejected', 'filling')
            """, (days_ahead,))
            return cur.fetchall()
    finally:
        conn.close()

def mark_order_completed(order_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE orders SET status='done', completed_at=NOW() WHERE id=%s",
                (order_id,)
            )
    finally:
        conn.close()

def upsert_customer(user_id, username, full_name):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO customers (user_id, username, full_name)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE username=%s, full_name=%s
            """, (user_id, username, full_name, username, full_name))
    finally:
        conn.close()

def update_customer_profile(user_id, phone=None, email=None, notes=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            parts, vals = [], []
            if phone is not None:
                parts.append("phone=%s"); vals.append(phone)
            if email is not None:
                parts.append("email=%s"); vals.append(email)
            if notes is not None:
                parts.append("notes=%s"); vals.append(notes)
            if not parts:
                return
            vals.append(user_id)
            cur.execute(f"UPDATE customers SET {', '.join(parts)} WHERE user_id=%s", vals)
    finally:
        conn.close()

def get_customer(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM customers WHERE user_id=%s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()

def get_all_customers(limit=50, offset=0):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM customers ORDER BY IFNULL(last_order_at, '1970-01-01') DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            return cur.fetchall()
    finally:
        conn.close()

def get_customers_count():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM customers")
            return cur.fetchone()['total']
    finally:
        conn.close()

def recalculate_customer_stats(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE customers c SET
                    total_orders = (SELECT COUNT(*) FROM orders WHERE user_id=c.user_id AND status NOT IN ('filling', 'rejected')),
                    total_spent = COALESCE((SELECT SUM(price) FROM orders WHERE user_id=c.user_id AND price_status='accepted'), 0),
                    last_order_at = (SELECT MAX(created_at) FROM orders WHERE user_id=c.user_id)
                WHERE c.user_id = %s
            """, (user_id,))
    finally:
        conn.close()

def add_admin(chat_id, username=None, full_name=None, role='admin'):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO admins (chat_id, username, full_name, role)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE username=%s, full_name=%s
            """, (chat_id, username, full_name, role, username, full_name))
    finally:
        conn.close()

def remove_admin(chat_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM admins WHERE chat_id=%s", (chat_id,))
    finally:
        conn.close()

def get_all_admins():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM admins")
            return cur.fetchall()
    finally:
        conn.close()

def is_admin(chat_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM admins WHERE chat_id=%s LIMIT 1", (chat_id,))
            return cur.fetchone() is not None
    finally:
        conn.close()

def get_user_orders(user_id, limit=10, offset=0):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, status, order_data, price, price_currency, deadline, created_at
                FROM orders WHERE user_id=%s
                ORDER BY id DESC LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
            orders = cur.fetchall()
            for order in orders:
                data = order.get('order_data')
                if data and isinstance(data, (str, bytes)):
                    try:
                        order['order_data'] = json.loads(data)
                    except Exception:
                        order['order_data'] = {}
            return orders
    finally:
        conn.close()

def get_analytics(date_from=None, date_to=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            where = ""
            params = []
            if date_from:
                where += " AND created_at >= %s"; params.append(date_from)
            if date_to:
                where += " AND created_at <= %s"; params.append(date_to)

            cur.execute(f"SELECT COUNT(*) as total FROM orders WHERE 1=1 {where}", params)
            total = cur.fetchone()['total']

            cur.execute(f"SELECT COALESCE(SUM(price),0) as revenue FROM orders WHERE price_status='accepted' {where}", params)
            revenue = float(cur.fetchone()['revenue'])

            cur.execute(f"SELECT COALESCE(AVG(price),0) as avg_check FROM orders WHERE price_status='accepted' {where}", params)
            avg_check = float(cur.fetchone()['avg_check'])

            cur.execute(f"""
                SELECT COALESCE(AVG(TIMESTAMPDIFF(HOUR, created_at, completed_at)),0) as avg_hours
                FROM orders WHERE completed_at IS NOT NULL {where}
            """, params)
            avg_hours = float(cur.fetchone()['avg_hours'])

            cur.execute(f"""
                SELECT status, COUNT(*) as cnt FROM orders WHERE 1=1 {where} GROUP BY status
            """, params)
            by_status = {row['status']: row['cnt'] for row in cur.fetchall()}

            return {
                "total_orders": total,
                "revenue": revenue,
                "avg_check": avg_check,
                "avg_completion_hours": round(avg_hours, 1),
                "by_status": by_status
            }
    finally:
        conn.close()

def get_orders_for_export(status_filter=None, date_from=None, date_to=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            where, params = [], []
            if status_filter:
                where.append("status=%s"); params.append(status_filter)
            if date_from:
                where.append("created_at >= %s"); params.append(date_from)
            if date_to:
                where.append("created_at <= %s"); params.append(date_to)
            clause = (" WHERE " + " AND ".join(where)) if where else ""
            cur.execute(f"SELECT * FROM orders{clause} ORDER BY id DESC", params)
            orders = cur.fetchall()
            for order in orders:
                data = order.get('order_data')
                if data and isinstance(data, (str, bytes)):
                    try:
                        order['order_data'] = json.loads(data)
                    except Exception:
                        order['order_data'] = {}
            return orders
    finally:
        conn.close()

def get_all_customer_user_ids():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT user_id FROM orders WHERE status NOT IN ('filling', 'rejected')")
            return [row['user_id'] for row in cur.fetchall()]
    finally:
        conn.close()

def create_template(name, body):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO templates (name, body) VALUES (%s, %s)", (name, body))
            return cur.lastrowid
    finally:
        conn.close()

def get_templates():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM templates ORDER BY id DESC")
            return cur.fetchall()
    finally:
        conn.close()

def get_template(template_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM templates WHERE id=%s", (template_id,))
            return cur.fetchone()
    finally:
        conn.close()

def update_template(template_id, name=None, body=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            parts, vals = [], []
            if name is not None:
                parts.append("name=%s"); vals.append(name)
            if body is not None:
                parts.append("body=%s"); vals.append(body)
            if not parts:
                return
            vals.append(template_id)
            cur.execute(f"UPDATE templates SET {', '.join(parts)} WHERE id=%s", vals)
    finally:
        conn.close()

def delete_template(template_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM templates WHERE id=%s", (template_id,))
    finally:
        conn.close()