#!/usr/bin/env python3
import argparse
import difflib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

__projectdir__ = Path(os.path.dirname(os.path.realpath(__file__)) + '')

# change color of text when printing
sys.path.append(str(__projectdir__ / Path('submodules/python-general-func/')))
from colors_basic import RED
from colors_basic import BLACK

# y/n single key input using getch
sys.path.append(str(__projectdir__ / Path('submodules/py-getch/getch/')))
from getch import getch


# Definitions:{{{1
namereplacedtext = 'replacedTEXThere'


# Argparse General Function for getting Files to Search/Replace on:{{{1
def argparse_fileinputs(filelist, files_asstring, files_infile, files_indir, files_inpwd):
    """
    Take a list of input choices from argparse and turn them into a file list for infrep

    filelist = list of files

    files_asstring = filenames inputted as a string with spaces in between (filenames should not have spaces)
    """
    import os
    import subprocess
    import sys

    numfileinputs = 0
    if filelist is not None:
        numfileinputs = numfileinputs + 1
    if files_asstring is not None:
        numfileinputs = numfileinputs + 1
    if files_infile is not None:
        numfileinputs = numfileinputs + 1
    if files_indir is not None:
        numfileinputs = numfileinputs + 1
    if files_inpwd is True:
        numfileinputs = numfileinputs + 1
    if numfileinputs != 1:
        raise ValueError('Multiple file input methods')

    if filelist is not None:
        return(filelist)

    if files_asstring is not None:
        return(files_asstring.split(' '))

    if files_infile is not None:
        if not os.path.exists(files_infile):
            raise ValueError('files_infile should be a filename. It does not exist. files_infile: ' + str(files_infile))
        with open(files_infile, 'r') as f:
            filenames = f.read().split()[: -1]
        return(filenames)

    if files_indir is not None or files_inpwd is True:
        if files_inpwd is True:
            files_indir = [os.path.abspath(os.getcwd())]
        filenames = []
        for root, dirs, files in os.walk(".", topdown=False):
            for name in files:
                filenames.append(os.path.join(root, name))

        return(filenames)


