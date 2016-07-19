import re
import urllib.parse
import collections

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
			titles_by_index[entry.index] = title
		
		# Remove exact matches first
		indices_by_title = collections.defaultdict(list)
		for (index, title) in titles_by_index.items():
			indices_by_title[title].append(index)

		return indices_by_title

class MiscTools(object):
	_ISBN13_RE = re.compile("\d{3}-\d-\d{3}-\d{5}-[0-9X]")
	_ISBN10_RE = re.compile("\d-\d{3}-\d{5}-[0-9X]")

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
