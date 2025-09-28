import os
import unittest
from collectors.base import Article


class TestArticle(unittest.TestCase):
    def test_article_defaults(self):
        a = Article(external_id='1', title='t')
        self.assertIsInstance(a.metadata, dict)


if __name__ == '__main__':
    unittest.main()


