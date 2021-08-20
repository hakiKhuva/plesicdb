"""
PlesicDB
~~~~~~~~

PlesicDB is simple module to do your personal projects.

PlesicDB stores data in JSON format.

Plesic uses folders as database.
You need to specify a directory to store all databases in that directory.
In that folder there are chunks of collections.
Every database collection chunk size is default to (2*CPU_CORES).


Example-

>>> from plesicdb import Plesic

>>> pl = Plesic("/home/mydbs")   # directory to store all databases in it.

>>> db = pl["myapp"]             # Getting database
>>> db.chunksize = 16            # This will work

>>> users = db["users"]          # Users collection
>>> db.chunksize = 16            # This won't work


If you want to change chunksize you need to set it before you get the collection.
"""

from ._base import Plesic
from .__about__ import __name__, __version__, __author__, __author_email__, __license__
from ._utils import date

__all__ = ('Plesic','date')
