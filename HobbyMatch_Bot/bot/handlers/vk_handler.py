import json
import httpx
import logging
import os
import aiofiles
from vk_api import VkUpload
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

# Настройки
CORE_API_URL = "http://api:8000/profiles/" 
UPLOAD_DIR = "/app/uploads"
user_states = {}

SKILL_LEVELS = {
    "1": "Новичок (только начинаю)",
    "2": "Любитель (есть базовый опыт)",
    "3": "Продвинутый (уверенно владею)",
    "4": "Эксперт (профи/могу обучать)"
}

HELP_TEXT = (
    "🆘 **СПРАВКА ПО БОТУ**\n"
    "━━━━━━━━━━━━━━\n"
    "📍 **Команды:**\n"
    "• /start — Регистрация\n"
    "• /profile — Твоя анкета\n"
    "• 🔄 Перезаполнить анкету — Сброс данных\n"
    "• 🔍 Найти партнера — Поиск людей\n"
    "━━━━━━━━━━━━━━"
)

MAX_NAME_LEN = 30
MAX_BIO_LEN = 300
MAX_HOBBY_LEN = 50

async def download_vk_photo(url, user_id):
    os.makedirs("/app/uploads", exist_ok=True)
    ext = os.path.splitext(url.split("?")[0])[1] or ".jpg"
    filename = f"{user_id}{ext}"
    local_path = f"/app/uploads/{filename}"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, timeout=15.0)
            if resp.status_code == 200:
                content = resp.content
                if not content:
                    logging.error(f"❌ Пустой ответ при скачивании фото: {url}")
                    return None
                async with aiofiles.open(local_path, mode='wb') as f:
                    await f.write(content)
                logging.info(f"✅ Фото сохранено: {local_path} ({len(content)} байт)")
                return filename
            logging.error(f"❌ HTTP {resp.status_code} при скачивании фото: {url}")
            return None
        except Exception as e:
            logging.error(f"❌ Не удалось скачать фото: {e}")
            return None

def get_main_keyboard(is_registered=False):
    keyboard = VkKeyboard(one_time=False)
    if is_registered:
        keyboard.add_button("🔍 Найти партнера", color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button("📄 Мой профиль", color=VkKeyboardColor.SECONDARY)
        keyboard.add_button("❤️ Мои лайки", color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button("🔄 Перезаполнить анкету", color=VkKeyboardColor.NEGATIVE)
    else:
        keyboard.add_button("🚀 Начать регистрацию", color=VkKeyboardColor.POSITIVE)
    return keyboard.get_keyboard()

def get_back_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("⬅️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def get_search_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("➡️ Следующий", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🏠 В главное меню", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def get_search_profile_keyboard(profile_user_id: int):
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "❤️ Лайк", "payload": "{\"cmd\":\"like\"}"}, "color": "positive"},
                {"action": {"type": "text", "label": "➡️ Следующий", "payload": "{\"cmd\":\"next\"}"}, "color": "primary"}
            ],
            [
                {"action": {"type": "open_link", "link": f"https://vk.com/id{profile_user_id}", "label": "✉️ Написать"}}
            ],
            [
                {"action": {"type": "text", "label": "🏠 В главное меню", "payload": "{\"cmd\":\"menu\"}"}, "color": "secondary"}
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def get_likes_browse_keyboard(profile_user_id: int):
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "➡️ Следующий", "payload": "{\"cmd\":\"next\"}"}, "color": "primary"}
            ],
            [
                {"action": {"type": "open_link", "link": f"https://vk.com/id{profile_user_id}", "label": "✉️ Написать"}}
            ],
            [
                {"action": {"type": "text", "label": "🏠 В главное меню", "payload": "{\"cmd\":\"menu\"}"}, "color": "secondary"}
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)


async def get_search_results(user_id: int):
    async with httpx.AsyncClient() as client:
        try:
            # Стучимся в наш новый эндпоинт
            url = f"http://api:8000/profiles/search/{user_id}"
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logging.error(f"Ошибка поиска: {e}")
            return []

async def get_profile_from_api(user_id: int):
    async with httpx.AsyncClient() as client:
        try:
            url = f"{CORE_API_URL}{user_id}"
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logging.error(f"Ошибка API: {e}")
            return None

