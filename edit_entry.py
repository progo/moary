"""This module contains functions to edit data, invoke the user interactively
about it."""

import re
import subprocess
import os
import datetime
import tempfile

import imdbutils

from entry import Entry

class UserCancel():
    """Exception when user decides to cancel the interactive scenes."""
    pass

def parse_file(f):
    """read the temp file containing rate and other stuff. Return an Entry."""

    def clean_line(s):
        """remove initial label from the beginning of the line"""
        return re.sub(r"\A.*?: ?", "", s.strip()).strip()

    f.seek(0)

    # now just go through the file format
    entry = Entry(movie=unicode(clean_line(f.readline())))
    entry.rating = clean_line(f.readline())
    entry.imdb = clean_line(f.readline())
    f.readline()
    entry.message = unicode(f.read().strip())
    return entry

def fill_in_form(entry):
    """given movie dict, return filled-out form string for editors."""
    initial_message = (
        "Movie: {0}\n" +
        "Rating: {1}\n" +
        "IMDB: {2}\n" +
        "----- Review -----\n" +
        "{3}")
    if not entry:
        return initial_message.format('','','','\n')
    return initial_message.format(entry.movie, entry.rating, entry.imdb,
            entry.message)

def edit_data_interactive(olddata, skip_imdb=False):
    """given the Entry, invoke editor on user to edit the entry. Return the
    Entry with possibly updated info."""
    EDITOR = os.environ['EDITOR'] or "ed"

    with tempfile.NamedTemporaryFile() as tf:
        tf.write(fill_in_form(olddata))
        tf.flush()
        subprocess.call([EDITOR, tf.name])
        newdata = parse_file(tf)

        if not newdata.movie:
            raise UserCancel()

        if not skip_imdb:
            newdata = imdbutils.ensure_good_imdb_id_interactive(newdata)
        else:
            try: newdata.imdb = imdbutils.clean_imdb_id(newdata.imdb)
            except imdbutils.BadIMDBIdException:
                newdata.imdb = '' # will not pass the full covered test suite!

        newdata.update = datetime.datetime.now()

        return newdata
