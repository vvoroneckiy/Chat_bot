import os
import logging
import asyncio
from dotenv import load_dotenv

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

from bot.handlers.vk_handler import process_message

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def send_message(vk, user_id, text, keyboard=None, attachment=None):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=get_random_id(),
            keyboard=keyboard,
            attachment=attachment
        )
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")

async def bot_loop():
    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    
    try:
        longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)
        logging.info("🚀 БОТ ЗАПУЩЕН (VkBotLongPoll)! Жду сообщения...")
    except Exception as e:
        logging.error(f"Ошибка подключения к LongPoll: {e}")
        return

    loop = asyncio.get_event_loop()

    while True:
        try:
            events = await loop.run_in_executor(None, longpoll.check)
        except Exception as e:
            logging.error(f"Ошибка LongPoll check: {e}")
            await asyncio.sleep(1)
            continue

        for event in events:
            if event.type == VkBotEventType.MESSAGE_NEW:
                msg = event.obj.message
                user_id = msg['from_id']
                text = msg['text']

                result = await process_message(user_id, text, msg, vk)
                
                if isinstance(result, tuple):
                    if len(result) == 3:
                        response, keyboard, attachment = result
                    else:
                        response, keyboard = result
                        attachment = None
                else:
                    response, keyboard, attachment = result, None, None
                
                if response:
                    await loop.run_in_executor(
                        None, lambda: send_message(vk, user_id, response, keyboard, attachment)
                    )

if __name__ == "__main__":
    asyncio.run(bot_loop())
