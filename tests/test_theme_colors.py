import unittest
from unittest.mock import Mock
from rbc_app import surface_theme_colors


class NativeThemeColorsTests(unittest.TestCase):
    def test_system_colors_remain_dynamic_instead_of_hard_coded_black(self):
        style=Mock()
        style.lookup.side_effect=lambda name,option: {'TFrame':'systemWindowBackgroundColor','TLabel':'systemLabelColor'}[name]
        self.assertEqual(surface_theme_colors(Mock(),style),('systemWindowBackgroundColor','systemLabelColor'))

    def test_light_and_dark_theme_text_is_preserved(self):
        for bg,fg in (('#eeeeee','#111111'),('#1e1e1e','#ffffff')):
            with self.subTest(background=bg):
                style=Mock()
                style.lookup.side_effect=lambda name,option:{'TFrame':bg,'TLabel':fg}[name]
                self.assertEqual(surface_theme_colors(Mock(),style),(bg,fg))
