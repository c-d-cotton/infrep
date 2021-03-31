#!/usr/bin/env python3

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

__projectdir__ = Path(os.path.dirname(os.path.realpath(__file__)) + '/')

from infrep_func import infrep_main
from infrep_func import pathmv_main

# Infrep Test:{{{1
def testinfrep_setup():
    if os.path.isdir(__projectdir__ / Path('testinfrep')):
        shutil.rmtree(__projectdir__ / Path('testinfrep'))

    os.mkdir(__projectdir__ / Path('testinfrep'))

    with open(__projectdir__ / Path('testinfrep/test_simple.txt'), 'w+') as f:
        f.write('1\n\\1cat.\n2\n')
    with open(__projectdir__ / Path('testinfrep/test_funcboth.txt'), 'w+') as f:
        f.write('test_funcboth.txt:123\ntest_funcboth2.txt:124\n')
    

def testinfrep_basic():
    """
    Verifies the case where I just enter text strings works
    """
    testinfrep_setup()

    # do replace
    infrep_main([{'inputterm': '\\1cat.', 'outputterm': '\\1dog.', 'filenames': [__projectdir__ / Path('testinfrep/test_simple.txt')]}])

    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\1dog.\n2\n':
        raise ValueError('No match')
        

def testinfrep_inputmethod_re_outputmethod_eval():
    testinfrep_setup()

    # do replace
    # note that I could also write r'\\' which would be the same
    infrep_main([{'inputterm': '\\\\[0-9]([a-z]*)\.', 'outputterm': '"\\\\2" + match.group(1) + "."', 'filenames': [__projectdir__ / Path('testinfrep/test_simple.txt')], 'inputmethod': 're', 'outputmethod': 'eval'}])

    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\2cat.\n2\n':
        raise ValueError('No match')
        

def testinfrep_inputmethod_recompiled():
    testinfrep_setup()

    # do replace
    infrep_main([{'inputterm': re.compile('\\\\[0-9][a-z][a-z][a-z]\.'), 'outputterm': '\\1dog.', 'filenames': [__projectdir__ / Path('testinfrep/test_simple.txt')], 'inputmethod': 'recompiled'}])

    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\1dog.\n2\n':
        raise ValueError('No match')
        

def testinfrep_inputmethod_recompiledfunc_outputmethod_func():
    testinfrep_setup()

    # define functions
    def inputfunc(filename):
        pattern = str(os.path.basename(filename)) + ':' + '([0-9]*)'
        regex = re.compile(pattern)
        return(regex)
    def outputfunc(match, filename):
        return(str(os.path.basename(filename)) + '!' + match.group(1))

    # do replace
    infrep_main([{'inputterm': inputfunc, 'outputterm': outputfunc, 'filenames': [__projectdir__ / Path('testinfrep/test_funcboth.txt')], 'inputmethod': 'recompiledfunc', 'outputmethod': 'func'}])

    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_funcboth.txt')) as f:
        text = f.read()
    if text != 'test_funcboth.txt!123\ntest_funcboth2.txt:124\n':
        raise ValueError('No match')


def testinfrep_all():
    print('\ntestinfrep_basic')
    testinfrep_basic()

    print('testinfrep_inputmethod_re_outputmethod_eval')
    testinfrep_inputmethod_re_outputmethod_eval()

    print('\ntestinfrep_inputmethod_recompiled')
    testinfrep_inputmethod_recompiled()

    print('\ntestinfrep_inputmethod_recompiledfunc_outputmethod_func')
    testinfrep_inputmethod_recompiledfunc_outputmethod_func()


# Infrep Argparse Test:{{{1
def testinfrep_argparse():
    testinfrep_setup()

    # do replace
    subprocess.check_call([str(__projectdir__ / Path('run/infrep.py')), '\\1cat.', '\\1dog.', '-f', str(__projectdir__ / Path('testinfrep/test_simple.txt'))])

    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\1dog.\n2\n':
        raise ValueError('No match')
        

def testinfrep_argparse_re():
    """
    Do argparse test with groups.
    """
    testinfrep_setup()

    # do replace
    subprocess.check_call([str(__projectdir__ / Path('run/infrep.py')), '\\\\([0-9])cat.', '"\\\\" + match.group(1) + "dog."', '--reboth', '-f', str(__projectdir__ / Path('testinfrep/test_simple.txt'))])

    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\1dog.\n2\n':
        raise ValueError('No match')
        

def testinfrep_argparse_fileinput():
    """
    Test whether 
    """
    testinfrep_setup()

    with open(__projectdir__ / Path('testinfrep/input.txt'), 'w+') as f:
        f.write('\\1cat.')
    with open(__projectdir__ / Path('testinfrep/output.txt'), 'w+') as f:
        f.write('\\1dog.')

    # do replace
    subprocess.check_call([str(__projectdir__ / Path('run/infrep.py')), str(__projectdir__ / Path('testinfrep/input.txt')), str(__projectdir__ / Path('testinfrep/output.txt')), '--fileboth', '-f', str(__projectdir__ / Path('testinfrep/test_simple.txt'))])

    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\1dog.\n2\n':
        raise ValueError('No match')
        

