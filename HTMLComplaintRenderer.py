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

import mako.lookup

class HTMLComplaintRenderer(object):
	def __init__(self, complaints):
		self._complaints = complaints

	def render(self):
		lookup = mako.lookup.TemplateLookup([ "template" ])
		template = lookup.get_template("template.html")
		result = template.render(complaints = self._complaints)
		return result
