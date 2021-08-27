import os
import json
import shutil
import datetime
from plesicdb._database import Database

class Plesic:
    """
    Main class of PlesicDB
    ======================

    Args:
        databaseDirPath : database directory where your all databases will be created.

    Methods:
        drop    : remove/delete database.
        info    : get databases, collections, collection-chunks count, memory used.
        IMPORT  : import database exported by PlesicDB

    Properties:
        dir : database directory path
    """

    def __init__(self,databaseDirPath : str) -> None:
        """
            databaseDirPath : where to store all databases
        """
        # check directory exists or not
        self.__checkPath(databaseDirPath)
        # setting database path to __dbDir
        self.__dbDir = databaseDirPath

        self.__preload()


    def __preload(self):
        """
            Preload function create journal file.

            This journal file contains databases and it's created time.
        """
        # checking if journal exists
        if(not os.path.exists(os.path.join(self.__dbDir,'journal.json'))):
            try:
                with open(os.path.join(self.__dbDir,'journal.json'),"w") as f:
                    f.write(json.dumps({}))
            # If permission denied
            except PermissionError:
                raise PermissionError(
                    f"Cannot create journal at path[{self.__dbDir}]. Makesure user have permission."
                ) from None
        # setting as class variable
        self.__journalPointer = open(os.path.join(self.__dbDir,'journal.json'),"r+")


    def __checkPath(self,path):
        """
            Check for directory exists or not..
        """
        try:
            truth = os.path.exists(path)
        except TypeError:
            raise ValueError(
                "Cannot set NoneType to database dir"
            ) from None
        if not truth:
            raise TypeError(
                f"Cannot set database directory\nremoved or not exists : {path}"
            )



    @property
    def dir(self):
        """
            dir property to get/set database directory
        """
        return self.__dbDir


    @dir.setter
    def dir(self,path):
        self.__checkPath(path)
        self.__dbDir = path
        self.__preload()



    def __getitem__(self, databaseName : str) -> Database:
        if type(databaseName) != str:
            raise TypeError("database name must be type of str.")
        if len(databaseName) < 2:
            raise ValueError("database name must contains min two characters.")
        if len(databaseName) > 50:
            raise ValueError("database name can contains max 50 characters.")

        # checking if journal exists or not
        if(not os.path.exists(os.path.join(self.__dbDir,'journal.json'))):
            self.__preload()
        # creating joined path - contains database directory path and database name
        JOINED = os.path.join(self.__dbDir, databaseName)
        # checking if database exists or not
        if not os.path.exists(JOINED):
            try:
                os.mkdir(JOINED)
            # If permission denied
            except PermissionError:
                raise PermissionError(
                    f"Cannot create database[{databaseName}] at {self.__dbDir}."
                ) from None
            # reading data of journal
            data = self.__journalManage("r")
            # adding dbname and create time as record
            data[databaseName] = datetime.datetime.now().isoformat()
            # writing changes
            self.__journalManage("w",data)

        database = Database(
            name = databaseName,
            dbPath = self.__dbDir
        )
        return database




    def __journalManage(self, mode, data=None):
        """
            Method to read,write data in journal.
        """
        if(mode == "w"):
            self.__journalPointer.seek(0)
            self.__journalPointer.write(json.dumps(data))
            self.__journalPointer.truncate()
        elif (mode == "r"):
            self.__journalPointer.seek(0)
            try:
                return json.loads(self.__journalPointer.read())
            except:
                pass



    def drop(self,databaseName : str) -> int:
        """
            Drop database
            =============

            Args:
                databaseName : database name you want drop

            Usage:
                :- drop("dbName")

            Returns:
                :: 1 if dropped
                :: 0 if not dropped
        """
        data = self.__journalManage("r")
        if databaseName not in data.keys():
            return 0

        if(os.path.exists(os.path.join(self.__dbDir,databaseName))):
            try:
                shutil.rmtree(os.path.join(self.__dbDir,databaseName))
            except:
                raise PermissionError(
                    "Cannot remove database folder!"
                )
            data = self.__journalManage("r")
            data.pop(databaseName)

            self.__journalManage("w",data)
            return 1
        return 0


    def IMPORT(self,filename_with_path:str):
        """
            IMPORT exported JSON database file
            ==================================

            Args:
                filename_with_path : file that contains exported data
        """
        # checking file exists or not
        if not os.path.exists(filename_with_path) or not os.path.isfile(filename_with_path):
            raise FileNotFoundError(
                f"File not found : {filename_with_path}"
            )

        # loading file data
        try:
            _d = json.loads(open(filename_with_path,'r').read())
        # if data not in JSON format.
        except json.decoder.JSONDecodeError:
            raise ValueError(
                "Cannot get data from file [Invalid JSON data]."
            ) from None
        # if file not found
        except FileNotFoundError:
            raise FileNotFoundError(
                f"File not found at {filename_with_path}"
            )

        # Getting all data
        name = _d.get("_name")
        collections = _d.get("_collections")
        data = _d.get("data")

        if not name or not collections or not data:
            raise ReferenceError(
                "Document does not contain database name,collection and it's data."
            )

        _data = self.__journalManage("r")
        # if database already exists raise Exception
        if name in _data.keys():
            raise Exception(
                f"DATABASE already exists at path : {self.__dbDir}."
            )

        # checking for collection all collection data is present or not
        for c in collections:
            if c not in data.keys():
                raise Exception(
                    f"COLLECTION:{c} not found in document."
                )

        db = self[name]
        for c in collections:
            col = db[c]
            col.insertMany(data.get(c))


    def info(self,createTime="isoformat"):
        """
        Get details about your databases
        ================================

        Args:
            createTime : "isoformat" or 'else'
                       : database create date in "isoformat" or "datetime.datetime" object
        """
        returndata = {}
        totalMemory = 0
        d = self.__journalManage("r")
        for db in d:
            if os.path.exists(os.path.join(self.__dbDir,db)):
                if createTime == "isoformat":
                    date = d[db]
                else:
                    date = datetime.datetime.fromisoformat(d[db])

                returndata[db] = {
                    "created" : date,
                    "memory" : 0
                }

        for db in d:
            dbmemory = 0
            temp_d = self[db]
            statsdata = temp_d._statsManage("r")
            returndata[db]["collections"] = list(statsdata.keys())
            returndata[db]["data"] = {}
            for c in returndata[db]["collections"]:
                returndata[db]["data"][c] = {}

                returndata[db]["data"][c]["chunk_count"] = len(temp_d._statsManage("r")[c].get("chunks"))
                memory = 0
                for chunk in temp_d._statsManage("r")[c].get("chunks"):
                    memory += os.path.getsize(os.path.join(self.__dbDir,db,chunk+".json"))

                returndata[db]["data"][c]["memory"] = memory
                dbmemory += memory

            statsMemory = os.path.getsize(os.path.join(self.__dbDir,db,"stats.json"))
            returndata[db]["statsMemory"] = statsMemory
            returndata[db]["memory"] = dbmemory
            totalMemory += dbmemory+statsMemory

        returndata["totalMemory"] = totalMemory

        return returndata



    def __repr__(self):
        return(
        "<"
        f"Plesic databaseDir=\"{self.__dbDir}\""
        ">"
        )
