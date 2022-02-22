"""This module allows users to easily attach callback functions to state
changes of custom python objects, either through a `@dataclass`-like default
interface, or by using an `@callback_property` decorator, which mimics the
built-in `@property` interface for getter/setter logic.

The bones of this module were originally created by Chris Beaumont
(https://github.com/ChrisBeaumont) and Thomas Robitaille
(https://github.com/astrofrog), for their 'echo' package
(https://github.com/glue-viz/echo).  The contents have been heavily adapted,
but the core functionality was developed by them.
"""
from __future__ import annotations
from typing import Any, Callable, Iterable, Iterator
import weakref

from curvefit import error_trace


"""
TODO: write unit tests
TODO: render documentation and do final cleanup
"""


def callback_property(getter: Callable) -> CallbackProperty:
    """
    A decorator used to build a CallbackProperty, wrapping a getter method
    just like the built-in @property.

    Parameters
    ----------
    :param getter:
        The getter method to associate with this CallbackProperty.
    :type getter: Callable

    Returns
    -------
    :returns:
        A CallbackProperty, to which state-based callback functions can then
        be attached (see :func:`~curvefit.add_callback`).
    :rtype: CallbackProperty

    Examples
    --------
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
    return CallbackProperty(getter=getter, docstring=getter.__doc__)


def callbacks(
    instance,
    prop_name: str | None = None
) -> list[Callable] | dict[str, list[Callable]]:
    """
    Return a list of callback functions attached to an instance property.  If
    `prop_name` is omitted, returns a dictionary whose keys represent the
    names of all callback properties associated with `instance`, and whose
    values are lists of the callback functions/methods that are attached to
    each key.

    Parameters
    ----------
    :param instance:
        The instance to retrieve callbacks for.
    :type instance: Any
    :prop_name:
        The name of the property whose callbacks are to be retrieved.  If
        `None`, returns the entire callback dictionary for `instance`.
    :type prop_name: str | None, defaults to None

    Returns
    -------
    :return:
        A list of callback functions/methods for `prop_name`, or if `prop_name`
        is omitted, a dictionary mapping the names of all the
        CallbackProperties in `instance` to their corresponding list of bound
        callback functions/methods.
    :rtype: list[Callable] | dict[str, list[Callable]]

    Raises
    ------
    :raises TypeError:
        If `prop_name` is given and is not a string.
    :raises ValueError:
        If `prop_name` is given and does not point to a CallbackProperty within
        `instance`.
    """
    if prop_name is None:  # return callback dictionary for entire instance
        callback_dict = {}
        for prop_name in dir(instance):
            if hasattr(type(instance), prop_name):
                prop_val = getattr(type(instance), prop_name)
                if isinstance(prop_val, CallbackProperty):
                    callback_dict[prop_name] = prop_val.callbacks(instance)
        return callback_dict

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


def add_callback(
    instance,
    props: (str | Iterable[str] | dict[str, Callable] |
            dict[str, Iterable[Callable]]),
    callback: Callable | Iterable[Callable] | None = None,
    priority: int = 0
) -> None:
    """
    Attach a callback function to a property in an instance.  Supports
    multiple assignment via dictionaries and/or iterables of property
    names/callback functions.

    If `props` is an iterable of property names and `callback` is not `None`,
    then `callback` is assigned to every property in `props`.  Conversely, if
    `props` is the name of a single property and `callback` is an iterable of
    Callables, then each function in `callback` will be attached to the
    property specified in `props`.  If both are iterable, then every function
    in `callback` will be added to every property in `props`.

    If `props` is a dictionary of property names and Callables, then each
    Callable will be attached to the property specified by its key.  The values
    of this dictionary can themselves be iterable, mirroring the above
    functionality.  In this case, `callback` should be omitted
    (`callback=None`).

    Parameters
    ----------
    :param instance:
        The instance to add the callback(s) to.
    :type instance: Any
    :param props:
        Name or iterable of names of callback properties in `instance`, or a
        dictionary of property names and callback functions to add.
    :type props: str | Iterable[str] | dict[str, Callable]
    :param callback:
        The callback function(s) to add.  If using a callback dictionary, leave
        this blank.
    :type callback: Callable | Iterable[Callable] | None, defaults to None
    :param priority:
        This can optionally be used to force a certain order of execution of
        callbacks (larger values indicate a higher priority).
    :type priority: int, defaults to 0

    Raises
    ------
    :raises TypeError:
        If `props` is not a recognized type, or it contains non-string-based
        property names, or not all callback functions are Callable.
    :raises ValueError:
        If the properties specified in `props` do not correspond to
        CallbackProperties in the base class of `instance`.
    :raises RuntimeError:
        If the function signature is not as expected, for instance when a
        callback function is omitted during single assignment, or when
        `callback` is specified when performing dict-based multiple assignment.

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
    def get_cb_prop(name):
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

    def try_add(cb_prop, func):
        try:
            if isinstance(func, Iterable):
                for cb_func in func:
                    cb_prop.add_callback(instance, cb_func, priority=priority)
            else:
                cb_prop.add_callback(instance, func, priority=priority)
        except Exception as exc:
            err_msg = (f"[{error_trace()}] could not add callback(s): "
                       f"{repr(func)}")
            raise type(exc)(err_msg) from exc

    if isinstance(props, str):  # single property, one or more callbacks
        if callback is None:
            err_msg = (f"[{error_trace()}] `callback` must not be None")
            raise RuntimeError(err_msg)
        cb_prop = get_cb_prop(props)
        try_add(cb_prop, callback)

    elif isinstance(props, dict):  # dict-based, fine control
        if callback is not None:
            err_msg = (f"[{error_trace()}] when passing a callback dictionary, "
                       f"the `callback` argument should not be used")
            raise RuntimeError(err_msg)
        for prop_name, func in props.items():
            cb_prop = get_cb_prop(prop_name)
            try_add(cb_prop, func)

    elif isinstance(props, Iterable):  # multiple properties, one/more callbacks
        if callback is None:
            err_msg = (f"[{error_trace()}] `callback` must not be None")
            raise RuntimeError(err_msg)
        for prop_name in props:
            cb_prop = get_cb_prop(prop_name)
            try_add(cb_prop, callback)

    else:  # not recognized
        err_msg = (f"[{error_trace()}] could not interpret `props` "
                   f"(received: {repr(props)})")
        raise TypeError(err_msg)