# Infrep Functions:{{{1
def infrep_main(tochangedictlist, confirmwhennochanges = True):
    """
    Each element is a dictionary.
    Mandatory elements: inputterm, outputterm, filenames.
    Optional elements: inputmethod, outputmethod

    inputmethod:
    inputmethod == None: inputterm is just text that I want to match
    inputmethod == 're': inputterm is a regex to compile i.e. I run re.compile(inputterm)
    inputmethod == 'recompiled': inputterm is already a compiled regex i.e. I already ran re.compile(inputterm)
    inputmethod == 'recompiledfunc': inputterm is a function with argument (filename) which returns an re.compile() argument

    outputmethod:
    outputmethod == None: outputterm is just text
    outputmethod == 'eval': outputterm is a string that I evaluate to get the output. Only needed if I want to include matched groups in the output. For example outputterm = 'match.group(1) + "hello"'
    outputmethod == 'func': outputterm is a function of (match, filename) that returns text
    """

    # dictionary containing file read from initial file with replacements
    replacedtextdict = {}
    # the replacements by filename
    outputlistdict = {}
    
    # this allows me to skip checks for all files - set to False at start
    allok = False
    # this allows me to see whether or not any changes have been made - set to False at start
    changemade = False

    for item in tochangedictlist:

        # Parse dict:{{{
        inputterm = item['inputterm']
        outputterm = item['outputterm']
        filenames = item['filenames']

        # this option determines the input method - see details in intro to function
        if 'inputmethod' in item:
            inputmethod = item['inputmethod']
        else:
            # just use a string
            inputmethod = None

        # this option determines the output method - see details in intro to function
        if 'outputmethod' in item:
            outputmethod = item['outputmethod']
        else:
            # just use a string
            outputmethod = None

        # End parse dict:}}}

        # verify filenames exists
        notexist = False
        for filename in filenames:
            if not os.path.isfile(filename):
                print('Filename: ' + str(filename) + ' does not exist.')
                notexist = True
        if notexist is True:
            sys.exit(1)

        # verify filenames are not duplicates
        notunique = set()
        seen = set()
        for x in filenames:
            if x in seen:
                notunique.add(x)
            else:
                seen.add(x)
                
        if len(notunique) > 0:
            raise ValueError('Duplicates in list of filenames: ' + ' '.join([str(notu) for notu in list(notunique)]))

        # get regex inputpattern
        if inputmethod == None:
            # input was basic text
            inputpattern = re.compile(re.escape(inputterm))
        if inputmethod == 're':
            # input method was a regex to input into re.compile
            inputpattern = re.compile(inputterm)
        if inputmethod == 'recompiled':
            # input method was a regex already inputted as re.compile
            inputpattern = inputterm
        if inputmethod == 'recompiledfunc':
            # input method was a function of the filename
            # since need filename do below
            None

        for filename in filenames:

            # update regex inputpattern if using filename
            if inputmethod == 'recompiledfunc':
                # need to convert the filename to a string in case it's inputted as a pathlib.Path
                inputpattern = inputterm(str(filename))

            # get text if not already used this file
            if filename not in replacedtextdict:
                with open(filename, 'r', encoding = 'latin-1') as f:
                    replacedtextdict[filename] = f.read()
                outputlistdict[filename] = []

            # if this is True, print the filename in red so I know I've not used it before
            firsttimefile = True
            # automatically accept changes on this file without checking for this pattern if True
            fileok = False
            # automatically reject changes on this file without checking for this pattern if True
            filenotok = False

            while True:

                text = replacedtextdict[filename]
                outputlist = outputlistdict[filename]
                replacementnumber = len(outputlist)

                # Getting input and output patterns:{{{
                match = inputpattern.search(text)
                if not match:
                    break
                originalterm = match.group(0)

                # getting text position of original term
                startbyte = match.span()[0]
                endbyte = match.span()[1]

                if outputmethod == None:
                    # outputmethod is basic text
                    outputpattern = outputterm
                if outputmethod == 'eval':
                    # outputmethod is to evaluate the outputterm
                    # so outputterm will be sth like 'match.group(1) + "hello"'
                    namespace = locals()
                    exec('outputpattern = ' + outputterm, globals(), namespace)
                    outputpattern = namespace['outputpattern']
                if outputmethod == 'func':
                    # need to convert to string in case filename is a pathlib.Path
                    outputpattern = outputterm(match, str(filename))

                textbefore = text[0:startbyte]
                textafter = text[endbyte:]
                # }}}


                # no point in asking about changes where nothing changes
                if originalterm == outputpattern:
                    # don't make replacement if thisok = 0
                    # but still need to do temporary replacement to ensure we don't continue to match this pattern so can't just continue on to next pattern
                    thisok = 0

                else:

                    # Get details to print:{{{

                    textbeforesplit = textbefore.split('\n')
                    textaftersplit = textafter.split('\n')

                    # line numbers:
                    linenumstart = len(textbeforesplit) - 1
                    linenumendbef = linenumstart + len(originalterm.split('\n')) - 1
                    linenumendaft = linenumstart + len(outputpattern.split('\n')) - 1

                    # match before:
                    curline = textbeforesplit[-1] + RED + originalterm + BLACK + textaftersplit[0]

                    # match after
                    postline = textbeforesplit[-1] + RED + outputpattern + BLACK + textaftersplit[0]

                    # End get details to print:}}}

                    # Print details:{{{

                    print('\n')

                    # old method - print separately
                    # print('Full lines before: ' + curline)
                    # print('Full lines after: ' + postline)

                    # new method - use difflib which is clearer with large files.
                    # this emphasizes places where the text has changed
                    diff = difflib.ndiff(curline.splitlines(), postline.splitlines())
                    print('\n'.join(diff))

                    if linenumstart == linenumendbef:
                        print('Line number: ' + str(linenumstart + 1))
                    else:
                        print('Line numbers: ' + str(linenumstart + 1) + '-' + str(linenumendbef + 1))

                    if firsttimefile is True:
                        print('Filename: ' + RED + str(filename) + BLACK)
                        firsttimefile = False
                    else:
                        print('Filename: ' + str(filename))
                    # End print details}}}

                    # Ask user what to do for each match:{{{
                    
                    thisok = False
                    if fileok is False and filenotok is False and allok is False:
                        inputagain = True
                        while inputagain is True:
                            inputagain = False
                            print("y/Y/n/N/A/Q: ")
                            inputted = getch()
                            if inputted == "y":
                                thisok = True
                            elif inputted == "n":
                                thisok = False
                            elif inputted == "Y":
                                fileok = True
                            elif inputted == "N":
                                filenotok = True
                            elif inputted == "A":
                                allok = True
                            elif inputted == "Q":
                                sys.exit(1)
                            else:
                                inputagain = True
                                print('Input one of the available letters.')

                    # }}}

                # Adjusting dicts with replaced text:{{{
                replacedtextdict[filename] = textbefore + namereplacedtext + str(replacementnumber) + 'num' + textafter

                if fileok is True or allok is True or thisok is True:
                    outputlistdict[filename].append(outputpattern)  # replace match with new term
                    changemade = True
                else:
                    outputlistdict[filename].append(originalterm)  # replace match with original term
                # }}}

    if changemade is True or confirmwhennochanges is True:
        inputagain = True
        while inputagain is True:
            print("\nProceed (y/n):")
            inputted = getch()
            if inputted == "y":
                inputagain = False
            elif inputted == 'n':
                sys.exit(1)
            else:
                inputagain = True
                print('Input one of the available letters.')

    for filename in replacedtextdict:
        if len(outputlistdict[filename]) == 0:
            continue
        text = replacedtextdict[filename]
        for i in range(len(outputlistdict[filename])):
            text = text.replace(namereplacedtext + str(i) + 'num', outputlistdict[filename][i])
        with open(filename, 'wb') as f:
            f.write(text.encode('latin-1'))


