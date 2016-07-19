import re
import collections

class Citations(object):
	_CITE_RE = re.compile(r"\\(no)?[Cc]ite[tp]?{(?P<content>[^}]+)}")

	_Citation = collections.namedtuple("Citation", [ "filename", "lineno", "colno", "citation" ])
	def __init__(self):
		self._citations = collections.defaultdict(list)

	def _parseline(self, lineno, filename, line):
		for result in self._CITE_RE.finditer(line):
			citations = result.groupdict()["content"]
			colno = result.span()[0] + 1
			for citation in citations.split(","):
				citation = citation.strip(" ")
				self._citations[citation].append(self._Citation(filename = filename, lineno = lineno, colno = colno, citation = citation))

	def read_from_file(self, filename):
		with open(filename) as f:
			for (lineno, line) in enumerate(f, 1):
				line = line.rstrip("\r\n")
				self._parseline(lineno, filename, line)

	def getbyname(self, name):
		yield from self._citations[name]

	def __iter__(self):
		return iter(self._citations)

	def __len__(self):
		return len(self._citations)
