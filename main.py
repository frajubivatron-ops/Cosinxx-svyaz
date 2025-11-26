import requests
import json
import time
import logging

# Отключаем предупреждения SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8562075568:AAGqPZrcchZW1VcS4M4gcsfrlQuJaesNbKE"
GROUP_CHAT_ID = "-5015568735"

# Хранилище данных о заявках
user_data = {}
applications = {}  # Храним информацию о заявках для кнопок

def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': str(chat_id), 
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, data=data, timeout=10, verify=False)
        result = response.json()
        return result
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return None

def send_photo(chat_id, photo_file_id, caption="", reply_markup=None):
    """Отправка фото"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    data = {
        'chat_id': str(chat_id),
        'photo': str(photo_file_id),
        'caption': caption[:1024],
        'parse_mode': 'HTML'
    }
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, data=data, timeout=10, verify=False)
        result = response.json()
        return result
    except Exception as e:
        logger.error(f"Ошибка отправки фото: {e}")
        return None

def edit_message_reply_markup(chat_id, message_id, reply_markup):
    """Изменяем кнопки сообщения"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageReplyMarkup"
    data = {
        'chat_id': str(chat_id),
        'message_id': message_id,
        'reply_markup': json.dumps(reply_markup)
    }
    
    try:
        response = requests.post(url, data=data, timeout=10, verify=False)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка изменения кнопок: {e}")
        return None

def create_application_keyboard(application_id):
    """Создаем клавиатуру с кнопками одобрения/отказа"""
    return {
        'inline_keyboard': [[
            {
                'text': '✅ Одобрить',
                'callback_data': f'approve_{application_id}'
            },
            {
                'text': '❌ Отказать',
                'callback_data': f'reject_{application_id}'
            }
        ]]
    }

def test_connection():
    """Тестирование соединения с группой"""
    print("🔧 Тестирование подключения к группе...")
    
    result = send_message(GROUP_CHAT_ID, "🤖 Бот запущен и готов принимать заявки!")
    if result and result.get('ok'):
        print("✅ Бот успешно подключен к группе!")
        return True
    else:
        print(f"❌ Ошибка подключения к группе: {result}")
        return False

def generate_application_id():
    """Генерируем уникальный ID для заявки"""
    return str(int(time.time()))

def process_photo_message(chat_id, message, user_info):
    """Обработка фото и отправка в группу с кнопками"""
    if 'photo' in message:
        # Берем самое большое фото
        photo_id = message['photo'][-1]['file_id']
        username = message.get('from', {}).get('username', 'Нет юзернейма')
        user_id = message.get('from', {}).get('id', '')
        
        # Генерируем ID заявки
        application_id = generate_application_id()
        
        # Сохраняем информацию о заявке
        applications[application_id] = {
            'user_id': user_id,
            'username': username,
            'clan_name': user_info.get('clan_name', 'Не указано'),
            'leader': user_info.get('leader', 'Не указан'),
            'player_ids': user_info.get('player_ids', 'Не указаны'),
            'clan_tag': user_info.get('clan_tag', 'Не указан'),
            'photo_id': photo_id,
            'status': 'pending'
        }
        
        # Формируем подпись
        caption = f"""📋 <b>Новая заявка на регистрацию клана!</b>

🏷 <b>Название:</b> {user_info.get('clan_name', 'Не указано')}
👑 <b>Лидер:</b> {user_info.get('leader', 'Не указан')}
🆔 <b>ID игроков:</b> {user_info.get('player_ids', 'Не указаны')}
🔖 <b>Тег клана:</b> {user_info.get('clan_tag', 'Не указан')}
👤 <b>Отправитель:</b> @{username} (ID: {user_id})
🆔 <b>ID заявки:</b> {application_id}"""

        print(f"📤 Отправка данных в группу с кнопками...")
        
        # Создаем клавиатуру с кнопками
        keyboard = create_application_keyboard(application_id)
        
        # Пытаемся отправить фото с подписью и кнопками
        result = send_photo(GROUP_CHAT_ID, photo_id, caption, keyboard)
        
        if result and result.get('ok'):
            send_message(chat_id, 
                "✅ Спасибо! Все данные успешно отправлены в группу!\n"
                "Ваш клан будет рассмотрен администрацией.")
            print("✅ Данные отправлены в группу с кнопками")
            return True
        else:
            # Пробуем отправить текстом с кнопками
            text_message = f"{caption}\n\n📷 Фото приложено"
            text_result = send_message(GROUP_CHAT_ID, text_message, keyboard)
            if text_result and text_result.get('ok'):
                send_message(chat_id, 
                    "✅ Данные отправлены!\n"
                    "Ваш клан будет рассмотрен администрацией.")
                print("✅ Данные отправлены текстом с кнопками")
                return True
            else:
                send_message(chat_id, 
                    "❌ Ошибка при отправке данных.\n"
                    "Попробуйте позже или обратитесь к администратору.")
                print("❌ Ошибка отправки в группу")
                return False
    else:
        send_message(chat_id, "❌ Пожалуйста, отправьте фотографию клана.")
        return False

