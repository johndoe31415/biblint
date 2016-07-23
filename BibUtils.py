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

import json
import collections

class BibUtils(object):

	def __init__(self, bibliography):
		self._bibliography = bibliography


	def author_scan(self, file):
		names = set()
		for entry in self._bibliography:
			for field in [ "author", "editor" ]:
				if entry.haskey(field):
					for name in entry.parsenames(field):
						names.add(name)
		names = [ { "firstname": person.firstname, "lastname": person.lastname, "midname": person.midname } for person in sorted(names, key = lambda p: (p.lastname, p.firstname, p.midname)) ]
		print(json.dumps(names), file = file)

