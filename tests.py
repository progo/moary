#!/usr/bin/python
# coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8') # wtf

import os
import sys
import unittest
from io import BytesIO

#import pkg_resources
#pkg_resources.require("ludibrio==3.0.3")
from ludibrio import Stub, Mock, any

from entry import Entry
import moary
import edit_entry, data
import imdbutils

# mock imdbutils here instead of ludibrio.
imdbutils.ask_imdb_interactive = lambda x: '1234567'
imdbutils.query_imdb_name = lambda x: 'Dummy Movie'
 
class FileMockReadonly(BytesIO):
    """Mock temporaryfile that has a .name and something else.
    Ignore writes."""
    name = ''
    def write(self, s): pass

class FileMock(BytesIO):
    """Mock temporaryfile, allow rewrites."""
    name = ''

class MoaryTestCase(unittest.TestCase): pass

### [Batch] adds, edits. We'll try to keep BB-y here.

class MoaryBatchTestCase(MoaryTestCase):
    TESTDB = "movies.db_tests"
    COMMON_ARGS = ["-f", TESTDB]

    def setUp(self):
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

class MoaryBatchTestCase_SkippingIMDB(MoaryBatchTestCase):
    """Define -I in arguments so that we'll run stuff without IMDB."""
    TESTDB = "movies.db_tests"
    COMMON_ARGS = ["-I", "-f", TESTDB]

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

class MoaryStubEditorInvokes(MoaryTestCase):
    """Have facilities to fake user involvement by stubbing editor invocation.
    Use `self.set_edited_content` to set the string coming from the editor."""

    def setUp(self):
        # set text we find from the file
        with Stub() as tempfile:
            from tempfile import NamedTemporaryFile
            NamedTemporaryFile() >> FileMock('')

    def set_edited_content(self, string):
        with Stub() as edit_entry:
            from edit_entry import invoke_editor
            invoke_editor(any(), any()) >> string
    
class MoaryAddTestCase(MoaryStubEditorInvokes):
    """This test case sets up canned responses as if coming from the user with
    $EDITOR. Set contents coming from the imaginary user using
    `self.set_edited_content`.
    """
    pass

class TestGoodAdd(MoaryAddTestCase):
    """Test various interactive adds."""

    def testSimpleAdd(self):
        self.set_edited_content("""
        Movie: ABC
        Rating: 4
        IMDB:  01234
        ----- Review -----
        Cool movie.
        """)
 
        entry = edit_entry.edit_data_interactive({})
        self.assertEquals(entry.movie, "ABC")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.message, "Cool movie.")
        self.assertEquals(entry.imdb, '0001234')

    def testSimpleAdd_noIMDB(self):
        self.set_edited_content("""
        Movie: ABC
        Rating: 4
        IMDB:  01234
        ----- Review -----
        Cool movie.
        """)

        entry = edit_entry.edit_data_interactive({}, skip_imdb=True)
        self.assertEquals(entry.movie, "ABC")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.message, "Cool movie.")
        self.assertEquals(entry.imdb, '0001234')

    def testSimpleAddU8(self):
        """Test a situation everything has been provided. Try UTF8
        capabilities.  Terrible issues: IMDB query itself should be tested
        here. Well, not everything is going to be automatized and I hope we get
        away with simply trying to store proper UTF8 content to DB."""

        self.set_edited_content("""
        Movie: Yö
        Rating: 4
        IMDB:  01234
        ----- Review -----
        Sacré bleu!
        """)

        entry = edit_entry.edit_data_interactive({})
        self.assertEquals(entry.movie, "Yö")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.message, "Sacré bleu!")
        self.assertEquals(entry.imdb, '0001234')

    def testSimpleAddNoIMDB(self):
        """test a situation where no IMDB id has been provided. Should ask
        about it."""
        self.set_edited_content("""
        Movie: def
        Rating: 4
        IMDB: 
        ----- Review -----
        Cool movie.
        """)
        entry = edit_entry.edit_data_interactive({})
        self.assertEquals(entry.movie, "def")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.imdb, '1234567')
        self.assertEquals(entry.message, "Cool movie.")

    def testSimpleAddNoIMDB_noIMDB(self):
        """test a situation where no IMDB id has been provided. Should skip."""
        self.set_edited_content("""Movie: def
        Rating: 4
        IMDB: 
        ----- Review -----
        Cool movie.
        """)
        entry = edit_entry.edit_data_interactive({}, skip_imdb=True)
        self.assertEquals(entry.movie, "def")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.imdb, '')
        self.assertEquals(entry.message, "Cool movie.")

    def testBadRating(self):
        """Test bad rating. should clear the bad rating to 0."""
        self.set_edited_content("""Movie: Balzone
        Rating: +
        IMDB: 
        ----- Review -----
        Cool.
        """)
        entry = edit_entry.edit_data_interactive({}, skip_imdb=True)
        self.assertEquals(entry.movie, "Balzone")
        self.assertEquals(entry.rating, '0')
        self.assertEquals(entry.imdb, '')
        self.assertEquals(entry.message, "Cool.")
 
    def testFaultyIMDBAdd_imdb(self):
        """should query the id"""
        self.set_edited_content("""Movie: def
        Rating: 4
        IMDB: vccv
        ----- Review -----
        Cool movie.
        """)
        entry = edit_entry.edit_data_interactive({})
        self.assertEquals(entry.movie, "def")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.imdb, '1234567')
        self.assertEquals(entry.message, "Cool movie.")

