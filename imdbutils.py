"""IMDB related functions. """

import re

class NoIMDBpyException(): pass
class BadIMDBIdException(): pass

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
    if s.isdigit(): return s
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

def ensure_good_imdb_id_interactive(entry):
    """Cleans the entry's imdb id. If it is not up to task, ask interactively
    better one. Return entry with updated info."""
    try:
        clean_id = clean_imdb_id(entry.imdb)
    except BadIMDBIdException:
        clean_id = '' # we'll ask for new one
    if not clean_id:
        try:
            entry.imdb = ask_imdb_interactive(entry.movie)
        except NoIMDBpyException:
            pass #keep dirty id
    else:
        entry.imdb = clean_id
    return entry
