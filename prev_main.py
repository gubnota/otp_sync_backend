from fastapi import FastAPI, Request, HTTPException
from base64 import b64decode
import traceback
import dotenv
from aes256cipher import AES256Cipher

app = FastAPI()

# Secret key for AES-GCM (must match the key used in the Android app)
SECRET_KEY = dotenv.get("SECRET_KEY")  # bytes.fromhex(SECRET_KEY)[:32]  # 256-bit key

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = dotenv.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS = dotenv.get("TELEGRAM_CHAT_IDS")


def decrypt_data(encrypted_data: str) -> str:
    try:
        # Decode the Base64-encoded data
        decoded_data = b64decode(encrypted_data)

        # # Extract the nonce (first 12 bytes), ciphertext, and tag
        # nonce = decoded_data[:12]
        # ciphertext = decoded_data[12:-16]  # Everything except the last 16 bytes
        # tag = decoded_data[-16:]  # Last 16 bytes are the authentication tag

        # Initialize AES-GCM cipher
        cipher = AES256Cipher(SECRET_KEY)

        # Decrypt the data and verify the tag
        decrypted_data = cipher.decrypt(decoded_data)

        return decrypted_data.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


def send_telegram_notification(chat_id: str, message: str):
    print(f"Failed to send notification to chat ID {chat_id}: {message}")
    return
    # url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # payload = {
    #     "chat_id": chat_id,
    #     "text": message,
    #     "parse_mode": "Markdown"
    # }
    # response = requests.post(url, json=payload)
    # if response.status_code != 200:
    #     print(f"Failed to send notification to chat ID {chat_id}: {response.text}")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/")
async def receive_data(request: Request):
    encrypted_data = await request.body()
    try:
        # Read the encrypted data from the request body
        encrypted_data_str = encrypted_data.decode("utf-8")
        print(f"Received raw data: {encrypted_data_str}")  # Log raw input

        # Decrypt the data
        print("Attempting decryption...")
        decrypted_data = decrypt_data(encrypted_data_str)
        print(f"Decrypted data: {decrypted_data}")  # Log decrypted content

        # Parse the decrypted data
        print("Parsing message...")
        lines = decrypted_data.split("\n")
        if len(lines) < 2:
            raise ValueError("Invalid message format")

        message_type = lines[0]
        message_content = "\n".join(lines[1:])

        # Print the decrypted message to the console
        print(f"Received {message_type} message:")
        print(message_content)

        # Send notifications to Telegram
        for chat_id in TELEGRAM_CHAT_IDS:
            send_telegram_notification(chat_id, f"*{message_type}*\n{message_content}")

        return {"status": "success", "message": "Data received and processed"}
    except Exception as e:
        print("Error processing request:")
        print(f"Encrypted data: {encrypted_data_str}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9374,
        ssl_keyfile="private.key",
        ssl_certfile="cert.crt",
    )
