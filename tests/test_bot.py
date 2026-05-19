import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock i18n before importing bot
import i18n
i18n.t = MagicMock(return_value="mocked_text")

import bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import types

class TestBot(unittest.IsolatedAsyncioTestCase):
    async def test_process_work_type(self):
        # Mock callback
        callback = AsyncMock(spec=types.CallbackQuery)
        callback.data = "type_repair"
        callback.from_user.id = 123
        callback.message = AsyncMock(spec=types.Message)
        
        # Mock state
        storage = MemoryStorage()
        key = types.StorageKey(bot_id=1, chat_id=123, user_id=123)
        state = FSMContext(storage=storage, key=key)
        await state.update_data(order_id=1)
        
        # Mock database
        with patch('database.update_order_data_json') as mock_update:
            with patch('database.get_user_language', return_value='ru'):
                await bot.process_work_type(callback, state)
                
                # Verify JSON update was called
                mock_update.assert_called_with(1, 'work_type', "mocked_text")
                
                # Verify state transition (it should have moved to dimensions, but we can't easily check state name here without more setup)
                callback.message.answer.assert_called()

    async def test_process_dimensions(self):
        # Mock message
        message = AsyncMock(spec=types.Message)
        message.text = "100mm"
        message.from_user.id = 123
        
        # Mock state
        storage = MemoryStorage()
        key = types.StorageKey(bot_id=1, chat_id=123, user_id=123)
        state = FSMContext(storage=storage, key=key)
        await state.update_data(order_id=1)
        
        # Mock database
        with patch('database.update_order_data_json') as mock_update:
            with patch('database.get_user_language', return_value='ru'):
                await bot.process_dimensions(message, state)
                
                # Verify JSON update was called
                mock_update.assert_called_with(1, 'dimensions', "100mm")
                message.answer.assert_called()

if __name__ == '__main__':
    unittest.main()
