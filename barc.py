# -*- coding: utf-8 -*-
# Copyright 2017 Spajderix <spajderix@gmail.com>
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.
#
from urllib import quote, urlencode
from urllib2 import Request, urlopen
import ssl
from base64 import b64encode
from xml.dom.minidom import parseString, parse, getDOMImplementation, Node
from datetime import datetime
import re


date_format = r'%a, %d %b %Y %H:%M:%S %z'
date_format_notz = r'%a, %d %b %Y %H:%M:%S'


class BESCoreElement(object):
    __slots__ = ('base_node', '_base_node_name', '_field_order')

    def __init__(self, o=None):
        #self._field_order = []
        if o == None:
            self._create_empty_element()
        else:
            try:
                tmp = o.nodeName
            except AttributeError as e:
                raise ValueError('Expecting xml Element')
            else:
                self.base_node = o

    def _create_empty_element(self):
        impl = getDOMImplementation()
        xmlo = impl.createDocument(None, self._base_node_name, None)
        self.base_node = xmlo.childNodes[0]
        self.base_node.appendChild(xmlo.createTextNode(''))

    def _exists_child_elem(self, ename):
        for elem in self.base_node.childNodes:
            if elem.nodeName == ename:
                return True
        return False

    def _create_child_elem(self, ename, simple_elem = True):
        findex = None
        for x in xrange(len(self._field_order)):
            if self._field_order[x] == ename:
                findex = x
                break
        if findex == None:
            raise NotImplementedError('Not sure if this is going to ever work')
        else:
            # now create new node
            new_node = self.base_node.ownerDocument.createElement(ename)
            if simple_elem:
                new_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
            putbeforeme = None
            for elem in self.base_node.childNodes:
                if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName not in self._field_order[:findex]:
                    putbeforeme = elem
                    break
            if putbeforeme != None:
                self.base_node.insertBefore(new_node, putbeforeme)
            else:
                self.base_node.appendChild(new_node)

    def _value_for_elem(self, ename):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == ename:
                try:
                    return elem.childNodes[0].nodeValue
                except IndexError as e:
                    return u''
        return None

    def _set_newvalue_for_elem(self, ename, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == ename:
                # first empty out previous value
                while (len(elem.childNodes)) != 0:
                    elem.childNodes.pop()
                # now create new text node
                tnode = self.base_node.ownerDocument.createTextNode(newvalue)
                # now append the value to doctree
                elem.childNodes.append(tnode)

class BESAPICoreElement(object):
    __slots__ = ('base_node',)

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






#### BES Elements ####
class MIMEField(BESCoreElement):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'MIMEField'
        super(MIMEField, self).__init__(*args, **kwargs)
        self._field_order = ('Name', 'Value')
    def _create_empty_element(self, *args, **kwargs):
        super(MIMEField, self)._create_empty_element(*args, **kwargs)
        name_node = self.base_node.ownerDocument.createElement('Name')
        name_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        value_node = self.base_node.ownerDocument.createElement('Value')
        value_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        self.base_node.appendChild(name_node)
        self.base_node.appendChild(value_node)

    @property
    def Name(self):
        return self._value_for_elem('Name')
    @Name.setter
    def Name(self, newvalue):
        if not self._exists_child_elem('Name'):
            self._create_child_elem('Name')
        self._set_newvalue_for_elem('Name', newvalue)
    @property
    def Value(self):
        return self._value_for_elem('Value')
    @Value.setter
    def Value(self, newvalue):
        if not self._exists_child_elem('Value'):
            self._create_child_elem('Value')
        self._set_newvalue_for_elem('Value', newvalue)

class BaseFixlet(BESCoreElement):
    def __init__(self, *args, **kwargs):
        try:
            tmp = self._base_node_name
        except AttributeError as e:
            self._base_node_name = 'BaseFixlet'
        super(BaseFixlet, self).__init__(*args, **kwargs)
        self._field_order = ('Title', 'Description', 'Relevance', 'GroupRelevance', 'Category', 'WizardData', 'DownloadSize', 'Source', 'SourceID', 'SourceReleaseDate', 'CVENames', 'SANSID', 'MIMEField', 'Domain', 'Delay')
    def _create_empty_element(self, *args, **kwargs):
        super(BaseFixlet, self)._create_empty_element(*args, **kwargs)
        title_node = self.base_node.ownerDocument.createElement('Title')
        title_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        description_node = self.base_node.ownerDocument.createElement('Description')
        description_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        relevance_node = self.base_node.ownerDocument.createElement('Relevance')
        relevance_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        self.base_node.appendChild(title_node)
        self.base_node.appendChild(description_node)
        self.base_node.appendChild(relevance_node)

    @property
    def Title(self):
        return self._value_for_elem('Title')
    @Title.setter
    def Title(self, newvalue):
        if len(newvalue) < 1 or len(newvalue) > 255:
            raise ValueError('Title can be between 1 and 255 characters long')
        if not self._exists_child_elem('Title'):
            self._create_child_elem('Title')
        self._set_newvalue_for_elem('Title', newvalue)

    @property
    def Description(self):
        return self._value_for_elem('Description')
    @Description.setter
    def Description(self, newvalue):
        if not self._exists_child_elem('Description'):
            self._create_child_elem('Description')
        self._set_newvalue_for_elem('Description', newvalue)

    @property
    def Relevance(self):
        rlist = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Relevance':
                rlist.append(elem.childNodes[0].nodeValue)
        return rlist
    @Relevance.setter
    def Relevance(self, newvalue):
        if type(newvalue) not in (list, tuple):
            raise TypeError('Always provide a list of relevance clauses to add')
        # first clear all relevance elements
        to_remove = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Relevance':
                to_remove.append(elem)
        for elem in to_remove:
            self.base_node.removeChild(elem)
        # now add all new relevance elements
        for x in xrange(len(newvalue)):
            self._create_child_elem('Relevance')
        # and add all proper values
        r_nodes = self.base_node.getElementsByTagName('Relevance')
        for x in xrange(len(newvalue)):
            r_nodes[x].childNodes[0].nodeValue = newvalue[x]

    @property
    def Category(self):
        return self._value_for_elem('Category')
    @Category.setter
    def Category(self, newvalue):
        if not self._exists_child_elem('Category'):
            self._create_child_elem('Category')
        self._set_newvalue_for_elem('Category', newvalue)

    @property
    def DownloadSize(self):
        return self._value_for_elem('DownloadSize')
    @DownloadSize.setter
    def DownloadSize(self, newvalue):
        if type(newvalue) is not int:
            raise TypeError('Needs to be an integer')
        if newvalue < 0:
            raise TypeError('Needs to be more or equal to 0')
        if not self._exists_child_elem('DownloadSize'):
            self._create_child_elem('DownloadSize')
        self._set_newvalue_for_elem('DownloadSize', newvalue)

    @property
    def Source(self):
        return self._value_for_elem('Source')
    @Source.setter
    def Source(self, newvalue):
        if not self._exists_child_elem('Source'):
            self._create_child_elem('Source')
        self._set_newvalue_for_elem('Source', newvalue)

    @property
    def SourceID(self):
        return self._value_for_elem('SourceID')
    @SourceID.setter
    def SourceID(self, newvalue):
        if not self._exists_child_elem('SourceID'):
            self._create_child_elem('SourceID')
        self._set_newvalue_for_elem('SourceID', newvalue)

    @property
    def SourceReleaseDate(self):
        return self._value_for_elem('SourceReleaseDate')
    @SourceReleaseDate.setter
    def SourceReleaseDate(self, newvalue):
        if not self._exists_child_elem('SourceReleaseDate'):
            self._create_child_elem('SourceReleaseDate')
        self._set_newvalue_for_elem('SourceReleaseDate', newvalue)

    @property
    def SourceSeverity(self):
        return self._value_for_elem('SourceSeverity')
    @SourceSeverity.setter
    def SourceSeverity(self, newvalue):
        if not self._exists_child_elem('SourceSeverity'):
            self._create_child_elem('SourceSeverity')
        self._set_newvalue_for_elem('SourceSeverity', newvalue)

    @property
    def CVSNames(self):
        return self._value_for_elem('CVSNames')
    @CVSNames.setter
    def CVSNames(self, newvalue):
        if not self._exists_child_elem('CVSNames'):
            self._create_child_elem('CVSNames')
        self._set_newvalue_for_elem('CVSNames', newvalue)

    @property
    def SANSID(self):
        return self._value_for_elem('SANSID')
    @SANSID.setter
    def SANSID(self, newvalue):
        if not self._exists_child_elem('SANSID'):
            self._create_child_elem('SANSID')
        self._set_newvalue_for_elem('SANSID', newvalue)

    @property
    def MIMEFields(self):
        m_list = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'MIMEField':
                m_list.append(MIMEField(elem))
        return m_list
    @MIMEFields.setter
    def MIMEFields(self, newvalue):
        if type(newvalue) not in (list, tuple):
            raise TypeError('Always provide a list of relevance clauses to add')
        for elem in newvalue:
            if type(elem) is not MIMEField:
                raise TypeError('List should contain MIMEField objects')
        # first clear all relevance elements
        to_remove = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'MIMEField':
                to_remove.append(elem)
        for elem in to_remove:
            self.base_node.removeChild(elem)
        # now add all new relevance elements
        for x in xrange(len(newvalue)):
            self._create_child_elem('MIMEField')
        # and add all proper values
        m_nodes = self.base_node.getElementsByTagName('MIMEField')
        for x in xrange(len(newvalue)):
            #r_nodes[x].childNodes[0].nodeValue = newvalue[x]
            self.base_node.replaceChild(newvalue[x].base_node, m_nodes[x])


    @property
    def Domain(self):
        return self._value_for_elem('Domain')
    @Domain.setter
    def Domain(self, newvalue):
        if type(newvalue) not in (str, unicode):
            raise TypeError('Needs to be string or unicode')
        if len(newvalue) != 4:
            raise ValueError('Domain needs to be exactly 4 characters long')
        if not self._exists_child_elem('Domain'):
            self._create_child_elem('Domain')
        self._set_newvalue_for_elem('Domain', newvalue)

    @property
    def Delay(self):
        return self._value_for_elem('Delay')
    @Delay.setter
    def Delay(self, newvalue):
        if re.search('^P([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\.[0-9]{1,6})?S)?)?$', newvalue) is None:
            raise ValueError('Incorrectly formatted delay duration')
        if not self._exists_child_elem('Delay'):
            self._create_child_elem('Delay')
        self._set_newvalue_for_elem('Delay', newvalue)




class Fixlet(BaseFixlet):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'Fixlet'
        super(Fixlet, self).__init__(*args, **kwargs)
        self._field_order = self._field_order + ('DefaultAction', 'Action')

class Task(BaseFixlet):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'Task'
        super(Task, self).__init__(*args, **kwargs)
        self._field_order = self._field_order + ('DefaultAction', 'Action')

class SiteSubscription(BESCoreElement):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'Subscription'
        super(SiteSubscription, self).__init__(*args, **kwargs)
        self._field_order = ('Mode', 'CustomGroup')

    @property
    def Mode(self):
        return self._value_for_elem('Mode')
    @Mode.setter
    def Mode(self, newvalue):
        if newvalue not in ('All', 'None', 'AdHoc', 'Custom'):
            raise ValueError('Mode can only be All, None, AdHoc or Custom')
        if not self._exists_child_elem('Mode'):
            self._create_child_elem('Mode')
        self._set_newvalue_for_elem('Mode', newvalue)

class Site(BESCoreElement):
    def __init__(self, *args, **kwargs):
        try:
            tmp = self._base_node_name
        except AttributeError as e:
            self._base_node_name = 'Site'
        super(Site, self).__init__(*args, **kwargs)
        self._field_order = ('Name', 'GatherURL', 'Description', 'Domain', 'GlobalReadPermission', 'Subscription')
    def _create_empty_element(self, *args, **kwargs):
        super(Site, self)._create_empty_element(*args, **kwargs)
        name_node = self.base_node.ownerDocument.createElement('Name')
        name_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        self.base_node.appendChild(name_node)

    @property
    def Name(self):
        return self._value_for_elem('Name')
    @Name.setter
    def Name(self, newvalue):
        if len(newvalue) > 255:
            raise ValueError('Name can only be 255 characters')
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Name':
                elem.childNodes[0].nodeValue = newvalue

    @property
    def GatherURL(self):
        return self._value_for_elem('GatherURL')
    @GatherURL.setter
    def GatherURL(self, newvalue):
        if not self._exists_child_elem('GatherURL'):
            self._create_child_elem('GatherURL')
        self._set_newvalue_for_elem('GatherURL', newvalue)

    @property
    def Description(self):
        return self._value_for_elem('Description')
    @Description.setter
    def Description(self, newvalue):
        if not self._exists_child_elem('Description'):
            self._create_child_elem('Description')
        self._set_newvalue_for_elem('Description', newvalue)

    @property
    def Domain(self):
        return self._value_for_elem('Domain')
    @Domain.setter
    def Domain(self, newvalue):
        if len(newvalue) != 4:
            raise ValueError('Domain must be a 4-character string')
        if not self._exists_child_elem('Domain'):
            self._create_child_elem('Domain')
        self._set_newvalue_for_elem('Domain', newvalue)

    @property
    def GlobalReadPermission(self):
        return self._value_for_elem('GlobalReadPermission')
    @GlobalReadPermission.setter
    def GlobalReadPermission(self, newvalue):
        if newvalue not in ('true', 'false'):
            raise ValueError('GlobalReadPermission can only be true or false')
        if not self._exists_child_elem('GlobalReadPermission'):
            self._create_child_elem('GlobalReadPermission')
        self._set_newvalue_for_elem('GlobalReadPermission')

    @property
    def Subscription(self):
        if not self._exists_child_elem('Subscription'):
            self._create_child_elem('Subscription')
        try:
            return self._subscription_o
        except AttributeError as e:
            for elem in self.base_node.childNodes:
                if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Subscription':
                    self._subscription_o = SiteSubscription(elem)
                    break
            return self._subscription_o

class ActionSite(Site):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'ActionSite'
        super(ActionSite, self).__init__(*args, **kwargs)
class CustomSite(Site):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'CustomSite'
        super(CustomSite, self).__init__(*args, **kwargs)
class ExternalSite(Site):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'ExternalSite'
        super(ExternalSite, self).__init__(*args, **kwargs)
        self._field_order = self._field_order + ('Masthead',)
    @property
    def Masthead(self):
        return self._value_for_elem('Masthead')
    @Masthead.setter
    def Masthead(self, newvalue):
        if not self._exists_child_elem('Masthead'):
            self._create_child_elem('Masthead')
        self._set_newvalue_for_elem('Masthead', newvalue)

class OperatorSite(Site):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'OperatorSite'
        super(OperatorSite, self).__init__(*args, **kwargs)
        self._field_order = ('Name', 'GatherURL')
    @property
    def Name(self):
        return self._value_for_elem('Name')
    @Name.setter
    def Name(self, newvalue):
        if len(newvalue) > 255:
            raise ValueError('Name can only be 255 characters')
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Name':
                elem.childNodes[0].nodeValue = newvalue
    @property
    def GatherURL(self):
        return self._value_for_elem('GatherURL')
    @GatherURL.setter
    def GatherURL(self, newvalue):
        if not self._exists_child_elem('GatherURL'):
            self._create_child_elem('GatherURL')
        self._set_newvalue_for_elem('GatherURL', newvalue)




#### BESAPI Elements ####
class APIComputerProperties(object):
    __slots__ = ('_nodes_list',)

    def __init__(self, nodes_list):
        self._nodes_list = []
        for elem in nodes_list:
            if elem.nodeName == 'Property':
                self._nodes_list.append(elem)

    def __len__(self):
        return len(self._nodes_list)

    def __getitem__(self, key):
        if type(key) not in (str, unicode):
            raise TypeError('Key should be a string or unicode')
        if self.keys().count(key) == 0:
            raise KeyError('Key {0} does not exist'.format(key))
        elif self.keys().count(key) > 1:
            tmplist = []
            for elem in self._nodes_list:
                if elem.attributes['Name'].nodeValue == key:
                    tmplist.append(elem.childNodes[0].nodeValue)
            return tmplist
        else:
            for elem in self._nodes_list:
                if elem.attributes['Name'].nodeValue == key:
                    return elem.childNodes[0].nodeValue
        raise KeyError('Key {0} does not exist'.format(key))

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def __iter__(self):
        for elem in self._nodes_list:
            yield elem

    def keys(self):
        return [elem.attributes['Name'].nodeValue for elem in self._nodes_list]
    def values(self):
        return [elem.childNodes[0].nodeValue for elem in self._nodes_list]
    def has_key(self, key):
        return key in self.keys()
    def iteritems(self):
        uniq_keys = []
        for elem in self.keys():
            if elem not in uniq_keys:
                uniq_keys.append(elem)
        for elem in uniq_keys:
            yield (elem, self.__getitem__(elem))

class APIComputer(BESAPICoreElement):
    __slots__ = ('Properties', )

    def __init__(self, *args, **kwargs):
        super(APIComputer, self).__init__(*args, **kwargs)
        self.Properties = APIComputerProperties([x for x in self.base_node.childNodes if x.nodeName == 'Property'])

    @property
    def ID(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ID':
                return elem.childNodes[0].nodeValue
    @ID.setter
    def ID(self, newval):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ID':
                elem.childNodes[0].nodeValue = newval

    @property
    def LastReportTime(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'LastReportTime':
                try:
                    return datetime.strptime(elem.childNodes[0].nodeValue, date_format)
                except ValueError as e:
                    # python2.7 in some versions seem to not understand time zone modifiers in time zone, hence:
                    return datetime.strptime(elem.childNodes[0].nodeValue[:-6], date_format_notz)
    @LastReportTime.setter
    def LastReportTime(self, newval):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'LastReportTime':
                try:
                    elem.childNodes[0].nodeValue = datetime.strftime(newval, date_format)
                except ValueError as e:
                    # once more, for the tz issue
                    elem.childNodes[0].nodeValue = '{0} +0000'.format(datetime.strftime(newval, date_format_notz))





class APIGenericSite(BESAPICoreElement):
    @property
    def Name(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Name':
                return elem.childNodes[0].nodeValue
    @Name.setter
    def Name(self, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Name':
                elem.childNodes[0].nodeValue = newvalue

    @property
    def DisplayName(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'DisplayName':
                return elem.childNodes[0].nodeValue
    @DisplayName.setter
    def DisplayName(self, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'DisplayName':
                elem.childNodes[0].nodeValue = newvalue

    @property
    def GatherURL(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'GatherURL':
                return elem.childNodes[0].nodeValue
    @GatherURL.setter
    def GatherURL(self, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'GatherURL':
                elem.childNodes[0].nodeValue = newvalue


class APIExternalSite(APIGenericSite):
    pass
class APICustomSite(APIGenericSite):
    pass
class APIOperatorSite(APIGenericSite):
    pass
class APIActionSite(APIGenericSite):
    pass




class APIGenericContent(BESAPICoreElement):
    @property
    def Name(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Name':
                return elem.childNodes[0].nodeValue
    @Name.setter
    def Name(self, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Name':
                elem.childNodes[0].nodeValue = newvalue

    @property
    def ID(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ID':
                return elem.childNodes[0].nodeValue
    @ID.setter
    def ID(self, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ID':
                elem.childNodes[0].nodeValue = newvalue

    @property
    def LastModified(self):
        try:
            return datetime.strptime(self.base_node.attributes['LastModified'].nodeValue, date_format)
        except ValueError as e:
            # when not understanding timezone, try this
            return datetime.strptime(self.base_node.attributes['LastModified'].nodeValue[:-6], date_format_notz)
    @LastModified.setter
    def LastModified(self, newvalue):
        try:
            self.base_node.attributes['LastModified'] = datetime.strftime(newvalue, date_format)
        except ValueError as e:
            self.base_node.attributes['LastModified'] = '{0} +0000'.format(datetime.strftime(newvalue, date_format_notz))

class APIFixlet(APIGenericContent):
    pass
class APITask(APIGenericContent):
    pass
class APIAnalysis(APIGenericContent):
    pass
class APIBaseline(APIGenericContent):
    pass
class APIAction(APIGenericContent):
    pass







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

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, k):
        if type(k) is not int:
            raise TypeError('Incorrect index type, should be int')
        elif k < 0 or k >= len(self.elements):
            raise IndexError('Index outside of list size')
        return self.elements[k]

    def __setitem__(self, k, v):
        if not isinstance(v, BESAPICoreElement) and not isinstance(v, BESCoreElement):
            raise TypeError('Value is not a subclass of BESAPICoreElement or BESCoreElement')
        elif type(k) is not int:
            raise TypeError('Incorrect index type, should be int')
        elif k < 0 or k >= len(self.elements):
            raise IndexError('Index outside of list size')

        for elem in self.base_node.childNodes:
            if elem.isSameNode(v.base_node):
                raise ValueError('This object is already added')

        to_replace = self.elements.pop(k)
        self.base_node.replaceChild(v.base_node, to_replace.base_node)
        self.elements.insert(k, v)
        return True

    def __delitem__(self, k):
        if type(k) is not int:
            raise TypeError('Incorrect index type, should be int')
        elif k < 0 or k >= len(self.elements):
            raise IndexError('Index outside of list size')
        to_remove = self.elements.pop(k)
        self.base_node.removeChild(to_remove.base_node)
        return True

    def append(self, v):
        if not isinstance(v, BESAPICoreElement) and not isinstance(v, BESCoreElement):
            raise TypeError('Value is not a subclass of BESAPICoreElement')

        for elem in self.base_node.childNodes:
            if elem.isSameNode(v.base_node):
                raise ValueError('This object is already added')

        self.base_node.appendChild(v.base_node)
        self.elements.append(v)

    def pop(self, k):
        if type(k) is not int:
            raise TypeError('Incorrect index type, should be int')
        elif k < 0 or k >= len(self.elements):
            raise IndexError('Index outside of list size')

        to_pop = self.elements.pop(k)
        self.base_node.removeChild(to_pop.base_node)
        return to_pop

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
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        self.base_node_name = 'BES'
        super(BESContainer, self).__init__(*args, **kwargs)
        self._parse_elements()

    def _parse_elements(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                if elem.nodeName == 'ExternalSite':
                    self.elements.append(ExternalSite(elem))
                elif elem.nodeName == 'ActionSite':
                    self.elements.append(ActionSite(elem))
                elif elem.nodeName == 'CustomSite':
                    self.elements.append(CustomSite(elem))
                elif elem.nodeName == 'OperatorSite':
                    self.elements.append(OperatorSite(elem))
                elif elem.nodeName == 'Fixlet':
                    self.elements.append(Fixlet(elem))
                elif elem.nodeName == 'Task':
                    self.elements.append(Task(elem))
                else:
                    self.elements.append(BESCoreElement(elem))

class BESAPIContainer(CoreContainer):
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        self.base_node_name = 'BESAPI'
        super(BESAPIContainer, self).__init__(*args, **kwargs)
        self._parse_elements()

    def _parse_elements(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                if elem.nodeName == 'Computer':
                    self.elements.append(APIComputer(elem))
                elif elem.nodeName == 'ExternalSite':
                    self.elements.append(APIExternalSite(elem))
                elif elem.nodeName == 'CustomSite':
                    self.elements.append(APICustomSite(elem))
                elif elem.nodeName == 'OperatorSite':
                    self.elements.append(APIOperatorSite(elem))
                elif elem.nodeName == 'ActionSite':
                    self.elements.append(APIActionSite(elem))
                elif elem.nodeName == 'Fixlet':
                    self.elements.append(APIFixlet(elem))
                elif elem.nodeName == 'Task':
                    self.elements.append(APITask(elem))
                elif elem.nodeName == 'Analysis':
                    self.elements.append(APIAnalysis(elem))
                elif elem.nodeName == 'Baseline':
                    self.elements.append(APIBaseline(elem))
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

    def get(self, resource, raw_response=False):
        req = self._build_base_request(resource)

        o = urlopen(req, **self._urlopen_kwargs)
        if o.code != 200:
            raise ValueError('Exit code different than 200')
        else:
            contents = o.read()
            if raw_response:
                return contents
            if re.search(r'\<BESAPI\s+', contents, re.MULTILINE) != None:
                return BESAPIContainer(contents)
            elif re.search(r'\<BES\s+', contents, re.MULTILINE) != None:
                return BESContainer(contents)
            else:
                raise ValueError('Not BESAPI nor BES xml element found')

    def post(self, resource, data, raw_response=False):
        req = self._build_base_request(resource)
        if isinstance(data, BESContainer) or isinstance(data, BESAPIContainer):
            req.add_data(data.base_node.toxml())
        else:
            req.add_data(data)

        o = urlopen(req, **self._urlopen_kwargs)
        if o.code != 200:
            raise ValueError('Exit code different than 200')
        else:
            contents = o.read()
            if raw_response:
                return contents
            if re.search(r'\<BESAPI\s+', contents, re.MULTILINE) != None:
                return BESAPIContainer(contents)
            elif re.search(r'\<BES\s+', contents, re.MULTILINE) != None:
                return BESContainer(contents)
            else:
                raise ValueError('Not BESAPI nor BES xml element found')

    def put(self, resource, data, raw_response=False):
        req = self._build_base_request(resource)
        if isinstance(data, BESContainer) or isinstance(data, BESAPIContainer):
            req.add_data(data.base_node.toxml())
        else:
            req.add_data(data)
        req.get_method = lambda: 'PUT'

        o = urlopen(req, **self._urlopen_kwargs)
        if o.code != 200:
            raise ValueError('Exit code different than 200')
        else:
            contents = o.read()
            if raw_response:
                return contents
            if re.search(r'\<BESAPI\s+', contents, re.MULTILINE) != None:
                return BESAPIContainer(contents)
            elif re.search(r'\<BES\s+', contents, re.MULTILINE) != None:
                return BESContainer(contents)
            else:
                raise ValueError('Not BESAPI nor BES xml element found')

    def delete(self, resource, raw_response=False):
        req = self._build_base_request(resource)
        req.get_method = lambda: 'DELETE'

        o = urlopen(req, **self._urlopen_kwargs)
        if o.code != 200:
            raise ValueError('Exit code different than 200')
        else:
            contents = o.read()
            if raw_response:
                return contents
            if re.search(r'\<BESAPI\s+', contents, re.MULTILINE) != None:
                return BESAPIContainer(contents)
            elif re.search(r'\<BES\s+', contents, re.MULTILINE) != None:
                return BESContainer(contents)
            elif contents == 'ok':
                return True
            else:
                return contents
