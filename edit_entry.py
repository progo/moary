"""This module contains functions to edit data, invoke the user interactively
about it."""

import re
import os

def parse_file(f):
    """read the temp file containing rate and other stuff. Return a dict with
    the data."""

    def clean_line(s):
        """remove initial label from the beginning of the line"""
        return re.sub(r"\A.*?: ?", "", s.strip()).strip()

    f.seek(0)
    parsed = {}
    # now just go through the file format
    parsed["movie"] = clean_line(f.readline())
    parsed["rating"] = clean_line(f.readline())
    parsed["imdb"] = clean_line(f.readline())
    f.readline()
    parsed["message"] = f.read().strip()
    return parsed

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
    import imdb
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
            number = int(raw_input(
                "Which of these titles you had in mind? [0 to skip] "))
            if number == 0: return ""
            if number < 0 or number > ITEMS: raise ValueError()
            return ids[number - 1]
        except ValueError:
            print "Sorry, not understood..."

def fill_in_form(data):
    """given movie dict, return filled-out form string for editors."""
    initial_message = (
        "Movie: {movie}\n" +
        "Rating: {rating}\n" +
        "IMDB: {imdb}\n" +
        "----- Review -----\n" +
        "{message}")
    if not data:
        data = {"movie": "", "rating": "", "imdb": "", "message": ""}
    return initial_message.format(**data)

def edit_data_interactive(data):
    """given the movie dict, invoke editor on user to edit the entry. Return
    the dict with possibly updated info."""
    from subprocess import call
    import tempfile
    EDITOR = os.environ['EDITOR'] or "ed"

    with tempfile.NamedTemporaryFile() as tempfile:
        tempfile.write(fill_in_form(data))
        tempfile.flush()
        call([EDITOR, tempfile.name])
        data = parse_file(tempfile)

        if not data["movie"]:
            print "No movie name provided."

    clean_id = clean_imdb_id(data["imdb"])
    if not clean_id:
        data["imdb"] = ask_imdb_interactive(data["movie"])
    else:
        data["imdb"] = clean_id
 
    return data
