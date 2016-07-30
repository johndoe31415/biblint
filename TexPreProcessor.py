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
#		print("Removing span [ %d; %d ] length %d" % (span_from, span_to, length))

		# Remove the span in the actual text
		removed_text = self._text[span_from : span_to]
#		print("Removed: '%s'" % (removed_text))
		self._text = self._text[ : span_from] + self._text[span_to : ]

		# Then find out the current translated offset
		(index_from, translated_from) = self.translate_full_offset(span_from)
		(index_to, translated_to) = self.translate_full_offset(span_to)
#		print("Previously: offset %d is idx %d-%d (%s - %s), translated_offset end = %d" % (span_to, index_from, index_to, self._offsetmap[index_from], self._offsetmap[index_to], translated_to))

		# Remove old spans first
#		print("PRE ", self._offsetmap)
		self._offsetmap = self._offsetmap[ : index_from + 1 ] + self._offsetmap[index_to + 1 : ]
#		print("POST", self._offsetmap)

		# Then insert new one
		insert_index = index_from + 1
		new_element = [ span_from, translated_to ]
#		print("New element: %s" % (new_element))

		if self._offsetmap[index_from][0] == new_element[0]:
#			old_element = self._offsetmap[index_from]
#			print("Updating index of element at %d: %s -> %s" % (insert_index, old_element, new_element))
			self._offsetmap[index_from] = new_element
		else:
#			print("Inserting new element at %d: %s" % (insert_index, new_element))
			self._offsetmap.insert(insert_index, new_element)

		for i in range(insert_index + 1, len(self._offsetmap)):
			self._offsetmap[i][0] -= length

		# Only during debugging, check list after every modification
#		self._assert_offsetmap_integrity()
#		print()

	def replace_span(self, span, replacement):
		self.delete_span(span)
		(span_from, span_to) = span
		self._text = self._text[ : span_from] + replacement + self._text[span_from : ]


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
		regex = self._mkregex(regex)
		replacements = [ ]
		for occurence in regex.finditer(self.text):
			replpattern = self._evalpattern(occurence, replacement)
			replacements.append((occurence.span(), replpattern))
		for (span, replpattern) in reversed(replacements):
			self.replace_span(span, replpattern)

	def delete_regex(self, regex, delete_spans = None):
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

class TexPreprocessor(object):
	# These are removed completely
	_REMOVE_COMPLETELY_ENVIRONMENTS = ( "listing", "figure", "table", "equation" )

	# Static search/replace
	_STATIC_REPLACEMENTS = (
		(r"\\us", "µs"),
		(r"\\cgd", "CGD"),
		(r"\\cgs", "CGS"),
		(r"\\vdd", "Vdd"),
		(r"\\Rdson", "Rdson"),
		(r"\\rds", "Rds"),
		(r"\\vil", "VIL"),
		(r"\\vih", "VIH"),
		(r"\\ohm", "Ohm"),
		(r"\\ldots", "..."),
	)

	# Strip these commands and only take their inner values
	_STRIP_NAMES = (
		"emph",
		"texttt",
		"textbf",
		"textnormal",
		"mbox",
		"url",
		"footnote",
		"opcode",
		"hex",
		"register",
	)

	# Enclose these by brackets
	_HEADINGS = (
		"chapter",
		"section",
		"subsection",
	)
		
	# Regex to detect a word
	_WORD_RE = re.compile("[^ \n]+")

	# Words that do not conclude a sentence
	_NO_END_OF_SENTENCE = re.compile(r"\(?(Sect|Tab|List|i\.e|e\.g|Fig)[\.:;]")

	def __init__(self, texfilename):
		self._texfilename = texfilename
		with open(texfilename) as f:
			self._text = f.read()
		self._text = _TextFragment(self._text)
		self._words = [ ]
		self._sentences = [ ]
		self._raw_words = [ ]
		self._remove_tex_code()
		self._extract_words()
		self._extract_sentences()
		self._extract_raw_words()

	@property
	def text(self):
		return self._text

	def _remove_tex_code(self):
		# Remove comments
		self._text.delete_regex(r"[^\\](%.*[^\n])", delete_spans = [ 1 ])

		# Then remove listings, figures and tables 
		for name in self._REMOVE_COMPLETELY_ENVIRONMENTS:
			regex = re.compile(r"\\begin{%s\*?}.*?\\end{%s\*?}" % (name, name), flags = re.DOTALL | re.MULTILINE)
			self._text.replace_regex(regex, "<Removed %s>" % (name))

		# Completely remove some commands including their arguments
		for name in [ "label", "selectlanguage", "nocite", "todo" ]:
			self._text.delete_regex(r"\\%s{[^}]*}" % (name))

		# Remove enquoted quotations
		self._text.replace_regex(r"\\enquote{([^}]*)}", "\"\\1\"")

		# Strip certain items
		for name in self._STRIP_NAMES:
			self._text.replace_regex(r"\\%s{([^}]*)}" % (name), lambda o: o.group(1))

		# Same for these, but with braces
		for name in self._HEADINGS:
			self._text.replace_regex(r"\\%s{([^}]*)}" % (name), lambda o: "<" + o.group(1) + ">")

		# Replace quotation marks
		self._text.replace_regex(r"(``|'')", "\"")

		# Replace citet quotations
		self._text.replace_regex(r"\\[cC]itet{[^}]*}", "John Doe and Jane Doe")

		# Replace citep quotations at end of sentence
		# TODO?
