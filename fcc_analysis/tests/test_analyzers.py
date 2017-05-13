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

    def test_source(self):
        samples = {
            'johnoliver': [
                'I support strong net neutrality backed by title 2 oversight of isps',
                'I support strong net neutrality backed by title 2 oversight of ISP\'s.',
                'I support strong Net Neutrality oversight backed by title 2 oversight of ISPs.',
                # 'I SUPPORT STRONG NET NEUTRALITY BACKED BY TITLE II (2) OVERSIGHT OF ISPS.',
                'I support strong net neutrality oversight backed by Title II oversight of ISP\'s.',
                # 'I support strong net neutrality backed by title oversight of Title II oversight of ISPs.',
                'I specifically support strong Net Neutrality, backed by Title II oversight of ISP\'s.',
                'I specifically support strong net neutrality backed by Title II oversight of ISP\'s!!!',
                'i strongly support Net Neutrality backed by TItle II oversight.',
                'I support strong net neutrality by Title II oversight of ISPs.',
                'I strongly urge the FCC to maintain strong net neutrality rules backed by Title II.',
                'Support Strong Net Neutrality backed by Title II Oversight of ISP\'s.',
                'I am in support of strong net neutrality rules backed by Title II!',
                'I specifically support strong net neutrality backed by title (2) two oversite of isps.'
            ],
            'form.freeourinternet': [
                'In 2015, President Obama’s FCC passed rules treating the Internet as a government regulated public utility for the first time in history. Those pushing hardest for the new rules were Silicon Valley monopolies like Google and leftist globalists like George Soros.'
            ]
        }

        for sourcename, sample_list in samples.items():

            for text in sample_list:
                comment = {'text_data': text}
                self.assertEqual(source(comment), sourcename, msg='No match for {}: \n    "{}"'.format(sourcename, text))

