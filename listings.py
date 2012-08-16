"""Provide functions to list, filter and sort entries."""

import StringIO
import csv
from textwrap import fill

import data
import imdbutils
from entry import Entry

def format_compact(e):
    """print entry e compactly in one line."""
    return '({date}) {rating:<4}    {movie}'.format(
            date=e.origdate.strftime("%Y-%m-%d"),
            rating=e.rating, 
            movie=e.movie)

def format_full(e):
    """print entry e in a nice, full form."""
    formatstring = ('-'*78 + '\n'+
                    '{movie}\n'+
                    '{rating:<4} points       {imdburl}      ({longdate})\n'+
                    '{message}')
    if not e.imdb:
        imdburl = ' '*36  # apprx length of a would-be IMDB url
    else:
        imdburl = imdbutils.imdb_url(e.imdb)
    return formatstring.format(movie=e.movie,
            rating=e.rating,
            imdburl=imdburl,
            longdate=e.origdate.strftime("%Y-%m-%d %H:%M"),
            message=fill(e.message))

def format_csv(e):
    """print entry e in csv format."""
    output = StringIO.StringIO()
    writer = csv.writer(output)
    writer.writerow((e.movie, e.rating, e.origdate, e.message))
    return output.getvalue()

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

