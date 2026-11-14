from telethon import events
import telethon

import plugins.client

# Get the client instance
client = plugins.client.client

@events.register(events.NewMessage(outgoing=True, pattern=r'^(\.qu)$'))
async def quote(event):
    """
    Event handler for the '.qu' command.
    Forwards the replied message to the @QuotLyBot to create a quote.
    """
    quote_bot = '@QuotLyBot'
    
    if event.is_reply:
        replied_message = await event.get_reply_message()
        await event.edit('__•Creating quote....__')

        try:
            # Forwarding the replied message to the quote bot
            quote_chat = await replied_message.forward_to(quote_bot)
        except telethon.errors.rpcerrorlist.YouBlockedUserError:
            # Handle the error when the user has blocked the bot
            await event.respond("__Sorry, you have blocked the @QuotLyBot. Please unblock it and try again....__")
            await event.message.delete()
            return

        # Starting a conversation with the quote bot
        async with client.conversation(quote_bot) as quote_conversation:
            response = await quote_conversation.get_response(quote_chat.id)
            await client.send_read_acknowledge(quote_conversation.chat_id)

        # Deleting the original message and sending the response
        await event.message.delete()
        await client.send_message(event.chat_id, response)
    else:
        await event.edit('__•Please reply to a message....__')
