import unittest
from futures_lab.fast_cursor import Cursor

class CursorTests(unittest.TestCase):
    def test_sequence(self):
        c=Cursor(bytes.fromhex("c0 80 81 ff 82"))
        self.assertTrue(c.pmap()[0])
        self.assertIsNone(c.integer(nullable=True))
        self.assertEqual(c.integer(nullable=True),0)
        self.assertEqual(c.integer(nullable=True,is_signed=True),-1)
        self.assertEqual(c.integer(nullable=True,is_signed=True),1)
        c.finish()
    def test_failure(self):
        c=Cursor(b"\x00")
        with self.assertRaises(ValueError):
            c.integer()
        self.assertEqual(c.pos,0)
        with self.assertRaises(ValueError):
            c.finish()
    def test_nullable_maximum(self):
        c=Cursor(bytes.fromhex("08 00 00 00 80"))
        self.assertEqual(c.integer(nullable=True),2**32-1)
        c.finish()
