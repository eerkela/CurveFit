import unittest

from curvefit.callback import *


class TestClass:
    foo = CallbackProperty("abc", "naked callback property")
    _bar = "xyz"
    _baz = None
    triggered = False

    @callback_property
    def bar(self):
        """getter for bar"""
        return self._bar

    @callback_property
    def baz(self):
        """getter for baz"""
        return self._baz

    @baz.setter
    def baz(self, new_value):
        self._baz = new_value

    def callback_method(self, instance):
        self.triggered = True


class BasicCallbackPropertyTests(unittest.TestCase):

    def test_callback_property_docstring(self):
        test = TestClass()
        get_prop = lambda prop_name: getattr(type(test), prop_name)
        self.assertEqual(get_prop("foo").__doc__, "naked callback property")
        self.assertEqual(get_prop("bar").__doc__, "getter for bar")
        self.assertEqual(get_prop("baz").__doc__, "getter for baz")

    def test_list_callbacks_for_specific_property(self):
        def callback1(instance):
            pass

        def callback2(instance):
            pass
        
        test = TestClass()
        self.assertEqual(callbacks(test, "foo"), [])
        add_callback(test, "foo", callback1)
        self.assertEqual(callbacks(test, "foo"), [callback1])
        add_callback(test, "foo", callback2)
        self.assertEqual(callbacks(test, "foo"), [callback1, callback2])
        callbacks(test, "foo").remove(callback1)  # not propagated
        self.assertEqual(callbacks(test, "foo"), [callback1, callback2])

    def test_list_callbacks_for_entire_instance(self):
        def callback1(instance):
            pass

        def callback2(instance):
            pass

        test = TestClass()
        expected = {"foo": [], "bar": [], "baz": []}
        self.assertEqual(callbacks(test), expected)
        add_callback(test, "foo", callback1)
        expected = {"foo": [callback1], "bar": [], "baz": []}
        self.assertEqual(callbacks(test), expected)
        add_callback(test, ("foo", "bar"), callback2)
        expected = {"foo": [callback1, callback2], "bar": [callback2], "baz": []}
        self.assertEqual(callbacks(test), expected)

    def test_copy_callbacks(self):
        def callback(instance):
            instance.triggered = True

        old_instance = TestClass()
        add_callback(old_instance, "foo", callback)
        new_instance = TestClass()
        self.assertEqual(callbacks(new_instance, "foo"), [])
        copy_callbacks(old_instance, new_instance)
        self.assertEqual(callbacks(new_instance, "foo"), [callback])
        new_instance.foo = "def"
        self.assertTrue(new_instance.triggered)