class TestBaddAdd(MoaryAddTestCase):
    """Some bad adds."""
    def testFaultyIMDBAdd(self):
        """should clear the faulty id because no previous id provided."""
        self.set_edited_content("""Movie: def
        Rating: 4
        IMDB: vccv
        ----- Review -----
        Cool movie.
        """)
        entry = edit_entry.edit_data_interactive({}, skip_imdb=True)
        self.assertEquals(entry.movie, "def")
        self.assertEquals(entry.rating, '4')
        self.assertEquals(entry.imdb, '')
        self.assertEquals(entry.message, "Cool movie.")

    def testEmptyAdd_without_imdb(self):
        """test a situation where the user provides nothing new. Should raise
        UserCancel."""
        self.set_edited_content(edit_entry.fill_in_form(None))
        self.assertRaises(edit_entry.UserCancel,
            lambda: edit_entry.edit_data_interactive({}, skip_imdb=True))

    def testEmptyAdd_with_imdb(self):
        """test a situation where the user provides nothing new. Should raise
        UserCancel."""
        self.set_edited_content(edit_entry.fill_in_form(None))
        self.assertRaises(edit_entry.UserCancel,
            lambda: edit_entry.edit_data_interactive({}))

### [Interactive] Editing existing data

class MoaryEditTestCase(MoaryStubEditorInvokes):
    """Test cases with an existing entry and provide changed edit form."""
    pass

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

### Test stuff when IMDBpy is not present.

## Batch stuff
##############

class TestBatchAddWithoutIMDBpy(MoaryBatchTestCase):
    """Run batch tests with IMDBpy disabled."""
    def setUp(self):
        MoaryBatchTestCase.setUp(self)
        def throw_noimdbpy(x): raise imdbutils.NoIMDBpyException()
        imdbutils.ask_imdb_interactive = throw_noimdbpy
        imdbutils.query_imdb_name = throw_noimdbpy
    def tearDown(self):
        MoaryBatchTestCase.tearDown(self)
        imdbutils.ask_imdb_interactive = lambda x: '1234567'
        imdbutils.query_imdb_name = lambda x: 'Dummy Movie'

    def testAddIMDBidonly(self):
        """try adding with IMDB id only. Shouldn't insert anything."""
        self.call("add -i http://www.imdb.com/title/tt0233332")
        self.call("add -i 0233332")
        self.call("add -i tt0233332")
        db = data.DataFacilities(dbfile=self.TESTDB)
        self.assertRaises(data.EmptyDBException, db.get_last)

    def testAddByMovie(self):
        """add with movie name only. IMDB should go ''. """
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
        self.assertEquals(entry.imdb, '')

# ugh how wet.
class TestBatchAddWithoutIMDBpy_skipIMDB(MoaryBatchTestCase):
    """Run batch tests with IMDBpy disabled."""
    def setUp(self):
        MoaryBatchTestCase.setUp(self)
        def throw_noimdbpy(x): raise imdbutils.NoIMDBpyException()
        imdbutils.ask_imdb_interactive = throw_noimdbpy
        imdbutils.query_imdb_name = throw_noimdbpy
    def tearDown(self):
        MoaryBatchTestCase.tearDown(self)
        imdbutils.ask_imdb_interactive = lambda x: '1234567'
        imdbutils.query_imdb_name = lambda x: 'Dummy Movie'

    def testAddIMDBidonly(self):
        """try adding with IMDB id only. Shouldn't insert anything."""
        self.call("add -i http://www.imdb.com/title/tt0233332")
        self.call("add -i 0233332")
        self.call("add -i tt0233332")
        db = data.DataFacilities(dbfile=self.TESTDB)
        self.assertRaises(data.EmptyDBException, db.get_last)

    def testAddByMovie(self):
        """add with movie name only. IMDB should go ''. """
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
        self.assertEquals(entry.imdb, '')

### Interactive adds without IMDBpy
###################################

class InteractiveTestCases_without_imdbpy(MoaryAddTestCase):
    def setUp(self):
        MoaryAddTestCase.setUp(self)
        def throw_noimdbpy(x): raise imdbutils.NoIMDBpyException()
        imdbutils.ask_imdb_interactive = throw_noimdbpy
        imdbutils.query_imdb_name = throw_noimdbpy
    def tearDown(self):
        MoaryAddTestCase.tearDown(self)
        imdbutils.ask_imdb_interactive = lambda x: '1234567'
        imdbutils.query_imdb_name = lambda x: 'Dummy Movie'

### Interactive edits without IMDBpy


if __name__ == '__main__':
    unittest.main()
