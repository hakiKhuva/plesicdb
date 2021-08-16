import random
import string

strGen = lambda length:"".join([random.choice(string.ascii_letters+string.digits) for _ in range(length)])
