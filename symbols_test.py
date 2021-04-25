import unittest

import symbols

class TestSymbols(unittest.TestCase):
    def test_symbols(self):
        self.assertEqual(symbols.get_drive_position_symbols([0, 0]), ["\N{UPWARDS BLACK ARROW}", "\N{BLACK RIGHTWARDS ARROW}", "\N{OCTAGONAL SIGN}"])
        self.assertEqual(symbols.get_drive_position_symbols([16, 16]), ["\N{LEFTWARDS BLACK ARROW}", "\N{DOWNWARDS BLACK ARROW}", "\N{OCTAGONAL SIGN}"])
        self.assertEqual(symbols.get_drive_position_symbols([16, 0]), ["\N{LEFTWARDS BLACK ARROW}", "\N{UPWARDS BLACK ARROW}", "\N{OCTAGONAL SIGN}"])
        self.assertEqual(symbols.get_drive_position_symbols([0, 16]), ["\N{DOWNWARDS BLACK ARROW}", "\N{BLACK RIGHTWARDS ARROW}", "\N{OCTAGONAL SIGN}"])
        self.assertEqual(symbols.get_drive_position_symbols([4, 4]), ["\N{LEFTWARDS BLACK ARROW}", "\N{DOWNWARDS BLACK ARROW}", "\N{UPWARDS BLACK ARROW}", "\N{BLACK RIGHTWARDS ARROW}", "\N{OCTAGONAL SIGN}"])
        self.assertEqual(symbols.get_drive_position_symbols([0, 5]), ["\N{DOWNWARDS BLACK ARROW}", "\N{UPWARDS BLACK ARROW}", "\N{BLACK RIGHTWARDS ARROW}", "\N{OCTAGONAL SIGN}"])
        self.assertEqual(symbols.get_drive_position_symbols([5, 0]), ["\N{LEFTWARDS BLACK ARROW}", "\N{UPWARDS BLACK ARROW}", "\N{BLACK RIGHTWARDS ARROW}", "\N{OCTAGONAL SIGN}"])

if __name__ == '__main__':
    unittest.main()
