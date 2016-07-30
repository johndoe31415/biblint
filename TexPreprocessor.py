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
from LineMapper import LineMapper
from TextFragmentTracker import TextFragmentTracker

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
	_NO_END_OF_SENTENCE = re.compile(r"\(?(Sect|Tab|List|Fig|i\.e|e\.g)[\.:;]")

	def __init__(self, texfilename, machine_checking = True):
		self._texfilename = texfilename
		self._machine_checking = machine_checking
		with open(texfilename) as f:
			self._text = f.read()
		self._line_col_mapper = LineMapper(self._text)
		self._text = TextFragmentTracker(self._text)
		self._words = [ ]
		self._sentences = [ ]
		self._raw_words = [ ]
		self._remove_tex_code()
		self._extract_words()
		self._extract_sentences()
		self._extract_raw_words()

	def get_line_col(self, offset):
		return self._line_col_mapper.resolve(offset)

	@property
	def filename(self):
		return self._texfilename

	@property
	def text(self):
		return self._text

	def _remove_tex_code(self):
		# Remove comments
		self._text.delete_regex(r"[^\\](%.*[^\n])", delete_spans = [ 1 ])
		self._text.delete_regex(r"\n(\s*%[^\n]*)", delete_spans = [ 1 ])

		# Then remove listings, figures and tables 
		for name in self._REMOVE_COMPLETELY_ENVIRONMENTS:
			regex = re.compile(r"\\begin{%s\*?}.*?\\end{%s\*?}" % (name, name), flags = re.DOTALL | re.MULTILINE)
			replacement = "" if self._machine_checking else "<Removed %s>" % (name)
			self._text.replace_regex(regex, replacement)

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
		replacement = "" if self._machine_checking else "John Doe and Jane Low"
		self._text.replace_regex(r"\\[cC]itet{[^}]*}", replacement)

		# Replace citep quotations at end of sentence
		# TODO?
#		regex = re.compile(r"~\\citep{[^}]*}\.")
#		tex = regex.sub(".", tex)

		# Replace citep quotations
		replacement = "" if self._machine_checking else "[Jane Doe, 2016]"
		self._text.replace_regex(r"\\citep{[^}]*}", replacement)

		# Replace references
		replacement = "" if self._machine_checking else "1.2.3"
		self._text.replace_regex(r"\\ref{[^}]*}", replacement)

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
		self._text.replace_regex(r"\\le", "<=")

		# Remove setlength
		self._text.delete_regex(r"\\setlength{[^}]*}{[^}]*}")

		# Remove formulas
		replacement = "" if self._machine_checking else "<Removed formula>"
		self._text.replace_regex(re.compile(r"\\\[.*?\\\]", flags = re.MULTILINE), replacement)
		self._text.replace_regex(r"\$[-+*{}(),_^a-zA-Z0-9=\. ]+?\$", replacement)

		# Pull percent sign in
		self._text.replace_regex(r"([0-9]) %", lambda o: o.group(1) + "%")

		# Remove other stuff
		for (searchpattern, replacement) in self._STATIC_REPLACEMENTS:
			self._text.replace_regex(searchpattern, replacement)

		# Remove entire commands
		self._text.replace_regex(r"\\newpage", "")
		self._text.replace_regex(r"\\@", "")

		if not self._machine_checking:
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
	
	def n_words_iter(self, n):
		return zip(*(self._words[i:] for i in range(n)))

	def n_raw_words_iter(self, n):
		return zip(*(self._raw_words[i:] for i in range(n)))

	def __str__(self):
		return "TeX text, %d characters, %d words and %d sentences" % (len(self._text), len(self._words), len(self._sentences))

