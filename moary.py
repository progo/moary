#!/usr/bin/python

import argparse

import edit_entry
import imdbutils
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
                args.imdb, unicode(args.message))
        if not args.skip_imdb:
            newflick = imdbutils.ensure_good_imdb_id(newflick)
    if args.debug:
        print newflick.__dict__
    else:
        data.store_entry(newflick)

def do_list(args):
    """CLI func to call when doing subtask "list". """
    print "listing!"

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
    listparser.set_defaults(func=do_list)
    # TODO: to be concluded

    args = psr.parse_args()
    return args

if __name__ == '__main__':
    """parse args and direct execution towards the right func."""
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8') # wtf
    args = _create_and_parse_args()
    args.func(args)
