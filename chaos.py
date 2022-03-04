import functools


class Boom(Exception):
    msg = """
        _.-^^---....,,--       
     _--                  --_  
    <                        >)
    |                         | 
     \._                   _./  
        ```--. . , ; .--'''       
              | |   |             
           .-=||  | |=-.   
           `-=#$%&%$#=-'   
              | ;  :|     
     _____.,-#%&$@%#&#~,._____"""

    def __init__(self, *args, **kwargs):
        super().__init__(self.msg)

    def __str__(self):
        return f'{self.msg}'


def timebomb(timer_start: int):
    def decorator_timebomb(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            wrapper.timer -= 1
            if wrapper.timer < 1:
                raise Boom()
            return value

        wrapper.timer = timer_start
        return wrapper

    return decorator_timebomb
