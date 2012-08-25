#!/usr/bin/python
# coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8') # wtf

import os
import unittest
from ludibrio import Stub, Mock, Dummy, any
from io import BytesIO

from entry import Entry
import moary
import edit_entry, data

class FileMockReadonly(BytesIO):
    """Mock temporaryfile that has a .name and something else.
    Ignore writes."""
    name = ''
    def write(self, s): pass

class FileMock(BytesIO):
    """Mock temporaryfile, allow rewrites."""
    name = ''

class MoaryTestCase(unittest.TestCase): pass

### [Batch] adds, edits. We'll try to keep BB-y.

class MoaryBatchTestCase(MoaryTestCase):
    TESTDB = "movies.db_tests"
    COMMON_ARGS = ["-f", TESTDB]

    def setUp(self):
        with Stub() as imdbutils:
            from imdbutils import ask_imdb_interactive
            ask_imdb_interactive(any()) >> '1234567'
        with Stub() as imdbutils:
            from imdbutils import query_imdb_name
            query_imdb_name(any()) >> 'Dummy Movie'

        try:
            os.remove(self.TESTDB)
        except OSError:
            pass # file doesn't exist

    def tearDown(self):
        os.remove(self.TESTDB)

    def call(self, cmdline):
        moary.main(self.COMMON_ARGS + cmdline.split())

class TestAddByMovie(MoaryBatchTestCase):
    """Test adding movie the usual way, not relying on IMDB only."""

    def testAddMovieOnly(self):
        """add just the movie"""
        self.call("add ABC")
        entry = data.DataFacilities(dbfile=self.TESTDB).get_last()
        self.assertEquals('ABC', entry.movie)
        self.assertEquals('1234567', entry.imdb)

    def testAddAllIn(self):
        """pass in everything correctly"""
        self.call("add ABC -i 999555 -m Nice -r 3")
        entry = data.DataFacilities(dbfile=self.TESTDB).get_last()
        self.assertEquals(entry.movie, u"ABC")
        self.assertEquals(entry.imdb, u"0999555")
        self.assertEquals(entry.rating, 3.0)
        self.assertEquals(entry.message, u"Nice")

    def testAddFaultyIMDB(self):
        """give movie and faulty imdb. Should ask about it."""
        self.call("add XYZ -i 999vc")
        entry = data.DataFacilities(dbfile=self.TESTDB).get_last()
        self.assertEquals(entry.movie, u"XYZ")
        self.assertEquals(entry.imdb, u"1234567")

class TestGoodAddIMDBonly(MoaryBatchTestCase):
    """test adding by IMDB id only."""

    def testAddIMDBurl(self):
        self.call("add -i http://www.imdb.com/title/tt0233332")
        entry = data.DataFacilities(dbfile=self.TESTDB).get_last()
        self.assertEquals(entry.imdb, '0233332')
        self.assertEquals(entry.movie, 'Dummy Movie')

    def testAddIMDBid(self):
        self.call("add -i 023332")
        entry = data.DataFacilities(dbfile=self.TESTDB).get_last()
        self.assertEquals(entry.imdb, '0023332')
        self.assertEquals(entry.movie, 'Dummy Movie')

    def testAddIMDBfaulty(self):
        self.call("add -i bsv")
        # should have added nothing
        db = data.DataFacilities(dbfile=self.TESTDB)
        self.assertRaises(data.EmptyDBException, db.get_last)

class TestAddAndDelete(MoaryBatchTestCase):
    """test adding and deleting."""
    def testAddAndDelete(self):
        self.call("add ABC -i 123")
        self.call("edit -d")
        db = data.DataFacilities(dbfile=self.TESTDB)
        self.assertRaises(data.EmptyDBException, db.get_last)
        self.call("edit -d")

class MoaryBatchTestCase_SkippingIMDB(MoaryTestCase):
    """Define -I in arguments so that we'll run stuff without IMDB."""
    TESTDB = "movies.db_tests"
    COMMON_ARGS = ["-I", "-f", TESTDB]

    def setUp(self):
        try:
            os.remove(self.TESTDB)
        except OSError:
            pass # file doesn't exist

    def tearDown(self):
        os.remove(self.TESTDB)

    def call(self, cmdline):
        moary.main(self.COMMON_ARGS + cmdline.split())

