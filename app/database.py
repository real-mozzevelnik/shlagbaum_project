import sqlite3
from werkzeug.security import check_password_hash
from phonenumbers import is_valid_number, parse, NumberParseException

from app.token import generate_token, decode_token
from app.exceptions import InvalidTokenException, CarNumAlreadyExistsException, UserAlreadyExistsException, UserDoesntExistsExceptoin, WrongPasswordException, NotYourCarException

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
            # Если нет - возвращаем ошибку, обрабатывая исключение NumberParseException.
            s = parse(phone)
            if not is_valid_number(s):
                raise NumberParseException(0, 'Not valid ph')
            # Проверяем, существует ли уже юзер с таким номером телефона.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE phone = '{phone}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                raise UserAlreadyExistsException
            
            # Создаем нового юзера в базе данных.
            self.__cur.execute(f"""INSERT INTO Users (name, lastname, phone, password, car_num) 
                               VALUES('{name}', '{lastname}', '{phone}', '{hpsw}', '{car_num}')""")
            self.__db.commit()

            # Запрашиваем в дб id юзера, чтобы добавить его в токен.
            self.__cur.execute(f"SELECT user_id FROM Users WHERE phone = '{phone}'")
            res = self.__cur.fetchone()
            access_token = generate_token(res['user_id'], phone, name, lastname, car_num)
            return {'token' : access_token}

        # Обрабатываем возможные исключения.
        except NumberParseException:
            return {'error' : 'Не валидный номер телефона.'}
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except UserAlreadyExistsException:
            return {'error' : 'Пользователь с таким номером телефона уже зарегистрирован.'}


    # Метод для входа в аккаунт.
    # Проверяет, существует ли юзер с данной почтой. 
    # Возвращает данные о юзере в токене.
    def retrieve_user(self, phone, password):
        try:
            # Проверяем, валиден ли номер телефона.
            # Если нет - возвращаем ошибку, обрабатывая исключение NumberParseException.
            s = parse(phone)
            if not is_valid_number(s):
                raise NumberParseException(0, 'Not valid ph')
            # Проверяем, существует ли пользователь с таким номером телефона.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE phone = '{phone}'")
            res = self.__cur.fetchone()
            if res['count'] != 1:
                raise UserDoesntExistsExceptoin
            
            # Получаем данные из бд.
            self.__cur.execute(f"SELECT user_id, name, lastname, car_num, password FROM Users WHERE phone = '{phone}'")
            res = self.__cur.fetchone()

            # Проверяем пароль и возвращаем данные в токене.
            access_token = generate_token(res['user_id'], phone, res['name'], res['lastname'], res['car_num'])
            if check_password_hash(res['password'], password):
                return {'token' : access_token} 
            else:
                raise WrongPasswordException

        except NumberParseException:
            return {'error' : 'Не валидный номер телефона.'}
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except UserDoesntExistsExceptoin:
            return {'error' : 'Аккаунта не существует.'}
        except WrongPasswordException:
            return {'error' : 'Неверный пароль.'}
        
    
    # Метод для добавления гостя.
    def create_guest(self, token, guest_name, car_num, one_time_visit):
        try:
            # Пытаемся декодировать токен.
            user_data = decode_token(token)
            
            # Проверяем наличие номера авто в таблице гостей.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Guests WHERE car_num = '{car_num}'")
            res = self.__cur.fetchone()
            # Проверяем наличие номера авто в таблице пользователей.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE car_num = '{car_num}'")
            res2 = self.__cur.fetchone()
            # Если нашлось авто с таким номером - возвращаем ошибку.
            if res['count'] or res2['count']:
                raise CarNumAlreadyExistsException
            
            visits = 2 if one_time_visit else -1

            # Добавляем данные в бд.
            self.__cur.execute(f"""INSERT INTO Guests (guest_name, car_num, user_id, visits_available) 
                               VALUES('{guest_name}', '{car_num}', '{user_data['user_id']}', '{visits}')""")
            self.__db.commit()
            return {}
            
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен'}
        except CarNumAlreadyExistsException:
            return {'error' : 'Авто уже зарегистрировано.'}
        

    # Метод для изменения данных о пользователе в бд.
    def update_user(self, token, param, new_stat):
        try:
            # Декодируем токен.
            user_data = decode_token(token)
            
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
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        

    def delete_user(self, token):
        try:
            # Декодируем токен.
            user_data = decode_token(token)
            
            # Удаляем гостей пользователя.
            self.__cur.execute(f"""DELETE FROM Guests where user_id = '{user_data['user_id']}'""")
            # Удаляем самого пользователя.
            self.__cur.execute(f"""DELETE FROM Users where user_id = '{user_data['user_id']}'""")
            self.__db.commit()

            return {}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        

    def update_guest(self, token, guest_car_num, param, new_stat):
        try:
            # Декодируем токен.
            user_data = decode_token(token)
            # Проверяем, существует ли в бд тс с таким номером, и принадлежит ли оно к данному пользователю.
            self.__cur.execute(f"SELECT user_id FROM Guests WHERE car_num = '{guest_car_num}'")
            res = self.__cur.fetchone()
            # Если нет - вызываем исключение.
            if not res or user_data['user_id'] != res['user_id']:
                raise NotYourCarException
            
            # Обновлем данные.
            self.__cur.execute(f"""UPDATE Guests SET {param} = '{new_stat}' WHERE car_num = '{guest_car_num}'""")
            self.__db.commit()

            return {}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        except NotYourCarException:
            return {'error' : 'Данное тс не является для вас гостевым.'}
    
