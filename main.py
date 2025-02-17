from fastapi import FastAPI, Request
import telebot
from typing import List
import uvicorn
from threading import Thread
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize FastAPI app and Telegram bot
app = FastAPI()
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Load from .env file
AUTH_KEY = os.getenv("AUTH_KEY")  # Load from .env file
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

bot = telebot.TeleBot(BOT_TOKEN)


# Telegram message handler
@bot.message_handler(func=lambda message: True)
def echo_id(message):
    bot.reply_to(message, f"Your Telegram ID is: {message.from_user.id}")


@app.get("/")
async def root():
    return {"message": "Hello World"}


# HTTPS endpoint to receive data
@app.post("/receive_data")
async def receive_data(request: Request):
    try:
        headers = request.headers
        auth_key = headers.get("X-Auth-Key")
        if auth_key != AUTH_KEY:
            return {"error": "Invalid auth key"}, 401

        data = (await request.body()).decode("utf-8")
        lines = data.split("\n", 1)

        if len(lines) < 2:
            return {"error": "Invalid format: Need user IDs and content"}, 400

        user_ids: List[str] = [id.strip() for id in lines[0].split(",")]
        content = lines[1]

        # Send message to each user
        failed_ids = []
        for user_id in user_ids:
            try:
                bot.send_message(user_id, content)
            except Exception as e:
                print(f"Failed to send message to user {user_id}: {str(e)}")
                failed_ids.append(user_id)

        if failed_ids:
            return {"status": "partial_success", "failed_ids": failed_ids}
        return {"status": "success"}

    except Exception as e:
        return {"error": str(e)}, 500


def run_bot():
    bot.infinity_polling()


if __name__ == "__main__":
    # Start Telegram bot in a separate thread
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = (
        True  # This ensures the thread will be terminated when the main program exits
    )
    bot_thread.start()

    # Run FastAPI with uvicorn in main thread
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9374,
        ssl_keyfile="private.key",
        ssl_certfile="cert.crt",
    )