class TestAddByMovie_SkipIMDB(MoaryBatchTestCase_SkippingIMDB):
    """Test adding movie the usual way, not relying on IMDB at all."""

    def testAddMovieOnly(self):
        """add just the movie"""
        self.call("add ABC")
        entry = data.DataFacilities(dbfile=self.TESTDB).get_last()
        self.assertEquals('ABC', entry.movie)
        self.assertEquals('', entry.imdb)

    def testAddAllIn(self):
        """pass in everything correctly"""
        self.call("add ABC -i 999555 -m Nice -r 3")
        entry = data.DataFacilities(dbfile=self.TESTDB).get_last()
        self.assertEquals(entry.movie, u"ABC")
        self.assertEquals(entry.imdb, u"0999555")
        self.assertEquals(entry.rating, 3.0)
        self.assertEquals(entry.message, u"Nice")

    def testAddFaultyIMDB(self):
        """give movie and faulty imdb. Should clear it."""
        self.call("add XYZ -i 999vc")
        entry = data.DataFacilities(dbfile=self.TESTDB).get_last()
        self.assertEquals(entry.movie, u"XYZ")
        self.assertEquals(entry.imdb, u"")

class TestAddIMDBOnly_SkipIMDB(MoaryBatchTestCase_SkippingIMDB):
    """nonsense operation should do nothing."""
    def testNonsenseOp(self):
        self.call("add -i 1234567")
        db = data.DataFacilities(dbfile=self.TESTDB)
        self.assertRaises(data.EmptyDBException, db.get_last)

### [Interactive] Adding from nothing

class MoaryAddTestCase(MoaryTestCase):
    """This test case sets up canned responses as if coming from the user with
    $EDITOR.  The contents of the file will be looked up from
    `self.filecontents`.
    """

    filecontents = ''

    def setUp(self):
        # ignore calls to $editor
        with Stub() as subprocess:
            from subprocess import call
            call(any()) >> None
        with Stub() as edit_entry:
            from edit_entry import invoke_editor
            invoke_editor(any(),any()) >> self.filecontents

        # set text we find from the file
        with Stub() as tempfile:
            from tempfile import NamedTemporaryFile
            NamedTemporaryFile() >> FileMockReadonly('')

class TestGoodAdd(MoaryAddTestCase):
    """test a situation everything has been provided."""

    filecontents = """Movie: ABC
    Rating: 4
    IMDB:  01234
    ----- Review -----
    Cool movie.
    """
 
    def testSimpleAdd_imdb(self):
        entry = edit_entry.edit_data_interactive({})
        self.assertEquals(entry.movie, "ABC")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.message, "Cool movie.")
        self.assertEquals(entry.imdb, '0001234')

    def testSimpleAdd(self):
        entry = edit_entry.edit_data_interactive({}, skip_imdb=True)
        self.assertEquals(entry.movie, "ABC")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.message, "Cool movie.")
        self.assertEquals(entry.imdb, '0001234')

class TestGoodAddUTF8(MoaryAddTestCase):
    """Test a situation everything has been provided. Try UTF8 capabilities.
    Terrible issues: IMDB query itself should be tested here. Well, not
    everything is going to be automatized and I hope we get away with simply
    trying to store proper UTF8 content to DB."""

    filecontents = """Movie: Yö
    Rating: 4
    IMDB:  01234
    ----- Review -----
    Sacré bleu!
    """
 
    def testSimpleAddU8_imdb(self):
        entry = edit_entry.edit_data_interactive({})
        self.assertEquals(entry.movie, "Yö")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.message, "Sacré bleu!")
        self.assertEquals(entry.imdb, '0001234')

class TestAddNoIMDB(MoaryAddTestCase):
    """test a situation where no IMDB id has been provided. Should ask about
    it."""

    filecontents = """Movie: def
    Rating: 4
    IMDB: 
    ----- Review -----
    Cool movie.
    """
 
    def testSimpleAdd_imdb(self):
        entry = edit_entry.edit_data_interactive({})
        self.assertEquals(entry.movie, "def")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.imdb, '1234567')
        self.assertEquals(entry.message, "Cool movie.")
    def testSimpleAdd(self):
        entry = edit_entry.edit_data_interactive({}, skip_imdb=True)
        self.assertEquals(entry.movie, "def")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.imdb, '')
        self.assertEquals(entry.message, "Cool movie.")

