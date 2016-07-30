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

import bisect
import collections

_LineColLocation = collections.namedtuple("LineColLocation", [ "lineno", "colno" ])

class LineMapper(object):
	def __init__(self, text):
		self._text = text
		lineno = 1
		self._offsets = [ (0, lineno) ]
		for (offset, char) in enumerate(self._text):
			if char == "\n":
				lineno += 1
				self._offsets.append((offset, lineno))

	def resolve(self, offset):
		searchpattern = (offset + 1, 0)
		index = bisect.bisect_left(self._offsets,  searchpattern) - 1
		if index < 0:
			index = 0
		(baseoffset, lineno) = self._offsets[index]
		if lineno == 1:
			# First line does not start with '\n'
			offset += 1
		result = _LineColLocation(lineno = lineno, colno = offset - baseoffset)
		return result


if __name__ == "__main__":
	lm = LineMapper("foobar\nbarfoo")
	for i in range(10):
		print(i, lm.resolve(i))
	assert(tuple(lm.resolve(0)) == (1, 1))
	assert(tuple(lm.resolve(5)) == (1, 6))
	assert(tuple(lm.resolve(6)) == (2, 0))
	assert(tuple(lm.resolve(7)) == (2, 1))
	assert(tuple(lm.resolve(10)) == (2, 4))

