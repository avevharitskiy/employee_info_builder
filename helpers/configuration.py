from configparser import ConfigParser


class Configuration():
    """
    Configuration class
    """
    @classmethod
    def load_configuration(cls):
        config = ConfigParser()
        config.read('application.ini')

        if not config.sections():
            raise FileNotFoundError(
                'Не удалось прочитать конфигурацию из файла application.ini! Проверьте его наличие в корне проекта!'
            )

        cls.app_config = config

