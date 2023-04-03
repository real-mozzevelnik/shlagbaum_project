class InvalidTokenException(Exception):
    """Вызывается при некоректном декодировании токена."""
    pass


class WrongPasswordException(Exception):
    """Вызывается при неправильном ввода пароля."""
    pass


class UserAlreadyExistsException(Exception):
    """Вызывается в случае, если пользователь с данным номером телефона уже зарегистрирован."""
    pass


class UserDoesntExistsExceptoin(Exception):
    """Вызывается в случае если пользователя не существует."""
    pass


class CarNumAlreadyExistsException(Exception):
    """Вызывается при регистрации нового гостевого тс, 
    если тс с таким номером уже зарегистрировано."""