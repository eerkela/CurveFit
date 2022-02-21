"""This module allows users to attach callback functions to property state
changes.  One can do so either through an @dataclass-like interface, or by
using the @callback_property decorator, which mimics the base python @property
interface.

The content of this module is adapted from the fantastic 'echo' package
developed by Chris Beaumont and Thomas Robitaille.  Source code for that
package can be found here: https://github.com/glue-viz/echo
"""
from __future__ import annotations
from typing import Callable, Iterable
import weakref

from curvefit import error_trace


def callback_property(getter: Callable) -> CallbackProperty:
    """
    A decorator used to build a CallbackProperty, wrapping a getter method
    just like @property.

    ::
        class Foo(object):

            @callback_property
            def x(self):
                 return self._x

            @x.setter
            def x(self, value):
                self._x = value

    In simple cases with no getter or setter logic, it's easier to create a
    :class:`~curvefit.CallbackProperty` directly
    
    ::
        class Foo(object);
            x = CallbackProperty(initial_value)
    """

    cb = CallbackProperty(getter=getter)
    cb.__doc__ = getter.__doc__
    return cb


def callbacks(
    instance,
    prop_name: str | None = None) -> list[Callable] | dict[str, Callable]:
    """
    Return a list of callback functions attached to an instance property.  If
    `prop_name` is omitted, returns a dictionary whose keys represent the
    names of all callback properties associated with `instance`, and whose
    values are lists of the callback functions/methods that are attached to
    each key.

    Parameters
    ----------
    :param instance:
        The instance to retrieve callbacks for
    :type instance: Any
    :prop_name:
        The name of the property whose callbacks are to be retrieved.  If
        `None`, returns the entire callback dictionary for `instance`.
    :type prop_name: str | None, defaults to None
    """
    if prop_name is None:  # return callback dictionary for entire instance
        callbacks = {}
        for prop_name in dir(instance):
            if hasattr(type(instance), prop_name):
                prop_val = getattr(type(instance), prop_name)
                if isinstance(prop_val, CallbackProperty):
                    callbacks[prop_name] = prop_val.callbacks(instance)
        return callbacks

    # return callbacks for specific property
    if not isinstance(prop_name, str):
        err_msg = (f"[{error_trace()}] `prop_name` must be a string "
                   f"(received: {repr(prop_name)})")
        raise TypeError(err_msg)
    prop = getattr(type(instance), prop_name)
    if not isinstance(prop, CallbackProperty):
        err_msg = (f"[{error_trace()}] {type(instance)}.{prop_name} is not "
                   f"a CallbackProperty")
        raise ValueError(err_msg)
    return prop.callbacks(instance)


def add_callback(instance,
                 props: str | Iterable[str] | dict[str, Callable],
                 callback: Callable | Iterable[Callable] | None = None,
                 priority: int = 0) -> None:
    """
    Attach a callback function to a property in an instance.

    Supports multiple assignment via dictionaries and/or iterables of property
    names/callback functions.  If using a dictionary to perform multiple
    assignment, the `callback` field should be omitted, and the values of
    `props` should reference the callback function(s) to use for each property.

    Parameters
    ----------
    :param instance:
        The instance to add the callback(s) to
    :type instance: Any
    :param props:
        Name or iterable of names of callback properties in `instance`, or a
        dictionary of property names and callback functions to add
    :type props: str | Iterable[str] | dict[str, Callable]
    :param callback:
        The callback function(s) to add.  If using a callback dictionary, leave
        this blank
    :type callback: Callable | Iterable[Callable] | None, defaults to None
    :param priority:
        This can optionally be used to force a certain order of execution of
        callbacks (larger values indicate a higher priority).
    :type priority: int, defaults to 0

    Examples
    --------
    ::
        class Foo:
            bar = CallbackProperty(0)

            @callback_property
            def baz(self):
                return self._baz

            @baz.setter
            def baz(self, new_baz):
                self._baz = new_baz

            def callback(self, instance):
                pass

        def callback(instance):
            pass

        f = Foo()
        add_callback(f, 'bar', callback)  # single assignment
        add_callback(f, 'baz', f.callback)  # method callbacks
        add_callback(f, ['bar', 'baz'], callback)  # multiple properties
        add_callback(f, 'bar', [callback, f.callback])  # multiple callbacks
        add_callback(f, {'bar': callback, 'baz': f.callback})  # dict-based
    """
    def get_cb_prop(name: str) -> CallbackProperty:
        if not isinstance(name, str):
            err_msg = (f"[{error_trace(stack_index=2)}] property names must "
                       f"be strings (received: {repr(name)})")
            raise TypeError(err_msg)
        cb_prop = getattr(type(instance), name)
        if not isinstance(cb_prop, CallbackProperty):
            err_msg = (f"[{error_trace(stack_index=2)}] "
                       f"{type(instance)}.{name} is not a CallbackProperty")
            raise ValueError(err_msg)
        return cb_prop
    
    def try_add(cb_prop: CallbackProperty, func: Callable) -> None:
        try:
            cb_prop.add_callback(instance, func, priority=priority)
        except Exception as exc:
            err_msg = (f"[{error_trace()}] could not add callback: "
                       f"{repr(func)}")
            raise type(exc)(err_msg) from exc

    if isinstance(props, str):  # single property, one or more callbacks
        if callback is None:
            err_msg = (f"[{error_trace()}] `callback` must not be None")
            raise RuntimeError(err_msg)
        cb_prop = get_cb_prop(props)
        if isinstance(callback, Iterable):
            for cb_func in callback:
                try_add(cb_prop, cb_func)
        else:
            try_add(cb_prop, callback)

    elif isinstance(props, dict):  # multiple properties, multiple callbacks
        if callback is not None:
            err_msg = (f"[{error_trace()}] when passing a callback dictionary, "
                       f"the `callback` argument should not be used")
            raise RuntimeError(err_msg)
        for prop_name, func in props.items():
            cb_prop = get_cb_prop(prop_name)
            if isinstance(func, Iterable):
                for cb_func in func:
                    try_add(cb_prop, cb_func)
            else:
                try_add(cb_prop, func)

    elif isinstance(props, Iterable):  # multiple properties, single callback
        for prop_name in props:
            cb_prop = get_cb_prop(prop_name)
            try_add(cb_prop, callback)

    else:  # not recognized
        err_msg = (f"[{error_trace()}] could not interpret `props` "
                   f"(received: {repr(props)})")
        raise TypeError(err_msg)


