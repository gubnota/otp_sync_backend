from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import telebot
from typing import List, Dict, Any, Optional
import uvicorn
from threading import Thread
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import re

# Load environment variables
load_dotenv()

# Initialize FastAPI app and Telegram bot
app = FastAPI()
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTH_KEY = os.getenv("AUTH_KEY")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(func=lambda message: True)
def echo_id(message):
    bot.reply_to(message, f"Your Telegram ID is: {message.from_user.id}")


@app.get("/")
async def root():
    return {"message": "Hello World"}


def extract_otp_codes(text: str) -> str:
    """Extract OTP codes from text and wrap them in backticks for easy copying."""
    otp_pattern = r'\b(\d{4,8})\b'
    
    def replace_otp(match):
        return f"`{match.group(1)}`"
    
    formatted_text = re.sub(otp_pattern, replace_otp, text)
    return formatted_text

def extract_last_digits(phone: str, digits: int = 6) -> str:
    """Extract last N digits from a phone number."""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Return last N digits
    return digits_only[-digits:] if len(digits_only) >= digits else digits_only



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



@app.post("/receive_data")
async def receive_data(request: Request):
    telegram_available = False
    
    try:
        # Check auth key
        headers = request.headers
        auth_key = headers.get("X-Auth-Key")
        if auth_key != AUTH_KEY:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid auth key"}
            )

        # Parse JSON body
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid JSON format"}
            )
        
        # Validate that body is a list
        if not isinstance(body, list):
            return JSONResponse(
                status_code=400,
                content={"error": "Expected array of message objects"}
            )
        
        # Process each message
        failed_messages = []
        successful_messages = []
        
        for idx, message_data in enumerate(body):
            # Validate message structure
            if not isinstance(message_data, dict):
                failed_messages.append({
                    "index": idx,
                    "error": "Invalid message format: expected object"
                })
                continue
            
            # Extract user IDs from the "ids" field
            ids_str = message_data.get("ids", "")
            if not ids_str:
                failed_messages.append({
                    "index": idx,
                    "error": "Missing 'ids' field"
                })
                continue
            
            user_ids = [id.strip() for id in ids_str.split(",") if id.strip()]
            
            if not user_ids:
                failed_messages.append({
                    "index": idx,
                    "error": "No valid user IDs found"
                })
                continue
            
            # Check that at least SMS or Call is present
            has_sms = bool(message_data.get("sms"))
            has_call = bool(message_data.get("call"))
            
            if not has_sms and not has_call:
                failed_messages.append({
                    "index": idx,
                    "error": "Either 'sms' or 'call' field is required"
                })
                continue
            
            # Format the message
            formatted_message = format_message(message_data)
            
            # Send to each user
            for user_id in user_ids:
                try:
                    bot.send_message(
                        user_id, 
                        formatted_message,
                        parse_mode="Markdown"
                    )
                    telegram_available = True
                    successful_messages.append({
                        "index": idx,
                        "user_id": user_id
                    })
                except Exception as e:
                    print(f"Failed to send message to user {user_id}: {str(e)}")
                    failed_messages.append({
                        "index": idx,
                        "user_id": user_id,
                        "error": str(e)
                    })
        
        # If we couldn't send any messages, Telegram might be down
        if not telegram_available and failed_messages:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Telegram is down or unavailable",
                    "details": failed_messages
                }
            )
        
        # Return results
        if failed_messages:
            return JSONResponse(
                status_code=207,
                content={
                    "status": "partial_success",
                    "successful": successful_messages,
                    "failed": failed_messages
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "delivered": len(successful_messages)
            }
        )

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


def run_bot():
    bot.infinity_polling()


if __name__ == "__main__":
    # Start Telegram bot in a separate thread
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Run FastAPI with uvicorn in main thread
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9374,
        ssl_keyfile="private.key",
        ssl_certfile="cert.crt",
    )
