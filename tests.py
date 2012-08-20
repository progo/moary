#!/usr/bin/python
# Too late, too late.
import unittest
from ludibrio import Stub, Mock, Dummy
from io import BytesIO

from entry import Entry
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

### Adding from nothing

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
 
    def testSimpleAdd(self):
        entry = edit_entry.edit_data_interactive({}, skip_imdb=True)
        self.assertEquals(entry.movie, "ABC")
        self.assertEquals(entry.rating, '4')

class TestEmptyAdd(MoaryAddTestCase):
    """test a situation where the user provides nothing new. Should raise
    UserCancel."""
    filecontents = """Movie: 
    Rating: 
    IMDB:  
    ----- Review -----
    """

    def testEmptyAdd(self):
        self.assertRaises(edit_entry.UserCancel,
            lambda: edit_entry.edit_data_interactive({}, skip_imdb=True))

### Editing existing data

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
    """Test edit where the user doesn't actually edit anything. Ensure nothing
    changes."""
    def testNonEdit(self):
        old_entry = Entry("ABC", rating='3')
        new_entry = edit_entry.edit_data_interactive(old_entry, skip_imdb=True)
        self.assertEquals(old_entry.movie, new_entry.movie)
        self.assertEquals(old_entry.message, new_entry.message)
        self.assertEquals(old_entry.imdb, new_entry.imdb)
        self.assertEquals(old_entry.rating, new_entry.rating)

if __name__ == '__main__':
    unittest.main()
