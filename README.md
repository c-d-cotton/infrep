# Introduction
The idea behind this project is to give the user the option to check the results of in-file text replacements before they are made. Users may accept or reject individual/file-specific replacements. Replacements are only made once the user has had the option to observe all the replacements.

The primary function is `infrep` (in-file-replace). Infrep conducts text replacements over a set of files. The text to be replaced may be conducted by standard text or by python regular expressions.

A secondary function that builds upon `infrep` is `pathmv`. `Pathmv` checks whether, when files are moved or renamed, the user also wishes to change the paths of the moved/renamed files in the text of another set of files. The default is only for full paths to be replaced but relative paths may be replaced as well. The move/rename only takes place once the user has had the option to observe all the potential path replacements.
# Setup
Run setup_submodules.sh to add in required submodules.

# Infrep Details
Infrep on the command line:

Basic case:
- `infrep` *inputterm* *outputterm*
This will look for any occurrences of *inputterm* in files in the specified files (see details on how to specify files below) and give the user the option to replace it with *outputterm*.

Which files run on:
- Specify in code: I define my own infrep_argparse function and define which files I want to do the replace in there.
-f, --filename: Input a list of filenames separated using -f file1 -f file2
--files_asstring: input a string with filenames separated by single spaces
--files_infile: Input a filename which contains a list of filenames separated by newlines
-d, --files_indr: Run on a specified directory. Can also run on multiple directories by specifying -d dir1, -d dir2.
--files_inpwd: get all filenames in current directory

Run infrep --help to get additional options to do regex replace and input the terms to search/replace from a filename.

Various tests/examples are given in infrep_func.py.

# Pathmv Details
`pathmv` may be run in the same way as you would specify files for `mv` i.e.:
1. `pathmv` *filestomove* *newdirectory*
2. `pathmv` *oldname* *newname*

It conducts the move but it also replaces any absolute and (when relevant) home-directory relative filenames with the new location of the files. For example, if you do pathmv /home/user/file1.txt dir1/ then it will make the following replacements in the specified files:
1. /home/user/file1.txt -> /home/user/dir1/file1.txt
2. file1.txt -> dir1/file1.txt

It only does 2. in the case where all the moved files start and end in the home directory of the user running the script.

The files where the search/replace is done are specified in the same way as for infrep.

Various tests/examples are given in infrep_func.py.

# Confirmation 
Each replacement will be listed with the filename (given in red if it or the input has changed from the last replacement), the line numbers in the file where the input pattern was to begin, the line(s) to be replaced (with the input pattern given in red) and the lines that will replace them (with the output pattern given in red).

The options given to the user are as follows:
- y: Accept the single change.
- Y: Accept this change and all future changes in this file.
- n: Reject the single change.
- N: Reject this change and all future changes in this file.
- A: Accept this and all future changes.
- Q: Exit with error.

