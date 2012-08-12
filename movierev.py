#!/usr/bin/python

from edit_entry import edit_data_interactive
import data

if __name__ == '__main__':
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8') # wtf
    newflick = edit_data_interactive(None)
    print newflick.__dict__
    data.store_entry(newflick)
