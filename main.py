import requests
from operator import itemgetter
from bs4 import BeautifulSoup
from collections import namedtuple
import pylint.epylint
import tempfile
import os.path
import shutil
import random

STACK_EXCHANGE_API = r'https://api.stackexchange.com/2.1/search/advanced'

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'


def get_stackexchange_links(query):
    params = dict(
        order='desc',
        sort='relevance',
        q=str(query),
        accepted=True,
        answers=1,
        views=50,
        site='stackoverflow',
    )
    r = requests.get(STACK_EXCHANGE_API, params=params)
    assert r.status_code == requests.codes.ok
    data = r.json()
    print data['quota_remaining']
    return map(itemgetter('link'), data['items'])


def gen_answers(url):
    r = requests.get(url)
    assert r.status_code == requests.codes.ok
    soup = BeautifulSoup(r.content)
    answer_cells = soup.find_all('td', {'class' : 'answercell'})
    for cell in answer_cells:
        codes = cell.find_all('code')
        if not codes:
            continue
        contents = codes[0].contents[0]
        if not contents:
            continue
        code_lines = str(contents).split('\n')
        yield code_lines


def make_random_letter():
    return random.choice(ALPHABET)

def make_random_name(n=8):
    return 'func_%s' % ''.join(make_random_letter() for _ in xrange(n))

def indent(s):
    return '    ' + s

Program = namedtuple('Program', ['name', 'args', 'return_value', 'body_lines'])

def make_program(body_lines, name=None):
    if name is None:
        name = make_random_name()
    return Program(name, [], None, list(body_lines))

def render(p):
    args = []
    header = 'def %s(%s):' % (p.name, ', '.join(p.args))
    body = [indent(line) for line in p.body_lines]
    footer = indent('return %s' % p.return_value)
    return '\n'.join([header] + body + [footer])


def parse_pylint_issue(message):
    kinds = [
        'Undefined variable',
        'Unused variable',
    ]
    for kind in kinds:
        if kind in message:
            i = message.index(kind)
            j = i + len(kind)
            name = message[j:].replace('\'', '').strip()
            return kind, name
    return 'Unknown', None


def repair(program, issue):
    kind, name = issue
    if kind == 'Undefined variable':
        program_prime = program._replace(args=list(program.args) + [name])
    elif kind == 'Unused variable':
        program_prime = program._replace(return_value=name)
    else:
        program_prime = program
    return program_prime


class TemporaryModule:
    def __init__(self, program):
        self.program = program
        self.__d = tempfile.mkdtemp()
        self.__f = tempfile.NamedTemporaryFile('r+', suffix='.py', dir=self.__d, delete=False)
        self.__f.write(render(program))
        self.__f.close()
        self.name = os.path.abspath(self.__f.name)

    def __del__(self):
        shutil.rmtree(self.__d)
        

def query_pylint(program):
    module = TemporaryModule(program)
    out, err = pylint.epylint.py_run(module.name, True)
    output = out.read()
    out.close()
    err.close()
    return map(parse_pylint_issue, output.split('\n'))


def make_useful_function(body_lines, max_attempts=5):
    p = make_program(body_lines)
    for attempt in xrange(max_attempts):
        issues = query_pylint(p)
        p_prev = p
        for issue in issues:
            p = repair(p, issue)
        if p == p_prev:
            break
    return p


def main():
    links = get_stackexchange_links("sort list python")
    for link in links:
        for code_lines in gen_code(link):
            print code_lines

if __name__ == '__main__':
    body_lines = ['b = sorted(a)']
    p = make_useful_function(body_lines)
    print render(p)

