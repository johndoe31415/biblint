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
import re
try:
	import fuzzywuzzy.process
except ImportError:
	fuzzywuzzy = None
from Tools import BibEntryTools, BibliographyTools, MiscTools

_ABBRV_RE = re.compile("([A-Z][0-9a-z]*[A-Z]+[A-Za-z0-9]*)")

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
			return "%s:%d (%s): %s - %s" % (os.path.basename(self.filename), self.lineno, self._bibentry.name, self._bibentry.rawtext("author"), self._bibentry.rawtext("title"))
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

	def long_dump(self, file):
		offenses = "\n".join(source.longstr() for source in self._sources)
		print(self._lintclass.name, file = file)
		print(offenses, file = file)
		print("    %s" % (self.description), file = file)
		if self.uris is not None:
			for (name, uri) in self.uris.items():
				print("    %s: %s" % (name, uri), file = file)
		if self.expect_field is not None:
			print("    Expect: %s = {%s}," % (self.expect_field[0], self._expect_field[1]), file = file)
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
	name = None
	description = None
	linttype = "per_entry"

	def __init__(self, arguments, bibliography, citations):
		self._arguments = arguments
		self._bibliography = bibliography
		self._citations = citations

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
		raise Exception(NotImplemented)

	def check_all(self):
		raise Exception(NotImplemented)

class _CheckDuplicateEntriesByName(BibLintCheck):
	name = "duplicate-entries-by-name"
	linttype = "once"
	description = """
	Finds BibTeX entries which have the same cite name. This can lead to unexpected results in document and should usually not happen."""
	def check_all(self):
		multiples = [ entries for entries in self.bibliography.grouped_entries_by_name.values() if len(entries) > 1 ]
		for entries in multiples:
			name = entries[0].name
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentries(entries), description = "%d entries for entry with name \"%s\"." % (len(entries), name))

class _CheckEntriesWithOverquotedMonth(BibLintCheck):
	name = "misformatted-month"
	description = """
	Shows entries with a misformatted month. Months are expected to be in unquoted form and use three-letter lowercase English month abbreviations (e.g. month = jan, ..., month = dec). This will show overquoted months (i.e. {mar} or {{mar}}) which would show up wrong in the final document. It will also reject days of the week which are encoded in the month field.
	"""
	_expect_months = set([ "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec" ])
	def check_entry(self, entry):
		if not entry.haskey("month"):
			return
		month = entry.parsefield("month")
		if len(month) != 1:
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "month"), description = "Month has unexpected multipart field (expect only one).")

		month = month[0]
		if month.text not in self._expect_months:
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "month"), description = "Unrecognized month \"%s\", expect lowercase unquoted three-letter abbreviation." % (month.text))
		elif month.quotelvl != 0:
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "month"), description = "Month was quoted when unquoted expected: %s" % (month.text))

class _CheckEntriesWithIllegalCharacters(BibLintCheck):
	name = "entries-with-illegal-chars"
	description = """
	Finds special characters in title or booktitle such as typographic quotation marks or typographic dashes which will frequently lead to problems during typesetting.
	"""
	def check_entry(self, entry):
		check_keys = [ "title", "booktitle" ]
		allowed_chars = set(" 0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~")
		for key in check_keys:
			if not entry.haskey(key):
				continue
			value = entry[key]
			used_chars = set(value)
			illegal_chars = used_chars - allowed_chars
			if len(illegal_chars) > 0:
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = key), description = "Entry has illegal chars '%s' in field '%s'." % ("".join(sorted(illegal_chars)), key))

class _CheckUnquotedAbbreviations(BibLintCheck):
	name = "entries-with-unquoted-abbreviations"
	description = """
	Finds underquoted abbreviations in the title. For example, if the title was set to

	title = {How to use AES}

	this could become the unintended

	How to use aes

	if the abbreviation AES was not enclosed by curly braces.
	"""
	def check_entry(self, entry):
		for field in [ "title" ]:
			parsed_title = entry.parsefield(field)
			unquoted = [ part.text for part in parsed_title if part.quotelvl <= 1 ]
			for part in unquoted:
				result = _ABBRV_RE.search(part)
				if result is not None:
					abbreviation = result.groups(0)[0]
					yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = field), description = "Unquoted abbreviation '%s' in %s." % (abbreviation, field))
					break

