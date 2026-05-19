import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from routers.auth import verify_token

class TestOrdersAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Mock auth via dependency overrides
        app.dependency_overrides[verify_token] = lambda: {"sub": "admin"}

    def tearDown(self):
        app.dependency_overrides = {}

    @patch('database.get_orders_paginated')
    def test_get_orders(self, mock_get_orders):
        # Setup mock
        mock_get_orders.return_value = [
            {
                "id": 1,
                "user_id": 123,
                "username": "testuser",
                "full_name": "Test User",
                "status": "new",
                "order_data": {"test": "data"},
                "photo_file_id": None,
                "created_at": "2023-01-01T00:00:00",
                "internal_note": None
            }
        ]
        
        # Execute
        response = self.client.get("/api/orders/")
        
        # Verify
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["order_data"]["test"], "data")
        self.assertNotIn("work_type", data[0]) # Verify turner-specific fields are gone

    @patch('database.get_order')
    @patch('database.update_order_field')
    @patch('routers.orders.send_status_update_notification')
    def test_update_order_status(self, mock_notify, mock_update, mock_get_order):
        # Setup mock
        mock_get_order.return_value = {"id": 1, "user_id": 123, "status": "new"}
        
        # Execute
        response = self.client.put("/api/orders/1", json={"status": "approved"})
        
        # Verify
        self.assertEqual(response.status_code, 200)
        mock_update.assert_any_call(1, 'status', 'approved')
        # mock_notify.assert_called_once() # We patched it so it shouldn't try to send real TG msg

if __name__ == '__main__':
    unittest.main()
