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
             origdate text,
             updated text);"""

DBFILE = "movies.db"
DATADIR = "."

def establish_connection():
    dbfileloc = os.path.join(sys.path[0], DATADIR, DBFILE)
    con = sqlite3.connect(dbfileloc)
    con.execute(CREATE)
    con.commit()
    return con

def store_entry(e):
    """push an Entry to the database."""
    with establish_connection() as con:
        con.execute("INSERT INTO movies VALUES (?,?,?,?,?,?)",
                (e.movie, e.rating, e.imdb, e.message, e.origdate, e.update))
        con.commit()

def get_last():
    """get and return the last entry saved."""
    with establish_connection() as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM movies ORDER BY rowid DESC LIMIT 1")
        return Entry(*cur.fetchone())

def get_all_entries():
    """return all entries from db."""
    # TODO wasteful...
    with establish_connection() as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM movies")
        return [Entry(*row) for row in cur.fetchall()]

def __get_last_rowid(con):
    """get the last rowid. Uses an existing connection."""
    cur = con.cursor()
    cur.execute("SELECT rowid FROM movies ORDER BY rowid DESC LIMIT 1")
    return cur.fetchone()[0]

def set_entry(e, row_id=None):
    """set given entry with new values. If row_id not given, replace the last
    one."""
    with establish_connection() as con:
        if not row_id: row_id = __get_last_rowid(con)
        con.execute("UPDATE movies SET "+
                "movie=?,"+ "rating=?,"+ "imdb=?,"+ "message=?,"+ "updated=?"+
                " WHERE rowid=?",
                (e.movie, e.rating, e.imdb, e.message, e.update, row_id))
        con.commit()

def delete_entry(row_id=None):
    """delete given entry, or the last one by default."""
    with establish_connection() as con:
        cur = con.cursor()
        if not row_id: row_id = __get_last_rowid(con)
        cur.execute("DELETE FROM movies WHERE rowid=?", (row_id,))
        con.commit()
