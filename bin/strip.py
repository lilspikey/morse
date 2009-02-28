import fileinput
import re
import sys

# remove comments and blank-lines etc

blank = re.compile(r'^\s*$')
comments = re.compile(r'\s#.*?$')
reindent = re.compile(r'^(?:\s{4})+')

write=sys.stdout.write

for line in fileinput.input():
    line=comments.sub('',line)
    if not blank.match(line):
        # replace 4 space indent with 1 space indent
        line=reindent.sub(lambda m: ' ' * (len(m.group(0))/4),line)
        write(line)