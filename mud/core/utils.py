import random
import string

randstr = lambda sz: ''.join(random.choice(string.letters) for i in xrange(sz))