def remove_callback(
    instance,
    props: (str | Iterable[str] | dict[str, Callable] |
            dict[str, Iterable[Callable]]),
    callback: Callable | Iterable[Callable] | None = None
) -> None:
    """
    Remove a callback function from a property in an instance.  Supports
    multiple removal via dictionaries and/or iterables of property
    names/callback functions, using the same interface as
    :func:`~curvefit.callback.add_callback`.

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

    Raises
    ------
    :raises TypeError:
        If `props` is not a recognized type, or it contains non-string-based
        property names, or not all callback functions are Callable.
    :raises ValueError:
        If the properties specified in `props` do not correspond to
        CallbackProperties in the base class of `instance`.
    :raises RuntimeError:
        If the function signature is not as expected, for instance when a
        callback function is omitted during single removal, or when `callback`
        is specified when performing dict-based multiple removal.

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
        remove_callback(f, 'bar', callback)  # single removal
        remove_callback(f, 'baz', f.callback)  # method callbacks
        remove_callback(f, ['bar', 'baz'], callback)  # multiple properties
        remove_callback(f, 'bar', [callback, f.callback])  # multiple callbacks
        remove_callback(f, {'bar': callback, 'baz': f.callback})  # dict-based
    """
    def get_cb_prop(name):
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

    def try_remove(cb_prop, func):
        try:
            if isinstance(func, Iterable):
                for cb_func in func:
                    cb_prop.remove_callback(instance, cb_func)
            else:
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
        try_remove(cb_prop, callback)

    elif isinstance(props, dict):  # multiple properties, multiple callbacks
        if callback is not None:
            err_msg = (f"[{error_trace()}] when passing a callback dictionary, "
                       f"the `callback` argument should not be used")
            raise RuntimeError(err_msg)
        for prop_name, func in props.items():
            cb_prop = get_cb_prop(prop_name)
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
    Clear all callbacks associated with specified properties in `instance`.  If
    no properties are given, clears every callback associated with `instance`.

    Parameters
    ----------
    :param instance:
        The instance to clear the callbacks from.
    :type instance: Any
    :param props:
        Name or sequence of names of callback properties in `instance` to clear
        callbacks for.
    :type props: str, optional

    Raises
    ------
    :raises TypeError:
        If `props` is not a recognized type, or it contains non-string-based
        property names.
    :raises ValueError:
        If the properties specified in `props` do not correspond to
        CallbackProperties in the base class of `instance`.
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


