#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Aleksandr Kolosov <akolosov@cs.petrsu.ru>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import re

status_messages = {
    200: "Ok",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    501: "Not Implemented"
}

def send_response_start(out, status_code, maj_ver, min_ver, headers=dict()):
    """
    Sends response start line with the given status code, then given
    headers, then empty line.
    """
    
    resp_line = "HTTP/{}.{} {} {}\r\n".format(maj_ver, min_ver,
                                              status_code,
                                              status_messages[status_code])
    out.write(resp_line)
    
    for hdr in headers:
        hdr_line = "{}: {}\r\n".format(hdr, headers[hdr])
        out.write(hdr_line)

    out.write("\r\n")

def send_simple_response(out, status_code, data, maj_ver, min_ver,
                         content_type="text/html"):
    """
    Sends simple response using given string as content.
    """

    size = len(data)
    hdrs = dict();
    hdrs["Content-Type"] = content_type
    hdrs["Content-Length"] = size

    send_response_start(out, status_code, maj_ver, min_ver, hdrs)

    out.write(data)    

def parse_http_request(inp):
    """
    Parses HTTP request from the given input
    """
    
    request = dict()

    # Some grammar to parse request
    token_re = "[!#$%&'*+-.^_`|~0-9a-zA-Z]+"
    target_re = "(/\S+)+(\?\S*)?"
    field_val_re = "\S([ \t]?\S)*"

    # Parse request start line (RFC7230 3.1.1):
    # request-line = method SP request-target SP HTTP-version CRLF
    req_line = inp.readline().strip()
    m = re.match("^({}) ({}) HTTP/(\d)\.(\d)$".format(token_re,
                                                      target_re),
                 req_line)

    # If request first line is not matching to the expected RE,
    # interrupt request handling and return 400 to the client
    if m == None:
        raise RequestParseError("Request start line")

    # Else, fill the request dictionary
    request["method"] = m.group(1)
    request["target"] = m.group(2)
    request["maj_ver"] = m.group(5)
    request["min_ver"] = m.group(6)

    # Parse headers (RFC7230 3.2):
    # header-field = field-name ":" OWS field-value OWS
    headers = dict()
    request["headers"] = headers
    for line in inp:
        line = line.strip()

        # Do until empty string separator is read
        if line == "":
            break

        # Try to match header to the RE
        m = re.match("^({}):[ \t]*({})[ \t]*$".format(token_re,
                                                      field_val_re),
                     line)
            
        # If it doesn't match, interrupt and return 400 to th client
        if m == None:
            raise RequestParseError("Headers")

        # Else, add successfully read header
        headers[m.group(1)] = m.group(2)

    # Return request dictionary
    return request

# TODO: implement helper method for sending data using 'chunked'
# transfer encoding
def send_data_chunk(out, data_chunk):
    pass
