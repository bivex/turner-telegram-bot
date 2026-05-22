import sys
import os
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram import types

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bot
import i18n

TEST_USER_ID = 999999
TEST_ORDER_ID = 777

class TestBusinessFlow(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.storage = MemoryStorage()
        self.key = StorageKey(bot_id=1, chat_id=TEST_USER_ID, user_id=TEST_USER_ID)
        self.state = FSMContext(storage=self.storage, key=self.key)

    async def test_full_survey_flow_logic(self):
        """Test the logic of moving through the new metal processing flow"""
        
        # Mocked Survey Flow (simplified version of the real one)
        mocked_flow = [
            {"id": "photo", "type": "photo", "label": "Step 1", "required_key": "is_photo_required"},
            {"id": "service_type", "type": "choice", "label": "Step 2", "options": [{"val": "mechanical", "label": "Mechanical"}]},
            {"id": "material", "type": "text", "label": "Step 3"}
        ]

        # 1. Test Starting Step 0 (Photo) - Skipping it
        message = AsyncMock(spec=types.Message)
        message.answer = AsyncMock()
        message.from_user = MagicMock(spec=types.User)
        message.from_user.id = TEST_USER_ID
        message.from_user.username = "test_user"
        message.from_user.full_name = "Test User"
        message.text = "Skip"
        message.photo = None
        message.document = None
        await self.state.update_data(order_id=TEST_ORDER_ID, current_step=0)

        with patch('bot.get_survey_flow', return_value=mocked_flow), \
             patch('database.get_user_language', return_value='uk'), \
             patch('i18n.t', side_effect=lambda key, lang, **kwargs: "Skip" if key == 'btn_skip_photo' else key), \
             patch('bot.get_config_bool', return_value=False), \
             patch('bot.ask_step', new_callable=AsyncMock) as mock_ask_step:
            
            await bot.process_survey_message(message, self.state)
            
            # Verify it moved to next step
            mock_ask_step.assert_called_with(message, self.state, 1)

    async def test_notify_admin_key_mapping(self):
        """Test that notify_admin correctly maps the new flow IDs to the notification template"""
        
        mock_order = {
            'id': TEST_ORDER_ID,
            'user_id': TEST_USER_ID,
            'full_name': 'Test Client',
            'username': 'test_client',
            'photo_file_id': None,
            'order_data': {
                'service_type': '⚙️ Mechanical',
                'material': 'Aluminum',
                'dimensions_qty': '100x100, 2pcs',
                'urgency': 'Urgent',
                'extra_info': 'Be careful'
            }
        }

        with patch('database.get_all_admins', return_value=[111]), \
             patch('database.get_order', return_value=mock_order), \
             patch('database.get_user_language', return_value='uk'), \
             patch('bot._admin_lang', return_value='uk'), \
             patch('i18n.t') as mock_t, \
             patch('bot.bot.send_message', new_callable=AsyncMock) as mock_send:
            
            await bot.notify_admin(TEST_ORDER_ID)
            
            # Verify i18n.t was called with correctly mapped fields
            args, kwargs = mock_t.call_args
            self.assertEqual(kwargs['work_type'], '⚙️ Mechanical')
            self.assertEqual(kwargs['conditions'], 'Aluminum')
            self.assertEqual(kwargs['dimensions'], '100x100, 2pcs')
            self.assertEqual(kwargs['comment'], 'Be careful')

if __name__ == '__main__':
    unittest.main()
