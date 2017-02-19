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
from Tools import MiscTools
from BaseLintChecks import TexLintCheck, LintOffense, OffenseSource

class _CheckNumberWordHyphen(TexLintCheck):
	name = "number-word-hyphen"
	description = """
	Finds occurences which are supposed to have a hypen between a number and word (e.g., in '32-bit architecture'). May also yield false positives (e.g., 'the leftmost 4 bits are')."""
	linttype = "n-raw-words"
	word_count = 2

	def check_n_words(self, texfile, generator):
		for ((offset1, word1), (offset2, word2)) in generator:
			if (word2 == "bit") and word1.isdigit():
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset2), description = "Number and word \"%s %s\" is possibly missing a hyphen in between the words." % (word1, word2))

class _CheckSeparatedWords(TexLintCheck):
	name = "separated-words"
	description = """
	Finds occurences where two words are separate that should be written as one word (e.g., 'bit stream', 'byte code', 'run time')."""
	linttype = "n-raw-words"
	word_count = 2
	_CHECKED_WORDS = {
		("bit", "stream"): "bitstream",
		("byte", "code"): "bytecode",
		("run", "time"): "run time",
		("key", "less"): "keyless",
		("hard", "code"): "hardcode",
		("hard", "coded"): "hardcoded",
		("work", "flow"): "workflow",
		("tag", "line"): "tagline",
		("wire", "bound"): "wire-bound"
	}

	def check_n_words(self, texfile, generator):
		for ((offset1, word1), (offset2, word2)) in generator:
			word = (word1.lower(), word2.lower())
			if word in self._CHECKED_WORDS:
				replacement = self._CHECKED_WORDS[word]
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset1), description = "\"%s %s\" should possibly be spelled \"%s\"." % (word1, word2, replacement))

class _CheckRepeatedWords(TexLintCheck):
	name = "repeated-words"
	description = """
	Finds text locations which repeat a lot (i.e. more than x occurences in y consecutive words)."""
	linttype = "n-raw-words"
	word_count = 45
	threshold = 4
	_WHITELIST = set((
		"the",
		"are",
		"were",
	))

	@staticmethod
	def _wordstem(word):
		word = word.lower()
		if word.endswith("s"):
			word = word[:-1]
		if word.endswith("er"):
			word = word[:-2]
		return word

	def check_n_words(self, texfile, generator):
		holdoff = { }
		for offset_words in generator:
			words = [ offset_word[1] for offset_word in offset_words ]
			words = [ word for word in words if (len(word) >= 3) and (word not in self._WHITELIST) ]
			words = [ self._wordstem(word) for word in words ]
			counter = collections.Counter(words)
			for (wordstem, occurences) in counter.most_common():
				if occurences < self.threshold:
					break
				if holdoff.get(wordstem, 0) == 0:
					offset = None
					fullwords = [ ]
					for (wordoffset, fullword) in offset_words:
						if fullword.lower().startswith(wordstem):
							if offset is None:
								offset = wordoffset
							fullwords.append(fullword)
					if offset is None:
						raise Exception("Word stem '%s' not found in full word list %s -- programming error?" % (wordstem, str(offset_words)))
					yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset), description = "Word stem \"%s\" occurs %d times within %d words (%s)." % (wordstem, occurences, self.word_count, ", ".join(fullwords)))

					# Hold off on warning about this word again within the next
					# x words (identical error would otherwise throw the same
					# error message lots of times due to word sliding window)
					holdoff[wordstem] = self.word_count
				elif wordstem in holdoff:
					# Decrease holdoff for that word so that eventually warnings are emitted again
					holdoff[wordstem] -= 1

class _CheckAbbreviationCommata(TexLintCheck):
	name = "abbreviation-commata"
	description = """
	Finds occurences of abbreviations that call for a comma immediately after the abbreviation. Examples are 'e.g.' and 'i.e.'."""
	linttype = "n-words"
	word_count = 1

	def check_n_words(self, texfile, generator):
		for ((offset, word), ) in generator:
			if word.startswith("e.g.") or word.startswith("i.e."):
				if not word.endswith(","):
					yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset + len(word) - 1), description = "Abbreviation \"%s\" should probably end with a comma, but does not." % (word))


