import sys
import bz2
import base64

write=sys.stdout.write

for name in sys.argv[1:]:
    contents=bz2.compress(open(name).read())
    write('import bz2, base64\n')
    write('exec bz2.decompress(base64.b64decode(\'')
    write(base64.b64encode((contents)))
    write('\'))\n')
