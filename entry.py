"""Contains the class Entry."""

from datetime import datetime

class Entry():
    """A movie diary entry."""
    def __init__(self, movie, rating=0, imdb='', message='',
            origdate='', update=''):
        self.movie = movie
        self.rating = rating or 0
        self.imdb = imdb or ''
        self.message = message or ''
        self.origdate = origdate or datetime.now()
        self.update = update or self.origdate

    def __repr__(self):
        return "'{0}', r:{1}, i:'{2}'".format(
                self.movie, self.rating, self.imdb)
