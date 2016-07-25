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

class _TextFragment(object):
	def __init__(self, text, startoffset = offset):
		self._text = text
		self._offset = offset

	@property
	def text(self):
		return self._text

	def __str__(self):
		return "\"%s\"" % (self._text)

class TexPreprocessor(object):
	def __init__(self, texfilename):
		with open(texfilename) as f:
			self._text = f.read()
		self._words = None
		self._sentences = None

	def extract_words(self):
		pass


if __name__ == "__main__":
	text = _TextFragment("foobar")
	print(text)
