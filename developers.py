"""
WARNING : this is a terrible idea. it downloads and executres arbitrary code. run at your own peril.
"""

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
import sys


STACK_EXCHANGE_API = r'https://api.stackexchange.com/2.1/search/advanced'
ALPHABET = 'abcdefghijklmnopqrstuvwxyz'

Program = namedtuple('Program', ['smell', 'name', 'args', 'return_value', 'body_lines'])

FUNCTION_SMELL = 0
CODE_SMELL = 1


def implement_function(requirements, test_cases):
    print '>>> REQUIREMENTS: "%s"' % requirements
    query = '%s python' % str(requirements.strip())
    for i, body_lines in enumerate(gen_candidate_solutions(query)):
        print '>>> SOLUTION %d:' % i
        f = make_function_from_code(body_lines)
        print
        print render(f.program)
        print
        passes = [run_test(t, f) for t in test_cases]
        status = ''.join('.' if x else 'F' for x in passes)
        print '>>> TEST RESULTS: %s' % status
        if all(passes):
            print '>>> ALL TESTS PASSED'
            return f
        else:
            print '>>> TEST FAILURE'
    raise NotImplementedError((requirements, test_cases))


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
    print '>>> QUOTA REMAINING: %d' % data['quota_remaining']
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


def make_random_name(prefix, n=12):
    return '%s_%s' % (prefix, ''.join(make_random_letter() for _ in xrange(n)))


def indent(s):
    return '    ' + s


def match_function_definition(body_lines):
    if not body_lines:
        return None
    line = body_lines[0].strip()
    line = line.strip()
    if line.startswith('def '):
        try:
            line = line[4:]
            i = line.index('(')
            j = line.index(')')
            name = line[:i].strip()
            args = [x.strip() for x in line[i+1:j].split(',')]
            return (name, args)
        except ValueError:
            pass
    return None


def sniff(body_lines):
    if body_lines:
        if match_function_definition(body_lines) is None:
            return CODE_SMELL
        else:
            return FUNCTION_SMELL
    return CODE_SMELL


def make_program(body_lines):
    smell = sniff(body_lines)
    if smell == CODE_SMELL:
        name = make_random_name('func')
        return Program(CODE_SMELL, name, [], None, list(body_lines))
    elif smell == FUNCTION_SMELL:
        name, args = match_function_definition(body_lines)
        return Program(FUNCTION_SMELL, name, args, None, list(body_lines))
    else:
        raise ValueError(smell)


def render(p):
    if p.smell == CODE_SMELL:
        header = 'def %s(%s):' % (p.name, ', '.join(p.args))
        body = [indent(line) for line in p.body_lines]
        if p.return_value:
            footer = indent('return %s' % p.return_value)
        else:
            footer = ''
        out = '\n'.join([header] + body + [footer])
        return out
    elif p.smell == FUNCTION_SMELL:
        return '\n'.join(p.body_lines)
    else:
        raise ValueError(p.smell)


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
    success = True
    if kind == 'Undefined variable':
        program_prime = program._replace(args=list(program.args) + [name])
    elif kind == 'Unused variable':
        program_prime = program._replace(return_value=name)
    else:
        program_prime = program
        success = False
    return program_prime, success


def query_pylint(program):
    module = TemporaryModule(program)
    out, err = pylint.epylint.py_run(module.filename, True)
    output = out.read()
    out.close()
    err.close()
    return map(parse_pylint_issue, output.split('\n'))


def graft(s, x):
    for i, c in enumerate(s):
        if not c.isspace():
            return s[:i] + x + s[i:]
    return s + x


def patch_last_line(program):
    if not program.body_lines:
        return program
    last_line = program.body_lines[-1]
    name = make_random_name('var')
    last_line_prime = graft(last_line, '%s = ' % name)
    body_lines = list(program.body_lines[:-1]) + [last_line_prime]
    return program._replace(body_lines=body_lines, return_value=name)


def debugged(program, max_attempts=8):
    if program.smell == FUNCTION_SMELL:
        return program
    for _ in xrange(max_attempts):
        issues = query_pylint(program)
        prev = program
        for issue in issues:
            program, success = repair(program, issue)
            if success:
                break
        if program == prev:
            break
    if program.return_value is None:
        program = patch_last_line(program)
    return program


def fix_doctest(line):
    if line.strip().startswith('>>> '):
        return ''
    else:
        return line

def fix_print(line):
    if line.strip().startswith('print '):
        return line.replace('print ', '')
    else:
        return line


def preprocessed(body_lines):
    return [fix_doctest(fix_print(line)) for line in body_lines]


def make_function_from_code(body_lines):
    return UsefulFunction(debugged(make_program(preprocessed(body_lines))))


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
    except Exception as e:
        sys.stderr.write(str(e) + '\n')
        return False