def remove_callback(instance,
                    props: str | Iterable[str] | dict[str, Callable],
                    callback: Callable | Iterable[Callable] | None) -> None:
    """
    Remove a callback function from a property in an instance.

    Supports multiple removal via dictionaries and/or iterables of property
    names/callback functions.  If using a dictionary to perform multiple
    removal, the `callback` field should be omitted, and the values of `props`
    should reference the callback function(s) to remove for each property.

    Parameters
    ----------
    :param instance:
        The instance to remove the callback(s) to
    :type instance: Any
    :param props:
        Name or iterable of names of callback properties in `instance`, or a
        dictionary of property names and callback functions to remove
    :type props: str | Iterable[str] | dict[str, Callable]
    :param callback:
        The callback function(s) to remove.  If using a callback dictionary,
        leave this blank
    :type callback: Callable | Iterable[Callable] | None, defaults to None
    """
    def get_cb_prop(name: str) -> CallbackProperty:
        if not isinstance(name, str):
            err_msg = (f"[{error_trace(stack_index=2)}] property names must "
                       f"be strings (received: {repr(name)})")
            raise TypeError(err_msg)
        cb_prop = getattr(type(instance), name)
        if not isinstance(cb_prop, CallbackProperty):
            err_msg = (f"[{error_trace(stack_index=2)}] "
                       f"{type(instance)}.{name} is not a CallbackProperty")
            raise ValueError(err_msg)
        return cb_prop
    
    def try_remove(cb_prop: CallbackProperty, func: Callable) -> None:
        try:
            cb_prop.remove_callback(instance, func)
        except Exception as exc:
            err_msg = (f"[{error_trace()}] could not remove callback: "
                       f"{repr(func)}")
            raise type(exc)(err_msg) from exc
    
    if isinstance(props, str):  # single property, one or more callbacks
        if callback is None:
            err_msg = (f"[{error_trace()}] `callback` must not be None")
            raise RuntimeError(err_msg)
        cb_prop = get_cb_prop(props)
        if isinstance(callback, Iterable):
            for cb_func in callback:
                try_remove(cb_prop, cb_func)
        else:
            try_remove(cb_prop, callback)

    elif isinstance(props, dict):  # multiple properties, multiple callbacks
        if callback is not None:
            err_msg = (f"[{error_trace()}] when passing a callback dictionary, "
                       f"the `callback` argument should not be used")
            raise RuntimeError(err_msg)
        for prop_name, func in props.items():
            cb_prop = get_cb_prop(prop_name)
            if isinstance(func, Iterable):
                for cb_func in func:
                    try_remove(cb_prop, cb_func)
            else:
                try_remove(cb_prop, func)

    elif isinstance(props, Iterable):  # multiple properties, single callback
        if callback is None:
            err_msg = (f"[{error_trace()}] `callback` must not be None")
            raise RuntimeError(err_msg)
        for prop_name in props:
            cb_prop = get_cb_prop(prop_name)
            try_remove(cb_prop, callback)

    else:  # not recognized
        err_msg = (f"[{error_trace()}] could not interpret `props` "
                   f"(received: {repr(props)})")
        raise TypeError(err_msg)


