#!/usr/bin/env python3
import argparse
import difflib
import os
from pathlib import Path
import re
import shutil
import sys

__projectdir__ = Path(os.path.dirname(os.path.realpath(__file__)) + '')

# change color of text when printing
sys.path.append(str(__projectdir__ / Path('submodules/python-general-func/')))
from colors_basic import RED
from colors_basic import BLACK

# y/n single key input using getch
sys.path.append(str(__projectdir__ / Path('submodules/py-getch/getch/')))
from getch import getch

# argparse fileinputs
sys.path.append(str(__projectdir__ / Path('submodules/argparse-fileinputs/')))
from argparse_fileinputs import add_fileinputs
from argparse_fileinputs import process_fileinputs

# Definitions:{{{1
namereplacedtext = 'replacedTEXThere'


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

    parser = add_fileinputs(parser)

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
        filelist = process_fileinputs(args.filename, args.files_asstring, args.files_aslines, args.files_infile, args.files_indir, args.files_inpwd)

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

    parser = add_fileinputs(parser)

    args = parser.parse_args()


    # Get files to do search and replace on:
    if filelist is None:
        filelist = process_fileinputs(args.filename, args.files_asstring, args.files_aslines, args.files_infile, args.files_indir, args.files_inpwd)

    pathmv_main(args.files, filelist)

    
