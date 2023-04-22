from werkzeug.security import generate_password_hash
from flask import request, g, jsonify
import sqlite3

from app.database import Database
from app import app

dbase = None


# Устанавливаем соединение с базой данных.
def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory =  sqlite3.Row
    return conn


# Получаем доступ к базе данных, если его еще нет.
def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


# Как только поступает запрос - устанавливаем соединение с бд.
@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = Database(db)


# Как только запрос обработан - закрываем соединение с бд.
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()



# ! ПРИЛОЖЕНИЕ ПОЛЬЗОВАТЕЛЯ

# Вход пользователя.
@app.route('/login', methods = ["POST"])
def login():
    content = request.json
    res = dbase.retrieve_user(content['phone'] ,content['password'])

    return jsonify(res)


# Добавление гостя.
@app.route("/add_guest", methods = ["POST"])
def add_guest():
    content = request.json
    res = dbase.create_guest(content['token'], content['guest_name'], 
                             content['car_num'], content['one_time_visit'], content['car_type'])

    return jsonify(res)


# Изменения информации и пользователе.
@app.route("/change_user", methods = ["POST"])
def change_user():
    content = request.json
    res = dbase.update_user(content["token"], content["changes"])

    return jsonify(res)


# Удаление пользователя.
@app.route("/del_user", methods = ["POST"])
def del_user():
    content = request.json
    res = dbase.delete_user(content["token"])

    return jsonify(res)


# Удаление гостя.
@app.route("/del_guest", methods = ["POST"])
def del_guest():
    content = request.json
    res = dbase.delete_guest(content["token"], content["guest_id"])

    return jsonify(res)


# Изменение информации о госте.
@app.route("/change_guest", methods = ["POST"])
def change_guest():
    content = request.json
    res = dbase.update_guest(content["token"], content["guest_id"], 
                            content["changes"])
    
    return jsonify(res)


# Проверка существования пользователя.
@app.route("/check_user", methods = ["POST"])
def check_user_existance():
    content = request.json
    res = dbase.does_user_exists(content["token"])

    return jsonify(res)


# Изменение пароля пользователя.
@app.route("/change_password", methods = ["POST"])
def change_psw():
    content = request.json
    res = dbase.change_password(content["token"], content["old_psw"], content["new_psw"])

    return jsonify(res)


# Получение всех гостей конкретного пользователя.
@app.route("/get_guests", methods = ["POST"])
def get_guests():
    content = request.json
    res = dbase.retrieve_guests(content["token"])

    return jsonify(res)


@app.route("/call", methods = ["POST"])
def call():
    content = request.json
    return 1



# ! ПРИЛОЖЕНИЕ АДМИНА.  


# Регистрация пользователя.
@app.route('/registr', methods = ["POST"])
def registr():
    content = request.json
    res = dbase.create_user(content['phone'], 
                                content['name'], content['lastname'], content['car_num'],
                                content['place'], content['car_type'])

    return jsonify(res)