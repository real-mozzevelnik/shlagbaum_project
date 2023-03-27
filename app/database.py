import sqlite3
from werkzeug.security import check_password_hash
from email_validator import validate_email, EmailNotValidError

from app.token import generate_token, decode_token

# Класс для взаимодействия с базой данных.
class Database():
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()


    # Метод для создания аккаунта пользователя.
    # Проверяет, существует ли уже пользователь с данной почтой.
    # Пароли хранятся в базе данных в виде хэша.
    # Возвращает jwt токен.
    def create_user(self, mail, hpsw, name, lastname, car_num):
        try:
            # Проверяем, валидна ли почта.
            # Если нет - вызовется исключение, обработанное ниже (EmailNotValidError).
            validate_email(mail)
            # Проверяем, существует ли уже юзер с такой почтой.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE mail = '{mail}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                return {'error' : 'Пользователь с такой почтой уже зарегистрирован.'}
            
            # Создаем нового юзера в базе данных.
            self.__cur.execute(f"""INSERT INTO Users (name, lastname, mail, password, car_num) 
                               VALUES('{name}', '{lastname}', '{mail}', '{hpsw}', '{car_num}')""")
            self.__db.commit()

            # Запрашиваем в дб id юзера, чтобы добавить его в токен.
            self.__cur.execute(f"SELECT user_id FROM Users WHERE mail = '{mail}'")
            res = self.__cur.fetchone()
            access_token = generate_token(res['user_id'], mail, name, lastname, car_num)
            return {'access_token' : access_token}

        # Обрабатываем возможные исключения.
        except EmailNotValidError:
            return {'error' : 'Не валидная почта.'}
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}


    # Метод для входа в аккаунт.
    # Проверяет, существует ли юзер с данной почтой. 
    # Возвращает данные о юзере в токене.
    def retrieve_user(self, mail, password):
        try:
            # Проверяем, существует ли пользователь с такой почтой.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE mail = '{mail}'")
            res = self.__cur.fetchone()
            if res['count'] != 1:
                return {'error' : 'Аккаунта не существует.'}
            
            # Получаем данные из бд.
            self.__cur.execute(f"SELECT user_id, name, lastname, car_num, password FROM Users WHERE mail = '{mail}'")
            res = self.__cur.fetchone()

            # Проверяем пароль и возвращаем данные в токене.
            access_token = generate_token(res['user_id'], mail, res['name'], res['lastname'], res['car_num'])
            return {'access_token' : access_token} if check_password_hash(res['password'], password) else {'error' : 'Неверный пароль.'}

        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