def copy_callbacks(old_instance,
                   new_instance,
                   check_type: bool = True) -> None:
    """
    Copy all the callbacks associated with `old_instance` onto `new_instance`.

    This is useful when setting properties that involve pass-by-reference
    object definitions.  In order to maintain the state-change behavior of such
    properties, one must usually construct a new object of the same type, then
    transfer the callbacks associated with the old instance over to the new
    one.  This function facilitates that, and should generally not be used in
    any other context.

    Parameters
    ----------
    :param old_instance:
        The old object to copy the callbacks from.
    :type old_instance: Any
    :param new_instance:
        The new object to add callbacks to.
    :type new_instance: Any
    :param check_type:
        Specifies whether to check that `old_instance` and `new_instance` are
        of the same type.  This is meant to ensure that the fields of both
        objects match, but can be disabled if desired.
    :type check_type: bool, defaults to True

    Raises
    ------
    :raises TypeError:
        If `check_type=True` and `type(old_instance) != type(new_instance)`.
    """
    if check_type and not isinstance(new_instance, type(old_instance)):
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
    reference is created which results in a memory leak. Instead, we need to
    use a weak reference which results in the callback being removed if the
    instance is destroyed. This container class takes care of this
    automatically.
    """

    def __init__(self):
        self.callbacks = []

    @staticmethod
    def is_bound_method(func: Callable) -> bool:
        """Check whether `func` is a naked function or a bound method"""
        return (hasattr(func, '__func__') and
                getattr(func, '__self__', None) is not None)

    def _wrap(self,
              value: Callable,
              priority: int = 0
    ) -> (tuple(Callable, int) |
          tuple(weakref.ref[Callable], weakref.ref[Any], int)):
        """
        Given a function or a method, this will automatically wrap a method
        using weakref to avoid circular references.
        """
        if not callable(value):
            err_msg = "Only callable values can be stored in CallbackContainer"
            raise TypeError(err_msg)
        if self.is_bound_method(value):
            # We are dealing with a bound method. Method references aren't
            # persistent, so instead we store a reference to the function
            # and instance.
            return (weakref.ref(value.__func__),
                    weakref.ref(value.__self__, self._auto_remove),
                    priority)
        return (value, priority)

    def _auto_remove(self, method_instance) -> None:
        """
        A callback function that is invoked when the instance to which a method
        was bound has been garbage collected, removing it from the callback
        container.
        """
        for value in self.callbacks[:]:
            if isinstance(value, tuple) and value[1] is method_instance:
                self.callbacks.remove(value)

    def append(self, value: Callable, priority: int = 0) -> None:
        """Append a Callable with priority level `priority` to this container"""
        self.callbacks.append(self._wrap(value, priority=priority))

    def clear(self) -> None:
        """Clear the callback references associated with this container."""
        self.callbacks[:] = []

    def remove(self, value: Callable) -> None:
        """Remove a Callable from this container"""
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

    def __contains__(self, value: Callable) -> bool:
        if self.is_bound_method(value):
            for callback in self.callbacks[:]:
                if (len(callback) == 3 and
                    value.__func__ is callback[0]() and
                    value.__self__ is callback[1]()):
                    return True
            return False
        for callback in self.callbacks[:]:
            if len(callback) == 2 and value is callback[0]:
                return True
        return False

    def __iter__(self) -> Iterator[Callable]:
        """
        Iterates through container contents, yielding the associated callables
        as naked functions or bound instance methods.
        """
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

    def __len__(self) -> int:
        return len(self.callbacks)


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
    :param default:
        The initial value for the property.
    :param docstring:
        The docstring for the property.
    :type docstring: str | None
    :param getter:
        A custom getter function, to mimic the built-in @property decorator.
    :type getter: Callable | None
    :param setter:
        A custom setter function, to mimic the built-in @property.setter
        decorator.
    :type setter: Callable | None
    """

    def __init__(self,
                 default = None,
                 docstring: str = None,
                 getter: Callable = None,
                 setter: Callable = None):
        if default is not None:  # Manual CallbackProperty
            self._default = default
            self._values = weakref.WeakKeyDictionary()
            if getter is None:
                getter = self._default_getter
            if setter is None:
                setter = self._default_setter
        self._callbacks = weakref.WeakKeyDictionary()
        self._disabled = weakref.WeakKeyDictionary()
        self._getter = getter
        self._setter = setter
        if docstring is not None:
            self.__doc__ = docstring

    def _default_getter(self, instance, owner=None):
        """
        Default getter for manual CallbackProperties (not created through
        `@callback_property`).
        """
        return self._values.get(instance, self._default)

    def _default_setter(self, instance, value) -> None:
        """
        Default setter for manual CallbackProperties (not created through
        `@callback_property`).
        """
        self._values.__setitem__(instance, value)

    def __get__(self, instance, owner=None) -> Any:
        """Get the current value of the CallbackProperty."""
        if instance is None:
            return self
        return self._getter(instance)

    def __set__(self, instance, value) -> None:
        """
        Set the current value of the CallbackProperty, invoking related
        callback functions if a state change is detected.
        """
        if self._setter is None:
            raise AttributeError("CallbackProperty has no setter")
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
        if not callable(func):
            err_msg = (f"[{error_trace(self)}] `func` must be callable "
                       f"(received: {repr(func)})")
            raise TypeError(err_msg)
        self._setter = func
        return self

    def notify(self, instance) -> None:
        """
        Invoke all callback functions attached to this CallbackProperty. Each
        will be invoked as `func(instance)`, where `instance` is a reference
        to the instance whose state has changed.

        Parameters
        ----------
        :param instance:
            The object instance to consider.
        :type instance: Any
        """
        if not self.enabled(instance):
            return
        for cback in self._callbacks.get(instance, []):
            cback(instance)

    def disable(self, instance) -> None:
        """Disable callbacks for a specific instance."""
        self._disabled[instance] = True

    def enable(self, instance) -> None:
        """Enable previously-disabled callbacks for a specific instance."""
        self._disabled[instance] = False

    def enabled(self, instance) -> bool:
        """
        Check whether callbacks are currently enabled for a specific instance.
        """
        return not self._disabled.get(instance, False)

    def callbacks(self, instance) -> list[Callable]:
        """Return a list of all callback functions/methods associated with this
        CallbackProperty.

        Modifications that are made to this list (i.e. appending/removing
        values in-situ) are not propagated to the property itself.  For that,
        see :meth:`~curvefit.CallbackProperty.add_callback` and
        :meth:`~curvefit.CallbackProperty.remove_callback`
        """
        return list(self._callbacks.get(instance, []))

    def add_callback(self,
                     instance,
                     func: Callable,
                     priority: int = 0) -> None:
        """
        Add a callback function/method to this CallbackProperty within a
        specific instance.

        Parameters
        ----------
        :param instance:
            The instance to add the callback to.
        :type instance: Any
        :param func:
            The callback function/method to add.
        :type func: Callable
        :param priority:
            This can optionally be used to force a certain order of execution
            of callbacks (larger values indicate a higher priority).
        :type priority: int, optional
        """
        if not callable(func):
            err_msg = (f"[{error_trace(self)}] `func` must be callable "
                       f"(received: {repr(func)})")
            raise TypeError(err_msg)
        self._callbacks.setdefault(instance, CallbackContainer()) \
                       .append(func, priority=priority)

    def remove_callback(self,
                        instance,
                        func: Callable) -> None:
        """
        Remove a previously-added callback function/method from this
        CallbackProperty within `instance`.

        Parameters
        ----------
        :param instance:
            The instance to detach the callback from.
        :type instance: Any
        :param func:
            The callback function/method to remove
        :type func: Callable
        """
        if not callable(func):
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
        """Remove all callbacks on this CallbackProperty within `instance`."""
        container = self._callbacks.get(instance, None)
        if container is not None:
            container.clear()
        if instance in self._disabled:
            self._disabled.pop(instance)


