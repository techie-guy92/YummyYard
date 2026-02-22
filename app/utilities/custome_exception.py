#======================================== Eceptions ===========================================

class CustomEmailException(Exception): pass


class CustomRedisException(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return f"{self.args[0]} (code: {self.code})"
    
    
#==============================================================================================