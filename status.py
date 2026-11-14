import psutil
from datetime import datetime
from plugins.client import client
from telethon import events

# Channel ID for notifications
STATUS_CHANNEL_ID = -1002309648603  # Replace with the actual channel ID

@events.register(events.NewMessage(outgoing=True, pattern=r'^(.status)$'))
async def status(event):
    """
    Send a status message with system information.
    """
    # Get system information
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    cpu_usage = psutil.cpu_percent(interval=1)
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    uptime_s = uptime.total_seconds()
    days, remainder = divmod(uptime_s, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

    # Create a status message
    status_message = f"""
    🤖**Server Status**
━━━━━━━━━━━━━━━━━━━━━━━
🕒 **__Uptime:__** __{uptime_str}__
💾 **__CPU Usage:__** __{cpu_usage}%__
📊 **__Memory Usage:__** __{memory_usage}%__
💿 **__Disk Usage:__** __{disk_usage}%__
━━━━━━━━━━━━━━━━━━━━━━━
    """

    # Replace the original message with status message
    await event.edit(status_message)

async def notify_bot_restart():
    """
    Notify the channel when the bot starts up.
    """
    if hasattr(client, "startup_notified") and client.startup_notified:
        return

    # Set the startup notification flag
    client.startup_notified = True

    # Notify the channel of the bot's restart
    startup_message = f"""
    ⚡ **Bot Restart Detected**
━━━━━━━━━━━━━━━━━━━━━━━━━━
🕒 **__Restart Time:__** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
💾 __Bot is now online and operational.__
━━━━━━━━━━━━━━━━━━━━━━━━━━
    """

    await client.send_message(
        STATUS_CHANNEL_ID,
        startup_message
    )