import setuptools

long_description = """
# PlesicDB

PlesicDB stores data in **JSON** format.

Plesic uses folders as database.

You need to specify a directory to store all databases in that directory. In that folder there are chunks of collections.

Every database collection-chunk size is default to (2*CPU_CORES)

Usage
======

Simple program
--------------

Below is an example of how to import plesicdb and creating database and collection.

```
>>> from plesicdb import Plesic

>>> pl = Plesic("/home/mydbs")   # directory to store all databases in it.

>>> db = pl["myapp"]             # Getting database
>>> db.chunksize = 16            # This will work

>>> users = db["users"]          # Users collection
>>> db.chunksize = 16            # This won't work
```

If you want to change `chunksize` you need to set it before you get the collection.
"""

setuptools.setup(
    name="PlesicDB",
    version="1.0.2",
    author="Harkishan Khuva",
    author_email="harkishankhuva02@gmail.com",
    description="Document(JSON) oriented database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hakiKhuva/plesicdb",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    package_dir={"plesicdb": "plesicdb"},
    packages=["plesicdb"],
    python_requires=">=3.6",
    license="MIT"
)
