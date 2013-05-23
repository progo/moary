"""Provide functions to list, filter and sort entries."""

import StringIO
import csv
import math
from textwrap import fill

import data
import imdbutils
from entry import Entry

COLORS = {"Movie": '\033[1;36m',
        "graph-good": '\033[1;32m',
        "graph-decent": '\033[1;34m',
        "graph-bad": '\033[1;30m',
        "END": '\033[0m'}
NOCOLORS = dict((key, '') for key,_ in COLORS.items())
Colors = COLORS

def with_color(colname, string):
    return Colors[colname] + string + Colors['END']

def color_stars(stars, color, begin, end):
    "color given stars (list) with color"
    i = begin
    while i <= end:
        stars[i] = with_color(color, stars[i])
        i += 1

def exp_graph(rating, width=20):
    """Exponential growing graph. Assumes ratings from 1-5."""
    max_rat = math.log(5)
    rating /= max_rat
    rating = math.exp(rating)
    stars = [' '] * width
    stars[0:int(rating)] = '=' * int(rating)
    color_stars(stars, "graph-bad", 0, 2)
    color_stars(stars, "graph-decent", 3, 6)
    color_stars(stars, "graph-good", 7, width-1)
    return ''.join(stars)

def linear_graph(rating, width=10):
    """Build a star seq from rating. Give some color when wanted. Width not
    used; fixed at 10."""
    ratint = int(rating*2 + 0.5)
    stars = [' '] * 10
    stars[0:ratint] = '=' * ratint
    color_stars(stars, "graph-bad", 0, 2)
    color_stars(stars, "graph-decent", 3, 5)
    color_stars(stars, "graph-good", 6, 9)
    return ''.join(stars)

# What graphing shall be used by default?
graph_func = linear_graph

def format_compact(e):
    """print entry e compactly in one line."""
    return '({date}) {rating:<4} {graph}   {movie}'.format(
            date=e.origdate.strftime("%Y-%m-%d"),
            rating=e.rating, 
            graph=graph_func(e.rating),
            movie=with_color('Movie',e.movie))

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

    return formatstring.format(movie=with_color('Movie',e.movie),
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

def format_org(e):
    """print entry e in an org-mode format."""
    LEVEL = 1 # what headline levels the movies make?
    result = [] # build the result string line-by-line
    result.append("*"*LEVEL + " " + e.movie)
    result.append(":PROPERTIES:")
    result.append(":RATING: " + str(e.rating))
    result.append(":IMDB: " + imdbutils.imdb_url(e.imdb))
    result.append(":END:")
    result.append(e.origdate.strftime("[%Y-%m-%d %a %H:%M]"))
    result.append(e.message)
    return '\n'.join(result)

FORMATTERS = {'compact': format_compact,
              'full': format_full,
              'org': format_org,
              'csv': format_csv}

def do_list(args):
    """CLI func to call when doing subtask "list". """
    
    global Colors
    Colors = NOCOLORS if args.nocolor else COLORS
    fmtfunc = FORMATTERS[args.format]

    global graph_func
    graph_func = exp_graph if args.exp else linear_graph

    filters = {}
    order = ""

    if args.title: filters["movie LIKE ?"] = "%" + args.title + "%"
    if args.message: filters["message LIKE ?"] = "%" + args.message + "%"
    if args.ge: filters["rating >= ?"] = args.ge
    if args.gt: filters["rating > ?"] = args.gt
    if args.le: filters["rating <= ?"] = args.le
    if args.lt: filters["rating < ?"] = args.lt

    if args.begin: filters["origdate >= ?"] = args.begin
    if args.end: filters["origdate <= ?"] = args.end

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