class TestAddBadRating(MoaryAddTestCase):
    """Test adding with bad rating.""" 

    filecontents = """Movie: Balzone
    Rating: +
    IMDB: 
    ----- Review -----
    Cool.
    """
 
    def testBadRating(self):
        """should clear the bad rating to 0."""
        entry = edit_entry.edit_data_interactive({}, skip_imdb=True)
        self.assertEquals(entry.movie, "Balzone")
        self.assertEquals(entry.rating, '0')
        self.assertEquals(entry.imdb, '')
        self.assertEquals(entry.message, "Cool.")

class TestAddFaultyIMDB(MoaryAddTestCase):
    """test a situation a faulty IMDB id has been provided.""" 

    filecontents = """Movie: def
    Rating: 4
    IMDB: vccv
    ----- Review -----
    Cool movie.
    """
 
    def testFaultyIMDBAdd_imdb(self):
        """should query the id"""
        entry = edit_entry.edit_data_interactive({})
        self.assertEquals(entry.movie, "def")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.imdb, '1234567')
        self.assertEquals(entry.message, "Cool movie.")
    def testFaultyIMDBAdd(self):
        """should clear the faulty id because no previous id provided."""
        entry = edit_entry.edit_data_interactive({}, skip_imdb=True)
        self.assertEquals(entry.movie, "def")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.imdb, '')
        self.assertEquals(entry.message, "Cool movie.")

class TestEmptyAdd(MoaryAddTestCase):
    """test a situation where the user provides nothing new. Should raise
    UserCancel."""
    filecontents = edit_entry.fill_in_form(None)
    def testEmptyAdd_without_imdb(self):
        self.assertRaises(edit_entry.UserCancel,
            lambda: edit_entry.edit_data_interactive({}, skip_imdb=True))
    def testEmptyAdd_with_imdb(self):
        self.assertRaises(edit_entry.UserCancel,
            lambda: edit_entry.edit_data_interactive({}))

### [Interactive] Editing existing data

class MoaryEditTestCase(MoaryTestCase):
    """Test cases with an existing entry and provide changed edit form."""

    def setUp(self):
        # set text we find from the file
        with Stub() as tempfile:
            from tempfile import NamedTemporaryFile
            NamedTemporaryFile() >> FileMock('')

    def set_edited_content(self, string):
        with Stub() as edit_entry:
            from edit_entry import invoke_editor
            invoke_editor(any(), any()) >> string

class TestGoodEdits(MoaryEditTestCase):
    """make good edits to good material"""

    def testGoodEdit(self):
        """change one bit."""
        old_entry = Entry("Dland", rating='1', imdb='0999555', message='+1')
 
        self.set_edited_content("""
        Movie: DBland
        Rating: 1
        IMDB: 0999555
        ----- Review -----
        +1
        """)
 
        new_entry = edit_entry.edit_data_interactive(old_entry)
        self.assertEquals(new_entry.movie, "DBland")
        self.assertEquals(new_entry.rating, old_entry.rating)
        self.assertEquals(new_entry.message, old_entry.message)
        self.assertEquals(new_entry.imdb, old_entry.imdb)

    def testGoodEdit_noIMDB(self):
        """change one bit. Skip imdb."""
        old_entry = Entry("Dland", rating='1', imdb='0999555', message='+1')
 
        self.set_edited_content("""
        Movie: DBland
        Rating: 1
        IMDB: 0999555
        ----- Review -----
        +1
        """)
 
        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=True)
        self.assertEquals(new_entry.movie, "DBland")
        self.assertEquals(new_entry.rating, old_entry.rating)
        self.assertEquals(new_entry.message, old_entry.message)
        self.assertEquals(new_entry.imdb, old_entry.imdb)

    def testGoodEdits(self):
        """change everything a bit."""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='+1')

        self.set_edited_content("""
        Movie: DEZ
        Rating: 0
        IMDB: 0999000
        ----- Review -----
        Cool!
        """)

        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=False)
        self.assertEquals(new_entry.movie, "DEZ")
        self.assertEquals(new_entry.rating, '0')
        self.assertEquals(new_entry.message, 'Cool!')
        self.assertEquals(new_entry.imdb, '0999000')

    def testGoodEdits_noIMDB(self):
        """change everything a bit. Skip IMDB."""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='+1')

        self.set_edited_content("""
        Movie: DEZ
        Rating: 0
        IMDB: 0999000
        ----- Review -----
        Cool!
        """)

        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=True)
        self.assertEquals(new_entry.movie, "DEZ")
        self.assertEquals(new_entry.rating, '0')
        self.assertEquals(new_entry.message, 'Cool!')
        self.assertEquals(new_entry.imdb, '0999000')

    def testClearIMDB(self):
        """clear the IMDB for a reason or another. New ID will be queried."""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='+1')

        self.set_edited_content("""
        Movie: ABC
        Rating: 0
        IMDB: 
        ----- Review -----
        +1
        """)

        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=False)
        self.assertEquals(new_entry.movie, "ABC")
        self.assertEquals(new_entry.rating, '0')
        self.assertEquals(new_entry.imdb, '1234567')

    def testClearIMDB_noIMDB(self):
        """clear the IMDB for a reason or another. ID will be cleared."""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='+1')

        self.set_edited_content("""
        Movie: ABC
        Rating: 0
        IMDB: 
        ----- Review -----
        +1
        """)

        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=True)
        self.assertEquals(new_entry.movie, "ABC")
        self.assertEquals(new_entry.rating, '0')
        self.assertEquals(new_entry.imdb, '')

