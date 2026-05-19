from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import database
from routers.auth import verify_token
import httpx
import config

router = APIRouter()

class BotConfigUpdate(BaseModel):
    key: str
    value: str

class AdminAdd(BaseModel):
    chat_id: int
    role: str = 'admin'

class BroadcastMessage(BaseModel):
    text: str
    parse_mode: str = 'HTML'

@router.get("/")
async def get_bot_config(_payload: dict = Depends(verify_token)) -> Dict[str, Any]:
    """Получить все настройки бота"""
    try:
        config_data = database.get_bot_config()
        return config_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек: {str(e)}")

@router.put("/")
async def update_bot_config(
    config_update: BotConfigUpdate,
    _payload: dict = Depends(verify_token)
):
    """Обновить настройку бота"""
    try:
        # Определяем, в какую таблицу сохранять
        if config_update.key in ['admin_chat_id', 'bot_token']:
            database.update_setting(config_update.key, config_update.value)
        else:
            database.update_bot_config(config_update.key, config_update.value)

        return {"message": "Настройка обновлена успешно"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления настройки: {str(e)}")

@router.get("/settings")
async def get_bot_settings(_payload: dict = Depends(verify_token)) -> Dict[str, Any]:
    """Получить системные настройки бота"""
    try:
        config_data = database.get_bot_config()
        # Фильтруем только настройки (не тексты)
        settings_keys = [
            'is_photo_required', 'step_extra_enabled', 'admin_chat_id'
        ]
        settings = {key: config_data.get(key, '') for key in settings_keys}
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек: {str(e)}")

@router.put("/settings")
async def update_bot_settings(
    settings: Dict[str, Any],
    _payload: dict = Depends(verify_token)
):
    """Обновить системные настройки бота"""
    try:
        for key, value in settings.items():
            if key == 'admin_chat_id':
                database.update_setting(key, str(value))
            else:
                database.update_bot_config(key, str(value))
        return {"message": "Настройки обновлены успешно"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления настроек: {str(e)}")

@router.get("/flow")
async def get_survey_flow(_payload: dict = Depends(verify_token)) -> List[Dict[str, Any]]:
    """Получить структуру опроса (JSON)"""
    try:
        import json
        config_data = database.get_bot_config()
        flow_raw = config_data.get('survey_flow', '[]')
        if isinstance(flow_raw, str):
            return json.loads(flow_raw)
        return flow_raw
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения структуры: {str(e)}")

@router.put("/flow")
async def update_survey_flow(
    flow: List[Dict[str, Any]],
    _payload: dict = Depends(verify_token)
):
    """Обновить структуру опроса"""
    try:
        import json
        database.update_bot_config('survey_flow', json.dumps(flow, ensure_ascii=False))
        return {"message": "Структура опроса обновлена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления структуры: {str(e)}")

# --- Admin Management ---

@router.get("/admins")
async def list_admins(_payload: dict = Depends(verify_token)):
    """List all admins with full records"""
    try:
        admins = database.get_all_admins()
        return {"admins": admins}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching admins: {str(e)}")

@router.post("/admins")
async def add_admin(
    admin_data: AdminAdd,
    _payload: dict = Depends(verify_token)
):
    """Add a new admin"""
    try:
        database.add_admin(admin_data.chat_id, role=admin_data.role)
        return {"message": "Admin added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding admin: {str(e)}")

@router.delete("/admins/{chat_id}")
async def remove_admin(
    chat_id: int,
    _payload: dict = Depends(verify_token)
):
    """Remove an admin"""
    try:
        database.remove_admin(chat_id)
        return {"message": "Admin removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing admin: {str(e)}")

# --- Broadcast ---

@router.post("/broadcast")
async def broadcast_message(
    broadcast: BroadcastMessage,
    _payload: dict = Depends(verify_token)
):
    """Send a message to all customers via Telegram"""
    try:
        user_ids = database.get_all_customer_user_ids()
        bot_token = config.BOT_TOKEN
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        sent = 0
        failed = 0

        async with httpx.AsyncClient() as client:
            for user_id in user_ids:
                try:
                    payload = {
                        "chat_id": user_id,
                        "text": broadcast.text,
                        "parse_mode": broadcast.parse_mode
                    }
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    sent += 1
                except Exception:
                    failed += 1

        return {"sent": sent, "failed": failed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error broadcasting message: {str(e)}")
