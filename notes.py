from telethon import events
import sqlite3
import time
import asyncio
import plugins.client

# SQLite database file
DB_FILE = "data.db"

# Get the client from the plugins.client module
client = plugins.client.client

# Define the channel ID
channel_id = -1004371612620

def init_db():
    """
    Initialize the SQLite database and create the necessary tables if they do not exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS command_usage (
            user_id INTEGER PRIMARY KEY,
            last_command TEXT,
            last_used INTEGER,
            last_command_rpl_id INTEGER,
            last_command_rpl_chat_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Utility functions for database operations
def execute_query(query, params=(), fetch=False):
    """
    Execute a query on the SQLite database.
    :param query: SQL query to execute
    :param params: Parameters to pass to the query
    :param fetch: Whether to fetch the results
    :return: Fetched results if fetch is True, otherwise None
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall() if fetch else None
        conn.commit()
    return result

def get_users(table):
    """
    Get a list of user IDs from a specified table.
    :param table: Table name to fetch user IDs from
    :return: List of user IDs
    """
    return [row[0] for row in execute_query(f"SELECT user_id FROM {table}", fetch=True)]

def get_last_command_usage(user_id):
    """
    Get the last command usage details for a user.
    :param user_id: User ID to fetch command usage for
    :return: Tuple of (last_command, last_used) if available, otherwise (None, 0)
    """
    result = execute_query(
        "SELECT last_command, last_used FROM command_usage WHERE user_id = ?",
        (user_id,),
        fetch=True
    )
    return result[0] if result else (None, 0)

def update_last_command_usage(user_id, command, timestamp, msg_id, chat_id):
    """
    Update the last command usage details for a user.
    :param user_id: User ID to update command usage for
    :param command: Command used
    :param timestamp: Timestamp of the command usage
    :param msg_id: Message ID of the response
    :param chat_id: Chat ID of the response
    """
    execute_query("""
        INSERT INTO command_usage (user_id, last_command, last_used, last_command_rpl_id, last_command_rpl_chat_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            last_command = excluded.last_command,
            last_used = excluded.last_used,
            last_command_rpl_id = excluded.last_command_rpl_id,
            last_command_rpl_chat_id = excluded.last_command_rpl_chat_id
    """, (user_id, command, timestamp, msg_id, chat_id))

# Cache for approved and disapproved users
user_cache = {
    "approved": [],
    "disapproved": [],
    "last_update": 0
}

def refresh_user_cache():
    """
    Refresh the user cache for approved and disapproved users.
    """
    global user_cache
    if time.time() - user_cache["last_update"] > 60:  # Refresh every 60 seconds
        user_cache["approved"] = get_users('approved_users')
        user_cache["disapproved"] = get_users('disapproved_users')
        user_cache["last_update"] = time.time()

# Define a dictionary of message IDs for different commands
message_ids = {
    '/price': 4,
    '/package': 5,
    '.bank': 7,
    '.ezcash': 6,
    '.reload': 6,
    '.bot1': 6,
    '.bot2': 6,
    '.bot3': 6,
    '.bot4': 6,
    '.iphone': 8,
    '.v2ray': 8,
}

async def public_commands(event):
    """
    Handle public commands and forward the corresponding message.
    :param event: Event containing the command
    :return: New message ID if command is forwarded, otherwise None
    """
    # Get the command from the event's pattern match
    command = event.pattern_match.group()

    # If the command is in the message IDs dictionary, forward the corresponding message
    if command in message_ids:
        result = execute_query(
            "SELECT last_command_rpl_id, last_command_rpl_chat_id FROM command_usage WHERE user_id = ?",
            (event.sender_id,),
            fetch=True
        )

        if result:
            last_command_rpl_id, last_command_rpl_chat_id = result[0]
            # If a previous command reply exists, delete it
            if last_command_rpl_id is not None:
                try:
                    old_message = await client.get_messages(last_command_rpl_chat_id, ids=last_command_rpl_id)
                    if old_message is not None:
                        await old_message.delete()
                except Exception as e:
                    print(f"Error deleting old message: {e}")

        channel_entity = await client.get_entity(channel_id)
        message = await client.get_messages(channel_entity, ids=message_ids[command])
        new_message = await client.forward_messages(event.chat_id, message)

        # Return the new welcome message ID
        return new_message.id


async def private_commands(event):
    """
    Handle private commands and forward the corresponding message.
    :param event: Event containing the command
    """
    # Get the command from the event's pattern match
    command = event.pattern_match.group()

    # If the command is in the message IDs dictionary, forward the corresponding message
    if command in message_ids:
        try:
            # Get the channel entity using the channel ID
            channel_entity = await client.get_entity(channel_id)

            # Get the message using the message ID
            message = await client.get_messages(channel_entity, ids=message_ids[command])

            # Send the message as a new message to the event's chat ID
            await client.forward_messages(event.chat_id, message)
        except Exception as e:
            print(f"Error: {e}")

        # Delete the original command message
        await event.message.delete()


@events.register(events.NewMessage(incoming=True, pattern='/price|/package'))
async def handle_public_commands(event):
    """
    Event handler to handle public commands.
    :param event: Event containing the public command
    """
    refresh_user_cache()  # Refresh cache

    sender = await event.get_sender()
    sender_id = sender.id
    command = event.pattern_match.group()

    if event.is_group or event.is_channel or sender.bot:
        return
    if sender_id in user_cache["approved"] or sender_id in user_cache["disapproved"]:
        pass
    else:
        # Spam prevention logic
        last_command, last_used = get_last_command_usage(sender_id)
        now = int(time.time())
        if last_command == command and now - last_used < 600:  # 10 minutes
            reply = await event.reply("__•Please wait a while before using this command again....__")
            await asyncio.gather(delete_message(reply, 30))
        else:
            new_message_id = await public_commands(event)
            if new_message_id:
                update_last_command_usage(sender_id, command, now, new_message_id, event.chat_id)
                # Schedule deletion of the public command message after 1 hour (3600 seconds)
                try:
                    new_message = await client.get_messages(event.chat_id, ids=new_message_id)
                    if new_message:
                        asyncio.create_task(delete_message(new_message, 3600))
                except Exception as e:
                    print(f"Error scheduling message deletion: {e}")

@events.register(events.NewMessage(outgoing=True, pattern=r'^(\.cclear)$'))
async def clear_command_database(event):
    """
    Event handler to clear the command database.
    :param event: Event triggering the command database clear
    """
    await event.edit('__•Processing....__')
    unknown_users = execute_query("SELECT user_id, last_command_rpl_id, last_command_rpl_chat_id FROM command_usage", fetch=True)

    for user_id, msg_id, chat_id in unknown_users:
        try:
            if msg_id and chat_id:
                old_message = await client.get_messages(chat_id, ids=msg_id)
                if old_message:
                    await old_message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")

    execute_query("DELETE FROM command_usage")
    await event.edit('__•Command database clear completed....__')


@events.register(
    events.NewMessage(
        outgoing=True,
        pattern=r'^(/price|/package|\.bank|\.ezcash|\.reload|\.bot1|\.bot2|\.bot3|\.bot4|\.iphone|\.v2ray)$'
    )
)
async def handle_private_commands(event):
    """
    Event handler to handle private commands.
    :param event: Event containing the private command
    """
    await private_commands(event)

async def delete_message(message, delay):
    """
    Delete a message after a specified delay.
    :param message: Message to delete
    :param delay: Delay in seconds before deletion
    """
    await asyncio.sleep(delay)
    try:
        await message.delete(revoke=True)
    except Exception as e:
        print(f"Error deleting message after delay: {e}")