def infrep_argparse(filelist = None):
    """
    Always need to specify inputterm outputterm

    Which files do search and replace on:
    If put filelist as an argument at the start of the function, use those.
    Otherwise, need to give an argument specifying filenames to argparse.
    5 options - see below

    Can specify inputmethod/outputmethod:
    Note I can't use inputmethod== 'recompiled'/'recompiledfunc' or outputmethod=='func' since I need python to use them
    So I can only specify 'reinput' to get inputmethod == 're' and/or 'reoutput' to get outputmethod == 'eval'
    '--reboth' gives '--reinput --reoutput'

    Can specify that inputterm and outputterm are filenames and the files contain the actual inputterm/outputterm
    """

    # Get argparse:{{{

    parser = argparse.ArgumentParser()

    # Input/output:
    parser.add_argument("inputterm", type=str, help="What I will change from. If I want to match a backslash, I only need to write 1 backslash since I escape the text before applying it to a regex.")
    parser.add_argument("outputterm", type=str, help="What I will change to. If I want to output a backslash, i only need to write 1 backslash.")

    # Which files do the search and replace on:
    parser.add_argument("-f", "--filename", type=list, help="Input a list of filenames separated using -f file1 -f fil2")
    parser.add_argument("--files_asstring", type=str, help="input a string with filenames separated by single spaces")
    parser.add_argument("--files_infile", type=str, help="Input a filename which contains a list of filenames separated by newlines")
    parser.add_argument("-d", "--files_indir", type=list, help="Run on a directory. Can also run on multiple directories by specifying -d dir1 -d dir2")
    parser.add_argument("--files_inpwd", type=str, help="get all filenames in current directory")

    # inputmethod/outputmethod:
    parser.add_argument('--reinput', help = "inputterm that is inputted into re.compile (inputmethod = 're'). I need two backslashes if I want to write backslash, since when I input in the regex \\\\ -> \\", action = 'store_true')
    parser.add_argument('--reoutput', help = "outputterm is text that is executed. Allows me to input matches. Something like 'match.group(1) + \"hello\". (outputmethod = 'eval'). I need two backslashes if I want to write a backslash, since eval('\\\\') = '\\'", action = 'store_true')
    parser.add_argument("-r", "--reboth", action='store_true', help="Equivalent to setting --reinput --reoutput.")
    
    # if want to put inputterm/outputterm in a file rather than on command line:
    parser.add_argument("--fileboth", action='store_true', help="Both inputterm and outputterm are filenames which should be read to get the actual inputterm and outputterm. Equivalent to setting --fileinput --fileoutput.")
    parser.add_argument("--fileinput", action='store_true', help="inputterm is actually a filename which should be read to get the actual inputterm. If a newline is the last character, ignore this.")
    parser.add_argument("--fileoutput", action='store_true', help="outputterm is actually a filename which should be read to get the actual outputterm. If a newline is the last character, ignore this.")

    args = parser.parse_args()

    # End get argparse:}}}

    # Get files to do search and replace on:
    if filelist is None:
        filelist = argparse_fileinputs(args.filename, args.files_asstring, args.files_infile, args.files_indir, args.files_inpwd)

    # get inputmethod/outputmethod
    if args.reboth is True or args.reinput is True:
        inputmethod = 're'
    else:
        inputmethod = None
    if args.reboth is True or args.reoutput is True:
        outputmethod = 'eval'
    else:
        outputmethod = None

    # read files if inputterm and/or outputterm given in a file:
    if args.fileboth is True or args.fileinput is True:
        if not os.path.isfile(args.inputterm):
            raise ValueError('Since args.fileinput is True, args.inputterm should be a filename. args.inputterm: ' + str(args.inputterm))
        with open(args.inputterm) as f:
            inputterm = f.read()
        if inputterm[-1] == '\n':
            inputterm = inputterm[: -1]
        args.inputterm = inputterm
    if args.fileboth is True or args.fileoutput is True:
        if not os.path.isfile(args.outputterm):
            raise ValueError('Since args.fileoutput is True, args.outputterm should be a filename. args.outputterm: ' + str(args.outputterm))
        with open(args.outputterm) as f:
            outputterm = f.read()
        if outputterm[-1] == '\n':
            outputterm = outputterm[: -1]
        args.outputterm = outputterm

    # Call infrep:
    infrep_main([{'filenames': filelist, 'inputterm': args.inputterm, 'outputterm': args.outputterm, 'inputmethod': inputmethod, 'outputmethod': outputmethod}])


