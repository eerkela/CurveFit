"""This module allows users to attach callback functions to property state
changes.  One can do so either through an @dataclass-like interface, or by
using the @callback_property decorator, which mimics the base python @property
interface.

The content of this module is adapted from the fantastic 'echo' package
developed by Chris Beaumont and Thomas Robitaille.  Source code for that
package can be found here: https://github.com/glue-viz/echo
"""
from __future__ import annotations
from contextlib import contextmanager
from functools import partial
from typing import Callable, Iterable, Union
import weakref
from weakref import WeakKeyDictionary


class CallbackContainer(object):
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
                yield partial(func, inst)
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


class CallbackProperty(object):
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
        self._callbacks = WeakKeyDictionary()
        self._disabled = WeakKeyDictionary()
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

    def setter(self, func):
        """
        Method to use as a decorator, to mimic @property.setter
        """
        self._setter = func
        return self

    def notify(self, instance):
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

    def disable(self, instance):
        """
        Disable callbacks for a specific instance
        """
        self._disabled[instance] = True

    def enable(self, instance):
        """
        Enable previously-disabled callbacks for a specific instance
        """
        self._disabled[instance] = False

    def enabled(self, instance):
        """
        Check whether callbacks for a specific instance are currently enabled
        """
        return not self._disabled.get(instance, False)

    def add_callback(self, instance, func, priority=0):
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
        self._callbacks.setdefault(instance, CallbackContainer()) \
                       .append(func, priority=priority)

    def remove_callback(self, instance, func):
        """
        Remove a previously-added callback
        Parameters
        ----------
        instance
            The instance to detach the callback from
        func : func
            The callback function to remove
        """
        for cb in self._callbacks:
            if instance not in cb:
                continue
            if func in cb[instance]:
                cb[instance].remove(func)
                return
        raise ValueError("Callback function not found: %s" % func)

    def clear_callbacks(self, instance):
        """
        Remove all callbacks on this property.
        """
        for cb in self._callbacks:
            if instance in cb:
                cb[instance].clear()
        if instance in self._disabled:
            self._disabled.pop(instance)


def add_callback(instance,
                 prop_name: Union[str, Iterable[str]],
                 callback: Callable,
                 priority: int = 0) -> None:
    """
    Attach a callback function to a property in an instance
    Parameters
    ----------
    instance
        The instance to add the callback to
    prop_name : str
        Name of callback property in `instance`
    callback : func
        The callback function to add
    priority : int, optional
        This can optionally be used to force a certain order of execution of
        callbacks (larger values indicate a higher priority).
    Examples
    --------
    ::
        class Foo:
            bar = CallbackProperty(0)
        def callback(value):
            pass
        f = Foo()
        add_callback(f, 'bar', callback)
    """
    if isinstance(prop_name, Iterable):
        for pname in prop_name:
            prop = getattr(type(instance), pname)
            if not isinstance(prop, CallbackProperty):
                raise TypeError(f"{pname} is not a CallbackProperty")
            prop.add_callback(instance, callback, priority=priority)
    else:
        prop = getattr(type(instance), prop_name)
        if not isinstance(prop, CallbackProperty):
            raise TypeError(f"{prop_name} is not a CallbackProperty")
        prop.add_callback(instance, callback, priority=priority)


def remove_callback(instance,
                    prop_name: Union[str, Iterable[str]],
                    callback: Callable) -> None:
    """
    Remove a callback function from a property in an instance
    Parameters
    ----------
    instance
        The instance to detach the callback from
    prop : str
        Name of callback property in `instance`
    callback : func
        The callback function to remove
    """
    if isinstance(prop_name, Iterable):
        for pname in prop_name:
            prop = getattr(type(instance), pname)
            if not isinstance(prop, CallbackProperty):
                raise TypeError(f"{pname} is not a CallbackProperty")
            prop.remove_callback(instance, callback)
    else:
        prop = getattr(type(instance), prop_name)
        if not isinstance(prop, CallbackProperty):
            raise TypeError(f"{prop_name} is not a CallbackProperty")
        prop.remove_callback(instance, callback)


def callback_property(getter: Callable) -> CallbackProperty:
    """
    A decorator to build a CallbackProperty.
    This is used by wrapping a getter method, similar to the use of @property::
        class Foo(object):
            @callback_property
            def x(self):
                 return self._x
            @x.setter
            def x(self, value):
                self._x = value
    In simple cases with no getter or setter logic, it's easier to create a
    :class:`~echo.CallbackProperty` directly::
        class Foo(object);
            x = CallbackProperty(initial_value)
    """

    cb = CallbackProperty(getter=getter)
    cb.__doc__ = getter.__doc__
    return cb


class delay_callback(object):
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

    def __init__(self, instance, *props):
        self.instance = instance
        self.props = props

    def __enter__(self):

        delay_props = {}

        for prop in self.props:

            p = getattr(type(self.instance), prop)
            if not isinstance(p, CallbackProperty):
                raise TypeError("%s is not a CallbackProperty" % prop)

            if (self.instance, prop) not in self.delay_count:
                self.delay_count[self.instance, prop] = 1
                self.old_values[self.instance, prop] = p._get_full_info(self.instance)
                delay_props[prop] = p._get_full_info(self.instance)
            else:
                self.delay_count[self.instance, prop] += 1

            p.disable(self.instance)

    def __exit__(self, *args):

        resume_props = {}

        notifications = []

        for prop in self.props:

            p = getattr(type(self.instance), prop)
            if not isinstance(p, CallbackProperty):  # pragma: no cover
                raise TypeError("%s is not a CallbackProperty" % prop)

            if self.delay_count[self.instance, prop] > 1:
                self.delay_count[self.instance, prop] -= 1
            else:
                self.delay_count.pop((self.instance, prop))
                old = self.old_values.pop((self.instance, prop))
                p.enable(self.instance)
                new = p._get_full_info(self.instance)
                if old != new:
                    notifications.append((p, (self.instance)))
                resume_props[prop] = new

        for p, args in notifications:
            p.notify(*args)


@contextmanager
def ignore_callback(instance, *props):
    """
    Temporarily ignore any callbacks from one or more callback properties
    This is a context manager. Within the context block, no callbacks will be
    issued. In contrast with `delay_callback`, no callbacks will be
    called on exiting the context manager
    Parameters
    ----------
    instance
        An instance object with callback properties
    *props : str
        One or more properties within instance to ignore
    Examples
    --------
    ::
        with ignore_callback(foo, 'bar', 'baz'):
                f.bar = 20
                f.baz = 30
                f.bar = 10
        print('done')  # no callbacks called
    """
    for prop in props:
        p = getattr(type(instance), prop)
        if not isinstance(p, CallbackProperty):
            raise TypeError("%s is not a CallbackProperty" % prop)
        p.disable(instance)

    yield

    for prop in props:
        p = getattr(type(instance), prop)
        assert isinstance(p, CallbackProperty)
        p.enable(instance)