import inspect
from typing import Callable, Iterable, Union


NUMERIC = Union[int, float]
NUMERIC_TYPECHECK = (int, float)


def error_trace(*args, stack_index: int = 1):
    """Returns a quick trace to the calling namespace for a function/method,
    in case of an error.  Object instances supplied to *args have their
    class names prepended to the message, separated by '.' characters.
    """
    objects = [o.__class__.__name__ for o in args]
    calling_func = inspect.stack()[stack_index].function
    if len(objects) > 0:
        return f"{'.'.join(objects)}.{calling_func}"
    return f"{calling_func}"


class CallableList(list):

    def append(self, func: Callable) -> None:
        if not isinstance(func, Callable):
            err_msg = (f"[{error_trace(self)}] Could not append to "
                       f"CallableList: `func` must be callable (received: "
                       f"{repr(func)})")
            raise TypeError(err_msg)
        super().append(func)

    def extend(self, func_iterable: Iterable[Callable]) -> None:
        for index, func in enumerate(func_iterable):
            if not isinstance(func, Callable):
                err_msg = (f"[{error_trace(self)}] Could not extend "
                           f"CallableList: `func_iterable` contains "
                           f"non-callable element (observed: {repr(func)} at "
                           f"index: {index})")
                raise TypeError(err_msg)
        super().extend(func_iterable)

    def insert(self, index: int, func: Callable) -> None:
        if not isinstance(func, Callable):
            err_msg = (f"[{error_trace(self)}] Could not insert into "
                       f"CallableList: `func` must be callable (received: "
                       f"{repr(func)})")
            raise TypeError(err_msg)
        super().insert(index, func)
