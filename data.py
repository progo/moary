"""Persistent data facilities.
We use SQlite 3 to store all these reviews."""

# CREATE TABLE movies
#      (movie text,
#       rating real,
#       imdb text,
#       message text,
#       origdate text,
#       updated text);

import sqlite3
DBFILE = "movies.db"

def store_entry(e):
    """push an Entry to the database."""
    with sqlite3.connect(DBFILE) as con:
        con.execute("INSERT INTO movies VALUES (?,?,?,?,?,?)",
                (e.movie,
                 e.rating,
                 e.imdb,
                 e.message,
                 e.origdate,
                 e.update))

