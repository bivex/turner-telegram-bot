import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import bot
import i18n
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram import types

TEST_USER_ID = 123

class TestBot(unittest.IsolatedAsyncioTestCase):
    async def test_process_work_type(self):
        # Mock callback
        callback = AsyncMock(spec=types.CallbackQuery)
        callback.data = "flow_val:type_repair"
        callback.from_user = MagicMock()
        callback.from_user.id = TEST_USER_ID
        callback.message = AsyncMock(spec=types.Message)
        callback.message.from_user = MagicMock()
        callback.message.from_user.id = TEST_USER_ID
        callback.message.edit_text = AsyncMock()
        callback.message.answer = AsyncMock()
        callback.answer = AsyncMock()
        
        # Mock state
        storage = MemoryStorage()
        key = StorageKey(bot_id=1, chat_id=TEST_USER_ID, user_id=TEST_USER_ID)
        state = FSMContext(storage=storage, key=key)
        await state.update_data(order_id=1, current_step=1)
        
        # Mock database and i18n
        mocked_flow = [
            {}, 
            {'id': 'work_type', 'type': 'choice', 'options': [{'val': 'type_repair', 'label': 'Mocked Repair'}]}
        ]
        with patch('database.update_order_data_json') as mock_update:
            with patch('bot.get_survey_flow', return_value=mocked_flow):
                with patch('database.get_user_language', return_value='ru'):
                    with patch('i18n.t', return_value='mocked_text'):
                        with patch('bot.notify_admin'):
                            await bot.process_choice(callback, state)

                # Verify JSON update was called
                mock_update.assert_any_call(1, 'work_type', "Mocked Repair")

                
                # Verify state transition
                callback.message.answer.assert_called()

    async def test_process_dimensions(self):
        # Mock message
        message = AsyncMock(spec=types.Message)
        message.text = "100mm"
        message.photo = None
        message.document = None
        message.from_user = MagicMock()
        message.from_user.id = TEST_USER_ID
        message.answer = AsyncMock()
        
        # Mock state
        storage = MemoryStorage()
        key = StorageKey(bot_id=1, chat_id=TEST_USER_ID, user_id=TEST_USER_ID)
        state = FSMContext(storage=storage, key=key)
        await state.update_data(order_id=1, current_step=0)
        
        # Mock database and i18n
        with patch('database.update_order_data_json') as mock_update:
            with patch('bot.get_survey_flow', return_value=[{'id': 'dimensions', 'type': 'text'}]):
                with patch('database.get_user_language', return_value='ru'):
                    with patch('i18n.t', return_value='mocked_text'):
                        with patch('bot.notify_admin') as mock_notify:
                            await bot.process_survey_message(message, state)

                # Verify JSON update was called
                mock_update.assert_any_call(1, 'dimensions', "100mm")

                message.answer.assert_called()

if __name__ == '__main__':
    unittest.main()
