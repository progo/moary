"""Persistent data facilities.
We use SQlite 3 to store all these reviews."""

import os, sys
import sqlite3

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

