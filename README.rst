Moary
=====

An effort to provide a local movie rating database or rather a diary
for the CLI environment. The workflow with the usable product follows:

Workflow examples
-----------------

Moary is designed with interactive editing in mind, but I value the power of
batch-oriented inserts.

Interactive workflow
````````````````````

The usual way with longer messages is to have the interactive session with
your favourite editor.

1. Watch the picture, gather your thoughts about it.
2. Run ``moary.py add``.
3. ``$EDITOR`` will open with a simple form. Fill as much as you'd like to.
   Movie name is the only required field. Save and exit.
4. If you didn't enter IMDB id or URL, Moary queries IMDB with 7 closest names
   and you choose the one you meant. (Skip this phase using option ``-I``.)
5. There it is now. Saved in database somewhere.

Enter from CLI
``````````````

For those quick ones, or for applications of batch process capabilities,
everything can be done with command-line arguments.

1. Watch the picture, gather your thoughts about it.
2. As an example::

    moary.py add "Mulholland Dr." -r 5 -m "Very nice movie."

3. As you didn't enter IMDB url (with the optional ``-i`` flag), you get the
   prompt asking about correct IMDB title.
4. Skip the query with the flag ``-I`` (don't query IMDB) or enter correct(ish)
   IMDB id with ``-i``.

A some sort of list or search capability will appear some time.

Plain examples
``````````````

Get help::
    
    moary.py -h
    moary.py add -h

Full entry from command line (doesn't ask you IMDB titles because one is
given)::

    moary.py add "Mulholland Dr." -r 5 -m "ok movie" -i 0166924

The same example with long options::

    moary.py add "Mulholland Dr." --rating 5 --message "ok movie" --imdb 0166924

The only required thing to add, is the name of the movie. Moary will ask about
the IMDB title::

    moary.py add "Lost Highway"

Now it keeps quiet and no ID is set or searched::

    moary.py -I add "Lost Highway"


List format
```````````

Compact listing (the default) supports a user-provided format strings
now. (The `-F` or `--list-format` option.) The strings follow Python's
string format syntax. The supported symbols are currently: movie,
rating, graph, date.

Statistics
``````````

Now get basic statistics from your viewing habits. Works best when you
record the experience soon after the movie. Most will enjoy a HTML
presentation::

    moary.py stats -Ho

Use your shell's functionality when you want to save the stats for
later use.


Philosophy
----------

The film experience will fluctuate from a view to another. I hence support the
viewpoint that each written "review" is as immutable as possible. If one
watches a movie the second time, they write another review. Perhaps this is not
as much about reviewing as it is about a movie diary.


Requirements
------------

- If IMDB searches desired, IMDBpy version 6.5+ for latest support.
- A sensible ``$EDITOR`` set.
