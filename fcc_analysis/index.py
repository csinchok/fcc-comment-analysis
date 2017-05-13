import argparse
import requests
import time
import io
import itertools
import json
import warnings


def iter_comments(before=None, after=None, page=0, limit=100, sort='date_disseminated,DESC'):
    endpoint = 'https://ecfsapi.fcc.gov/filings'
    for page in itertools.count(page):
        query = {
            'proceedings.name': '17-108',
            'limit': limit,
            'offset': page * limit,
            'sort': sort
        }
        if before and after:
            query['date_received'] = '[gte]{after}[lte]{before}'.format(
                after=after,
                before=before
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

        if len(filings) != limit:
            break


def single_index(document, endpoint='https://127.0.0.1:9000/', verify=True):

    endpoint = '{}{}/filing/{}'.format(
        endpoint,
        'fcc-comments',
        document['id_submission']
    )

    response = requests.post(endpoint, headers={
        'Content-Type': 'application/json'
    }, data=json.dumps(document), verify=verify)
    if response.status_code == 413:
        print('Still too large! {}'.format(document['id_submission']))
    return response.status_code == 201


def bulk_index(documents, endpoint='https://127.0.0.1:9000/', verify=True):
    endpoint = '{}{}/filing/{}'.format(
        endpoint,
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
        
        index = {"create": {"_id" : document['id_submission'] } }
        payload_size += payload.write(json.dumps(index))
        payload_size += payload.write('\n')
        payload_size += payload.write(json.dumps(document))
        payload_size += payload.write('\n')

        if payload_size > 8 * 1024 * 1024:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                response = requests.post(endpoint, data=payload.getvalue(), verify=verify)
                if response == 413:
                    raise Exception('Too large!')
                payload = io.StringIO()
                payload_size = 0
                for item in response.json()['items']:
                    if item['create']['status'] == 201:
                        created = True

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        response = requests.post(endpoint, data=payload.getvalue(), verify=verify)
        payload = io.StringIO()
        payload_size = 0
        for item in response.json()['items']:
            if item['create']['status'] == 201:
                created = True

    return created



def main():
    parser = argparse.ArgumentParser(description='Locally index FCC comments')
    parser.add_argument(
        '-b', '--before', dest='before',
        help='Only index comments sent before this'
    )
    parser.add_argument(
        '-a', '--after', dest='after',
        help='Only index comments sent after this'
    )
    parser.add_argument(
        '--endpoint', dest='endpoint',
        default='http://127.0.0.1:9200/'
    )
    parser.add_argument(
        '--no-verify', dest='verify', nargs='?',
        help='Don\'t verify SSL certs', default=True,
        const=False
    )
    parser.add_argument(
        '--fast-out', dest='fastout', nargs='?',
        help='Quit when we see a comment that we\'ve already ingested', default=True,
        const=False
    )
    args = parser.parse_args()

    if args.before is None and args.after is None:
        # Just get the latest
        documents = []
        for i, comment in enumerate(iter_comments()):

            del comment['_index']

            documents.append(comment)

            if i != 0 and i % 100 == 0:
                created = bulk_index(documents, endpoint=args.endpoint, verify=args.verify)
                if created is False and args.fastout:
                    print('done!')
                    break

    elif args.before and args.after:
        documents = []
        for i, comment in enumerate(iter_comments(before=args.before, after=args.after, sort='date_received,ASC')):

            del comment['_index']

            documents.append(comment)

            if i != 0 and i % 100 == 0:
                created = bulk_index(documents, endpoint=args.endpoint, verify=args.verify)
                if created is False and args.fastout:
                    print('nothing')


if __name__ == '__main__':
    main()
