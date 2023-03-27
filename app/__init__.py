from flask import Flask
import os

from app.config import SECRET_KEY

# Создаем приложение.
app = Flask(__name__)
# Соединяем его с базой данных.
app.config['SECRET_KEY'] = SECRET_KEY

# Импортируем все руты
from app import views