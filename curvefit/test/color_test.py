from functools import partial
import numpy as np
import random
import unittest

import matplotlib as mpl

from curvefit.callback import add_callback
from curvefit.color import COLORS_NAMED, DynamicColor, NAMED_COLORS


assert_equal_float = partial(np.testing.assert_almost_equal, decimal=3)


class DynamicColorBasicTests(unittest.TestCase):

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
        color = DynamicColor((0.16666666, 1.0, 1.0), space="hsv")  # yellow
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
        self.assertEqual(color.name, "aqua")
        assert_equal_float(color.rgb, (0.0, 1.0, 1.0))
        assert_equal_float(color.rgba, (0.0, 1.0, 1.0, 0.6))

    def test_parse_in_place_errors(self):
        bad_color_type = 12345
        bad_color_value = "this is not a color-like"
        bad_space_type = 42
        bad_space_value = "this is an invalid color space"

        # bad_color_type
        color = DynamicColor("red")
        with self.assertRaises(ValueError) as cm:
            color.parse(bad_color_type)
        err_msg = ("[DynamicColor.parse] could not parse color")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_color_value
        with self.assertRaises(ValueError) as cm:
            color.parse(bad_color_value)
        err_msg = ("[DynamicColor.parse] could not parse color")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_space_type
        with self.assertRaises(ValueError) as cm:
            color.parse((0.5, 0.5, 0.5), space=bad_space_type)
        err_msg = ("[DynamicColor.parse] could not parse color")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_mode_value
        with self.assertRaises(ValueError) as cm:
            color.parse((0.5, 0.5, 0.5), space=bad_space_value)
        err_msg = ("[DynamicColor.parse] could not parse color")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

    def test_properties(self):
        color = DynamicColor((1, 0, 0, 1))
        expected = {
            "alpha": 1.0,
            "hex_code": "#ff0000ff",
            "hsv": (0, 1.0, 1.0),
            "name": "red",
            "rgb": (1.0, 0.0, 0.0),
            "rgba": (1.0, 0.0, 0.0, 1.0)
        }
        self.assertDictEqual(color.properties(), expected)

    def test_equality(self):
        color = DynamicColor((0, 1, 0))
        self.assertEqual(color, DynamicColor((0, 1, 0)))
        self.assertNotEqual(color, DynamicColor((1, 0, 0)))

    def test_hash(self):
        color1 = DynamicColor((0, 0, 1))
        color2 = DynamicColor((0, 0, 1))
        self.assertNotEqual(hash(color1), hash(color2))

    def test_repr(self):
        color = DynamicColor((1, 1, 0, 1))
        self.assertEqual(repr(color), "DynamicColor((1, 1, 0, 1))")

    def test_str(self):
        color = DynamicColor("red")
        self.assertEqual(str(color), "red")
        color.hex_code = "#0587ef77"
        self.assertEqual(str(color), "#0587ef77")


class DynamicColorCallbackTests(unittest.TestCase):

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

        color = DynamicColor((0, 0, 1), space="hsv")
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


class DynamicColorSweepTests(unittest.TestCase):

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
        color = DynamicColor(starting_color, space="hsv")
        for test_hue in np.linspace(0, 1, num=256):
            # get expected values:
            expected_hsv = (test_hue % 1,) + starting_color[1:]
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
        color = DynamicColor(starting_color, space="hsv")
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
        starting_color = (0.0, 0.0, 0.0)
        color = DynamicColor(starting_color, space="hsv")
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


