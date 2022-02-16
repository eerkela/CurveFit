from functools import partial
import numpy as np
import random
import unittest

import matplotlib as mpl

from curvefit.callback import add_callback
from curvefit.color import COLORS_NAMED, DynamicColor, NAMED_COLORS


"""
TODO: generate error handling + blend/diff/invert tests
"""


assert_equal_float = partial(np.testing.assert_almost_equal, decimal=3)


class DynamicColorTestCases(unittest.TestCase):

    def test_init_hex_code_no_alpha(self):
        color = DynamicColor("#ff0000")  # pure red
        assert_equal_float(color.alpha, 1.0)
        self.assertEqual(color.hex_code, "#ff0000ff")
        assert_equal_float(color.hsv, (0.0, 1.0, 1.0))
        self.assertEqual(color.name, "red")
        assert_equal_float(color.rgb, (1.0, 0.0, 0.0))
        assert_equal_float(color.rgba, (1.0, 0.0, 0.0, 1.0))

    def test_init_hex_code_with_alpha(self):
        color = DynamicColor("#00ff0080")  # pure green
        assert_equal_float(color.alpha, 0.50196)
        self.assertEqual(color.hex_code, "#00ff0080")
        assert_equal_float(color.hsv, (0.33333, 1.0, 1.0))
        self.assertEqual(color.name, 'lime')
        assert_equal_float(color.rgb, (0.0, 1.0, 0.0))
        assert_equal_float(color.rgba, (0.0, 1.0, 0.0, 0.50196))

    def test_init_hsv(self):
        color = DynamicColor((0.16666666, 1.0, 1.0), color_spec="hsv")  # yellow
        assert_equal_float(color.alpha, 1.0)
        self.assertEqual(color.hex_code, "#ffff00ff")
        assert_equal_float(color.hsv, (0.16666, 1.0, 1.0))
        self.assertEqual(color.name, "yellow")
        assert_equal_float(color.rgb, (1.0, 1.0, 0.0))
        assert_equal_float(color.rgba, (1.0, 1.0, 0.0, 1.0))

    def test_init_named_color(self):
        color = DynamicColor("blue")  # pure blue
        assert_equal_float(color.alpha, 1.0)
        self.assertEqual(color.hex_code, "#0000ffff")
        assert_equal_float(color.hsv, (0.66666, 1.0, 1.0))
        self.assertEqual(color.name, "blue")
        assert_equal_float(color.rgb, (0.0, 0.0, 1.0))
        assert_equal_float(color.rgba, (0.0, 0.0, 1.0, 1.0))

    def test_init_rgb(self):
        color = DynamicColor((1, 0, 1))  # magenta
        assert_equal_float(color.alpha, 1.0)
        self.assertEqual(color.hex_code, "#ff00ffff")
        assert_equal_float(color.hsv, (0.83333, 1.0, 1.0))
        self.assertEqual(color.name, "fuchsia")
        assert_equal_float(color.rgb, (1.0 ,0.0, 1.0))
        assert_equal_float(color.rgba, (1.0, 0.0, 1.0, 1.0))

    def test_init_rgba(self):
        color = DynamicColor((0.0, 1.0, 1.0, 0.6))  # cyan, 60% opacity
        assert_equal_float(color.alpha, 0.6)
        self.assertEqual(color.hex_code, "#00ffff99")
        assert_equal_float(color.hsv, (0.5, 1.0, 1.0))
        self.assertEqual(color.name, "xkcd:cyan")
        assert_equal_float(color.rgb, (0.0, 1.0, 1.0))
        assert_equal_float(color.rgba, (0.0, 1.0, 1.0, 0.6))

    def test_red_sweep(self):
        starting_color = (0.0, 0.0, 0.0)
        color = DynamicColor(starting_color)
        if len(starting_color) == 4:
            expected_alpha = starting_color[-1]
        else:
            expected_alpha = 1.0
        for test_red in np.linspace(0, 1, num=256):
            # get expected values:
            expected_rgba = (test_red,) + starting_color[1:]
            expected_hex = mpl.colors.to_hex(expected_rgba, keep_alpha=True)
            expected_hsv = tuple(mpl.colors.rgb_to_hsv(expected_rgba[:3]))

            # set and test:
            color.rgb = expected_rgba[:3]
            assert_equal_float(color.alpha, expected_alpha)
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgba[:3])
            if len(expected_rgba) == 4:
                assert_equal_float(color.rgba, expected_rgba)
            else:
                assert_equal_float(color.rgba, expected_rgba + (1.0,))

    def test_green_sweep(self):
        starting_color = (0.0, 0.0, 0.0)
        color = DynamicColor(starting_color)
        if len(starting_color) == 4:
            expected_alpha = starting_color[-1]
        else:
            expected_alpha = 1.0
        for test_green in np.linspace(0, 1, num=256):
            # get expected values:
            expected_rgba = starting_color[:1] + (test_green,) + starting_color[2:]
            expected_hex = mpl.colors.to_hex(expected_rgba, keep_alpha=True)
            expected_hsv = tuple(mpl.colors.rgb_to_hsv(expected_rgba[:3]))

            # set and test:
            color.rgb = expected_rgba[:3]
            assert_equal_float(color.alpha, expected_alpha)
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgba[:3])
            if len(expected_rgba) == 4:
                assert_equal_float(color.rgba, expected_rgba)
            else:
                assert_equal_float(color.rgba, expected_rgba + (1.0,))

    def test_blue_sweep(self):
        starting_color = (0.0, 0.0, 0.0)
        color = DynamicColor(starting_color)
        if len(starting_color) == 4:
            expected_alpha = starting_color[-1]
        else:
            expected_alpha = 1.0
        for test_blue in np.linspace(0, 1, num=256):
            # get expected values:
            expected_rgba = starting_color[:2] + (test_blue,) + starting_color[3:]
            expected_hex = mpl.colors.to_hex(expected_rgba, keep_alpha=True)
            expected_hsv = tuple(mpl.colors.rgb_to_hsv(expected_rgba[:3]))

            # set and test:
            color.rgb = expected_rgba[:3]
            assert_equal_float(color.alpha, expected_alpha)
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgba[:3])
            if len(expected_rgba) == 4:
                assert_equal_float(color.rgba, expected_rgba)
            else:
                assert_equal_float(color.rgba, expected_rgba + (1.0,))

    def test_alpha_sweep(self):
        starting_color = (1.0, 1.0, 1.0, 0.0)
        color = DynamicColor(starting_color)
        for test_alpha in np.linspace(0, 1, num=256):
            # get expected values:
            expected_rgba = starting_color[:-1] + (test_alpha,)
            expected_hex = mpl.colors.to_hex(expected_rgba, keep_alpha=True)
            expected_hsv = tuple(mpl.colors.rgb_to_hsv(expected_rgba[:-1]))

            # set and test:
            color.alpha = test_alpha
            assert_equal_float(color.alpha, test_alpha)
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgba[:-1])
            assert_equal_float(color.rgba, expected_rgba)

    def test_hex_red_sweep(self):
        starting_color = "#000000ff"
        color = DynamicColor(starting_color)
        for test_red in range(0, 255):
            # get expected values:
            hex_red = hex(test_red).split("x")[-1]
            if len(hex_red) < 2:
                hex_red = "0" + hex_red
            expected_hex = f"#{hex_red}{starting_color[3:]}"
            expected_rgba = mpl.colors.to_rgba(expected_hex)
            expected_hsv = mpl.colors.rgb_to_hsv(expected_rgba[:3])

            # set and test:
            color.hex_code = expected_hex
            assert_equal_float(color.alpha, expected_rgba[-1])
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgba[:3])
            assert_equal_float(color.rgba, expected_rgba)

    def test_hex_green_sweep(self):
        starting_color = "#000000ff"
        color = DynamicColor(starting_color)
        for test_green in range(0, 255):
            # get expected values:
            hex_green = hex(test_green).split("x")[-1]
            if len(hex_green) < 2:
                hex_green = "0" + hex_green
            expected_hex = f"{starting_color[:3]}{hex_green}{starting_color[5:]}"
            expected_rgba = mpl.colors.to_rgba(expected_hex)
            expected_hsv = mpl.colors.rgb_to_hsv(expected_rgba[:3])

            # set and test:
            color.hex_code = expected_hex
            assert_equal_float(color.alpha, expected_rgba[-1])
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgba[:3])
            assert_equal_float(color.rgba, expected_rgba)

    def test_hex_blue_sweep(self):
        starting_color = "#000000ff"
        color = DynamicColor(starting_color)
        for test_blue in range(0, 255):
            # get expected values:
            hex_blue = hex(test_blue).split("x")[-1]
            if len(hex_blue) < 2:
                hex_blue = "0" + hex_blue
            expected_hex = f"{starting_color[:5]}{hex_blue}{starting_color[7:]}"
            expected_rgba = mpl.colors.to_rgba(expected_hex)
            expected_hsv = mpl.colors.rgb_to_hsv(expected_rgba[:3])

            # set and test:
            color.hex_code = expected_hex
            assert_equal_float(color.alpha, expected_rgba[-1])
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgba[:3])
            assert_equal_float(color.rgba, expected_rgba)

    def test_hex_alpha_sweep(self):
        starting_color = "#ffffff00"
        color = DynamicColor(starting_color)
        for test_alpha in range(0, 255):
            # get expected values:
            hex_alpha = hex(test_alpha).split("x")[-1]
            if len(hex_alpha) < 2:
                hex_alpha = "0" + hex_alpha
            expected_hex = f"{starting_color[:-2]}{hex_alpha}"
            expected_rgba = mpl.colors.to_rgba(expected_hex)
            expected_hsv = mpl.colors.rgb_to_hsv(expected_rgba[:3])

            # set and test:
            color.hex_code = expected_hex
            assert_equal_float(color.alpha, expected_rgba[-1])
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgba[:3])
            assert_equal_float(color.rgba, expected_rgba)

    def test_hue_sweep(self):
        starting_color = (0.0, 1.0, 1.0)
        color = DynamicColor(starting_color, color_spec="hsv")
        for test_hue in np.linspace(0, 1, num=256):
            # get expected values:
            expected_hsv = (test_hue,) + starting_color[1:]
            expected_rgb = tuple(mpl.colors.hsv_to_rgb(expected_hsv))
            expected_hex = mpl.colors.to_hex(expected_rgb, keep_alpha=True)

            # set and test:
            color.hsv = expected_hsv
            assert_equal_float(color.alpha, 1.0)
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgb)
            assert_equal_float(color.rgba, expected_rgb + (1.0,))

    def test_saturation_sweep(self):
        starting_color = (0.0, 0.0, 1.0)
        color = DynamicColor(starting_color, color_spec="hsv")
        for test_sat in np.linspace(0, 1, num=256):
            # get expected values:
            expected_hsv = starting_color[:1] + (test_sat,) + starting_color[2:]
            expected_rgb = tuple(mpl.colors.hsv_to_rgb(expected_hsv))
            expected_hex = mpl.colors.to_hex(expected_rgb, keep_alpha=True)

            # set and test:
            color.hsv = expected_hsv
            assert_equal_float(color.alpha, 1.0)
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgb)
            assert_equal_float(color.rgba, expected_rgb + (1.0,))

    def test_value_sweep(self):
        starting_color = (0.0, 1.0, 0.0)
        color = DynamicColor(starting_color, color_spec="hsv")
        for test_val in np.linspace(0, 1, num=256):
            # get expected values:
            expected_hsv = starting_color[:2] + (test_val,)
            expected_rgb = tuple(mpl.colors.hsv_to_rgb(expected_hsv))
            expected_hex = mpl.colors.to_hex(expected_rgb, keep_alpha=True)

            # set and test:
            color.hsv = expected_hsv
            assert_equal_float(color.alpha, 1.0)
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgb)
            assert_equal_float(color.rgba, expected_rgb + (1.0,))

    def test_name_sweep(self):
        def sample_dict(d: dict, size: int):
            keys = random.sample(list(d), size)
            values = [d[k] for k in keys]
            return dict(zip(keys, values))

        random.seed(123)
        name_sample = sample_dict(NAMED_COLORS, size=32)
        color = DynamicColor("white")
        for name in name_sample:
            # get expected values:
            expected_hex = NAMED_COLORS[name] + "ff"
            expected_rgb = mpl.colors.to_rgb(expected_hex)
            expected_hsv = tuple(mpl.colors.rgb_to_hsv(expected_rgb))

            # set and test:
            color.name = name
            assert_equal_float(color.alpha, 1.0)
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            assert_equal_float(color.rgb, expected_rgb)
            assert_equal_float(color.rgba, expected_rgb + (1.0,))

    def test_name_detection(self):
        def sample_dict(d: dict, size: int):
            keys = random.sample(list(d), size)
            values = [d[k] for k in keys]
            return dict(zip(keys, values))

        random.seed(123)
        hex_sample = sample_dict(COLORS_NAMED, size=32)
        color = DynamicColor("white")
        for hex_code in hex_sample:
            # get expected values:
            expected_name = COLORS_NAMED[hex_code][0]
            expected_hex = hex_code + "ff"
            expected_rgb = mpl.colors.to_rgb(expected_hex)
            expected_hsv = tuple(mpl.colors.rgb_to_hsv(expected_rgb))

            # set and test:
            color.hex_code = hex_code
            assert_equal_float(color.alpha, 1.0)
            self.assertEqual(color.hex_code, expected_hex)
            assert_equal_float(color.hsv, expected_hsv)
            self.assertEqual(color.name, expected_name)
            assert_equal_float(color.rgb, expected_rgb)
            assert_equal_float(color.rgba, expected_rgb + (1.0,))

    def test_alpha_callback(self):
        def callback(color_instance):
            color_instance.alpha = 0

        color = DynamicColor("white")
        add_callback(color, "alpha", callback)
        assert_equal_float(color.alpha, 1.0)
        color.alpha = 1.0  # no state change
        assert_equal_float(color.alpha, 1.0)  # callback not invoked
        color.alpha = 0.5  # state change
        assert_equal_float(color.alpha, 0.0)  # callback invoked

    def test_hex_code_callback(self):
        def callback(color_instance):
            color_instance.hex_code = "#000000ff"

        color = DynamicColor("#ffffffff")
        add_callback(color, "hex_code", callback)
        self.assertEqual(color.hex_code, "#ffffffff")
        color.hex_code = "#ffffffff"  # no state change
        self.assertEqual(color.hex_code, "#ffffffff")  # callback not invoked
        color.hex_code = "#ff0000ff"  # state change
        self.assertEqual(color.hex_code, "#000000ff")  # callback invoked

    def test_hsv_callback(self):
        def callback(color_instance):
            color_instance.hsv = (0, 0, 0)

        color = DynamicColor((0, 0, 1), color_spec="hsv")
        add_callback(color, "hsv", callback)
        assert_equal_float(color.hsv, (0.0, 0.0, 1.0))
        color.hsv = (0.0, 0.0, 1.0)  # no state change
        assert_equal_float(color.hsv, (0.0, 0.0, 1.0))  # callback not invoked
        color.hsv = (0.0, 1.0, 1.0)  # state change
        assert_equal_float(color.hsv, (0.0, 0.0, 0.0))  # callback invoked

    def test_name_callback(self):
        def callback(color_instance):
            color_instance.name = "black"

        color = DynamicColor("white")
        add_callback(color, "name", callback)
        self.assertEqual(color.name, "white")
        color.name = "white"  # no state change
        self.assertEqual(color.name, "white")  # callback not invoked
        color.name = "red"  # state change
        self.assertEqual(color.name, "black")  # callback invoked

    def test_rgb_callback(self):
        def callback(color_instance):
            color_instance.rgb = (0, 0, 0)

        color = DynamicColor((1, 1, 1))
        add_callback(color, "rgb", callback)
        assert_equal_float(color.rgb, (1.0, 1.0, 1.0))
        color.rgb = (1.0, 1.0, 1.0)  # no state change
        assert_equal_float(color.rgb, (1.0, 1.0, 1.0))  # callback not invoked
        color.rgb = (1.0, 0.0, 0.0)  # state change
        assert_equal_float(color.rgb, (0.0, 0.0, 0.0))  # callback invoked

    def test_rgba_callback(self):
        def callback(color_instance):
            color_instance.rgba = (0, 0, 0, 0)

        color = DynamicColor((1, 1, 1, 1))
        add_callback(color, "rgba", callback)
        assert_equal_float(color.rgba, (1.0, 1.0, 1.0, 1.0))
        color.rgba = (1.0, 1.0, 1.0, 1.0)  # no state change
        assert_equal_float(color.rgba, (1.0, 1.0, 1.0, 1.0))  # callback not invoked
        color.rgba = (1.0, 0.0, 0.0, 1.0)  # state change
        assert_equal_float(color.rgba, (0.0, 0.0, 0.0, 0.0))  # callback invoked
