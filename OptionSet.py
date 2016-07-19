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

class OptionSet(object):
	def __init__(self, valid_options, default_str):
		self._valid_options = frozenset(option.lower() for option in valid_options)
		self._default_set = frozenset()
		self._default_set = self.parse(default_str)
		self._default_str = default_str

	@property
	def default_str(self):
		return self._default_str

	def _get_set(self, element):
		if element == "all":
			return self._valid_options
		elif element == "default":
			return self._default_set
		else:
			return set([ element ])

	def parse(self, string):		
		string = string.lower().split(":")
		result = set()
		for entry in string:
			if entry.startswith("+"):
				mode = "+"
				entry = entry[1:]
			elif entry.startswith("-"):
				mode = "-"
				entry = entry[1:]
			else:
				mode = "+"
			
			change_set = self._get_set(entry)
			if mode == "+":
				result |= change_set
			else:
				result -= change_set
		result &= self._valid_options
		return result

if __name__ == "__main__":
	oset = OptionSet([ "foo", "bar", "moo", "koo", "hubbeldubbel" ], "ALL:-foo")
	print(oset.parse("ALL:-default"))
