# Author: Sergey Akulov
# GitHub: https://github.com/serg-akulov

import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
    InlineKeyboardButton, InputMediaPhoto, InputMediaDocument
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import database
import i18n

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

class OrderForm(StatesGroup):
    survey = State()

class BroadcastForm(StatesGroup):
    waiting_message = State()

# --- HELPERS ---
def _lang(user_id: int) -> str:
    return database.get_user_language(user_id)

def _admin_lang() -> str:
    cfg = database.get_bot_config()
    aid = cfg.get("admin_chat_id", "0")
    if aid and aid != '0':
        return database.get_user_language(int(aid))
    return 'ru'

async def get_survey_flow():
    cfg = database.get_bot_config()
    flow_raw = cfg.get('survey_flow', '[]')
    if isinstance(flow_raw, str):
        import json
        return json.loads(flow_raw)
    return flow_raw

async def ask_step(message: types.Message, state: FSMContext, step_index: int = 0):
    flow = await get_survey_flow()
    if step_index >= len(flow):
        data = await state.get_data()
        await finalize_order(message, data['order_id'], "")
        await state.clear()
        return

    step = flow[step_index]
    lang = _lang(message.from_user.id)
    
    # Priority: 1. Custom label from Visual Builder 2. Translation key 3. Fallback
    text = step.get('label')
    if not text and step.get('label_key'):
        text = i18n.t(step.get('label_key'), lang)
    if not text:
        text = '...'
    
    kb = None
    if step['type'] == 'photo':
        kb = kb_photo_step_dynamic(lang, step)
    elif step['type'] == 'choice':
        btns = []
        for opt in step.get('options', []):
            opt_text = opt.get('label')
            if not opt_text and opt.get('label_key'):
                opt_text = i18n.t(opt.get('label_key'), lang)
            if not opt_text:
                opt_text = opt.get('val')
                
            btns.append([InlineKeyboardButton(text=opt_text, callback_data=f"flow_val:{opt['val']}")])
        kb = InlineKeyboardMarkup(inline_keyboard=btns)

    await state.update_data(current_step=step_index)
    
    if kb:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")

