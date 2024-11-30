import asyncio
import datetime
import csv
import os
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
import nest_asyncio

nest_asyncio.apply()

# Replace with your Telegram API credentials and session
api_id = 1234567  # Your API ID
api_hash = 'your_api_hash'  # Your API hash
session_string = 'your_session_string'

# Group details
group_title = 'groupname'
limit_msg = 100
Repeat_number = 2000

# Start date
datetime_before = datetime.datetime(2024, 9, 3, 22, 6, 3, tzinfo=datetime.timezone.utc)

# Directory for saving media
media_save_path = "downloaded_media"
os.makedirs(media_save_path, exist_ok=True)

async def get_messages(client, group_title, timestamp_before, limit):
    """Fetch messages and media from the group."""
    all_messages = []
    try:
        group = await client.get_entity(group_title)
        posts = await client(GetHistoryRequest(
            peer=group,
            limit=limit,
            offset_date=timestamp_before,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))

        for message in posts.messages:
            message_data = message.to_dict()
            if message.media:
                file_path = await client.download_media(message, file=media_save_path)
                message_data['media_file_path'] = file_path
            else:
                message_data['media_file_path'] = None
            all_messages.append(message_data)

    except FloodWaitError as e:
        print(f"FloodWaitError: Waiting for {e.seconds} seconds")
        await asyncio.sleep(e.seconds)

    except Exception as e:
        print(f"An error occurred: {e}")

    return all_messages

async def save_messages_to_csv(messages, group_title, datetime_before):
    """Save messages to a CSV file."""
    all_fieldnames = set()
    for msg in messages:
        all_fieldnames.update(msg.keys())

    timestamp_str = datetime_before.strftime("%Y-%m-%d--%H-%M-%S")
    file_name = f"{group_title}---UpTo---{timestamp_str}.csv"

    with open(file_name, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(all_fieldnames), restval='')
        writer.writeheader()
        writer.writerows(messages)

    print(f"Saved {len(messages)} messages to {file_name}")

async def main():
    """Main function to fetch and save messages repeatedly."""
    global datetime_before
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        for _ in range(Repeat_number):
            timestamp_before = datetime_before.timestamp()
            all_messages = []

            for i in range(50):  # Inner loop for message fetching
                try:
                    messages = await get_messages(client, group_title, timestamp_before, limit_msg)
                    if messages:
                        datetime_before = messages[-1]['date']
                        timestamp_before = datetime_before.timestamp() - 1
                        all_messages.extend(messages)
                        print(f"Loop {i}: Collected {len(messages)} messages so far.")
                    await asyncio.sleep(1)  # Delay to avoid rate limits
                except FloodWaitError as e:
                    print(f"FloodWaitError in inner loop: Waiting for {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)

            if all_messages:
                await save_messages_to_csv(all_messages, group_title, datetime_before)

await main()
