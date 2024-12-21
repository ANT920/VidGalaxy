import dropbox
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка клиента Dropbox
dropbox_access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
if not dropbox_access_token:
    raise ValueError("Нет токена доступа к Dropbox. Убедитесь, что переменная окружения DROPBOX_ACCESS_TOKEN установлена.")

dbx = dropbox.Dropbox(dropbox_access_token)

# Тестовый запрос к Dropbox API
try:
    account_info = dbx.users_get_current_account()
    print("Токен доступа действителен. Информация об аккаунте:")
    print(account_info)
except dropbox.exceptions.AuthError as err:
    print(f"Ошибка аутентификации: {err}")