def kb_photo_step_dynamic(lang, step):
    buttons = [[KeyboardButton(text=i18n.t('btn_photos_done', lang))]]
    is_required = get_config_bool(step.get('required_key')) if step.get('required_key') else False
    if not is_required:
        buttons.append([KeyboardButton(text=i18n.t('btn_skip_photo', lang))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def get_config_bool(key):
    cfg = database.get_bot_config()
    return str(cfg.get(key, '0')) == '1'

def safe_text(message: types.Message, lang: str = 'ru'):
    if message.text: return message.text
    if message.caption: return message.caption
    if message.sticker: return i18n.t('safe_sticker', lang)
    if message.photo: return i18n.t('safe_photo', lang)
    return i18n.t('safe_unknown', lang)

async def forward_message_to_admin(message: types.Message, order_id):
    try:
        admins = database.get_all_admins()
        if not admins:
            lang = _lang(message.from_user.id)
            await message.answer(i18n.t('err_admin_not_set', lang))
            return

        al = _admin_lang()
        header = i18n.t('msg_client_msg_header', al, order_id=order_id)
        for admin_id in admins:
            try:
                if message.text:
                    await bot.send_message(admin_id, header + message.text, parse_mode="HTML")
                else:
                    await message.copy_to(admin_id)
                    await bot.send_message(
                        admin_id,
                        i18n.t('msg_refers_to_order', al, order_id=order_id),
                        parse_mode="HTML"
                    )
            except Exception as e:
                logging.error(f"Deliver error to {admin_id}: {e}")
    except Exception as e:
        logging.error(f"Deliver error: {e}")

# --- KEYBOARDS ---
def kb_photo_step(lang):
    buttons = [[KeyboardButton(text=i18n.t('btn_photos_done', lang))]]
    if not get_config_bool('is_photo_required'):
        buttons.append([KeyboardButton(text=i18n.t('btn_skip_photo', lang))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def kb_work_type(lang):
    buttons = [
        [InlineKeyboardButton(text=i18n.t('btn_type_repair', lang), callback_data="type_repair")],
        [InlineKeyboardButton(text=i18n.t('btn_type_copy', lang), callback_data="type_copy")],
        [InlineKeyboardButton(text=i18n.t('btn_type_drawing', lang), callback_data="type_drawing")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def kb_start_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.t('btn_new_order', lang), callback_data="start_new_order")],
        [InlineKeyboardButton(text=i18n.t('btn_cancel_order', lang), callback_data="start_cancel"),
         InlineKeyboardButton(text=i18n.t('btn_my_orders', lang), callback_data="start_myorders"),
         InlineKeyboardButton(text=i18n.t('btn_lang', lang), callback_data="start_lang")],
    ])

def kb_urgency(lang):
    buttons = [
        [InlineKeyboardButton(text=i18n.t('btn_urgency_high', lang), callback_data="urgency_high")],
        [InlineKeyboardButton(text=i18n.t('btn_urgency_med', lang), callback_data="urgency_med")],
        [InlineKeyboardButton(text=i18n.t('btn_urgency_low', lang), callback_data="urgency_low")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- LOGIC ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    lang = _lang(message.from_user.id)
    user_id = message.from_user.id
    welcome = i18n.t('welcome_msg', lang)
    await message.answer(welcome, reply_markup=kb_start_menu(lang), parse_mode="HTML")

@dp.callback_query(F.data == "start_new_order")
async def cb_new_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    lang = _lang(callback.from_user.id)
    user_id = callback.from_user.id

    database.cancel_old_filling_orders(user_id)

    username = callback.from_user.username or "NoNick"
    full_name = callback.from_user.full_name
    order_id = database.create_order(user_id, username, full_name)

    await state.update_data(order_id=order_id, photo_ids=[], current_step=0)
    await state.set_state(OrderForm.survey)

    label = i18n.t('new_order_label', lang, order_id=order_id)
    await callback.message.edit_text(label, reply_markup=None, parse_mode="Markdown")
    
    await ask_step(callback.message, state, 0)
    await callback.answer()

@dp.callback_query(F.data == "start_cancel")
async def cb_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    lang = _lang(callback.from_user.id)
    database.cancel_old_filling_orders(callback.from_user.id)
    await callback.message.edit_text(i18n.t('msg_order_canceled', lang))
    await callback.answer()

@dp.callback_query(F.data == "start_lang")
async def cb_lang(callback: types.CallbackQuery):
    lang = _lang(callback.from_user.id)
    buttons = []
    for code, label in i18n.SUPPORTED_LANGUAGES.items():
        prefix = '✅ ' if code == lang else ''
        buttons.append([InlineKeyboardButton(text=f"{prefix}{label}", callback_data=f"lang_{code}")])
    await callback.message.edit_text(
        i18n.t('lang_select_prompt', lang), 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    lang = _lang(message.from_user.id)
    database.cancel_old_filling_orders(message.from_user.id)
    await message.answer(i18n.t('msg_order_canceled', lang))

@dp.message(Command("lang"))
async def cmd_lang(message: types.Message):
    lang = _lang(message.from_user.id)
    buttons = []
    for code, label in i18n.SUPPORTED_LANGUAGES.items():
        prefix = '✅ ' if code == lang else ''
        buttons.append([InlineKeyboardButton(text=f"{prefix}{label}", callback_data=f"lang_{code}")])
    await message.answer(
        i18n.t('lang_select_prompt', lang), 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data.startswith("lang_"))
async def process_lang(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[1]
    database.set_user_language(callback.from_user.id, new_lang)
    await callback.message.edit_text(i18n.t('lang_changed', new_lang))
    await callback.answer()

@dp.callback_query(OrderForm.survey, F.data.startswith("flow_val:"))
async def process_choice(callback: types.CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    data = await state.get_data()
    flow = await get_survey_flow()
    step_idx = data.get('current_step', 0)
    if step_idx >= len(flow):
        await callback.answer()
        return
    step = flow[step_idx]
    
    lang = _lang(callback.from_user.id)
    human = val
    for opt in step.get('options', []):
        if opt['val'] == val:
            human = opt.get('label')
            if not human and opt.get('label_key'):
                human = i18n.t(opt.get('label_key'), lang)
            if not human:
                human = val
            break

    database.update_order_data_json(data['order_id'], step['id'], human)
    
    await callback.message.edit_text(i18n.t('label_chosen', lang, human=human))
    await ask_step(callback.message, state, step_idx + 1)
    await callback.answer()

@dp.message(OrderForm.survey)
async def process_survey_message(message: types.Message, state: FSMContext):
    lang = _lang(message.from_user.id)
    data = await state.get_data()
    flow = await get_survey_flow()
    
    step_idx = data.get('current_step', 0)
    if step_idx >= len(flow):
        await state.clear()
        return

    step = flow[step_idx]

    if step['type'] == 'photo':
        if message.photo or (message.document and message.document.mime_type.startswith('image/')):
            p_ids = data.get('photo_ids', [])
            if message.photo:
                p_ids.append(f"p:{message.photo[-1].file_id}")
            else:
                p_ids.append(f"d:{message.document.file_id}")
            await state.update_data(photo_ids=p_ids)
            await message.answer(
                i18n.t('msg_photo_accepted_count', lang, count=len(p_ids)), 
                reply_markup=kb_photo_step_dynamic(lang, step)
            )
            return

        txt = safe_text(message, lang)
        if txt == i18n.t('btn_photos_done', lang):
            if not data.get('photo_ids'):
                await message.answer(i18n.t('err_no_photos_uploaded', lang))
                return
            database.update_order_field(data['order_id'], 'photo_file_id', ",".join(data['photo_ids']))
            await message.answer(i18n.t('msg_photos_accepted', lang), reply_markup=types.ReplyKeyboardRemove())
            await ask_step(message, state, step_idx + 1)
        elif txt == i18n.t('btn_skip_photo', lang):
            is_required = get_config_bool(step.get('required_key')) if step.get('required_key') else False
            if is_required:
                await message.answer(i18n.t('err_photo_required', lang))
            else:
                await message.answer(i18n.t('msg_ok_no_photo', lang), reply_markup=types.ReplyKeyboardRemove())
                await ask_step(message, state, step_idx + 1)
        else:
            await message.answer(i18n.t('err_send_image_not_other', lang))

    elif step['type'] == 'text':
        txt = safe_text(message, lang)
        database.update_order_data_json(data['order_id'], step['id'], txt)
        await ask_step(message, state, step_idx + 1)

async def finalize_order(message, order_id, comment_text):
    lang = _lang(message.from_user.id)
    database.update_order_data_json(order_id, 'comment', comment_text)
    database.finish_order_creation(order_id)
    database.upsert_customer(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(i18n.t('msg_done', lang), parse_mode="Markdown")
    await notify_admin(order_id)

async def notify_admin(order_id):
    admins = database.get_all_admins()
    if not admins:
        return

    al = _admin_lang()
    order = database.get_order(order_id)
    data = order.get('order_data') or {}

    text = i18n.t('msg_new_order_admin', al,
        order_id=order['id'],
        full_name=order['full_name'],
        username=order['username'],
        work_type=data.get('work_type', ''),
        dimensions=data.get('dimensions', ''),
        conditions=data.get('conditions', ''),
        urgency=data.get('urgency', ''),
        comment=data.get('comment', '')
    )
    for admin_id in admins:
        try:
            raw_ids = order['photo_file_id'].split(',') if order['photo_file_id'] else []
            media = []
            for rid in raw_ids:
                if rid.startswith('p:'):
                    media.append(types.InputMediaPhoto(media=rid[2:]))
                elif rid.startswith('d:'):
                    media.append(types.InputMediaDocument(media=rid[2:]))
                else:
                    media.append(types.InputMediaPhoto(media=rid))

            if len(media) > 1:
                await bot.send_media_group(admin_id, media=media)
                await bot.send_message(admin_id, text, parse_mode="HTML")
            elif len(media) == 1:
                m = media[0]
                if isinstance(m, types.InputMediaPhoto):
                    await bot.send_photo(admin_id, m.media, caption=text, parse_mode="HTML")
                else:
                    await bot.send_document(admin_id, m.media, caption=text, parse_mode="HTML")
            else:
                await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Err admin {admin_id}: {e}")

# --- ADMIN ---
@dp.message(Command("iamadmin"))
async def cmd_admin_auth(message: types.Message):
    lang = _lang(message.from_user.id)
    args = message.text.split()
    if len(args) > 1 and args[1] == config.BOT_ADMIN_PASSWORD:
        database.add_admin(message.chat.id, message.from_user.username, message.from_user.full_name, role='superadmin')
        await message.answer(i18n.t('msg_admin_authorized', lang))
    else:
        await message.answer(i18n.t('err_wrong_password', lang))

@dp.message(F.reply_to_message)
async def admin_reply_handler(message: types.Message):
    try:
        if not database.is_admin(message.chat.id): return

        lang = _lang(message.from_user.id)

        orig = message.reply_to_message.caption or message.reply_to_message.text
        if not orig:
            await message.answer(i18n.t('err_no_reply_text', lang))
            return

        match = re.search(r"(?:№|#|No|Num|Заказ|Order)\s*[:#]?\s*(\d+)", orig, re.IGNORECASE)
        if not match:
            await message.answer(i18n.t('err_no_order_number', lang))
            return

        oid = int(match.group(1))
        order = database.get_order(oid)
        if not order:
            await message.answer(i18n.t('err_order_not_found', lang, order_id=oid))
            return

        try:
            if message.text:
                await bot.send_message(
                    order['user_id'],
                    i18n.t('msg_from_master', lang, text=message.text),
                    parse_mode="HTML"
                )
            else:
                await message.copy_to(order['user_id'])
            await message.react([types.ReactionTypeEmoji(emoji="👍")])
        except Exception as e:
            await message.answer(i18n.t('err_send_failed', lang, error=e))
    except Exception as e:
        await message.answer(i18n.t('msg_fatal_error', lang, error=e))

# --- TEMPLATES IN BOT ---
@dp.message(Command("templates"))
async def cmd_templates(message: types.Message):
    if not database.is_admin(message.chat.id): return
    templates = database.get_templates()
    if not templates:
        await message.answer("📋 Нет сохранённых шаблонов.")
        return
    rows = []
    for tpl in templates:
        rows.append([InlineKeyboardButton(
            text=tpl['name'],
            callback_data=f"tpl_show:{tpl['id']}"
        )])
    await message.answer("📋 Шаблоны:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@dp.callback_query(F.data.startswith("tpl_show:"))
async def cb_tpl_show(callback: types.CallbackQuery):
    if not database.is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    tid = int(callback.data.split(":")[1])
    tpl = database.get_template(tid)
    if not tpl:
        await callback.answer("Шаблон не найден", show_alert=True)
        return
    await callback.message.answer(
        f"📋 <b>{tpl['name']}</b>\n\n{tpl['body']}\n\n"
        f"↩️ Reply на сообщение клиента + /sendtpl {tid} <code>номер_заказа</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.message(Command("sendtpl"))
async def cmd_send_template(message: types.Message):
    if not database.is_admin(message.chat.id): return
    lang = _lang(message.from_user.id)
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Формат: /sendtpl template_id order_id")
        return
    try:
        tid, oid = int(args[1]), int(args[2])
    except ValueError:
        await message.answer("⚠️ Неверные ID. Формат: /sendtpl template_id order_id")
        return

    tpl = database.get_template(tid)
    if not tpl:
        await message.answer("Шаблон не найден")
        return
    order = database.get_order(oid)
    if not order:
        await message.answer(i18n.t('err_order_not_found', lang, order_id=oid))
        return

    try:
        await bot.send_message(order['user_id'], i18n.t('msg_from_master', lang, text=tpl['body']), parse_mode="HTML")
        await message.react([types.ReactionTypeEmoji(emoji="👍")])
    except Exception as e:
        await message.answer(i18n.t('err_send_failed', lang, error=e))

# --- MY ORDERS ---
MYORDERS_PER_PAGE = 5

def _build_orders_text(orders, lang):
    status_map = {
        'filling': '📝', 'new': '🔥', 'discussion': '💬',
        'approved': '🛠', 'work': '⚙️', 'done': '✅', 'rejected': '❌'
    }
    lines = [i18n.t('msg_order_history_header', lang)]
    for order in orders:
        emoji = status_map.get(order['status'], '📦')
        date = order['created_at'].strftime('%d.%m.%Y') if order.get('created_at') else ''
        line = f"{emoji} #{order['id']} — {order['status']} — {date}"
        if order.get('price'):
            line += f" — {order['price']} {order.get('price_currency', 'UAH')}"
        lines.append(line)
    return '\n'.join(lines)

def _orders_kb(user_id, page):
    offset = page * MYORDERS_PER_PAGE
    orders = database.get_user_orders(user_id, limit=MYORDERS_PER_PAGE + 1, offset=offset)
    has_next = len(orders) > MYORDERS_PER_PAGE
    orders = orders[:MYORDERS_PER_PAGE]
    rows = []
    if page > 0:
        rows.append(InlineKeyboardButton(text="⬅️", callback_data=f"myorders:{page-1}"))
    if has_next:
        rows.append(InlineKeyboardButton(text="➡️", callback_data=f"myorders:{page+1}"))
    kb = InlineKeyboardMarkup(inline_keyboard=[rows]) if rows else None
    return orders, kb

@dp.message(Command("myorders"))
async def cmd_my_orders(message: types.Message):
    lang = _lang(message.from_user.id)
    orders, kb = _orders_kb(message.from_user.id, 0)
    if not orders:
        await message.answer(i18n.t('msg_no_orders_history', lang))
        return
    await message.answer(_build_orders_text(orders, lang), reply_markup=kb)

@dp.callback_query(F.data == "start_myorders")
async def cb_myorders(callback: types.CallbackQuery):
    lang = _lang(callback.from_user.id)
    orders, kb = _orders_kb(callback.from_user.id, 0)
    if not orders:
        await callback.message.answer(i18n.t('msg_no_orders_history', lang))
        await callback.answer()
        return
    await callback.message.answer(_build_orders_text(orders, lang), reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("myorders:"))
async def cb_myorders_page(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[1])
    lang = _lang(callback.from_user.id)
    orders, kb = _orders_kb(callback.from_user.id, page)
    if not orders:
        await callback.answer(i18n.t('msg_no_orders_history', lang), show_alert=True)
        return
    text = _build_orders_text(orders, lang)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()

# --- PRICE ACCEPT/REJECT ---
@dp.callback_query(F.data.startswith("price_accept:"))
async def cb_price_accept(callback: types.CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    database.update_price_status(order_id, 'accepted')
    order = database.get_order(order_id)
    lang = _lang(order['user_id'])
    await callback.message.edit_text(
        callback.message.text + '\n\n' + i18n.t('msg_price_accepted', lang, order_id=order_id)
    )
    admins = database.get_all_admins()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, i18n.t('msg_price_accepted_admin', 'ru', order_id=order_id))
        except Exception:
            pass

@dp.callback_query(F.data.startswith("price_reject:"))
async def cb_price_reject(callback: types.CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    database.update_price_status(order_id, 'rejected')
    order = database.get_order(order_id)
    lang = _lang(order['user_id'])
    await callback.message.edit_text(
        callback.message.text + '\n\n' + i18n.t('msg_price_rejected', lang, order_id=order_id)
    )
    admins = database.get_all_admins()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, i18n.t('msg_price_rejected_admin', 'ru', order_id=order_id))
        except Exception:
            pass

# --- BROADCAST ---
@dp.message(Command("broadcast"))
async def cmd_broadcast_start(message: types.Message):
    if not database.is_admin(message.chat.id):
        return
    lang = _admin_lang()
    await message.answer(i18n.t('msg_broadcast_prompt', lang))
    await BroadcastForm.waiting_message.set()

@dp.message(BroadcastForm.waiting_message)
async def process_broadcast(message: types.Message, state: FSMContext):
    if not database.is_admin(message.chat.id):
        await state.clear()
        return
    user_ids = database.get_all_customer_user_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, message.text)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(i18n.t('msg_broadcast_sent', 'ru', count=sent, failed=failed))
    await state.clear()

# --- DEADLINE REMINDER ---
async def check_deadline_reminders():
    orders = database.get_upcoming_deadlines(days_ahead=1)
    for order in orders:
        lang = database.get_user_language(order['user_id'])
        deadline_str = str(order['deadline'])
        try:
            await bot.send_message(
                order['user_id'],
                i18n.t('msg_deadline_reminder', lang, order_id=order['id'], deadline=deadline_str)
            )
        except Exception:
            pass

# --- SMART INTERCEPTOR ---
@dp.message()
async def user_chat_handler(message: types.Message):
    await check_lost_state(message, None)

async def check_lost_state(message, state):
    lang = _lang(message.from_user.id)
    filling_id = database.get_active_order_id(message.from_user.id)

    if filling_id:
        if state:
            data = await state.get_data()
            if 'current_step' not in data:
                await state.update_data(order_id=filling_id, photo_ids=[], current_step=0)
                await state.set_state(OrderForm.survey)
                await ask_step(message, state, 0)
                return
            await process_survey_message(message, state)
        else:
            state = FSMContext(storage=dp.storage, key=types.StorageKey(bot.id, message.chat.id, message.from_user.id))
            await state.update_data(order_id=filling_id, photo_ids=[], current_step=0)
            await state.set_state(OrderForm.survey)
            await ask_step(message, state, 0)
        return

    order_id = database.get_user_last_active_order(message.from_user.id)
    if order_id:
        await forward_message_to_admin(message, order_id)
    else:
        await message.answer(i18n.t('err_no_active_order', lang))

async def main():
    i18n.refresh_db_overrides()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_deadline_reminders, 'cron', hour=9)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
