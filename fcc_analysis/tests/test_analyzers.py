import os
import json
from unittest import TestCase

from fcc_analysis.analyzers import source, fulladdress, capsemail, fingerprint

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class AnalyzerTestCase(TestCase):
    maxDiff = 1000

    def get_comment(self, name):
        path = os.path.join(DATA_DIR, '{}.json'.format(name))
        with open(path, 'r') as f:
            return json.load(f)

    def test_unprecedented_bot(self):
        comment = self.get_comment('unprecedented-bot')

        self.assertEqual(source(comment), 'bot.unprecedented')
        self.assertTrue(fulladdress(comment))
        self.assertTrue(capsemail(comment))
        self.assertEqual(
            fingerprint(comment),
            'a administration american and as at bipartisan bureaucratic commission communications consensus consideration creation currently damaging economy enabled end everyone fcc federal flourish for forward free grab help i ii imposed innovation internet is job known lighttouch more obama obamas obstructing of on open overreach plan positive power promote regulatory repeal restore smothering step than that the title to truly under unprecedented urge will years'
        )

    def test_oliver(self):
        oliver_text = [
            'I support strong net neutrality backed by title 2 oversight of isps',
            'I support strong net neutrality backed by title 2 oversight of ISP\'s.',
            'I support strong Net Neutrality oversight backed by title 2 oversight of ISPs.',
            # 'I SUPPORT STRONG NET NEUTRALITY BACKED BY TITLE II (2) OVERSIGHT OF ISPS.',
            'I support strong net neutrality oversight backed by Title II oversight of ISP\'s.',
            # 'I support strong net neutrality backed by title oversight of Title II oversight of ISPs.',
            'I specifically support strong Net Neutrality, backed by Title II oversight of ISP\'s.',
            'I specifically support strong net neutrality backed by Title II oversight of ISP\'s!!!'
        ]

        for text in oliver_text:

            comment = {'text_data': text}
            self.assertEqual(source(comment), 'johnoliver', msg='No match: \n    "{}"'.format(text))