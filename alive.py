from telethon import events
from datetime import datetime
import os

# Get the current time as the start time
start_time = datetime.now()

# Registering an event handler for the outgoing message with the pattern '.alive'
@events.register(events.NewMessage(outgoing=True, pattern=r'^(\.alive)$'))
async def alive(event):
    # Calculate the uptime of the bot
    end_time = datetime.now()
    uptime = end_time - start_time
    uptime_s = uptime.total_seconds()
    days = divmod(uptime_s, 86400)
    hours = divmod(days[1], 3600)
    minutes = divmod(hours[1], 60)
    seconds = divmod(minutes[1], 1)
    uptime_f = (f"{int(days[0])}d: "
                f"{int(hours[0])}h: "
                f"{int(minutes[0])}min: "
                f"{int(seconds[0])}sec"
                )

    # Measure the ping duration by sending a 'Pong!' message
    start = datetime.now()
    pong_message = await event.respond("Pong!")
    end = datetime.now()
    duration = (end - start).microseconds / 1000

    # Get information about the user and create a caption with the uptime, ping, and other details
    user = await event.client.get_me()
    profile_pic = await event.client.download_profile_photo(user)
    first_name = user.first_name or "None"
    last_name = user.last_name or ""

    cap = f'''
    👑 **Hello, Lord** {first_name} {last_name}!
__I am alive and ready to serve you, My Lord__

🔹 __**Uptime:** {uptime_f}__
🔹 __**Ping:** {duration}ms__

⚙️__**Crafted by:** @TheErrorR__
    '''

    # Send the caption with the profile picture if available, otherwise respond with the caption
    if profile_pic:
        await event.client.send_file(event.chat_id, file=profile_pic, caption=cap)
        os.remove(profile_pic)
    else:
        await event.respond(cap)

    # Delete the original message and the 'Pong!' message
    await event.delete()
    await pong_message.delete()
