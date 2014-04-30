import re
from collections import deque
import unittest

try:
	import sublime, sublime_plugin
	class NicewrapCommand(sublime_plugin.TextCommand):
		def run(self, edit, **args):
			for region in self.view.sel():
				if region.empty():
					region = self.expand_to_paragraph(region)
					self.run_text(edit, region)
				else:
					region = self.view.line(region)
					self.run_text(edit, region)

		def run_text(self, edit, region):
			text = self.view.substr(region)
			print("'" + text + "'")
			w = WrapperProgram(text)
			new = w.get_wrapped()
			self.view.replace(edit, region, new)

		def expand_to_paragraph(self, region):
			#
			region = self.view.line(region)

			max_region = sublime.Region(0, 1e5)
			all_text = self.view.substr(max_region)

			index = region.a
			text_to_end = all_text[index:]
			text_to_beg = all_text[:index][::-1];

			start_i = 0
			end_i = 1e5

			prog = re.compile("\n\n")
			end_match = prog.search(text_to_end)
			start_match = prog.search(text_to_beg)
			if end_match:
				end_i = index + end_match.start(0)
			if start_match:
				start_i = index - start_match.start(0)

			return sublime.Region(start_i, end_i)


			# while text[a] != "\n" or text[a-1] != "\n":
			# 	a -= 1
			# while text[b] != "\n" or text[b+1] != "\n":
			# 	b += 1

			# region = sublime.Region(a, b)
			# return region



except ImportError:
	print("ImportError")

class Paragraph:

	MAX_LEN = 81

	def __init__(self):
		self.lines = []
		self.empty_lines_above = 0

	def add_line(self, line):
		self.lines.append(line)

	def has_non_empty_lines(self):
		for line in self.lines:
			if line.strip() != "":
				return True
		return False

	def get_wrapped(self):
		self.init_indent()
		text = " ".join(self.lines).strip()
		words = re.split(r"\s*", text)

		max_len = self.MAX_LEN - self.indent_len
		wrapper = LineWrapper(max_len)

		word_que = deque(words)
		wrapped_lines = []

		while word_que:
			word = word_que.popleft()
			if wrapper.can_add_word(word):
				wrapper.add_word(word)
			else:
				line = self.indent + wrapper.get_line()
				wrapped_lines.append(line)
				wrapper.reset()
				wrapper.add_word(word)
		wrapped_lines.append(self.indent + wrapper.get_line())

		return "\n" * self.empty_lines_above + "\n".join(wrapped_lines)


	def init_indent(self):
		first_line = ""
		for line in self.lines:
			if line.strip() != "":
				first_line = line
				break
			else:
				self.empty_lines_above += 1
		indent_chars = []
		for char in first_line:
			if char == "\t" or char == " ":
				indent_chars.append(char)
			else:
				break
		self.indent = "".join(indent_chars)
		self.indent_len = 0
		for char in indent_chars:
			if char == " ":
				self.indent_len += 1
			elif char == "\t":
				self.indent_len += 4

	def __repr__(self):
		return repr(self.lines) + "\n"


class LineWrapper:

	def __init__(self, max_len):
		self.max_len = max_len
		self.indent = "\t"
		self.indent_len = 4
		self.line = []
		self.is_continued = False
		self.is_continued_prev = False

	def reset(self):
		self.is_continued_prev = self.is_continued
		self.line = []

	def add_word(self, word):
		self.line.append(word)

	def get_len(self):
		space_len = len(self.line) - 1
		words_len = sum([len(word) for word in self.line])
		continued_len = self.indent_len if self.is_continued else 0
		return space_len + words_len + continued_len

	def is_end_of_sentence(self):
		if len(self.line) == 0:
			return False
		return self.line[-1][-1] == "."

	def can_add_word(self, word):
		if self.is_end_of_sentence():
			self.is_continued = False
			return False
		self.line.append(word)
		new_len = self.get_len()
		self.line.pop()
		if new_len >= self.max_len:
			self.is_continued = True
			return False
		else:
			return True


	def get_line(self):
		indent = self.indent if self.is_continued_prev else ""
		return indent + " ".join(self.line)


