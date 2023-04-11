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
    pass


class NotYourCarException(Exception):
    """Вызывается в случае, когда пользователь пытается изменить информацию
    не о своем тс."""
    pass


class NotYourGuestException(Exception):
    """Вызывается в случае, когда пользователь пытается удалить не своего гостя."""
    pass