class DynamicColorErrorTests(unittest.TestCase):

    def test_alpha_errors(self):
        bad_type = "1"
        negative = -1
        too_high = 1.5

        # bad_type
        color = DynamicColor("black")
        with self.assertRaises(ValueError) as cm:
            color.alpha = bad_type
        err_msg = ("[DynamicColor.alpha] `alpha` must be a numeric between 0 "
                   "and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # negative
        with self.assertRaises(ValueError) as cm:
            color.alpha = negative
        err_msg = ("[DynamicColor.alpha] `alpha` must be a numeric between 0 "
                   "and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # too_high
        with self.assertRaises(ValueError) as cm:
            color.alpha = too_high
        err_msg = ("[DynamicColor.alpha] `alpha` must be a numeric between 0 "
                   "and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

    def test_hex_code_errors(self):
        bad_type = 123456789  # length 9
        no_hash = "ffffff"
        bad_length = "#fffff"
        bad_value = "#fffffg"

        # bad_type
        color = DynamicColor("#000000")
        with self.assertRaises(ValueError) as cm:
            color.hex_code = bad_type
        err_msg = ("[DynamicColor.hex_code] `hex_code` must be a string of the "
                   "form '#rrggbb' or '#rrggbbaa'")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # no_hash
        with self.assertRaises(ValueError) as cm:
            color.hex_code = no_hash
        err_msg = ("[DynamicColor.hex_code] `hex_code` must be a string of the "
                   "form '#rrggbb' or '#rrggbbaa'")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_length
        with self.assertRaises(ValueError) as cm:
            color.hex_code = bad_length
        err_msg = ("[DynamicColor.hex_code] `hex_code` must be a string of the "
                   "form '#rrggbb' or '#rrggbbaa'")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_value
        with self.assertRaises(ValueError) as cm:
            color.hex_code = bad_value
        err_msg = ("[DynamicColor.hex_code] `hex_code` must be a string of the "
                   "form '#rrggbb' or '#rrggbbaa'")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

    def test_hsv_errors(self):
        bad_type = [1, 1, 1]
        bad_length = (0, 0.0, 0, 1.0)
        bad_val_type = (0.0, "0", 1)
        negative = (0, -0.2, 0.5)
        too_high = (1, 1.5, 0.5)

        # bad_type
        color = DynamicColor((0, 0, 0), space="hsv")
        with self.assertRaises(ValueError) as cm:
            color.hsv = bad_type
        err_msg = ("[DynamicColor.hsv] `hsv` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_length
        with self.assertRaises(ValueError) as cm:
            color.hsv = bad_length
        err_msg = ("[DynamicColor.hsv] `hsv` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_val_type
        with self.assertRaises(ValueError) as cm:
            color.hsv = bad_val_type
        err_msg = ("[DynamicColor.hsv] `hsv` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # negative
        with self.assertRaises(ValueError) as cm:
            color.hsv = negative
        err_msg = ("[DynamicColor.hsv] `hsv` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # too_high
        with self.assertRaises(ValueError) as cm:
            color.hsv = too_high
        err_msg = ("[DynamicColor.hsv] `hsv` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

    def test_named_color_errors(self):
        bad_type = 24.0
        not_recognized = "this is not a named color"

        # bad_type
        color = DynamicColor("black")
        with self.assertRaises(ValueError) as cm:
            color.name = bad_type
        err_msg = ("[DynamicColor.name] `name` must be a string referencing a "
                   "key in `NAMED_COLORS`")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # not_recognized
        with self.assertRaises(ValueError) as cm:
            color.name = not_recognized
        err_msg = ("[DynamicColor.name] `name` must be a string referencing a "
                   "key in `NAMED_COLORS`")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

    def test_rgb_errors(self):
        bad_type = [1, 1, 1]
        bad_length = (0, 0.0, 0, 1.0)
        bad_val_type = (0.0, "0", 1)
        negative = (0, -0.2, 0.5)
        too_high = (1, 1.5, 0.5)

        # bad_type
        color = DynamicColor((0, 0, 0))
        with self.assertRaises(ValueError) as cm:
            color.rgb = bad_type
        err_msg = ("[DynamicColor.rgb] `rgb` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_length
        with self.assertRaises(ValueError) as cm:
            color.rgb = bad_length
        err_msg = ("[DynamicColor.rgb] `rgb` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_val_type
        with self.assertRaises(ValueError) as cm:
            color.rgb = bad_val_type
        err_msg = ("[DynamicColor.rgb] `rgb` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # negative
        with self.assertRaises(ValueError) as cm:
            color.rgb = negative
        err_msg = ("[DynamicColor.rgb] `rgb` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # too_high
        with self.assertRaises(ValueError) as cm:
            color.rgb = too_high
        err_msg = ("[DynamicColor.rgb] `rgb` must be a length-3 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

    def test_rgba_errors(self):
        bad_type = [1, 1, 1, 1]
        bad_length = (0, 0.0, 0)
        bad_val_type = (0.0, "0", 1, 0.2)
        negative = (0, -0.2, 0.5, 1)
        too_high = (1, 1.5, 0.5, 0.8)

        # bad_type
        color = DynamicColor((0, 0, 0, 1.0))
        with self.assertRaises(ValueError) as cm:
            color.rgba = bad_type
        err_msg = ("[DynamicColor.rgba] `rgba` must be a length-4 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_length
        with self.assertRaises(ValueError) as cm:
            color.rgba = bad_length
        err_msg = ("[DynamicColor.rgba] `rgba` must be a length-4 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_val_type
        with self.assertRaises(ValueError) as cm:
            color.rgba = bad_val_type
        err_msg = ("[DynamicColor.rgba] `rgba` must be a length-4 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # negative
        with self.assertRaises(ValueError) as cm:
            color.rgba = negative
        err_msg = ("[DynamicColor.rgba] `rgba` must be a length-4 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # too_high
        with self.assertRaises(ValueError) as cm:
            color.rgba = too_high
        err_msg = ("[DynamicColor.rgba] `rgba` must be a length-4 tuple of "
                   "numerics between 0 and 1")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)


class DynamicColorBlendTests(unittest.TestCase):

    def test_additive_blend(self):
        # basic additive blend
        start = DynamicColor((0.1, 0.2, 0.3))
        blend = start.blend((0.1, 0.1, 0.1), mode="add")
        assert_equal_float(blend.rgb, (0.2, 0.3, 0.4))

        # clipping
        start = DynamicColor((0.7, 0.8, 0.9))
        blend = start.blend((0.2, 0.2, 0.2), mode="add")
        assert_equal_float(blend.rgb, (0.9, 1.0, 1.0))

        # quick blend
        start = DynamicColor((0.5, 0.5, 0.5))
        blend = start + (0.5, 0.5, 0.5)
        assert_equal_float(blend.rgb, (1.0, 1.0, 1.0))

        # in-place blend
        start = DynamicColor((0.1, 0.2, 0.3))
        start.blend((0.2, 0.2, 0.2), mode="add", in_place=True)
        assert_equal_float(start.rgb, (0.3, 0.4, 0.5))

        # quick blend in-place
        start = DynamicColor((0.3, 0.2, 0.1))
        start += (0.1, 0.2, 0.3)
        assert_equal_float(start.rgb, (0.4, 0.4, 0.4))

    def test_subtractive_blend(self):
        # basic subtractive blend
        start = DynamicColor((0.9, 0.8, 0.7))
        blend = start.blend((0.1, 0.1, 0.1), mode="subtract")
        assert_equal_float(blend.rgb, (0.8, 0.7, 0.6))

        # clipping
        start = DynamicColor((0.1, 0.2, 0.3))
        blend = start.blend((0.2, 0.2, 0.2), mode="subtract")
        assert_equal_float(blend.rgb, (0.0, 0.0, 0.1))

        # quick blend
        start = DynamicColor((0.5, 0.5, 0.5))
        blend = start - (0.5, 0.5, 0.5)
        assert_equal_float(blend.rgb, (0.0, 0.0, 0.0))

        # in-place blend
        start = DynamicColor((0.9, 0.7, 0.5))
        start.blend((0.2, 0.2, 0.2), mode="subtract", in_place=True)
        assert_equal_float(start.rgb, (0.7, 0.5, 0.3))

        # quick blend in-place
        start = DynamicColor((0.5, 0.5, 0.5))
        start -= (0.1, 0.2, 0.3)
        assert_equal_float(start.rgb, (0.4, 0.3, 0.2))

    def test_difference_blend(self):
        # basic difference blend
        start = DynamicColor((0.9, 0.8, 0.7))
        blend = start.blend((0.1, 0.1, 0.1), mode="difference")
        assert_equal_float(blend.rgb, (0.8, 0.7, 0.6))

        # clipping
        start = DynamicColor((0.1, 0.2, 0.3))
        blend = start.blend((0.2, 0.2, 0.2), mode="difference")
        assert_equal_float(blend.rgb, (0.1, 0.0, 0.1))

        # in-place blend
        start = DynamicColor((0.5, 0.5, 0.5))
        start.blend((0.5, 0.5, 0.5), mode="difference", in_place=True)
        assert_equal_float(start.rgb, (0.0, 0.0, 0.0))

    def test_multiplicative_blend(self):
        # basic multiplicative blend
        start = DynamicColor((0.5, 0.5, 0.5))
        blend = start.blend((0.5, 0.5, 0.5), mode="multiply")
        assert_equal_float(blend.rgb, (0.25, 0.25, 0.25))

        # quick blend
        start = DynamicColor((1, 1, 1))
        blend = start * (0, 0, 0)
        assert_equal_float(blend.rgb, (0.0, 0.0, 0.0))

        # in-place blend
        start = DynamicColor((0.1, 0.2, 0.3))
        start.blend((0.1, 0.2, 0.3), mode="multiply", in_place=True)
        assert_equal_float(start.rgb, (0.01, 0.04, 0.09))

        # quick blend in-place
        start = DynamicColor((0.9, 0.8, 0.7))
        start *= (0.1, 0.2, 0.3)
        assert_equal_float(start.rgb, (0.09, 0.16, 0.21))

    def test_division_blend(self):
        # basic division blend
        start = DynamicColor((0.5, 0.5, 0.5))
        blend = start.blend((0.9, 0.8, 0.7), mode="divide")
        assert_equal_float(blend.rgb, (0.55555, 0.625, 0.71429))

        # clipping
        start = DynamicColor((0.5, 0.5, 0.5))
        blend = start.blend((0.1, 1, 0), mode="divide")
        assert_equal_float(blend.rgb, (1.0, 0.5, 1.0))

        # quick blend
        start = DynamicColor((0.1, 0.2, 0.3))
        blend = start / (0.1, 0.2, 0.3)
        assert_equal_float(blend.rgb, (1.0, 1.0, 1.0))

        # in-place blend
        start = DynamicColor((0.1, 0.2, 0.3))
        start.blend((0.5, 0.5, 0.5), mode="divide", in_place=True)
        assert_equal_float(start.rgb, (0.2, 0.4, 0.6))

        # quick blend in-place
        start = DynamicColor((0.2, 0.2, 0.2))
        start /= (0.3, 0.4, 0.5)
        assert_equal_float(start.rgb, (0.66666, 0.5, 0.4))

    def test_burn_blend(self):
        # basic burn blend
        start = DynamicColor((0.5, 0.5, 0.5))
        blend = start.blend((0.6, 0.7, 0.8), mode="burn")
        assert_equal_float(blend.rgb, (0.16666, 0.28571, 0.375))

        # clipping
        start = DynamicColor((0.9, 0.8, 0.7))
        blend = start.blend((0.2, 0.1, 0.0), mode="burn")
        assert_equal_float(blend.rgb, (0.5, 0.0, 0.0))

        # in-place blend
        start = DynamicColor((0.8, 0.7, 0.6))
        start.blend((1, 1, 1), mode="burn", in_place=True)
        assert_equal_float(start.rgb, (0.8, 0.7, 0.6))

    def test_dodge_blend(self):
        # basic dodge blend
        start = DynamicColor((0.5, 0.5, 0.5))
        blend = start.blend((0.1, 0.2, 0.3), mode="dodge")
        assert_equal_float(blend.rgb, (0.55555, 0.625, 0.71429))

        # clipping
        start = DynamicColor((0.4, 0.4, 0.4))
        blend = start.blend((0.5, 0.6, 0.7), mode="dodge")
        assert_equal_float(blend.rgb, (0.8, 1.0, 1.0))

        # in-place blend
        start = DynamicColor((0.9, 0.8, 0.7))
        start.blend((0.0, 0.0, 0.0), mode="dodge", in_place=True)
        assert_equal_float(start.rgb, (0.9, 0.8, 0.7))

    def test_screen_blend(self):
        # basic screen blend
        start = DynamicColor((0.1, 0.2, 0.3))
        blend = start.blend((0.1, 0.2, 0.3), mode="screen")
        assert_equal_float(blend.rgb, (0.19, 0.36, 0.51))

        # in-place blend
        start = DynamicColor((0.5, 0.5, 0.5))
        start.blend((0.3, 0.5, 0.7), mode="screen", in_place=True)
        assert_equal_float(start.rgb, (0.65, 0.75, 0.85))

    def test_overlay_blend(self):
        # basic overlay blend
        start = DynamicColor((0.1, 0.2, 0.3))
        blend = start.blend((0.1, 0.2, 0.3), mode="screen")
        assert_equal_float(blend.rgb, (0.19, 0.36, 0.51))

        # in-place blend
        start = DynamicColor((0.5, 0.5, 0.5))
        start.blend((0.3, 0.5, 0.7), mode="screen", in_place=True)
        assert_equal_float(start.rgb, (0.65, 0.75, 0.85))

    def test_hard_light_blend(self):
        # basic hard light blend
        start = DynamicColor((0.1, 0.2, 0.3))
        blend = start.blend((0.6, 0.7, 0.8), mode="hard light")
        assert_equal_float(blend.rgb, (0.28, 0.52, 0.72))

        # in-place blend
        start = DynamicColor((0.9, 0.8, 0.7))
        start.blend((0.1, 0.2, 0.3), mode="hard light", in_place=True)
        assert_equal_float(start.rgb, (0.18, 0.32, 0.42))

    def test_soft_light_blend(self):
        # basic soft light blend
        start = DynamicColor((0.1, 0.2, 0.3))
        blend = start.blend((0.9, 0.8, 0.7), mode="soft light")
        assert_equal_float(blend.rgb, (0.172, 0.296, 0.384))

        # in-place blend
        start = DynamicColor((0.3, 0.3, 0.3))
        start.blend((0.4, 0.5, 0.6), mode="soft light", in_place=True)
        assert_equal_float(start.rgb, (0.258, 0.3, 0.342))

    def test_darken_blend(self):
        # basic darken blend
        start = DynamicColor((0.4, 0.5, 0.6))
        blend = start.blend((0.6, 0.5, 0.4), mode="darken")
        assert_equal_float(blend.rgb, (0.4, 0.5, 0.4))

        # in-place blend
        start = DynamicColor((0.1, 0.3, 0.5))
        start.blend((0.2, 0.3, 0.4), mode="darken", in_place=True)
        assert_equal_float(start.rgb, (0.1, 0.3, 0.4))

    def test_lighten_blend(self):
        # basic lighten blend
        start = DynamicColor((0.4, 0.5, 0.6))
        blend = start.blend((0.6, 0.5, 0.4), mode="lighten")
        assert_equal_float(blend.rgb, (0.6, 0.5, 0.6))

        # in-place blend
        start = DynamicColor((0.1, 0.3, 0.5))
        start.blend((0.2, 0.3, 0.4), mode="lighten", in_place=True)
        assert_equal_float(start.rgb, (0.2, 0.3, 0.5))

    def test_blend_errors(self):
        bad_color_type = 12345
        bad_color_value = "this is not a color-like"
        bad_mode_type = 42
        bad_mode_value = "fake_space"

        # bad_color_type
        color = DynamicColor("red")
        with self.assertRaises(ValueError) as cm:
            color.blend(bad_color_type, mode="multiply")
        err_msg = ("[DynamicColor.blend] could not blend colors")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_color_value
        with self.assertRaises(ValueError) as cm:
            color.blend(bad_color_value, mode="multiply")
        err_msg = ("[DynamicColor.blend] could not blend colors")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_mode_type
        with self.assertRaises(ValueError) as cm:
            color.blend((0.5, 0.5, 0.5), mode=bad_mode_type)
        err_msg = ("[DynamicColor.blend] `mode` must be a string with one of "
                   "the following values:")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_mode_value
        with self.assertRaises(ValueError) as cm:
            color.blend((0.5, 0.5, 0.5), mode=bad_mode_value)
        err_msg = ("[DynamicColor.blend] `mode` must be a string with one of "
                   "the following values:")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)


class DynamicColorDistanceTests(unittest.TestCase):

    def test_distance_measure(self):
        # unweighted distance
        color = DynamicColor((1, 1, 1))
        assert_equal_float(color.distance((1, 1, 1)), 0.0)
        assert_equal_float(color.distance((0, 0, 0)), 1.73205)

        # weighted redmean distance
        assert_equal_float(color.distance((1, 1, 1), weighted=True), 0.0)
        assert_equal_float(color.distance((0, 0, 0), weighted=True), 2.99935)

    def test_distance_measure_errors(self):
        bad_color_type = 12345
        bad_color_value = "this is not a color-like"

        # bad_color_type
        color = DynamicColor("red")
        with self.assertRaises(ValueError) as cm:
            color.distance(bad_color_type)
        err_msg = ("[DynamicColor.distance] could not compute distance")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)

        # bad_color_value
        with self.assertRaises(ValueError) as cm:
            color.distance(bad_color_value)
        err_msg = ("[DynamicColor.distance] could not compute distance")
        self.assertEqual(str(cm.exception)[:len(err_msg)], err_msg)


class DynamicColorInversionTests(unittest.TestCase):

    def test_invert(self):
        # standard inversion
        color = DynamicColor((0, 0, 0))
        inverted = color.invert()
        assert_equal_float(inverted.rgb, (1.0, 1.0, 1.0))

        # in-place inversion
        color.invert(in_place=True)
        assert_equal_float(color.rgb, (1.0, 1.0, 1.0))

    def test_parse_in_place(self):
        hex_code_noalpha = "#00ff00"
        hex_code_alpha = "#00ff0080"
        hsv = (0, 1, 1)
        name = "blue"
        rgb = (1, 1, 0)
        rgba = (0, 1, 1, 0.8)

        color = DynamicColor("white")
        color.parse(hex_code_noalpha)
        self.assertEqual(color.hex_code, hex_code_noalpha + "ff")
        color.parse(hex_code_alpha)
        self.assertEqual(color.hex_code, hex_code_alpha)
        color.parse(hsv, space="hsv")
        assert_equal_float(color.hsv, hsv)
        color.parse(name)
        self.assertEqual(color.name, name)
        color.parse(rgb)
        assert_equal_float(color.rgb, rgb)
        color.parse(rgba)
        assert_equal_float(color.rgba, rgba)