class WrapperProgram:

	def __init__(self, input_text):
		self.input_text = input_text
		self.paragraphs = []
		self.bottom_paragraph = None
		self.seperate_into_paragraphs()

	def seperate_into_paragraphs(self):
		lines = self.input_text.split("\n")
		par = Paragraph()
		for line in lines:
			if line.strip() == "" and par.has_non_empty_lines():
				self.paragraphs.append(par)
				par = Paragraph()
			par.add_line(line)
		if par.has_non_empty_lines():
			self.paragraphs.append(par)
			self.bottom_paragraph = ""
		else:
			self.bottom_paragraph = par.get_wrapped()

	def get_wrapped(self):
		if self.input_text.strip() == "":
			return self.input_text
		wrapped = [par.get_wrapped() for par in self.paragraphs]
		return "\n".join(wrapped) + self.bottom_paragraph



test_text_expected = """

Toledo is hardly the only American city pursuing investors from China, but it is
	punching well above its weight at a time when other cities are striking bla
	aotnaowfet aowftn aowftnoawftnoafwtnao.



	Once a bounded length deque is full, when new.
	items are added, a corresponding number of items are discarded from the
		opposite end.
	Bounded length deques provide functionality.

   bare tre mellomrom

"""

test_text_input = """

Toledo is hardly the only American city pursuing investors from China, but it is punching well above its weight at a time when other cities are striking bla aotnaowfet aowftn aowftnoawftnoafwtnao.



	Once a bounded length deque is full, when new. items are added, a corresponding number of items are discarded from the opposite end. Bounded length deques provide functionality.

   bare tre mellomrom

"""


class Test(unittest.TestCase):

	def setUp(self):
		self.w = WrapperProgram(test_text_input)
		self.pw = LineWrapper(Paragraph.MAX_LEN)
		Paragraph.MAX_LEN = 81

	def test_empty(self):
		w = WrapperProgram("")
		wrapped = w.get_wrapped()
		self.assertEqual("", wrapped)

	def test_paragraphs(self):
		w = self.w
		self.assertEqual(3, len(w.paragraphs))

		pars = w.paragraphs
		for par in pars: par.get_wrapped()

		self.assertEqual(0, pars[0].indent_len)
		self.assertEqual(2, pars[0].empty_lines_above)
		self.assertEqual("", pars[0].indent)

		self.assertEqual(4, pars[1].indent_len)
		self.assertEqual(3, pars[1].empty_lines_above)
		self.assertEqual("\t", pars[1].indent)

		self.assertEqual(3, pars[2].indent_len)
		self.assertEqual(1, pars[2].empty_lines_above)
		self.assertEqual("   ", pars[2].indent)

	def test_output(self):
		w = self.w
		self.maxDiff = None
		actual = w.get_wrapped()
		self.assertEqual(test_text_expected, actual)

	def test_output_super_simple(self):
		text = "a b\n c d"
		expected = "a b c d"
		w = WrapperProgram(text)
		actual = w.get_wrapped()
		self.assertEqual(expected, actual)

	def test_wrapper(self):
		pw = self.pw
		par = "a ab abc"
		words = par.split(" ")
		for word in words:
			pw.add_word(word)
		self.assertEqual(len(par), pw.get_len())

	def test_simple_output(self):
		text = "Dette er enkelt\n\n"
		w = WrapperProgram(text)
		w.debug = True

		self.assertEqual(w.get_wrapped(), text)

	def test_advanced_output_doubled(self):
		output = """Lorem ipsum dolor sit amet, consectetur
	adipiscing elit.
Nam suscipit feugiat imperdiet.
Class aptent taciti sociosqu ad litora
	torquent per conubia nostra, per
	inceptos himenaeos.
Nullam at turpis pharetra, suscipit
	sapien vel, feugiat elit.
"""

		input = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam suscipit feugiat imperdiet. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Nullam at turpis pharetra, suscipit sapien vel, feugiat elit.\n"
		w = WrapperProgram(input)
		Paragraph.MAX_LEN = 40
		actual = w.get_wrapped()
		self.assertEqual(output, actual)

		w = WrapperProgram(actual)
		actual_two = w.get_wrapped()
		self.assertEqual(actual_two, actual)



if __name__ == "__main__":
	unittest.main()