def clear_callbacks(instance, *props: str) -> None:
    """
    Clear all callbacks associated with specified properties of `instance`.

    Parameters
    ----------
    :param instance:
        The instance to clear the callbacks from
    :type instance: Any
    :param props:
        Name or sequence of names of callback properties in `instance` to clear
        callbacks for
    :type props: str, optional
    """
    if len(props) > 0:
        for prop_name in props:
            try:
                cb_funcs = callbacks(instance, prop_name)
                remove_callback(instance, prop_name, cb_funcs)
            except Exception as exc:
                err_msg = (f"[{error_trace()}] could not clear callbacks for "
                           f"property: {prop_name}")
                raise type(exc)(err_msg) from exc
    else:
        try:
            remove_callback(instance, callbacks(instance))
        except Exception as exc:
            err_msg = f"[{error_trace()}] could not clear instance callbacks"
            raise type(exc)(err_msg) from exc


def copy_callbacks(old_instance, new_instance, check_type: bool = True) -> None:
    """Attach all callbacks associated with `old_instance` to `new_instance`"""
    if check_type and not type(old_instance) == type(new_instance):
        err_msg = (f"[{error_trace()}] type of `old_instance` does not match "
                   f"that of `new_instance`({type(old_instance)} != "
                   f"{type(new_instance)}); if this is intended behavior, use "
                   f"`check_type=False`")
        raise TypeError(err_msg)
    add_callback(new_instance, callbacks(old_instance))


class CallbackContainer:
    """
    A list-like container for callback functions. We need to be careful with
    storing references to methods, because if a callback method is on a class
    which contains both the callback and a callback property, a circular
    reference is created which results in a memory leak. Instead, we need to use
    a weak reference which results in the callback being removed if the instance
    is destroyed. This container class takes care of this automatically.
    """

    def __init__(self):
        self.callbacks = []

    def clear(self):
        self.callbacks[:] = []

    def _wrap(self, value, priority=0):
        """
        Given a function/method, this will automatically wrap a method using
        weakref to avoid circular references.
        """
        if not callable(value):
            err_msg = "Only callable values can be stored in CallbackContainer"
            raise TypeError(err_msg)
        elif self.is_bound_method(value):
            # We are dealing with a bound method. Method references aren't
            # persistent, so instead we store a reference to the function
            # and instance.
            value = (weakref.ref(value.__func__),
                     weakref.ref(value.__self__, self._auto_remove),
                     priority)
        else:
            value = (value, priority)
        return value

    def _auto_remove(self, method_instance):
        # Called when weakref detects that the instance on which a method was
        # defined has been garbage collected.
        for value in self.callbacks[:]:
            if isinstance(value, tuple) and value[1] is method_instance:
                self.callbacks.remove(value)

    def __contains__(self, value):
        if self.is_bound_method(value):
            for callback in self.callbacks[:]:
                if (len(callback) == 3 and
                    value.__func__ is callback[0]() and
                    value.__self__ is callback[1]()):
                    return True
            return False
        else:
            for callback in self.callbacks[:]:
                if len(callback) == 2 and value is callback[0]:
                    return True
            return False

    def __iter__(self):
        for callback in sorted(self.callbacks, key=lambda x: x[-1],
                               reverse=True):
            if len(callback) == 3:
                func = callback[0]()
                inst = callback[1]()
                # In some cases it can happen that the instance has been
                # garbage collected but _auto_remove hasn't been called, so we
                # just check here that the weakrefs were resolved
                if func is None or inst is None:
                    continue
                yield func.__get__(inst)  # bound method rather than partial
                # yield partial(func, inst)  # original source
            else:
                yield callback[0]

    def __len__(self):
        return len(self.callbacks)

    @staticmethod
    def is_bound_method(func):
        return (hasattr(func, '__func__') and
                getattr(func, '__self__', None) is not None)

    def append(self, value, priority=0):
        self.callbacks.append(self._wrap(value, priority=priority))

    def remove(self, value):
        if self.is_bound_method(value):
            for callback in self.callbacks[:]:
                if (len(callback) == 3 and
                    value.__func__ is callback[0]() and
                    value.__self__ is callback[1]()):
                    self.callbacks.remove(callback)
        else:
            for callback in self.callbacks[:]:
                if len(callback) == 2 and value is callback[0]:
                    self.callbacks.remove(callback)


