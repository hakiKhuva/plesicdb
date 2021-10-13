import json
import os
import hashlib
import uuid
import types
import typing
import datetime
from ._helpers import strGen


class Collection:
    """
        This class internally used by Plesic.

        Methods:
            insert       : Insert record in collection
            insertMany   : Insert multiple records in collection
            find         : find record(s) from collection
            remove       : remove record(s)
            update       : update record(s)
            exists       : check if record exists or not
    """
    _busy = False
    __read_attempt = 250
    def __init__(self,**kwargs) -> None:
        self.__name = kwargs["name"]
        self.__dbPath = kwargs["dbStats"][0]
        self.__dbName = kwargs["dbStats"][1]
        self.__statsManager = kwargs["statsManager"]
        self.__chunkSize = kwargs["chunkSize"]


    @property
    def __chunks(self):
        """
        return chunks of collection
        """
        try:
            return self.__statsManager("r").get(self.__name).get("chunks")
        # if chunk not present in stats.json
        except AttributeError:
            raise UnboundLocalError(
                "Cannot read collection! If you've dropped the collection create new instance and tryagain."
            ) from None


    def insert(self, data : dict) -> typing.Any:
        """
            Insert data in collection
            =========================

            Args:
                data : record must be dictionary

            Returns:
                Id of record
        """

        # checking type of data

        if type(data) != dict:
            raise TypeError("Insert data must be in dict format.")

        # cannot insert empty dictionary
        if data == {}:
            raise ValueError("Cannot insert empty dict.")

        # insert data contains _id or not
        if not data.get("_id"):
            # if not create one
            # data["_id"] = hashlib.md5(str(datetime.datetime.now().isoformat()+strGen(10)+"".join(list(data.keys()))).encode()).hexdigest()
            data["_id"] = str(uuid.uuid4())
        else:
            # checking if _id used before in another record
            if self.find(lambda x:x["_id"] == data['_id']) != []:
                raise ValueError(
                    "Record _id cannot be same!"
                )

        while self._busy:
            continue
        # getting running collection which means last
        try:
            runningCollection = self.__chunks[-1]
        # if IndexError because all collections are deleted but collection exists
        except IndexError:
            # create new collection-chunk
            _data = self.__statsManager("r")
            if self.__name not in _data.keys() or len(_data.get(self.__name).get("chunks")) == 0:
                newName = hashlib.md5(str(strGen(15)+datetime.datetime.now().isoformat()).encode()).hexdigest()
                _data[self.__name] = {
                    "chunks" : [newName],
                }
                try:
                    with open(os.path.join(self.__dbPath,self.__dbName,newName+".json"),"w") as f:
                        f.write(json.dumps({
                            self.__name : []
                        }))
                except PermissionError:
                    raise PermissionError(
                        "Cannot create new collection-chunk."
                    )
            self.__statsManager("w",_data)
            runningCollection = self.__chunks[-1]

        # full path to collection-chunk
        pathToCollection = os.path.join(self.__dbPath,self.__dbName,runningCollection+".json")

        # checking if collection-chunk size is larger than chunksize
        if(os.path.getsize(pathToCollection) > self.__chunkSize*1024):
            newName = hashlib.md5(str(strGen(15)+datetime.datetime.now().isoformat()).encode()).hexdigest()
            pathToCollection = os.path.join(self.__dbPath,self.__dbName,newName+".json")
            # if it is exists
            while os.path.exists(pathToCollection):
                newName = hashlib.md5(str(strGen(15)+datetime.datetime.now().isoformat()).encode()).hexdigest()
                pathToCollection = os.path.join(self.__dbPath,self.__dbName,newName+".json")
            statsdata = self.__statsManager("r")
            statsdata[self.__name]["chunks"].append(newName)
            self.__statsManager("w",statsdata)
            runningCollection = self.__chunks[-1]
            pathToCollection = os.path.join(self.__dbPath,self.__dbName,runningCollection+".json")
            try:
                with open(pathToCollection, "w") as f:
                    f.write(json.dumps({
                        self.__name : []
                    }))
            except PermissionError:
                raise PermissionError(
                    "Cannot create new collection-chunk."
                )
            del statsdata


        _data = self.__manage(runningCollection, 'r')

        # appending insert data
        _data.append(data)

        self.__manage(runningCollection, "w", data=_data)

        return data.pop("_id")


    def insertMany(self, data: list) -> list:
        """
            Insert multiple records
            =======================

            Args:
                data : data must be in list format contains records in dictionary format.

            Returns:
                list of record's id
        """
        if(type(data) != list):
            raise ValueError("insert_many data must be in list format.")
        if data == []:
            return []
        _ids = []
        i = 0
        # adding record one by one
        while i < len(data):
            _id = self.insert(data[i])
            _ids.append(_id)
            i+=1
        return _ids


    def find(self, exp :types.LambdaType = None) -> list:
        """
            Find records from collection
            ============================

            Args:
                exp : lambda or regular function, None will return all records of collection.

            Returns:
                list of records
        """

        # checking if exp type is valid
        if type(exp) not in (type(None), types.LambdaType, types.FunctionType):
            raise TypeError(
                f"Cannot find records with expression type {type(exp).__name__}."
            )

        while self._busy:
            continue
        # if exp is None return all records
        if exp == None:
            records = []
            for chunk in self.__chunks:
                data = self.__manage(chunk, "r")
                records += data
            return records

        # finding records with expression : function
        chunks = self.__chunks
        result = []
        for chunk in chunks:
            # reading chunk
            _data = self.__manage(chunk, "r")
            # iterating records
            for record in _data:
                try:
                    # if condition true
                    if exp(record):
                        result.append(record)
                # records are stored in JSON format
                # so some records contain key and some not
                # if not Python will raise KeyError.
                except KeyError:
                    continue
        return result


    @property
    def read_attempt(self):
        """
            read_attempt is maximum number to read collection chunk if json.decoder.JSONDecodeError raised.
        """
        return self.__read_attempt


    @read_attempt.setter
    def read_attempt(self,new_val):
        if type(new_val) not in (int,):
            raise TypeError("read_attempt value must be an integer.")
        if new_val < 25:
            raise ValueError("read_attempt value must be greater than 25.")
        self.__read_attempt = new_val


    def __manage(self, chunk, mode, data=None):
        """
            collection manage to read and write chunks
        """
        if mode == "r":
            # Busy check --------
            while self._busy:
                continue

            self._busy = True

            try:
                with open(os.path.join(self.__dbPath,self.__dbName,chunk+".json"), "r") as f:
                    data = f.read()
                    try:
                        data = json.loads(data)
                    except json.decoder.JSONDecodeError:
                        _done = 0
                        for _ in range(self.__read_attempt):
                            try:
                                f.seek(0)
                                data = f.read()
                                data = json.loads(data)
                            except json.decoder.JSONDecodeError:
                                continue
                            else:
                                _done = 1
                                break
                        if _done != 1:
                            self._busy = False
                            raise ValueError(
                                "Collection chunk contains invalid JSON data."
                            ) from None

                    self._busy = False

                    return data.get(self.__name)
            except FileNotFoundError:
                self._busy = False
                raise FileNotFoundError(
                    "Unable to read collection-chunk."
                ) from None

        elif mode == "w":
            # Busy check --------
            while self._busy:
                continue

            self._busy = True

            try:
                with open(os.path.join(self.__dbPath,self.__dbName,chunk+".json"), "r+") as f:
                    try:
                        f.seek(0)
                        f.write(json.dumps({
                            self.__name : data
                        }))
                    except TypeError:
                        self._busy = False
                        raise TypeError(
                            "Cannot convert data into JSON."
                        ) from None
                    else:
                        f.truncate()
            except FileNotFoundError:
                self._busy = False
                raise FileNotFoundError(
                    "Unable to write changes to collection-chunk."
                ) from None

            self._busy = False


    def remove(self,exp :types.LambdaType = None) -> list:
        """
            Remove records from collection
            ==============================

            Args:
                exp : lambda or regular function, None if you want to truncate.

            Returns:
                function : removed records id
                None : None
        """

        # check exp type
        if type(exp) not in (type(None), types.LambdaType, types.FunctionType):
            raise TypeError(
                f"Cannot find records with expression type {type(exp).__name__}."
            )

        while self._busy:
            continue
        # truncate collection
        if exp == None:
            for chunk in self.__chunks:
                _data = self.__statsManager("r")
                _data[self.__name]["chunks"].remove(chunk)
                self.__statsManager("w",_data)
                # remove file
                try:
                    os.remove(os.path.join(self.__dbPath,self.__dbName, chunk+".json"))
                # Permission denied
                except PermissionError:
                    raise PermissionError(
                        f"Cannot remove collection:{self.__name} chunk:{chunk}"
                    ) from None
                # if file not found
                except FileNotFoundError:
                    raise FileNotFoundError(
                        "Database dropped or collection document manually removed!"
                    ) from None
            return None

        result = []
        for chunk in self.__chunks:
            _data = self.__manage(chunk, "r")
            # changed default to None
            changed = 0
            for record in _data:
                try:
                    if exp(record):
                        result.append(record.get("_id"))
                        _data.remove(record)
                        # changed to 1 because collection-chunk data updated
                        changed = 1
                except TypeError:
                    continue
                except KeyError:
                    continue

            # if only data removed then write changes else do not
            if changed:
                # if collection chunk == []
                if _data == []:
                    _stats = self.__statsManager("r")
                    _stats[self.__name]["chunks"].remove(chunk)
                    self.__statsManager("w",_stats)
                    os.remove(os.path.join(self.__dbPath,self.__dbName,chunk+".json"))
                else:
                    self.__manage(chunk,"w",_data)
        return result


    def update(self, exp :types.LambdaType, update_data: dict) -> list:
        """
            Update records of collection
            ============================

            Args:
                exp         : lambda or regular function
                update_data : update data in dictionary


            Returns:
                updated records id


            Example:
                {
                    "name" : "abcd",
                    "age" : 18,
                    "info" : {
                        "addr" : {
                            "country" : "India"
                        }
                    },
                    "_id" : 1
                }

                To change the age to 19-
                    update(lambda d:d["_id"] == 1, {"age":19})

                what if you want to change country
                    update(lambda d:d["_id"] == 1, {"info.addr.country": None})

                use (.) operator

                if key doesn't exists then it will be created.

                update(lambda d:d["_id"] == 1, {"info.addr.pincode": None})
        """
        # checking exp type
        if type(exp) not in (types.LambdaType, types.FunctionType):
            raise TypeError(
                f"Cannot find records with expression type {type(exp).__name__}."
            )

        while self._busy:
            continue

        # getting all keys, values of update data
        keys = [key.split(".") for key in update_data.keys()]
        values = list(update_data.values())

        # update ids
        update_ids = []

        # function to update records
        def recursion(record, key, value,num=0):
            try:
                num += 1
                if num < len(key):
                    recursion(record[key[num-1]], key, value,num=num)
                else:
                    record[key[num-1]] = value
            except KeyError as e:
                record[key[num-1]] = {}
                recursion(record[key[num-1]], key, value,num=num)

        # iterating chunks
        for chunk in self.__chunks:
            _chunkUpdated = 0
            # reading chunk
            _data = self.__manage(chunk,"r")
            # iterating records
            for record in _data:
                try:
                    # if true
                    if exp(record):
                        _chunkUpdated = 1
                        update_ids.append(record.get("_id"))
                        _i = 0
                        # setting all keys and values
                        while _i < len(keys):
                            recursion(record,keys[_i],values[_i])
                            _i += 1
                # if keyerror
                except KeyError:
                    continue
            # if chunk update then write it
            if _chunkUpdated:
                self.__manage(chunk, "w", _data)

        return update_ids


    def exists(self,exp:types.LambdaType) -> int:
        """
            Record exists or not
            ====================

            Args:
                exp : lambda or regular function

            Returns:
                1 if exists else 0

            if you want to check for user exists or not:
                :- exists(lambda d:d["email"] == "abcd@abcd.com")

            if you want to check for user and password:
                :- exists(lambda d:d["email"] == "abcd@abcd.com" and d["password"] == "12345678")

        """
        if type(exp) not in (types.LambdaType, types.FunctionType):
            raise TypeError(
                f"Cannot find records with expression type {type(exp).__name__}."
            )
        while self._busy:
            continue
        chunks = self.__chunks
        for chunk in chunks:
            _data = self.__manage(chunk, "r")
            for record in _data:
                try:
                    if exp(record):
                        return 1
                except KeyError:
                    pass
        return 0


    def __repr__(self):
        return(
            "<"
            f"Collection name=\"{self.__name}\" "
            f"database=\"{self.__dbName}\" "
            f"chunksize={self.__chunkSize}"
            ">"
        )
