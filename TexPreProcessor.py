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

import re
import bisect
import sys

class _TextFragment(object):
	def __init__(self, text):
		self._text = text
		self._offsetmap = [ [ 0, 0 ] ]

	def _assert_offsetmap_integrity(self):
		last_src = self._offsetmap[0][0]
		if not last_src == 0:
			raise AssertionError("offsetmap[0][0] is not starting with zero index.")
		for (index, (src, dst)) in enumerate(self._offsetmap[1:]):
			if src <= last_src:
				raise AssertionError("offsetmap is not strictly monotonically increasing, error at index %d: %s" % (index + 1, str(self._offsetmap)))
			last_src = src

	@property
	def text(self):
		return self._text

	def delete_span(self, span):
		# Assign some helper variables first
		(span_from, span_to) = span
		length = span_to - span_from
		print("Removing span [ %d; %d ] length %d" % (span_from, span_to, length))
		
		# Remove the span in the actual text
		self._text = self._text[ : span_from] + self._text[span_to : ]

		# Then find out the current translated offset
		(index_from, translated_from) = self.translate_full_offset(span_from)
		(index_to, translated_to) = self.translate_full_offset(span_to)
		print("Previously: offset %d is idx %d-%d (%s - %s), translated_offset end = %d" % (span_to, index_from, index_to, self._offsetmap[index_from], self._offsetmap[index_to], translated_to))

		# Remove old spans first
		print("PRE ", self._offsetmap)
		self._offsetmap = self._offsetmap[ : index_from + 1 ] + self._offsetmap[index_to + 1 : ]
		print("POST", self._offsetmap)

		# Then insert new one
		insert_index = index_from + 1
		new_element = [ span_from, translated_to ]
		print("New element: %s" % (new_element))

		if self._offsetmap[index_from][0] == new_element[0]:
			old_element = self._offsetmap[index_from]
			print("Updating index of element at %d: %s -> %s" % (insert_index, old_element, new_element))
			self._offsetmap[index_from] = new_element
		else:
			print("Inserting new element at %d: %s" % (insert_index, new_element))
			self._offsetmap.insert(insert_index, new_element)

		for i in range(insert_index + 1, len(self._offsetmap)):
			self._offsetmap[i][0] -= length

		# Only during debugging, check list after every modification
		self._assert_offsetmap_integrity()
		print()

	def delete_regex(self, regex):
		regex = re.compile(regex)
		deletions = [ ]
		for deletion in regex.finditer(self.text):
			deletions.append(deletion.span())
		for span in reversed(deletions):
			self.delete_span(span)

	def translate_offset_index(self, qry_offset):
		index = bisect.bisect_left(self._offsetmap, [ qry_offset + 1, 0 ]) - 1
		if index == -1:
			index = 0
		return index

	def translate_full_offset(self, qry_offset):
		index = self.translate_offset_index(qry_offset)
		span = self._offsetmap[index]
		distance = span[1] - span[0]
		return (index, qry_offset + distance)
	
	def translate_offset(self, qry_offset):
		return self.translate_full_offset(qry_offset)[1]

	def dump(self):
		for (offset, char) in enumerate(self.text):
			(index, xoffset) = self.translate_full_offset(offset)
			print("%2d %2d %3d %s" % (offset, index, xoffset, char))

	def __iter__(self):
		for (offset, pos) in enumerate(self.text):
			yield (self.translate_offset(offset), pos)

	def __str__(self):
		return "\"%s\"" % (self.text)

class TexPreprocessor(object):
	def __init__(self, texfilename):
		with open(texfilename) as f:
			self._text = f.read()
		self._words = None
		self._sentences = None

	def extract_words(self):
		pass


