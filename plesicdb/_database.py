import os
import json
import multiprocessing
import datetime
import hashlib
from ._collection import Collection
from ._helpers import strGen

class Database:
    """
        This class internally used by Plesic.

        Methods:
            drop    : remove/delete collection
            export  : export database to JSON file

        Property:
            chunksize : maximum size of collection-chunk
    """

    __CPU_CORES = multiprocessing.cpu_count()

    # Busy
    _busy = False

    # default chunk size
    __chunkSize = 2*__CPU_CORES

    def __init__(self,**kwargs) -> None:
        self.__name = kwargs["name"]
        self.__dbPath = kwargs["dbPath"]
        self.__preload()


    @property
    def chunksize(self):
        """
            Chunksize is used to limit collection chunk size.
        """
        return self.__chunkSize

    @chunksize.setter
    def chunksize(self,value):
        if type(value) not in (int,float):
            raise ValueError("chunksize must be an integer or float.")
        # value must be > 1
        if value < 1:
            raise ValueError(
                f"chunksize must be >= 1"
            )
        # print warning if chunksize is large
        elif value > 4*self.__CPU_CORES:
            print(f"Setting chunksize to {value} but large document read takes more time.\nrecommended : [4 - {4*self.__CPU_CORES}]")
        self.__chunkSize = value


    def __preload(self):
        """
            Preload method to check if stats.json exists or not

            Create if it's not
        """
        if( not os.path.exists(os.path.join(self.__dbPath,self.__name,"stats.json"))):
            with open(os.path.join(self.__dbPath,self.__name,"stats.json"), "w") as f:
                try:
                    f.write(json.dumps({}))
                except PermissionError:
                    raise PermissionError("Cannot create stats file for database.")
        self.__statsPointer = open(os.path.join(self.__dbPath,self.__name,"stats.json"), "r+")



    def _statsManage(self, mode, data=None):
        """
            stats.json document manage function
        """
        while self._busy:
            continue

        if(mode == "w"):
            self._busy = True

            self.__statsPointer.seek(0)
            try:
                self.__statsPointer.write(json.dumps(data))
            except FileNotFoundError:
                self._busy = False
                raise Exception(
                    "Unable to access stats file - may be database has been removed."
                )

            self.__statsPointer.truncate()
            self._busy = False

        elif(mode == "r"):
            self._busy = True

            self.__statsPointer.seek(0)
            try:
                statsData = json.loads(self.__statsPointer.read())
            except FileNotFoundError:
                self._busy = False
                raise Exception(
                    "Unable to access stats file - may be database has been removed."
                )
            except json.decoder.JSONDecodeError:
                _doneAtAll = 0
                for _ in range(5):
                    self.__statsPointer.seek(0)
                    try:
                        statsData = json.loads(self.__statsPointer.read())
                    except FileNotFoundError:
                        self._busy = False
                        raise Exception(
                            "Unable to access stats file - may be database has been removed."
                        )
                    except json.decoder.JSONDecodeError:
                        continue
                    else:
                        _doneAtAll = 1
                        break

                if _doneAtAll == 0:
                    self._busy = False
                    raise ValueError(
                        "Unable to get database data - stats file manually modified."
                    )
            self._busy = False
            return statsData


    def __getitem__(self, collectionName:str):
        if type(collectionName) != str:
            raise TypeError("Collection name must be type of str.")
        if len(collectionName) < 2:
            raise ValueError("Collection name must contains min two characters.")
        if len(collectionName) > 50:
            raise ValueError("collection name can contains max 50 characters.")

        # Getting data of stats.json
        data = self._statsManage("r")

        # checking if collection is already created or not
        if collectionName not in data.keys() or len(data.get(collectionName).get("chunks")) == 0:
            # using randomstring of 15 char, current datetime and md5 so all chunks have unique name.
            newName = hashlib.md5(str(strGen(15)+datetime.datetime.now().isoformat()).encode()).hexdigest()

            data[collectionName] = {
                "chunks" : [newName],
            }
            try:
                with open(os.path.join(self.__dbPath,self.__name,newName+".json"),"w") as f:
                    f.write(json.dumps({
                        collectionName : []
                    }))
            # permission denied
            except PermissionError:
                raise PermissionError(
                    "Cannot create collection document."
                )
            except FileNotFoundError:
                raise FileNotFoundError(
                    "Database dropped or collection document manually removed!"
                ) from None
        # writing new data to stats.json
        self._statsManage("w",data)
        return Collection(
            name = collectionName,
            dbStats = (self.__dbPath, self.__name),
            statsManager = self._statsManage,
            chunkSize = self.__chunkSize
        )


    def drop(self,collection):
        """
            drop database collection
            ========================

            Args:
                collection : collection name you want to drop

            Usage:
                :- drop(collectionname)

            Returns:
                1 if collection exists and dropped successfully.
                0 if not.
        """
        _data = self._statsManage("r")
        if collection in _data.keys():
            name = collection
            collection = self[collection]
            collection.remove()
            _data.pop(name)
            self._statsManage("w",_data)
            return 1
        return 0



    def export(self,destination:str):
        """
            Export whole database to one JSON file
            ======================================

            Args:
                destination : path where to save file
        """
        # check if path exists and it is dir or file
        if not os.path.exists(destination) or not os.path.isdir(destination):
            raise NotADirectoryError("destination must be a dir.")

        # data to export
        _d = {
            "_name" : self.__name,
            "_collections" : list(self._statsManage("r").keys()),
            "data" : {}
        }

        # appending collection data to data in _d
        for collection in _d.get("_collections"):
            _d["data"][collection] = self[collection].find()

        _time = datetime.datetime.now().isoformat()
        # new name of file
        name = f"{self.__name}--{hashlib.md5(str(_time).encode()).hexdigest()}.json"
        try:
            with open(os.path.join(destination,name), "w") as f:
                f.write(json.dumps(_d))
        # Permission denied
        except PermissionError:
            raise PermissionError(
                "Cannot save the document : Permission denied"
            ) from None


    def __repr__(self):
        return (
            "<"
            f"Database name=\"{self.__name}\" "
            f"path=\"{self.__dbPath}\" "
            f"chunksize={self.__chunkSize}"
            ">"
        )
