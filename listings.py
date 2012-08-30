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
                    '{rating:<4} points       {imdburl}      ({longdate})'+
                    '{message}')
    if not e.imdb:
        imdburl = ' '*36  # apprx length of a would-be IMDB url
    else:
        imdburl = imdbutils.imdb_url(e.imdb)

    # massage messages to a nice form.
    if e.message:
        msglines = e.message.split('\n\n')
        msglines = [fill(line) for line in msglines]
        message = '\n' + '\n\n'.join(msglines)
    else:
        message = ''

    return formatstring.format(movie=e.movie,
            rating=e.rating,
            imdburl=imdburl,
            longdate=e.origdate.strftime("%Y-%m-%d %H:%M"),
            message=message)

def format_csv(e):
    """print entry e in csv format."""
    output = StringIO.StringIO()
    writer = csv.writer(output)
    writer.writerow((e.movie, e.rating, e.origdate, e.message))
    return output.getvalue().rstrip('\r\n ')

FORMATTERS = {'compact': format_compact,
              'full': format_full,
              'csv': format_csv}

def do_list(args):
    """CLI func to call when doing subtask "list". """
    fmtfunc = FORMATTERS[args.format]

    filters = {}
    order = ""

    if args.title: filters["movie LIKE ?"] = "%" + args.title + "%"
    if args.message: filters["message LIKE ?"] = "%" + args.message + "%"
    if args.ge: filters["rating >= ?"] = args.ge
    if args.gt: filters["rating > ?"] = args.gt
    if args.le: filters["rating <= ?"] = args.le
    if args.lt: filters["rating < ?"] = args.lt

    if args.sort_name: order = "movie"
    elif args.sort_rating: order = "rating"
    if args.asc:
        order = order or "rowid"
        order = order + " ASC"
    elif args.desc:
        order = order or "rowid"
        order = order + " DESC"

    db = data.DataFacilities(dbfile=args.db_file)
    try:
        for e in db.get_entries(filters, order):
            print fmtfunc(e)
    except IOError:
        # can be caused by premature pipe closes (head etc)
        return
