Moary
=====

A work-in-progress effort to provide a local movie rating database for CLI. The
workflow with the usable product follows:

1. Watch the picture, gather your thoughts about it.
2. Run ``moary.py``.
3. ``$EDITOR`` will open with a simple form. Fill as much as you'd like to.
   Movie name is the only required field. Save and exit.
4. If you didn't enter IMDB id or URL, Moary queries IMDB with 7 closest names
   and you choose the one you meant.
5. There it is now. Saved in database somewhere.

A some sort of list or search capability will appear some time.

Philosophy
----------

The film experience will fluctuate from a view to another. I hence support the
viewpoint that each written "review" is as immutable as possible. If one
watches a movie the second time, they write another review. Perhaps this is not
as much about reviewing as it is about a movie diary.


Requirements
------------

- IMDBpy version 4.9 (older versions have trouble with name search)
- SQlite3 will be used.
- A sensible ``$EDITOR`` set.
