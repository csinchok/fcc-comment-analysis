import json
import multiprocessing
from tqdm import tqdm
import requests
import warnings
import io
import argparse

from .analyzers import analysis


def get_source(comment):
    if 'text_data' not in comment:
        return

    if comment['text_data'].startswith('The unprecedented regulatory power the Obama Administration imposed on the internet'):
        return 'bot.unprecedented'

    if comment['text_data'].startswith('The FCC Open Internet Rules (net neutrality rules) are extremely important to me'):
        return 'form.battleforthenet'

    if comment['text_data'].startswith('I was outraged by the Obama/Wheeler FCC'):
        return 'bot.outraged'

    if 'my understanding that the FCC Chairman intends to reverse net neutrality rules' in comment['text_data']:
        return 'reddit.technology'

    if 'i support the existing net neutrality rules, which classify internet service providers under the title i' in comment['text_data'].lower():
        return 'blog.venturebeat'

    if comment['text_data'].startswith('Obama’s Title II order has diminished broadband investment'):
        return 'form.diminished-investment'



class CommentAnalyzer:

    def __init__(self, endpoint='http://localhost:9200/', verify=True):
        self.endpoint = endpoint
        self.verify = verify

    def run(self):
        in_queue = multiprocessing.Queue(maxsize=1000)
        out_queue = multiprocessing.Queue()
        tagging_processes = []

        for _ in range(5):
            process = multiprocessing.Process(target=self.tagging_worker, args=(in_queue, out_queue))
            process.start()
            tagging_processes.append(process)
        
        index_process = multiprocessing.Process(target=self.index_worker, args=(out_queue,))
        index_process.start()

        try:
            for comment in self.iter_comments(size=100):
                in_queue.put(comment)
        except KeyboardInterrupt:
            pass

        for _ in range(5):
            in_queue.put(None)

        for p in tagging_processes:
            p.join()

        out_queue.put(None)

        index_process.join()

    def tagging_worker(self, in_queue, out_queue):
        
        while True:
            comment = in_queue.get()
            if comment is None:
                break
            analysis = analyze(comment)
            out_queue.put((comment['id_submission'], analysis))

    def index_worker(self, queue, size=250):

        endpoint = '{}{}/filing/{}'.format(
            self.endpoint,
            'fcc-comments',
            '_bulk'
        )

        payload = io.StringIO()
        counter = 0
        while True:
            item = queue.get()
            if item is None:
                print('bailing...')
                break
            id_submission, analysis = item

            index = {"update": {"_id" : id_submission} }
            payload.write(json.dumps(index))
            payload.write('\n')
            payload.write(json.dumps({'doc': {'fields':{ 'analysis': analysis}}}))
            payload.write('\n')

            counter += 1
            if counter % size == 0:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    response = requests.post(endpoint, data=payload.getvalue(), verify=self.verify)
                    if response.status_code != 200:
                        print(response.text)
                        raise Exception(response.status_code)
                payload = io.StringIO()
                counter = 0

    def iter_comments(self, timeout='5m', size=100, progress=True):
        start_url = '{}fcc-comments/filing/_search?scroll={}'.format(
            self.endpoint, timeout
        )
        scroll_url = '{}_search/scroll'.format(self.endpoint)
        headers={'Content-Type': 'application/json'}

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = requests.post(start_url, verify=self.verify, headers=headers, data=json.dumps({
                'size': size,
                'query': {
                    'match_all': {}
                },
                'sort': [
                    '_doc'
                ]
            }))
        scroll_id = response.json()['_scroll_id']
        progress = tqdm(total=response.json()['hits']['total'])
        hits = response.json()['hits']['hits']

        while hits:

            for hit in hits:
                yield hit['_source']
                progress.update(1)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                response = requests.post(scroll_url, headers=headers, verify=self.verify, data=json.dumps({
                    'scroll': timeout,
                    'scroll_id': scroll_id
                }))
                
            scroll_id = response.json()['_scroll_id']
            hits = response.json()['hits']['hits']

        progress.close()


if __name__ == '__main__':
    analyzer = CommentAnalyzer(endpoint='https://search-fcc-comments-m72e6e5oukdhdmhhrngv4hewsi.eu-west-1.es.amazonaws.com/', verify=False)
    analyzer.run()
