"""Provide functions to list, filter and sort entries."""

import data
import imdbutils
from entry import Entry


def format_compact(e):
    """print entry e compactly in one line."""
    return '{movie},   {rating},     ({origdate})'.format(**vars(e))

def format_full(e):
    """print entry e in full form."""
    return ('---------------------------------------------------\n'+
            '{movie}\n'+
            '{rating} points,   {imdburl}     ({origdate})\n'+
            '{message}').format(movie=e.movie, rating=e.rating,
                        imdburl=imdbutils.imdb_url(e.imdb),
                        origdate=e.origdate, message=e.message)

def format_csv(e):
    """print entry e in csv format."""
    return '{movie};{rating};{origdate}'.format(**vars(e))

def do_list(args):
    """CLI func to call when doing subtask "list". """
    if args.format == 'compact':
        fmtfunc = format_compact
    elif args.format == 'full':
        fmtfunc = format_full
    elif args.format == 'csv':
        fmtfunc = format_csv

    for e in data.get_all_entries():
        print fmtfunc(e)

