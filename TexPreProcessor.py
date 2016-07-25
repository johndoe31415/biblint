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

class _TextFragment(object):
	def __init__(self, text):
		self._text = text
		self._offsetmap = [ [ 0, 0 ] ]

	@property
	def text(self):
		return self._text

	def delete_span(self, span):
		(span_from, span_to) = span
		self._text = self._text[ : span_from] + self._text[span_to : ]

		translated_from = self.translate_offset(span_from)
		increase = span_to - span_from
		if translated_from not in self._offsetmap:
			self._offsetmap[translated_from] = translated_from + increase
#		for (src_offset, dst_offset) in self._offsetmap.items():
#			if src_offset > span_from:
#				self._offsetmap[src_offset] += increase

	def delete_regex(self, regex):
		regex = re.compile(regex)
		deletions = [ ]
		for deletion in regex.finditer(self.text):
			deletions.append(deletion.span())
		for span in reversed(deletions):
			self.delete_span(span)
			break

	def translate_offset(self, qry_offset):
		index = bisect.bisect_left(self._offsetmap, [ qry_offset, 0 ])
		span = self._offsetmap[index]
		distance = span[1] - span[0]
		return qry_offset + distance
		print(index)

		mapped_offset = 0
		for (src_offset, dst_offset) in sorted(self._offsetmap.items()):
			if qry_offset >= src_offset:
				mapped_offset = dst_offset - src_offset
			else:
				break
		return qry_offset + mapped_offset

	def dump(self):
		for (offset, char) in enumerate(self.text):
			print("%2d %s" % (self.translate_offset(offset), char))

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
#	with open("test.tex") as f:
#		text = f.read()

	text = _TextFragment("Numbers at eleven and another at 33 at at 42.")
	text.dump()
	print("-" * 120)
	for i in range(4):
		text.delete_regex("at ")
		text.dump()
		print(text._offsetmap)
		print()