class _CheckUnquotedNames(BibLintCheck):
	name = "entries-with-unquoted-names"
	description = """
	Finds unquoted names in the title. For example, a BibTeX entry that had

	title = {How to use the	Internet}

	could become the unintended

	How to use the internet

	if the word "Internet" was not enclosed by curly braces. This only works for a certain hardcoded list of names right now and will probably only fit your purpose if you extend the list manually by editing the code.
	"""
	def check_entry(self, entry):
		words = [ "keccak", "internet", "fourier", "atmel", "galois", "fibonacci", "stmicroelectronics", "intel", "micron" ]
		for field in [ "title" ]:
			parsed_title = entry.parsefield(field)
			for word in words:
				unquoted = [ part.text for part in parsed_title if part.quotelvl <= 1 ]
				for part in unquoted:
					if word in part.lower():
						yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = field), description = "Unquoted name '%s' in %s." % (word, field))
						break

class _CheckOverquotedAbbreviations(BibLintCheck):
	name = "entries-with-overquoted-title"
	description = """
	Finds overquoted titles. For example, for

	title = {{How To Use The Internet}}

	it would advise you that there are multiple words in one huge curly brace. This might be unintentional.
	"""
	def check_entry(self, entry):
		parsed_title = entry.parsefield("title")
		quoted = [ part.text for part in parsed_title if part.quotelvl > 1 ]
		for part in quoted:
			if len(part.split()) >= 3:
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "title"), description = "Overquoted title.")
				break


class _CheckLocalCopies(BibLintCheck):
	name = "check-local-copies"
	description = """
	Checks if the referred files are present as local files. It checks for files in the localdir command line argument directory and checks for both .pdf and .txt files in that directory. It will give you a Google search links with arguments that you can use to search for a PDF.
	"""
	def check_entry(self, entry):
		extensions = [ ".pdf", ".txt" ]
		basefile = entry.name.replace(":", "_").replace("/", "_")
		have_file = False
		for extension in extensions:
			expect_filename = self.args.localdir + "/%s%s" % (basefile, extension)
			if os.path.isfile(expect_filename):
				return

		search_url = "https://scholar.google.de/scholar?hl=de&q=%s&btnG=&lr=" % (BibEntryTools.title_keywords_search(entry, urlencode = True))
		yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry), description = "Missing local bibliography file.", uris = { "Google Scholar": search_url })


class _CheckUniformDOIUrl(BibLintCheck):
	name = "check-uniform-doi-url"
	description = """
	For entries which have a DOI present, checks that the URL points to

	https://dx.doi.org/${doi}

	An exception are RFCs, which should also have a DOI but a different URL. For RFCs, it expects

	https://tools.ietf.org/rfc/rfc${no}.txt

	to be set as the URL. RFCs are detected by having a citation name of rfc(\d+). This check does not issue any warnings if no DOI is present at all.
	"""
	def check_entry(self, entry):
		if entry.haskey("doi"):
			# Definitely has DOI set
			expect_url = BibEntryTools.expected_doi_url(entry)

			# Make an exception for RFCs however
			rfc_no = BibEntryTools.is_rfc_reference(entry)
			if rfc_no is not None:
				# This is a RFC reference
				expect_url = "https://tools.ietf.org/rfc/rfc%d.txt" % (rfc_no)

			if entry.haskey("url"):
				current_url = entry.rawtext("url")
				if current_url != expect_url:
					yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "url"), description = "DOI present, but URL does not point to it.", expect_field = ("url", expect_url))
			else:
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry), description = "DOI present, but no URL present at all.", expect_field = ("url", expect_url))


class _CheckMissingDOIUrl(BibLintCheck):
	name = "check-missing-doi"
	description = """
	Checks for missing DOIs and tries to heuristically find out if it's a IEEE, Springer, ACM or Elsevier publication. For these publications, it directly shows a clickable search link that should lead to the paper so you can easily find the DOI. Also detects DOIs that are potentially present in other metadata fields (e.g. "ee") and advises accordingly.
	"""
	def check_entry(self, entry):
		if not entry.haskey("doi"):
			org_string = " ".join([ entry.softget("jornal"), entry.softget("organization"), entry.softget("publisher"), entry.softget("booktitle") ])
			org_string = org_string.lower()
			known_organizations = {
				"ieee":		("IEEE", "http://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=%s"),
				"springer":	("Springer", "http://link.springer.com/search?query=%s"),
				"acm":		("ACM", "http://dl.acm.org/results.cfm?query=%s&Go.x=0&Go.y=0"),
				"elsevier":	("ACM", "https://www.elsevier.com/search-results?query=%s&labels=all"),
			}
			orga = None
			for (pattern, (organame, searchtemplate)) in known_organizations.items():
				if pattern in org_string:
					orga = pattern
					break

			if BibEntryTools.probably_has_doi(entry):
				# Probably has DOI set
				text = "DOI probably present in metadata, but DOI field not set."
			else:
				text = "No DOI present anywhere in metadata."

			if orga is not None:
				(organame, searchtemplate) = known_organizations[orga]
				url_title = BibEntryTools.title_keywords_search(entry, urlencode = True)
				search_url = {
					organame + " search": searchtemplate % url_title
				}
				text += " Possible %s publication should have DOI." % (organame)
			else:
				search_url = None

			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry), description = text, uris = search_url)

