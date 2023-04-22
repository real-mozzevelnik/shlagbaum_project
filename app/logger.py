from datetime import date


# Класс для логирования действий.
class Logger:

    def log(self, message):
        # Получаем текущую дату.
        day = date.today().strftime("%d.%m.%Y")
        
        # Открываем файл с соответсвующим названием и записываем информацию.
        try:
            with open(f"app/logs/{day}.txt", "a") as f:
                to_write = ['\n-----------------------------------------------------------------\n',
                            message,
                            '\n-----------------------------------------------------------------\n']
                f.writelines(to_write)
        except:
            with open(f"app/logs/{day}.txt", "w") as f:
                to_write = ['\n-----------------------------------------------------------------\n',
                            message,
                            '\n-----------------------------------------------------------------\n']
                f.writelines(to_write)

