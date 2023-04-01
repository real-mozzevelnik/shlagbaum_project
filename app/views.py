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



# Вход пользователя.
@app.route('/login', methods = ["POST"])
def login():
    content = request.json
    res = dbase.retrieve_user(content['phone'] ,content['password'])

    return jsonify(res)


# Регистрация пользователя.
@app.route('/registr', methods = ["POST"])
def registr():
    content = request.json
    hash = generate_password_hash(content['password'])
    res = dbase.create_user(content['phone'], hash, 
                                content['name'], content['lastname'], content['car_num'])

    return jsonify(res)


# Добавление гостя.
@app.route("/add_guest", methods = ["POST"])
def add_guest():
    content = request.json
    res = dbase.create_guest(content['token'], content['guest_name'], 
                             content['car_num'], content['one_time_visit'])

    return jsonify(res)


# Изменения информации и пользователе.
@app.route("/change_user", methods = ["POST"])
def change_user():
    content = request.json
    res = dbase.update_user(content["token"], content["param"], content["new_stat"])

    return jsonify(res)


# Удаление пользователя.
@app.route("/del_user", methods = ["POST"])
def del_user():
    content = request.json
    res = dbase.delete_user(content["token"])

    return jsonify(res)


@app.route("/call", methods = ["POST"])
def call():
    content = request.json
    return 1
