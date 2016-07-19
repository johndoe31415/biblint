class BibUtils(object):
	def __init__(self, bibliography):
		self._bibliography = bibliography

	@staticmethod
	def _tex2unicode(text):
		text = text.replace(r"\'e", "é")
		text = text.replace(r"\'o", "ó")
		text = text.replace(r"\'i", "í")
		text = text.replace(r"\'E", "É")
		text = text.replace(r"\'O", "Ó")
		text = text.replace(r"\'I", "Í")
		text = text.replace(r"\"a", "ä")
		text = text.replace(r"\"o", "ö")
		text = text.replace(r"\"u", "ü")
		text = text.replace(r"\"A", "Ä")
		text = text.replace(r"\"O", "Ö")
		text = text.replace(r"\"U", "Ü")
		text = text.replace(r"\ss", "ß")
		text = text.replace(r"\cc", "ç")
		text = text.replace(r"\"y", "ÿ")
		return text

	def author_scan(self):
		for entry in self._bibliography:
			for field in [ "author", "editor" ]:
				authors = entry.rawtext("author")
				authors = self._tex2unicode(authors)
				authors = authors.split(" and ")
				for author in authors:
					if ", " in author:
						(lastname, firstname) = author.split(", ")
					else:
						lastname_words = set([ "de", "der", "von", "van" ])
						author = author.split(" ")
						firstname = author[:-1]
						lastname = [ author[-1] ]

						while len(firstname) > 1 and firstname[-1] in lastname_words:
							lastname.insert(0, firstname[-1])
							firstname = firstname[:-1]

						firstname = " ".join(firstname)
						lastname = " ".join(lastname)
					print("> %s, %s" % (lastname, firstname))
