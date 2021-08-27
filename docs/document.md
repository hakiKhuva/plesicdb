# PlesicDB

PlesicDB stores data in **JSON** format.

Plesic uses folders as database.

You need to specify a directory to store all databases in that directory. In that folder there are chunks of collections.

Every database collection-chunk size is default to (2*CPU_CORES)

* [Usage](#usage)
* [Change log](#changelog)


v1.0.1
======

*read_attempt* property
-----------------------

read_attempt is for how many times a chunk should be read if json.decoder.JSONDecodeError raised

```python
>>> from plesicdb import Plesic, date
>>> from datetime import datetime

>>> pl = Plesic("/home/mydbs")
>>> db = pl["myapp"]
>>> users = db["users"]

>>> # read_attempt default value is 250
>>> users.read_attempt = 500
```



v1.0.0
======

*date* function
---------------

```python
>>> from plesicdb import Plesic, date
>>> from datetime import datetime

>>> pl = Plesic("/home/mydbs")
>>> db = pl["myapp"]
>>> users = db["users"]

>>> record = {
    "name" : "Haki",
    "account created date" : date(datetime.now())
}
>>> # record will be
>>> # {
>>> #    "name": "Haki",
>>> #    "account created date": {
>>> #        "year": 2021,
>>> #        "month": 8,
>>> #        "day": 20,
>>> #        "hour": 9,
>>> #        "minute": 13,
>>> #        "second": 17,
>>> #        "m_second": 858142
>>> #    }
>>> # }

>>> users.insert(record)
```



Usage
======

Simple program
--------------

Below is an example of how to import plesicdb and creating database and collection.

```python
>>> from plesicdb import Plesic

>>> pl = Plesic("/home/mydbs")   # directory to store all databases in it.

>>> db = pl["myapp"]             # Getting database
>>> db.chunksize = 16            # This will work

>>> users = db["users"]          # Users collection
>>> db.chunksize = 16            # This won't work
```

If you want to change `chunksize` you need to set it before you get the collection.


Insert record
-------------
When you insert record in collection function will return `_id` of record.

If `_id` provided in `dict` then it will be used else uuid4 function will be used.
```python
>>> # Using users collection

>>> insertdata = {
    "name" : "Abc def",
    "info" : {
        "email" : None,
        "addr" : {
            "country" : "India"
        }
    }
}

>>> _id = users.insert(insertdata) # storing id of record in _id variable

>>> print("record id :",_id)
```

```
# Output
record id : 15c99800-f480-4099-948c-b6e409edcefd
```

To insert multiple records
--------------------------
When you insert multiple records in collection function will return `_id list`.
```python
>>> import random

>>> insertdata = [
    {
        "name" : "Abc def",
        "age" :  random.randint(15,25)
    },
    {
        "name" : "Ghi jkl",
        "age" :  random.randint(15,25)
    },
    {
        "name" : "Mno pqr",
        "age" :  random.randint(15,25)
    }
]

>>> users.insertMany(insertdata)
```
```
# Output
['d0d66f10-d50f-48fc-8779-ee2a12965b19', '719bacc7-7be0-43d2-985a-36309fe38142', '4d1a2dd6-f5d4-4ceb-af8d-b495cde22e7d']
```


Search records
--------------
When you search for record pass lambda function or regular function that returns true.

To get all records call without passing function.
```python
>>> users.find(lambda x:x["_id"] == '15c99800-f480-4099-948c-b6e409edcefd')

>>> # To get all records - users.find()
```

```
# Output
[{'name': 'Abc def', 'info': {'email': None, 'addr': {'country': 'India'}}, '_id': '15c99800-f480-4099-948c-b6e409edcefd'}]
```


Remove records
--------------
If you want to clear all records from collection call without passing function.

Pass lambda or regular function that returns true.

Function will return list of `_id` of removed records.
```python
>>> # truncate collection
>>> users.remove()

>>> # remove specific records
>>> users.remove(lambda x:x["_id"] == '15c99800-f480-4099-948c-b6e409edcefd')
```

```
# Output
['15c99800-f480-4099-948c-b6e409edcefd']
```


Update records
--------------
Update records will return `_id` of updated records.

Pass lambda or regular function that returns true.
```python
>>> users.update(lambda x:x["_id"] == 'd0d66f10-d50f-48fc-8779-ee2a12965b19',{"name" : "Stu vw"})
```
```
# Output
['d0d66f10-d50f-48fc-8779-ee2a12965b19']
```


Update records - nested dict
----------------------------
If you have added data in nested format then you can update it using `.`(dot) as shown below.

If key doesn't exists it will be created.
```python
>>> record = {
    "name" : "Haki",
    "info" : {
        "addr" : {
            "country" : None
        }
    },
    "_id" : 1
}

>>> users.insert(record)

>>> users.update(lambda x:x["_id"] == 1,{"info.addr.country" : "India"})
```



Check record exists or not
--------------------------
This function will return 1 if exists else 0.
```python
>>> records = [
    {
        "username" : "user1",
        "password" : '25d55ad283aa400af464c76d713c07ad' # 12345678
    },
    {
        "username" : "user2",
        "password" : '81dc9bdb52d04dc20036dbd8313ed055' # 1234
    },
    {
        "username" : "user3",
        "password" : '6531401f9a6807306651b87e44c05751' # 09876
    }
]

>>> users.insertMany(records)
```

```python
>>> users.exists(lambda x:x["username"] == "user1")
```
```
# Output
1
```

```python
>>> users.exists(lambda x:x["username"] == "user10")
```
```
# Output
0
```



Drop collection
---------------
return 1 if dropped else 0
```python
>>> db.drop("users")
```
```
# Output
1
```


Export database
---------------
Export database to one JSON file.

JSON file will be generated at path with db data.
```python
>>> db.export("/home/mydbs/")
```


Import database
---------------
Import database that exported before
```python
>>> pl.IMPORT("/home/mydbs/myapp--7cf27d12adadbb2778e04b7a98097c84.json")
```



Drop database
-------------
return 1 if dropped else 0
```python
>>> pl.drop("myapp")
```
```
# Output
1
```

Get info about your databases
-----------------------------
return database, memory, stats.json memory, collections, collection-chunks count, memory
```python
>>> import json
>>> print(json.dumps(pl.info(),indent=4))
```

```JSON
# Output
{
    "app": {
        "created": "2021-08-09T10:34:55.244625",
        "memory": 4150488,
        "collections": [
            "users",
            "data"
        ],
        "data": {
            "users": {
                "chunk_count": 996,
                "memory": 4150476
            },
            "data": {
                "chunk_count": 1,
                "memory": 12
            }
        },
        "statsMemory": 35937
    },
    "test": {
        "created": "2021-08-09T14:14:50.644847",
        "memory": 19464728,
        "collections": [
            "data"
        ],
        "data": {
            "data": {
                "chunk_count": 4668,
                "memory": 19464728
            }
        },
        "statsMemory": 168070
    },
    "chat-app": {
        "created": "2021-08-11T11:34:39.070612",
        "memory": 2165,
        "collections": [
            "users",
            "openchats",
            "openchat"
        ],
        "data": {
            "users": {
                "chunk_count": 1,
                "memory": 1244
            },
            "openchats": {
                "chunk_count": 1,
                "memory": 921
            },
            "openchat": {
                "chunk_count": 0,
                "memory": 0
            }
        },
        "statsMemory": 150
    },
    "totalMemory": 23821538
}
```

Plesic methods
================
method | description | args | args type | return
---------|-----------|-------|------------|---------
IMPORT | Create new database from exported database JSON file | filename_with_path | str | None
drop | drop database | databaseName | str |  1 or 0



Database methods
================

method | description | args | args type | return
---------|-----------|-------|------------|---------
drop | drop collection | collection | str | 1 or 0
export | export database to single JSON file | destination | str | None


Collection methods
==================

method | description | args | args type | return
---------|-----------|-------|------------|---------
insert | Insert record | data | dict | id of record
insertMany | Insert multiple records | data | list | id of records in list
find | search records in collection | exp | lambda/ regular function or None | list of records
exists | check record exists or not | exp | lambda/ regular function | 1 or 0
remove | remove records | exp | lambda/ regular function | list of removed records' id
update | update records | exp, data | lambda/ regular function, dict | list of updated records' id


Properties
==========
name | from | description
-----|------|-------------
dir | Plesic | dir property to get/set database directory
chunksize | Database | Chunksize is used to limit collection chunk size
read_attempt | Collection | read_attempt is maximum number to read collection chunk if json.decoder.JSONDecodeError raised


Changelog
=========

v1.0.1
------
* Added read_attempt property

v1.0.0
------
* Added date function to save date and datetime object in JSON format.
* Added busy property to database and collection so there is low chance of getting json decoder error
* Forgot to add value in f.seek - line 290 - v0.0.1.


v0.0.1
------
* First release
