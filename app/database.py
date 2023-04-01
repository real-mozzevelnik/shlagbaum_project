import sqlite3
from werkzeug.security import check_password_hash
from phonenumbers import is_valid_number

from app.token import generate_token, decode_token

# Класс для взаимодействия с базой данных.
class Database():
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()


    # Метод для создания аккаунта пользователя.
    # Проверяет, существует ли уже пользователь с данным номером телефона.
    # Пароли хранятся в базе данных в виде хэша.
    # Возвращает jwt токен.
    def create_user(self, phone, hpsw, name, lastname, car_num):
        try:
            # Проверяем, валиден ли номер телефона.
            # Если нет - возвращаем ошибку.
            if not is_valid_number(phone):
                return {'error' : 'Не валидный номер телефона.'}
            # Проверяем, существует ли уже юзер с такой почтой.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE phone = '{phone}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                return {'error' : 'Пользователь с такой почтой уже зарегистрирован.'}
            
            # Создаем нового юзера в базе данных.
            self.__cur.execute(f"""INSERT INTO Users (name, lastname, phone, password, car_num) 
                               VALUES('{name}', '{lastname}', '{phone}', '{hpsw}', '{car_num}')""")
            self.__db.commit()

            # Запрашиваем в дб id юзера, чтобы добавить его в токен.
            self.__cur.execute(f"SELECT user_id FROM Users WHERE phone = '{phone}'")
            res = self.__cur.fetchone()
            access_token = generate_token(res['user_id'], phone, name, lastname, car_num)
            return {'access_token' : access_token}

        # Обрабатываем возможные исключения.
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}


    # Метод для входа в аккаунт.
    # Проверяет, существует ли юзер с данной почтой. 
    # Возвращает данные о юзере в токене.
    def retrieve_user(self, phone, password):
        try:
            # Проверяем, валиден ли номер телефона.
            # Если нет - возвращаем ошибку.
            if not is_valid_number(phone):
                return {'error' : 'Не валидный номер телефона.'}
            # Проверяем, существует ли пользователь с таким номером телефона.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE phone = '{phone}'")
            res = self.__cur.fetchone()
            if res['count'] != 1:
                return {'error' : 'Аккаунта не существует.'}
            
            # Получаем данные из бд.
            self.__cur.execute(f"SELECT user_id, name, lastname, car_num, password FROM Users WHERE phone = '{phone}'")
            res = self.__cur.fetchone()

            # Проверяем пароль и возвращаем данные в токене.
            access_token = generate_token(res['user_id'], phone, res['name'], res['lastname'], res['car_num'])
            return {'access_token' : access_token} if check_password_hash(res['password'], password) else {'error' : 'Неверный пароль.'}

        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        
    
    # Метод для добавления гостя.
    def create_guest(self, token, guest_name, car_num):
        try:
            # Пытаемся декодировать токен.
            user_data = decode_token(token)
            # Если не получилось - возвращаем ошибку.
            if not user_data:
                return {'error' : 'Не валидный токен'}
            
            # Проверяем наличие номера авто в таблице гостей.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Guests WHERE car_num = '{car_num}'")
            res = self.__cur.fetchone()
            # Проверяем наличие номера авто в таблице пользователей.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE car_num = '{car_num}'")
            res2 = self.__cur.fetchone()
            # Если нашлось авто с таким номером - возвращаем ошибку.
            if res['count'] or res2['count']:
                return {'error' : 'Авто уже зарегистрировано.'}
            
            # Добавляем данные в бд.
            self.__cur.execute(f"""INSERT INTO Guests (guest_name, car_num, user_id) 
                               VALUES('{guest_name}', '{car_num}', '{user_data['user_id']}')""")
            self.__db.commit()
            return {}
            
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        

    # Метод для изменения данных о пользователе в бд.
    def update_user(self, token, param, new_stat):
        try:
            # Декодируем токен.
            user_data = decode_token(token)
            if not user_data:
                return {'error' : 'Не валидный токен.'}
            
            # Обновлем данные.
            self.__cur.execute(f"""UPDATE Users SET {param} = '{new_stat}' WHERE user_id = '{user_data["user_id"]}'""")
            self.__db.commit()
            
            # Получаем данные из бд для создания нового токена.
            self.__cur.execute(f"SELECT phone, name, lastname, car_num FROM Users WHERE user_id = '{user_data['user_id']}'")
            res = self.__cur.fetchone()

            # Возвращаем новые данные в токене.
            access_token = generate_token(user_data['user_id'], res['phone'], res['name'], res['lastname'], res['car_num'])

            return {"token" : access_token}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        

    def delete_user(self, token):
        try:
            # uset_data = 
            pass

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        

    
