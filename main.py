import requests
from operator import itemgetter
from bs4 import BeautifulSoup
from collections import namedtuple
import pylint.epylint
import tempfile
import os.path
import shutil
import random
import imp
import multiprocessing
import Queue


STACK_EXCHANGE_API = r'https://api.stackexchange.com/2.1/search/advanced'
ALPHABET = 'abcdefghijklmnopqrstuvwxyz'

Program = namedtuple('Program', ['name', 'args', 'return_value', 'body_lines'])


class TemporaryModule:
    def __init__(self, program):
        self.program = program
        self.__d = tempfile.mkdtemp()
        self.__f = tempfile.NamedTemporaryFile('r+', suffix='.py', dir=self.__d, delete=False)
        self.__f.write(render(program))
        self.__f.close()
        self.filename = os.path.abspath(self.__f.name)
        self.name = os.path.splitext(os.path.basename(self.filename))[0]

    def __del__(self):
        shutil.rmtree(self.__d)


class UsefulFunction:
    def __init__(self, program):
        self.program = program

    def __call__(self, *args):
        return call(self.program, args)


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


def query_pylint(program):
    module = TemporaryModule(program)
    out, err = pylint.epylint.py_run(module.filename, True)
    output = out.read()
    out.close()
    err.close()
    return map(parse_pylint_issue, output.split('\n'))


def debugged(program, max_attempts=5):
    for attempt in xrange(max_attempts):
        issues = query_pylint(program)
        prev = program
        for issue in issues:
            program = repair(program, issue)
        if program == prev:
            break
    return program


def make_function_from_code(body_lines):
    return UsefulFunction(debugged(make_program(body_lines)))


def evaluate(q, program, args):
    module = TemporaryModule(program)
    m = imp.load_source(module.name, module.filename)
    f = getattr(m, program.name)
    q.put(f(*args))


def call(program, args, timeout=1):
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=evaluate, args=(q, program, args))
    p.start()
    result = q.get(timeout=timeout)
    p.join()
    return result


def gen_candidate_solutions(query):
    links = get_stackexchange_links(query)
    for link in links:
        for body_lines in gen_answers(link):
            yield body_lines


def run_test(t, f):
    try:
        return t(f)
    except Queue.Empty:
        return False


def implement_function(requirements, test_cases):
    query = '%s python' % str(requirements.strip())
    for i, body_lines in enumerate(gen_candidate_solutions(query)):
        print '>>> SOLUTION %d:' % i
        f = make_function_from_code(body_lines)
        print
        print render(f.program)
        print
        print '>>> HIT ENTER TO RUN TESTS...'
        raw_input() # hack for some degree of sanity
        passes = [run_test(t, f) for t in test_cases]
        status = ''.join('.' if x else 'F' for x in passes)
        print '>>> TEST RESULTS: %s' % status
        if all(passes):
            return f
    raise NotImplementedError((requirements, test_cases))


def main():
    # ha ha ha ha ha!
    f = implement_function(
        requirements='sort a list',
        test_cases=[
            lambda f : f([3, 1, 2]) == [1, 2, 3],
            lambda f : f([9, 0, 2, 1, 0]) == [0, 0, 1, 2, 9],
        ]
    )

    print f([8, 7, 3, 8, 5, 9, 1, 5, 7, 9, 4])


if __name__ == '__main__':
    main()

