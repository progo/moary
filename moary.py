#!/usr/bin/python

import argparse

import edit_entry
from entry import Entry
import data


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
        # TODO, warning: WET code
        clean_id = edit_entry.clean_imdb_id(newflick.imdb)
        if not clean_id:
            newflick.imdb = '' if args.skip_imdb \
                else edit_entry.ask_imdb_interactive(newflick.movie)
        else:
            newflick.imdb = clean_id
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
