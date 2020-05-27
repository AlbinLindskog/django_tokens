class ClassPropertyDescriptor(object):

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, cls=None):
        return self.fget.__get__(obj, cls)()


def classproperty(func):
    if not isinstance(func, classmethod):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)