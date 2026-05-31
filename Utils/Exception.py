# Handles user defined Exceptions

import logging

logger = logging.getLogger(__name__)

class BaseException(Exception):
    def __init___(self,message):
        logger.error(message)
        super().__init__(message)

class UnsupportedLanguage(BaseException):
    def __init__(self,message):
        super().__init__(message)

class UnsupportedLanguage(Exception):
    def __init__(self,message):
        super().__init__(message)