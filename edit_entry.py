"""This module contains functions to edit data, invoke the user interactively
about it."""

import re
import subprocess
import os
import time

from entry import Entry

class UserCancel():
    """Exception when user decides to cancel the interactive scenes."""
    pass

def parse_file(f):
    """read the temp file containing rate and other stuff. Return an Entry."""

    def clean_line(s):
        """remove initial label from the beginning of the line"""
        return re.sub(r"\A.*?: ?", "", s.strip()).strip()

    f.seek(0)

    # now just go through the file format
    data = Entry(movie=unicode(clean_line(f.readline())))
    data.rating = clean_line(f.readline())
    data.imdb = clean_line(f.readline())
    f.readline()
    data.message = unicode(f.read().strip())
    return data

def clean_imdb_id(s):
    """Clean IMDB identifiers. Return all-numeric presentation (as string).
    Take urls and short ids and real ids. These forms are supported:
        http://www.imdb.com/title/tt0075784/
        tt0075784
        0075784
    Return empty if s doesn't appear to be valid at all.
    """
    s = s.strip(" /")
    s = s.replace("http://www.imdb.com/title/", "")
    s = s.replace("tt", "")
    if s.isdigit():
        return s
    return ""

def ask_imdb_interactive(moviename):
    """run query to IMDB and ask user the movie id. Return the id."""
    try:
        import imdb
    except ImportError:
        return ""
    ia = imdb.IMDb()
    ITEMS = 7
    run = ia.search_movie(moviename, results=ITEMS)
    counter = 1
    ids = []
    for movie in run:
        print "[" + str(counter) + "]   " + movie["long imdb title"]
        ids.append(movie.movieID)
        counter += 1
    while True:
        try:
            user_input = raw_input(
                "Which of these titles you had in mind? [0 to skip] ")
            if user_input == '': #default
                number = 1
            else:
                number = int(user_input)
            if number == 0: return ""
            if number < 0 or number > ITEMS: raise ValueError()
            return ids[number - 1]
        except ValueError:
            print "Sorry, not understood..."

def ensure_good_imdb_id(entry):
    """Cleans the entry's imdb id. If it is not up to task, ask interactively
    better one. Return entry with updated info."""
    clean_id = clean_imdb_id(entry.imdb)
    if not clean_id:
        entry.imdb = ask_imdb_interactive(entry.movie)
    else:
        entry.imdb = clean_id
    return entry

def fill_in_form(data):
    """given movie dict, return filled-out form string for editors."""
    initial_message = (
        "Movie: {0}\n" +
        "Rating: {1}\n" +
        "IMDB: {2}\n" +
        "----- Review -----\n" +
        "{3}")
    if not data:
        return initial_message.format('','','','\n')
    return initial_message.format(data.movie, data.rating, data.imdb,
            data.message)

def edit_data_interactive(data, skip_imdb=False):
    """given the Entry, invoke editor on user to edit the entry. Return the
    Entry with possibly updated info."""
    import tempfile
    EDITOR = os.environ['EDITOR'] or "ed"

    with tempfile.NamedTemporaryFile() as tempfile:
        tempfile.write(fill_in_form(data))
        tempfile.flush()
        subprocess.call([EDITOR, tempfile.name])
        data = parse_file(tempfile)

    if not data.movie:
        raise UserCancel()

    if not skip_imdb:
        data = ensure_good_imdb_id(data)

    # update timestamps
    data.update = time.ctime()
 
    return data
