import mako.lookup

class HTMLComplaintRenderer(object):
	def __init__(self, complaints):
		self._complaints = complaints

	def render(self):
		lookup = mako.lookup.TemplateLookup([ "template" ])
		template = lookup.get_template("template.html")
		result = template.render(complaints = self._complaints)
		return result
