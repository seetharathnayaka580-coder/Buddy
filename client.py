from telethon import TelegramClient

# Use your own values here
api_id = 33328077  # Your Telegram API ID
api_hash = 'f1c2e72dfe5c55fbfd5c114985790b46'  # Your Telegram API hash

# Initialize the Telegram client
try:
    client = TelegramClient('session', api_id=api_id, api_hash=api_hash)
    print("Client initialized successfully.")
except Exception as e:
    print(f"Failed to initialize client: {e}")
