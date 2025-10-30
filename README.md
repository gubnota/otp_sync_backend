# [Mobile part see here](https://github.com/gubnota/otp_sync)

## Self-signed certificate

- [video](https://github.com/user-attachments/assets/b106ab6e-db6a-45d1-a1f2-f367561ad184)

First you need to generate a self-signed certificate.
Certificate authority is not required to place on the client side.

```bash
openssl genrsa -out private.key 2048
openssl req -new -key private.key -out cert.csr
openssl x509 -req -days 36500 -in cert.csr -signkey private.key -out cert.crt
```

## .env

1. create `.env` (see env.example)
2. make sure BOT_TOKEN is the correct secret for your Telegram bot.

## Run and test

```sh
docker compose up --build
curl -X GET https://localhost:9374/ \
     --cert cert.crt \
     --key private.key \
     --insecure

```

## Running locally without docker

- Using pip:

```bash
python -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
```

- Using poetry:

```bash
poetry install
```

- Using uv:

```bash
uv sync
uv run main.py
```

## Troubleshooting

```log
ERROR - TeleBot: "Threaded polling exception: A request to the Telegram API was unsuccessful. Error code: 409. Description: Conflict: can't use getUpdates method while webhook is active; use deleteWebhook to delete the webhook first"
```

Delete webhook by accessing this endpoint:

- https://api.telegram.org/bot<TOKEN>/deleteWebhook

### Run tests

```sh
uv run test_webhook.py
uv run test_real_messages.py
```

## Expected input

```json
[
  {
    "ids": "123456789",
    "sms": "Login code: 123456"
  },
  {
    "ids": "987654321",
    "call": true,
    "from": "+1234567890",
    "to": "SIM 1"
  },
  {
    "ids": "555555555",
    "sms": "Reset your password with code 654321"
  }
]
```

# Message Formatting Documentation

## Overview

The `format_message()` function processes incoming SMS and call data, transforming them into user-friendly Telegram messages with highlighted OTP codes and phone number snippets.

## Function Signature

```python
def format_message(data: Dict[str, Any]) -> str:
    """Format the incoming data into a readable Telegram message."""
```

## Parameters

- **data** (Dict[str, Any]): Dictionary containing message data with the following possible keys:
  - `sms` (str): SMS text content
  - `call` (bool): Flag indicating incoming call
  - `from` (str): Incoming call phone number
  - `to` (str): Destination SIM or location

## SMS Formatting

### Behavior

When `data["sms"]` is provided:

- The function extracts OTP codes (4-8 digit sequences)
- OTP codes are wrapped in backticks for easy copying
- Returns formatted SMS text with highlighted codes

### Example

**Input:**

```python
{
  "sms": "Your verification code is 827364. Do not share."
}
```

**Output:**

```
Your verification code is `827364`. Do not share.
```

### Multiple OTP Codes

If the SMS contains multiple OTP codes, all are highlighted:

**Input:**

```python
{
  "sms": "First code: 1234, second code: 567890"
}
```

**Output:**

```
First code: `1234`, second code: `567890`
```

## Call Notification Formatting

### Behavior

When `data["call"]` is `True`:

- Full phone number from `data["from"]` is displayed
- Last 6 digits of the phone number are extracted and wrapped in backticks
- Destination (SIM) information from `data["to"]` is included
- Call emoji (📞) indicates incoming call

### Example

**Input:**

```python
{
  "call": True,
  "from": "+861234567890",
  "to": "SIM 1"
}
```

**Output:**

```
📞 +861234567890 (`567890`), SIM 1
```

### Last 6 Digits Extraction

The function uses `extract_last_digits()` helper to:

1. Remove all non-digit characters from phone number
2. Extract the last 6 digits
3. Return fewer digits if the phone number contains less than 6 digits

**Examples:**

- `"+861234567890"` → `"567890"`
- `"+79991234567"` → `"234567"`
- `"1234567890"` → `"567890"`
- `"12345"` → `"12345"` (only 5 digits available)

## Priority

- **SMS takes priority over calls**: If both `sms` and `call` are provided, only SMS is formatted
- **Mutual exclusivity**: In production, either SMS or call should be present, not both

## Return Value

- (str): Formatted message ready to send to Telegram
- Empty string if neither SMS nor call data is provided

## Implementation Details

```python
def format_message(data: Dict[str, Any]) -> str:
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
        # Format Call message with last 6 digits wrapped in backticks
        from_phone = data.get('from', 'Unknown')
        to_location = data.get('to', 'Unknown')
        last_digits = extract_last_digits(from_phone, 6)
        lines.append(f"📞 {from_phone} (`{last_digits}`), {to_location}")

    return "\n".join(lines)
```

## Helper Functions

### extract_otp_codes(text: str) -> str

Wraps 4-8 digit sequences in backticks using regex pattern `\b(\d{4,8})\b`.

```python
def extract_otp_codes(text: str) -> str:
    """Extract OTP codes from text and wrap them in backticks for easy copying."""
    otp_pattern = r'\b(\d{4,8})\b'

    def replace_otp(match):
        return f"`{match.group(1)}`"

    formatted_text = re.sub(otp_pattern, replace_otp, text)
    return formatted_text
```

### extract_last_digits(phone: str, digits: int = 6) -> str

Extracts the last N digits from a phone number by removing non-digit characters.

```python
def extract_last_digits(phone: str, digits: int = 6) -> str:
    """Extract last N digits from a phone number."""
    digits_only = re.sub(r'\D', '', phone)
    return digits_only[-digits:] if len(digits_only) >= digits else digits_only
```

## Error Handling

The function handles missing data gracefully:

- Missing phone number defaults to `"Unknown"`
- Missing SIM/location defaults to `"Unknown"`
- Empty data returns empty string

## Testing

See `test_webhook.py` for unit tests of the formatting logic.
