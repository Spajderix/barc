# -*- coding: utf-8 -*-
from urllib import quote, urlencode
from urllib2 import Request, urlopen
import ssl
from base64 import b64encode
from xml.dom.minidom import parseString, parse, getDOMImplementation
from datetime import datetime


class BESCoreElement(object):
    pass

class BESAPICoreElement(object):
    __slots__ = ('base_node')

    def __init__(self, o):
        try:
            tmp = o.nodeName
        except AttributeError as e:
            raise ValueError('Expecting xml Element')
        else:
            self.base_node = o

    @property
    def Resource(self):
        return self.base_node.getAttribute('Resource')
    @Resource.setter
    def Resource(self, newval):
        self.base_node.setAttribute('Resource', newval)

class APIComputer(BESAPICoreElement):
    __slots__ = ('date_format', 'date_format_notz')
    date_format = r'%a, %d %b %Y %H:%M:%S %z'
    date_format_notz = r'%a, %d %b %Y %H:%M:%S'

    @property
    def ID(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == 1 and elem.nodeName == 'ID':
                return elem.childNodes[0].nodeValue
    @ID.setter
    def ID(self, newval):
        for elem in self.base_node.childNodes:
            if elem.nodeType == 1 and elem.nodeName == 'ID':
                elem.childNodes[0].nodeValue = newval

    @property
    def LastReportTime(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == 1 and elem.nodeName == 'LastReportTime':
                try:
                    return datetime.strptime(elem.childNodes[0].nodeValue, self.date_format)
                except ValueError as e:
                    # python2.7 in some versions seem to not understand time zone modifiers in time zone, hence:
                    return datetime.strptime(elem.childNodes[0].nodeValue[:-6], self.date_format_notz)
    @LastReportTime.setter
    def LastReportTime(self, newval):
        for elem in self.base_node.childNodes:
            if elem.nodeType == 1 and elem.nodeName == 'LastReportTime':
                try:
                    elem.childNodes[0].nodeValue = datetime.strftime(newval, self.date_format)
                except ValueError as e:
                    # once more, for the tz issue
                    elem.childNodes[0].nodeValue = '{0} +0000'.format(datetime.strftime(newval, self.date_format_notz))


class CoreContainer(object):
    __slots__ = ('xmlo', 'base_node', 'base_node_name', 'elements')

    def __init__(self, file_or_contents=None):
        self.xmlo = None
        self.elements = []

        if type(file_or_contents) in (str, unicode, file):
            self._parse_content(file_or_contents)
        elif file_or_contents == None:
            self._create_empty_container()
        else:
            raise ValueError('Needs to be file object or string containing xml definition')

    def _create_empty_container(self):
        impl = getDOMImplementation()
        self.xmlo = impl.createDocument(None, self.base_node_name, None)
        self.base_node = self.xmlo.documentElement

        self.base_node.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        self.base_node.setAttribute('xsi:noNamespaceSchemaLocation', '{0}.xsd'.format(self.base_node_name))
        self.base_node.appendChild(self.xmlo.createTextNode(''))

    def _parse_content(self, content):
        if type(content) in (str, unicode):
            self.xmlo = parseString(content)
        else:
            self.xmlo = parse(content)
        self.base_node = self.xmlo.documentElement
        if self.base_node.nodeName != self.base_node_name:
            raise ValueError('Wrong base element. Expected BESAPI Element')

class BESContainer(CoreContainer):
    base_node_name = 'BES'

class BESAPIContainer(CoreContainer):
    base_node_name = 'BESAPI'

    def __init__(self, *args, **kwargs):
        super(BESAPIContainer, self).__init__(*args, **kwargs)
        self._parse_elements()

    def _parse_elements(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == 1:
                if elem.nodeName == 'Computer':
                    self.elements.append(APIComputer(elem))
                else:
                    self.elements.append(BESAPICoreElement(elem))




class Client(object):
    __slots__ = ('hostname', 'port', 'user', 'password', 'rewrite_resource', '_verify_cert', '_ssl_c', '_urlopen_kwargs')

    def __init__(self, hostname, port, user, password, rewrite_resource=False, verify_certificate=False):
        self.hostname = hostname
        self.port = port
        self.user = user
        self.password = password
        self.rewrite_resource = rewrite_resource
        self.verify_cert = verify_certificate

    @property
    def verify_cert(self):
        return self._verify_cert

    @verify_cert.setter
    def verify_cert(self, val):
        if val not in (0,1,True,False):
            raise ValueError('Not a bolean value')
        self._verify_cert = val
        if self._verify_cert:
            self._enable_certverify()
        else:
            self._disable_certverify()

    def _disable_certverify(self):
        self._ssl_c = ssl.create_default_context()
        self._ssl_c.check_hostname = False
        self._ssl_c.verify_mode = ssl.CERT_NONE
        self._urlopen_kwargs={'context': self._ssl_c}
    def _enable_certverify(self):
        self._ssl_c = None
        self._urlopen_kwargs={}

    def _build_resource_url(self, resource):
        if resource[:4] == '/api':
            return 'https://{0}:{1}{2}'.format(self.hostname, self.port, resource)
        else:
            return 'https://{0}:{1}/api{2}'.format(self.hostname, self.port, resource)

    def _build_base_request(self, resource):
        if self.rewrite_resource:
            raise NotImplementedError()
        if resource[0] == '/':
            resource = self._build_resource_url(resource)
        req = Request(resource)
        encoded_creds=b64encode('{0}:{1}'.format(self.user, self.password))
        auth_token = 'Basic {0}'.format(encoded_creds)
        req.add_header('Authorization', auth_token)
        return req

    def get(self, resource):
        req = self._build_base_request(resource)
        return urlopen(req, **self._urlopen_kwargs).read()

    def post(self):
        raise NotImplementedError()
    def delete(self):
        raise NotImplementedError()
