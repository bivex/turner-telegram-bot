# Author: Sergey Akulov
# GitHub: https://github.com/serg-akulov

import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

import config
import database
import i18n

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

class OrderForm(StatesGroup):
    photo = State()
    work_type = State()
    dimensions = State()
    conditions = State()
    urgency = State()
    extra_q = State()
    comment = State()

# --- HELPERS ---
def _lang(user_id: int) -> str:
    return database.get_user_language(user_id)

def _admin_lang() -> str:
    cfg = database.get_bot_config()
    aid = cfg.get("admin_chat_id", "0")
    if aid and aid != '0':
        return database.get_user_language(int(aid))
    return 'ru'

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
        cfg = database.get_bot_config()
        admin_id = cfg.get("admin_chat_id", "0")
        if admin_id and admin_id != '0':
            al = _admin_lang()
            header = i18n.t('msg_client_msg_header', al, order_id=order_id)
            if message.text:
                await bot.send_message(admin_id, header + message.text, parse_mode="HTML")
            else:
                await message.copy_to(admin_id)
                await bot.send_message(admin_id, i18n.t('msg_refers_to_order', al, order_id=order_id), parse_mode="HTML")
        else:
            lang = _lang(message.from_user.id)
            await message.answer(i18n.t('err_admin_not_set', lang))
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

    await state.update_data(order_id=order_id, photo_ids=[])

    label = i18n.t('new_order_label', lang, order_id=order_id)
    await callback.message.edit_text(f"{label}\n\n{i18n.t('step_photo_text', lang)}", reply_markup=None, parse_mode="Markdown")
    await callback.message.answer(i18n.t('step_photo_text', lang), reply_markup=kb_photo_step(lang), parse_mode="Markdown")
    await state.set_state(OrderForm.photo)
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
    await callback.message.edit_text(i18n.t('lang_select_prompt', lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
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
    await message.answer(i18n.t('lang_select_prompt', lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("lang_"))
async def process_lang(callback: types.CallbackQuery):
    new_lang = callback.data.split("_")[1]
    database.set_user_language(callback.from_user.id, new_lang)
    await callback.message.edit_text(i18n.t('lang_changed', new_lang))
    await callback.answer()

# 1. PHOTO
@dp.message(OrderForm.photo, F.photo | F.document)
async def process_photo(message: types.Message, state: FSMContext):
    lang = _lang(message.from_user.id)
    data = await state.get_data()
    p_ids = data.get('photo_ids', [])

    if message.photo:
        p_ids.append(f"p:{message.photo[-1].file_id}")
    elif message.document and message.document.mime_type.startswith('image/'):
        p_ids.append(f"d:{message.document.file_id}")
    else:
        await message.answer(i18n.t('err_send_image_not_other', lang))
        return

    await state.update_data(photo_ids=p_ids)
    await message.answer(i18n.t('msg_photo_accepted_count', lang, count=len(p_ids)), reply_markup=kb_photo_step(lang))

@dp.message(OrderForm.photo)
async def process_photo_done(message: types.Message, state: FSMContext):
    lang = _lang(message.from_user.id)
    txt = safe_text(message, lang)
    data = await state.get_data()
    p_ids = data.get('photo_ids', [])
    photos_done_btn = i18n.t('btn_photos_done', lang)
    skip_btn = i18n.t('btn_skip_photo', lang)

    if txt == photos_done_btn:
        if not p_ids:
            await message.answer(i18n.t('err_no_photos_uploaded', lang))
            return
        database.update_order_field(data['order_id'], 'photo_file_id', ",".join(p_ids))
        await message.answer(i18n.t('msg_photos_accepted', lang), reply_markup=types.ReplyKeyboardRemove())
        await ask_work_type(message, state)

    elif txt == skip_btn:
        if get_config_bool('is_photo_required'):
            await message.answer(i18n.t('err_photo_required', lang))
        else:
            await message.answer(i18n.t('msg_ok_no_photo', lang), reply_markup=types.ReplyKeyboardRemove())
            await ask_work_type(message, state)
    else:
        if get_config_bool('is_photo_required') and not p_ids:
            await message.answer(i18n.t('err_photo_required', lang))
            return
        await check_lost_state(message, state)

async def ask_work_type(message, state):
    lang = _lang(message.from_user.id)
    await message.answer(i18n.t('step_type_text', lang), reply_markup=kb_work_type(lang), parse_mode="Markdown")
    await state.set_state(OrderForm.work_type)

# 2. WORK TYPE
@dp.callback_query(OrderForm.work_type)
async def process_work_type(callback: types.CallbackQuery, state: FSMContext):
    lang = _lang(callback.from_user.id)
    map_types = {'type_repair': 'btn_type_repair', 'type_copy': 'btn_type_copy', 'type_drawing': 'btn_type_drawing'}
    key = map_types.get(callback.data)
    human = i18n.t(key, lang)

    database.update_order_field((await state.get_data())['order_id'], 'work_type', human)

    await callback.message.edit_text(i18n.t('label_chosen', lang, human=human))
    await callback.message.answer(i18n.t('step_dim_text', lang), parse_mode="Markdown")
    await state.set_state(OrderForm.dimensions)

# 3. DIMENSIONS
@dp.message(OrderForm.dimensions)
async def process_dimensions(message: types.Message, state: FSMContext):
    lang = _lang(message.from_user.id)
    txt = safe_text(message, lang)
    database.update_order_field((await state.get_data())['order_id'], 'dimensions_info', txt)

    btns = [
        [InlineKeyboardButton(text=i18n.t('btn_cond_rotation', lang), callback_data="cond_rotation")],
        [InlineKeyboardButton(text=i18n.t('btn_cond_static', lang), callback_data="cond_static")],
        [InlineKeyboardButton(text=i18n.t('btn_cond_impact', lang), callback_data="cond_impact")],
        [InlineKeyboardButton(text=i18n.t('btn_cond_unknown', lang), callback_data="cond_unknown")]
    ]
    await message.answer(i18n.t('step_cond_text', lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=btns), parse_mode="Markdown")
    await state.set_state(OrderForm.conditions)

# 4. CONDITIONS
@dp.callback_query(OrderForm.conditions)
async def process_conditions(callback: types.CallbackQuery, state: FSMContext):
    lang = _lang(callback.from_user.id)
    map_cond = {'cond_rotation': 'btn_cond_rotation', 'cond_static': 'btn_cond_static', 'cond_impact': 'btn_cond_impact', 'cond_unknown': 'btn_cond_unknown'}
    human = i18n.t(map_cond.get(callback.data), lang)

    database.update_order_field((await state.get_data())['order_id'], 'conditions', human)

    await callback.message.edit_text(i18n.t('label_chosen', lang, human=human))
    await callback.message.answer(i18n.t('step_urgency_text', lang), reply_markup=kb_urgency(lang), parse_mode="Markdown")
    await state.set_state(OrderForm.urgency)

# 5. URGENCY
@dp.callback_query(OrderForm.urgency)
async def process_urgency(callback: types.CallbackQuery, state: FSMContext):
    lang = _lang(callback.from_user.id)
    map_urg = {'urgency_high': 'btn_urgency_high', 'urgency_med': 'btn_urgency_med', 'urgency_low': 'btn_urgency_low'}
    human = i18n.t(map_urg.get(callback.data), lang)

    database.update_order_field((await state.get_data())['order_id'], 'urgency', human)
    await callback.message.edit_text(i18n.t('label_chosen', lang, human=human))

    if get_config_bool('step_extra_enabled'):
        await callback.message.answer(i18n.t('step_extra_text', lang), parse_mode="Markdown")
        await state.set_state(OrderForm.extra_q)
    else:
        await ask_final(callback.message, state)

@dp.message(OrderForm.extra_q)
async def process_extra(message: types.Message, state: FSMContext):
    lang = _lang(message.from_user.id)
    txt = safe_text(message, lang)
    await state.update_data(temp_comment=i18n.t('msg_extra_prefix', lang, text=txt))
    await ask_final(message, state)

async def ask_final(message, state):
    lang = _lang(message.from_user.id)
    await message.answer(i18n.t('step_final_text', lang), parse_mode="Markdown")
    await state.set_state(OrderForm.comment)

# 6. FINAL
@dp.message(OrderForm.comment)
async def process_comment(message: types.Message, state: FSMContext):
    lang = _lang(message.from_user.id)
    data = await state.get_data()
    comm = safe_text(message, lang)
    final_comm = data.get('temp_comment', '') + comm
    await finalize_order(message, data['order_id'], final_comm)
    await state.clear()

async def finalize_order(message, order_id, comment_text):
    lang = _lang(message.from_user.id)
    database.update_order_field(order_id, 'comment', comment_text)
    database.finish_order_creation(order_id)
    await message.answer(i18n.t('msg_done', lang), parse_mode="Markdown")
    await notify_admin(order_id)

async def notify_admin(order_id):
    cfg = database.get_bot_config()
    aid = cfg.get("admin_chat_id", "0")
    if not aid or aid == '0': return

    al = _admin_lang()
    order = database.get_order(order_id)
    text = i18n.t('msg_new_order_admin', al,
        order_id=order['id'],
        full_name=order['full_name'],
        username=order['username'],
        work_type=order['work_type'] or '',
        dimensions=order['dimensions_info'] or '',
        conditions=order['conditions'] or '',
        urgency=order['urgency'] or '',
        comment=order['comment'] or ''
    )
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
            await bot.send_media_group(aid, media=media)
            await bot.send_message(aid, text, parse_mode="HTML")
        elif len(media) == 1:
            m = media[0]
            if isinstance(m, types.InputMediaPhoto):
                await bot.send_photo(aid, m.media, caption=text, parse_mode="HTML")
            else:
                await bot.send_document(aid, m.media, caption=text, parse_mode="HTML")
        else:
            await bot.send_message(aid, text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Err admin: {e}")

# --- ADMIN ---
@dp.message(Command("iamadmin"))
async def cmd_admin_auth(message: types.Message):
    lang = _lang(message.from_user.id)
    args = message.text.split()
    if len(args) > 1 and args[1] == config.BOT_ADMIN_PASSWORD:
        database.update_bot_config("admin_chat_id", str(message.chat.id))
        await message.answer(i18n.t('msg_admin_authorized', lang))
    else:
        await message.answer(i18n.t('err_wrong_password', lang))

@dp.message(F.reply_to_message)
async def admin_reply_handler(message: types.Message):
    try:
        cfg = database.get_bot_config()
        aid = str(cfg.get("admin_chat_id", "0"))
        if str(message.chat.id) != aid: return

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
                await bot.send_message(order['user_id'], i18n.t('msg_from_master', lang, text=message.text), parse_mode="HTML")
            else:
                await message.copy_to(order['user_id'])
            await message.react([types.ReactionTypeEmoji(emoji="👍")])
        except Exception as e:
            await message.answer(i18n.t('err_send_failed', lang, error=e))
    except Exception as e:
        await message.answer(i18n.t('msg_fatal_error', lang, error=e))

# --- SMART INTERCEPTOR ---
@dp.message()
async def user_chat_handler(message: types.Message):
    await check_lost_state(message, None)

async def check_lost_state(message, state):
    lang = _lang(message.from_user.id)
    filling_id = database.get_active_order_id(message.from_user.id)

    if filling_id:
        order = database.get_order(filling_id)
        has_photos = order['photo_file_id'] is not None and len(str(order['photo_file_id'])) > 5

        if not has_photos:
            if message.photo or (message.document and message.document.mime_type.startswith('image/')):
                if state: await state.set_state(OrderForm.photo)
                await process_photo(message, state or FSMContext(storage=dp.storage, key=types.StorageKey(bot.id, message.chat.id, message.from_user.id)))
                return

            if get_config_bool('is_photo_required'):
                await message.answer(i18n.t('err_photo_required', lang))
                return

            if state:
                await state.update_data(order_id=filling_id)
                await state.set_state(OrderForm.photo)
            await process_photo_done(message, state or FSMContext(storage=dp.storage, key=types.StorageKey(bot.id, message.chat.id, message.from_user.id)))
            return

        if not order['work_type']:
            await message.answer(i18n.t('msg_restoring_type', lang), reply_markup=kb_work_type(lang))
            if state: await state.set_state(OrderForm.work_type)
            return

        if not order['dimensions_info']:
            database.update_order_field(filling_id, 'dimensions_info', safe_text(message, lang))
            btns = [[InlineKeyboardButton(text=i18n.t('btn_cond_rotation', lang), callback_data="cond_rotation")], [InlineKeyboardButton(text=i18n.t('btn_cond_static', lang), callback_data="cond_static")], [InlineKeyboardButton(text=i18n.t('btn_cond_unknown', lang), callback_data="cond_unknown")]]
            await message.answer(i18n.t('msg_dimensions_recorded', lang, dimensions=safe_text(message, lang)), reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))
            if state: await state.set_state(OrderForm.conditions)
            return

        await finalize_order(message, filling_id, safe_text(message, lang))
        return

    order_id = database.get_user_last_active_order(message.from_user.id)
    if order_id:
        await forward_message_to_admin(message, order_id)
    else:
        await message.answer(i18n.t('err_no_active_order', lang))

async def main():
    i18n.refresh_db_overrides()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
