"""Persistent data facilities.
We use SQlite 3 to store all these reviews."""

import os, sys
import sqlite3

from entry import Entry

CREATE = """CREATE TABLE IF NOT EXISTS movies
            (movie text,
             rating real,
             imdb text,
             message text,
             origdate timestamp,
             updated timestamp);"""

DBFILE = "movies.db"
DATADIR = "."

class EmptyDBException(): pass

class DataFacilities():
    """Wrapped data interfaces in a class. (A closure would have done.)"""

    def __establish_connection(self, datadir, dbfile):
        dbfileloc = os.path.join(sys.path[0], datadir, dbfile)
        if dbfile == ':memory:': dbfileloc = ':memory:'
        con = sqlite3.connect(dbfileloc,
                detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        con.execute(CREATE)
        con.commit()
        return con

    def __init__(self, datadir=None, dbfile=None):
        """Init sqlite3 connection. Use dbfile in datadir."""
        datadir = datadir or DATADIR
        dbfile = dbfile or DBFILE
        self.con = self.__establish_connection(datadir, dbfile)

    def store_entry(self, e):
        """push an Entry to the database."""
        self.con.execute("INSERT INTO movies VALUES (?,?,?,?,?,?)",
                (e.movie, e.rating, e.imdb, e.message, e.origdate,
                    e.update))
        self.con.commit()

    def get_last(self):
        """get and return the last entry saved. Throw EmptyDBException if
        nothing comes out."""
        cur = self.con.cursor()
        cur.execute("SELECT * FROM movies ORDER BY rowid DESC LIMIT 1")
        lastrow = cur.fetchone()
        if not lastrow: raise EmptyDBException()
        return Entry(*lastrow)

    def get_entries(self, filtermap=None, order=None):
        """Return a list of Entries from the DB that satisfy the given
        conditions in filtermap. Sort by conditions given in order."""
        cur = self.con.cursor()
        query = "SELECT * FROM movies"
        arguments = []
        if filtermap:
            query = query + " WHERE " + " AND ".join(filtermap.keys())
            arguments.extend(filtermap.values())
        if order:
            query = query + " ORDER BY " + order
        cur.execute(query, arguments)
        return [Entry(*row) for row in cur.fetchall()]

    def get_all_entries(self):
        """return all entries from db."""
        # TODO wasteful...
        cur = self.con.cursor()
        cur.execute("SELECT * FROM movies")
        return [Entry(*row) for row in cur.fetchall()]

    def __get_last_rowid(self):
        """get the last rowid.""" 
        cur = self.con.cursor()
        cur.execute("SELECT rowid FROM movies ORDER BY rowid DESC LIMIT 1")
        lastid = cur.fetchone()
        if not lastid: raise EmptyDBException()
        return lastid[0]

    def set_entry(self, e, row_id=None):
        """set given entry with new values. If row_id not given, replace the
        last one."""
        if not row_id: row_id = self.__get_last_rowid()
        self.con.execute("UPDATE movies SET "+
                "movie=?,"+ "rating=?,"+ "imdb=?,"+ "message=?,"+ "updated=?"+
                " WHERE rowid=?",
                (e.movie, e.rating, e.imdb, e.message, e.update, row_id))
        self.con.commit()

    def delete_entry(self, row_id=None):
        """delete given entry, or the last one by default."""
        cur = self.con.cursor()
        if not row_id: row_id = self.__get_last_rowid()
        cur.execute("DELETE FROM movies WHERE rowid=?", (row_id,))
        self.con.commit()
