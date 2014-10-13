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

import SocketServer
import re
import tao_config
from tao_http_util import *
from tao_http_errors import *
    
class HTTPConnectionHandler(SocketServer.StreamRequestHandler):
    def _process_request(self, req):

        # This web-server doesn't support other methods than GET
        if req["method"] != "GET":
            raise NotImplementedError

        # Check if HTTP/1.1 request has the Host header
        if (req["maj_ver"] == '1' and
            req["min_ver"] == '1' and
            not "Host" in req["headers"]):
            
            raise HTTPBadRequestError("Host header absent")

        # Else, if it's an HTTP/1.0 connection, let the 'Host' hader
        # value be "default"
        elif (req["maj_ver"] == '1' and
              req["min_ver"] == '0' and
              not "Host" in req["headers"]):

            host_hdr = "default"

        # At last, take the 'Host' header value
        else:
            host_hdr = req["headers"]["Host"]
            
        # Find a configuration for the given host
        if host_hdr in tao_config.cfg['vhosts']:
            vhost_cfg = tao_config.cfg['vhosts'][host_hdr]
        else:
            vhost_cfg = tao_config.cfg['vhosts']["default"]

        # A request target generally has the next format: path?param1=val1&...
        # Parse the request target to uri and query params apart
        uri, query_str = req["target"].partition("?")[::2]
        params = dict()
        for pv_pair in query_str.split("&"):
            name, val = pv_pair.partition("=")[::2]
            params[name] = val

        req["uri"] = uri
        req["params"] = params

        # TODO: implement request routing (different handlers could be
        # configured for different uri's)

        # Handle the request using the handler specified in the config
        h = vhost_cfg["handler"](vhost_cfg)
        h.handle(req, self.wfile)
    
    def handle(self):
        """
        Handling input HTTP request
        """

        # Trying to keep persistent connection according to HTTP/1.1
        #
        # FIXME: this solution doesn't consider that client can close
        # the connection without Connection: close header even if it
        # supports HTTP/1.1
        while True:
            try:
                req = parse_http_request(self.rfile);
                self._process_request(req)
                
            except HTTPBadRequestError as e:
                # Use HTTP version of request if start line was
                # successfully read
                if req:
                    maj_ver = 1
                    min_ver = 0
                else:
                    maj_ver = req["maj_ver"]
                    min_ver = req["min_ver"]

                # Send '400 Bad Request' to the client
                send_simple_response(self.wfile, 400, str(e), maj_ver, min_ver)

            except HTTPNotFoundError as e:
                send_simple_response(self.wfile, 404, str(e),
                                     req["maj_ver"], req["min_ver"])

            except HTTPForbiddenError as e:
                send_simple_response(self.wfile, 403, str(e),
                                     req["maj_ver"], req["min_ver"])

            except NotImplementedError as e:
                # Send '501 Not Implemented' to the client
                send_simple_response(self.wfile, 501, str(e),
                                     req["maj_ver"], req["min_ver"])


            except Exception as e:
                # Send '500 Internal Server Error' on all another
                # exceptions, that happen after request parse
                if req:
                    send_simple_response(self.wfile, 500, str(e),
                                         req["maj_ver"],
                                         req["min_ver"])
                
            # Close the connection if the client doesn't speak
            # HTTP/1.1 or pass the 'Connection: close' header
            if (not req or
                (req["maj_ver"] == '1' and req["min_ver"] == '0') or
                ("Connection" in req["headers"] and
                 req["headers"]["Connection"] == "close")):
                
                break

class ForkingTCPServer(SocketServer.ForkingMixIn, SocketServer.TCPServer):
    pass
        
class TaoWebServer:
    """
    Without going out the door, know the world
    Without peering out the window, see the Heavenly Tao
    The further one goes
    The less one knows
    	    /Laozi, Tao Te Ching, Chapter 47 (trans. by Derek Lin)/
    """

    @staticmethod
    def run():
        """
        Tao Web Server start procedure. IP and port for binding are taken
        from the configuration file
        """

        host = tao_config.cfg["bind_ip"]
        port = tao_config.cfg["bind_port"]
        server = SocketServer.ForkingTCPServer((host, port),
                                               HTTPConnectionHandler)

        server.serve_forever()

if __name__ == '__main__':
    TaoWebServer.run();
