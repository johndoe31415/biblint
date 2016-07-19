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
import sys
import collections

class BibEntry(object):
	_key_value_re = re.compile("^\s*(?P<key>[-_a-zA-Z0-9]+)\s*=\s*(?P<value>.*)")
	_parsed_part = collections.namedtuple("ParsedPart", [ "text", "quotelvl" ])
	_preferred_order = [
			"author", "title", "shorttitle", "editor",
			"series",
			"journal", "articleno", "issue", "volume", "numpages", "pages",
			"howpublished",
			"booktitle",
			"edition", "publisher", "address", "isbn", "issn",
			"school", "institution", "organization", "number", "location",
			"year", "month", "day", "doi", "url", "urldate", "note",
			"bibsource", "biburl",
			"bibdate", "timestamp", "added-at", "posted-at",
			"language", "keywords", "tags", "abstract",
			"ee", "masid", "acmid", "lccn",
			"priority",
			"cites", "citedby",
	]
	_preferred_order_set = set(_preferred_order)

	def __init__(self, index, entrytype, name, filename, lineno):
		self._index = index
		self._etype = entrytype
		self._name = name
		self._properties = { }
		self._fieldlines = { }
		self._filename = filename
		self._lineno = lineno
		self._last_key = None
		self._suppressions = { }

	def add_suppression(self, suppression):
		self._suppressions[suppression.suppress] = suppression
		return self

	@property
	def index(self):
		return self._index

	@property
	def filename(self):
		return self._filename

	@property
	def etype(self):
		return self._etype

	def lineof(self, fieldname):
		return self._fieldlines.get(fieldname, self._lineno)

	def parseline(self, line, lineno):
		line = line.rstrip("\r\n")
		result = self._key_value_re.match(line)
		if result:
			result = result.groupdict()
			key = result["key"].lower()
			self._last_key = key
			self._properties[key] = result["value"]
			self._fieldlines[key] = lineno
		else:
			self._properties[self._last_key] += " " + line.lstrip()

	@property
	def pretty_etype(self):
		return self._etype.lower()

	def _printkey(self, key, f):
		value = self._properties[key]
		print("	%-20s = %s" % (key, value), file = f)

	def pretty_print(self, f = None):
		if f is None:
			f = sys.stdout
		for suppression in sorted(self._suppressions.values()):
			if suppression.description is None:
				print("%% LINT %s" % (suppression.suppress), file = f)
			else:
				print("%% LINT %s %s" % (suppression.suppress, suppression.description), file = f)
		print("@%s{%s," % (self.pretty_etype, self._name), file = f)

		# Print preferred key/values first
		for key in self._preferred_order:
			if self.haskey(key):
				self._printkey(key, f)

		# Then the rest in alphabetical order
		for (key, value) in sorted(self._properties.items()):
			if key not in self._preferred_order_set:
				self._printkey(key, f)
		print("}", file = f)
		print(file = f)

	def parsetext(self, value):
		value = value.rstrip("\r\n\t ")
		if value.endswith(","):
			value = value[:-1]

		quotelvl = 0
		start_by_quot = False
		groups = [ ]
		for char in value:
			if char == "{":
				quotelvl += 1
				continue
			elif char == "}":
				quotelvl -= 1
			elif char == "\"" and (quotelvl == 0):
				quotelvl += 1
				start_by_quot = True
			elif char == "\"" and (quotelvl == 1) and (start_by_quot):
				quotelvl -= 1
				start_by_quot = False
			else:
				if (len(groups) == 0) or (groups[-1].quotelvl != quotelvl):
					groups.append(self._parsed_part(text = char, quotelvl = quotelvl))
				else:
					groups[-1] = self._parsed_part(text = groups[-1].text + char, quotelvl = quotelvl)
		return groups

	def parsefield(self, fieldname):
		parsedtext = self.parsetext(self[fieldname])
		return parsedtext

	def rawtext(self, fieldname):
		return "".join(field.text for field in self.parsefield(fieldname))

	@property
	def name(self):
		return self._name

	@property
	def identifier(self):
		return "%s %s (%s:%d)" % (self._etype, self._name, self._filename, self._lineno)

	def haskey(self, name):
		return name in self._properties

	def get(self, key, alternative = None):
		return self._properties.get(key, alternative)

	def softget(self, key):
		return self.get(key, "")

	def suppressed(self, check):
		return check in self._suppressions

	def __getitem__(self, key):
		return self._properties[key]

	def __str__(self):
		return self.identifier
