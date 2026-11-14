from telethon import TelegramClient

# Use your own values here
api_id = 21949583  # Your Telegram API ID
api_hash = 'cd58e4e5b5ae94f949a879c32c8728eb'  # Your Telegram API hash

# Initialize the Telegram client
try:
    client = TelegramClient('session', api_id=api_id, api_hash=api_hash)
    print("Client initialized successfully.")
except Exception as e:
    print(f"Failed to initialize client: {e}")
