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

import os
import textwrap
import io
from BaseLintChecks import BibLintCheck, TexLintCheck

class LintDB(object):
	def __init__(self):
		self._known_modules = { }

	def scan_module(self, module):
		for (lint_class_name, lint_class) in vars(module).items():
			if not isinstance(lint_class, type):
				# Isn't a class
				continue
			if any(superclass in [ BibLintCheck, TexLintCheck ] for superclass in lint_class.__mro__[1:]):
				name = lint_class.name
				if name is None:
					raise Exception("Lint class %s has no name associated, refusing to register it." % (lint_class))
				if name in self._known_modules:
					raise Exception("Lint check has duplicate name: %s" % (name))
				self._known_modules[name] = lint_class

	@property
	def known_check_names(self):
		return sorted(list(self._known_modules.keys()))

	@property
	def check_classes(self):
		return sorted(list(self._known_modules.values()), key = lambda cls: cls.name)

	def _print_help(self, file, cmd_prefix = " - ", pre_cmd = "", post_cmd = "", ignore_markdown = True, initial_indent = "      ", subsequent_indent = "      "):
		for (linttarget, linttarget_name) in ( [ "tex", "TeX" ], [ "bib", "bibliography" ] ):
			classes = self.get_check_classes_by_linttarget(linttarget)
			print("%d %s lint checks available:" % (len(classes), linttarget_name), file = file)
			for check_cls in classes:
				print("%s%s%s%s" % (cmd_prefix, pre_cmd, check_cls.name, post_cmd), file = file)
				description = textwrap.dedent(check_cls.description).strip()
				for paragraph in description.split("\n"):
					if paragraph != "":
						for line in textwrap.wrap(paragraph, initial_indent = initial_indent, subsequent_indent = subsequent_indent):
							is_markdown = ("```" in line)
							if ignore_markdown and is_markdown:
								continue
							print(line, file = file)
					else:
						print(file = file)
				print(file = file)
			print(file = file)

	def print_help(self, file):
		print(file = file)
		self._print_help(file)

	def update_markdown(self):
		readme = io.StringIO()
		with open("README.md") as f:
			# Read until the list appears
			for line in f:
				readme.write(line)
				if line.startswith("### Full list of implemented checks"):
					break

			# Generate the new list
			for line in textwrap.wrap("To get a complete list of checks that biblint is able to execute, just run it on the command line wihtout any arguments. Currently, the implemented checks are:"):
				print(line, file = readme)
			print(file = readme)

			# Print the new help to the new README.md file
			self._print_help(readme, ignore_markdown = False, cmd_prefix = "- ", pre_cmd = "**", post_cmd = "**: ", initial_indent = "      ", subsequent_indent = "      ")
			print(file = readme)
			print(file = readme)

			# Read until the section is finished
			for line in f:
				if not line.startswith("###"):
					continue
				readme.write(line)
				break

			# Put the whole suffix in the README.md file
			for line in f:
				readme.write(line)

		readme = readme.getvalue()
		with open("README.md", "w") as f:
			f.write(readme)

	def get_check_classes(self, checknames):
		return [ self._known_modules[name] for name in sorted(checknames) ]

	def get_check_classes_by_linttarget(self, linttarget):
		return sorted([ module for module in self._known_modules.values() if (module.linttarget == linttarget) ], key = lambda cls: cls.name)

