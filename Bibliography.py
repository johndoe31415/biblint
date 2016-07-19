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
import collections
from BibEntry import BibEntry

class Bibliography(object):
	_BEGIN_ENTRY_RE = re.compile("^\s*@(?P<entrytype>[a-zA-Z]+)\s*{(?P<entryname>[-a-zA-Z0-9._:/]+),")
	_END_ENTRY_RE = re.compile("^\s*},?\s*")
	_SUPPRESSION_RE = re.compile("^%\s+LINT\s+(?P<suppress>[^\s]+)(\s+(?P<description>.+))?")
	_Suppression = collections.namedtuple("Suppression", [ "suppress", "description" ])
	
	def __init__(self, filenames):
		self._entries = [ ]
		for filename in filenames:
			self._parse_file(filename)
		self._grouped_entries_by_name = self._group_entries_by_name()

	def _parse_file(self, filename):
		suppressions = [ ]
		current_entry = None
		with open(filename, "r") as f:
			for (lineno, line) in enumerate(f, 1):
				result = self._END_ENTRY_RE.match(line)
				if result:
					if current_entry is None:
						raise Exception("Error parsing BibTeX file %s on line number %d: End of entry found, but no entry recognized." % (filename, lineno + 1))
					current_entry = None
					continue

				if current_entry is not None:
					current_entry.parseline(line, lineno)

				result = self._BEGIN_ENTRY_RE.match(line)
				if result:
					if current_entry is not None:
						raise Exception("Error parsing BibTeX file %s on line number %d: Begin of new entry found, but last entry not finished yet." % (filename, lineno + 1))
					result = result.groupdict()
					current_entry = BibEntry(len(self._entries), result["entrytype"], result["entryname"], filename, lineno)
					for suppression in suppressions:
						current_entry.add_suppression(suppression)
					suppressions = [ ]
					self._entries.append(current_entry)
					continue
				
				result = self._SUPPRESSION_RE.match(line)
				if result:
					result = result.groupdict()
					suppression = self._Suppression(**result)
					suppressions.append(suppression)

	def _group_entries_by_name(self):
		groups_by_name = collections.defaultdict(list)
		for entry in self._entries:
			groups_by_name[entry.name].append(entry)
		return groups_by_name

	@property
	def grouped_entries_by_name(self):
		return self._grouped_entries_by_name

	def pretty_print(self, f):
		for entry in self._entries:
			entry.pretty_print(f)

	def getbyindex(self, index):
		return self._entries[index]

	def getbyname(self, name):
		return self._grouped_entries_by_name[name]

	def __len__(self):
		return len(self._entries)

	def __iter__(self):
		return iter(self._entries)