class _CheckRFCDOIs(BibLintCheck):
	name = "check-rfc-dois"
	description = """
	Checks for RFCs that the DOIs are in the appropriate format as specified by RFC 7669 (DOI 10.17487/rfc7669).
	"""
	def check_entry(self, entry):
		rfc_no = BibEntryTools.is_rfc_reference(entry)
		if rfc_no is not None:
			# This is a RFC reference
			expect_doi = "10.17487/rfc%d" % (rfc_no)
			if entry.haskey("doi"):
				if entry.rawtext("doi") != expect_doi:
					yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "doi"), expect_field = ("doi", expect_doi), description = "Recognized an RFC, but DOI was not the expected %s." % (expect_doi))
			else:
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "doi"), expect_field = ("doi", expect_doi), description = "Recognized an RFC, DOI is not set to %s, however." % (expect_doi))

class _CheckIdenticalTitles(BibLintCheck):
	name = "check-identical-titles"
	description = """
	Checks for two titles which are exactly identical for different bibliography entries (possible duplicate under two different citation names).
	"""
	linttype = "once"
	def check_all(self):
		indices_by_title = BibliographyTools.get_indices_by_title(self.bibliography)

		exact_duplicates = { title: indices for (title, indices) in indices_by_title.items() if len(indices) > 1}
		for (title, indices) in exact_duplicates.items():
			entries = [ self.bibliography.getbyindex(index) for index in indices ]
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentries(entries, fieldname = "title"), description = "Exact title matches, possible duplicate.")


if fuzzywuzzy is not None:
	class _CheckSimilarTitles(BibLintCheck):
		name = "check-similar-titles"
		description = """
		Checks for two titles which are approximately equal for two publications. This uses fuzzy stirng comparison and is relatively slow; it also only works if the fuzzywuzzy Python package is installed.
		"""
		linttype = "once"
		def check_all(self):
			indices_by_title = BibliographyTools.get_indices_by_title(self.bibliography)
			compare_pool = set(indices_by_title)
			while len(compare_pool) >= 2:
				next_title = compare_pool.pop()

				similar = fuzzywuzzy.process.extractBests(next_title, compare_pool, score_cutoff = 90, limit = 10)
				indices = [ indices_by_title[title] for (title, score) in similar ]

				indices.append(indices_by_title[next_title])

				indices = sorted([ item for sublist in indices for item in sublist ])
				if len(indices) > 1:
					entries = [ self.bibliography.getbyindex(index) for index in indices ]
					yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentries(entries, fieldname = "title"), description = "Closely similar title matches, possible duplicates.")


class _CheckISBN(BibLintCheck):
	name = "check-isbn"
	description = """
	Checks that the ISBN-10 or ISBN-13 checksum is correct. Checks that the format is either n-nnn-nnnnn-n (for ISBN-10) or nnn-n-nnn-nnnnn-n (for ISBN-13). Also suggests to convert ISBN-10 to ISBN-13 and recalculates the proper ISBN-13 checksum for the converted value.
	"""
	def check_entry(self, entry):
		if not entry.haskey("isbn"):
			return
		isbn = entry.rawtext("isbn")

		format_correct = MiscTools.isbn_format_correct(isbn)
		if not format_correct:
			isbn_len = len(isbn.replace("-", ""))
			if isbn_len == 13:
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "isbn"), description = "ISBN-13 format wrong. Should be nnn-n-nnn-nnnnn-n")
			elif isbn_len == 10:
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "isbn"), description = "ISBN-10 format wrong. Should be n-nnn-nnnnn-n")
			else:
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "isbn"), description = "ISBN format unrecognized.")

		checksum_correct = MiscTools.isbn_checksum_correct(isbn)
		if not checksum_correct:
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "isbn"), description = "Invalid ISBN, checksum is wrong.")

		if format_correct and checksum_correct and len(isbn) == 13:
			# ISBN-10 conversion
			new_isbn = MiscTools.convert_isbn10_to_isbn13(isbn)
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "isbn"), description = "Old ISBN-10, suggest converting to new ISBN-13 form: %s" % (new_isbn))