# Pathmv:{{{1
def getabspath(files):
    """
    Example:
    I want to be able to run pathmv hello.txt goodbye.txt to move hello.txt to goodbye.txt and change files referencing hello.txt to have goodbye.txt instead
    Or I want to be able to run pathmv hello.txt to dir1/hello.txt

    files is the list of inputs that I am giving to pathmv
    this function returns the full filenames that are being changed
    """

    # Files checks
    if len(files) < 2:
        print('Not enough files inputted i.e. need at least input and output file.')
        sys.exit(1)

    # Standardize files using abspath to remove / from end of directories and remove ../
    for i in range(len(files)):
        if os.path.isabs(files[i]) is True:
            files[i] = os.path.abspath(files[i])
        else:
            # if relative, do abspath of os.getenv('PWD') because this ensures that I maintain symlinks in the path
            files[i] = os.path.abspath(os.path.join(os.getenv('PWD'), files[i]))
        
    # Defining input and output files:
    fullinputpaths = files[0:len(files) - 1]
    outputfile = files[-1:][0]

    # Ensure input files exist
    for inputpath in fullinputpaths:
        if not os.path.exists(inputpath):
            raise ValueError('The following input file does not exist: ' + inputpath)

    # 2 cases: 1. moving files into directory 2. renaming file
    if os.path.exists(outputfile):
        # Must be directory that moving stuff into
        if not os.path.isdir(outputfile):
            raise ValueError('The following output file exists but is not a directory: ' + outputfile)
        for inputpath in fullinputpaths:
            if os.path.exists(os.path.join(outputfile, os.path.basename(inputpath))):
                raise ValueError('The following file that would be generated already exists: ' + os.path.join(outputfile, os.path.basename(inputpath)))

        fulloutputpaths = [os.path.join(outputfile, os.path.basename(inputpath)) for inputpath in fullinputpaths]

    else:
        # Must be changing name of file
        if len(fullinputpaths) > 1:
            print('You are attempting to change the name of multiple files to the same name.')
            sys.exit()
        if not os.path.isdir(os.path.dirname(os.path.abspath(outputfile))):
            print('You are attempting to rename a file to a file in a folder that does not exist.')
            sys.exit()

        fulloutputpaths = [outputfile]

    return(fullinputpaths, fulloutputpaths)


