from app import app
import jwt
from app.exceptions import InvalidTokenException


# Создаем jwt токен, в котором будут храниться:
# user_id, phone, name, lastname, car_num, exp.
def generate_token(user_id, phone, name, last_name, car_num, place, car_type):
    token = jwt.encode({"user_id" : user_id, "phone" : phone,
    "name" : name, "last_name" : last_name, "car_num" : car_num,
    "place" : place, "car_type" : car_type}, 
    app.config['SECRET_KEY'], algorithm = "HS256")
    return token

# Декодируем jwt токен.
# Если декодировать получилось - возвращаем данные из токена в виде словаря.
# Если декодировать не получилось - вызываем ошибку.
def decode_token(token):
    try:
        return jwt.decode(token, app.config['SECRET_KEY'], algorithms = "HS256")
    except:
        raise InvalidTokenException