def handle_callback_query(update):
    """Обработка нажатий на кнопки"""
    callback_query = update.get('callback_query', {})
    data = callback_query.get('data', '')
    message = callback_query.get('message', {})
    message_id = message.get('message_id')
    chat_id = message.get('chat', {}).get('id')
    
    if not data or not message_id:
        return
    
    # Получаем информацию о пользователе, который нажал кнопку
    user = callback_query.get('from', {})
    admin_username = user.get('username', 'Неизвестно')
    admin_id = user.get('id')
    
    if data.startswith('approve_'):
        application_id = data.replace('approve_', '')
        handle_application_approval(application_id, chat_id, message_id, admin_username, admin_id)
        
    elif data.startswith('reject_'):
        application_id = data.replace('reject_', '')
        handle_application_rejection(application_id, chat_id, message_id, admin_username, admin_id)

def handle_application_approval(application_id, chat_id, message_id, admin_username, admin_id):
    """Обработка одобрения заявки"""
    if application_id in applications:
        application = applications[application_id]
        application['status'] = 'approved'
        application['approved_by'] = admin_username
        application['approved_by_id'] = admin_id
        application['approval_time'] = time.time()
        
        # Обновляем кнопки - убираем их
        new_keyboard = {
            'inline_keyboard': [[
                {
                    'text': '✅ ОДОБРЕНО',
                    'callback_data': 'approved'
                }
            ]]
        }
        
        edit_message_reply_markup(chat_id, message_id, new_keyboard)
        
        # Отправляем сообщение пользователю
        user_message = f"""🎉 <b>Поздравляем! Ваша заявка одобрена!</b>

🏷 <b>Название клана:</b> {application['clan_name']}
✅ <b>Статус:</b> Одобрено администратором @{admin_username}

Ваш клан успешно зарегистрирован!"""
        
        send_message(application['user_id'], user_message)
        
        # Отправляем уведомление в группу
        notification = f"✅ Заявка {application_id} одобрена администратором @{admin_username}"
        send_message(chat_id, notification)
        
        print(f"✅ Заявка {application_id} одобрена администратором @{admin_username}")

def handle_application_rejection(application_id, chat_id, message_id, admin_username, admin_id):
    """Обработка отказа заявки"""
    if application_id in applications:
        application = applications[application_id]
        application['status'] = 'rejected'
        application['rejected_by'] = admin_username
        application['rejected_by_id'] = admin_id
        application['rejection_time'] = time.time()
        
        # Обновляем кнопки - убираем их
        new_keyboard = {
            'inline_keyboard': [[
                {
                    'text': '❌ ОТКАЗАНО',
                    'callback_data': 'rejected'
                }
            ]]
        }
        
        edit_message_reply_markup(chat_id, message_id, new_keyboard)
        
        # Отправляем сообщение пользователю
        user_message = f"""❌ <b>Ваша заявка отклонена</b>

🏷 <b>Название клана:</b> {application['clan_name']}
❌ <b>Статус:</b> Отклонено администратором @{admin_username}

По вопросам обращайтесь к администрации."""
        
        send_message(application['user_id'], user_message)
        
        # Отправляем уведомление в группу
        notification = f"❌ Заявка {application_id} отклонена администратором @{admin_username}"
        send_message(chat_id, notification)
        
        print(f"❌ Заявка {application_id} отклонена администратором @{admin_username}")