class AddCallbackTests(unittest.TestCase):

    def test_add_callback_function(self):
        def callback_function(instance):
            instance.triggered = True

        # foo - default value
        test = TestClass()
        self.assertFalse(test.triggered)
        add_callback(test, "foo", callback_function)
        self.assertEqual(callbacks(test, "foo"), [callback_function])
        test.foo = "abc"  # no state change
        self.assertFalse(test.triggered)  # no callback
        test.foo = "def"
        self.assertTrue(test.triggered)

        # bar - has no setter method
        test.triggered = False
        self.assertFalse(test.triggered)
        add_callback(test, "bar", callback_function)
        self.assertEqual(callbacks(test, "bar"), [callback_function])
        with self.assertRaises(AttributeError) as cm:
            test.bar = "xyz"  # no state change
            self.assertFalse(test.triggered)  # no callback
            test.bar = "uvw"
            self.assertTrue(test.triggered)
        err_msg = "CallbackProperty has no setter"
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # baz - has setter
        test.triggered = False
        self.assertFalse(test.triggered)
        add_callback(test, "baz", callback_function)
        self.assertEqual(callbacks(test, "baz"), [callback_function])
        test.baz = None  # no state change
        self.assertFalse(test.triggered)  # no callback
        test.baz = True
        self.assertTrue(test.triggered)

    def test_add_callback_method(self):
        # foo - default value
        test = TestClass()
        self.assertFalse(test.triggered)
        add_callback(test, "foo", test.callback_method)
        self.assertEqual(callbacks(test, "foo"), [test.callback_method])
        test.foo = "abc"  # no state change
        self.assertFalse(test.triggered)  # no callback
        test.foo = "def"
        self.assertTrue(test.triggered)

        # bar - has no setter method
        test.triggered = False
        self.assertFalse(test.triggered)
        add_callback(test, "bar", test.callback_method)
        self.assertEqual(callbacks(test, "bar"), [test.callback_method])
        with self.assertRaises(AttributeError) as cm:
            test.bar = "xyz"  # no state change
            self.assertFalse(test.triggered)  # no callback
            test.bar = "uvw"
            self.assertTrue(test.triggered)
        err_msg = "CallbackProperty has no setter"
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # baz - has setter
        test.triggered = False
        self.assertFalse(test.triggered)
        add_callback(test, "baz", test.callback_method)
        self.assertEqual(callbacks(test, "baz"), [test.callback_method])
        test.baz = None  # no state change
        self.assertFalse(test.triggered)  # no callback
        test.baz = True
        self.assertTrue(test.triggered)

    def test_add_callback_multiple_properties(self):
        test = TestClass()
        add_callback(test, ("foo", "bar", "baz"), test.callback_method)
        expected = {"foo": [test.callback_method],
                    "bar": [test.callback_method],
                    "baz": [test.callback_method]}
        self.assertEqual(callbacks(test), expected)
        self.assertFalse(test.triggered)
        test.foo = "def"
        self.assertTrue(test.triggered)
        test.triggered = False
        with self.assertRaises(AttributeError):  # bar has no setter
            test.bar = "uvw"
            self.assertTrue(test.triggered)
        test.triggered = False
        test.baz = True
        self.assertTrue(test.triggered)

    def test_add_callback_multiple_functions(self):
        def callback1(instance):
            instance.triggered = True

        def callback2(instance):
            instance._bar = "trigger 2"
        
        test = TestClass()
        add_callback(test, "foo", (callback1, callback2))
        self.assertEqual(callbacks(test, "foo"), [callback1, callback2])
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")
        test.foo = "def"
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "trigger 2")

    def test_add_callback_multiple_properties_and_functions(self):
        def callback1(instance):
            instance.triggered = True

        def callback2(instance):
            instance._bar = "trigger 2"
        
        test = TestClass()
        add_callback(test, ("foo", "baz"), (callback1, callback2))
        self.assertEqual(callbacks(test, "foo"), [callback1, callback2])
        self.assertEqual(callbacks(test, "baz"), [callback1, callback2])
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")
        test.foo = "def"
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "trigger 2")
        test.triggered = False
        test._bar = "xyz"
        test.baz = True
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "trigger 2")

    def test_add_callback_dict(self):
        def callback1(instance):
            instance.triggered = True

        def callback2(instance):
            instance._bar = "trigger 2"

        test = TestClass()
        add_callback(test, {"foo": [callback1, callback2], "baz": callback1})
        self.assertEqual(callbacks(test, "foo"), [callback1, callback2])
        self.assertEqual(callbacks(test, "baz"), [callback1])
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")
        test.foo = "def"
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "trigger 2")
        test.triggered = False
        test._bar = "xyz"
        test.baz = True
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "xyz")


