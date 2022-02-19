from functools import partial
import unittest

import numpy as np
from matplotlib.text import Text

from curvefit.text import DynamicText


assert_equal_float = partial(np.testing.assert_almost_equal, decimal=3)


class DynamicTextBasicTests(unittest.TestCase):

    def test_basic_init(self):
        text_obj = Text(text="test")
        dtext = DynamicText(text_obj)
        self.assertEqual(dtext.text, "test")

        # with kwargs
        dtext = DynamicText(text_obj, alpha=0.8, color="white")
        self.assertEqual(dtext.text, "test")
        assert_equal_float(dtext.alpha, 0.8)
        self.assertEqual(dtext.color.name, "white")

    # def test
        