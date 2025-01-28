import sqlite3
from telebot import TeleBot, types
import time
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler
import telegram.ext.filters as filters
# from user_save_profiles import *

from datetime import datetime, date

BOT_TOKEN = '7702064015:AAHkpI7E_xTuo4Wvn7VVp4kNQAObNCS8JH4'
bot = TeleBot(BOT_TOKEN)

def create_users_table():
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                phone_number TEXT,
                first_name TEXT,
                last_name TEXT,
                school TEXT,
                teacher_name TEXT,
                age INTEGER,
                tickets INTEGER DEFAULT 0,
                last_day_activity DATE,
                free_tickets INTEGER DEFAULT 0,
                post_tickets INTEGER DEFAULT 0,
                montion_tickets INTEGER DEFAULT 0    
            )
        ''')
        conn.commit()


# _____________________________________

def save_user_data(user_id, username, phone_number, first_name, last_name, school, teacher_name, age):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, phone_number, first_name, last_name, school, teacher_name, age, tickets, free_tickets, post_tickets, montion_tickets)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0)
        ''', (user_id, username, phone_number, first_name, last_name, school, teacher_name, age))
        conn.commit()

def create_registration_form(message):
    markup = types.ReplyKeyboardRemove()
    msg = bot.send_message(
        message.chat.id,
        "Привет, Чемпион 🏆\n" 
        "Чтобы поучаствовать в розыгрыше подарков ко дню рождения MAXIMUM нам нужно с тобой познакомиться 🧡🤝\n\n" +
        "Заполни немного информации о себе, чтобы я знал имя будущего победителя 🥰\n\n" +
        "1. Имя:\n" +
        "2. Фамилия:\n" +
        "3. номер телефона из Личного кабинета:\n" +
        "4. Школа:\n" +
        "5. Имя преподавателя/куратора сообщившего о розыгрыше:\n" +
        "6. Возраст:\n\n" +
        "Введи данные в одном сообщении начиная с новой строки, например:\n" +
        "Иван\nПетров\n+79991234567\nШкола №1\nАртём Кармаз\n16",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_registration_form)

def check_user_exists(user_id):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
    return user is not None

def process_registration_form(message):
    try:
        if check_user_exists(message.from_user.id):
            user = get_user_by_id(message.from_user.id)
            bot.send_message(
                message.chat.id, 
                f"Привет, {user[3]}!"
            )
            return

        data = message.text.split('\n')
        if len(data) != 6:
            raise ValueError("Неверный формат данных")

        first_name, last_name, phone_number, school, teacher_name, age = data

        markup = types.InlineKeyboardMarkup()
        approve_btn = types.InlineKeyboardButton("Все верно!", callback_data="approve_registration")
        edit_btn = types.InlineKeyboardButton("Редактировать", callback_data="edit_registration")
        markup.row(approve_btn, edit_btn)

        bot.session_data[message.chat.id] = {
            'user_id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': phone_number,
            'school': school,
            'teacher_name': teacher_name,
            'age': int(age)
        }

        bot.send_message(
            message.chat.id, 
            f"Проверьте введенные данные:\n\n" +
            f"Имя: {first_name}\n" +
            f"Фамилия: {last_name}\n" +
            f"Телефон: {phone_number}\n" +
            f"Школа: {school}\n" +
            f"Преподаватель: {teacher_name}\n" +
            f"Возраст: {age}",
            reply_markup=markup
        )


    except Exception as e:
        bot.send_message(
            message.chat.id, 
            f"Вводи данные также как в примере! \n А возраст вводи числом! \n ＼（〇_ｏ）／"
        )
        create_registration_form(message)

def get_user_by_username(username):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
    return user

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_registration') or call.data.startswith('edit_registration'))
def handle_registration_callback(call):
    if check_user_exists(call.from_user.id):
        start(call.message)
        return
    if call.data == 'approve_registration':
        user_data = bot.session_data.get(call.message.chat.id, {})
        save_user_data(
            user_data['user_id'],
            user_data['username'], 
            user_data['phone_number'], 
            user_data['first_name'], 
            user_data['last_name'], 
            user_data['school'], 
            user_data['teacher_name'], 
            user_data['age']
        )
        bot.session_data.pop(call.message.chat.id, None)
        bot.answer_callback_query(call.id, "Регистрация завершена!")
        msg = bot.send_message(call.message.chat.id, "Отлично! Теперь нажми /start")
        bot.register_next_step_handler(msg, start)
    elif call.data == 'edit_registration':
        create_registration_form(call.message)

