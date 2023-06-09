import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from phonenumbers import is_valid_number, parse, NumberParseException

from app.token import generate_token, decode_token
from app.password import generate_password
from app.logger import Logger
from app.exceptions import InvalidTokenException, CarNumAlreadyExistsException, UserAlreadyExistsException, UserDoesntExistsExceptoin, WrongPasswordException, NotYourCarException, NotYourGuestException, BannedUserException

# Класс для взаимодействия с базой данных.
class Database():
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()
        self.logger = Logger()


    # !  ПРИЛОЖЕНИЕ ЮЗЕРА.


    def check_user_ban(self, user_id):
        self.__cur.execute(f"""SELECT active FROM Users 
                                WHERE user_id = '{user_id}'""")
        act_res = self.__cur.fetchone()
        if not int(act_res['active']):
            raise BannedUserException


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
            self.__cur.execute(f"SELECT * FROM Users WHERE phone = '{phone}'")
            res = self.__cur.fetchone()

            # Проверяем пароль.
            if not check_password_hash(res['password'], password):
                raise WrongPasswordException
            
            # Проверка, забанен ли пользователь.
            self.check_user_ban(res['user_id'])

            # Возвращаем данные в токене.
            access_token = generate_token(res['user_id'], phone, res['name'], res['lastname'], 
                                        res['car_num'], res['place'], res['car_type'])

            return {'token' : access_token}

        except NumberParseException:
            return {'error' : 'Не валидный номер телефона.'}
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except UserDoesntExistsExceptoin:
            return {'error' : 'Аккаунта не существует.'}
        except WrongPasswordException:
            return {'error' : 'Неверный пароль.'}
        except BannedUserException:
            return {'error' : 'Аккаунт заблокирован администратором.'}
        
    
    # Метод для добавления гостя.
    def create_guest(self, token, guest_name, car_num, one_time_visit, car_type):
        try:
            # Пытаемся декодировать токен.
            user_data = decode_token(token)

            # Проверяем, забанен ли пользователь.
            self.check_user_ban(user_data['user_id'])
            
            
            # Проверяем, не существует ли уже номер авто в бд.
            self.check_guest_car_num(car_num)
            
            visits = 2 if one_time_visit else -1

            # Добавляем данные в бд.
            self.__cur.execute(f"""INSERT INTO Guests (guest_name, car_num, user_id, visits_available, car_type, active, location) 
                               VALUES('{guest_name}', '{car_num}', '{user_data['user_id']}', '{visits}', '{car_type}', '{1}', '{0}')""")
            self.__db.commit()

            self.__cur.execute(f"""SELECT guest_id FROM Guests WHERE car_num = '{car_num}'""")
            res = self.__cur.fetchone()

            # Логируем добавление гостя.
            self.logger.log(f"""Пользователь {user_data['name'] + ' ' + user_data['last_name']}, {user_data['phone']}, участок номер {user_data['place']}: \nДобавил гостя {guest_name}, номер машины {car_num}, тип транспорта {car_type}""")

            return {'guest_id' : res['guest_id']}
            
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен'}
        except CarNumAlreadyExistsException:
            return {'error' : 'Авто уже зарегистрировано.'}
        except BannedUserException:
            return {'error' : 'Аккаунт заблокирован администратором.'}
        

    # Метод для изменения номера пользователя.
    def update_phone(self, token, new_phone):
        try:
            # Декодируем токен.
            user_data = decode_token(token)

            # Заменяем первую восьмерку в номере телефона на +7.
            if new_phone[0] == '8':
                new_phone = new_phone.replace('8', '+7', 1)
            # Проверяем, валиден ли номер телефона.
            # Если нет - возвращаем ошибку, обрабатывая исключение NumberParseException.
            s = parse(new_phone)
            if not is_valid_number(s):
                raise NumberParseException(0, 'Not valid ph')
            
            # Если пользователь меняет номер телефона, надо проверить, 
            # не зарегестрирован ли уже этот номер телефона.
            self.__cur.execute(f"SELECT phone FROM Users where user_id = '{user_data['user_id']}'")
            res = self.__cur.fetchone()
            if res['phone'] != new_phone:
            
                # Проверяем, существует ли уже юзер с таким номером телефона.
                self.__cur.execute(f"SELECT COUNT() as 'count' FROM Users WHERE phone = '{new_phone}'")
                res = self.__cur.fetchone()
                if res['count'] > 0:
                    raise UserAlreadyExistsException
            
            # Обновлем данные.
            self.__cur.execute(f"""UPDATE Users SET phone = '{new_phone}'""")
            self.__db.commit()

            # Возвращаем новые данные в токене.
            access_token = generate_token(user_data['user_id'], new_phone, user_data['name'], 
                                          user_data['last_name'], user_data['car_num'], user_data['place'], user_data['car_type'])

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
                car_num = '{changes['car_num']}', visits_available = '{visits}', car_type = '{changes['car_type']}'
                WHERE guest_id = '{guest_id}'""")
            self.__db.commit()

            # Логируем изменение информации.
            self.logger.log(f"""Пользователь {user_data['name'] + ' ' + user_data['last_name']}, {user_data['phone']}, участок номер {user_data['place']}: \nИзменил гостя, новая информация о госте: {changes['guest_name']} номер машины {changes['car_num']}, тип транспорта {changes['car_type']}""")

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
            
            self.check_user_ban(user_data['user_id'])

            return {}
        
        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        except UserDoesntExistsExceptoin:
            return {'error' : 'Пользователь не зерегистрирован.'}
        except BannedUserException:
            return {'error' : 'Аккаунт заблокирован администратором.'}
        

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
            
            new_psw = generate_password_hash(new_psw)
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
                               visits_available, Guests.car_type, Guests.active FROM Guests INNER JOIN Users ON Users.user_id = Guests.user_id 
                               WHERE Users.user_id = '{user_data['user_id']}'""")
            res = self.__cur.fetchall()

            # Упаковываем каждого гостя в более удобную структуру.
            guests_to_send = []

            for i, _ in enumerate(res):
                tmp = list(res[i])
                one_time_visit = True if tmp[3] > 0 else False
                tmp_dict = {'guest_id' : tmp[0], 'guest_name' : tmp[1], 'car_num' : tmp[2], 
                            "one_time_visit" : one_time_visit, "car_type" : tmp[4], "active" : tmp[5]}

                guests_to_send.append(tmp_dict)

            return {'guests' : guests_to_send}

        except sqlite3.Error:
            return {'error' : 'DataBase error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}

    
    # ! ПРИЛОЖЕНИЕ АДМИНА.

    
    # Метод для создания аккаунта пользователя.
    # Аккаунт создается в приложении админа.
    # Проверяет, существует ли уже пользователь с данным номером телефона.
    # Пароли хранятся в базе данных в виде хэша.
    # Возвращает пароль для юзера.
    def create_user(self, phone, name, lastname, car_num, place, car_type):
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
            
            # Генерируем пароль для пользователя.
            password = generate_password()
            # Генерируем хэш пароля для хранения в бд.
            hpsw = generate_password_hash(password)
            
            # Создаем нового юзера в базе данных.
            self.__cur.execute(f"""INSERT INTO Users (name, lastname, phone, 
                                password, car_num, place, car_type, active, location) 
                                VALUES('{name}', '{lastname}', '{phone}', '{hpsw}', 
                                '{car_num}', '{int(place)}', '{car_type}', '{1}', '{0}')""")
            self.__db.commit()

            # Возвращаем пароль.
            return {'password' : password}

        # Обрабатываем возможные исключения.
        except NumberParseException:
            return {'error' : 'Не валидный номер телефона.'}
        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except UserAlreadyExistsException:
            return {'error' : 'Пользователь с таким номером телефона уже зарегистрирован.'}
        

    # Вход для админа.
    def retrieve_admin(self, password):
        try:
            # Проверяем, существует ли админ с таким паролем.
            self.__cur.execute(f"SELECT COUNT() as 'count' FROM Admins WHERE password = '{password}'")
            res = self.__cur.fetchone()
            if res['count'] != 1:
                raise WrongPasswordException
            # Возвращаем токен.
            access_token = generate_token(None, None, "Admin", "Admin", None, None, None)

            return {'token' : access_token}

        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except WrongPasswordException:
            return {'error' : 'Неверный пароль.'}
        
    
    # Получение логов. 
    def retrieve_logs(self, token):
        try:
            # Проверяем токен админа.
            decode_token(token)
            # Получаем логи.
            logs = self.logger.get_log()
            return {'logs' : logs}
        
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        

    # Получение всех пользователей.
    def admin_retrieve_users(self, token):
        try:
            # Проверяем токен админа.
            decode_token(token)
            # Забираем из бд всех пользователей.
            self.__cur.execute("""SELECT * from Users""")
            res = self.__cur.fetchall()

            # Формируем массив с пользователями.
            users_to_send = []

            for i, _ in enumerate(res):
                tmp = list(res[i])
                tmp_dict = {"user_id" : tmp[0], "name" : tmp[1], "lastname" : tmp[2],
                            "phone" : tmp[3], "car_num" : tmp[5], "place" : tmp[6],
                            "car_type" : tmp[7], "active" : tmp[8], "location" : tmp[9]}
                users_to_send.append(tmp_dict)

            return {"users" : users_to_send}

        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        

    # Получение гостей админом.
    def admin_retrieve_guests(self, token, user_id):
        try:
            # Проверяем токен админа.
            decode_token(token)

            # Получаем гостей из бд.
            self.__cur.execute(f"""SELECT * FROM Guests WHERE user_id = '{user_id}'""")
            res = self.__cur.fetchall()

            # Упаковываем каждого гостя в более удобную структуру.
            guests_to_send = []

            for i, _ in enumerate(res):
                tmp = list(res[i])
                one_time_visit = True if tmp[4] > 0 else False
                tmp_dict = {'guest_id' : tmp[0], 'guest_name' : tmp[2], 'car_num' : tmp[3], 
                            "one_time_visit" : one_time_visit, "car_type" : tmp[5], "active" : tmp[6], "location" : tmp[7]}

                guests_to_send.append(tmp_dict)

            return {'guests' : guests_to_send}


        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        

    # Изменение активности пользователя.
    def change_user_active(self, token, user_id, act):
        try:
            # Проверяем токен админа.
            decode_token(token)

            # В зависимости от дейтсвия меняем активность пользователя.
            if act == 'ban':
                active = 0
            else:
                active = 1

            # Записываем изменение в бд.
            self.__cur.execute(f"""UPDATE Users SET active = '{active}' WHERE user_id = '{user_id}'""")
            self.__db.commit()
            # Удаляем всех гостей пользователя.
            self.__cur.execute(f"""DELETE FROM Guests WHERE user_id = '{user_id}'""")
            self.__db.commit()

            return {}

        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}
        

    # Изменение активности гостя.
    def change_guest_active(self, token, guest_id, act):
        try:
            # Проверяем токен админа.
            decode_token(token)

            # В зависимости от дейтсвия меняем активность пользователя.
            if act == 'ban':
                active = 0
            else:
                active = 1

            # Записываем изменение в бд.
            self.__cur.execute(f"""UPDATE Guests SET active = '{active}' WHERE guest_id = '{guest_id}'""")
            self.__db.commit()

            return {}

        except sqlite3.Error:
            return {'error' : 'DataBase Error'}
        except InvalidTokenException:
            return {'error' : 'Не валидный токен.'}      




        
