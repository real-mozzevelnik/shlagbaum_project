CREATE TABLE IF NOT EXISTS Users (
    user_id integer PRIMARY KEY AUTOINCREMENT,
    name text NOT NULL,
    lastname text NOT NULL,
    mail text NOT NULL,
    password text NOT NULL,
    car_num text NOT NULL
);

CREATE TABLE IF NOT EXISTS Guests (
    guest_id integer PRIMARY KEY AUTOINCREMENT,
    user_id integer NOT NULL,
    guest_name text NOT NULL,
    car_num text NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users (user_id)
);