class delay_callbacks:
    """
    A context manager which delays the firing of callback functions from one or
    more CallbackProperties until the end of the `with` block.  Each callback
    will be called once on exit.

    `delay_callbacks` blocks can be nested if needed, causing each callback to
    be invoked when it is released from the last block that references it.

    Parameters
    ----------
    :param instance:
        An instance object with CallbackProperties.
    :type instance: Any
    :param *props:
        One or more names of properties within `instance` to delay.  If
        omitted, all callbacks associated with `instance` will be delayed until
        the end of the block.
    :type *props: str, optional

    Examples
    --------
    ::
        with delay_callbacks(foo, 'bar', 'baz'):
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


class ignore_callbacks:
    """
    A context manager which suppresses the firing of callback functions from
    one or more CallbackProperties until the end of the `with` block.  No
    callbacks will be invoked within this block.

    `ignore_callback` blocks can be nested if needed, causing each callback to
    be disabled until it is released from the last block that references it.

    Parameters
    ----------
    :param instance:
        An instance object with CallbackProperties.
    :type instance: Any
    :param *props:
        One or more names of properties within `instance` to ignore.  If
        omitted, all callbacks associated with `instance` will be disabled
        until the end of the block.
    :type *props: str, optional

    Examples
    --------
    ::
        with ignore_callbacks(foo, 'bar', 'baz'):
            f.bar = 20
            f.baz = 30
            f.bar = 10
        print('done')  # no callbacks triggered
    """

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
        """Disable all CallbackProperties specified in `__init__`."""
        for prop_name in self.props:
            cb_prop = getattr(type(self.instance), prop_name)
            cb_prop.disable(self.instance)
            if (self.instance, prop_name) not in self.ignore_count:
                self.ignore_count[self.instance, prop_name] = 1
            else:
                self.ignore_count[self.instance, prop_name] += 1
            cb_prop.disable(self.instance)

    def __exit__(self, *_) -> None:
        """
        Re-enable CallbackProperties if no other ignore_callbacks block
        mentions them.
        """
        for prop_name in self.props:
            cb_prop = getattr(type(self.instance), prop_name)
            if self.ignore_count[self.instance, prop_name] > 1:
                self.ignore_count[self.instance, prop_name] -= 1
            else:
                self.ignore_count.pop((self.instance, prop_name))
                cb_prop.enable(self.instance)
