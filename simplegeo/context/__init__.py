API_VERSION = '1.0'

import urllib

# example: http://api.simplegeo.com/0.1/context/37.797476,-122.424082.json

from simplegeo.shared import json_decode
from simplegeo.shared import Client as SGClient, is_valid_ip, is_valid_lat, is_valid_lon
from simplegeo.shared import APIError
from pyutil.assertutil import precondition
import oauth2 as oauth
try:
    from google.appengine.api import urlfetch
except:
    pass

class Client(SGClient):
    def __init__(self, key, secret, api_version=API_VERSION, host="api.simplegeo.com", port=80):
        SGClient.__init__(self, key, secret, api_version=api_version, host=host, port=port)

        self.endpoints['context'] = 'context/%(lat)s,%(lon)s.json'
        self.endpoints['context_by_ip'] = 'context/%(ip)s.json'
        self.endpoints['context_by_my_ip'] = 'context/ip.json'
        self.endpoints['context_by_address'] = 'context/address.json?address=%(address)s'

    def get_context(self, lat, lon):
        precondition(is_valid_lat(lat), lat)
        precondition(is_valid_lon(lon), lon)
        endpoint = self._endpoint('context', lat=lat, lon=lon)
        return json_decode(self._request(endpoint, "GET")[1])

    def get_context_by_ip(self, ipaddr):
        """ The server uses guesses the latitude and longitude from
        the ipaddr and then does the same thing as get_context(),
        using that guessed latitude and longitude."""
        precondition(is_valid_ip(ipaddr), ipaddr)
        endpoint = self._endpoint('context_by_ip', ip=ipaddr)
        return json_decode(self._request(endpoint, "GET")[1])

    def get_context_by_my_ip(self):
        """ The server gets the IP address from the HTTP connection
        (this may be the IP address of your device or of a firewall,
        NAT, or HTTP proxy device between you and the server), and
        then does the same thing as get_context_by_ip(), using that IP
        address."""
        endpoint = self._endpoint('context_by_my_ip')
        return json_decode(self._request(endpoint, "GET")[1])

    def get_context_by_address(self, address):
        """
        The server figures out the latitude and longitude from the
        street address and then does the same thing as get_context(),
        using that deduced latitude and longitude.
        """
        precondition(isinstance(address, basestring), address)
        endpoint = self._endpoint('context_by_address', address=urllib.quote_plus(address))
        return json_decode(self._request(endpoint, "GET")[1])


class AppEngineClient(Client):
    """
    An implementation of Client that executes requests
    asynchronously using Google App Engine's URL Fetch service, instead of
    synchronously using httplib2.
    
    Example usage:
    
    import simplegeo.context as context
    client = context.AppEngineClient(mykey, mysecret)
    rpc = client.get_context_async(lat, lon)
    
    # some other stuff do to...
    # ...
    # now I need the context, this call blocks for it if it hasn't already returned:
    
    context = client.get_context_result(rpc)
    
    """
    
    def get_context_async(self, lat, lon, **kwds):
        """
        Starts an asynchronous request using GAE's URL Fetch service.
        Returns an RPC object that can be subsequently passed to get_context_result()
        
        **kwds
            Keyword arguments to pass when creating the RPC object.
            See http://code.google.com/appengine/docs/python/urlfetch/asynchronousrequests.html#create_rpc
        """
        
        rpc = urlfetch.create_rpc(**kwds)
        precondition(is_valid_lat(lat), lat)
        precondition(is_valid_lon(lon), lon)
        endpoint = self._endpoint('context', lat=lat, lon=lon)
        headers = self._headers(endpoint, 'GET')
        urlfetch.make_fetch_call(rpc, endpoint, headers=headers)
        return rpc
        
        
    def get_context_result(self, rpc):
        result = rpc.get_result()
        if not 200 <= result.status_code < 400:
            raise APIError(result.status_code, result.content, self.headers)
        return json_decode(result.content)