def pathmv_main(filestomove, filestoparse):
    """
    Function to check for any references to files that are being moved in filestoparse and replace those references
    If error during the text replacement part then do not actually move the files
    """

    fullinputpaths, fulloutputpaths = getabspath(filestomove)

    infreplist = []
    for i in range(len(fullinputpaths)):
        infreplist.append({'inputterm': fullinputpaths[i], 'outputterm': fulloutputpaths[i], 'filenames': filestoparse})

        # also replace files replace to the home directory
        # so if home directory is /home/user1 and moving /home/user1/dir1/1.txt to /home/user1/dir1/2.txt then also replace dir1/1.txt with dir1/2.txt
        # note this might not be ideal if moving common filenames in the home directory
        tildereplace = True

        if fullinputpaths[i].startswith(os.path.expanduser('~') + os.sep):
            tildeinput = fullinputpaths[i].replace(os.path.expanduser('~') + os.sep, '', 1)
        else:
            tildereplace = False
        
        if fulloutputpaths[i].startswith(os.path.expanduser('~') + os.sep):
            tildeoutput = fulloutputpaths[i].replace(os.path.expanduser('~') + os.sep, '', 1)
        else:
            tildereplace = False

        if tildereplace is True:
            infreplist.append({'inputterm': tildeinput, 'outputterm': tildeoutput, 'filenames': filestoparse})
                

    # do the file text replacement
    infrep_main(infreplist)

    # actually move the files
    for inputfile in filestomove[: -1]:
        shutil.move(inputfile, filestomove[-1])
        

def pathmv_argparse(filelist = None):

    parser = argparse.ArgumentParser()

    # Actual files that are being moved:
    parser.add_argument('files', nargs='*')

    # Which files do the search and replace on:
    parser.add_argument("-f", "--filename", type=list, help="Input a list of filenames separated using -f file1 -f fil2")
    parser.add_argument("--files_asstring", type=str, help="input a string with filenames separated by single spaces")
    parser.add_argument("--files_infile", type=str, help="Input a filename which contains a list of filenames separated by newlines")
    parser.add_argument("-d", "--files_indir", type=list, help="Run on a directory. Can also run on multiple directories by specifying -d dir1 -d dir2")
    parser.add_argument("--files_inpwd", type=str, help="get all filenames in current directory")

    args = parser.parse_args()


    # Get files to do search and replace on:
    if filelist is None:
        filelist = argparse_fileinputs(args.filename, args.files_asstring, args.files_infile, args.files_indir, args.files_inpwd)

    pathmv_main(args.files, filelist)

    
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


def testinfrep_argparse_aux():
    """
    Function to define argparse with filelist so I can test argparse when I have used the filelist argument.
    """
    infrep_argparse(filelist = [__projectdir__ / Path('testinfrep/test_simple.txt')])
    

