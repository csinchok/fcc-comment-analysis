import argparse
import requests
import time
import io
import itertools
import json
import warnings
import math


class CommentIndexer:

    def __init__(self, lte=None, gte=None, limit=100, sort='date_disseminated,DESC', fastout=False, verify=True, endpoint='http://127.0.0.1/'):
        self.lte = lte
        self.gte = gte
        self.limit = limit
        self.sort = sort
        self.fastout = fastout
        self.verify = verify
        self.endpoint = endpoint

    def run(self):

        documents = []
        for i, comment in enumerate(self.iter_comments()):

            del comment['_index']

            documents.append(comment)

            if i != 0 and i % 100 == 0:
                created = self.bulk_index(documents)
                if created is False and self.fastout:
                    print('done!')
                    break

    def iter_comments(self):
        endpoint = 'https://ecfsapi.fcc.gov/filings'
        for page in itertools.count(0):
            query = {
                'proceedings.name': '17-108',
                'limit': self.limit,
                'offset': page * self.limit,
                'sort': self.sort
            }
            if self.lte and self.gte:
                query['date_received'] = '[gte]{gte}[lte]{lte}'.format(
                    gte=self.gte,
                    lte=self.lte
                )
            for i in range(7):
                response = requests.get(endpoint, params=query)

                try:
                    filings = response.json().get('filings', [])
                except json.decoder.JSONDecodeError:
                    time.sleep(math.pow(2, i))
                    continue
                else:
                    break
            for filing in filings:
                yield filing

            if len(filings) != self.limit:
                break

    def bulk_index(self, documents):
        endpoint = '{}{}/filing/{}'.format(
            self.endpoint,
            'fcc-comments',
            '_bulk'
        )

        payload = io.StringIO()
        payload_size = 0
        created = False
        for document in documents:
            try:
                del document['_index']
            except KeyError:
                pass

            index = {"create": {"_id": document['id_submission']}}
            payload_size += payload.write(json.dumps(index))
            payload_size += payload.write('\n')
            payload_size += payload.write(json.dumps(document))
            payload_size += payload.write('\n')

            if payload_size > 8 * 1024 * 1024:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    response = requests.post(endpoint, data=payload.getvalue(), verify=self.verify)
                    if response == 413:
                        raise Exception('Too large!')
                    payload = io.StringIO()
                    payload_size = 0
                    for item in response.json()['items']:
                        if item['create']['status'] == 201:
                            created = True

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = requests.post(endpoint, data=payload.getvalue(), verify=self.verify)
            payload = io.StringIO()
            payload_size = 0
            for item in response.json()['items']:
                if item['create']['status'] == 201:
                    created = True

        return created
