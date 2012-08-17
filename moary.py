#!/usr/bin/python

import sys
import argparse

import edit_entry
import imdbutils
import listings
import data

from entry import Entry

def do_add(args):
    """CLI func to call when doing subtask "add". """
    if not args.movie:
        try:
            newflick = edit_entry.edit_data_interactive(None,
                    skip_imdb=args.skip_imdb)
        except edit_entry.UserCancel:
            print "Empty name, exiting..."
            return 0
    else:
        newflick = Entry(unicode(args.movie), args.rating,
                args.imdb, unicode(args.message or ""))
        if not args.skip_imdb:
            newflick = imdbutils.ensure_good_imdb_id(newflick)
    if args.debug:
        print newflick.__dict__
    else:
        data.store_entry(newflick)

def do_edit(args):
    """Handle subtask "edit"."""
    try:
        lastentry = data.get_last()
    except data.EmptyDBException:
        print "Nothing in the DB!"
        return

    if args.delete:
        if args.debug:
            print "Would delete:", vars(lastentry)
            return
        else:
            data.delete_entry()
            return
    # at this point, only edit the last one
    edited = edit_entry.edit_data_interactive(lastentry,
            skip_imdb=args.skip_imdb)
    data.set_entry(edited)

def _create_and_parse_args():
    """Create the arg parser and do the magic."""
    psr = argparse.ArgumentParser(description="A movie diary.")
    subparser = psr.add_subparsers(
            title="Subtasks",
            help=None)

    psr.add_argument('-I', '--skip-imdb', action='store_true',
            help="Don't query IMDB")
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

    if len(sys.argv) == 1: psr.parse_args(['-h'])
    args = psr.parse_args()
    return args

if __name__ == '__main__':
    """parse args and direct execution towards the right func."""
    reload(sys)
    sys.setdefaultencoding('utf-8') # wtf
    args = _create_and_parse_args()
    args.func(args)
