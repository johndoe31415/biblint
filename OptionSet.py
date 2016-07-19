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
