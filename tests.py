#!/usr/bin/python
# Too late, too late.
import os
import unittest
from ludibrio import Stub, Mock, Dummy
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
            ask_imdb_interactive(Dummy()) >> '1234567'
        with Stub() as imdbutils:
            from imdbutils import query_imdb_name
            query_imdb_name(Dummy()) >> 'Dummy Movie'

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
            call(Dummy()) >> None

        # set text we find from the file
        with Stub() as tempfile:
            from tempfile import NamedTemporaryFile
            NamedTemporaryFile() >> FileMockReadonly(self.filecontents)

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
    """ Set up test cases with something predefined """

    def setUp(self):
        # ignore calls to $editor
        with Stub() as subprocess:
            from subprocess import call
            call(Dummy()) >> None

        # set text we find from the file
        with Stub() as tempfile:
            from tempfile import NamedTemporaryFile
            NamedTemporaryFile() >> FileMock('')

class TestNonEdit(MoaryEditTestCase):
    """Test edit where the user doesn't actually edit anything. Ensure that
    nothing unwanted changes."""

    def testNonEdit_full_info_with_imdb(self):
        old_entry = Entry("ABC", imdb='0023332', rating='3', message='Cool.')
        new_entry = edit_entry.edit_data_interactive(old_entry)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(old_entry.message, new_entry.message)
        self.assertEquals(old_entry.imdb, new_entry.imdb)
        self.assertEquals(old_entry.rating, new_entry.rating)

    def testNonEdit_full_info_without_imdb(self):
        old_entry = Entry("ABC", imdb='0023332', rating='3', message='Cool.')
        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=True)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(old_entry.message, new_entry.message)
        self.assertEquals(old_entry.imdb, new_entry.imdb)
        self.assertEquals(old_entry.rating, new_entry.rating)

    def testNonEdit_name_only_with_imdb(self):
        """null id has been queried."""
        old_entry = Entry("ABC")
        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=False)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(old_entry.message, new_entry.message)
        self.assertEquals('1234567', new_entry.imdb)
        self.assertEquals('0', new_entry.rating)

    def testNonEdit_name_only_without_imdb(self):
        old_entry = Entry("ABC")
        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=True)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(old_entry.message, new_entry.message)
        self.assertEquals('', new_entry.imdb)
        self.assertEquals('0', new_entry.rating)

if __name__ == '__main__':
    unittest.main()