async def save_profile_to_api(profile_data: dict):
    async with httpx.AsyncClient() as client:
        try:
            data_to_send = {
                "user_id": int(profile_data.get("user_id")),
                "name": profile_data.get("name"),
                "hobby": profile_data.get("hobby"),
                "city": profile_data.get("city"),
                "skill_level": profile_data.get("skill_level"),
                "has_equipment": bool(profile_data.get("has_equipment")),
                "bio": profile_data.get("bio", ""),
                "photo_path": profile_data.get("photo_path"),
                "photo_attachment": profile_data.get("photo_attachment")
            }
            response = await client.post(CORE_API_URL, json=data_to_send, timeout=5.0)
            return response.status_code in [200, 201]
        except Exception as e:
            logging.error(f"❌ Ошибка сохранения в API: {e}")
            return False

async def upload_photo_to_vk(vk, photo_filename, user_id):
    import asyncio
    full_path = os.path.join("/app/uploads", photo_filename)

    if not os.path.exists(full_path):
        logging.error(f"❗ ФАЙЛ НЕ НАЙДЕН НА ДИСКЕ: {full_path}")
        return None

    loop = asyncio.get_event_loop()
    try:
        upload = VkUpload(vk)
        photo = await loop.run_in_executor(None, lambda: upload.photo_messages(full_path)[0])
        attachment = f"photo{photo['owner_id']}_{photo['id']}"
        logging.info(f"✅ Фото загружено в ВК: {attachment}")
        return attachment
    except Exception as e:
        logging.error(f"❌ ВК отклонил загрузку: {e}")
        return None

async def ensure_photo_attachment(vk, profile: dict, user_id: int):
    attach = profile.get('photo_attachment')
    if attach:
        return attach
    photo_path = profile.get('photo_path')
    if photo_path:
        attach = await upload_photo_to_vk(vk, photo_path, user_id)
        if attach:
            profile['photo_attachment'] = attach
            await save_profile_to_api(profile)
    return attach

async def show_search_profile(vk, state, user_id):
    results = state.get("search_results", [])
    index = state.get("search_index", 0)
    
    if index >= len(results):
        state["step"] = None
        return ("✨ Вы посмотрели все доступные анкеты!", get_main_keyboard(True), None)
    
    user = results[index]
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"http://api:8000/profiles/{user['user_id']}/view",
                json={"viewer_id": user_id},
                timeout=5.0
            )
        except:
            pass
    
    views = (user.get('views_count') or 0) + 1
    msg = (f"👤 {user['name']}, {user['city']}\n"
           f"🎯 Хобби: {user['hobby']}\n"
           f"📊 Уровень: {user['skill_level']}\n"
           f"📝 О себе: {user.get('bio', '...')}\n"
           f"👁 Просмотров: {views}")
    
    attachment = await ensure_photo_attachment(vk, user, user['user_id'])
        
    return (msg, get_search_profile_keyboard(user['user_id']), attachment)

async def show_like_profile(vk, state, user_id):
    results = state.get("likes_list", [])
    index = state.get("likes_index", 0)

    if index >= len(results):
        state["step"] = None
        return ("✨ Это все кто вас лайкал!", get_main_keyboard(True), None)

    user = results[index]

    eq = "✅ Есть" if user.get('has_equipment') else "❌ Нет"
    msg = (f"👤 {user['name']}, {user['city']}\n"
           f"🎯 Хобби: {user['hobby']}\n"
           f"📊 Уровень: {user['skill_level']}\n"
           f"🎒 Снаряжение: {eq}\n"
           f"📝 О себе: {user.get('bio', '...')}")

    attachment = await ensure_photo_attachment(vk, user, user['user_id'])

    return (msg, get_likes_browse_keyboard(user['user_id']), attachment)


