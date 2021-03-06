#
#	biblint - Static checking of BibTeX files to find errors or inconsistencies.
#	Copyright (C) 2016-2020 Johannes Bauer
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
import urllib.parse
import collections

class TexTools(object):
	def tex2unicode(text):
		text = text.replace(r"\'e", "é")
		text = text.replace(r"\'o", "ó")
		text = text.replace(r"\'i", "í")
		text = text.replace(r"\'E", "É")
		text = text.replace(r"\'O", "Ó")
		text = text.replace(r"\'I", "Í")
		text = text.replace(r"\"a", "ä")
		text = text.replace(r"\"o", "ö")
		text = text.replace(r"\"u", "ü")
		text = text.replace(r"\"A", "Ä")
		text = text.replace(r"\"O", "Ö")
		text = text.replace(r"\"U", "Ü")
		text = text.replace(r"\ss", "ß")
		text = text.replace(r"\cc", "ç")
		text = text.replace(r"\"y", "ÿ")
		return text

class BibEntryTools(object):
	def title_keywords_search(bibentry, urlencode = False):
		title = bibentry["title"]
		title = title.rstrip("},\"").lstrip("{\"")
		title = title.replace("{", "").replace("}", "")
		title = title.replace(":", "")
		title = title.split()
		title = [ word for word in title if len(word) > 3 ]
		title = title[:5]
		title = " ".join(title)
		if urlencode:
			title = urllib.parse.quote_plus(title)
		return title

	def probably_has_doi(bibentry):
		has_doi = bibentry.haskey("doi")
		has_doi = has_doi or (bibentry.haskey("ee") and ("doi" in bibentry["ee"]))
		has_doi = has_doi or (bibentry.haskey("url") and ("doi" in bibentry["url"]))
		return has_doi

	def expected_doi_url(bibentry):
		return "https://dx.doi.org/" + bibentry.rawtext("doi")

	def is_rfc_reference(bibentry):
		if bibentry.name.startswith("rfc") and bibentry.name[3:].isdigit():
			return int(bibentry.name[3:])

	def readable_title(bibentry):
		if not bibentry.haskey("title"):
			return None
		title = bibentry.rawtext("title")
		title = title.replace("\\enquote", "")
		title = title.replace("~", " ")
		title = title.replace("\\textnormal", "")
		return title


class BibliographyTools(object):
	def get_indices_by_title(bibliography):
		titles_by_index = { }
		for entry in bibliography:
			title = BibEntryTools.readable_title(entry)
			if title is not None:
				titles_by_index[entry.index] = title

		# Remove exact matches first
		indices_by_title = collections.defaultdict(list)
		for (index, title) in titles_by_index.items():
			indices_by_title[title].append(index)

		return indices_by_title

class MiscTools(object):
	_ISBN13_RE = re.compile("\d{3}-\d-\d{3}-\d{5}-[0-9X]")
	_ISBN10_RE = re.compile("\d-\d{3}-\d{5}-[0-9X]")
	_ABBRV_RE = re.compile("([A-Z][0-9a-z]*[A-Z]+[A-Za-z0-9]*)")

	@classmethod
	def isbn_format_correct(cls, isbn):
		result = cls._ISBN13_RE.fullmatch(isbn)
		if result is not None:
			return True

		result = cls._ISBN10_RE.fullmatch(isbn)
		if result is not None:
			return True

		return False

	def isbn_calc_checksum_digit(isbn):
		assert(len(isbn) in [ 9, 12 ])
		if len(isbn) == 9:
			check = sum(pos * value for (pos, value) in enumerate(isbn, 1)) % 11
		else:
			weights = [ 1, 3 ] * 6
			check = sum(weight * value for (weight, value) in zip(weights, isbn)) % 10
			check = (10 - check) % 10

		if check == 10:
			check = "X"
		else:
			check = str(check)
		return check

	@classmethod
	def isbn_checksum_correct(cls, isbn):
		isbn = isbn.replace(" ", "").replace("-", "").lower()
		allowed_characters = set("0123456789x")
		if len(set(isbn) - allowed_characters) > 0:
			# Illegal characters in ISBN
			return False

		if len(isbn) not in [ 10, 13 ]:
			# Invalid length
			return False

		int_isbn = [ int(x) if x.isdigit() else 10 for x in isbn ]
		wanted_checksum_char = cls.isbn_calc_checksum_digit(int_isbn[:-1])
		return wanted_checksum_char == isbn[-1]

	@classmethod
	def convert_isbn10_to_isbn13(cls, isbn):
		assert(cls.isbn_format_correct(isbn))
		assert(cls.isbn_checksum_correct(isbn))
		assert(len(isbn) == 13)

		isbn = isbn.replace("-", "").replace(" ", "")
		int_isbn = [ 9, 7, 8 ] + [ int(x) if x.isdigit() else 10 for x in isbn ][:-1]
		checksum = cls.isbn_calc_checksum_digit(int_isbn)

		isbn = "".join(str(x) for x in int_isbn) + checksum

		return isbn[0 : 3] + "-" + isbn[3] + "-" + isbn[4 : 7] + "-" + isbn[7 : 12] + "-" + isbn[12]

	@classmethod
	def is_abbreviation(cls, text):
		return cls._ABBRV_RE.fullmatch(text) is not None

	@classmethod
	def contains_abbreviation(cls, text):
		return cls._ABBRV_RE.search(text)

