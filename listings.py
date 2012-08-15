"""Provide functions to list, filter and sort entries."""

import data
import imdbutils
from entry import Entry

from textwrap import fill


def format_compact(e):
    """print entry e compactly in one line."""
    return '{movie},   {rating},     ({origdate})'.format(**vars(e))

def format_full(e):
    """print entry e in a nice, full form."""
    formatstring = ('-'*78 + '\n'+
                    '{movie}\n'+
                    '{rating:<3} points,  {imdburl}   ({origdate})\n'+
                    '{message}')
    if not e.imdb:
        imdburl = ' '*36  # apprx length of a would-be IMDB url
    else:
        imdburl = imdbutils.imdb_url(e.imdb)
    return formatstring.format(movie=e.movie,
            rating=e.rating,
            imdburl=imdburl,
            origdate=e.origdate,
            message=fill(e.message))

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