class CallbackProperty:
    """
    A property that callback functions can be added to.
    When a callback property changes value, each callback function
    is called with information about the state change. Otherwise,
    callback properties behave just like normal instance variables.
    CallbackProperties must be defined at the class level. Use
    the helper function :func:`~echo.add_callback` to attach a callback to
    a specific instance of a class with CallbackProperties
    Parameters
    ----------
    default
        The initial value for the property
    docstring : str
        The docstring for the property
    getter, setter : func
        Custom getter and setter functions (advanced)
    """

    def __init__(self, default=None, docstring=None, getter=None, setter=None):
        """
        :param default: The initial value for the property
        """
        self._default = default
        self._callbacks = weakref.WeakKeyDictionary()
        self._disabled = weakref.WeakKeyDictionary()
        self._getter = getter
        self._setter = setter
        if docstring is not None:
            self.__doc__ = docstring

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return self._getter(instance)

    def __set__(self, instance, value):
        if self._setter is None:
            raise AttributeError("attribute has no setter")
        try:
            old = self.__get__(instance)
        except AttributeError:  # pragma: no cover
            old = None
        self._setter(instance, value)
        new = self.__get__(instance)
        if old != new:
            self.notify(instance)

    def setter(self, func: Callable) -> CallbackProperty:
        """Method to use as a decorator, to mimic @property.setter"""
        if not isinstance(func, Callable):
            err_msg = (f"[{error_trace(self)}] `func` must be callable "
                       f"(received: {repr(func)})")
            raise TypeError(err_msg)
        self._setter = func
        return self

    def notify(self, instance) -> None:
        """
        Call all callback functions with the current value. Each callback will
        be passed a reference to the instance whose state has changed:
        (`callback(instance)`).

        Parameters
        ----------
        instance
            The instance to consider
        old
            The old value of the property
        new
            The new value of the property
        """
        if not self.enabled(instance):
            return
        for cback in self._callbacks.get(instance, []):
            cback(instance)

    def disable(self, instance) -> None:
        """
        Disable callbacks for a specific instance
        """
        self._disabled[instance] = True

    def enable(self, instance) -> None:
        """
        Enable previously-disabled callbacks for a specific instance
        """
        self._disabled[instance] = False

    def enabled(self, instance) -> bool:
        """
        Check whether callbacks for a specific instance are currently enabled
        """
        return not self._disabled.get(instance, False)

    def callbacks(self, instance) -> list[Callable]:
        return [signature for signature in self._callbacks.get(instance, [])]

    def add_callback(self, instance, func: Callable, priority: int = 0) -> None:
        """
        Add a callback to a specific instance that manages this property
        Parameters
        ----------
        instance
            The instance to add the callback to
        func : func
            The callback function to add
        priority : int, optional
            This can optionally be used to force a certain order of execution of
            callbacks (larger values indicate a higher priority).
        """
        if not isinstance(func, Callable):
            err_msg = (f"[{error_trace(self)}] `func` must be callable "
                       f"(received: {repr(func)})")
            raise TypeError(err_msg)
        self._callbacks.setdefault(instance, CallbackContainer()) \
                       .append(func, priority=priority)

    def remove_callback(self, instance, func: Callable) -> None:
        """
        Remove a previously-added callback
        Parameters
        ----------
        instance
            The instance to detach the callback from
        func : func
            The callback function to remove
        """
        if not isinstance(func, Callable):
            err_msg = (f"[{error_trace(self)}] `func` must be a callable "
                       f"(received: {repr(func)})")
            raise TypeError(err_msg)
        container = self._callbacks.get(instance, [])
        if func in container:
            container.remove(func)
            return
        err_msg = f"[{error_trace(self)}] callback function not found: {func}"
        raise ValueError(err_msg)

    def clear_callbacks(self, instance) -> None:
        """
        Remove all callbacks on this property.
        """
        for cb in self._callbacks:
            if instance in cb:
                cb[instance].clear()
        if instance in self._disabled:
            self._disabled.pop(instance)


