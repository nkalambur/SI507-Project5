import unittest
from SI507project5_code import *

class Tests(unittest.TestCase):
	def setUp(self):
		self.url = "https://api.tumblr.com/v2/tagged?"
		self.ml_tag = {"tag":"Machine Learning", "limit":1}
		self.ux_tag = {"tag": "UX", "limit":1}
		self.service = "Tumblr"
		
		# Return API results
		self.ux = process_api_results(self.url, self.ux_tag)
		self.ml = process_api_results(self.url, self.ml_tag)

		# Construct a class
		self.ux_cl = Tumblr_response(self.ux[0])
		self.ml_cl = Tumblr_response(self.ml[0])

		# open up files from project5_code.py
		self.UX_file = open("UX_tag_results.csv", "r")
		self.ML_file = open("ML_tag_results.csv", "r")

		print("All Set Up!")

	def test_class_num_tags_method(self):
		self.assertIsInstance(self.ux_cl.num_tags(), int)
		# Checks that the number of tags return is actually integer

	def test_type_returned(self):
		# should be tuple
		self.assertIsInstance(self.ux[0], tuple)

	def test_class_constructor1(self):
		self.assertIsInstance(self.ml_cl.blog_name, str)

	def test_class_string(self):
		self.assertEqual(str(self.ml_cl), self.ml[0][0]+" | "+self.ml[0][1])

	def test_files_created(self):
		self.assertTrue(self.UX_file.read())
		self.assertTrue(self.ML_file.read())

	def tearDown(self):
		self.UX_file.close()
		self.ML_file.close()

		print("Tore Down!!")

if __name__ == "__main__":
    unittest.main(verbosity=2)
