import sqlite3
import time
import asyncio
from telethon import events
import plugins.client

# SQLite database file
DB_FILE = "data.db"

# Set up the Telethon client
client = plugins.client.client

# Define the channel ID and message IDs
channel_id = -1002369469078
welcome_message_id = 2
warning_message_id = 11

def init_db():
    """
    Initialize the SQLite database and create the necessary tables if they do not exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approved_users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disapproved_users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unknown_users (
            user_id INTEGER PRIMARY KEY,
            last_welcome INTEGER
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

async def add_user(table, user_id):
    """
    Add a user to a specified table.
    :param table: Table name to add the user to
    :param user_id: User ID to add
    """
    execute_query(f"INSERT OR IGNORE INTO {table} (user_id) VALUES (?)", (user_id,))
    # Remove from unknown users when approved/disapproved
    execute_query("DELETE FROM unknown_users WHERE user_id = ?", (user_id,))

async def remove_user(table, user_id):
    """
    Remove a user from a specified table.
    :param table: Table name to remove the user from
    :param user_id: User ID to remove
    """
    execute_query(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
    # Remove from unknown users when removed from approved/disapproved
    execute_query("DELETE FROM unknown_users WHERE user_id = ?", (user_id,))

def get_users(table):
    """
    Get a list of user IDs from a specified table.
    :param table: Table name to fetch user IDs from
    :return: List of user IDs
    """
    return [row[0] for row in execute_query(f"SELECT user_id FROM {table}", fetch=True)]

def get_last_welcome(user_id):
    """
    Get the last welcome timestamp for a user.
    :param user_id: User ID to fetch last welcome for
    :return: Last welcome timestamp if available, otherwise 0
    """
    result = execute_query(
        "SELECT last_welcome FROM unknown_users WHERE user_id = ?", (user_id,), fetch=True
    )
    return result[0][0] if result else 0

def set_last_welcome(user_id, timestamp):
    """
    Set the last welcome timestamp for a user.
    :param user_id: User ID to set timestamp for
    :param timestamp: Timestamp of the last welcome
    """
    execute_query("""
        INSERT INTO unknown_users (user_id, last_welcome)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            last_welcome = excluded.last_welcome
    """, (user_id, timestamp))

@events.register(events.NewMessage(incoming=True))
async def incoming_messages(event):
    """
    Event handler for incoming messages. This function processes incoming messages and determines if the sender is approved, disapproved, or unknown. 
    If the sender is unknown and has not received a welcome message in the last 24 hours, a welcome message is sent.
    :param event: Event containing the incoming message. The event object includes details about the message, sender, and chat.
    """
    sender = await event.get_sender()
    sender_id = sender.id
    
    # Ignore group, channel, and bot messages
    if event.is_group or event.is_channel or sender.bot or sender.contact:
        return
    if sender_id in get_users('approved_users'):
        pass
    elif sender_id in get_users('disapproved_users'):
        await warning_message(event)
    else:
        last_welcome = get_last_welcome(sender_id)
        if time.time() - last_welcome > 86400:  # 86400 seconds = 24 hours
            await welcome_message(event)
            set_last_welcome(sender_id, int(time.time()))

@events.register(events.NewMessage(outgoing=True, pattern=r'^(\.au|\.du|\.ru)$'))
async def manage_user(event):
    """
    Event handler to manage users (approve, disapprove, reset).
    :param event: Event containing the management command
    """
    if event.is_reply:
        replied_message = await event.get_reply_message()
        sender_id = replied_message.sender_id
        aproved_users = get_users('approved_users')
        disapproved_users = get_users('disapproved_users')

        if event.pattern_match.group() == '.au':  # Approve user
            if sender_id in aproved_users:
                await event.edit('__•User is already in the approved list....__')
            elif sender_id in disapproved_users:
                await remove_user('disapproved_users', sender_id)
                await add_user('approved_users', sender_id)
                await event.edit('__•User has been removed from disapproved list and added to approved list....__')
            else:
                await add_user('approved_users', sender_id)
                await event.edit('__•User has been added to approved list....__')

        elif event.pattern_match.group() == '.du':  # Disapprove user
            if sender_id in disapproved_users:
                await event.edit('__•User is already in the disapproved list....__')
            elif sender_id in aproved_users:
                await remove_user('approved_users', sender_id)
                await add_user('disapproved_users', sender_id)
                await event.edit('__•User has been removed from approved list and added to disapproved list....__')
            else:
                await add_user('disapproved_users', sender_id)
                await event.edit('__•User has been added to disapproved list....__')

        elif event.pattern_match.group() == '.ru':  # Remove user
            if sender_id in aproved_users:
                await remove_user('approved_users', sender_id)
                await event.edit('__•User has been removed from approved list....__')
            elif sender_id in disapproved_users:
                await remove_user('disapproved_users', sender_id)
                await event.edit('__•User has been removed from disapproved list....__')
            else:
                await event.edit('__•User is not in approved list nor disapproved list....__')
        
        await asyncio.gather(delete_message(event.message, 10))

    else:
        await event.edit('__•Please reply to a message....__')
        await asyncio.gather(delete_message(event.message, 15))

@events.register(events.NewMessage(outgoing=True, pattern=r'^(\.al|\.dl)$'))
async def get_user_list(event):
    """
    Event handler to get the list of approved or disapproved users.
    :param event: Event containing the command to get user list
    """
    table = 'approved_users' if event.pattern_match.group() == '.al' else 'disapproved_users'
    user_type = "Approved" if table == 'approved_users' else "Disapproved"

    user_ids = get_users(table)

    if not user_ids:
        await event.edit(f'__•No {user_type.lower()} users found....__')
        return

    user_list = []
    for user_id in user_ids:
        try:
            user = await client.get_entity(user_id)
            if user.username:
                user_list.append(f'@{user.username}')
            else:
                user_list.append(user.first_name)
        except Exception as e:
            print(f"Error fetching user: {e}")
            user_list.append(f"User {user_id} (unavailable)")

    user_list_text = '\n'.join(user_list)
    await event.edit(f'{user_type} users:\n{user_list_text}')

@events.register(events.NewMessage(outgoing=True, pattern=r'^(\.uclear)$'))
async def clear_user_database(event):
    """
    Event handler to clear the user database.
    :param event: Event triggering the user database clear
    """
    await event.edit('__•Processing....__')
    execute_query("DELETE FROM unknown_users")
    await event.edit('__•Database clear completed....__')

async def welcome_message(event):
    """
    Send a welcome message to the user and schedule auto-deletion after 1 hour.
    :param event: Event containing the incoming message
    """
    channel_entity = await client.get_entity(channel_id)
    message = await client.get_messages(channel_entity, ids=welcome_message_id)
    new_message = await client.forward_messages(event.chat_id, message)
    
    # Schedule auto-deletion after 1 hour (3600 seconds)
    asyncio.create_task(delete_message(new_message, 3600))

async def warning_message(event):
    """
    Send a warning message to the user.
    :param event: Event containing the incoming message
    """
    try:
        channel_entity = await client.get_entity(channel_id)
        message = await client.get_messages(channel_entity, ids=warning_message_id)
        await client.forward_messages(event.chat_id, message, channel_entity)
    except Exception as e:
        print(f"Error: {e}")

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
        print(f"Error deleting message: {e}")