#		regex = re.compile(r"~\\citep{[^}]*}\.")
#		tex = regex.sub(".", tex)

		# Replace citep quotations
		self._text.replace_regex(r"\\citep{[^}]*}", "[Jane Doe, 2016]")

		# Replace references
		self._text.replace_regex(r"\\ref{[^}]*}", "1.2.3")

		# Replace non breaking spaces
		self._text.replace_regex(r"~", " ")

		# Replace certain delimiters
		self._text.delete_regex(r"\\(begin|end){(itemize|enumerate|landscape|abstract)}")

		# Enumerate/itemize
		self._text.replace_regex(r"\\item", "  *")

		# Replace escaped chacters
		self._text.replace_regex(r"\\#", "#")
		self._text.replace_regex(r"\\,", " ")
		self._text.replace_regex(r"\\%", "%")
		self._text.replace_regex(r"\\ ", " ")
		self._text.replace_regex(r"\\_", "_")

		# Remove setlength
		self._text.delete_regex(r"\\setlength{[^}]*}{[^}]*}")

		# Remove formulas
		self._text.replace_regex(r"\\\[.*\\\]", "[Removed formula]")
		self._text.replace_regex(r"\$[-+*{}(),_^a-zA-Z0-9=\. ]+?\$", "x+y")

		# Pull percent sign in
		self._text.replace_regex(r"([0-9]) %", lambda o: o.group(1) + "%")

		# Remove other stuff
		for (searchpattern, replacement) in self._STATIC_REPLACEMENTS:
			self._text.replace_regex(searchpattern, replacement)

		# Remove entire commands
		self._text.replace_regex(r"\\newpage", "")
		self._text.replace_regex(r"\\@", "")

		# Remove empty lines
		self._text.replace_regex(r"^\s+$", "")

		# Remove consecutive empty lines
		self._text.replace_regex(re.compile(r"\n{2,}", flags = re.MULTILINE), "\n\n")

	def _extract_words(self):
		for occurence in self._WORD_RE.finditer(self.text.text):
			str_offset = occurence.span()[0]
			orig_offset = self.text.translate_offset(str_offset)
			text = occurence.group(0)
			self._words.append((orig_offset, text))
	
	def _extract_sentences(self):
		sentence_offset = None
		sentence = [ ]

		for (offset, word) in self._words:
			if sentence_offset is None:
				sentence_offset = offset
			sentence.append(word)

			if word.endswith(".") or word.endswith(">"):
				# Probably end of sentence
				result = self._NO_END_OF_SENTENCE.match(word)
				if result is not None:
					# No, this is NOT the end of the sentence, continue!
					continue

				sentence = " ".join(sentence)
				self._sentences.append((sentence_offset, sentence))
				sentence_offset = None
				sentence = [ ]

	def _extract_raw_words(self):
		for (offset, word) in self._words:
			word = word.rstrip(".;:,])>").lstrip("[(<")
			self._raw_words.append((offset, word))

	def n_raw_words_iter(self, n):
		return zip(*(self._raw_words[i:] for i in range(n)))

	def __str__(self):
		return "TeX text, %d characters, %d words and %d sentences" % (len(self._text), len(self._words), len(self._sentences))

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
