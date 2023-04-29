from datetime import date, datetime


# Класс для логирования действий.
class Logger:

    def log(self, message):
        # Получаем текущую дату.
        day = date.today().strftime("%d.%m.%Y")
        time = datetime.now().strftime("%H:%M:%S")
        
        # Открываем файл с соответсвующим названием и записываем информацию.
        try:
            with open(f"app/logs/{day}.txt", "a") as f:
                to_write = ['\n-----------------------------------------------------------------\n',
                            time, " ", message,
                            '\n-----------------------------------------------------------------\n']
                f.writelines(to_write)
        except:
            with open(f"app/logs/{day}.txt", "w") as f:
                to_write = ['\n-----------------------------------------------------------------\n',
                            time, " ", message,
                            '\n-----------------------------------------------------------------\n']
                f.writelines(to_write)


    def get_log(self):
        # Получаем текущий день.
        day = date.today().strftime("%d.%m.%Y")
        try:
            # Получаем логи из файла.
            with open(f"app/logs/{day}.txt") as f:
                logs = f.read()
                return logs
        except:
            # Если файл не открылся - сообщение о пустых логах.
            return "Нет логов за сегодня."

