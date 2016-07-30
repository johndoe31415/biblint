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
from BaseLintChecks import TexLintCheck, LintOffense, OffenseSource

class _CheckNumberWordHyphen(TexLintCheck):
	name = "number-word-hyphen"
	description = """
	Finds occurences which are supposed to have a hypen between a number and word (e.g., in '32-bit architecture'). May also yield false positives (e.g., 'the leftmost 4 bits are')."""
	linttype = "n-raw-words"
	word_count = 2
	
	def check_n_raw_words(self, texfile, generator):
		for ((offset1, word1), (offset2, word2)) in generator:
			if (word2 == "bit") and word1.isdigit():
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset2), description = "Number and word \"%s %s\" is possibly missing a hyphen in between the words." % (word1, word2))

class _CheckSeparatedWords(TexLintCheck):
	name = "separated-words"
	description = """
	Finds occurences where two words are separate that should be written as one word (e.g., 'bit stream', 'byte code', 'run time')."""
	linttype = "n-raw-words"
	word_count = 2
	_CHECKED_WORDS = set((
		("bit", "stream"),
		("byte", "code"),
		("run", "time"),
		("key", "less"),
		("hard", "code"),
		("hard", "coded"),
		("work", "flow"),
	))
	
	def check_n_raw_words(self, texfile, generator):
		for ((offset1, word1), (offset2, word2)) in generator:
			word = (word1, word2)
			if word in self._CHECKED_WORDS:
				yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset1), description = "\"%s %s\" should possibly be spelled \"%s%s\"." % (word1, word2, word1, word2))

class _CheckRepeatedWords(TexLintCheck):
	name = "repeated-words"
	description = """
	Finds text locations which repeat a lot (i.e. more than x occurences in y consecutive words)."""
	linttype = "n-raw-words"
	word_count = 20
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

	def check_n_raw_words(self, texfile, generator):
		holdoff = { }
		for offset_words in generator:
			words = [ offset_word[1] for offset_word in offset_words ] 
			words = [ word for word in words if (len(word) >= 3) and (word not in self._WHITELIST) ]
			words = [ self._wordstem(word) for word in words ]
			counter = collections.Counter(words)
			for (word, occurences) in counter.most_common():
				if occurences < self.threshold:
					break
				if holdoff.get(word, 0) == 0:
					yield LintOffense(lintclass = self.__class__, sources = OffenseSource.from_texfile(texfile, offset_words[0][0]), description = "Word stem \"%s\" occurs %d times within %d words." % (word, occurences, self.word_count))

					# Hold off on warning about this word again within the next
					# x words (identical error would otherwise throw the same
					# error message lots of times due to word sliding window)
					holdoff[word] = self.word_count
				elif word in holdoff:
					# Decrease holdoff for that word so that eventually warnings are emitted again
					holdoff[word] -= 1