class _CheckPresentFields(BibLintCheck):
	name = "check-present-fields"
	description = """
	Checks that certain fields are present for certain types of citations. For example, checks that an "article" has also a "journal" set and so on.
	"""
	def check_entry(self, entry):
		expect_all = set(["title", "author", "year" ])
		expect_specific = {
			"inproceedings":	set([ "booktitle", "publisher", "doi" ]),
			"incollection":		set([ "booktitle", "publisher", "doi" ]),
			"techreport":		set([ "number", "institution" ]),
			"book":				set([ "publisher", "isbn" ]),
			"article":			set([ "journal", "pages" ]),
			"manual":			set(),
			"misc":				set(),
			"phdthesis":		set(),
		}

		expect = expect_all
		expect |= expect_specific.get(entry.etype.lower(), set())
		if entry.etype.lower() not in expect_specific:
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry), description = "Unknown entry type %s." % (entry.pretty_etype))

		for fieldname in expect:
			if not entry.haskey(fieldname):
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry), description = "Entry with type %s is supposed to have field %s, but doesn't." % (entry.pretty_etype, fieldname))


class _CheckUncitedCitations(BibLintCheck):
	name = "uncited-citations"
	linttype = "once"
	description = """
	When TeX files are given, this check will determine if there are citations in the BibTeX which are never cited from the TeX."""
	def check_all(self):
		if self.citations is None:
			# No TeX file
			return

		all_bibentries = set(bibentry.name for bibentry in self.bibliography)
		uncited_bibentries = all_bibentries - set(self.citations)
		for entry_name in uncited_bibentries:
			entries = self.bibliography.getbyname(entry_name)
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentries(entries), description = "BibTeX entry never cited from TeX file.")


class _CheckUndefinedCitations(BibLintCheck):
	name = "undefined-citations"
	linttype = "once"
	description = """
	When TeX files are given, this check will determine if there are undefined citations in the TeX which never appear in the BibTeX."""
	def check_all(self):
		if self.citations is None:
			# No TeX file
			return

		undefined_citation_names = set(self.citations) - set(bibentry.name for bibentry in self.bibliography)
		for undefined_citation_name in undefined_citation_names:
			for citation in self.citations.getbyname(undefined_citation_name):
				source = OffenseSource(filename = citation.filename, lineno = citation.lineno, colno = citation.colno, srctype = "tex")
				yield LintOffense(lintclass = self.__class__, sources = [ source ], description = "Citation entry \"%s\" does not appear in BibTeX source." % (undefined_citation_name), order = -1)

class _CheckNameConsistency(BibLintCheck):
	name = "check-name-consistency"
	description = """
	Checks that author names are consistently written in terms of abbreviating their last names. For example, "F. Bar and M. Koo" is okay, "Foo Bar and Moo Koo" as well, but the mixing, i.e. "F. Bar and Moo Koo" is raised as an error.
	"""
	def check_entry(self, entry):
		names = list(entry.parsenames("author"))
		abbreviated = [ ("." in name.firstname) or len(name.firstname) == 1 for name in names ]
		if len(set(abbreviated)) > 1:
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "author"), description = "Entry has inconsistent abbreviation of first names.")

class _CheckFullFirstnames(BibLintCheck):
	name = "check-full-first-names"
	description = """
	Checks that author first names are spelled out in full (i.e. not abbreviated). An exception to this are RFCs, where first names are abbreviated.
	"""
	def check_entry(self, entry):
		if entry.name.startswith("rfc"):
			# Ignore RFCs from this check
			return
		names = list(entry.parsenames("author"))
		abbreviated = [ ("." in name.firstname) or len(name.firstname) == 1 for name in names ]
		abbreviated = set(abbreviated)
		if True in abbreviated:
			yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_bibentry(entry, fieldname = "author"), description = "Entry has abbreviated first names of authors.")


known_lint_checks = [ ]
for (lint_class_name, lint_class) in list(globals().items()):
	if not isinstance(lint_class, type):
		continue
	if lint_class.__mro__[1] == BibLintCheck:
		known_lint_checks.append(lint_class)
_names = set(check.name for check in known_lint_checks)
if len(_names) != len(known_lint_checks):
	raise Exception("Lint checks do not have unique name.")
known_lint_checks = { check.name: check for check in known_lint_checks }

