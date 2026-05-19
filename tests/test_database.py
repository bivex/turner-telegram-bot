import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add the project root to sys.path to import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database

class TestDatabase(unittest.TestCase):

    @patch('database.pymysql.connect')
    def test_update_order_data_json_initial(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Simulate empty order_data
        mock_cursor.fetchone.return_value = {'order_data': None}
        
        # Execute
        database.update_order_data_json(1, 'test_key', 'test_val')
        
        # Verify initial creation of JSON object
        mock_cursor.execute.assert_any_call(
            "UPDATE orders SET order_data = JSON_OBJECT(%s, %s) WHERE id=%s", 
            ('test_key', 'test_val', 1)
        )

    @patch('database.pymysql.connect')
    def test_update_order_data_json_update(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Simulate existing order_data
        mock_cursor.fetchone.return_value = {'order_data': '{"old_key": "old_val"}'}
        
        # Execute
        database.update_order_data_json(1, 'new_key', 'new_val')
        
        # Verify JSON_SET is used
        mock_cursor.execute.assert_any_call(
            "UPDATE orders SET order_data = JSON_SET(order_data, %s, %s) WHERE id=%s", 
            ('$.new_key', 'new_val', 1)
        )

    @patch('database.pymysql.connect')
    def test_get_bot_config(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Simulate rows
        mock_cursor.fetchall.side_effect = [
            [{'key_name': 'token', 'value_text': '123'}], # settings
            [{'cfg_key': 'welcome', 'cfg_value': 'Hi'}]   # bot_config
        ]
        
        # Execute
        cfg = database.get_bot_config()
        
        # Verify
        self.assertEqual(cfg['token'], '123')
        self.assertEqual(cfg['welcome'], 'Hi')

if __name__ == '__main__':
    unittest.main()
