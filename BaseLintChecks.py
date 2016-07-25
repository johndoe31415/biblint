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

import collections
import os.path
from Ansi256 import Ansi256

class OffenseSource(object):
	def __init__(self, filename, lineno, colno, srctype, **kwargs):
		assert(srctype in [ "bib", "tex" ])
		self._filename = filename
		self._lineno = lineno
		self._colno = colno
		self._srctype = srctype
		self._bibentry = kwargs.get("bibentry")

	@property
	def filename(self):
		return self._filename

	@property
	def lineno(self):
		return self._lineno

	@property
	def colno(self):
		return self._colno

	@property
	def srctype(self):
		return self._srctype

	@property
	def bibentry(self):
		assert(self._srctype == "bib")
		return self._bibentry

	@classmethod
	def _from_bibentry(cls, entry, fieldname):
		return cls(filename = entry.filename, lineno = entry.lineof(fieldname), colno = 1, srctype = "bib", bibentry = entry)

	@classmethod
	def from_bibentries(cls, entries, fieldname = None):
		return [ cls._from_bibentry(entry = entry, fieldname = fieldname) for entry in entries ]

	@classmethod
	def from_bibentry(cls, entry, fieldname = None):
		return cls.from_bibentries([ entry ], fieldname = fieldname)

	def to_dict(self):
		data = {
			"filename":		self.filename,
			"lineno":		self.lineno,
			"colno":		self.colno,
			"srctype":		self.srctype,
			"specific":		{ },
		}
		if self.srctype == "bib":
			for field in [ "author", "title" ]:
				data["specific"][field] = self._bibentry.rawtext(field)
		return data

	def longstr(self):
		if self.srctype == "bib":
			return "%s:%d (<fg:cyan>%s<reset>): <fg:purple>%s<reset> - <fg:green>%s<reset>" % (os.path.basename(self.filename), self.lineno, self._bibentry.name, self._bibentry.rawtext("author"), self._bibentry.rawtext("title"))
		else:
			return str(self)

	def __str__(self):
		if self.srctype == "bib":
			return "%s:%d (%s)" % (os.path.basename(self.filename), self.lineno, self._bibentry.name)
		else:
			return "%s:%d:%d" % (os.path.basename(self.filename), self.lineno, self.colno)

class LintOffense(object):
	def __init__(self, lintclass, sources, description, **kwargs):
		assert(all(kwarg in set([ "uris", "expect_field", "order" ]) for kwarg in kwargs))
		self._lintclass = lintclass
		self._sources = sources
		self._description = description
		self._uris = kwargs.get("uris")
		self._expect_field = kwargs.get("expect_field")
		self._order = kwargs.get("order", 0)

	@property
	def bibsource(self):
		"""If a source is a bibentry, return that bibentry. Otherwise, reutrns
		None."""
		for source in self.sources:
			if source.srctype == "bib":
				return source.bibentry

	@property
	def sourcecnt(self):
		return len(self.sources)

	def getsource(self, index):
		return self._sources[index]

	@property
	def lintclass(self):
		return self._lintclass

	@property
	def sources(self):
		return self._sources

	@property
	def description(self):
		return self._description

	@property
	def uris(self):
		return self._uris

	@property
	def expect_field(self):
		return self._expect_field

	@property
	def order(self):
		return self._order

	@property
	def cmpkey(self):
		return (self._order, self._sources[0].filename, self._sources[0].lineno, self.sources[0].colno, self._lintclass.name)

	def short_dump(self, file):
		sources = ", ".join(str(source) for source in self._sources)
		text = "%s: %s" % (sources, self.description)
		if self.uris is not None:
			text += " %s" % (" / ".join(self.uris.values()))
		if self.expect_field is not None:
			text += " Expect: %s = {%s}," % (self.expect_field[0], self._expect_field[1])
		text += " [%s]" % (self._lintclass.name)
		print(text, file = file)

	def long_dump(self, file, use_ansi = True):
		ansi = Ansi256(strip_ansi = not use_ansi)
		offenses = "\n".join(source.longstr() for source in self._sources)
		print(ansi.format("<fg:brightred>%s<reset>" % (self._lintclass.name)), file = file)
		print(ansi.format(offenses), file = file)
		print(ansi.format("    <fg:orange>%s<reset>" % (self.description)), file = file)
		if self.uris is not None:
			for (name, uri) in self.uris.items():
				print(ansi.format("    <fg:cyan>%s<reset>: <fg:yellow>%s<reset>" % (name, uri)), file = file)
		if self.expect_field is not None:
			print(ansi.format("    Expect: <fg:yellow>%s = {%s},<reset>" % (self.expect_field[0], self._expect_field[1])), file = file)
		print(file = file)

	def to_dict(self):
		data = {
			"sources":			[ source.to_dict() for source in self._sources ],
			"class":			self.lintclass.name,
			"description":		self.description,
			"uris":				self._uris,
			"expect_field":		self.expect_field,
		}
		return data

	def print_vim_quickfix(self, f):
		for source in self.sources:
			msg = "%s [%s]" % (self.description, self._lintclass.name)
			if self.expect_field is not None:
				msg += " %s = {%s}," % (self.expect_field[0], self.expect_field[1])
			substitutions = {
				"filename":		source.filename,
				"linenumber":	source.lineno,
				"columnnumber":	source.colno,
				"errortype":	"E",
				"errornumber":	self.lintclass.name,
				"errormessage":	msg,
			}
			#print("%(filename)s>%(linenumber)d:%(columnnumber)d:%(errortype)s:%(errornumber)s:%(errormessage)s" % substitutions, file = f)
			print("%(filename)s:%(linenumber)d:%(columnnumber)d:%(errormessage)s" % substitutions, file = f)

	def __eq__(self, other):
		return self.cmpkey == other.cmpkey

	def __lt__(self, other):
		return self.cmpkey < other.cmpkey



class BibLintCheck(object):
	"""This is the class that one needs to override in order to provide another
	lint check of the bibliography."""
	name = None
	description = None
	linttype = "per_entry"

	def __init__(self, arguments, bibliography, citations):
		self._arguments = arguments
		self._bibliography = bibliography
		self._citations = citations
		assert(self.linttype in [ "per_entry", "once" ])

	@property
	def linttarget(self):
		return "bib"

	@property
	def args(self):
		return self._arguments

	@property
	def bibliography(self):
		return self._bibliography

	@property
	def citations(self):
		return self._citations

	def check_entry(self, entry):
		"""This is the hook that is called for 'per_entry' lint types.
		Intuitively, this is called for every bibliography entry exactly
		once."""
		raise Exception(NotImplemented)

	def check_all(self):
		"""This is the hook that is called for 'once' lint types.
		Unsurprisingly, it is only called once and needs to check the
		bibliography itself."""
		raise Exception(NotImplemented)


class TexLintCheck(object):
	"""This is the class that one needs to override in order to provide another
	lint check of the TeX files."""
	name = None
	description = None
	linttype = None

	def __init__(self, arguments, bibliography, citations):
		self._arguments = arguments
		self._bibliography = bibliography
		self._citations = citations
		assert(self._linttype in [ "per-word", "per-sentence", "per-texfile" ])

	@property
	def linttarget(self):
		return "tex"

	@property
	def args(self):
		return self._arguments

	@property
	def bibliography(self):
		return self._bibliography

	@property
	def citations(self):
		return self._citations

	def check_texfile(self, texdata):
		"""This is the hook that is called for each TeX file that was
		passed."""
		raise Exception(NotImplemented)


