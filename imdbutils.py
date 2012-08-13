"""IMDB related functions. """

def imdb_url(imdbid):
    """Return an URL to a movie's IMDB page."""
    return "http://www.imdb.com/title/{0}/".format(imdbid)

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

