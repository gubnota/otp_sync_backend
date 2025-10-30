import unittest
from unittest.mock import patch, MagicMock
import json
import re


def extract_otp_codes(text: str) -> str:
    """Extract OTP codes from text and wrap them in backticks for easy copying."""
    otp_pattern = r'\b(\d{4,8})\b'
    
    def replace_otp(match):
        return f"`{match.group(1)}`"
    
    formatted_text = re.sub(otp_pattern, replace_otp, text)
    return formatted_text


def format_message(data: dict) -> str:
    """Format the incoming data into a readable Telegram message."""
    lines = []
    
    # Check if it's SMS or Call
    has_call = bool(data.get("call") and data.get("call", True))
    has_sms = bool(data.get("sms"))
    
    if has_sms:
        # Format SMS message
        formatted_sms = extract_otp_codes(data["sms"])
        lines.append(formatted_sms)
    elif has_call:
        # Format Call message
        lines.append(f"📞 {data.get('from', 'Unknown')}, {data.get('to', 'Unknown')}")
    
    return "\n".join(lines)


class TestTestWebhook(unittest.TestCase):
    def setUp(self):
        pass

    def test_sms_only_formatting(self):
        entry = {
            "ids": "123123",
            "sms": "Your code is 2345. Please use 2345 to verify."
        }
        msg = format_message(entry)
        self.assertIn("`2345`", msg)
        self.assertIn("Your code is", msg)

    def test_call_only_formatting(self):
        entry = {
            "ids": "987654",
            "call": True,
            "from": "+861234567890",
            "to": "SIM 1"
        }
        msg = format_message(entry)
        self.assertIn("📞 +861234567890, SIM 1", msg)

    def test_invalid_no_content(self):
        """Test that empty message is returned when neither SMS nor call provided."""
        entry = {
            "ids": "000000"
        }
        msg = format_message(entry)
        self.assertEqual(msg, "")

    def test_call_false_not_included(self):
        """Test that call: False doesn't include call message."""
        entry = {
            "ids": "111111",
            "call": False,
            "from": "+861234567890",
            "to": "SIM 1"
        }
        msg = format_message(entry)
        self.assertEqual(msg, "")

    def test_call_empty_string_not_included(self):
        """Test that call: '' (empty string) doesn't include call message."""
        entry = {
            "ids": "111111",
            "call": "",
            "from": "+861234567890",
            "to": "SIM 1"
        }
        msg = format_message(entry)
        self.assertEqual(msg, "")

    def test_different_keys_no_error(self):
        """Ensure extra fields don't crash and formatting remains stable."""
        entry = {
            "ids": "222222",
            "sms": "Code 9999",
            "extra": "ignored"
        }
        msg = format_message(entry)
        self.assertIn("`9999`", msg)

    def test_otp_extraction_multiple_codes(self):
        """Test that multiple OTP codes are properly wrapped."""
        entry = {
            "ids": "333333",
            "sms": "First code: 1234, second code: 567890, third: 99"
        }
        msg = format_message(entry)
        self.assertIn("`1234`", msg)
        self.assertIn("`567890`", msg)
        self.assertNotIn("`99`", msg)

    def test_no_sms_no_call_fields(self):
        """Test handling when neither sms nor call keys exist."""
        entry = {
            "ids": "444444",
            "from": "+10000000000",
            "to": "SIM 1"
        }
        msg = format_message(entry)
        self.assertEqual(msg, "")


if __name__ == "__main__":
    unittest.main()
