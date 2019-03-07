import unittest
import psycopg2
import requests
import config
from db_helper import Cats

base_url = 'http://localhost:8080/'
connection = psycopg2.connect("dbname='{0}' user='{1}' password='{2}' host='{3}' port='{4}'".format(config.dbname, config.user, config.password, config.host, config.port))

class TestCats(unittest.TestCase):

  def test_cats(self):
      url = base_url + 'cats'
      r = requests.get(url)
      self.assertEqual(r.status_code, 200)

  def test_cats_valid_params_first(self):
      url = base_url + 'cats?attribute=name&order=asc'
      r = requests.get(url)
      self.assertEqual(r.status_code, 200)

  def test_cats_valid_params_second(self):
      url = base_url + 'cats?limit=10&offset=10'
      r = requests.get(url)
      self.assertEqual(r.status_code, 200)

  def test_cats_valid_params_third(self):
      url = base_url + 'cats?attribute=name&order=asc&limit=10&offset=10'
      r = requests.get(url)
      self.assertEqual(r.status_code, 200)

  def test_cats_invalid_attribute(self):
      url = base_url + 'cats?atribute=name&order=asc'
      r = requests.get(url)
      self.assertEqual(r.status_code, 400)
      self.assertTrue(str(r.content).__contains__('Non-existent parameter: atribute'))

  def test_cats_invalid_name(self):
      url = base_url + 'cats?attribute=namef&order=asc'
      r = requests.get(url)
      self.assertEqual(r.status_code, 400)
      self.assertTrue(str(r.content).__contains__('Non-existent attribute: namef'))

  def test_cats_without_order(self):
      url = base_url + 'cats?attribute=name'
      r = requests.get(url)
      self.assertEqual(r.status_code, 400)
      self.assertTrue(str(r.content).__contains__('Order is required'))

  def test_cats_invalid_order(self):
      url = base_url + 'cats?attribute=name&order=asci'
      r = requests.get(url)
      self.assertEqual(r.status_code, 400)
      self.assertTrue(str(r.content).__contains__('Invalid order'))

  def test_cats_without_offset(self):
      url = base_url + 'cats?limit=10'
      r = requests.get(url)
      self.assertEqual(r.status_code, 400)
      self.assertTrue(str(r.content).__contains__('Offset is required'))

  def test_cats_invalid_offset(self):
      offset = Cats(connection).count()
      url = base_url + 'cats?limit=10&offset={}'.format(offset)
      r = requests.get(url)
      self.assertEqual(r.status_code, 400)
      self.assertTrue(str(r.content).__contains__('Invalid offset'))

  def test_post_cats_valid(self):
      Cats(connection).delete('name', 'TestCat')
      url = base_url + 'cat'
      json = {"name": "TestCat", "color": "red & white", "tail_length": 15, "whiskers_length": 12}
      r = requests.post(url, json=json)
      self.assertEqual(r.status_code, 200)
      self.assertTrue(Cats(connection).find('TestCat'))
      Cats(connection).delete('name', 'TestCat')

if __name__ == '__main__':
    unittest.main()