# ___________________________


def create_main_menu_keyboard():
    # """Создание клавиатуры с главным меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("Правила"),
        types.KeyboardButton("Призы")
    )
    markup.row(
        types.KeyboardButton("Бесплатный билет"),
        types.KeyboardButton("Билеты за активность")
    )
    
    markup.row(
        types.KeyboardButton("Профиль"),
        types.KeyboardButton("Мои билеты")
    )
    return markup
# _____________________________________
# БЕСПЛАТНЫЕ БИЛЕТЫ
# _____________________________________

def get_user_tickets(user_id):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT tickets FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result is None:
            return None
        return result[0]

def update_user_tickets(user_id, tickets_to_add=1):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET tickets = tickets + ? 
            WHERE user_id = ?
        ''', (tickets_to_add, user_id))
        conn.commit()

def can_get_free_ticket(user_id):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        today = str(date.today())
        
        cursor.execute('''   
            SELECT last_day_activity, free_tickets	 
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return False
        
        last_activity_date, free_tickets_count = result
        
        if last_activity_date is None or last_activity_date != today:
            cursor.execute('''
                UPDATE users 
                SET last_day_activity = ?, 
                    free_tickets = 1    
                WHERE user_id = ?
            ''', (today, user_id))
            conn.commit()
            return True
         
        if free_tickets_count >= 1:
            return False
        
        cursor.execute('''
            UPDATE users 
            SET free_tickets = free_tickets + 1  
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        
    return True


@bot.message_handler(func=lambda message: message.text == "Бесплатный билет")
def free_ticket(message):
    user_id = message.from_user.id
    
    if can_get_free_ticket(user_id):
        update_user_tickets(user_id)
        tickets = get_user_tickets(user_id)
        message_text = """Ты получил 1 бесплатный билет на сегодня! 💸
    Теперь переходи к другим действиям, чтобы заработать еще больше билетов и выиграть в розыгрыше 😍

    Забирай гарантированный приз по <a href="https://disk.yandex.ru/d/UlCdu7frVeLVFQ">ссылке</a>. И возвращайся завтра за новым бесплатным билетом"""
        bot.send_message(
            message.chat.id,
            message_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )       
        # bot.send_message(
        #     message.chat.id, 
        #     f"Теперь у вас {tickets} билетов!",
        #     reply_markup=create_main_menu_keyboard()
        # )
    else:
        user = get_user_by_id(message.from_user.id)
        message_text2= """на сегодня все🥲 
Бесплатные билеты закончились, но есть возможность заработать их, рассказывая друзьям о Навигаторе 🫡"""
        bot.send_message(
            message.chat.id, 
            f"{user[3]}, {message_text2}!",
            reply_markup=create_main_menu_keyboard()
        )

@bot.message_handler(func=lambda message: message.text == "Мои билеты")
def show_tickets(message):
    user_id = message.from_user.id
    tickets = get_user_tickets(user_id)
    
    bot.send_message(
        message.chat.id, 
        f"У вас {tickets} билет(ов)!",
        reply_markup=create_main_menu_keyboard()
    )

# _____________________________________
# ПРОФИЛЬ
# _____________________________________

@bot.message_handler(func=lambda message: message.text == "Профиль")
def show_profile(message):
    user_id = message.from_user.id
    
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
    
    profile_text = (
        f"Профиль:\n"
        f"Имя: {user[3]}\n"
        f"Фамилия: {user[4]}\n"
        f"Школа: {user[5]}\n"
        f"Преподаватель: {user[6]}\n"
        f"Возраст: {user[7]}\n"
        f"Билеты: {user[8]}"
    )
    
    bot.send_message(
        message.chat.id, 
        profile_text,
        reply_markup=create_main_menu_keyboard()
    )

# _____________________________________
#  ПРАВИЛА
# ____________________________________-
@bot.message_handler(func=lambda message: message.text == "Правила")
def show_rules(message):
    rules_text = """Твой любимый <b>MAXIMUM</b> отмечает 12 лет🧡
МЫ отметим его на "<u>Навигаторе Поступления</u>" в Санкт-Петербурге (8-9 февраля) и Москве (15-16) февраля 🥳🥳

Мы отметим его масштабно и ждем твоих друзей на нем. <b>Как ты можешь пригласить на ДР своих друзей?</b> 
За каждое <u>приглашение</u> друзей на "<u>Навигатор</u>" ты получишь определенное количество <u>билетов</u>.

    <b>Правило 1:</b> За одно приглашение друзей ты получаешь гарантированный приз! 
А чтобы побороться за более привлекательные призы (в отдельной кнопке есть список) нужно выполнять больше действий. Ведь, чем больше билетов, тем больше шансов выиграть 😎
 
    <b>Правило 2:</b> Как получить билеты? Пригласи друзей и отправь подтверждение:
       1️⃣ бесплатный билет за ежедневное участие в боте + гарантированный приз за участие (Кнопка: "<u>Бесплатный билет</u>")
       
       3️⃣  билета приглашение через чаты с одноклассниками/друзьями ("<u>Билеты за активность</u>")
 
       5️⃣ билета пригласительный пост в своем ТГ-канале или reels/shorts/tt с приглашением на "<u>Навигатор Поступления</u>" ("<u>Билеты за активность</u>") 

    <b>Правило 3:</b> Не удалять посты и ролики до конца розыгрыша - 14 февраля в 16:00 (по мск)"""

    bot.send_message(
        message.chat.id, 
        rules_text,
        parse_mode='HTML',
        reply_markup=create_main_menu_keyboard()
    )

# _____________________________________
#  Призы
# ____________________________________-
@bot.message_handler(func=lambda message: message.text == "Призы")
def show_prizes(message):
    prizes_text = """14 февраля в 16:00 (по мск) мы подведем итоги розыгрыша 🥰

<b>"Чем больше билетов, тем больше и подарков"</b> - девиз этого розыгрыша. 

Заработав хотя бы 1️⃣ билет ты получаешь <b>гарантированный приз</b> - коллекцию учебников по подготовке к ОГЭ/ЕГЭ 2025 года 😍
 
<b>12 наборов супер-призов</b>, которые мы разыграем среди самых активных учеников: 

<b>1 место</b> 
🏆 Набор <u>Вечеринка</u> 🏖
(Умная колонка Яндекс Станция Лайт 2 с Алисой на YandexGPT) 

<b>2 место:</b> 
🥈 Набор <u>Оптовик</u> 💅🏻
(сертификат в OZON на 3000 рублей) 

<b>3 место:</b> 
🥉 Набор <u>Человек-MAXIMUM</u> 🧡
(худи, чехол на телефон, шоппер с логотипом MAXIMUM Education) 

<b>4 место:</b> 
Набор <u>Chill guy</u> 😎
(кружка, бутылка, футболка с логотипом MAXIMUM Education) 

<b>5-6 место:</b> 
Набор <u>Черепашка-ниндзя</u> 🍕🐢
(4 пиццы в подарок) 

<b>7-8 место:</b> 
Набор <u>sigma</u> 🤫
(Книга о бизнесе с автографом генерального директора MAXIMUM Education и сертификат в ЗЯ на 1000 рублей)

<b>9-12 место:</b> 
Набор <u>студента</u> 🤓
(ручка МЕ + блокнот + значок Навигатора)"""
    bot.send_message(
        message.chat.id, 
        prizes_text,
        parse_mode='HTML',
        reply_markup=create_main_menu_keyboard()
    )
# _____________________________________
#  АКТИВНОСТЬ
# ____________________________________-


# Глобальные константы
MODERATOR_CHANNEL_ID = '@jn_hjpsuhsi'  
ACTIVITY_SCREENSHOTS_GROUP = '@jn_hjpsuhsi'  

def activity_tickets_menu(message):
    """Меню выбора способа получения билетов за активность"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("Отправить скрин"),
        types.KeyboardButton("Отправить ссылку")
    )
    markup.add(types.KeyboardButton("Назад в меню"))
    
    bot.send_message(
        message.chat.id, 
        "Выберите способ подтверждения активности:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "Назад в меню")
def back_home(message):    
    bot.send_message(
        message.chat.id, 
        'Что делаем дальше?',
        reply_markup=create_main_menu_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "Отправить ссылку")
def montion_ticket(message):
    user_id = message.from_user.id
    
    if can_send_url(user_id):
       send_url_instruction(message)
    else:
        bot.send_message(
            message.chat.id, 
            "Вы исчерпали лимит отправки ссылок на сегодня.",
            reply_markup=create_main_menu_keyboard()
        )

def can_send_url(user_id):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        today = date.today()
        
        cursor.execute('''   
            SELECT last_day_activity, montion_tickets	 
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return False
        
        last_activity_date, montion_tickets_count = result
        
        if last_activity_date is None or last_activity_date != str(today):
            return True
         
        if montion_tickets_count >= 3:
            return False
        
    return True

def send_url_instruction(message):
    message_text = """Отправляй ссылку на пост из своего ТГ-канала или на reels/shorts/tt и получай 5️⃣ билетов!!!

Максимальное количество ссылок за день 3️⃣

Текст в посте может быть таким:

В феврале пройдет классное мероприятие "Навигатор Поступления": будут крутые вузы и колледжи🏛, можно определиться с профессией👨🏻‍🏫👩🏼‍🏫 , а также пробник небольшой написать 💯

Я сам был на нем! Там очень круто! Если кто-то сможет пойти, то будет полезно. 
✅На мероприятие необходимо зарегистрироваться✅

Выставка в Санкт-Петербурге (8-9 февраля) <a href="https://stihi.ru/2024/03/03/2963">регистрация</a>
Выставка в Москве (15-16 февраля) <a href="https://stihi.ru/2024/03/03/2963">регистрация</a>
——————

<b>Для reels/shorts/tt:</b>
• Формат может быть разным (мем о поступлении, подготовке, профориентации или рассказ о Навигаторе)
• Полная свобода творчества, но не забывать о базовой самоцензуре
• <b>ВАЖНО:</b> упомянуть аккаунты (MAXIMUM и Навигатора) в reels/shorts/tt, чтобы заработать билеты"""

    bot.send_message(
        message.chat.id,
        message_text,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

    bot.register_next_step_handler(message, process_url)

def process_url(message):
    if message.content_type != 'text':
        bot.send_message(
            message.chat.id, 
            "❌ Вы должны отправить ссылку на пост/историю/шорт!"
        )
        return
    valid_domains = [
        'vk.com','t.me','telegram.me','youtube.com', 'instagram.com'
    ]

    text = message.text.lower()
    is_valid_url = any(domain in text for domain in valid_domains)

    if not is_valid_url:
        bot.send_message(
            message.chat.id,
            "❌ Отправьте корректную ссылку на пост в ВК/Telegram или короткое видео!",
        )
        
        return
   
    markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton(
        "✅ Одобрить", 
        callback_data=f"url_approve_{message.from_user.id}"
    )
    reject_btn = types.InlineKeyboardButton(
        "❌ Отклонить", 
        callback_data=f"url_reject_{message.from_user.id}"
    )
    markup.row(approve_btn, reject_btn)

    bot.forward_message(
        MODERATOR_CHANNEL_ID, 
        message.chat.id, 
        message.message_id
    )

    bot.send_message(
        MODERATOR_CHANNEL_ID, 
        f"Модерация ссылки от пользователя с ID: {message.from_user.id}",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('url_'))
def handle_url_moderation(call):
    action, user_id = call.data.split('_')[1:]
    user_id = int(user_id)
    
    if action == 'approve':
        if update_montion_tickets(user_id):
            bot.send_message(
                user_id, 
                "✅ Ваша ссылка одобрена! Начислено 5 билетов."
            )
            update_user_tickets(user_id, tickets_to_add=5)
        else:
            bot.send_message(
                user_id, 
                "✅ Ваша ссылка одобрена, но лимит билетов за ссылку на сегодня исчерпан."
            )
    
    elif action == 'reject':
        bot.send_message(
            user_id, 
            "❌ К сожалению, ваша ссылка не прошла модерацию. " +
            "Попробуйте загрузить другое подтверждение активности."
        )

    bot.delete_message(
        call.message.chat.id, 
        call.message.message_id
    )

def update_montion_tickets(user_id):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        today = date.today()
        
        cursor.execute('''   
            SELECT last_day_activity, montion_tickets	 
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return False
        
        last_activity_date, montion_tickets_count = result
        if last_activity_date is None or last_activity_date != str(today):
            cursor.execute('''
                UPDATE users 
                SET last_day_activity = ?,
                    montion_tickets = 1
                WHERE user_id = ?
            ''', (today, user_id))

        elif montion_tickets_count < 3:
            cursor.execute('''
                UPDATE users 
                SET montion_tickets = montion_tickets + 1  
                WHERE user_id = ?
            ''', (user_id,))
        else:
            return False
        
        conn.commit()
        return True
    
@bot.message_handler(func=lambda message: message.text == "Отправить скрин")
def post_ticket(message):
    user_id = message.from_user.id
    
    if can_send_screenshot(user_id):
       send_screenshot_instruction(message)
    else:
        bot.send_message(
            message.chat.id, 
            "Вы исчерпали лимит отправки скриншотов на сегодня.",
            reply_markup=create_main_menu_keyboard()
        )

def can_send_screenshot(user_id):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        today = date.today()
        
        cursor.execute('''   
            SELECT last_day_activity, post_tickets	 
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return False
        
        last_activity_date, post_tickets_count = result
        
        if last_activity_date is None or last_activity_date != str(today):
            return True
         
        if post_tickets_count >= 5:
            return False
        
    return True

def send_screenshot_instruction(message):
    message_text = """Отправляй скриншот сообщения в чаты с друзьями/одноклассниками и зарабатывай 3️⃣ билета! 

Максимальное количество за день 5️⃣ 

Держи примерный текст сообщения:

Привет! 
В феврале пройдет классное мероприятие "Навигатор Поступления": будут крутые вузы и колледжи🏛, можно определиться с профессией👨🏻‍🏫👩🏼‍🏫 , а также пробник небольшой написать 💯

Я сам был на нем! Там очень круто! Если кто-то сможет пойти, то будет полезно. 
    ✅На мероприятие необходимо зарегистрироваться✅

Выставка в Санкт-Петербурге (8-9 февраля) <a href="https://stihi.ru/2024/03/03/2963">ссылка</a>
Выставка в Москве (15-16 февраля) <a href="https://stihi.ru/2024/03/03/2963">ссылка</a>
    ——————

<b>Требования:</b>
✅четкое изображение
✅виден получатель и контекст отправки"""

    bot.send_message(
        message.chat.id,
        message_text,
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    bot.register_next_step_handler(message, process_screenshot)

def process_screenshot(message):
    if message.content_type != 'photo' and not (message.content_type == 'document'
         and message.document.mime_type in ['image/jpeg', 'image/png']):
        bot.send_message(
            message.chat.id, 
            "❌ Вы должны отправить изображение!"
        )
        return 
   
    markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton(
        "✅ Одобрить", 
        callback_data=f"screenshot_approve_{message.from_user.id}"
    )
    reject_btn = types.InlineKeyboardButton(
        "❌ Отклонить", 
        callback_data=f"screenshot_reject_{message.from_user.id}"
    )
    markup.row(approve_btn, reject_btn)

    bot.forward_message(
        MODERATOR_CHANNEL_ID, 
        message.chat.id, 
        message.message_id
    )

    bot.send_message(
        MODERATOR_CHANNEL_ID, 
        f"Модерация скриншота от пользователя с ID: {message.from_user.id}",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('screenshot_'))
def handle_screenshot_moderation(call):
    action, user_id = call.data.split('_')[1:]
    user_id = int(user_id)
    
    if action == 'approve':
        if update_post_tickets(user_id):
            bot.send_message(
                user_id, 
                "✅ Ваш скриншот одобрен! Начислено 3 билета."
            )
            update_user_tickets(user_id, tickets_to_add=3)
        else:
            bot.send_message(
                user_id, 
                "✅ Ваш скриншот одобрен, но лимит билетов за скриншоты на сегодня исчерпан."
            )
    
    elif action == 'reject':
        bot.send_message(
            user_id, 
            "❌ К сожалению, ваш скриншот не прошел модерацию. " +
            "Попробуйте загрузить другое подтверждение активности."
        )

    bot.delete_message(
        call.message.chat.id, 
        call.message.message_id
    )

def update_post_tickets(user_id):
    with sqlite3.connect('bot_users.db') as conn:
        cursor = conn.cursor()
        today = date.today()
        
        cursor.execute('''   
            SELECT last_day_activity, post_tickets	 
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return False
        
        last_activity_date, post_tickets_count = result
        if last_activity_date is None or last_activity_date != str(today):
            cursor.execute('''
                UPDATE users 
                SET last_day_activity = ?,
                    post_tickets = 1
                WHERE user_id = ?
            ''', (today, user_id))
            print ( 'хуй')

        elif post_tickets_count < 5:
            cursor.execute('''
                UPDATE users 
                SET post_tickets = post_tickets + 1  
                WHERE user_id = ?
            ''', (user_id,))
        else:
            return False
        
        conn.commit()
        return True


@bot.message_handler(func=lambda message: message.text == "Билеты за активность")
def activity_tickets(message):
    activity_tickets_menu(message)


bot.session_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    create_users_table()
    
    if check_user_exists(message.from_user.id):
        user = get_user_by_id(message.from_user.id)
        bot.send_message(
            message.chat.id, 
            f"Привет, {user[3]}!",
            reply_markup=create_main_menu_keyboard()
        )
    else:
        create_registration_form(message)

          
bot.polling(none_stop=True)