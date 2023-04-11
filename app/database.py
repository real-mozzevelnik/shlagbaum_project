import sqlite3
from werkzeug.security import check_password_hash
from phonenumbers import is_valid_number, parse, NumberParseException

from app.token import generate_token, decode_token
from app.exceptions import InvalidTokenException, CarNumAlreadyExistsException, UserAlreadyExistsException, UserDoesntExistsExceptoin, WrongPasswordException, NotYourCarException, NotYourGuestException

# Класс для взаимодействия с базой данных.
class Database():
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()


    # Метод для проверки наличия номера машины гостя в бд.
    def check_guest_car_num(self, car_num):
        # Проверяем наличие номера авто в таблице гостей.
        self.__cur.execute(f"SELECT COUNT() as 'count' FROM Guests WHERE car_num = '{car_num}'")
        res = self.__cur.fetchone()
        # Проверяем наличие номера авто в таблице пользователей.
        self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE car_num = '{car_num}'")
        res2 = self.__cur.fetchone()
        # Если нашлось авто с таким номером - возвращаем ошибку.
        if res['count'] or res2['count']:
            raise CarNumAlreadyExistsException


    # Метод для создания аккаунта пользователя.
    # Проверяет, существует ли уже пользователь с данным номером телефона.
    # Пароли хранятся в базе данных в виде хэша.
    # Возвращает jwt токен.
    def create_user(self, phone, hpsw, name, lastname, car_num):
        try:
            # Заменяем первую восьмерку в номере телефона на +7.
            if phone[0] == '8':
                phone = phone.replace('8', '+7', 1)
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
            # Заменяем первую восьмерку в номере телефона на +7.
            if phone[0] == '8':
                phone = phone.replace('8', '+7', 1)
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
            
            # Проверяем, не существует ли уже номер авто в бд.
            self.check_guest_car_num(car_num)
            
            visits = 2 if one_time_visit else -1

            # Добавляем данные в бд.
            self.__cur.execute(f"""INSERT INTO Guests (guest_name, car_num, user_id, visits_available) 
                               VALUES('{guest_name}', '{car_num}', '{user_data['user_id']}', '{visits}')""")
            self.__db.commit()

            self.__cur.execute(f"""SELECT guest_id FROM Guests WHERE car_num = '{car_num}'""")
            res = self.__cur.fetchone()

            return {'guest_id' : res['guest_id']}
            
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен'}
        except CarNumAlreadyExistsException:
            return {'error' : 'Авто уже зарегистрировано.'}
        

    # Метод для изменения данных о пользователе в бд.
    def update_user(self, token, changes):
        try:
            # Декодируем токен.
            user_data = decode_token(token)

            # Заменяем первую восьмерку в номере телефона на +7.
            if changes['phone'][0] == '8':
                changes['phone'] = changes['phone'].replace('8', '+7', 1)
            # Проверяем, валиден ли номер телефона.
            # Если нет - возвращаем ошибку, обрабатывая исключение NumberParseException.
            s = parse(changes['phone'])
            if not is_valid_number(s):
                raise NumberParseException(0, 'Not valid ph')
            
            # Если пользователь меняет номер телефона, надо проверить, 
            # не зарегестрирован ли уже этот номер телефона.
            self.__cur.execute(f"SELECT phone FROM Users where user_id = '{user_data['user_id']}'")
            res = self.__cur.fetchone()
            if res['phone'] != changes['phone']:
            
                # Проверяем, существует ли уже юзер с таким номером телефона.
                self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE phone = '{changes['phone']}'")
                res = self.__cur.fetchone()
                if res['count'] > 0:
                    raise UserAlreadyExistsException
            
            # Обновлем данные.
            self.__cur.execute(f"""UPDATE Users SET name = '{changes['name']}', 
            lastname = '{changes['lastname']}', car_num = '{changes['car_num']}', 
            phone = {changes['phone']} WHERE user_id = '{user_data["user_id"]}'""")
            self.__db.commit()

            # Возвращаем новые данные в токене.
            access_token = generate_token(user_data['user_id'], changes['phone'], changes['name'], changes['lastname'], changes['car_num'])

            return {"token" : access_token}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except NumberParseException:
            return {'error' : 'Не валидный номер телефона.'}
        except UserAlreadyExistsException:
            return {'error' : 'Пользователь с таким номером телефона уже зарегистрирован.'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        

    # Метод для удаления пользователя.
    def delete_user(self, token):
        try:
            # Декодируем токен.
            user_data = decode_token(token)
            
            # Удаляем гостей пользователя.
            self.__cur.execute(f"""DELETE FROM Guests WHERE user_id = '{user_data['user_id']}'""")
            # Удаляем самого пользователя.
            self.__cur.execute(f"""DELETE FROM Users WHERE user_id = '{user_data['user_id']}'""")
            self.__db.commit()

            return {}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        

    # Метод для удаления гостя.
    def delete_guest(self, token, guest_id):
        try:
            # Декодируем токен.
            user_data = decode_token(token)

            # Проверяем, принадлежит ли гость данному пользователю.
            self.__cur.execute(f"SELECT user_id FROM Guests WHERE guest_id = '{guest_id}'")
            res = self.__cur.fetchone()

            if res['user_id'] != user_data['user_id']:
                raise NotYourGuestException
            
            # Удаляем гостя.
            self.__cur.execute(f"DELETE FROM Guests WHERE guest_id = '{guest_id}'")
            self.__db.commit()

            return {}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        except NotYourGuestException:
            return {'error' : 'Гость вам не принадлежит.'}
        

    # Метод для изменения информации о госте.
    def update_guest(self, token, guest_id, changes):
        try:
            # Декодируем токен.
            user_data = decode_token(token)
            # Проверяем, существует ли в бд тс с таким номером, и принадлежит ли оно к данному пользователю.
            self.__cur.execute(f"SELECT user_id, car_num FROM Guests WHERE guest_id = '{guest_id}'")
            res = self.__cur.fetchone()
            # Если нет - вызываем исключение.
            if not res or user_data['user_id'] != res['user_id']:
                raise NotYourCarException
            
            # Если пользователь меняет номер машины гостя - проверяем нет ли уже такого номера в бд.
            if changes['car_num'] != res['car_num']:
                self.check_guest_car_num(changes['car_num'])

            # Обновляем статус гостя.
            visits = 2 if changes['one_time_visit'] else -1
            
            # Обновлем данные.
            self.__cur.execute(f"""UPDATE Guests SET guest_name = '{changes['guest_name']}', 
                car_num = '{changes['car_num']}', visits_available = '{visits}' 
                WHERE guest_id = '{guest_id}'""")
            self.__db.commit()

            return {'guest_id' : guest_id}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        except NotYourCarException:
            return {'error' : 'Данное тс не является для вас гостевым.'}
        except CarNumAlreadyExistsException:
            return {'error' : 'Авто уже зарегистрировано.'}
        

    # Метод для проверки существования пользователя.
    def does_user_exists(self, token):
        try:
            # Декодируем токен.
            user_data = decode_token(token)
            # Ищем в бд пользователей с совпадающим id.
            self.__cur.execute(f"SELECT COUNT() as count FROM Users WHERE user_id = '{user_data['user_id']}'")
            res = self.__cur.fetchone()
            # Если ничего не найдено - выбрасываем ошибку.
            if not res:
                raise UserDoesntExistsExceptoin
            return {}
        
        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        except UserDoesntExistsExceptoin:
            return {'error' : 'Пользователь не зерегистрирован.'}
        

    # Метод для изменения пароля пользователя.
    def change_password(self, token, old_psw, new_psw):
        try:
            # Декодируем токен.
            user_data = decode_token(token)
            self.__cur.execute(f"SELECT password FROM Users WHERE user_id = '{user_data['user_id']}'")
            res = self.__cur.fetchone()
            # Проверяем старый пароль на правильность.
            if not check_password_hash(res['password'], old_psw):
                raise WrongPasswordException
            
            # Изменяем данные.
            self.__cur.execute(f"UPDATE Users SET password = '{new_psw}' WHERE user_id = '{user_data['user_id']}'")
            self.__db.commit()

            return {}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        except WrongPasswordException:
            return {'error' : 'Неверный пароль.'}
        

    # Метод для получения всех гостей конкретного пользователя.
    def retrieve_guests(self, token):
        try:
            #  Декодируем токен.
            user_data = decode_token(token)
            # Вытаскиваем всю информацию из бд.
            self.__cur.execute(f"""SELECT guest_id, guest_name, Guests.car_num, 
                               visits_available FROM Guests INNER JOIN Users ON Users.user_id = Guests.user_id 
                               WHERE Users.user_id = '{user_data['user_id']}'""")
            res = self.__cur.fetchall()

            # Упаковываем каждого гостя в более удобную структуру.
            guests_to_send = []

            for i, _ in enumerate(res):
                tmp = list(res[i])
                one_time_visit = True if tmp[3] > 0 else False
                tmp_dict = {'guest_id' : tmp[0], 'guest_name' : tmp[1], 'car_num' : tmp[2], "one_time_visit" : one_time_visit}

                guests_to_send.append(tmp_dict)

            return {'guests' : guests_to_send}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}

    
    
