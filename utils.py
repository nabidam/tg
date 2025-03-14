from telethon.tl.patched import Message
from telethon.tl.types import User
from telethon.tl.functions.users import GetFullUserRequest
from telethon import TelegramClient
from sqlite3 import Connection
import os


async def save_user(user: User, client: TelegramClient, conn: Connection):
    cursor = conn.cursor()
    # check for exist
    user_id = user.id

    cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    exists = cursor.fetchone() is not None

    if not exists:
        # insert command
        full = await client(GetFullUserRequest(user))
        bio = full.full_user.about
        bday = (
            f"{full.full_user.birthday.year}-{full.full_user.birthday.month}-{full.full_user.birthday.day}"
            if full.full_user.birthday is not None
            else None
        )

        # save user
        cursor.execute(
            """
                INSERT INTO users (id, first_name, last_name, username, phone, bday, bio, is_verified, is_bot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user_id,
                user.first_name,
                user.last_name,
                user.username,
                user.phone,
                bday,
                bio,
                user.verified,
                user.bot,
            ),
        )
        # Commit the transaction to save changes
        conn.commit()
        print(f"{user.username}:{user_id} - Saved")

        photos = await client.get_profile_photos(user)

        # Download each profile photo
        for i, photo in enumerate(photos):
            # Generate a filename for each photo
            file_path = f"profile_pics/{user.id}_{i}.jpg"

            if not os.path.exists(file_path):
                # Download the photo
                await client.download_media(photo, file_path)

            # save in db
            cursor.execute(
                """
                INSERT INTO avatars (id, user_id, path)
                VALUES (?, ?, ?)
            """,
                (photo.id, user_id, file_path),
            )
            # Commit the transaction to save changes
            conn.commit()
            print(f"Downloaded {file_path}")

        return True
    else:
        return False


async def save_message(message: Message, client: TelegramClient, conn: Connection):
    cursor = conn.cursor()

    # check for id in db
    msg_id = message.id
    cursor.execute("SELECT 1 FROM messages WHERE id = ?", (msg_id,))
    exists = cursor.fetchone() is not None

    if not exists:
        # insert command

        # extract main data
        # id, date, edit_date, message, raw_text,
        # date = f"{message.date.year}-{message.date.month}-{message.date.day} {message.date.hour}:{message.date.minute}:{message.date.second}"
        date = message.date.strftime("%Y-%m-%d %H:%M:%S")
        # edit_date = (
        #     f"{message.edit_date.year}-{message.edit_date.month}-{message.edit_date.day} {message.edit_date.hour}:{message.edit_date.minute}:{message.edit_date.second}"
        #     if message.edit_date is not None
        #     else None
        # )
        edit_date = (
            message.edit_date.strftime("%Y-%m-%d %H:%M:%S")
            if message.edit_date is not None
            else None
        )

        msg_text = message.message
        raw_text = message.raw_text
        sender_id = message.sender_id
        is_sticker = message.sticker is not None
        sticker_emoji = message.file.emoji if is_sticker else None

        # check replies
        is_reply = message.is_reply
        reply_to = (
            message.reply_to_msg_id
            if is_reply and message.reply_to.reply_to_top_id is None
            else None
        )
        topic_id = None
        if message.reply_to is not None:
            topic_id = (
                message.reply_to_msg_id
                if message.reply_to.reply_to_top_id is None
                else message.reply_to.reply_to_top_id
            )

        # check for deleted user
        sender = message.sender
        if isinstance(sender, User):
            await save_user(sender, client, conn)

        # check for file
        has_file = False
        sent_file = None
        msg_file = message.file
        msg_document = message.document
        msg_photo = message.photo
        msg_video = message.video
        if msg_file is not None:
            ext = msg_file.ext
            height = msg_file.height
            width = msg_file.width
            mime_type = msg_file.mime_type
            size = msg_file.size
            sent_file = msg_file.media
        elif msg_photo is not None:
            ext = ".jpg"
            height = None
            width = None
            mime_type = None
            size = None
            sent_file = msg_photo
        elif msg_video is not None:
            ext = ".mp4"
            height = None
            width = None
            mime_type = None
            size = None
            sent_file = msg_video

        if sent_file is not None:
            file_id = sent_file.id

            cursor.execute("SELECT 1 FROM files WHERE id = ?", (file_id,))
            exists = cursor.fetchone() is not None

            if not exists:
                file_path = f"files/{msg_id}_{file_id}.{ext}"

                dl = None
                if not os.path.exists(file_path):
                    print(f"[INFO] msg has file, downloading ...")
                    # Download the photo
                    dl = await client.download_media(sent_file, file_path)

                if dl is not None:

                    has_file = True

                    # save in db
                    cursor.execute(
                        """
                        INSERT INTO files (id, ext, height, width, mime_type, size, path)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (file_id, ext, height, width, mime_type, size, file_path),
                    )
                    # Commit the transaction to save changes
                    conn.commit()
                    print(f"Downloaded {file_path}")
                else:
                    print(f"Coud'nt download {file_id}")

        # save message

        cursor.execute(
            """
                INSERT INTO messages (id, date, edit_date, message, raw_text, is_reply, reply_to, topic_id, sender_id, is_sticker, sticker_emoji, has_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                msg_id,
                date,
                edit_date,
                msg_text,
                raw_text,
                is_reply,
                reply_to,
                topic_id,
                sender_id,
                is_sticker,
                sticker_emoji,
                has_file,
            ),
        )
        # Commit the transaction to save changes
        conn.commit()
        print(f"msg id {msg_id} saved")
        return True
    else:
        return False


async def save_msg_file(message: Message, client: TelegramClient, dl_folder: str = None):
    # check for id in db
    msg_id = message.id

    # check for file
    has_file = False
    sent_file = None
    msg_file = message.file
    msg_document = message.document
    msg_photo = message.photo
    msg_video = message.video
    if msg_file is not None:
        ext = msg_file.ext
        height = msg_file.height
        width = msg_file.width
        mime_type = msg_file.mime_type
        size = msg_file.size
        sent_file = msg_file.media
    elif msg_photo is not None:
        ext = ".jpg"
        height = None
        width = None
        mime_type = None
        size = None
        sent_file = msg_photo
    elif msg_video is not None:
        ext = ".mp4"
        height = None
        width = None
        mime_type = None
        size = None
        sent_file = msg_video

    if sent_file is not None:
        file_id = sent_file.id

        file_path = f"{dl_folder}/{msg_id}_{file_id}.{ext}" if dl_folder is not None else f"gp/{msg_id}_{file_id}.{ext}"

        dl = None
        if not os.path.exists(file_path):
            print(f"[INFO] msg has file, downloading ...")
            # Download the photo
            dl = await client.download_media(sent_file, file_path)
        else:
            print(f"File exists: {file_id}")

        if dl is not None:

            has_file = True

            # save in db
            # Commit the transaction to save changes
            print(f"Downloaded {file_path}")
        else:
            print(f"Coud'nt download {file_id}")
            return False

    # Commit the transaction to save changes
    print(f"msg id {msg_id} saved")
    return True