def process_updates():
    """Основной цикл обработки сообщений"""
    last_update_id = 0
    
    print("🤖 Бот запущен и готов к работе!")
    print(f"📁 Группа для отправки: {GROUP_CHAT_ID}")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {'offset': last_update_id + 1, 'timeout': 25}
            
            response = requests.get(url, params=params, timeout=30, verify=False)
            
            if response.status_code == 200:
                updates = response.json()
                
                if updates.get('ok'):
                    for update in updates.get('result', []):
                        last_update_id = update['update_id']
                        
                        # Обработка callback query (нажатия на кнопки)
                        if 'callback_query' in update:
                            handle_callback_query(update)
                            continue
                        
                        # Обработка обычных сообщений
                        message = update.get('message', {})
                        chat_id = message.get('chat', {}).get('id')
                        text = message.get('text', '')
                        
                        if not chat_id:
                            continue
                        
                        # Пропускаем сообщения из целевой группы
                        if str(chat_id) == str(GROUP_CHAT_ID):
                            continue
                        
                        # Команда /start
                        if text == '/start':
                            user_data[chat_id] = {'step': 'clan_name'}
                            send_message(chat_id, 
                                "Привет! 👋\n"
                                "Я помогу зарегистрировать ваш клан.\n\n"
                                "📝 Напишите название вашего клана:")
                        
                        # Команда /help
                        elif text == '/help':
                            send_message(chat_id,
                                "📋 Помощь:\n"
                                "/start - начать регистрацию клана\n"
                                "/help - показать эту справку\n"
                                "/cancel - отменить текущую регистрацию")
                        
                        # Команда /cancel
                        elif text == '/cancel':
                            if chat_id in user_data:
                                del user_data[chat_id]
                                send_message(chat_id, "❌ Регистрация отменена.")
                            else:
                                send_message(chat_id, "❌ Нет активной регистрации для отмены.")
                        
                        # Обработка текстовых сообщений по шагам
                        elif text and chat_id in user_data:
                            step = user_data[chat_id].get('step')
                            
                            if step == 'clan_name':
                                user_data[chat_id]['clan_name'] = text
                                user_data[chat_id]['step'] = 'leader'
                                send_message(chat_id, "📝 Отлично! Теперь напишите юзернейм лидера:")
                                
                            elif step == 'leader':
                                user_data[chat_id]['leader'] = text
                                user_data[chat_id]['step'] = 'player_ids'
                                send_message(chat_id, "👑 Хорошо! Теперь отправьте ID игроков (через запятую или пробел):")
                                
                            elif step == 'player_ids':
                                user_data[chat_id]['player_ids'] = text
                                user_data[chat_id]['step'] = 'clan_tag'
                                send_message(chat_id, "🆔 Отлично! Теперь отправьте тег клана:")
                                
                            elif step == 'clan_tag':
                                user_data[chat_id]['clan_tag'] = text
                                user_data[chat_id]['step'] = 'photo'
                                send_message(chat_id, 
                                    "🔖 Отлично! Теперь отправьте фотографию клана.\n"
                                    "Это может быть скриншот состава, эмблема или любое другое изображение, связанное с кланом.")
                        
                        # Обработка фото
                        elif message.get('photo') and chat_id in user_data:
                            if user_data[chat_id].get('step') == 'photo':
                                print(f"📷 Получено фото от пользователя {chat_id}")
                                success = process_photo_message(chat_id, message, user_data[chat_id])
                                if success:
                                    # Успешно отправлено - очищаем данные
                                    if chat_id in user_data:
                                        del user_data[chat_id]
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Ошибка в главном цикле: {e}")
            time.sleep(5)

if __name__ == '__main__':
    print("🚀 Запуск бота для регистрации кланов...")
    print("🎯 Теперь с кнопками 'Одобрить' и 'Отказать'!")
    
    # Тестируем подключение
    if test_connection():
        # Запускаем бота
        process_updates()
    else:
        print("❌ Не удалось подключиться к группе. Проверьте:")
        print("1. Правильность ID группы")
        print("2. Что бот добавлен в группу")
        print("3. Что бот имеет права на отправку сообщений")
        print("4. Попробуйте перезапустить бота")
