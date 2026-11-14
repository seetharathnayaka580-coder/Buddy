from telethon import events

@events.register(events.NewMessage(outgoing=True, pattern=r'^(\.info)$'))
async def info(event):
    """
    Event handler for the '.info' command.
    Fetches and displays information about the user mentioned in the replied message.
    """
    # Indicate that info is being fetched
    await event.edit('__•Fetching Info....__')

    # Get the user information from the replied message
    user = (await event.get_reply_message()).sender

   # Extract user details
    tg_id = user.id or "None"

    # Create a message with the user information
    msg = f'''
    ━━━━━━━━━━━━━━━━━━━━━
📋 **User Information**
━━━━━━━━━━━━━━━━━━━━━
🆔 **__Telegram ID:__**  `{tg_id}`
━━━━━━━━━━━━━━━━━━━━━
    '''

    # Send the message
    await event.respond(msg)

    # Delete the original message
    await event.message.delete()
