# -*- coding: utf-8; Mode: python; tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
# ex: set softtabstop=4 tabstop=4 shiftwidth=4 expandtab fileencoding=utf-8:

"""Received from Evan Wheeler (http://github.com/ewheeler) on 1 April 2013."""

import codecs, csv, types
from cStringIO import StringIO

"""
The following classes are adapted from the CSV module documentation.
"""

_numbers = frozenset((types.IntType, types.LongType, types.FloatType))

class _UTF8Encoder(object):
    """
    Iterator that reads an encoded stream and re-encodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode('utf-8')

class UnicodeCSVReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """
    def __init__(self, f, encoding='utf-8', **kwargs):
        f = _UTF8Encoder(f, encoding)
        self.reader = csv.reader(f, **kwargs)

    def next(self):
        row = self.reader.next()
        row_decoded = []
        for value in row:
            if type(value) in _numbers:
                # fake csv distinguishing between int/long or float
                value_int = int(value)
                if value_int == value:
                    row_decoded.append(value_int)
                else:
                    row_decoded.append(value)
            else:
                row_decoded.append(unicode(value, 'utf-8'))
        return row_decoded

    def __iter__(self):
        return self

class UnicodeCSVWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """
    def __init__(self, f, encoding='utf-8', **kwargs):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, **kwargs)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        row_encoded = []
        for value in row:
            if value is None:
                row_encoded.append('')
            elif type(value) in _numbers:
                row_encoded.append(value)
            else:
                row_encoded.append(unicode(value).encode('utf-8'))
        self.writer.writerow(row_encoded)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

class UnicodeCSVDictReader(object):
    """
    A CSV DictReader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """
    def __init__(self, f, encoding='utf-8', **kwargs):
        f = _UTF8Encoder(f, encoding)
        self.reader = csv.DictReader(f, **kwargs)

    def next(self):
        row = self.reader.next()
        row_decoded = {}
        for key, value in row.iteritems():
            if type(value) in _numbers:
                # fake csv distinguishing between int/long or float
                value_int = int(value)
                if value_int == value:
                    row_decoded[key] = value_int
                else:
                    row_decoded[key] = value
            else:
                row_decoded[key] = unicode(value, 'utf-8')
        return row_decoded

    def __iter__(self):
        return self

class UnicodeCSVDictWriter(object):
    """
    A CSV DictWriter which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """
    def __init__(self, f, encoding='utf-8', **kwargs):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.DictWriter(self.queue, **kwargs)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        row_encoded = {}
        for key, value in row.iteritems():
            if value is None:
                row_encoded[key] = ('')
            elif type(value) in _numbers:
                row_encoded[key] = value
            else:
                row_encoded[key] = unicode(value).encode('utf-8')
        self.writer.writerow(row_encoded)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