def testinfrep_argparse_all():
    """
    Run all my test functions for infrep
    Need to run this function from run/testinfrep_all.py on the command line, since this file needs to call infrep_func.py when doing the argparse functions.

    Should be able to run without any raised errors. Otherwise, something likely is wrong.
    """
    print('\ntestinfrep_argparse')
    testinfrep_argparse()

    print('\ntestinfrep_argparse_re')
    testinfrep_argparse_re()

    print('\ntestinfrep_argparse_fileinput')
    testinfrep_argparse_fileinput()


# Pathmv Test:{{{1
def testpathmv_setup():
    # delete old version
    if os.path.isdir(__projectdir__ / Path('testpathmv')):
        shutil.rmtree(__projectdir__ / Path('testpathmv'))
    # make root directory
    os.mkdir(__projectdir__ / Path('testpathmv'))
    # add directory inside to move into
    os.mkdir(__projectdir__ / Path('testpathmv/dir1'))
    # add filename containing full path to that file
    with open(__projectdir__ / Path('testpathmv/file1.txt'), 'w+') as f:
        f.write(str(__projectdir__ / Path('testpathmv/file1.txt')) + '\n')

def testpathmv_basic():
    testpathmv_setup()
    
    pathmv_main([str(__projectdir__ / Path('testpathmv/file1.txt')), str(__projectdir__ / Path('testpathmv/file2.txt'))], [str(__projectdir__ / Path('testpathmv/file1.txt'))])

    with open(__projectdir__ / Path('testpathmv/file2.txt')) as f:
        text = f.read()
    if 'file2.txt' not in text:
        raise ValueError('Match failed')


def testpathmv_moveintodir():
    testpathmv_setup()
    
    pathmv_main([str(__projectdir__ / Path('testpathmv/file1.txt')), str(__projectdir__ / Path('testpathmv/dir1'))], [str(__projectdir__ / Path('testpathmv/file1.txt'))])

    with open(__projectdir__ / Path('testpathmv/dir1/file1.txt')) as f:
        text = f.read()
    if 'dir1/file1.txt' not in text:
        raise ValueError('Match failed')


def testpathmv_relpathinputs():
    """
    Verify that when relative paths are inputted into pathmv, it performs correctly
    """
    testpathmv_setup()
    
    pathmv_main([os.path.relpath(str(__projectdir__ / Path('testpathmv/file1.txt'))), os.path.relpath(str(__projectdir__ / Path('testpathmv/file2.txt')))], [os.path.relpath(str(__projectdir__ / Path('testpathmv/file1.txt')))])

    with open(__projectdir__ / Path('testpathmv/file2.txt')) as f:
        text = f.read()
    if 'file2.txt' not in text:
        raise ValueError('Match failed')


def testpathmv_relativereplace():
    """
    Verify that the code also matches and replace ~/paths as opposed to just /home/user1/paths
    """
    testpathmv_setup()
    # verify this test can be performed - only possible if this project is saved somewhere in the current user's home directory
    if not str(__projectdir__).startswith(os.path.expanduser('~') + os.sep):
        print('TEST NOT POSSIBLE for testpathmv_relativereplace. To do this test, project needs to be saved in user\'s home directory on a UNIX system.')
        return(None)

    # adjust writing in the file
    with open(__projectdir__ / Path('testpathmv/file1.txt'), 'w') as f:
        f.write(str(__projectdir__ / Path('testpathmv/file1.txt')).replace(os.path.expanduser('~') + '/', '', 1))
    
    pathmv_main([str(__projectdir__ / Path('testpathmv/file1.txt')), str(__projectdir__ / Path('testpathmv/file2.txt'))], [str(__projectdir__ / Path('testpathmv/file1.txt'))])

    with open(__projectdir__ / Path('testpathmv/file2.txt')) as f:
        text = f.read()
    if 'file2.txt' not in text:
        raise ValueError('Match failed')

def testpathmv_basic():
    testpathmv_setup()
    
    pathmv_main([str(__projectdir__ / Path('testpathmv/file1.txt')), str(__projectdir__ / Path('testpathmv/file2.txt'))], [str(__projectdir__ / Path('testpathmv/file1.txt'))])

    with open(__projectdir__ / Path('testpathmv/file2.txt')) as f:
        text = f.read()
    if 'file2.txt' not in text:
        raise ValueError('Match failed')


def testpathmv_all():
    print('\ntestpathmv_basic')
    testpathmv_basic()

    print('\ntestpathmv_moveintodir')
    testpathmv_moveintodir()

    print('\ntestpathmv_relpathinputs')
    testpathmv_relpathinputs()

    print('\ntestpathmv_relativereplace')
    testpathmv_relativereplace()

# Pathmv Argparse Test:{{{1
def testpathmv_argparse_basic():
    testpathmv_setup()

    subprocess.check_call([str(__projectdir__ / Path('run/pathmv.py')), str(__projectdir__ / Path('testpathmv/file1.txt')), str(__projectdir__ / Path('testpathmv/file2.txt')), '-f', str(__projectdir__ / Path('testpathmv/file1.txt'))])

    with open(__projectdir__ / Path('testpathmv/file2.txt')) as f:
        text = f.read()
    if 'file2.txt' not in text:
        raise ValueError('Match failed')


def testpathmv_all():
    print('testpathmv_argparse_basic')
    testpathmv_argparse_basic()


# Run:{{{1
if __name__ == "__main__":
    testinfrep_all()
    testinfrep_argparse_all()
    testpathmv_all()
    testpathmv_argparse_all()
