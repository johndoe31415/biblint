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
import collections

class Citations(object):
	_CITE_RE = re.compile(r"\\(no)?[Cc]ite[tp]?{(?P<content>[^}]+)}")

	_Citation = collections.namedtuple("Citation", [ "filename", "lineno", "colno", "citation" ])
	def __init__(self):
		self._citations = collections.defaultdict(list)

	def _parseline(self, lineno, filename, line):
		for result in self._CITE_RE.finditer(line):
			citations = result.groupdict()["content"]
			colno = result.span()[0] + 1
			for citation in citations.split(","):
				citation = citation.strip(" ")
				self._citations[citation].append(self._Citation(filename = filename, lineno = lineno, colno = colno, citation = citation))

	def read_from_file(self, filename):
		with open(filename) as f:
			for (lineno, line) in enumerate(f, 1):
				line = line.rstrip("\r\n")
				self._parseline(lineno, filename, line)

	def getbyname(self, name):
		yield from self._citations[name]

	def __iter__(self):
		return iter(self._citations)

	def __len__(self):
		return len(self._citations)