class delay_callback:
    """
    Delay any callback functions from one or more callback properties
    This is a context manager. Within the context block, no callbacks
    will be issued. Each callback will be called once on exit
    Parameters
    ----------
    instance
        An instance object with callback properties
    *props : str
        One or more properties within instance to delay
    Examples
    --------
    ::
        with delay_callback(foo, 'bar', 'baz'):
            f.bar = 20
            f.baz = 30
            f.bar = 10
        print('done')  # callbacks triggered at this point, if needed
    """

    # Class-level registry of properties and how many times the callbacks have
    # been delayed. The idea is that when nesting calls to delay_callback, the
    # delay count is increased, and every time __exit__ is called, the count is
    # decreased, and once the count reaches zero, the callback is triggered.
    delay_count = {}
    old_values = {}

    def __init__(self, instance, *props: str):
        self.instance = instance
        if len(props) > 0:
            for prop_name in props:
                if not isinstance(prop_name, str):
                    err_msg = (f"[{error_trace(self)}] property name must be "
                               f"a string (received: {repr(prop_name)})")
                    raise TypeError(err_msg)
                cb_prop = getattr(type(self.instance), prop_name)
                if not isinstance(cb_prop, CallbackProperty):
                    err_msg = (f"[{error_trace(self)}] {prop_name} is not a "
                               f"CallbackProperty")
                    raise TypeError(err_msg)
            self.props = props
        else:  # collect all properties related to instance
            self.props = []
            for prop_name in dir(instance):
                if hasattr(type(instance), prop_name):
                    prop_val = getattr(type(instance), prop_name)
                    if isinstance(prop_val, CallbackProperty):
                        self.props.append(prop_name)
            self.props = tuple(self.props)

    def __enter__(self) -> None:
        """Record old values and suppress callback properties"""
        for prop_name in self.props:
            cb_prop = getattr(type(self.instance), prop_name)
            if (self.instance, prop_name) not in self.delay_count:
                old_val = cb_prop.__get__(self.instance)
                self.delay_count[self.instance, prop_name] = 1
                self.old_values[self.instance, prop_name] = old_val
            else:
                self.delay_count[self.instance, prop_name] += 1
            cb_prop.disable(self.instance)

    def __exit__(self, *_) -> None:
        """Re-enable disabled properties and fire callbacks"""
        notifications = []
        for prop_name in self.props:
            cb_prop = getattr(type(self.instance), prop_name)
            if self.delay_count[self.instance, prop_name] > 1:
                self.delay_count[self.instance, prop_name] -= 1
            else:
                self.delay_count.pop((self.instance, prop_name))
                old = self.old_values.pop((self.instance, prop_name))
                cb_prop.enable(self.instance)
                new = cb_prop.__get__(self.instance)
                if old != new:
                    notifications.append((cb_prop, self.instance))
        for cb_prop, instance in notifications:
            cb_prop.notify(instance)


class ignore_callback:

    # Class-level registry of properties and how many times the callbacks have
    # been ignored. The idea is that when nesting calls to ignore_callback, the
    # ignore count is increased, and every time __exit__ is called, the count
    # is decreased, and once the count reaches zero, the property is re-enabled
    ignore_count = {}

    def __init__(self, instance, *props: str):
        self.instance = instance
        if len(props) > 0:
            for prop_name in props:
                if not isinstance(prop_name, str):
                    err_msg = (f"[{error_trace(self)}] property name must be "
                               f"a string (received: {repr(prop_name)})")
                    raise TypeError(err_msg)
                cb_prop = getattr(type(self.instance), prop_name)
                if not isinstance(cb_prop, CallbackProperty):
                    err_msg = (f"[{error_trace(self)}] {prop_name} is not a "
                               f"CallbackProperty")
                    raise TypeError(err_msg)
            self.props = tuple(set(props))  # ensure uniqueness
        else:  # collect all properties related to instance
            self.props = []
            for prop_name in dir(instance):
                if hasattr(type(instance), prop_name):
                    prop_val = getattr(type(instance), prop_name)
                    if isinstance(prop_val, CallbackProperty):
                        self.props.append(prop_name)
            self.props = tuple(set(self.props))  # ensure uniqueness

    def __enter__(self) -> None:
        for prop_name in self.props:
            cb_prop = getattr(type(self.instance), prop_name)
            cb_prop.disable(self.instance)
            if (self.instance, prop_name) not in self.ignore_count:
                self.ignore_count[self.instance, prop_name] = 1
            else:
                self.ignore_count[self.instance, prop_name] += 1
            cb_prop.disable(self.instance)

    def __exit__(self, *_) -> None:
        for prop_name in self.props:
            cb_prop = getattr(type(self.instance), prop_name)
            if self.ignore_count[self.instance, prop_name] > 1:
                self.ignore_count[self.instance, prop_name] -= 1
            else:
                self.ignore_count.pop((self.instance, prop_name))
                cb_prop.enable(self.instance)
