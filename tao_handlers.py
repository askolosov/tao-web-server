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

import mimetypes
import os
from os import path
from tao_http_util import *
from tao_http_errors import *

class FileHandler(object):
    """
    Simple handler that considers the target uri only as if it is a file
    """
    
    def __init__(self, cfg):
        self.cfg = cfg
        mimetypes.init()

    def handle(self, req, out):
        
        # Target filename is concatenation of this vhost's root with
        # uri without the starting '/'
        #
        # FIXME: security problem: if uri
        # will contain '..' we could get outside f the specified root
        # directory
        res_fs_path = path.normpath(path.join(self.cfg["root"],
                                              req["uri"][1::]))
        
        
        resp_hdrs = dict();

        # If the requested file doesn't exist return 404
        if not path.isfile(res_fs_path):
            raise HTTPNotFoundError("File doesn't exist")

        # If the requested file is not accessible return 403
        if not os.access(res_fs_path, os.R_OK):
            raise HTTPForbiddenError("Permissions denied")

        # Get the MIME type of the requested file
        mime_type, enc = mimetypes.guess_type(res_fs_path)
        # Get the length f the requested file
        size = path.getsize(res_fs_path)

        # Fill the corresponding HTTP-response headers
        resp_hdrs["Content-Type"] = mime_type
        resp_hdrs["Content-Length"] = size

        # Start to send response with Ok status code
        send_response_start(out, 200, req["maj_ver"],
                            req["min_ver"], resp_hdrs)

        # Read requested file by chunks and send them to the connection
        res = open(res_fs_path, "rb")
        n = 0
        while n < size:
            data_chunk = res.read((size - n) % 4096)
            out.write(data_chunk)
            n += len(data_chunk)

        res.close()
        