class TestNonEdits(MoaryEditTestCase):
    """do nothing on edits. """

    def testNothing(self):
        """test non-edit with full info."""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='Nice.')
        self.set_edited_content(edit_entry.fill_in_form(old_entry))
        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=False)
        self.assertEquals(old_entry.message, new_entry.message)
        self.assertEquals(old_entry.imdb, new_entry.imdb)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(old_entry.rating, new_entry.rating)

    def testNothing_noIMDB(self):
        """test non-edit with full info. Skip IMDB."""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='Nice.')
        self.set_edited_content(edit_entry.fill_in_form(old_entry))
        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=True)
        self.assertEquals(old_entry.message, new_entry.message)
        self.assertEquals(old_entry.imdb, new_entry.imdb)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(old_entry.rating, new_entry.rating)

    def testNothing_partial_info(self):
        """test non-edit with partial (no IMDB) info. Will ask about the ID."""
        old_entry = Entry("ABC", rating='1', message='Nice.')
        self.set_edited_content(edit_entry.fill_in_form(old_entry))
        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=False)
        self.assertEquals(old_entry.message, new_entry.message)
        self.assertEquals('1234567', new_entry.imdb)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(old_entry.rating, new_entry.rating)

    def testNothing_partial_info_noIMDB(self):
        """test non-edit with partial (no IMDB) info. Will skip the ID."""
        old_entry = Entry("ABC", rating='1', message='Nice.')
        self.set_edited_content(edit_entry.fill_in_form(old_entry))
        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=True)
        self.assertEquals(old_entry.message, new_entry.message)
        self.assertEquals(old_entry.imdb, new_entry.imdb)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(old_entry.rating, new_entry.rating)

class TestEditFromGoodToBad(MoaryEditTestCase):
    """make bad edits to good material."""

    def testBadIMDB(self):
        """full material, change to crappy imdb. Should ask about new one."""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='Nice.')

        self.set_edited_content("""
        Movie: ABC
        Rating: 1
        IMDB: aybabtu
        ----- Review -----
        Nice, isn't it.
        """)

        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=False)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(new_entry.imdb, '1234567')

    def testBadIMDB_skipIMDB(self):
        """full material, change to crappy imdb. Should keep the old one!"""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='Nice.')

        self.set_edited_content("""
        Movie: ABC
        Rating: 1
        IMDB: aybabtu
        ----- Review -----
        Nice, isn't it.
        """)

        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=True)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(new_entry.imdb, old_entry.imdb)

    def testClearMovieName(self):
        """empty the name field. Should probably raise UserCancel."""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='Nice.')

        self.set_edited_content("""
        Movie:
        Rating: 1
        IMDB: 0999555
        ----- Review -----
        Nice, isn't it.
        """)

        self.assertRaises(edit_entry.UserCancel,
                lambda: edit_entry.edit_data_interactive({}, skip_imdb=False))

    def testBadRating(self):
        """push something nonnumeric to rating. Should keep the old rating."""
        old_entry = Entry("ABC", rating='1', imdb='0999555', message='Nice.')

        self.set_edited_content("""
        Movie: ABC
        Rating: -
        IMDB: 0999555
        ----- Review -----
        Nice, isn't it.
        """)

        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=False)
        self.assertEquals(old_entry.rating, new_entry.rating)

class TestEditFromBadToBad(MoaryEditTestCase):
    """make bad edits to bad material."""
    # Not sure if this is needed. After all, we should aim to only store "good"
    # entries in the databases. What constitutes to a bad entry. Not everyone
    # fancies giving a rating or a message. The IMDB id isn't required either.
    pass

if __name__ == '__main__':
    unittest.main()
