"""Contains the class Entry."""

class Entry():
    """A movie diary entry."""
    def __init__(self, movie, rating=0, imdb='', message='',
            origdate='', update=''):
        self.movie = movie
        self.rating = rating or 0
        self.imdb = imdb or ''
        self.message = message or ''
        self.origdate = origdate or ''
        self.update = update or ''

    def __repr__(self):
        return "{0} ({1})".format(self.movie, self.rating)
