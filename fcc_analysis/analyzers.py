import re

WORDSPLIT_PATTERN = re.compile("['-]+", re.UNICODE)
NON_CHAR_PATTERN = re.compile('[^a-z ]+', re.UNICODE)


# I know...now I have two problems...
OLIVER_PATTERNS = [
    re.compile('(strong )?net neutrality( rules)? backed by title (ii|2|two)', flags=re.IGNORECASE),
    re.compile('i( specifically| strongly)? support( strong)? net neutrality backed by title', flags=re.IGNORECASE),
    re.compile('i( specifically| strongly)? support( strong)? net neutrality,?( oversight)?( backed)? by title (ii|2|two) oversight', flags=re.IGNORECASE),
]


def source(comment):
    '''Returns a string identifying the "source" of this comment, if possible.

    For example:

      - bot.unprecedented
      - johnoliver
      - form.battleforthenet

    '''
    if 'text_data' not in comment:
        return

    if comment['text_data'].startswith('The unprecedented regulatory power the Obama Administration imposed on the internet'):
        return 'bot.unprecedented'

    if comment['text_data'].startswith('I was outraged by the Obama/Wheeler FCC'):
        return 'bot.outraged'

    # This one is interesting, because it appends the Submitter's first name to the text_data, making the fingerprint unreliable...
    if comment['text_data'].startswith('The FCC Open Internet Rules (net neutrality rules) are extremely important to me'):
        return 'form.battleforthenet'

    if 'my understanding that the FCC Chairman intends to reverse net neutrality rules' in comment['text_data']:
        return 'reddit.technology'

    if 'i support the existing net neutrality rules, which classify internet service providers under the title i' in comment['text_data'].lower():
        return 'blog.venturebeat'

    if comment['text_data'].startswith('Obama’s Title II order has diminished broadband investment'):
        return 'form.diminished-investment'

    if 'passed rules treating the internet as a government regulated public utility for the first time in history' in comment['text_data'].lower():
        return 'form.freeourinternet'

    # This is the text that John Oliver suggested. Many people seemed to follow his suggestion.
    for pattern in OLIVER_PATTERNS:
        if pattern.search(comment['text_data']):
            return 'johnoliver'

    return 'unknown'


def titleii(comment):
    return None


def capsemail(comment):
    if comment.get('contact_email'):
        return comment['contact_email'] == comment['contact_email'].upper()


def fulladdress(comment):

    address = comment.get('addressentity', {})
    for key in ('address_line_1', 'city', 'state', 'zip_code'):
        if not address.get(key):
            return False
    return True


def fingerprint(comment):
    '''Get a text fingerprint--useful for looking for duplicate text'''

    text = comment.get('text_data', '').lower()
    text = WORDSPLIT_PATTERN.sub('', text)
    text = NON_CHAR_PATTERN.sub(' ', text)
    words = list(set(text.split()))
    words.sort()
    return " ".join(words)


def analyze(comment):

    analysis = {
        'fingerprint': fingerprint(comment),
        'fulladdress': fulladdress(comment),
        'capsemail': capsemail(comment),
        # 'titleii': titleii(comment),
        'source': source(comment)
    }

    source_mapping = {
        'bot.unprecedented': False,
        'bot.outraged': False,
        'form.diminished-investment': False,
        'form.freeourinternet': False,

        'johnoliver': True,
        'form.battleforthenet': True,
        'reddit.technology': True,
        'blog.venturebeat': True,
    }
    if analysis['source'] in source_mapping:
        analysis['titleii'] = source_mapping[analysis['source']]

    return analysis