# --- Основная логика ---
async def process_message(user_id: int, text: str, message=None, vk=None) -> tuple:
    user_id = int(user_id)
    clean_text = text.lower().strip()

    if user_id not in user_states:
        user_states[user_id] = {"registered": False, "step": None}
    
    state = user_states[user_id]

    # Восстановление сессии
    if state.get("step") is None and not state.get("registered"):
        remote_profile = await get_profile_from_api(user_id)
        if remote_profile:
            state.update({**remote_profile, "registered": True, "step": None})

    is_registered = state.get("registered", False)
    current_step = state.get("step")

    # Уведомление о новых лайках
    if is_registered and vk:
        async with httpx.AsyncClient() as client:
            try:
                unread_resp = await client.get(
                    f"http://api:8000/profiles/{user_id}/likes/unread",
                    timeout=5.0
                )
                if unread_resp.status_code == 200:
                    unread = unread_resp.json()
                    if unread:
                        await client.post(
                            f"http://api:8000/profiles/{user_id}/likes/mark-read",
                            timeout=5.0
                        )
                        if len(unread) == 1:
                            notify_text = f"🎉 {unread[0]['name']} лайкнул(а) вашу анкету!"
                        else:
                            names = ", ".join(l['name'] for l in unread)
                            notify_text = f"🎉 Вас лайкнули: {names}"
                        vk.messages.send(
                            user_id=user_id,
                            message=notify_text,
                            random_id=get_random_id()
                        )
            except:
                pass

    # Глобальные команды
    if clean_text in ["/start", "начать", "🚀 начать регистрацию"]:
        if is_registered:
            return ("👋 Вы уже зарегистрированы!", get_main_keyboard(True), None)
        state.update({"user_id": user_id, "step": "name", "registered": False})
        return ("👤 Как вас зовут?", get_back_keyboard(), None)

    elif clean_text in ["/reset", "🔄 перезаполнить анкету"]:
        state.update({"user_id": user_id, "step": "name", "registered": False})
        return ("Окей, давай переделаем анкету. 👤 Как вас зовут?", get_back_keyboard(), None)

    elif clean_text == "❤️ мои лайки":
        if not is_registered:
            return ("⚠️ Сначала зарегистрируйтесь!", get_main_keyboard(False), None)
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"http://api:8000/profiles/{user_id}/likes",
                    timeout=5.0
                )
                if resp.status_code == 200:
                    likers = resp.json()
                    if not likers:
                        return ("😔 У вас пока нет лайков.", get_main_keyboard(True), None)
                    profiles = []
                    for l in likers:
                        try:
                            p_resp = await client.get(
                                f"http://api:8000/profiles/{l['user_id']}",
                                timeout=5.0
                            )
                            if p_resp.status_code == 200:
                                profiles.append(p_resp.json())
                        except:
                            pass
                    if not profiles:
                        return ("😔 Не удалось загрузить анкеты.", get_main_keyboard(True), None)
                    state["likes_list"] = profiles
                    state["likes_index"] = 0
                    state["step"] = "browsing_likes"
                    return await show_like_profile(vk, state, user_id)
            except:
                pass
        return ("⚠️ Ошибка при получении лайков.", get_main_keyboard(True), None)

    elif clean_text in ["/profile", "📄 мой профиль"]:
        if not is_registered:
            return ("⚠️ Сначала пройдите регистрацию!", get_main_keyboard(False), None)

        remote = await get_profile_from_api(user_id)
        if remote:
            state.update(remote)

        attachment = await ensure_photo_attachment(vk, state, user_id)

        eq = "✅ Есть" if state.get('has_equipment') else "❌ Нет"
        views = state.get('views_count') or 0
        msg = (f"━━━━━━━━━━━━━━\n"
               f"👤 Имя: {state.get('name')}\n"
               f"📍 Город: {state.get('city')}\n"
               f"🎯 Хобби: {state.get('hobby')}\n"
               f"📝 О себе: {state.get('bio', 'Не указано')}\n"
               f"📊 Уровень: {state.get('skill_level')}\n"
               f"🎒 Снаряжение: {eq}\n"
               f"👁 Просмотров: {views}")

        return (msg, get_main_keyboard(True), attachment)

    # --- ЛОГИКА ПОИСКА ---
    elif clean_text == "🔍 найти партнера":
        if not is_registered:
            return ("⚠️ Сначала зарегистрируйтесь!", get_main_keyboard(False), None)
        
        # Получаем список из API
        results = await get_search_results(user_id)
        
        if not results:
            return ("😔 В вашем городе пока нет партнеров с таким хобби. Попробуйте позже!", get_main_keyboard(True), None)
        
        # Сохраняем результаты в стейт и ставим индекс на 0
        state["search_results"] = results
        state["search_index"] = 0
        state["step"] = "searching" # Переводим в режим поиска
        
        return await show_search_profile(vk, state, user_id)

    elif current_step == "searching":
        if clean_text == "➡️ следующий":
            state["search_index"] += 1
            return await show_search_profile(vk, state, user_id)
        
        elif clean_text == "❤️ лайк":
            index = state.get("search_index", 0)
            results = state.get("search_results", [])
            if index < len(results):
                liked_user_id = results[index]['user_id']
                liked_user_name = results[index]['name']
                async with httpx.AsyncClient() as client:
                    try:
                        await client.post(
                            f"http://api:8000/profiles/{liked_user_id}/like",
                            json={"from_user_id": user_id},
                            timeout=5.0
                        )
                    except:
                        pass
                # Мгновенное уведомление тому, кого лайкнули
                my_name = state.get('name', 'Пользователь')
                try:
                    vk.messages.send(
                        user_id=liked_user_id,
                        message=f"🎉 {my_name} лайкнул(а) вашу анкету!",
                        random_id=get_random_id()
                    )
                except:
                    pass
            return await show_search_profile(vk, state, user_id)
        
        elif clean_text in ["🏠 в главное меню", "назад", "⬅️ назад"]:
            state["step"] = None
            return ("Возвращаемся в меню", get_main_keyboard(True), None)
    # ---------------------

    elif current_step == "browsing_likes":
        if clean_text == "➡️ следующий":
            state["likes_index"] += 1
            return await show_like_profile(vk, state, user_id)
        elif clean_text in ["🏠 в главное меню", "назад", "⬅️ назад"]:
            state["step"] = None
            return ("Возвращаемся в меню", get_main_keyboard(True), None)

    elif clean_text in ["⬅️ назад", "назад"]:
        state.update({"step": None})
        return ("👋 Главное меню", get_main_keyboard(is_registered), None)

    elif clean_text in ["/help", "❓ помощь"]:
        return (HELP_TEXT, get_main_keyboard(is_registered), None)

    # Логика шагов регистрации
    if current_step == "name":
        if len(text) > MAX_NAME_LEN:
            return (f"⚠️ Имя слишком длинное.", get_back_keyboard(), None)
        if any(char.isdigit() for char in text):
            return ("⚠️ В имени не должно быть цифр.", get_back_keyboard(), None)
        state.update({"name": text, "step": "hobby"})
        return ("🎨 Ваше хобби?", get_back_keyboard(), None)
    
    elif current_step == "hobby":
        if len(text) > MAX_HOBBY_LEN:
            return ("⚠️ Слишком длинное название.", get_back_keyboard(), None)
        state.update({"hobby": text, "step": "city"})
        return ("📍 Ваш город?", get_back_keyboard(), None)
    
    elif current_step == "city":
        if len(text) < 2 or len(text) > 50:
            return ("⚠️ Введите нормальное название города.", get_back_keyboard(), None)
        state.update({"city": text, "step": "skill"})
        return (f"📊 Уровень мастерства:\n1. Новичок\n2. Любитель\n3. Профи\n4. Эксперт", get_back_keyboard(), None)
    
    elif current_step == "skill":
        if text not in SKILL_LEVELS:
            return ("Введите цифру от 1 до 4.", get_back_keyboard(), None)
        state.update({"skill_level": SKILL_LEVELS[text], "step": "equipment"})
        return ("🎒 Есть снаряжение? (да/нет)", get_back_keyboard(), None)
    
    elif current_step == "equipment":
        ans = text.lower()
        if ans not in ["да", "нет"]:
            return ("Ответьте 'да' или 'нет'.", get_back_keyboard(), None)
        state.update({"has_equipment": (ans == "да"), "step": "bio"})
        return ("📝 Расскажите о себе:", get_back_keyboard(), None)

    elif current_step == "bio":
        if len(text) > MAX_BIO_LEN:
            return ("⚠️ Слишком длинный текст.", get_back_keyboard(), None)
        state.update({"bio": text, "step": "waiting_for_photo"})
        return ("📸 Отправьте фото (вложением):", get_back_keyboard(), None)
    
    elif current_step == "waiting_for_photo":
        attachments = message.get('attachments', []) if message else []
        if attachments and attachments[0].get('type') == 'photo':
            photo_data = attachments[0].get('photo', {})
            url = photo_data.get('sizes', [])[-1].get('url')
            filename = await download_vk_photo(url, user_id)
            if filename:
                attachment = await upload_photo_to_vk(vk, filename, user_id)
                state.update({"photo_path": filename, "photo_attachment": attachment, "registered": True, "step": None})
                if await save_profile_to_api(state):
                    return ("✅ Профиль сохранен!", get_main_keyboard(True), None)
                return ("❌ Ошибка API.", get_main_keyboard(False), None)
        return ("Пожалуйста, отправьте фото.", get_back_keyboard(), None)

    return ("Не понимаю вас. Воспользуйтесь меню:", get_main_keyboard(is_registered), None)