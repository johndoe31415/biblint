#!/usr/bin/python3
#
#	biblint - Static checking of BibTeX files to find errors or inconsistencies.
#	Copyright (C) 2016-2016 Johannes Bauer
#
#	This file is part of biblint.
#
#	biblint is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	biblint is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with biblint; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <joe@johannes-bauer.com>
#

import unittest

from TextFragmentTracker import TextFragmentTracker

class TextFragmentTrackerTests(unittest.TestCase):
	def test_simple(self):
		# Simple test case
		text = TextFragmentTracker("AaBbCcDdEe")
		text._offsetmap = [ [ 0, 0 ], [ 2, 10 ], [ 4, 20 ], [ 6, 30 ], [ 8, 40 ] ]
		self.assertEqual(list(text), [(0, 'A'), (1, 'a'), (10, 'B'), (11, 'b'), (20, 'C'), (21, 'c'), (30, 'D'), (31, 'd'), (40, 'E'), (41, 'e')])

	def test_removal_within_spans(self):
		# Regular test case with removals within spans
		text = TextFragmentTracker("Foo^^bar Moo^^koo Blah^^Blubb")
		text._offsetmap = [ [ 0, 0 ], [ 9, 100 ], [ 18, 200 ] ]
		self.assertEqual(list(text), [(0, 'F'), (1, 'o'), (2, 'o'), (3, '^'), (4, '^'), (5, 'b'), (6, 'a'), (7, 'r'), (8, ' '), (100, 'M'), (101, 'o'), (102, 'o'), (103, '^'), (104, '^'), (105, 'k'), (106, 'o'), (107, 'o'), (108, ' '), (200, 'B'), (201, 'l'), (202, 'a'), (203, 'h'), (204, '^'), (205, '^'), (206, 'B'), (207, 'l'), (208, 'u'), (209, 'b'), (210, 'b')])
		text.delete_span((3, 5))
		self.assertEqual(list(text), [(0, 'F'), (1, 'o'), (2, 'o'), (5, 'b'), (6, 'a'), (7, 'r'), (8, ' '), (100, 'M'), (101, 'o'), (102, 'o'), (103, '^'), (104, '^'), (105, 'k'), (106, 'o'), (107, 'o'), (108, ' '), (200, 'B'), (201, 'l'), (202, 'a'), (203, 'h'), (204, '^'), (205, '^'), (206, 'B'), (207, 'l'), (208, 'u'), (209, 'b'), (210, 'b')])
		text.delete_span((10, 12))
		self.assertEqual(list(text), [(0, 'F'), (1, 'o'), (2, 'o'), (5, 'b'), (6, 'a'), (7, 'r'), (8, ' '), (100, 'M'), (101, 'o'), (102, 'o'), (105, 'k'), (106, 'o'), (107, 'o'), (108, ' '), (200, 'B'), (201, 'l'), (202, 'a'), (203, 'h'), (204, '^'), (205, '^'), (206, 'B'), (207, 'l'), (208, 'u'), (209, 'b'), (210, 'b')])
		text.delete_span((18, 20))
		self.assertEqual(list(text), [(0, 'F'), (1, 'o'), (2, 'o'), (5, 'b'), (6, 'a'), (7, 'r'), (8, ' '), (100, 'M'), (101, 'o'), (102, 'o'), (105, 'k'), (106, 'o'), (107, 'o'), (108, ' '), (200, 'B'), (201, 'l'), (202, 'a'), (203, 'h'), (206, 'B'), (207, 'l'), (208, 'u'), (209, 'b'), (210, 'b')])

	def test_removal_beginning(self):
		# Test case with removal at the beginning
		text = TextFragmentTracker("Foobar")
		self.assertEqual(list(text), [(0, 'F'), (1, 'o'), (2, 'o'), (3, 'b'), (4, 'a'), (5, 'r')] )
		text.delete_span((0, 3))
		self.assertEqual(list(text), [(3, 'b'), (4, 'a'), (5, 'r')] )

	def test_removal_multiple_spans_1(self):
		# Test case with removal over multiple spans
		text = TextFragmentTracker("FooXYZBar")
		text._offsetmap = [ [0, 0], [ 3, 100 ],[ 4, 200 ],[ 5, 300 ], [6, 1000] ]
		self.assertEqual(list(text), [(0, 'F'), (1, 'o'), (2, 'o'), (100, 'X'), (200, 'Y'), (300, 'Z'), (1000, 'B'), (1001, 'a'), (1002, 'r')])
		text.delete_span((3, 6))
		self.assertEqual(list(text), [(0, 'F'), (1, 'o'), (2, 'o'), (1000, 'B'), (1001, 'a'), (1002, 'r')])

	def test_removal_multiple_spans_2(self):
		# Test case with removal over multiple spans not starting in one
		text = TextFragmentTracker("FooBarKoo")
		text._offsetmap = [ [ 0, 0 ], [3, 100], [4, 200], [5, 300], [6, 1000] ]
		self.assertEqual(list(text), [(0, 'F'), (1, 'o'), (2, 'o'), (100, 'B'), (200, 'a'), (300, 'r'), (1000, 'K'), (1001, 'o'), (1002, 'o')])
		text.delete_span((1, 7))
		self.assertEqual(text._offsetmap, [ [ 0, 0 ], [ 1, 1001 ] ])
		self.assertEqual(list(text), [(0, 'F'), (1001, 'o'), (1002, 'o')])

	def test_numbers(self):
		# Number test
		text = TextFragmentTracker("Numbers at eleven and another at 33 at at 42.")
		self.assertEqual(text.translate_offset(text.text.index("33")), 33)
		self.assertEqual(text.translate_offset(text.text.index("42")), 42)
		text.delete_regex("at ")
		self.assertEqual(text.translate_offset(text.text.index("33")), 33)
		self.assertEqual(text.translate_offset(text.text.index("42")), 42)

	def _assert_integrity(self, text):
		assert(all(pos % 10 == int(char) for (pos, char) in text))

	def test_long_text(self):
		# Remove long text
		text = TextFragmentTracker("0123456789" * 3)
		text.delete_regex("012345")
		self._assert_integrity(text)

	def test_remove_head(self):
		# Head remove test
		text = TextFragmentTracker("0123456789" * 3)

		text.delete_regex("012345678")
		self._assert_integrity(text)

	def test_remove_multiple(self):
		# Multiple remove test
		text = TextFragmentTracker("0123456789" * 10)
		text.delete_regex("7")
		self._assert_integrity(text)
		text.delete_regex("2.4")
		self._assert_integrity(text)
		text.delete_regex("0")
		self._assert_integrity(text)
		text.delete_regex("915")
		self._assert_integrity(text)

	def test_simple_replacement(self):
		text = TextFragmentTracker("foobarMUHKUH12345")
		self.assertEqual(list(text), [(0, 'f'), (1, 'o'), (2, 'o'), (3, 'b'), (4, 'a'), (5, 'r'), (6, 'M'), (7, 'U'), (8, 'H'), (9, 'K'), (10, 'U'), (11, 'H'), (12, '1'), (13, '2'), (14, '3'), (15, '4'), (16, '5')])
		text._debug = True
		text.replace_regex("MUHKUH", "qwe")
		self.assertEqual(list(text), [(0, 'f'), (1, 'o'), (2, 'o'), (3, 'b'), (4, 'a'), (5, 'r'), (6, 'q'), (7, 'w'), (8, 'e'), (12, '1'), (13, '2'), (14, '3'), (15, '4'), (16, '5')])

if __name__ == "__main__":
	unittest.main()



