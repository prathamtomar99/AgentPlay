# A singleton class so that instance don't get initialised multiple times

def Singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

if __name__=="__main__":
    @Singleton
    class Temp():
        def __init__(self):
            pass

    t1 = Temp()
    t2 = Temp()
    print(t1 is t2)