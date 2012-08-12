"""Contains the class Entry."""

class Entry():
    """A movie diary entry."""
    def __init__(self, movie, rating=0, imdb='', message='',
            origdate='', update=''):
        self.movie = movie
        self.rating = rating
        self.imdb = imdb
        self.message = message
        self.origdate = origdate
        self.update = update

    def __repr__(self):
        return "{0} ({1})".format(self.movie, self.rating)
