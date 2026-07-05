class BusinessResult:

    def __init__(self):
        self.__success = False
        self.__message = ""
        self.__data = None

    # SETTERS

    def set_success(self, success):
        self.__success = success

    def set_message(self, message):
        self.__message = message

    def set_data(self, data):
        self.__data = data

    # GETTERS

    def get_success(self):
        return self.__success

    def get_message(self):
        return self.__message

    def get_data(self):
        return self.__data
