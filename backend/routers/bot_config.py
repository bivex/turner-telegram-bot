from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import database
from routers.auth import verify_token

router = APIRouter()

class BotConfigUpdate(BaseModel):
    key: str
    value: str

@router.get("/")
async def get_bot_config(payload: dict = Depends(verify_token)) -> Dict[str, Any]:
    """Получить все настройки бота"""
    try:
        config = database.get_bot_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек: {str(e)}")

@router.put("/")
async def update_bot_config(
    config_update: BotConfigUpdate,
    payload: dict = Depends(verify_token)
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
async def get_bot_settings(payload: dict = Depends(verify_token)) -> Dict[str, Any]:
    """Получить системные настройки бота"""
    try:
        config = database.get_bot_config()
        # Фильтруем только настройки (не тексты)
        settings_keys = [
            'is_photo_required', 'step_extra_enabled', 'admin_chat_id'
        ]
        settings = {key: config.get(key, '') for key in settings_keys}
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек: {str(e)}")

@router.put("/settings")
async def update_bot_settings(
    settings: Dict[str, Any],
    payload: dict = Depends(verify_token)
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
async def get_survey_flow(payload: dict = Depends(verify_token)) -> List[Dict[str, Any]]:
    """Получить структуру опроса (JSON)"""
    try:
        import json
        config = database.get_bot_config()
        flow_raw = config.get('survey_flow', '[]')
        if isinstance(flow_raw, str):
            return json.loads(flow_raw)
        return flow_raw
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения структуры: {str(e)}")

@router.put("/flow")
async def update_survey_flow(
    flow: List[Dict[str, Any]],
    payload: dict = Depends(verify_token)
):
    """Обновить структуру опроса"""
    try:
        import json
        database.update_bot_config('survey_flow', json.dumps(flow, ensure_ascii=False))
        return {"message": "Структура опроса обновлена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления структуры: {str(e)}")
