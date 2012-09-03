#!/usr/bin/python

import os
import sys
import argparse

from datetime import datetime

import edit_entry
import imdbutils
import listings
import data

from entry import Entry

def do_add(args):
    """CLI func to call when doing subtask "add". """
    # Three kinds of cases here in a mess:
    # 1. movie name provided (possibly other info) (go batch)
    # 2. movie name not provided, IMDB provided (go batch)
    # 3. neither is provided, go interactive
    # TODO refactoring needed. Replace functions and so on.
    db = data.DataFacilities(dbfile=args.db_file)
    if args.movie:
        # 1. batch
        newflick = Entry(unicode(args.movie),
                         args.rating,
                         args.imdb,
                         unicode(args.message or ""))
        newflick.imdb = imdbutils.just_work_dammit(newflick,
                skip=args.skip_imdb)
    elif args.imdb:
        # 2. batch: No movie name given but something of an IMDB id
        if args.skip_imdb:
            print "Can't do this without querying IMDB!"
            return
        try:
            moviename = imdbutils.query_imdb_name(args.imdb)
            clean_id = imdbutils.clean_imdb_id(args.imdb)
        except imdbutils.BadIMDBIdException:
            print "Malformed IMDB id, aborting."
            return
        except imdbutils.NoIMDBpyException:
            print "Can't do this without querying IMDB! (No IMDBpy)"
            return
        newflick = Entry(moviename, imdb=clean_id, rating=args.rating,
                message=unicode(args.message or ""))
    else:
        # 3. interactive
        try:
            newflick = edit_entry.edit_data_interactive(None,
                    skip_imdb=args.skip_imdb)
            if not args.skip_imdb:
                from textwrap import fill
                #triv = imdbutils.query_random_trivia(newflick.imdb)
                #if triv: print 'TRIVIA:',fill(triv )
        except edit_entry.UserCancel:
            print "Empty name, exiting..."
            return 0
    if args.debug:
        print newflick.__dict__
    else:
        db.store_entry(newflick)

def do_edit(args):
    """Handle subtask "edit"."""
    db = data.DataFacilities(dbfile=args.db_file)

    try:
        lastentry = db.get_last()
    except data.EmptyDBException:
        print "Nothing in the DB!"
        return

    if args.delete:
        if args.debug:
            print "Would delete:", vars(lastentry)
            return
        else:
            db.delete_entry()
            return
    # at this point, only edit the last one
    edited = edit_entry.edit_data_interactive(lastentry,
            skip_imdb=args.skip_imdb)
    db.set_entry(edited)

def _create_and_parse_args(argv):
    """Create the arg parser and do the magic."""
    psr = argparse.ArgumentParser(description="A movie diary.")
    subparser = psr.add_subparsers(
            title="Subtasks",
            help=None)

    psr.add_argument('-I', '--skip-imdb', action='store_true',
            help="Don't query IMDB")
    psr.add_argument('-f', '--db-file', action='store',
            help='Specify a database other than default.')
    psr.add_argument('-C', '--nocolor', action='store_true',
            help="Disable color output.")
    psr.add_argument('-D', '--debug', action='store_true',
            help="Debug and dry-run.")

    addparser = subparser.add_parser('add',
            help="Add new entry")
    addparser.add_argument("movie",
            nargs='?',
            help="Movie name")
    addparser.add_argument("-r", "--rating", type=float,
            help="How did you like the movie?")
    addparser.add_argument("-i", "--imdb",
            help="IMDB id or URL")
    addparser.add_argument("-m", "--message",
            help="A few words about the experience.")
    addparser.set_defaults(func=do_add)

    listparser = subparser.add_parser('list',
            help='List entries')
    listparser.add_argument("format", nargs='?',
            help='Select the format style.',
            choices=["compact", "csv", "full"])
    listparser.add_argument('-t', '--title', action='store',
            help='Grep titles.')
    listparser.add_argument('-m', '--message', action='store',
            help='Grep messages.')
    listparser.add_argument('--ge', type=float,
            help='Show films with rating greater or equal than')
    listparser.add_argument('--gt', type=float,
            help='Show films with rating greater than')
    listparser.add_argument('--le', type=float,
            help='Show films with rating less or equal than')
    listparser.add_argument('--lt', type=float,
            help='Show films with rating less than')

    def isodate(s):
        """Try and parse ISO date into a datetime. Raise ArgumentTypeError for
        argparse to handle in case of bad data."""
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            raise argparse.ArgumentTypeError("Invalid date.")

    listparser.add_argument('-b', '--begin', type=isodate,
            help='Show entries stored after the date [YYYY-MM-DD] inclusive.')
    listparser.add_argument('-e', '--end', type=isodate,
            help='Show entries stored before the date [YYYY-MM-DD] exclusive.')

    listparser.add_argument('-S', '--sort-name', action='store_true',
            help='Sort results by name.')
    listparser.add_argument('-R', '--sort-rating', action='store_true',
            help='Sort results by rating.')
    listparser.add_argument('-A', '--asc', action='store_true',
            help='Sort ascending')
    listparser.add_argument('-D', '--desc', action='store_true',
            help='Sort descending')
    listparser.set_defaults(format='compact', func=listings.do_list)

    # edit section will be limited to the last one for the time being.
    editparser = subparser.add_parser('edit',
            help='Edit entries')
    editparser.add_argument("-d", "--delete", action="store_true",
            help='Delete last entry')
    editparser.set_defaults(func=do_edit)

    if len(argv) == 0: psr.parse_args(['-h'])
    args = psr.parse_args(argv)

    # check for environ variables and set if no option given
    if not args.db_file: args.db_file = os.environ.get('MOARY_MOVIEDB', '')

    return args

def main(argv):
    """ Inspect arguments and dispatch to subtasks. """
    args = _create_and_parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    """parse args and direct execution towards the right func."""
    reload(sys)
    sys.setdefaultencoding('utf-8') # wtf
    main(sys.argv[1:])
