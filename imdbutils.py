"""IMDB related functions. """

import re
from entry import Entry

FORCE_SKIP = False # Ignore IMDBpy in JWD. Never set this outside testing!

class NoIMDBpyException(Exception): pass
class BadIMDBIdException(Exception): pass

def imdb_url(imdbid):
    """Return an URL to a movie's IMDB page."""
    return "http://www.imdb.com/title/tt{0}/".format(imdbid)

def clean_imdb_id(s):
    """Clean IMDB identifiers. Return all-numeric presentation (as string).
    Take urls and short ids and real ids. These forms are supported:
        http://www.imdb.com/title/tt0075784/
        tt0075784
        0075784
    Raise BadIMDBIdException if the input can't be read well.
    """
    if not s: return '' # pass-through for empty id's
    s = s.strip(" /")
    s = re.sub(r'\A.+title\/tt', '', s)
    s = s.replace("tt", "")
    if s.isdigit(): return s.zfill(7)
    raise BadIMDBIdException()

def ask_imdb_interactive(moviename):
    """run query to IMDB and ask user the movie id. Return the id."""
    try:
        import imdb
    except ImportError:
        raise NoIMDBpyException()
    ia = imdb.IMDb()
    ITEMS = 7
    run = ia.search_movie(moviename, results=ITEMS)
    counter = 1
    ids = []
    for movie in run:
        print "[" + str(counter) + "]   " + movie["long imdb title"]
        ids.append(movie.movieID)
        counter += 1
    if counter == 1:
        print "No movie matches."
        return ''
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

def query_imdb_name(imdb_id):
    """Query IMDB for movie name. Will raise NoIMDBpyException if necessary."""
    try:
        import imdb
    except ImportError:
        raise NoIMDBpyException()

    clean_id = clean_imdb_id(imdb_id)

    ia = imdb.IMDb()
    movie = ia.get_movie(clean_id)
    return movie["title"]

def is_valid_id(imdb_id):
    """Simple predicate to validate IMDB id."""
    try:
        clean_imdb_id(imdb_id)
        return True
    except BadIMDBIdException:
        return False

def just_work_dammit(entry, oldentry=None, skip=False):
    """Get an entry with old ID and movie name, clean it and return good IMDB
    id. Use 'skip' to go non-interactive. Don't raise anything."""

    try: import imdb
    except ImportError:
        skip = True

    if FORCE_SKIP: skip=True # for testing

    oldentry = oldentry or Entry('')

    if skip:
        if is_valid_id(entry.imdb):
            new_id = clean_imdb_id(entry.imdb)
        else:
            new_id = oldentry.imdb or ''
    else:
        if is_valid_id(entry.imdb) and entry.imdb != '':
            new_id = clean_imdb_id(entry.imdb)
        else:
            new_id = ask_imdb_interactive(entry.movie)

    return new_id

#
#   When skipping IMDB (or IMDBpy missing)
#   ======================================
#
#             | old ok   | old empty
#   ----------+----------+----------
#   new ok    | CHANGE   | CHANGE
#   new empty | CHANGE   | CHANGE
#   new inval | KEEP     | KEEP
#
#
#   When going interactive
#   ======================
#
#             | old ok   | old empty
#   ----------+----------+----------
#   new ok    | CHANGE   | CHANGE
#   new empty | ASK      | ASK
#   new inval | ASK      | ASK
#