if __name__ == "__main__":
	# Simple test case
	text = _TextFragment("AaBbCcDdEe")
	text._offsetmap = [ [ 0, 0 ], [ 2, 10 ], [ 4, 20 ], [ 6, 30 ], [ 8, 40 ] ]
	assert(list(text) == [(0, 'A'), (1, 'a'), (10, 'B'), (11, 'b'), (20, 'C'), (21, 'c'), (30, 'D'), (31, 'd'), (40, 'E'), (41, 'e')])

	# Regular test case with removals within spans
	text = _TextFragment("Foo^^bar Moo^^koo Blah^^Blubb")
	text._offsetmap = [ [ 0, 0 ], [ 9, 100 ], [ 18, 200 ] ]
	assert(list(text) == [(0, 'F'), (1, 'o'), (2, 'o'), (3, '^'), (4, '^'), (5, 'b'), (6, 'a'), (7, 'r'), (8, ' '), (100, 'M'), (101, 'o'), (102, 'o'), (103, '^'), (104, '^'), (105, 'k'), (106, 'o'), (107, 'o'), (108, ' '), (200, 'B'), (201, 'l'), (202, 'a'), (203, 'h'), (204, '^'), (205, '^'), (206, 'B'), (207, 'l'), (208, 'u'), (209, 'b'), (210, 'b')])
	text.delete_span((3, 5))
	assert(list(text) == [(0, 'F'), (1, 'o'), (2, 'o'), (5, 'b'), (6, 'a'), (7, 'r'), (8, ' '), (100, 'M'), (101, 'o'), (102, 'o'), (103, '^'), (104, '^'), (105, 'k'), (106, 'o'), (107, 'o'), (108, ' '), (200, 'B'), (201, 'l'), (202, 'a'), (203, 'h'), (204, '^'), (205, '^'), (206, 'B'), (207, 'l'), (208, 'u'), (209, 'b'), (210, 'b')])
	text.delete_span((10, 12))
	assert(list(text) == [(0, 'F'), (1, 'o'), (2, 'o'), (5, 'b'), (6, 'a'), (7, 'r'), (8, ' '), (100, 'M'), (101, 'o'), (102, 'o'), (105, 'k'), (106, 'o'), (107, 'o'), (108, ' '), (200, 'B'), (201, 'l'), (202, 'a'), (203, 'h'), (204, '^'), (205, '^'), (206, 'B'), (207, 'l'), (208, 'u'), (209, 'b'), (210, 'b')])
	text.delete_span((18, 20))
	assert(list(text) == [(0, 'F'), (1, 'o'), (2, 'o'), (5, 'b'), (6, 'a'), (7, 'r'), (8, ' '), (100, 'M'), (101, 'o'), (102, 'o'), (105, 'k'), (106, 'o'), (107, 'o'), (108, ' '), (200, 'B'), (201, 'l'), (202, 'a'), (203, 'h'), (206, 'B'), (207, 'l'), (208, 'u'), (209, 'b'), (210, 'b')])

	# Test case with removal at the beginning
	text = _TextFragment("Foobar")
	assert(list(text) == [(0, 'F'), (1, 'o'), (2, 'o'), (3, 'b'), (4, 'a'), (5, 'r')] )
	text.delete_span((0, 3))
	assert(list(text) == [(3, 'b'), (4, 'a'), (5, 'r')] )

	# Test case with removal over multiple spans
	text = _TextFragment("FooXYZBar")
	text._offsetmap = [ [0, 0], [ 3, 100 ],[ 4, 200 ],[ 5, 300 ], [6, 1000] ]
	assert(list(text) == [(0, 'F'), (1, 'o'), (2, 'o'), (100, 'X'), (200, 'Y'), (300, 'Z'), (1000, 'B'), (1001, 'a'), (1002, 'r')])
	text.delete_span((3, 6))
	assert(list(text) == [(0, 'F'), (1, 'o'), (2, 'o'), (1000, 'B'), (1001, 'a'), (1002, 'r')])
	
	# Test case with removal over multiple spans not starting in one
	text = _TextFragment("FooBarKoo")
	text._offsetmap = [ [ 0, 0 ], [3, 100], [4, 200], [5, 300], [6, 1000] ]
	assert(list(text) == [(0, 'F'), (1, 'o'), (2, 'o'), (100, 'B'), (200, 'a'), (300, 'r'), (1000, 'K'), (1001, 'o'), (1002, 'o')])
	text.delete_span((1, 7))
	assert(text._offsetmap == [ [ 0, 0 ], [ 1, 1001 ] ])
	assert(list(text) == [(0, 'F'), (1001, 'o'), (1002, 'o')])

	# Number test
	text = _TextFragment("Numbers at eleven and another at 33 at at 42.")
	assert(text.translate_offset(text.text.index("33")) == 33)
	assert(text.translate_offset(text.text.index("42")) == 42)
	text.delete_regex("at ")
	assert(text.translate_offset(text.text.index("33")) == 33)
	assert(text.translate_offset(text.text.index("42")) == 42)
	
	# Remove long text
	def assert_integrity(t):
		assert(all(pos % 10 == int(char) for (pos, char) in t))
	text = _TextFragment("0123456789" * 3)
	print("X")
	text.delete_regex("012345")
	text.dump()
	print(text._offsetmap)
	assert_integrity(text)
	
	# Head remove test
	text = _TextFragment("0123456789" * 3)
	print("X")
	text.delete_regex("01234")
	text.dump()
	print(text._offsetmap)
	assert_integrity(text)

	# Multiple remove test
	text = _TextFragment("0123456789" * 10)	
	text.delete_regex("7")
	assert_integrity(text)
	text.delete_regex("2.4")
	assert_integrity(text)
	text.delete_regex("0")
	assert_integrity(text)



#	text.delete_regex("915")
#	assert_integrity(text)
#	text.delete_regex("15686")
#	assert_integrity(text)
	text.dump()
