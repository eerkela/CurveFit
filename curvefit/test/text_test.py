from functools import partial
import unittest

import numpy as np
from matplotlib.figure import Figure
from matplotlib.text import Text

from curvefit.callback import add_callback
from curvefit.color import DynamicColor, to_rgba
from curvefit.text import DynamicText


assert_equal_float = partial(np.testing.assert_almost_equal, decimal=3)


class DynamicTextBasicTests(unittest.TestCase):

    def test_basic_init(self):
        text = DynamicText(Text(text="test"))
        self.assertEqual(text.text, "test")

        # with kwargs
        text = DynamicText(Text(text="test"), alpha=0.8, color="white")
        self.assertEqual(text.text, "test")
        assert_equal_float(text.alpha, 0.8)
        self.assertEqual(text.color.name, "white")

    def test_alignment(self):
        figure = Figure()
        figure.suptitle("test",
                        horizontalalignment = "left",
                        verticalalignment="baseline")
        text = DynamicText(figure._suptitle)
        self.assertEqual(text.alignment, ("left", "baseline"))
        text.alignment = "center"
        self.assertEqual(text.alignment, ("center", "baseline"))
        text.alignment = ("right", "center")
        self.assertEqual(text.alignment, ("right", "center"))

        # check errors
        with self.assertRaises(TypeError) as cm:
            text.alignment = 1
        err_msg = ("[DynamicText.alignment] `alignment` must be a string or "
                   "tuple of strings `(horizontal, vertical)` with one of the "
                   "following horizontal values: ")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        with self.assertRaises(ValueError) as cm:
            text.alignment = "bad alignment value"
        err_msg = ("[DynamicText.alignment] when given a string, `alignment` "
                   "must have one of the following values: ")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        with self.assertRaises(ValueError) as cm:
            text.alignment = ("bad alignment value", "baseline")
        err_msg = ("[DynamicText.alignment] when given a tuple, the first "
                   "element of `alignment` must have one of the following "
                   "values: ")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        with self.assertRaises(ValueError) as cm:
            text.alignment = ("left", "bad alignment value")
        err_msg = ("[DynamicText.alignment] when given a tuple, the second "
                   "element of `alignment` must have one of the following "
                   "values: ")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # test callbacks
        def callback(dynamic_text_instance):
            dynamic_text_instance.alignment = "right"
        
        text.alignment = ("left", "baseline")
        add_callback(text, "alignment", callback)
        text.alignment = ("left", "baseline")  # no state change
        self.assertEqual(text.alignment, ("left", "baseline"))  # no callback
        text.alignment = "left"  # still no state change
        self.assertEqual(text.alignment, ("left", "baseline"))  # no callback
        text.alignment = "center"  # state change
        self.assertEqual(text.alignment, ("right", "baseline"))  # callback

    def test_alpha(self):
        figure = Figure()
        figure.suptitle("test")
        text = DynamicText(figure._suptitle)
        assert_equal_float(text.alpha, 1.0)
        text.alpha = 0.5
        assert_equal_float(text.alpha, 0.5)

        # check errors
        with self.assertRaises(TypeError) as cm:
            text.alpha = "abc"
        err_msg = ("[DynamicColor.alpha] `alpha` must be a numeric "
                   "between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        with self.assertRaises(ValueError) as cm:
            text.alpha = 1.2
        err_msg = ("[DynamicColor.alpha] `alpha` must be a numeric "
                   "between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        with self.assertRaises(ValueError) as cm:
            text.alpha = -0.5
        err_msg = ("[DynamicColor.alpha] `alpha` must be a numeric "
                   "between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # test callbacks
        def callback(dynamic_text_instance):
            dynamic_text_instance.alpha = 0
        
        text.alpha = 1
        add_callback(text, "alpha", callback)
        text.alpha = 1.0  # no state change
        self.assertEqual(text.alpha, 1.0)  # no callback
        text.alpha = 0.5  # state change
        self.assertEqual(text.alpha, 0.0)  # callback

    def test_color(self):
        figure = Figure()
        figure.suptitle("test", color="black")
        text = DynamicText(figure._suptitle)
        assert_equal_float(text.color.rgb, (0, 0, 0))
        text.color = "red"
        assert_equal_float(text.color.rgb, (1, 0, 0))

        # check errors
        # with self.assertRaises(TypeError) as cm:
        #     text.color = {"color": "can't", "accept": "dicts"}
        # err_msg = ("[DynamicColor.parse] could not parse color")
        # self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        with self.assertRaises(ValueError) as cm:
            text.color = (0, 1.3, 0.6)
        err_msg = ("[DynamicColor.parse] could not parse color")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        with self.assertRaises(ValueError) as cm:
            text.color = (0, -0.4, 0.2)
        err_msg = ("[DynamicColor.parse] could not parse color")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # test callbacks
        def callback(dynamic_text_instance):
            dynamic_text_instance.color.name = "black"
        
        text.color = "white"
        add_callback(text, "color", callback)
        text.color = "white"  # no state change
        assert_equal_float(text.color.rgb, (1, 1, 1))  # no callback
        text.color = "blue"  # state change
        assert_equal_float(text.color.rgb, (0, 0, 0))  # callback
