class NoneEnvVariableError(Exception):
    '''
    Ошибка незаполненной переменной окружения.
    '''
    pass


class ApiRequestError(Exception):
    '''
    Ошибка при обращении к API.
    '''
    pass


class WrongHTTPStatus(Exception):
    '''
    Статус код не 2хх.
    '''
    pass


class HomeWorkApiError(Exception):
    '''
    Ошибка при неправильном наполнении словаря homework в ответе API.
    '''
    pass


class InvalidTelegramToken(Exception):
    '''
    Некорректный токен для бота Telegram
    '''
    pass
