#!/usr/bin/python

from edit_entry import edit_data_interactive
import data

if __name__ == '__main__':
    newflick = edit_data_interactive(None)
    print newflick.__dict__
    data.store_entry(newflick)
