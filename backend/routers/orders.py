from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import database
from routers.auth import verify_token
import httpx
import os
import config

router = APIRouter()

# Pydantic модели
class OrderBase(BaseModel):
    id: int
    user_id: int
    username: Optional[str]
    full_name: str
    status: str
    order_data: Optional[dict] = None
    photo_file_id: Optional[str]
    created_at: datetime
    internal_note: Optional[str]

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    internal_note: Optional[str] = None

class OrderStats(BaseModel):
    total_orders: int
    new_orders: int
    active_orders: int

DEFAULT_PAGE_LIMIT = 20

@router.get("/", response_model=List[OrderBase])
async def get_orders(
    page: int = 1,
    limit: int = DEFAULT_PAGE_LIMIT,
    status_filter: Optional[str] = None,
    _payload: dict = Depends(verify_token)
):
    """Получить список заказов с пагинацией"""
    try:
        offset = (page - 1) * limit
        orders = database.get_orders_paginated(limit, offset, status_filter)
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения заказов: {str(e)}")

@router.get("/stats", response_model=OrderStats)
async def get_order_stats(_payload: dict = Depends(verify_token)):
    """Получить статистику заказов"""
    try:
        stats = database.get_order_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.get("/{order_id}", response_model=OrderBase)
async def get_order(order_id: int, _payload: dict = Depends(verify_token)):
    """Получить заказ по ID"""
    try:
        order = database.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения заказа: {str(e)}")

@router.put("/{order_id}")
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    _payload: dict = Depends(verify_token)
):
    """Обновить заказ"""
    try:
        current_order = database.get_order(order_id)
        if not current_order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        old_status = current_order.get('status')
        
        if order_update.status:
            database.update_order_field(order_id, 'status', order_update.status)
            
            # Если статус изменился - отправляем уведомление
            if old_status != order_update.status:
                await send_status_update_notification(
                    current_order['user_id'], 
                    order_id, 
                    order_update.status
                )

        if order_update.internal_note is not None:
            database.update_order_field(order_id, 'internal_note', order_update.internal_note)

        return {"message": "Заказ обновлен успешно"}
    except Exception as e:
        print(f"Update order error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления заказа: {str(e)}")

@router.delete("/all")
async def delete_all_orders(_payload: dict = Depends(verify_token)):
    """Удалить все заказы"""
    try:
        database.delete_all_orders()
        return {"message": "Все заказы удалены"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления заказов: {str(e)}")

async def send_status_update_notification(user_id: int, order_id: int, new_status: str):
    """Отправить уведомление клиенту через Telegram Bot API"""
    status_map = {
        'new': '🔥 НОВЫЙ (Принят в обработку)',
        'discussion': '💬 Обсуждение деталей',
        'approved': '🛠 Одобрен / В работе',
        'work': '⚙️ Выполняется',
        'done': '✅ ГОТОВ!',
        'rejected': '❌ Отказ'
    }
    
    status_text = status_map.get(new_status, new_status)
    message_text = f"⚙️ <b>Статус вашего заказа №{order_id} изменен:</b>\n\n🔹 {status_text}"
    
    bot_token = config.BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "chat_id": user_id,
                "text": message_text,
                "parse_mode": "HTML"
            }
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")

@router.get("/{order_id}/photos")
async def get_order_photos(order_id: int, _payload: dict = Depends(verify_token)):
    """Получить рабочие ссылки на фото заказа"""
    try:
        order = database.get_order(order_id)
        if not order or not order['photo_file_id']:
            return {"photos": []}

        raw_ids = order['photo_file_id'].split(',')
        # Очищаем ID от префиксов p: и d:
        clean_ids = [p[2:] if p.startswith(('p:', 'd:')) else p for p in raw_ids]
        
        photo_urls = []
        bot_token = config.BOT_TOKEN
        
        async with httpx.AsyncClient() as client:
            for file_id in clean_ids:
                try:
                    # 1. Получаем путь к файлу через getFile
                    file_info_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
                    resp = await client.get(file_info_url)
                    
                    if resp.status_code == 200:
                        file_path = resp.json().get('result', {}).get('file_path')
                        if file_path:
                            # 2. Формируем прямую ссылку на скачивание
                            full_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                            photo_urls.append(full_url)
                except Exception as e:
                    print(f"Error resolving file_id {file_id}: {e}")
                    
        return {"photos": photo_urls}
    except Exception as e:
        print(f"Get photos error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения фото: {str(e)}")