class RemoveCallbackTests(unittest.TestCase):

    def test_remove_callback_function(self):
        def callback_function(instance):
            instance.triggered = True

        test = TestClass()
        add_callback(test, "foo", callback_function)
        self.assertEqual(callbacks(test, "foo"), [callback_function])
        self.assertFalse(test.triggered)
        test.foo = "def"
        self.assertTrue(test.triggered)
        test.triggered = False
        remove_callback(test, "foo", callback_function)
        self.assertEqual(callbacks(test, "foo"), [])
        test.foo = "def"
        self.assertFalse(test.triggered)

    def test_remove_callback_method(self):
        test = TestClass()
        add_callback(test, "foo", test.callback_method)
        self.assertEqual(callbacks(test, "foo"), [test.callback_method])
        self.assertFalse(test.triggered)
        test.foo = "def"
        self.assertTrue(test.triggered)
        test.triggered = False
        remove_callback(test, "foo", test.callback_method)
        self.assertEqual(callbacks(test, "foo"), [])
        test.foo = "def"
        self.assertFalse(test.triggered)

    def test_remove_callback_multiple_properties(self):
        test = TestClass()
        add_callback(test, ("foo", "bar", "baz"), test.callback_method)
        expected = {"foo": [test.callback_method],
                    "bar": [test.callback_method],
                    "baz": [test.callback_method]}
        self.assertEqual(callbacks(test), expected)
        self.assertFalse(test.triggered)

        # confirm callbacks work
        test.foo = "def"
        self.assertTrue(test.triggered)
        test.triggered = False
        with self.assertRaises(AttributeError):  # bar has no setter
            test.bar = "uvw"
            self.assertTrue(test.triggered)
        test.triggered = False
        test.baz = True
        self.assertTrue(test.triggered)

        # remove and confirm
        test.triggered = False
        remove_callback(test, ("foo", "bar", "baz"), test.callback_method)
        self.assertEqual(callbacks(test), {"foo": [], "bar": [], "baz": []})
        test.foo = "ghi"
        self.assertFalse(test.triggered)
        with self.assertRaises(AttributeError):  # bar has no setter
            test.bar = "rst"
            self.assertFalse(test.triggered)
        test.baz = None
        self.assertFalse(test.triggered)

    def test_add_callback_multiple_functions(self):
        def callback1(instance):
            instance.triggered = True

        def callback2(instance):
            instance._bar = "trigger 2"

        # confirm callbacks work
        test = TestClass()
        add_callback(test, "foo", (callback1, callback2))
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")
        test.foo = "def"
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "trigger 2")

        # remove and confirm
        test.triggered = False
        test._bar = "xyz"
        remove_callback(test, "foo", (callback1, callback2))
        test.foo = "ghi"
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")

    def test_add_callback_multiple_properties_and_functions(self):
        def callback1(instance):
            instance.triggered = True

        def callback2(instance):
            instance._bar = "trigger 2"

        # confirm callbacks work
        test = TestClass()
        add_callback(test, ("foo", "baz"), (callback1, callback2))
        self.assertEqual(callbacks(test, "foo"), [callback1, callback2])
        self.assertEqual(callbacks(test, "baz"), [callback1, callback2])
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")
        test.foo = "def"
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "trigger 2")
        test.triggered = False
        test._bar = "xyz"
        test.baz = True
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "trigger 2")

        # remove and confirm
        test.triggered = False
        test._bar = "xyz"
        remove_callback(test, ("foo", "baz"), (callback1, callback2))
        self.assertEqual(callbacks(test, "foo"), [])
        self.assertEqual(callbacks(test, "baz"), [])
        test.foo = "ghi"
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")
        test.baz = None
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")

    def test_add_callback_dict(self):
        def callback1(instance):
            instance.triggered = True

        def callback2(instance):
            instance._bar = "trigger 2"

        # confirm callbacks work
        test = TestClass()
        add_callback(test, {"foo": [callback1, callback2], "baz": callback1})
        self.assertEqual(callbacks(test, "foo"), [callback1, callback2])
        self.assertEqual(callbacks(test, "baz"), [callback1])
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")
        test.foo = "def"
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "trigger 2")
        test.triggered = False
        test._bar = "xyz"
        test.baz = True
        self.assertTrue(test.triggered)
        self.assertEqual(test.bar, "xyz")

        # remove and confirm
        test.triggered = False
        remove_callback(test, {"foo": [callback1, callback2], "baz": callback1})
        self.assertEqual(callbacks(test, "foo"), [])
        self.assertEqual(callbacks(test, "baz"), [])
        test.foo = "ghi"
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")
        test.baz = None
        self.assertFalse(test.triggered)
        self.assertEqual(test.bar, "xyz")


