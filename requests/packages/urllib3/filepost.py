# urllib3/filepost.py
# Copyright 2008-2011 Andrey Petrov and contributors (see CONTRIBUTORS.txt)
#
# This module is part of urllib3 and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import codecs
import mimetypes


# ---------------------------------
# Python 3 choose_boundary.
import os

from ... import compat

if compat.is_py2:

    try:
        import thread
    except ImportError:
        import dummy_thread as thread
    _counter_lock = thread.allocate_lock()

else:
    try:
        import _thread
    except ImportError:
        import _dummy_thread as thread
    _counter_lock = _thread.allocate_lock()

_counter = 0
def _get_next_counter():
    global _counter
    _counter_lock.acquire()
    _counter += 1
    result = _counter
    _counter_lock.release()
    return result

_prefix = None

def choose_boundary():
    """Return a string usable as a multipart boundary.

    The string chosen is unique within a single program run, and
    incorporates the user id (if available), process id (if available),
    and current time.  So it's very unlikely the returned string appears
    in message text, but there's no guarantee.

    The boundary contains dots so you have to quote it in the header."""

    global _prefix
    import time
    if _prefix is None:
        import socket
        try:
            hostid = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            hostid = '127.0.0.1'
        try:
            uid = repr(os.getuid())
        except AttributeError:
            uid = '1'
        try:
            pid = repr(os.getpid())
        except AttributeError:
            pid = '1'
        _prefix = hostid + '.' + uid + '.' + pid
    return "%s.%.3f.%d" % (_prefix, time.time(), _get_next_counter())


# ---------------------------------

StringIO = compat.BytesIO


writer = codecs.lookup('utf-8')[3]


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def encode_multipart_formdata(fields, boundary=None):
    """
    Encode a dictionary of ``fields`` using the multipart/form-data mime format.

    :param fields:
        Dictionary of fields. The key is treated as the field name, and the
        value as the body of the form-data. If the value is a tuple of two
        elements, then the first element is treated as the filename of the
        form-data section.

    :param boundary:
        If not specified, then a random boundary will be generated using
        :func:`mimetools.choose_boundary`.
    """
    body = StringIO()
    if boundary is None:
        boundary = choose_boundary()

    for fieldname, value in fields.iteritems():
        body.write('--%s\r\n' % (boundary))

        if isinstance(value, tuple):
            filename, data = value
            writer(body).write('Content-Disposition: form-data; name="%s"; '
                               'filename="%s"\r\n' % (fieldname, filename))
            body.write('Content-Type: %s\r\n\r\n' %
                       (get_content_type(filename)))
        else:
            data = value
            writer(body).write('Content-Disposition: form-data; name="%s"\r\n'
                               % (fieldname))
            body.write('Content-Type: text/plain\r\n\r\n')

        if isinstance(data, int):
            data = str(data)  # Backwards compatibility

        if isinstance(data, unicode):
            writer(body).write(data)
        else:
            body.write(data)

        body.write('\r\n')

    body.write('--%s--\r\n' % (boundary))

    content_type = 'multipart/form-data; boundary=%s' % boundary

    return body.getvalue(), content_type
