"""This module contains functions to edit data, invoke the user interactively
about it."""

import re
import subprocess
import os
import datetime
import tempfile
import io

import imdbutils

from entry import Entry

class UserCancel():
    """Exception when user decides to cancel the interactive scenes."""
    pass

def is_valid_rating(rating):
    """Predicate to check if the rating is valid."""
    return re.match(r'\A\d*\.?\d+\Z', str(rating))

def parse_string(string):
    """Read in the [multiline] string and parse it into an Entry."""
    # TODO could use a rewrite without lazy patches

    def clean_line(s):
        """remove initial label from the beginning of the line"""
        return re.sub(r"\A.*?: ?", "", s.strip()).strip()

    f = io.StringIO(string.lstrip())
    f.seek(0)

    # now just go through the file format
    entry = Entry(movie=clean_line(f.readline()))
    entry.rating = clean_line(f.readline())
    entry.imdb = clean_line(f.readline())
    f.readline()
    entry.message = f.read().strip()
    return entry

def fill_in_form(entry):
    """given movie dict, return filled-out form string for editors."""
    initial_message = (
        "Movie: {0}\n"
        "Rating: {1}\n"
        "IMDB: {2}\n"
        "----- Review -----\n"
        "{3}")
    if not entry:
        return initial_message.format('','','','\n')
    return initial_message.format(entry.movie, entry.rating, entry.imdb,
            entry.message)

def invoke_editor(form, tempfilehandle):
    """Invoke the editor on tempfilehandle. Write initial message 'form' in
    first. Return the file fully read as string!"""
    EDITOR = os.environ['EDITOR'] or "ed"
    tempfilehandle.write(form)
    tempfilehandle.flush()
    subprocess.call([EDITOR, tempfilehandle.name])
    tempfilehandle.seek(0)
    return tempfilehandle.read()

def edit_data_interactive(olddata, skip_imdb=False):
    """given the Entry, invoke editor on user to edit the entry. Return the
    Entry with possibly updated info."""

    with tempfile.NamedTemporaryFile(mode='w+') as tf:
        oldform = fill_in_form(olddata)
        newform = invoke_editor(oldform, tf)
        newdata = parse_string(newform)

        if not newdata.movie:
            raise UserCancel()

        try:
            newdata.imdb = imdbutils.just_work_dammit(newdata, olddata,
                                                      skip=skip_imdb)
        except Exception as e:
            # Yes, again the old dilemma: should we keep existing
            # value or clear it? I say, clear it, because the user
            # will be notified of the problem and he can try again
            # soon.
            print("IMDB couldn't be reached!", e)
            newdata.imdb = ''

        if olddata and olddata.rating and not is_valid_rating(newdata.rating):
            newdata.rating = olddata.rating
        elif not is_valid_rating(newdata.rating):
            newdata.rating = '0'

        newdata.update = datetime.datetime.now()

        return newdata