class ClearCallbackTests(unittest.TestCase):

    def test_clear_callbacks_single_property(self):
        def callback(instance):
            instance.triggered = True

        test = TestClass()
        add_callback(test, "foo", callback)
        self.assertEqual(callbacks(test, "foo"), [callback])
        clear_callbacks(test, "foo")
        self.assertEqual(callbacks(test, "foo"), [])

    def test_clear_callbacks_multiple_properties(self):
        def callback(instance):
            instance.triggered = True

        test = TestClass()
        add_callback(test, ("foo", "baz"), callback)
        self.assertEqual(callbacks(test, "foo"), [callback])
        self.assertEqual(callbacks(test, "baz"), [callback])
        clear_callbacks(test, "foo", "baz")
        self.assertEqual(callbacks(test, "foo"), [])
        self.assertEqual(callbacks(test, "baz"), [])

    def test_clear_callbacks_entire_instance(self):
        def callback(instance):
            instance.triggered = True

        test = TestClass()
        add_callback(test, ("foo", "bar", "baz"), callback)
        self.assertEqual(callbacks(test, "foo"), [callback])
        self.assertEqual(callbacks(test, "bar"), [callback])
        self.assertEqual(callbacks(test, "baz"), [callback])
        clear_callbacks(test)
        self.assertEqual(callbacks(test, "foo"), [])
        self.assertEqual(callbacks(test, "bar"), [])
        self.assertEqual(callbacks(test, "baz"), [])


class ContextManagerTestCases(unittest.TestCase):

    def test_delay_callbacks(self):
        def callback(instance):
            instance._bar += 1

        test = TestClass()
        test._bar = 0
        add_callback(test, "foo", callback)
        test.foo = "def"
        test.foo = "ghi"
        self.assertEqual(test.bar, 2)
        with delay_callbacks(test, "foo"):
            test.foo = "mno"
            test.foo = "pqr"
            test.foo = "stu"
        self.assertEqual(test.bar, 3)

    def test_delay_callbacks_whole_instance(self):
        def callback(instance):
            instance._bar += 1

        test = TestClass()
        test._bar = 0
        add_callback(test, ("foo", "baz"), callback)
        test.foo = "def"
        test.baz = "abc"
        self.assertEqual(test.bar, 2)
        with delay_callbacks(test):
            test.foo = "ghi"
            test.foo = "jkl"
            test.baz = "def"
            test.baz = "ghi"
        self.assertEqual(test.bar, 4)

    def test_delay_callbacks_nested(self):
        def callback(instance):
            instance._bar += 1

        test = TestClass()
        test._bar = 0
        add_callback(test, ("foo", "baz"), callback)
        test.foo = "def"
        test.foo = "ghi"
        self.assertEqual(test.bar, 2)
        with delay_callbacks(test, "foo"):
            with delay_callbacks(test, "foo", "baz"):
                test.foo = "mno"
                test.foo = "pqr"
                test.baz = "abc"
                test.baz = "def"
            # baz is released, fire one callback
            self.assertEqual(test.bar, 3)
            test.foo = "stu"
            test.foo = "vwx"
            test.baz = "ghi"  # no longer delayed, should trigger
            self.assertEqual(test.bar, 4)
        # foo is released, fire one callback
        self.assertEqual(test.bar, 5)

    def test_ignore_callbacks(self):
        def callback(instance):
            instance._bar += 1

        test = TestClass()
        test._bar = 0
        add_callback(test, "foo", callback)
        test.foo = "def"
        test.foo = "ghi"
        self.assertEqual(test.bar, 2)
        with ignore_callbacks(test, "foo"):
            test.foo = "mno"
            test.foo = "pqr"
            test.foo = "stu"
        self.assertEqual(test.bar, 2)

    def test_ignore_callbacks_whole_instance(self):
        def callback(instance):
            instance._bar += 1

        test = TestClass()
        test._bar = 0
        add_callback(test, ("foo", "baz"), callback)
        test.foo = "def"
        test.baz = "abc"
        self.assertEqual(test.bar, 2)
        with ignore_callbacks(test):
            test.foo = "ghi"
            test.foo = "jkl"
            test.baz = "def"
            test.baz = "ghi"
        self.assertEqual(test.bar, 2)

    def test_ignore_callbacks_nested(self):
        def callback(instance):
            instance._bar += 1

        test = TestClass()
        test._bar = 0
        add_callback(test, ("foo", "baz"), callback)
        test.foo = "def"
        test.foo = "ghi"
        self.assertEqual(test.bar, 2)
        with ignore_callbacks(test, "foo"):
            with ignore_callbacks(test, "foo", "baz"):
                test.foo = "mno"
                test.foo = "pqr"
                test.baz = "abc"
                test.baz = "def"
            test.foo = "stu"
            test.foo = "vwx"
            test.baz = "ghi"  # no longer ignored, should trigger
            self.assertEqual(test.bar, 3)
        self.assertEqual(test.bar, 3)
