from plugins import client, pmpermit, alive, quote, notes, info, status

# Get the client instance
client = client.client

# List of event handlers
event_handlers = [
    pmpermit.incoming_messages,
    pmpermit.manage_user,
    pmpermit.get_user_list,
    pmpermit.clear_user_database,
    alive.alive,
    quote.quote,
    notes.handle_public_commands,
    notes.handle_private_commands,
    notes.clear_command_database,
    info.info,
    status.status
]

# Connect to the client
with client as user:
    # Add each event handler to the client
    for event_handler in event_handlers:
        user.add_event_handler(event_handler)
    
    # Notify the channel of the bot's restart
    user.loop.run_until_complete(status.notify_bot_restart())

# Print a message indicating that the bot is running
print('''
╔══════════════════════════════╗
║                              ║
║       Bot is now online      ║
║                              ║
╚══════════════════════════════╝
''')

# Start the client and keep it running until disconnected
client.start()
client.run_until_disconnected()