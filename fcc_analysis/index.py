import io
import itertools
import json
import math
import time
import warnings
import multiprocessing
from tqdm import tqdm

import requests


class CommentIndexer:

    def __init__(self, lte=None, gte=None, limit=250, sort='date_disseminated,DESC', fastout=False, verify=True, endpoint='http://127.0.0.1/'):
        self.lte = lte
        self.gte = gte
        self.limit = limit
        self.sort = sort
        self.fastout = fastout
        self.verify = verify
        self.endpoint = endpoint

    def run(self):
        index_queue = multiprocessing.Queue()

        bulk_index_process = multiprocessing.Process(
            target=self.bulk_index, args=(index_queue,),
        )
        bulk_index_process.start()
        progress = tqdm(total=1515603)

        for comment in self.iter_comments():
            index_queue.put(comment)
            progress.update(1)

        index_queue.put(None)
        bulk_index_process.join()
        progress.close()

    def iter_comments(self, page=0):
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
                    # Exponentially wait--sometimes the API goes down.
                    time.sleep(math.pow(2, i))
                    continue
                else:
                    break
            for filing in filings:
                yield filing

            if len(filings) != self.limit:
                break

    def bulk_index(self, queue):
        endpoint = '{}{}/filing/{}'.format(
            self.endpoint,
            'fcc-comments',
            '_bulk'
        )

        payload = io.StringIO()
        payload_size = 0
        created = False

        while True:
            document = queue.get()
            if document is None:
                break

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