def testinfrep_argparse():
    testinfrep_setup()

    # do replace
    subprocess.check_call([str(__projectdir__ / Path('run/testinfrep_argparse_aux.py')), '\\1cat.', '\\1dog.'])

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
    subprocess.check_call([str(__projectdir__ / Path('run/testinfrep_argparse_aux.py')), '\\\\([0-9])cat.', '"\\\\" + match.group(1) + "dog."', '--reboth'])

    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\1dog.\n2\n':
        raise ValueError('No match')
        

def testinfrep_argparse_filelist():
    """
    Test of each of the filelist input methods
    """
    testinfrep_setup()

    f1 = str(__projectdir__ / Path('testinfrep/test_simple.txt'))
    f2 = str(__projectdir__ / Path('testinfrep/test_funcboth.txt'))

    # --filename
    subprocess.check_call([str(__projectdir__ / Path('run/testinfrep_argparse_aux.py')), '\\1cat.', '\\2cat.', '--filename', f1, '--filename', f2])
    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\2cat.\n2\n':
        raise ValueError('No match')
        
    # --files_asstring
    subprocess.check_call([str(__projectdir__ / Path('run/testinfrep_argparse_aux.py')), '\\2cat.', '\\3cat.', '--files_asstring', f1 + f2])
    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\3cat.\n2\n':
        raise ValueError('No match')

    # --files_infile
    # create file containing f1, f2
    f3 = str(__projectdir__ / Path('testinfrep/filelist.txt'))
    with open(f3, 'w+') as f:
        f.write(f1 + '\n' + f2 + '\n')
    subprocess.check_call([str(__projectdir__ / Path('run/testinfrep_argparse_aux.py')), '\\3cat.', '\\4cat.', '--files_infile', f3])
    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\4cat.\n2\n':
        raise ValueError('No match')

    # --files_indir
    subprocess.check_call([str(__projectdir__ / Path('run/testinfrep_argparse_aux.py')), '\\4cat.', '\\5cat.', '--files_infile', str(__projectdir__ / 'testinfrep/copy/')])
    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\5cat.\n2\n':
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
    subprocess.check_call([str(__projectdir__ / Path('run/testinfrep_argparse_aux.py')), str(__projectdir__ / Path('testinfrep/input.txt')), str(__projectdir__ / Path('testinfrep/output.txt')), '--fileboth'])

    # verify worked
    with open(__projectdir__ / Path('testinfrep/test_simple.txt')) as f:
        text = f.read()
    if text != '1\n\\1dog.\n2\n':
        raise ValueError('No match')
        

def testinfrep_all():
    """
    Run all my test functions for infrep
    Need to run this function from run/testinfrep_all.py on the command line, since this file needs to call infrep_func.py when doing the argparse functions.

    Should be able to run without any raised errors. Otherwise, something likely is wrong.
    """
    print('\ntestinfrep_basic')
    testinfrep_basic()

    print('testinfrep_inputmethod_re_outputmethod_eval')
    testinfrep_inputmethod_re_outputmethod_eval()

    print('\ntestinfrep_inputmethod_recompiled')
    testinfrep_inputmethod_recompiled()

    print('\ntestinfrep_inputmethod_recompiledfunc_outputmethod_func')
    testinfrep_inputmethod_recompiledfunc_outputmethod_func()

    print('\ntestinfrep_argparse')
    testinfrep_argparse()

    print('\ntestinfrep_argparse_re')
    testinfrep_argparse_re()

    print('\ntestinfrep_argparse_filelist')
    testinfrep_argparse_filelist()

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


def testpathmv_argparse_aux():
    """
    Function to define argparse with filelist so I can test argparse when I have used the filelist argument.
    """
    pathmv_argparse(filelist = [__projectdir__ / Path('testpathmv/file1.txt')])
    

def testpathmv_argparse_basic():
    testpathmv_setup()

    subprocess.check_call([str(__projectdir__ / Path('run/testpathmv_argparse_aux.py')), str(__projectdir__ / Path('testpathmv/file1.txt')), str(__projectdir__ / Path('testpathmv/file2.txt'))])

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

    print('testpathmv_argparse_basic')
    testpathmv_argparse_basic()

