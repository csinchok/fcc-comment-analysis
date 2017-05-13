import os
import json
from unittest import TestCase

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

from fcc_analysis.analyzers import *


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
