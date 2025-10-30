import unittest
from unittest.mock import patch, MagicMock
import os
from dotenv import load_dotenv
import requests
import json
import urllib3


# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTH_KEY = os.getenv("AUTH_KEY")
BASE_URL = os.getenv("BASE_URL", "https://localhost:9374")  # Changed to https


class TestRealMessageDelivery(unittest.TestCase):
    """Integration tests that deliver real messages to Telegram."""

    def setUp(self):
        """Set up test fixtures."""
        self.headers = {
            "X-Auth-Key": AUTH_KEY,
            "Content-Type": "application/json"
        }
        self.base_url = BASE_URL
        self.endpoint = f"{self.base_url}/receive_data"
        # Disable SSL verification for self-signed certs
        self.verify_ssl = False

    def test_send_sms_to_real_user(self):
        """Send a real SMS message to a real user ID."""
        user_id = "52504904"
        
        payload = [
            {
                "ids": user_id,
                "sms": "Test SMS: Your verification code is 123456"
            }
        ]
        
        response = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            verify=self.verify_ssl
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json()["status"])
        self.assertEqual(response.json()["delivered"], 1)

    def test_send_call_to_real_user(self):
        """Send a real call notification to a real user ID."""
        user_id = "52504904"
        
        payload = [
            {
                "ids": user_id,
                "call": True,
                "from": "+861234567890",
                "to": "SIM 1"
            }
        ]
        
        response = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            verify=self.verify_ssl
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json()["status"])
        self.assertEqual(response.json()["delivered"], 1)

    def test_send_to_multiple_users(self):
        """Send messages to multiple user IDs at once."""
        user_ids = "52504904,52504904,52504904"
        
        payload = [
            {
                "ids": user_ids,
                "sms": "Broadcast SMS: Your code is 789012"
            }
        ]
        
        response = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            verify=self.verify_ssl
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json()["status"])
        self.assertEqual(response.json()["delivered"], 3)

    def test_send_multiple_messages_batch(self):
        """Send multiple different messages in one batch."""
        user_id_1 = "52504904"
        user_id_2 = "52504904"
        
        payload = [
            {
                "ids": user_id_1,
                "sms": "Message 1: Code is 111111"
            },
            {
                "ids": user_id_2,
                "call": True,
                "from": "+79991234567",
                "to": "SIM 2"
            }
        ]
        
        response = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            verify=self.verify_ssl
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json()["status"])
        self.assertEqual(response.json()["delivered"], 2)

    def test_invalid_auth_key(self):
        """Test that invalid auth key is rejected."""
        payload = [
            {
                "ids": "123456",
                "sms": "This should fail"
            }
        ]
        
        bad_headers = {
            "X-Auth-Key": "INVALID_KEY",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.endpoint,
            json=payload,
            headers=bad_headers,
            verify=self.verify_ssl
        )
        
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid auth key", response.json()["error"])
    def test_missing_ids_field(self):
        """Test that missing 'ids' field returns error."""
        payload = [
            {
                "sms": "No ids field"
            }
        ]
        
        response = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            verify=self.verify_ssl
        )
        
        self.assertEqual(response.status_code, 503)
        response_data = response.json()
        self.assertIn("error", response_data)
        self.assertIn("details", response_data)
        self.assertIn("Missing 'ids' field", response_data["details"][0]["error"])


    def test_neither_sms_nor_call(self):
        """Test that message without SMS or call is rejected."""
        payload = [
            {
                "ids": "123456"
            }
        ]
        
        response = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            verify=self.verify_ssl
        )
        
        self.assertEqual(response.status_code, 503)
        response_data = response.json()
        self.assertIn("error", response_data)
        self.assertIn("details", response_data)
        self.assertIn("Either 'sms' or 'call' field is required", response_data["details"][0]["error"])


    def test_otp_code_wrapping(self):
        """Test that OTP codes are properly wrapped in backticks in real message."""
        user_id = "52504904"
        
        payload = [
            {
                "ids": user_id,
                "sms": "Your verification code is 654321. Do not share."
            }
        ]
        
        response = requests.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            verify=self.verify_ssl
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json()["status"])

def test_partial_failure_some_invalid_ids(self):
    """Test partial failure when some user IDs fail to send."""
    user_ids = "52504904,INVALID_BOT_ID"
    
    payload = [
        {
            "ids": user_ids,
            "sms": "Partial delivery test: 555555"
        }
    ]
    
    response = requests.post(
        self.endpoint,
        json=payload,
        headers=self.headers,
        verify=self.verify_ssl
    )
    
    self.assertEqual(response.status_code, 207)
    response_data = response.json()
    self.assertIn("partial_success", response_data["status"])
    self.assertIn("successful", response_data)
    self.assertIn("failed", response_data)
    
    # Verify that we have at least one successful and one failed
    self.assertGreater(len(response_data["successful"]), 0)
    self.assertGreater(len(response_data["failed"]), 0)
    
    # Verify the failed entry has error details
    failed_entry = response_data["failed"][0]
    self.assertIn("error", failed_entry)
    self.assertIn("chat not found", failed_entry["error"])



if __name__ == "__main__":
    unittest.main()