class _CheckPrepositions(TexLintCheck):
	name = "preposition-check"
	description = """
	Finds misused prepositions for certain words."""
	linttype = "n-raw-words"
	word_count = 2

	_PREPOSITIONS = set(['aboard', 'about', 'above', 'across', 'after',
		'against', 'along', 'amid', 'among', 'anti', 'around', 'as', 'at',
		'before', 'behind', 'below', 'beneath', 'beside', 'besides', 'between',
		'beyond', 'but', 'by', 'concerning', 'considering', 'despite', 'down',
		'during', 'except', 'excepting', 'excluding', 'following', 'for',
		'from', 'in', 'inside', 'into', 'like', 'minus', 'near', 'of', 'off',
		'on', 'onto', 'opposite', 'outside', 'over', 'past', 'per', 'plus',
		'regarding', 'round', 'save', 'since', 'than', 'through', 'to',
		'toward', 'towards', 'under', 'underneath', 'unlike', 'until', 'up',
		'upon', 'versus', 'via', 'with', 'within', 'without'])
	_ACCEPTABLE_PREPOSITIONS = {
		"equivalent":		("of", ),
		"interest":			("in", "of", "to"),
	}

	def check_n_words(self, texfile, generator):
		for ((offset, word), (prep_offset, preposition)) in generator:
			if word in self._ACCEPTABLE_PREPOSITIONS:
				acceptable = self._ACCEPTABLE_PREPOSITIONS[word]
				if (preposition in self._PREPOSITIONS) and preposition not in acceptable:
					yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, prep_offset), description = "Expected \"%s\" to stand with any of the prepositions \"%s\", but found \"%s\"." % (word, ", ".join(sorted(acceptable)), preposition))


class _CheckWordiness(TexLintCheck):
	name = "wordiness"
	description = """
	Checks wordiness of three-word phrases and offers alternatives. For example, "is able to" can be replaced by "can"."""
	linttype = "n-raw-words"
	word_count = [ 3, 4 ]

	_WORDINESS = {
		("are", "able", "to"):				"can",
		("is", "able", "to"):				"can",
		("in", "order", "to"):				"to",
		("in", "order", "for"):				"for",
		("in", "terms", "of"):				"regarding",
		("by", "means", "of"):				"using",
		("has", "the", "ability", "to"):	"can",
		("have", "the", "ability", "to"):	"can",
	}

	def check_n_words(self, texfile, generator):
		for offset_words in generator:
			words = tuple(word for (offset, word) in offset_words)
			if words in self._WORDINESS:
				replacement = self._WORDINESS[words]
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset_words[0][0]), description = "Wordiness: \"%s\" could be replaced by \"%s\"." % (" ".join(words), replacement))

class _CheckSloppyAbbreviations(TexLintCheck):
	name = "sloppy-abbreviations"
	description = """
	Checks sloppy abbreviations such as "don't" or "can't" which should be avoided in technical writing."""
	linttype = "n-raw-words"
	word_count = 1

	_ALTERNATIVES = {
		"don't":	"do not",
		"won't":	"will not",
		"can't":	"cannot",

		"i'm":		"I am",
		"you're":	"you are",
		"he's":		"he is",
		"she's":	"she is",
		"it's":		"it is",
		"we're":	"we are",
		"they're":	"they are",

		"i'd":		"I would",
		"you'd":	"you would",
		"he'd":		"he would",
		"she'd":	"she would",
		"it'd":		"it would",
		"we'd":		"we would",
		"they'd":	"they would",
	}

	def check_n_words(self, texfile, generator):
		for ((offset, word), ) in generator:
			if word in self._ALTERNATIVES:
				replacement = self._ALTERNATIVES[word]
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset), description = "\"%s\" could be replaced by \"%s\"." % (word, replacement))


class _CheckExplainedFirstAbbreviation(TexLintCheck):
	name = "explained-abbreviations"
	description = """
	Checks that the first occurence of every abbreviation is explained properly."""
	linttype = "once"
	word_count = 1

	@staticmethod
	def _extract_abbreviation(text):
		text = text.strip("\"().,:")
		if text.endswith("'s"):
			text = text[:-2]
		elif text.endswith("s"):
			text = text[:-1]			
		return text

	def check_all(self):
		first_occurences = set()
		for texfile in self.texfiles:
			for ((offset, raw_word), ) in texfile.n_words_iter(1):
				if raw_word.startswith("\\"):
					# That's a command
					continue
				abbreviation = MiscTools.contains_abbreviation(raw_word)
				if abbreviation is not None:
					word = self._extract_abbreviation(abbreviation.group(1))
					if word in first_occurences:
						continue
					first_occurences.add(word)
					
					expect_explained = "(" + word + ")"
#					print(raw_word, self._extract_abbreviation(raw_word), word, expect_explained)

					if self._extract_abbreviation(raw_word) != word:
						yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset), description = "\"%s\" is a possibly previously unexplained abbreviation." % (word))


