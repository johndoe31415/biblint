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

class TextFragmentTracker(object):
	"""Memorizes original offsets in modified pieces of text. This is useful
	because it allows us to pre-process the given TeX files (e.g., remove
	\emph{foo} fragments and replace them just by "foo" in order to make
	grammatical analysis easier/possible. However, we want to track the
	original positions in the file so we can later on -- once we find
	lint-worthy offenses, pinpoint their line/column number."""

	_debug = False

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
		"""Deletes a span from the text."""

		# Assign some helper variables first
		(span_from, span_to) = span
		length = span_to - span_from
		if __debug__ and self._debug:
			print("Removing span [ %d; %d ] length %d" % (span_from, span_to, length))

		# Remove the span in the actual text
		removed_text = self._text[span_from : span_to]
		if __debug__ and self._debug:
			print("Removed: '%s'" % (removed_text))
		self._text = self._text[ : span_from] + self._text[span_to : ]
		if __debug__ and self._debug:
			print("Remaining: '%s'" % (self._text))

		# Then find out the current translated offset
		(index_from, translated_from) = self.translate_full_offset(span_from)
		(index_to, translated_to) = self.translate_full_offset(span_to)
		if __debug__ and self._debug:
			print("Previously: offset %d is idx %d-%d (%s - %s), translated_offset end = %d" % (span_to, index_from, index_to, self._offsetmap[index_from], self._offsetmap[index_to], translated_to))

		# Remove old spans first
		if __debug__ and self._debug:
			print("Remove span PRE ", self._offsetmap)
		self._offsetmap = self._offsetmap[ : index_from + 1 ] + self._offsetmap[index_to + 1 : ]
		if __debug__ and self._debug:
			print("Remove span POST", self._offsetmap)

		# Then insert new one
		insert_index = index_from + 1
		new_element = [ span_from, translated_to ]
		if __debug__ and self._debug:
			print("New element: %s" % (new_element))

		if self._offsetmap[index_from][0] == new_element[0]:
			if __debug__ and self._debug:
				old_element = self._offsetmap[index_from]
				print("Updating index of element at %d: %s -> %s" % (insert_index, old_element, new_element))
			self._offsetmap[index_from] = new_element
			start_traversal_index = insert_index
		else:
			if __debug__ and self._debug:
				print("Inserting new element at %d: %s" % (insert_index, new_element))
			self._offsetmap.insert(insert_index, new_element)
			start_traversal_index = insert_index + 1

		for i in range(start_traversal_index, len(self._offsetmap)):
			self._offsetmap[i][0] -= length

		if __debug__ and self._debug:
			print("After linear traversal starting from %d: %s" % (start_traversal_index, self._offsetmap))

		if __debug__ and self._debug:
			# Only during debugging, check list after every modification
			self._assert_offsetmap_integrity()
			print()

	def insert_at(self, pos, text):
		if __debug__ and self._debug:
			print("Inserting at %d: '%s'" % (pos, text))
		length = len(text)
		if length == 0:
			return

		# Modify the text internally
		self._text = self._text[ : pos] + text + self._text[pos : ]

		(index, translated) = self.translate_full_offset(pos + length)
		for i in range(index, len(self._offsetmap)):
			self._offsetmap[i][0] += length
		
		if __debug__ and self._debug:
			# Only during debugging, check list after every modification
			self._assert_offsetmap_integrity()
			print()

	def replace_span(self, span, replacement):
		"""Deletes a span from the text and replaces it by the given
		replacement string."""
		self.delete_span(span)
		self.insert_at(span[0], replacement)

	@staticmethod
	def _mkregex(regex):
		if isinstance(regex, str):
			return re.compile(regex)
		else:
			return regex

	@staticmethod
	def _evalpattern(occurence, replacement):
		if isinstance(replacement, str):
			return replacement
		else:
			return replacement(occurence)

	def	replace_regex(self, regex, replacement):
		"""Searches the text for a given regex (can also be a string, will then
		be compiled on-the-fly) and replaces every occurence by the given
		replacement (can be a lambda which is passed the regex match or a
		static string as well.)"""
		regex = self._mkregex(regex)
		replacements = [ ]
		for occurence in regex.finditer(self.text):
			replpattern = self._evalpattern(occurence, replacement)
			replacements.append((occurence.span(), replpattern))
		for (span, replpattern) in reversed(replacements):
			self.replace_span(span, replpattern)

	def delete_regex(self, regex, delete_spans = None):
		"""Deletes the given regex from the text. The optional delete_spans
		argument can be specified and needs to contain a number of sub-span
		indicies which are to be deleted. For example, if you delete
		(.*)foobar(A+) and pass delete_spans = [ 2 ], only the (A+) will be
		deleted from text."""
		if delete_spans is None:
			delete_spans = [ 0 ]
		regex = self._mkregex(regex)
		deletions = [ ]
		for occurence in regex.finditer(self.text):
			for delspan in delete_spans:
				deletions.append(occurence.span(delspan))
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
		"""Translates an offset within the text into its original location offset."""
		return self.translate_full_offset(qry_offset)[1]

	def dump(self):
		for (offset, char) in enumerate(self.text):
			(index, xoffset) = self.translate_full_offset(offset)
			print("%2d %2d %3d %s" % (offset, index, xoffset, char))

	def __len__(self):
		return len(self.text)

	def __iter__(self):
		for (offset, pos) in enumerate(self.text):
			yield (self.translate_offset(offset), pos)

	def __str__(self):
		return "\"%s\"" % (self.text)

