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
simple_datetime_format = r'%Y-%m-%d %H:%M:%S'

search_by_property_relevance = 'exists ({0}) whose (it as string as lowercase {1} "{2}" as lowercase)'


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

    def _exists_child_elem_attr(self, ename, attr_name):
        enode = self._get_child_elem(ename)
        if enode is None:
            return False
        return enode.hasAttribute(attr_name)

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
            return new_node

    def _create_child_elem_with_attributes(self, ename, attrs={}, simple_elem = True):
        new_node = self._create_child_elem(ename, simple_elem)
        for k,v in attrs.iteritems():
            tmp = new_node.setAttribute(k, v)
        return new_node

    def _get_child_elem(self, ename):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == ename:
                return elem
        return None

    def _value_for_elem(self, ename):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == ename:
                try:
                    return elem.childNodes[0].nodeValue
                except IndexError as e:
                    return u''
        return None

    def _value_for_elem_attr(self, ename, attr_name):
        enode = self._get_child_elem(ename)
        if enode is None:
            return None
        if not enode.hasAttribute(attr_name):
            return None
        return enode.getAttribute(attr_name)

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

    def _set_newattr_for_elem(self, ename, attr_name, attr_value):
        enode = self._get_child_elem(ename)
        if enode is None:
            return False
        return enode.setAttribute(attr_name, attr_value)


    def _bool2str(self, v):
        if v not in (True, False):
            raise ValueError('Boolean types only')
        if v:
            return 'true'
        return 'false'
    def _str2bool(self, v):
        if v not in ('true', 'false', '1', '0'):
            raise ValueError('Boolean string representations only')
        if v == 'true' or v == '1':
            return True
        return False

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





#### Reusable properties ####
#
# Following classes contain  reusable properties,
# which are complex enough to move them for subclassing
#
####
class SuccessCriteriaProperty(object):
    @property
    def SuccessCriteria(self):
        if not self._exists_child_elem('SuccessCriteria'):
            return None
        sc_node = self._get_child_elem('SuccessCriteria')
        if sc_node.getAttribute('Option') in ('RunToCompletion', 'OriginalRelevance'):
            return sc_node.getAttribute('Option')
        else:
            return self._value_for_elem('SuccessCriteria')
    @SuccessCriteria.setter
    def SuccessCriteria(self, newvalue):
        if not self._exists_child_elem('SuccessCriteria'):
            self._create_child_elem('SuccessCriteria')
        # clear success criteria of all it's subnodes
        sc_node = self._get_child_elem('SuccessCriteria')
        while len(sc_node.childNodes) > 0:
            sc_node.removeChild(sc_node.childNodes[0])

        if newvalue in ('RunToCompletion', 'OriginalRelevance'):
            sc_node.setAttribute('Option', newvalue)
        else:
            sc_node.setAttribute('Option', 'CustomRelevance')
            sc_node.appendChild(self.base_node.ownerDocument.createTextNode(newvalue))

    @property
    def SuccessCriteriaLocked(self):
        if self._value_for_elem('SuccessCriteriaLocked') is None:
            return None
        return self._str2bool(self._value_for_elem('SuccessCriteriaLocked'))
    @SuccessCriteriaLocked.setter
    def SuccessCriteriaLocked(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('SuccessCriteriaLocked can only be true or false')
        if not self._exists_child_elem('SuccessCriteriaLocked'):
            self._create_child_elem('SuccessCriteriaLocked')
        self._set_newvalue_for_elem('SuccessCriteriaLocked', self._bool2str(newvalue))


class ParameterProperty(object):
    @property
    def Parameter(self):
        if not self._exists_child_elem('Parameter'):
            return None
        out = {}
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Parameter':
                try:
                    out[elem.getAttribute('Name')] = elem.childNodes[0].nodeValue
                except Exception as e:
                    pass # if something is wrong with a parameter, we ignore it
        return out
    @Parameter.setter
    def Parameter(self, newvalue):
        if not isinstance(newvalue, dict):
            raise ValueError('Parameter will only accept a dictionary of parameters')
        # clear all current parameters
        while self._exists_child_elem('Parameter'):
            n = self._get_child_elem('Parameter')
            self.base_node.removeChild(n)
        for x in xrange(len(newvalue.keys())):
            self._create_child_elem('Parameter', False)
        plist = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Parameter':
                plist.append(elem)
        for k,v in newvalue.iteritems():
            pnode = plist.pop(0)
            pnode.setAttribute('Name', k)
            pnode.appendChild(pnode.ownerDocument.createTextNode(v))

    @property
    def SecureParameter(self):
        if not self._exists_child_elem('SecureParameter'):
            return None
        out = {}
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'SecureParameter':
                try:
                    out[elem.getAttribute('Name')] = elem.childNodes[0].nodeValue
                except Exception as e:
                    pass # if something is wrong with a parameter, we ignore it
        return out
    @SecureParameter.setter
    def SecureParameter(self, newvalue):
        if not isinstance(newvalue, dict):
            raise ValueError('SecureParameter will only accept a dictionary of parameters')
        # clear all current parameters
        while self._exists_child_elem('SecureParameter'):
            n = self._get_child_elem('SecureParameter')
            self.base_node.removeChild(n)
        for x in xrange(len(newvalue.keys())):
            self._create_child_elem('SecureParameter', False)
        plist = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'SecureParameter':
                plist.append(elem)
        for k,v in newvalue.iteritems():
            pnode = plist.pop(0)
            pnode.setAttribute('Name', k)
            pnode.appendChild(pnode.ownerDocument.createTextNode(v))


class ActionScriptProperty(object):
    @property
    def ActionScript(self):
        return self._value_for_elem('ActionScript')
    @ActionScript.setter
    def ActionScript(self, newvalue):
        if not self._exists_child_elem('ActionScript'):
            self._create_child_elem('ActionScript')
        self._set_newvalue_for_elem('ActionScript', newvalue)

    @property
    def MIMEType(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ActionScript':
                return elem.getAttribute('MIMEType')
    @MIMEType.setter
    def MIMEType(self, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ActionScript':
                elem.setAttribute('MIMEType', newvalue)
                break


class MIMEFieldProperty(object):
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
        # first clear all MIMEField elements
        to_remove = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'MIMEField':
                to_remove.append(elem)
        for elem in to_remove:
            self.base_node.removeChild(elem)
        # now add all new MIMEField elements
        for x in xrange(len(newvalue)):
            self._create_child_elem('MIMEField')
        # and add all proper values
        m_nodes = self.base_node.getElementsByTagName('MIMEField')
        for x in xrange(len(newvalue)):
            #r_nodes[x].childNodes[0].nodeValue = newvalue[x]
            self.base_node.replaceChild(newvalue[x].base_node, m_nodes[x])


class RelevanceProperty(object):
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

class ComputerGroup(BESCoreElement):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'ComputerGroup'
        super(ComputerGroup, self).__init__(*args, **kwargs)
        self._field_order = ('Title', 'Domain', 'JoinByIntersection', 'IsDynamic', 'EvaluateOnClient', 'SearchComponentRelevance', 'SearchComponentPropertyReference', 'SearchComponentGroupReference')
    def _create_empty_element(self, *args, **kwargs):
        super(ComputerGroup, self)._create_empty_element(*args, **kwargs)
        title_node = self.base_node.ownerDocument.createElement('Title')
        title_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        jbi_node = self.base_node.ownerDocument.createElement('JoinByIntersection')
        jbi_node.appendChild(self.base_node.ownerDocument.createTextNode('false'))
        self.base_node.appendChild(title_node)
        self.base_node.appendChild(jbi_node)

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
    def JoinByIntersection(self):
        return self._value_for_elem('JoinByIntersection')
    @JoinByIntersection.setter
    def JoinByIntersection(self, newvalue):
        if newvalue not in ('True', 'TRUE', 'true', 'False', 'FALSE', 'false'):
            raise ValueError('JoinByIntersection can only be "true" or "false"')
        if newvalue in ('true', 'TRUE', 'True'):
            newvalue = 'true'
        elif newvalue in ('false', 'FALSE', 'False'):
            newvalue = 'false'
        if not self._exists_child_elem('JoinByIntersection'):
            self._create_child_elem('JoinByIntersection')
        self._set_newvalue_for_elem('JoinByIntersection', newvalue)

    @property
    def IsDynamic(self):
        return self._value_for_elem('IsDynamic')
    @IsDynamic.setter
    def IsDynamic(self, newvalue):
        if newvalue not in ('True', 'TRUE', 'true', 'False', 'FALSE', 'false'):
            raise ValueError('IsDynamic can only be "true" or "false"')
        if newvalue in ('true', 'TRUE', 'True'):
            newvalue = 'true'
        elif newvalue in ('false', 'FALSE', 'False'):
            newvalue = 'false'
        if not self._exists_child_elem('IsDynamic'):
            self._create_child_elem('IsDynamic')
        self._set_newvalue_for_elem('IsDynamic', newvalue)

    @property
    def EvaluateOnClient(self):
        return self._value_for_elem('EvaluateOnClient')
    @EvaluateOnClient.setter
    def EvaluateOnClient(self, newvalue):
        if newvalue not in ('True', 'TRUE', 'true', 'False', 'FALSE', 'false'):
            raise ValueError('EvaluateOnClient can only be "true" or "false"')
        if newvalue in ('true', 'TRUE', 'True'):
            newvalue = 'true'
        elif newvalue in ('false', 'FALSE', 'False'):
            newvalue = 'false'
        if not self._exists_child_elem('EvaluateOnClient'):
            self._create_child_elem('EvaluateOnClient')
        self._set_newvalue_for_elem('EvaluateOnClient', newvalue)

    @property
    def MatchCondition(self):
        if self.JoinByIntersection == 'true':
            return 'all'
        return 'any'
    @MatchCondition.setter
    def MatchCondition(self, newvalue):
        if newvalue not in ('any', 'all'):
            raise ValueError('MatchCondition can only be "any" or "all"')
        if newvalue == 'any':
            self.JoinByIntersection = 'false'
        elif newvalue == 'all':
            self.JoinByIntersection = 'true'


    def _delete_subscriptionlist(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                if elem.nodeName in ('SearchComponentRelevance', 'SearchComponentGroupReference', 'SearchComponentPropertyReference'):
                    self.base_node.removeChild(elem)

    def _parse_relevance_node(self, rel_node):
        comp = rel_node.getAttribute('Comparison')
        rel = ''
        for elem in rel_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Relevance':
                try:
                    rel = elem.childNodes[0].nodeValue
                except IndexError as e:
                    rel = ''
                break
        return {
            'type': 'relevance',
            'comparison': comp,
            'relevance': rel
        }

    def _parse_computergroup_node(self, cg_node):
        gr_name = cg_node.getAttribute('GroupName')
        comp = cg_node.getAttribute('Comparison')
        return {
            'type': 'computer_group',
            'comparison': comp,
            'group_name': gr_name
        }

    def _parse_property_node(self, prop_node):
        comp = prop_node.getAttribute('Comparison')
        prop_name = prop_node.getAttribute('PropertyName')
        search_text = ''
        rel = ''
        for elem in prop_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                if elem.nodeName == 'SearchText':
                    try:
                        search_text = elem.childNodes[0].nodeValue
                    except KeyError as e:
                        pass
                elif elem.nodeName == 'Relevance':
                    try:
                        rel = elem.childNodes[0].nodeValue
                    except KeyError as e:
                        pass
        return {
            'type': 'property',
            'search_text': search_text,
            'relevance': rel,
            'property_name': prop_name,
            'comparison': comp
        }

    def _insert_relevance_node(self, definition):
        if not definition.has_key('comparison'):
            raise ValueError('Required component "comparison" missing for relevance based subscription definition')
        elif not definition.has_key('relevance'):
            raise ValueError('Required component "relevance" missing for relevance based subscription definition')
        elif definition['comparison'] not in ('IsTrue', 'IsFalse'):
            raise ValueError('Comparison for relevance based subscription can only be "IsTrue" or "IsFalse"')
        main_node = self.base_node.ownerDocument.createElement('SearchComponentRelevance')
        main_node.setAttribute('Comparison', definition['comparison'])
        rel_node = main_node.ownerDocument.createElement('Relevance')
        rel_node.appendChild(rel_node.ownerDocument.createTextNode(definition['relevance']))
        main_node.appendChild(rel_node)
        self.base_node.appendChild(main_node)
        return True

    def _insert_computergroup_node(self, definition):
        if not definition.has_key('comparison'):
            raise ValueError('Required component "comparison" missing for computer group based subscription definition')
        elif not definition.has_key('group_name'):
            raise ValueError('Required component "group_name" missing for computer group based subscription definition')
        elif definition['comparison'] not in ('IsMember', 'IsNotMember'):
            raise ValueError('Comparison for computer group based subscription can only be "IsMember" or "IsNotMember"')
        main_node = self.base_node.ownerDocument.createElement('SearchComponentGroupReference')
        main_node.setAttribute('Comparison', definition['comparison'])
        main_node.setAttribute('GroupName', definition['group_name'])
        self.base_node.appendChild(main_node)
        return True

    def _insert_property_node(self, definition):
        if not definition.has_key('comparison'):
            raise ValueError('Required component "comparison" missing for property based subscription definition')
        elif not definition.has_key('relevance'):
            raise ValueError('Required component "relevance" missing for property based subscription definition')
        elif not definition.has_key('search_text'):
            raise ValueError('Required component "search_text" missing for property based subscription definition')
        elif not definition.has_key('property_name'):
            raise ValueError('Required component "property_name" missing for property based subscription definition')
        elif definition['comparison'] not in ('Contains', 'DoesNotContain', 'Equals', 'DoesNotEqual'):
            raise ValueError('Comparison for computer group based subscription can only be "Contains", "DoesNotContain", "Equals", "DoesNotEqual"')

        main_node = self.base_node.ownerDocument.createElement('SearchComponentPropertyReference')
        main_node.setAttribute('Comparison', definition['comparison'])
        main_node.setAttribute('PropertyName', definition['property_name'])

        rel_node = main_node.ownerDocument.createElement('Relevance')
        rel_node.appendChild(rel_node.ownerDocument.createTextNode(definition['relevance']))
        st_node = main_node.ownerDocument.createElement('SearchText')
        st_node.appendChild(st_node.ownerDocument.createTextNode(definition['search_text']))

        main_node.appendChild(st_node)
        main_node.appendChild(rel_node)
        self.base_node.appendChild(main_node)
        return True

    @property
    def SubscriptionList(self):
        out = []
        for subs_elem in self.base_node.childNodes:
            if subs_elem.nodeType == Node.ELEMENT_NODE:
                if subs_elem.nodeName == 'SearchComponentRelevance':
                    out.append(self._parse_relevance_node(subs_elem))
                elif subs_elem.nodeName == 'SearchComponentGroupReference':
                    out.append(self._parse_computergroup_node(subs_elem))
                elif subs_elem.nodeName == 'SearchComponentPropertyReference':
                    out.append(self._parse_property_node(subs_elem))
        return out
    @SubscriptionList.setter
    def SubscriptionList(self, newvalue):
        if type(newvalue) not in (list, tuple):
            raise ValueError('SubscriptionList can only be a list or tuple')
        for elem in newvalue:
            if type(elem) is not dict:
                raise ValueError('SubscriptionList components must be dict')
        # need to clear out current subscription list before loading up new one
        self._delete_subscriptionlist()
        # now to adding each custom subscription into the xml
        for elem in newvalue:
            t = elem.get('type', None)
            if t == 'property':
                self._insert_property_node(elem)
            elif t == 'relevance':
                self._insert_relevance_node(elem)
            elif t == 'computer_group':
                self._insert_computergroup_node(elem)
            elif t is None:
                raise ValueError('Component has to have a type!')
            else:
                raise ValueError('Component type can be one of the following: "property", "relevance", "computer_group"')

    def appendProperty(self, property_elem, search_text, comparison = 'Contains', relevance_string=None):
        if isinstance(property_elem, Property):
            prop_name = property_elem.Name
            relevance_string = property_elem.Relevance
        else:
            prop_name = property_elem

        if comparison == 'Contains':
            comparison_rel = 'contains'
        elif comparison == 'DoesNotContain':
            comparison_rel = 'does not contain'
        elif comparison == 'Equals':
            comparison_rel = '='
        elif comparison == 'DoesNotEqual':
            comparison_rel = '!='
        else:
            comparison_rel = ''

        relevance_compiled = search_by_property_relevance.format(relevance_string, comparison_rel, search_text)
        return self._insert_property_node({'property_name': prop_name, 'comparison': comparison, 'search_text': search_text, 'relevance': relevance_compiled})

    def appendRelevance(self, relevance_string, comparison = 'IsTrue'):
        return self._insert_relevance_node({'relevance': relevance_string, 'comparison': comparison})

    def appendComputerGroup(self, computer_group, comparison='IsMember'):
        return self._insert_computergroup_node({'comparison': comparison, 'group_name': computer_group})

    def removeSubscription(self, x):
        try:
            x = int(x)
        except ValueError as e:
            raise ValueError('A positive integer must be provided')
        if x < 0:
            raise ValueError('A positive integer must be provided')
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName in ('SearchComponentRelevance', 'SearchComponentGroupReference', 'SearchComponentPropertyReference'):
                if x == 0:
                    cg_node.removeChild(elem)
                    return True
                x = x - 1
        raise ValueError('Subscription component index out of range')





class BaseFixlet(BESCoreElement, MIMEFieldProperty, RelevanceProperty):
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
        self._set_newvalue_for_elem('DownloadSize', str(newvalue))

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


class ActionSettings(BESCoreElement):
    def __init__(self, *args, **kwargs):
        try:
            self._base_node_name
        except AttributeError as e:
            self._base_node_name = 'Settings'
        super(ActionSettings, self).__init__(*args, **kwargs)
        self._field_order = ('ActionUITitle', 'PreActionShowUI', 'PreAction', 'HasRunningMessage', 'RunningMessage', 'HasTimeRange', 'TimeRange', 'HasStartTime', 'StartDateTimeOffset', 'StartDateTimeLocalOffset', 'StartDateTime', 'StartDateTimeLocal', 'HasEndTime', 'EndDateTimeOffset', 'EndDateTimeLocalOffset', 'EndDateTime', 'EndDateTimeLocal', 'HasDayOfWeekConstraint', 'DayOfWeekConstraint', 'UseUTCTime', 'ActiveUserRequirement', 'ActiveUserType', 'UIGroupConstraints', 'HasWhose', 'Whose', 'PreActionCacheDownload', 'Reapply', 'HasReapplyLimit', 'ReapplyLimit', 'HasReapplyInterval', 'ReapplyInterval', 'HasRetry', 'RetryCount', 'RetryWait', 'HasTemporalDistribution', 'TemporalDistribution', 'ContinueOnErrors', 'PostActionBehavior', 'IsOffer', 'AnnounceOffer', 'OfferCategory', 'OfferDescriptionHTML')

    @property
    def ActionUITitle(self):
        return self._value_for_elem('ActionUITitle')
    @ActionUITitle.setter
    def ActionUITitle(self, newvalue):
        if not self._exists_child_elem('ActionUITitle'):
            self._create_child_elem('ActionUITitle')
        self._set_newvalue_for_elem('ActionUITitle', newvalue)

    @property
    def PreActionShowUI(self):
        if self._value_for_elem('PreActionShowUI') is None:
            return None
        return self._str2bool(self._value_for_elem('PreActionShowUI'))
    @PreActionShowUI.setter
    def PreActionShowUI(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('PreActionShowUI can only be true or false')
        if not self._exists_child_elem('PreActionShowUI'):
            self._create_child_elem('PreActionShowUI')
        self._set_newvalue_for_elem('PreActionShowUI', self._bool2str(newvalue))

    @property
    def HasRunningMessage(self):
        if self._value_for_elem('HasRunningMessage') is None:
            return None
        return self._str2bool(self._value_for_elem('HasRunningMessage'))
    @HasRunningMessage.setter
    def HasRunningMessage(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('HasRunningMessage can only be true or false')
        # if it is set to false, then we should remove RunningMessage elem
        if not newvalue and self._exists_child_elem('RunningMessage'):
            rm_node = self._get_child_elem('RunningMessage')
            self.base_node.removeChild(rm_node)
        if not self._exists_child_elem('HasRunningMessage'):
            self._create_child_elem('HasRunningMessage')
        self._set_newvalue_for_elem('HasRunningMessage', self._bool2str(newvalue))

    @property
    def RunningMessage(self):
        if not self._exists_child_elem('RunningMessage'):
            return None
        rm_node = self._get_child_elem('RunningMessage')
        rm_title = ''
        rm_text = ''
        for elem in rm_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                try:
                    if elem.nodeName == 'Title':
                        rm_title = elem.childNodes[0].nodeValue
                    elif elem.nodeName == 'Text':
                        rm_text = elem.childNodes[0].nodeValue
                except IndexError as e:
                    pass # we simply ignore it and leave the string empty
        return (rm_title, rm_text)
    @RunningMessage.setter
    def RunningMessage(self, newvalue):
        if not isinstance(newvalue, (list, tuple)):
            raise ValueError('Acceptable value is either list or tuple with 2 elements inside')
        if len(newvalue) != 2:
            raise ValueError('Acceptable value is either list or tuple with 2 elements inside')
        if not self._exists_child_elem('RunningMessage'):
            self._create_child_elem('RunningMessage')
        rm_node = self._get_child_elem('RunningMessage')
        # empty the node before proceeding
        while len(rm_node.childNodes) > 0:
            rm_node.removeChild(rm_node.childNodes[0])
        rm_title = self.base_node.ownerDocument.createElement('Title')
        rm_title.appendChild(self.base_node.ownerDocument.createTextNode(newvalue[0]))
        rm_text = self.base_node.ownerDocument.createElement('Text')
        rm_text.appendChild(self.base_node.ownerDocument.createTextNode(newvalue[1]))
        rm_node.appendChild(rm_title)
        rm_node.appendChild(rm_text)
        if not self.HasRunningMessage:
            self.HasRunningMessage = True

    @property
    def HasStartTime(self):
        if self._value_for_elem('HasStartTime') is None:
            return None
        return self._str2bool(self._value_for_elem('HasStartTime'))
    @HasStartTime.setter
    def HasStartTime(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('HasStartTime can only be true or false')
        if not self._exists_child_elem('HasStartTime'):
            self._create_child_elem('HasStartTime')
        self._set_newvalue_for_elem('HasStartTime', self._bool2str(newvalue))
        # if it is false, then we should drop all StartDate... elements
        if not newvalue:
            n = self._get_child_elem('StartDateTimeOffset')
            if n is not None:
                self.base_node.removeChild(n)
            n = self._get_child_elem('StartDateTimeLocalOffset')
            if n is not None:
                self.base_node.removeChild(n)
            n = self._get_child_elem('StartDateTime')
            if n is not None:
                self.base_node.removeChild(n)
            n = self._get_child_elem('StartDateTimeLocal')
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def StartDateTimeOffset(self):
        return self._value_for_elem('StartDateTimeOffset')
    @StartDateTimeOffset.setter
    def StartDateTimeOffset(self, newvalue):
        if re.search('^\-?P([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\.[0-9]{1,6})?S)?)?$', newvalue) is None:
            raise ValueError('Incorrectly formatted offset.')
        if not self._exists_child_elem('StartDateTimeOffset'):
            self._create_child_elem('StartDateTimeOffset')
        self._set_newvalue_for_elem('StartDateTimeOffset', newvalue)
        if not self.HasStartTime:
            self.HasStartTime = True
        # if this one is set, the other 3 need to go
        for ename in ('StartDateTimeLocalOffset', 'StartDateTime', 'StartDateTimeLocal'):
            n = self._get_child_elem(ename)
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def StartDateTimeLocalOffset(self):
        return self._value_for_elem('StartDateTimeLocalOffset')
    @StartDateTimeLocalOffset.setter
    def StartDateTimeLocalOffset(self, newvalue):
        if re.search('^\-?P([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\.[0-9]{1,6})?S)?)?$', newvalue) is None:
            raise ValueError('Incorrectly formatted offset.')
        if not self._exists_child_elem('StartDateTimeLocalOffset'):
            self._create_child_elem('StartDateTimeLocalOffset')
        self._set_newvalue_for_elem('StartDateTimeLocalOffset', newvalue)
        if not self.HasStartTime:
            self.HasStartTime = True
        # if this one is set, the other 3 need to go
        for ename in ('StartDateTimeOffset', 'StartDateTime', 'StartDateTimeLocal'):
            n = self._get_child_elem(ename)
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def StartDateTime(self):
        if not self._exists_child_elem('StartDateTime'):
            return None
        return datetime.strptime(self._value_for_elem('StartDateTime'), simple_datetime_format)
    @StartDateTime.setter
    def StartDateTime(self, newvalue):
        if not isinstance(newvalue, datetime):
            raise ValueError('Only accepts datetime objects')
        if not self._exists_child_elem('StartDateTime'):
            self._create_child_elem('StartDateTime')
        self._set_newvalue_for_elem('StartDateTime', newvalue.strftime(simple_datetime_format))
        # if this one is set, the other 3 need to go
        for ename in ('StartDateTimeOffset', 'StartDateTimeLocalOffset', 'StartDateTimeLocal'):
            n = self._get_child_elem(ename)
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def StartDateTimeLocal(self):
        if not self._exists_child_elem('StartDateTimeLocal'):
            return None
        return datetime.strptime(self._value_for_elem('StartDateTimeLocal'), simple_datetime_format)
    @StartDateTimeLocal.setter
    def StartDateTimeLocal(self, newvalue):
        if not isinstance(newvalue, datetime):
            raise ValueError('Only accepts datetime objects')
        if not self._exists_child_elem('StartDateTimeLocal'):
            self._create_child_elem('StartDateTimeLocal')
        self._set_newvalue_for_elem('StartDateTimeLocal', newvalue.strftime(simple_datetime_format))
        # if this one is set, the other 3 need to go
        for ename in ('StartDateTimeOffset', 'StartDateTimeLocalOffset', 'StartDateTime'):
            n = self._get_child_elem(ename)
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def HasEndTime(self):
        if self._value_for_elem('HasEndTime') is None:
            return None
        return self._str2bool(self._value_for_elem('HasEndTime'))
    @HasEndTime.setter
    def HasEndTime(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('HasEndTime can only be true or false')
        if not self._exists_child_elem('HasEndTime'):
            self._create_child_elem('HasEndTime')
        self._set_newvalue_for_elem('HasEndTime', self._bool2str(newvalue))
        # if it is false, then we should drop all EndDate... elements
        if not newvalue:
            n = self._get_child_elem('EndDateTimeOffset')
            if n is not None:
                self.base_node.removeChild(n)
            n = self._get_child_elem('EndDateTimeLocalOffset')
            if n is not None:
                self.base_node.removeChild(n)
            n = self._get_child_elem('EndDateTime')
            if n is not None:
                self.base_node.removeChild(n)
            n = self._get_child_elem('EndDateTimeLocal')
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def EndDateTimeOffset(self):
        return self._value_for_elem('EndDateTimeOffset')
    @EndDateTimeOffset.setter
    def EndDateTimeOffset(self, newvalue):
        if re.search('^\-?P([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\.[0-9]{1,6})?S)?)?$', newvalue) is None:
            raise ValueError('Incorrectly formatted offset.')
        if not self._exists_child_elem('EndDateTimeOffset'):
            self._create_child_elem('EndDateTimeOffset')
        self._set_newvalue_for_elem('EndDateTimeOffset', newvalue)
        if not self.HasEndTime:
            self.HasEndTime = True
        # if this one is set, the other 3 need to go
        for ename in ('EndDateTimeLocalOffset', 'EndDateTime', 'EndDateTimeLocal'):
            n = self._get_child_elem(ename)
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def EndDateTimeLocalOffset(self):
        return self._value_for_elem('EndDateTimeLocalOffset')
    @EndDateTimeLocalOffset.setter
    def EndDateTimeLocalOffset(self, newvalue):
        if re.search('^\-?P([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\.[0-9]{1,6})?S)?)?$', newvalue) is None:
            raise ValueError('Incorrectly formatted offset.')
        if not self._exists_child_elem('EndDateTimeLocalOffset'):
            self._create_child_elem('EndDateTimeLocalOffset')
        self._set_newvalue_for_elem('EndDateTimeLocalOffset', newvalue)
        if not self.HasEndTime:
            self.HasEndTime = True
        # if this one is set, the other 3 need to go
        for ename in ('EndDateTimeOffset', 'EndDateTime', 'EndDateTimeLocal'):
            n = self._get_child_elem(ename)
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def EndDateTime(self):
        if not self._exists_child_elem('EndDateTime'):
            return None
        return datetime.strptime(self._value_for_elem('EndDateTime'), simple_datetime_format)
    @EndDateTime.setter
    def EndDateTime(self, newvalue):
        if not isinstance(newvalue, datetime):
            raise ValueError('Only accepts datetime objects')
        if not self._exists_child_elem('EndDateTime'):
            self._create_child_elem('EndDateTime')
        self._set_newvalue_for_elem('EndDateTime', newvalue.strftime(simple_datetime_format))
        # if this one is set, the other 3 need to go
        for ename in ('EndDateTimeOffset', 'EndDateTimeLocalOffset', 'EndDateTimeLocal'):
            n = self._get_child_elem(ename)
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def EndDateTimeLocal(self):
        if not self._exists_child_elem('EndDateTimeLocal'):
            return None
        return datetime.strptime(self._value_for_elem('EndDateTimeLocal'), simple_datetime_format)
    @EndDateTimeLocal.setter
    def EndDateTimeLocal(self, newvalue):
        if not isinstance(newvalue, datetime):
            raise ValueError('Only accepts datetime objects')
        if not self._exists_child_elem('EndDateTimeLocal'):
            self._create_child_elem('EndDateTimeLocal')
        self._set_newvalue_for_elem('EndDateTimeLocal', newvalue.strftime(simple_datetime_format))
        # if this one is set, the other 3 need to go
        for ename in ('EndDateTimeOffset', 'EndDateTimeLocalOffset', 'EndDateTime'):
            n = self._get_child_elem(ename)
            if n is not None:
                self.base_node.removeChild(n)

    @property
    def HasDayOfWeekConstraint(self):
        if not self._exists_child_elem('HasDayOfWeekConstraint'):
            return None
        return self._str2bool(self._value_for_elem('HasDayOfWeekConstraint'))
    @HasDayOfWeekConstraint.setter
    def HasDayOfWeekConstraint(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('HasDayOfWeekConstraint can only be true or false')
        if not self._exists_child_elem('HasDayOfWeekConstraint'):
            self._create_child_elem('HasDayOfWeekConstraint')
        self._set_newvalue_for_elem('HasDayOfWeekConstraint', self._bool2str(newvalue))
        # if it is false, then DayOfWeekConstraint should be dropped
        if not newvalue and self._exists_child_elem('DayOfWeekConstraint'):
            dwc_node = self._get_child_elem('DayOfWeekConstraint')
            self.base_node.removeChild(dwc_node)

    @property
    def DayOfWeekConstraint(self):
        if not self._exists_child_elem('DayOfWeekConstraint'):
            return None
        out = {'Sun': False, 'Mon': False, 'Tue': False, 'Wed': False, 'Thu': False, 'Fri': False, 'Sat': False}
        dwc_node = self._get_child_elem('DayOfWeekConstraint')
        for elem in dwc_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName in out.keys():
                try:
                    out[ele.nodeName] = self._str2bool(elem.childNodes[0].nodeValue)
                except Exception as e:
                    pass # we just want to skip if we're unable to extract
        return out
    @DayOfWeekConstraint.setter
    def DayOfWeekConstraint(self, newvalue):
        if not isinstance(newvalue, dict):
            raise ValueError('DayOfWeekContraint only accepts dictionary')
        if not self._exists_child_elem('DayOfWeekConstraint'):
            self._create_child_elem('DayOfWeekConstraint')
        dwc_node = self._get_child_elem('DayOfWeekConstraint')
        # remove all children before proceeding
        while len(dwc_node.childNodes) > 0:
            dwc_node.removeChild(dwc_node.childNodes[0])
        for k in ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'):
            sub_n = self.base_node.ownerDocument.createElement(k)
            sub_n.appendChild(self.base_node.ownerDocument.createTextNode(self._bool2str(newvalue.get(k, False))))
            dwc_node.appendChild(sub_n)
        # since this is set HasDayOfWeelConstraint should be true
        if not self.HasDayOfWeekConstraint:
            self.HasDayOfWeekConstraint = True

    @property
    def UseUTCTime(self):
        if not self._exists_child_elem('UseUTCTime'):
            return None
        return self._str2bool(self._value_for_elem('UseUTCTime'))
    @UseUTCTime.setter
    def UseUTCTime(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('UseUTCTime only accept true or false')
        if not self._exists_child_elem('UseUTCTime'):
            self._create_child_elem('UseUTCTime')
        self._set_newvalue_for_elem('UseUTCTime', self._bool2str(newvalue))

    @property
    def PreActionCacheDownload(self):
        if not self._exists_child_elem('PreActionCacheDownload'):
            return None
        return self._str2bool(self._value_for_elem('PreActionCacheDownload'))
    @PreActionCacheDownload.setter
    def PreActionCacheDownload(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('PreActionCacheDownload only accept true or false')
        if not self._exists_child_elem('PreActionCacheDownload'):
            self._create_child_elem('PreActionCacheDownload')
        self._set_newvalue_for_elem('PreActionCacheDownload', self._bool2str(newvalue))

    @property
    def Reapply(self):
        if not self._exists_child_elem('Reapply'):
            return None
        return self._str2bool(self._value_for_elem('Reapply'))
    @Reapply.setter
    def Reapply(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('Reapply only accept true or false')
        if not self._exists_child_elem('Reapply'):
            self._create_child_elem('Reapply')
        self._set_newvalue_for_elem('Reapply', self._bool2str(newvalue))

    @property
    def HasReapplyLimit(self):
        if not self._exists_child_elem('HasReapplyLimit'):
            return None
        return self._str2bool(self._value_for_elem('HasReapplyLimit'))
    @HasReapplyLimit.setter
    def HasReapplyLimit(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('HasReapplyLimit only accept true or false')
        if not self._exists_child_elem('HasReapplyLimit'):
            self._create_child_elem('HasReapplyLimit')
        self._set_newvalue_for_elem('HasReapplyLimit', self._bool2str(newvalue))

    @property
    def ReapplyLimit(self):
        return self._value_for_elem('ReapplyLimit')
    @ReapplyLimit.setter
    def ReapplyLimit(self, newvalue):
        if not isinstance(newvalue, int) or newvalue < 0:
            raise ValueError('ReapplyLimit can only be non-negative integer')
        if not self._exists_child_elem('ReapplyLimit'):
            self._create_child_elem('ReapplyLimit')
        self._set_newvalue_for_elem('ReapplyLimit', str(newvalue))

    @property
    def HasReapplyInterval(self):
        if not self._exists_child_elem('HasReapplyInterval'):
            return None
        return self._str2bool(self._value_for_elem('HasReapplyInterval'))
    @HasReapplyInterval.setter
    def HasReapplyInterval(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('HasReapplyInterval only accept true or false')
        if not self._exists_child_elem('HasReapplyInterval'):
            self._create_child_elem('HasReapplyInterval')
        self._set_newvalue_for_elem('HasReapplyInterval', self._bool2str(newvalue))

    @property
    def ReapplyInterval(self):
        return self._value_for_elem('ReapplyInterval')
    @ReapplyInterval.setter
    def ReapplyInterval(self, newvalue):
        if newvalue not in ("PT15M", "PT30M", "PT1H", "PT2H", "PT4H", "PT6H", "PT8H", "PT12H", "P1D", "P2D", "P3D", "P5D", "P7D", "P15D", "P30D"):
            raise ValueError('ReapplyInterval can only be one of the following: PT15M, PT30M, PT1H, PT2H, PT4H, PT6H, PT8H, PT12H, P1D, P2D, P3D, P5D, P7D, P15D, P30D')
        if not self._exists_child_elem('ReapplyInterval'):
            self._create_child_elem('ReapplyInterval')
        self._set_newvalue_for_elem('ReapplyInterval', newvalue)

    @property
    def HasRetry(self):
        if not self._exists_child_elem('HasRetry'):
            return None
        return self._str2bool(self._value_for_elem('HasRetry'))
    @HasRetry.setter
    def HasRetry(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('Reapply only accept true or false')
        if not self._exists_child_elem('HasRetry'):
            self._create_child_elem('HasRetry')
        self._set_newvalue_for_elem('HasRetry', self._bool2str(newvalue))

    @property
    def RetryCount(self):
        if not self._exists_child_elem('RetryCount'):
            return None
        return self._value_for_elem('RetryCount')
    @RetryCount.setter
    def RetryCount(self, newvalue):
        try:
            tmp = int(newvalue)
        except ValueError as e:
            raise ValueError('RetryCount has to be integer type')
        if tmp <= 0:
            raise ValueError('RetryCount has to be positive integer')
        if not self._exists_child_elem('RetryCount'):
            self._create_child_elem('RetryCount')
        self._set_newvalue_for_elem('RetryCount', str(newvalue))

    @property
    def RetryWait(self):
        return self._value_for_elem('RetryWait')
    @RetryWait.setter
    def RetryWait(self, newvalue):
        if newvalue not in ("PT15M", "PT30M", "PT1H", "PT2H", "PT4H", "PT6H", "PT8H", "PT12H", "P1D", "P2D", "P3D", "P5D", "P7D", "P15D", "P30D"):
            raise ValueError('ReapplyInterval can only be one of the following: PT15M, PT30M, PT1H, PT2H, PT4H, PT6H, PT8H, PT12H, P1D, P2D, P3D, P5D, P7D, P15D, P30D')
        if not self._exists_child_elem('RetryWait'):
            self._create_child_elem_with_attributes('RetryWait', {'Behavior': 'WaitForInterval'})
        self._set_newvalue_for_elem('RetryWait', newvalue)

    @property
    def RetryWaitBehavior(self):
        return self._value_for_elem_attr('RetryWait', 'Behavior')
    @RetryWaitBehavior.setter
    def RetryWaitBehavior(self, newvalue):
        if newvalue not in ("WaitForInterval","WaitForReboot"):
            raise ValueError('RetryWaitBehavior can be only WaitForInterval or WaitForReboot')
        if self.RetryWait is None:
            self.RetryWait = 'PT1H'
        if newvalue == 'WaitForReboot':
            self.RetryWait = 'PT1H'
        self._set_newattr_for_elem('RetryWait','Behavior',  newvalue)

    @property
    def HasTemporalDistribution(self):
        if not self._exists_child_elem('HasTemporalDistribution'):
            return None
        return self._str2bool(self._value_for_elem('HasTemporalDistribution'))
    @HasTemporalDistribution.setter
    def HasTemporalDistribution(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('HasTemporalDistribution can only be true or false')
        if not self._exists_child_elem('HasTemporalDistribution'):
            self._create_child_elem('HasTemporalDistribution')
        self._set_newvalue_for_elem('HasTemporalDistribution', self._bool2str(newvalue))
        # if this is false, drop TemporalDistribution
        if not newvalue and self._exists_child_elem('TemporalDistribution'):
            td_node = self._get_child_elem('TemporalDistribution')
            self.base_node.removeChild(td_node)

    @property
    def TemporalDistribution(self):
        return self._value_for_elem('TemporalDistribution')
    @TemporalDistribution.setter
    def TemporalDistribution(self, newvalue):
        if re.search('^P([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\.[0-9]{1,6})?S)?)?$', newvalue) is None:
            raise ValueError('Incorrect value for TemporalDistribution')
        if not self._exists_child_elem('TemporalDistribution'):
            self._create_child_elem('TemporalDistribution')
        self._set_newvalue_for_elem('TemporalDistribution', newvalue)
        # if this is set, then raise flag to true
        if not self.HasTemporalDistribution:
            self.HasTemporalDistribution = True

    @property
    def ContinueOnErrors(self):
        if not self._exists_child_elem('ContinueOnErrors'):
            return None
        return self._str2bool(self._value_for_elem('ContinueOnErrors'))
    @ContinueOnErrors.setter
    def ContinueOnErrors(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('ContinueOnErrors can only be true or false')
        if not self._exists_child_elem('ContinueOnErrors'):
            self._create_child_elem('ContinueOnErrors')
        self._set_newvalue_for_elem('ContinueOnErrors', self._bool2str(newvalue))

    @property
    def IsOffer(self):
        if not self._exists_child_elem('IsOffer'):
            return None
        return self._str2bool(self._value_for_elem('IsOffer'))
    @IsOffer.setter
    def IsOffer(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('IsOffer can only be true or false')
        if not self._exists_child_elem('IsOffer'):
            self._create_child_elem('IsOffer')
        self._set_newvalue_for_elem('IsOffer', self._bool2str(newvalue))

    @property
    def AnnounceOffer(self):
        if not self._exists_child_elem('AnnounceOffer'):
            return None
        return self._str2bool(self._value_for_elem('AnnounceOffer'))
    @AnnounceOffer.setter
    def AnnounceOffer(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('AnnounceOffer can only be true or false')
        if not self._exists_child_elem('AnnounceOffer'):
            self._create_child_elem('AnnounceOffer')
        self._set_newvalue_for_elem('AnnounceOffer', self._bool2str(newvalue))

    @property
    def OfferCategory(self):
        return self._value_for_elem('OfferCategory')
    @OfferCategory.setter
    def OfferCategory(self, newvalue):
        if not self._exists_child_elem('OfferCategory'):
            self._create_child_elem('OfferCategory')
        self._set_newvalue_for_elem('OfferCategory', newvalue)

    @property
    def OfferDescriptionHTML(self):
        return self._value_for_elem('OfferDescriptionHTML')
    @OfferDescriptionHTML.setter
    def OfferDescriptionHTML(self, newvalue):
        if not self._exists_child_elem('OfferDescriptionHTML'):
            self._create_child_elem('OfferDescriptionHTML')
        self._set_newvalue_for_elem('OfferDescriptionHTML', newvalue)




class FixletAction(BESCoreElement, ActionScriptProperty, SuccessCriteriaProperty):
    __slots__ = ('_settings_o', )

    def __init__(self, *args, **kwargs):
        try:
            self._base_node_name
        except AttributeError as e:
            self._base_node_name = 'Action'
        super(FixletAction, self).__init__(*args, **kwargs)
        self._field_order = ('Description', 'ActionScript', 'SuccessCriteria', 'SuccessCriteriaLocked', 'Settings', 'SettingsLocks')
        self._settings_o = None
    def _create_empty_element(self, *args, **kwargs):
        super(FixletAction, self)._create_empty_element(*args, **kwargs)
        actionscript_node = self.base_node.ownerDocument.createElement('ActionScript')
        actionscript_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        actionscript_node.setAttribute('MIMEType', 'application/x-Fixlet-Windows-Shell')
        self.base_node.appendChild(actionscript_node)
        self.base_node.setAttribute('ID', '')

    @property
    def ID(self):
        return self.base_node.getAttribute('ID')
    @ID.setter
    def ID(self, newvalue):
        self.base_node.setAttribute('ID', newvalue)

    @property
    def Description(self):
        if not self._exists_child_elem('Description'):
            return ''
        else:
            dnode = None
            output = ''
            for elem in self.base_node.childNodes:
                if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Description':
                    dnode = elem
                    break
            #get prelink content
            for elem in dnode.childNodes:
                if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'PreLink':
                    for prelink_elem in elem.childNodes:
                        if prelink_elem.nodeType == Node.TEXT_NODE or prelink_elem.nodeType == Node.CDATA_SECTION_NODE:
                            output = '{0}{1}'.format(output, prelink_elem.nodeValue)
                    break
            #get link content
            output = '{0}[LINK]'.format(output)
            for elem in dnode.childNodes:
                if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Link':
                    for prelink_elem in elem.childNodes:
                        if prelink_elem.nodeType == Node.TEXT_NODE or prelink_elem.nodeType == Node.CDATA_SECTION_NODE:
                            output = '{0}{1}'.format(output, prelink_elem.nodeValue)
                    break
            output = '{0}[/LINK]'.format(output)
            #get postlink content
            for elem in dnode.childNodes:
                if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'PostLink':
                    for prelink_elem in elem.childNodes:
                        if prelink_elem.nodeType == Node.TEXT_NODE or prelink_elem.nodeType == Node.CDATA_SECTION_NODE:
                            output = '{0}{1}'.format(output, prelink_elem.nodeValue)
                    break
            return output
    @Description.setter
    def Description(self, newvalue):
        if not self._exists_child_elem('Description'):
            self._create_child_elem('Description')
        #find description node and clear it of it's children
        dnode = None
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Description':
                dnode = elem
                break
        while len(dnode.childNodes) > 0:
            dnode.removeChild(dnode.childNodes[0])
        #parse out prelink,link and postlink sections based on [LINK]...[/LINK] tags
        m = re.search(r'^(.+?)\[LINK\](.+?)\[\/LINK\](.+?)$', newvalue)
        if m is None:
            raise ValueError('Incorrectly formatted description. Need to include [LINK]..[/LINK] tags to specify clickable part of the action description')
        else:
            prelink = self.base_node.ownerDocument.createElement('PreLink')
            prelink.appendChild(self.base_node.ownerDocument.createTextNode(m.group(1)))
            link = self.base_node.ownerDocument.createElement('Link')
            link.appendChild(self.base_node.ownerDocument.createTextNode(m.group(2)))
            postlink = self.base_node.ownerDocument.createElement('PostLink')
            postlink.appendChild(self.base_node.ownerDocument.createTextNode(m.group(3)))
            dnode.appendChild(prelink)
            dnode.appendChild(link)
            dnode.appendChild(postlink)

    @property
    def Settings(self):
        if self._settings_o is not None:
            return self._settings_o
        if not self._exists_child_elem('Settings'):
            self._create_child_elem('Settings')
        self._settings_o = ActionSettings(self._get_child_elem('Settings'))
        return self._settings_o


class FixletDefaultAction(FixletAction):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'DefaultAction'
        super(FixletDefaultAction, self).__init__(*args, **kwargs)
        self._field_order = ('Description', 'ActionScript', 'SuccessCriteria', 'SuccessCriteriaLocked', 'Settings', 'SettingsLocks')

class ActionManager(object):
    "This class will manage actions within elements like Fixlet or Task"
    __slots__ = ('_core_element_o', '_default_action', '_actions')
    def __init__(self, core_o):
        if not isinstance(core_o, BESCoreElement):
            raise ValueError('ActionManager will only handle objects based on BESCoreElement')
        self._core_element_o = core_o # this is an element object for which we will handle actions, e.g. Fixlet or Task
        self._default_action = None
        self._actions = []

        self._parse_actions()

    def __len__(self):
        return len(self._actions)

    def __getitem__(self, k):
        if type(k) is not int:
            raise TypeError('Incorrect index type, should be int')
        elif k < 0 or k >= len(self._actions):
            raise IndexError('Index outside of list size')
        return self._actions[k]

    def __setitem__(self, k, v):
        if not isinstance(v, FixletAction):
            raise TypeError('Value is not a subclass of FixletAction')
        elif type(k) is not int:
            raise TypeError('Incorrect index type, should be int')
        elif k < 0 or k >= len(self._actions):
            raise IndexError('Index outside of list size')

        for elem in self._core_element_o.base_node.childNodes:
            if elem.isSameNode(v.base_node):
                raise ValueError('This object is already added')

        to_replace = self._actions.pop(k)
        self._core_element_o.base_node.replaceChild(v.base_node, to_replace.base_node)
        self._actions.insert(k, v)
        v.ID = to_replace.ID
        return True

    def __delitem__(self, k):
        if type(k) is not int:
            raise TypeError('Incorrect index type, should be int')
        elif k < 0 or k >= len(self._actions):
            raise IndexError('Index outside of list size')
        to_remove = self._actions.pop(k)
        self._core_element_o.base_node.removeChild(to_remove.base_node)
        return True

    def _append_action_node(self, n):
        if len(self._actions) > 0:
            next_element_node = None # this will be next element node after last Action node
            found_action = False
            for elem in self._core_element_o.base_node.childNodes:
                if elem.nodeType == Node.ELEMENT_NODE:
                    if not found_action and elem.nodeName != 'Action':
                        continue
                    elif not found_action and elem.nodeName == 'Action':
                        found_action = True
                    elif found_action and elem.nodeName == 'Action':
                        continue
                    elif found_action and elem.nodeName != 'Action':
                        next_element_node = elem
                        break
            if next_element_node is None:
                self._core_element_o.base_node.appendChild(n)
            else:
                self._core_element_o.base_node.insertBefore(n, next_element_node)
        else:
            self._core_element_o._create_child_elem('Action')
            # now find the action node, and replace it
            to_replace = None
            for elem in self._core_element_o.base_node.childNodes:
                if elem.nodeType == Node.NODE_ELEMENT and elem.nodeName == 'Action':
                    to_replace = elem
                    break
            self._core_element_o.base_node.replaceChild(n, to_replace)

    def append(self, v):
        if not isinstance(v, FixletAction):
            raise TypeError('Value is not a subclass of FixletAction')

        for elem in self._core_element_o.base_node.childNodes:
            if elem.isSameNode(v.base_node):
                raise ValueError('This object is already added')

        self._enumerate_action(v)
        self._append_action_node(v.base_node)
        self._actions.append(v)

    def pop(self, k):
        if type(k) is not int:
            raise TypeError('Incorrect index type, should be int')
        elif k < 0 or k >= len(self._actions):
            raise IndexError('Index outside of list size')

        to_pop = self._actions.pop(k)
        self._core_element_o.base_node.removeChild(to_pop.base_node)
        return to_pop

    def _parse_actions(self):
        for elem in self._core_element_o.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                if elem.nodeName == 'DefaultAction':
                    self._default_action = FixletDefaultAction(elem)
                elif elem.nodeName == 'Action':
                    self._actions.append(FixletAction(elem))

    def _enumerate_action(self, a):
        current_max = 0
        try:
            if self._default_action is not None and int(self._default_action.ID) > current_max:
                current_max = int(self._default_action.ID)
        except ValueError as e:
            pass
        for elem in self._actions:
            try:
                if int(elem.ID) > current_max:
                    current_max = int(elem.ID)
            except ValueError as e:
                pass
        a.ID = '{0}'.format(current_max + 1)

    @property
    def DefaultAction(self):
        return self._default_action
    @DefaultAction.setter
    def DefaultAction(self, newvalue):
        if not isinstance(newvalue, FixletDefaultAction):
            raise ValueError('Incorrect type. Should be instance of FixletDefaultAction class')
        self._enumerate_action(newvalue)
        self._default_action = newvalue
        if not self._core_element_o._exists_child_elem('DefaultAction'):
            self._core_element_o._create_child_elem('DefaultAction')
        old_da_node = None
        for elem in self._core_element_o.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'DefaultAction':
                old_da_node = elem
                break
        self._core_element_o.base_node.replaceChild(self._default_action.base_node, old_da_node)




class Fixlet(BaseFixlet):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'Fixlet'
        super(Fixlet, self).__init__(*args, **kwargs)
        self._field_order = self._field_order + ('DefaultAction', 'Action')
        self.Actions = ActionManager(self)

class Task(BaseFixlet):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'Task'
        super(Task, self).__init__(*args, **kwargs)
        self._field_order = self._field_order + ('DefaultAction', 'Action')
        self.Actions = ActionManager(self)

class SiteSubscription(BESCoreElement):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'Subscription'
        super(SiteSubscription, self).__init__(*args, **kwargs)
        self._field_order = ('Mode', 'CustomGroup')


    def _create_empty_customgroup(self):
        if not self._exists_child_elem('CustomGroup'):
            self._create_child_elem_with_attributes('CustomGroup', {'JoinByIntersection': 'false'}, False)

    def _delete_customgroup(self):
        enode = self._get_child_elem('CustomGroup')
        if enode is not None:
            self.base_node.removeChild(enode)

    def _parse_relevance_node(self, rel_node):
        comp = rel_node.getAttribute('Comparison')
        rel = ''
        for elem in rel_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Relevance':
                try:
                    rel = elem.childNodes[0].nodeValue
                except IndexError as e:
                    rel = ''
                break
        return {
            'type': 'relevance',
            'comparison': comp,
            'relevance': rel
        }

    def _parse_computergroup_node(self, cg_node):
        gr_name = cg_node.getAttribute('GroupName')
        comp = cg_node.getAttribute('Comparison')
        return {
            'type': 'computer_group',
            'comparison': comp,
            'group_name': gr_name
        }

    def _parse_property_node(self, prop_node):
        comp = prop_node.getAttribute('Comparison')
        prop_name = prop_node.getAttribute('PropertyName')
        search_text = ''
        rel = ''
        for elem in prop_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                if elem.nodeName == 'SearchText':
                    try:
                        search_text = elem.childNodes[0].nodeValue
                    except KeyError as e:
                        pass
                elif elem.nodeName == 'Relevance':
                    try:
                        rel = elem.childNodes[0].nodeValue
                    except KeyError as e:
                        pass
        return {
            'type': 'property',
            'search_text': search_text,
            'relevance': rel,
            'property_name': prop_name,
            'comparison': comp
        }

    def _insert_relevance_node(self, definition):
        if not definition.has_key('comparison'):
            raise ValueError('Required component "comparison" missing for relevance based subscription definition')
        elif not definition.has_key('relevance'):
            raise ValueError('Required component "relevance" missing for relevance based subscription definition')
        elif definition['comparison'] not in ('IsTrue', 'IsFalse'):
            raise ValueError('Comparison for relevance based subscription can only be "IsTrue" or "IsFalse"')
        cg_node = self._get_child_elem('CustomGroup')
        main_node = cg_node.ownerDocument.createElement('SearchComponentRelevance')
        main_node.setAttribute('Comparison', definition['comparison'])
        rel_node = main_node.ownerDocument.createElement('Relevance')
        rel_node.appendChild(rel_node.ownerDocument.createTextNode(definition['relevance']))
        main_node.appendChild(rel_node)
        cg_node.appendChild(main_node)
        return True

    def _insert_computergroup_node(self, definition):
        if not definition.has_key('comparison'):
            raise ValueError('Required component "comparison" missing for computer group based subscription definition')
        elif not definition.has_key('group_name'):
            raise ValueError('Required component "group_name" missing for computer group based subscription definition')
        elif definition['comparison'] not in ('IsMember', 'IsNotMember'):
            raise ValueError('Comparison for computer group based subscription can only be "IsMember" or "IsNotMember"')
        cg_node = self._get_child_elem('CustomGroup')
        main_node = cg_node.ownerDocument.createElement('SearchComponentGroupReference')
        main_node.setAttribute('Comparison', definition['comparison'])
        main_node.setAttribute('GroupName', definition['group_name'])
        cg_node.appendChild(main_node)
        return True

    def _insert_property_node(self, definition):
        if not definition.has_key('comparison'):
            raise ValueError('Required component "comparison" missing for property based subscription definition')
        elif not definition.has_key('relevance'):
            raise ValueError('Required component "relevance" missing for property based subscription definition')
        elif not definition.has_key('search_text'):
            raise ValueError('Required component "search_text" missing for property based subscription definition')
        elif not definition.has_key('property_name'):
            raise ValueError('Required component "property_name" missing for property based subscription definition')
        elif definition['comparison'] not in ('Contains', 'DoesNotContain', 'Equals', 'DoesNotEqual'):
            raise ValueError('Comparison for computer group based subscription can only be "Contains", "DoesNotContain", "Equals", "DoesNotEqual"')

        cg_node = self._get_child_elem('CustomGroup')
        main_node = cg_node.ownerDocument.createElement('SearchComponentPropertyReference')
        main_node.setAttribute('Comparison', definition['comparison'])
        main_node.setAttribute('PropertyName', definition['property_name'])

        rel_node = main_node.ownerDocument.createElement('Relevance')
        rel_node.appendChild(rel_node.ownerDocument.createTextNode(definition['relevance']))
        st_node = main_node.ownerDocument.createElement('SearchText')
        st_node.appendChild(st_node.ownerDocument.createTextNode(definition['search_text']))

        main_node.appendChild(st_node)
        main_node.appendChild(rel_node)
        cg_node.appendChild(main_node)
        return True

    @property
    def SubscriptionList(self):
        if self.Mode != 'Custom':
            return None
        out = []
        subs_node = self._get_child_elem('CustomGroup')
        for subs_elem in subs_node.childNodes:
            if subs_elem.nodeType == Node.ELEMENT_NODE:
                if subs_elem.nodeName == 'SearchComponentRelevance':
                    out.append(self._parse_relevance_node(subs_elem))
                elif subs_elem.nodeName == 'SearchComponentGroupReference':
                    out.append(self._parse_computergroup_node(subs_elem))
                elif subs_elem.nodeName == 'SearchComponentPropertyReference':
                    out.append(self._parse_property_node(subs_elem))
        return tuple(out)
    @SubscriptionList.setter
    def SubscriptionList(self, newvalue):
        if type(newvalue) not in (list, tuple):
            raise ValueError('SubscriptionList can only be a list or tuple')
        for elem in newvalue:
            if type(elem) is not dict:
                raise ValueError('SubscriptionList components must be dict')
        # need to clear out current subscription list before loading up new one
        self._delete_customgroup()
        self._create_empty_customgroup()
        # now to adding each custom subscription into the xml
        for elem in newvalue:
            t = elem.get('type', None)
            if t == 'property':
                self._insert_property_node(elem)
            elif t == 'relevance':
                self._insert_relevance_node(elem)
            elif t == 'computer_group':
                self._insert_computergroup_node(elem)
            elif t is None:
                raise ValueError('Component has to have a type!')
            else:
                raise ValueError('Component type can be one of the following: "property", "relevance", "computer_group"')

    def appendProperty(self, property_elem, search_text, comparison = 'Contains', relevance_string=None):
        if self.Mode != 'Custom':
            self.Mode = 'Custom'

        if isinstance(property_elem, Property):
            prop_name = property_elem.Name
            relevance_string = property_elem.Relevance
        else:
            prop_name = property_elem

        if comparison == 'Contains':
            comparison_rel = 'contains'
        elif comparison == 'DoesNotContain':
            comparison_rel = 'does not contain'
        elif comparison == 'Equals':
            comparison_rel = '='
        elif comparison == 'DoesNotEqual':
            comparison_rel = '!='
        else:
            comparison_rel = ''

        relevance_compiled = search_by_property_relevance.format(relevance_string, comparison_rel, search_text)
        return self._insert_property_node({'property_name': prop_name, 'comparison': comparison, 'search_text': search_text, 'relevance': relevance_compiled})

    def appendRelevance(self, relevance_string, comparison = 'IsTrue'):
        if self.Mode != 'Custom':
            self.Mode = 'Custom'
        return self._insert_relevance_node({'relevance': relevance_string, 'comparison': comparison})

    def appendComputerGroup(self, computer_group, comparison='IsMember'):
        if self.Mode != 'Custom':
            self.Mode = 'Custom'
        if isinstance(computer_group, APIComputerGroup):
            computer_group_name = computer_group.Name
        elif isinstance(computer_group, ComputerGroup):
            computer_group_name = computer_group.Title
        else:
            computer_group_name = computer_group
        return self._insert_computergroup_node({'comparison': comparison, 'group_name': computer_group_name})

    def remove(self, x):
        try:
            x = int(x)
        except ValueError as e:
            raise ValueError('A positive integer must be provided')
        if x < 0:
            raise ValueError('A positive integer must be provided')
        cg_node = self._get_child_elem('CustomGroup')
        for elem in cg_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName in ('SearchComponentRelevance', 'SearchComponentGroupReference', 'SearchComponentPropertyReference'):
                if x == 0:
                    cg_node.removeChild(elem)
                    return True
                x = x - 1
        raise ValueError('Subscription component index out of range')

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

        if newvalue == 'Custom':
            self._create_empty_customgroup()
        elif newvalue != 'Custom':
            self._delete_customgroup()

    @property
    def MatchCondition(self):
        if self.Mode != 'Custom':
            return None
        mc = self._value_for_elem_attr('CustomGroup', 'JoinByIntersection')
        if mc == 'true':
            return 'all'
        elif mc == 'false':
            return 'any'
    @MatchCondition.setter
    def MatchCondition(self, newvalue):
        if self.Mode != 'Custom':
            raise ValueError('MatchCondition can only be set if subscription mode is Custom')
        elif newvalue not in ('any', 'all'):
            raise ValueError('MatchCondition can only be "any" or "all"')
        if newvalue == 'all':
            mc = 'true'
        elif newvalue == 'any':
            mc = 'false'
        self._set_newattr_for_elem('CustomGroup', 'JoinByIntersection', mc)

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
        if self._value_for_elem('GlobalReadPermission') is None:
            return None
        return self._str2bool(self._value_for_elem('GlobalReadPermission'))
    @GlobalReadPermission.setter
    def GlobalReadPermission(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('GlobalReadPermission can only be true or false')
        if not self._exists_child_elem('GlobalReadPermission'):
            self._create_child_elem('GlobalReadPermission')
        self._set_newvalue_for_elem('GlobalReadPermission', self._bool2str(newvalue))

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


class Property(BESCoreElement):
    def __init__(self, *args, **kwargs):
        try:
            tmp = self._base_node_name
        except AttributeError as e:
            self._base_node_name = 'Property'
        super(Property, self).__init__(*args, **kwargs)

    @property
    def Name(self):
        return self.base_node.getAttribute('Name')
    @Name.setter
    def Name(self, newvalue):
        if len(newvalue) > 255:
            raise ValueError('Name can only be 255 characters long')
        self.base_node.setAttribute('Name', newvalue)

    @property
    def EvaluationPeriod(self):
        return self.base_node.getAttribute('EvaluationPeriod')
    @EvaluationPeriod.setter
    def EvaluationPeriod(self, newvalue):
        if re.search('^P([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\.[0-9]{1,6})?S)?)?$', newvalue) is None:
            raise ValueError('Incorrectly formatted delay duration')
        self.base_node.setAttribute('EvaluationPeriod', newvalue)

    @property
    def KeepStatistics(self):
        if self.base_node.getAttribute('KeepStatistics') is None:
            return None
        return self._str2bool(self.base_node.getAttribute('KeepStatistics'))
    @KeepStatistics.setter
    def KeepStatistics(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('It can only be true or false')
        self.base_node.setAttribute('KeepStatistics', self._bool2str(newvalue))

    @property
    def Relevance(self):
        if len(self.base_node.childNodes) == 0 or len(self.base_node.childNodes) > 1:
            return ''
        else:
            return self.base_node.childNodes[0].nodeValue
    @Relevance.setter
    def Relevance(self, newvalue):
        while len(self.base_node.childNodes) > 0:
            self.base_node.removeChild(self.base_node.childNodes[0])
        t_node = self.base_node.ownerDocument.createTextNode(newvalue)
        self.base_node.appendChild(t_node)




class BESActionSourceFixlet(BESCoreElement):
    def __init__(self, *args, **kwargs):
        try:
            self._base_node_name
        except AttributeError as e:
            self._base_node_name = 'SourceFixlet'
        super(BESActionSourceFixlet, self).__init__(*args, **kwargs)
        self._field_order = ('GatherURL', 'Sitename', 'SiteID', 'FixletID', 'Action')
    def _create_empty_element(self, *args, **kwargs):
        super(BESActionSourceFixlet, self)._create_empty_element(*args, **kwargs)
        gu_node = self.base_node.ownerDocument.createElement('GatherURL')
        gu_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        fid_node = self.base_node.ownerDocument.createElement('FixletID')
        fid_node.appendChild(self.base_node.ownerDocument.createTextNode('0'))
        self.base_node.appendChild(gu_node)
        self.base_node.appendChild(fid_node)

    @property
    def GatherURL(self):
        return self._value_for_elem('GatherURL')
    @GatherURL.setter
    def GatherURL(self, newvalue):
        if isinstance(newvalue, (str, unicode)):
            pass # we do nothing, newvalue is our new value
        elif isinstance(newvalue, (Site, APIGenericSite)):
            newvalue = newvalue.GatherURL # we're extracting actual value from object
        else:
            raise ValueError('GatherURL can either be string representation or site object')
        if not self._exists_child_elem('GatherURL'):
            self._create_child_elem('GatherURL')
        self._set_newvalue_for_elem('GatherURL', newvalue)
        # if this one is set, the other two need to go
        for ename in ('Sitename', 'SiteID'):
            if self._exists_child_elem(ename):
                n = self._get_child_elem(ename)
                self.base_node.removeChild(n)

    @property
    def Sitename(self):
        return self._value_for_elem('Sitename')
    @Sitename.setter
    def Sitename(self, newvalue):
        if isinstance(newvalue, (str, unicode)):
            pass # we do nothing, newvalue is our new value
        elif isinstance(newvalue, (Site, APIGenericSite)):
            newvalue = newvalue.Name
        else:
            raise ValueError('GatherURL can either be string representation or site object')
        if not self._exists_child_elem('Sitename'):
            self._create_child_elem('Sitename')
        self._set_newvalue_for_elem('Sitename', newvalue)
        # if this one is set, the other two need to go
        for ename in ('GatherURL', 'SiteID'):
            if self._exists_child_elem(ename):
                n = self._get_child_elem(ename)
                self.base_node.removeChild(n)

    @property
    def SiteID(self):
        return self._value_for_elem('SiteID')
    @SiteID.setter
    def SiteID(self, newvalue):
        if not isinstance(newvalue, int) or newvalue < 0:
            raise ValueError('SiteID must be an integer greater than 0')
        if not self._exists_child_elem('SiteID'):
            self._create_child_elem('SiteID')
        self._set_newvalue_for_elem('SiteID')
        # if this one is set, the other two need to go
        for ename in ('GatherURL', 'Sitename'):
            if self._exists_child_elem(ename):
                n = self._get_child_elem(ename)
                self.base_node.removeChild(n)
    @property
    def FixletID(self):
        return self._value_for_elem('FixletID')
    @FixletID.setter
    def FixletID(self, newvalue):
        if not isinstance(newvalue, int) or newvalue < 0:
            raise ValueError('FixletID must be an integer greater than 0')
        if not self._exists_child_elem('FixletID'):
            self._create_child_elem('FixletID')
        self._set_newvalue_for_elem('FixletID', str(newvalue))

    @property
    def Action(self):
        return self._value_for_elem('Action')
    @Action.setter
    def Action(self, newvalue):
        if not self._exists_child_elem('Action'):
            self._create_child_elem('Action')
        self._set_newvalue_for_elem('Action', newvalue)

class BESActionTarget(BESCoreElement):
    def __init__(self, *args, **kwargs):
        try:
            self._base_node_name
        except AttributeError as e:
            self._base_node_name = 'Target'
        super(BESActionTarget, self).__init__(*args, **kwargs)
        self._field_order = ('ComputerName', 'ComputerID', 'CustomRelevance', 'AllComputers')

    @property
    def ComputerName(self):
        if not self._exists_child_elem('ComputerName'):
            return None
        out = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ComputerName':
                try:
                    out.append(elem.childNodes[0].nodeValue)
                except Exception as e:
                    pass # if there's a problem, we add nothing to our list
        return out
    @ComputerName.setter
    def ComputerName(self, newvalue):
        if not isinstance(newvalue, (list, tuple)):
            raise ValueError('ComputerName can only be a list or a tuple of names')
        # drop all current elements
        while len(self.base_node.childNodes) > 0:
            self.base_node.removeChild(self.base_node.childNodes[0])
        for elem in newvalue:
            n = self.base_node.ownerDocument.createElement('ComputerName')
            n.appendChild(self.base_node.ownerDocument.createTextNode(elem))
            self.base_node.appendChild(n)

    @property
    def ComputerID(self):
        if not self._exists_child_elem('ComputerID'):
            return None
        out = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ComputerID':
                try:
                    out.append(elem.childNodes[0].nodeValue)
                except Exception as e:
                    pass # if there's a problem, we add nothing to our list
        return out
    @ComputerID.setter
    def ComputerID(self, newvalue):
        if not isinstance(newvalue, (list, tuple)):
            raise ValueError('ComputerID can only be a list or a tuple of ids')
        # drop all current elements
        while len(self.base_node.childNodes) > 0:
            self.base_node.removeChild(self.base_node.childNodes[0])
        for elem in newvalue:
            n = self.base_node.ownerDocument.createElement('ComputerID')
            n.appendChild(self.base_node.ownerDocument.createTextNode(str(elem)))
            self.base_node.appendChild(n)

    @property
    def CustomRelevance(self):
        return self._value_for_elem('CustomRelevance')
    @CustomRelevance.setter
    def CustomRelevance(self, newvalue):
        # drop all current elements
        while len(self.base_node.childNodes) > 0:
            self.base_node.removeChild(self.base_node.childNodes[0])
        self._create_child_elem('CustomRelevance')
        self._set_newvalue_for_elem('CustomRelevance', newvalue)

    @property
    def AllComputers(self):
        if not self._exists_child_elem('AllComputers'):
            return None
        return self._str2bool(self._value_for_elem('AllComputers'))
    @AllComputers.setter
    def AllComputers(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('AllComputers can only be true or false')
        # drop all current elements
        while len(self.base_node.childNodes) > 0:
            self.base_node.removeChild(self.base_node.childNodes[0])
        self._create_child_elem('AllComputers')
        self._set_newvalue_for_elem('AllComputers', self._bool2str(newvalue))

class SourcedFixletAction(BESCoreElement, ParameterProperty):
    __slots__ = ('_source_fixlet_o', '_target_o', '_settings_o')

    def __init__(self, *args, **kwargs):
        self._base_node_name = 'SourcedFixletAction'
        super(SourcedFixletAction, self).__init__(*args, **kwargs)
        self._field_order = ('SourceFixlet', 'Target', 'Parameter', 'SecureParameter', 'Settings', 'IsUrgent', 'Title')
        self._source_fixlet_o = None
        self._target_o = None
        self._settings_o = None
    def _create_empty_element(self, *args, **kwargs):
        super(SourcedFixletAction, self)._create_empty_element(*args, **kwargs)
        self.base_node.setAttribute('SkipUI', 'true')
        sf_node = self.base_node.ownerDocument.createElement('SourceFixlet')
        self.base_node.appendChild(sf_node)

    @property
    def SkipUI(self):
        if self.base_node.getAttribute('SkipUI') is None or self.base_node.getAttribute('SkipUI') == '':
            return None
        return self._str2bool(self.base_node.getAttribute('SkipUI'))
    @SkipUI.setter
    def SkipUI(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('SkipUI only accepts true or false')
        self.base_node.setAttribute('SkipUI', self._bool2str(newvalue))

    @property
    def SourceFixlet(self):
        if self._source_fixlet_o is not None:
            return self._source_fixlet_o
        if not self._exists_child_elem('SourceFixlet'):
            self._create_child_elem('SourceFixlet')
        self._source_fixlet_o = BESActionSourceFixlet(self._get_child_elem('SourceFixlet'))
        return self._source_fixlet_o

    @property
    def Target(self):
        if self._target_o is not None:
            return self._target_o
        if not self._exists_child_elem('Target'):
            self._create_child_elem('Target')
        self._target_o = BESActionTarget(self._get_child_elem('Target'))
        return self._target_o

    @property
    def Settings(self):
        if self._settings_o is not None:
            return self._settings_o
        if not self._exists_child_elem('Settings'):
            self._create_child_elem('Settings')
        self._settings_o = ActionSettings(self._get_child_elem('Settings'))
        return self._settings_o

    @property
    def Title(self):
        return self._value_for_elem('Title')
    @Title.setter
    def Title(self, newvalue):
        if not isinstance(newvalue, (str, unicode)):
            raise ValueError('Title can only be str or unicode')
        if len(newvalue) < 1 or len(newvalue) > 255:
            raise ValueError('Title can only be 1 to 255 characters long')
        if not self._exists_child_elem('Title'):
            self._create_child_elem('Title')
        self._set_newvalue_for_elem('Title', newvalue)

    @property
    def IsUrgent(self):
        if not self._exists_child_elem('IsUrgent'):
            return None
        return self._str2bool(self._value_for_elem('IsUrgent'))
    @IsUrgent.setter
    def IsUrgent(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('IsUrgent can only be true or false')
        if not self._exists_child_elem('IsUrgent'):
            self._create_child_elem('IsUrgent')
        self._set_newvalue_for_elem('IsUrgent', self._bool2str(newvalue))


class SingleAction(BESCoreElement, ActionScriptProperty, SuccessCriteriaProperty, ParameterProperty, MIMEFieldProperty):
    __slots__ = ('_settings_o', '_target_o', '_source_fixlet_o')

    def __init__(self, *args, **kwargs):
        self._base_node_name = 'SingleAction'
        super(SingleAction, self).__init__(*args, **kwargs)
        self._field_order = ('Title', 'Relevance', 'ActionScript', 'SuccessCriteria', 'SuccessCriteriaLocked', 'Parameter', 'SecureParameter', 'Settings', 'SettingsLocks', 'IsUrgent', 'Domain', 'Target', 'SourceFixlet', 'MIMEField')
        self._settings_o = None
        self._target_o = None
        self._source_fixlet_o = None
    def _create_empty_element(self, *args, **kwargs):
        super(SingleAction, self)._create_empty_element(*args, **kwargs)
        self.base_node.setAttribute('SkipUI', 'true')
        t_node = self.base_node.ownerDocument.createElement('Title')
        t_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        r_node = self.base_node.ownerDocument.createElement('Relevance')
        r_node.appendChild(self.base_node.ownerDocument.createTextNode('true'))
        as_node = self.base_node.ownerDocument.createElement('ActionScript')
        as_node.appendChild(self.base_node.ownerDocument.createTextNode(''))
        as_node.setAttribute('MIMEType', 'application/x-Fixlet-Windows-Shell')
        self.base_node.appendChild(t_node)
        self.base_node.appendChild(r_node)
        self.base_node.appendChild(as_node)

    @property
    def SkipUI(self):
        if self.base_node.getAttribute('SkipUI') is None or self.base_node.getAttribute('SkipUI') == '':
            return None
        return self._str2bool(self.base_node.getAttribute('SkipUI'))
    @SkipUI.setter
    def SkipUI(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('SkipUI only accepts true or false')
        self.base_node.setAttribute('SkipUI', self._bool2str(newvalue))

    @property
    def Title(self):
        return self._value_for_elem('Title')
    @Title.setter
    def Title(self, newvalue):
        if not isinstance(newvalue, (str, unicode)):
            raise ValueError('Title should be a string')
        if len(newvalue) < 1 or len(newvalue) > 255:
            raise ValueError('Title needs to be at least 1 character and at most 255 characters')
        if not self._exists_child_elem('Title'):
            self._create_child_elem('Title')
        self._set_newvalue_for_elem('Title', newvalue)

    @property
    def Relevance(self):
        return self._value_for_elem('Relevance')
    @Relevance.setter
    def Relevance(self, newvalue):
        if not isinstance(newvalue, (str, unicode)):
            raise ValueError('Relevance should be a string')
        if not self._exists_child_elem('Relevance'):
            self._create_child_elem('Relevance')
        self._set_newvalue_for_elem('Relevance', newvalue)

    @property
    def Settings(self):
        if self._settings_o is not None:
            return self._settings_o
        if not self._exists_child_elem('Settings'):
            self._create_child_elem('Settings', False)
        self._settings_o = ActionSettings(self._get_child_elem('Settings'))
        return self._settings_o

    @property
    def IsUrgent(self):
        if not self._exists_child_elem('IsUrgent'):
            return False
        return self._str2bool(self._value_for_elem('IsUrgent'))
    @IsUrgent.setter
    def IsUrgent(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('IsUrgent can only be true or false')
        if not self._exists_child_elem('IsUrgent'):
            self._create_child_elem('IsUrgent')
        self._set_newvalue_for_elem('IsUrgent', self._bool2str(newvalue))

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
    def Target(self):
        if self._target_o is not None:
            return self._target_o
        if not self._exists_child_elem('Target'):
            self._create_child_elem('Target')
        self._target_o = BESActionTarget(self._get_child_elem('Target'))
        return self._target_o

    @property
    def SourceFixlet(self):
        if self._source_fixlet_o is not None:
            return self._source_fixlet_o
        if not self._exists_child_elem('SourceFixlet'):
            self._create_child_elem('SourceFixlet')
        self._source_fixlet_o = BESActionSourceFixlet(self._get_child_elem('SourceFixlet'))
        return self._source_fixlet_o






#### BESAPI Elements ####
class OperatorComputerAssignments(BESCoreElement):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'ComputerAssignments'
        super(OperatorComputerAssignments, self).__init__(*args, **kwargs)
        self._field_order = ('AllComputers', 'ByActiveDirectory', 'ByRetrievedProperties', 'ByGroup')

    @property
    def AllComputers(self):
        if self._exists_child_elem('AllComputers'):
            return True
        return False
    @AllComputers.setter
    def AllComputers(self, newvalue):
        if newvalue not in (True, False):
            raise ValueError('AllComputers can only accept boolean True or False')
        if newvalue and not self._exists_child_elem('AllComputers'):
            # first remove all existing assignment children
            while len(self.base_node.childNodes) > 0:
                self.base_node.removeChild(self.base_node.childNodes[0])
            self._create_child_elem('AllComputers', simple_elem=False)
        elif not newvalue and self._exists_child_elem('AllComputers'):
            n = self._get_child_elem('AllComputers')
            self.base_node.removeChild(n)

    def _parse_bygroup_node(self, cg_node):
        gr_name = cg_node.getAttribute('Name')
        gr_resource = cg_node.getAttribute('Resource')
        gr_type = cg_node.getAttribute('Type')

        return {
            'type': 'computer_group',
            'group_name': gr_name,
            'group_resource': gr_resource,
            'group_type': gr_type
        }

    def _parse_byproperty_node(self, prop_node):
        for sub_n in prop_node.childNodes:
            if sub_n.nodeType == Node.ELEMENT_NODE:
                if sub_n.nodeName == 'Property':
                    p_node = sub_n
                elif sub_n.nodeName == 'Relevance':
                    r_node = sub_n
        prop_name = p_node.getAttribute('Name')
        prop_resource = p_node.getAttribute('Resource')
        for sub_n in p_node.childNodes:
            if sub_n.nodeType == Node.ELEMENT_NODE and sub_n.nodeName == 'Value':
                prop_value = sub_n.childNodes[0].nodeValue
        prop_relevance = r_node.childNodes[0].nodeValue

        return {
            'type': 'retrieved_property',
            'property_name': prop_name,
            'property_value': prop_value,
            'property_resource': prop_resource,
            'property_relevance': prop_relevance
        }

    def _parse_byad_node(self, ad_node):
        dn_val = None
        for elem in ad_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'DistinguishedName':
                dn_val = elem.childNodes[0].nodeValue
                break
        return {
            'type': 'active_directory',
            'distinguished_name': dn_val
        }

    def _insert_bygroup_node(self, definition):
        if not definition.has_key('group_name'):
            raise ValueError('Required component "group_name" missing for computer group based assignment definition')
        elif not definition.has_key('group_resource'):
            raise ValueError('Required component "group_resource" missing for computer group based assignment definition')
        elif not definition.has_key('group_type'):
            raise ValueError('Required component "group_type" missing for computer group based assignment definition')
        elif definition['group_type'] not in ('Automatic', 'Manual'):
            raise ValueError('group_type for computer group based assignment can only be "Automatic" or "Manual"')

        cg_node = self.base_node.ownerDocument.createElement('ByGroup')
        cg_node.setAttribute('Name', definition['group_name'])
        cg_node.setAttribute('Resource', definition['group_resource'])
        cg_node.setAttribute('Type', definition['group_type'])

        self.base_node.appendChild(cg_node)
        return True

    def _insert_byad_node(self, definition):
        if not definition.has_key('distinguished_name'):
            raise ValueError('Required component "distinguished_name" missing for AD based assignment definition')
        main_node = self.base_node.ownerDocument.createElement('ByActiveDirectory')
        dn_node = main_node.ownerDocument.createElement('DistinguishedName')
        dn_node.appendChild(dn_node.ownerDocument.createTextNode(definition['distinguished_name']))

        main_node.appendChild(dn_node)
        self.base_node.appendChild(main_node)
        return True

    def _insert_byproperty_node(self, definition):
        if not definition.has_key('property_name'):
            raise ValueError('Required component "property_name" missing for property based assignment definition')
        elif not definition.has_key('property_value'):
            raise ValueError('Required component "property_value" missing for property based assignment definition')
        elif not definition.has_key('property_resource'):
            raise ValueError('Required component "property_resource" missing for property based assignment definition')
        elif not definition.has_key('property_relevance'):
            raise ValueError('Required component "property_relevance" missing for property based assignment definition')

        main_node = self.base_node.ownerDocument.createElement('ByRetrievedProperties')
        main_node.setAttribute('Match', 'All')

        prop_node = main_node.ownerDocument.createElement('Property')
        prop_node.setAttribute('Name', definition['property_name'])
        prop_node.setAttribute('Resource', definition['property_resource'])

        val_node = main_node.ownerDocument.createElement('Value')
        val_node.appendChild(main_node.ownerDocument.createTextNode(definition['property_value']))

        rel_node = main_node.ownerDocument.createElement('Relevance')
        rel_node.appendChild(main_node.ownerDocument.createTextNode(definition['property_relevance']))

        prop_node.appendChild(val_node)
        main_node.appendChild(prop_node)
        main_node.appendChild(rel_node)
        self.base_node.appendChild(main_node)
        return True

    @property
    def AssignmentList(self):
        if self.AllComputers:
            return None
        result = []
        for sub_elem in self.base_node.childNodes:
            if sub_elem.nodeType == Node.ELEMENT_NODE and sub_elem.nodeName in ('ByActiveDirectory', 'ByRetrievedProperties', 'ByGroup'):
                if sub_elem.nodeName == 'ByActiveDirectory':
                    result.append(self._parse_byad_node(sub_elem))
                elif sub_elem.nodeName == 'ByRetrievedProperties':
                    result.append(self._parse_byproperty_node(sub_elem))
                elif sub_elem.nodeName == 'ByGroup':
                    result.append(self._parse_bygroup_node(sub_elem))
        return tuple(result)
    @AssignmentList.setter
    def AssignmentList(self, newvalue):
        if type(newvalue) not in (list, tuple):
            raise ValueError('AssignmentList can only be a list or tuple')
        for elem in newvalue:
            if type(elem) is not dict:
                raise ValueError('AssignmentList components must be dict')
        # this will make sure that both AllComputers is false and no other nodes exist within ComputerAssignments node
        self.AllComputers = True
        self.AllComputers = False
        # now adding each assignment
        for elem in newvalue:
            t = elem.get('type', None)
            if t == 'computer_group':
                self._insert_bygroup_node(elem)
            elif t == 'active_directory':
                self._insert_byad_node(elem)
            elif t == 'retrieved_property':
                self._insert_byproperty_node(elem)
            elif t is None:
                raise ValueError('Assignment component has to have a type!')
            else:
                raise ValueError('Assignment component can be one of the following: "computer_group", "active_directory", "retrieved_property"')

    def appendComputerGroup(self, computer_group, resource = None, group_type='Automatic'):
        if self.AllComputers:
            self.AllComputers = False
        if isinstance(computer_group, (APIComputerGroup, APIManualComputerGroup)):
            if isinstance(computer_group, APIComputerGroup):
                group_type = 'Automatic'
            else:
                group_type = 'Manual'
            group_name = computer_group.Name
            group_resource = computer_group.Resource
        else:
            group_name = computer_group
            group_resource = resource
        return self._insert_bygroup_node({
            'group_name': group_name,
            'group_resource': group_resource,
            'group_type': group_type
        })

    def appendAD(self, dn):
        if self.AllComputers:
            self.AllComputers = False
        return self._insert_byad_node({'distinguished_name': dn})

    def appendProperty(self, property_name, search_text, resource_string, relevance_string):
        relevance_compiled = search_by_property_relevance.format(relevance_string, '=', search_text)

        return self._insert_byproperty_node({'property_name': property_name, 'property_value': search_text, 'property_resource': resource_string, 'property_relevance': relevance_compiled})

    def remove(self, x):
        if self.AllComputers:
            return False
        try:
            x = int(x)
        except ValueError as e:
            raise ValueError('A positive integer must be provided')
        if x < 0:
            raise ValueError('A positive integer must be provided')
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName in ('ByGroup', 'ByRetrievedProperties', 'ByActiveDirectory'):
                if x == 0:
                    self.base_node.removeChild(elem)
                    return True
                x = x - 1
        raise ValueError('Assignment component index out of range')

class OperatorInterfaceLogins(BESCoreElement):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'InterfaceLogins'
        super(OperatorInterfaceLogins, self).__init__(*args, **kwargs)
        self._field_order = ('Console', 'WebUI', 'API', 'Applications')
        # following lines of code are a bit of a weird looking hack
        # to make sure that initial values are created as needed
        # while still keeping property methods fairly simple
        # and not having problems with e.g. _str2bool and _bool2str
        if not self._exists_child_elem('Console'):
            self.Console = False
        if not self._exists_child_elem('WebUI'):
            self.WebUI = False
        if not self._exists_child_elem('API'):
            self.API = False

    @property
    def Console(self):
        return self._str2bool(self._value_for_elem('Console'))
    @Console.setter
    def Console(self, newvalue):
        if not self._exists_child_elem('Console'):
            self._create_child_elem('Console')
        self._set_newvalue_for_elem('Console', self._bool2str(newvalue))

    @property
    def WebUI(self):
        return self._str2bool(self._value_for_elem('WebUI'))
    @WebUI.setter
    def WebUI(self, newvalue):
        if not self._exists_child_elem('WebUI'):
            self._create_child_elem('WebUI')
        self._set_newvalue_for_elem('WebUI', self._bool2str(newvalue))

    @property
    def API(self):
        return self._str2bool(self._value_for_elem('API'))
    @API.setter
    def API(self, newvalue):
        if not self._exists_child_elem('API'):
            self._create_child_elem('API')
        self._set_newvalue_for_elem('API', self._bool2str(newvalue))

    @property
    def Applications(self):
        app_node = self._get_child_elem('Applications')
        if app_node is None:
            return tuple()
        out = []
        for elem in app_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Name':
                out.append(elem.childNodes[0].nodeValue)
        return tuple(out)
    @Applications.setter
    def Applications(self, newvalue):
        if type(newvalue) not in [list, tuple]:
            raise ValueError('Applications value must be a list or tuple of application names')
        if not self._exists_child_elem('Applications'):
            app_node = self._create_child_elem('Applications', False)
        else:
            app_node = self._get_child_elem('Applications')
            # need to clear out current values before applying new ones
            for elem in app_node.childNodes:
                app_node.removeChild(elem)
        for elem in newvalue:
            new_node = app_node.ownerDocument.createElement('Name')
            new_node.appendChild(app_node.ownerDocument.createTextNode(elem))
            app_node.appendChild(new_node)

class Operator(BESCoreElement):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'Operator'
        super(Operator, self).__init__(*args, **kwargs)
        self._field_order = ('Name', 'ID', 'LastLoginTime', 'Password', 'LDAPServerID', 'LDAPDN', 'MasterOperator', 'CustomContent', 'ShowOtherActions', 'CanCreateActions', 'PostActionBehaviorPrivilege', 'ActionScriptCommandsPrivilege', 'CanLock', 'CanSendMultipleRefresh', 'LoginPermission', 'UnmanagedAssetPrivilege', 'InterfaceLogins', 'ApproverRoleID', 'ComputerAssignments')

    @property
    def Name(self):
        return self._value_for_elem('Name')
    @Name.setter
    def Name(self, newvalue):
        if len(newvalue) > 255:
            raise ValueError('Name can only be 255 characters')
        if not self._exists_child_elem('Name'):
            self._create_child_elem('Name')
        self._set_newvalue_for_elem('Name', newvalue)

    @property
    def ID(self):
        return self._value_for_elem('ID')
    @ID.setter
    def ID(self, newvalue):
        try:
            tmp = int(newvalue)
        except (ValueError, TypeError) as e:
            raise ValueError('ID must be a positive integer')
        if tmp < 0:
            raise ValueError('ID must be positive integer')
        if not self._exists_child_elem('ID'):
            self._create_child_elem('ID')
        self._set_newvalue_for_elem('ID', newvalue)

    @property
    def LastLoginTime(self):
        return self._value_for_elem('LastLoginTime')
    @LastLoginTime.setter
    def LastLoginTime(self, newvalue):
        if not self._exists_child_elem('LastLoginTime'):
            self._create_child_elem('LastLoginTime')
        self._set_newvalue_for_elem('LastLoginTime', newvalue)

    @property
    def Password(self):
        return self._value_for_elem('Password')
    @Password.setter
    def Password(self, newvalue):
        if not self._exists_child_elem('Password'):
            self._create_child_elem('Password')
        self._set_newvalue_for_elem('Password', newvalue)

    @property
    def LDAPServerID(self):
        return self._value_for_elem('LDAPServerID')
    @LDAPServerID.setter
    def LDAPServerID(self, newvalue):
        try:
            tmp = int(newvalue)
        except (ValueError, TypeError) as e:
            raise ValueError('LDAPServerID must be a positive integer')
        if tmp < 0:
            raise ValueError('LDAPServerID must be positive integer')
        if not self._exists_child_elem('LDAPServerID'):
            self._create_child_elem('LDAPServerID')
        self._set_newvalue_for_elem('LDAPServerID', newvalue)

    @property
    def LDAPDN(self):
        return self._value_for_elem('LDAPDN')
    @LDAPDN.setter
    def LDAPDN(self, newvalue):
        if not self._exists_child_elem('LDAPDN'):
            self._create_child_elem('LDAPDN')
        self._set_newvalue_for_elem('LDAPDN', newvalue)

    @property
    def MasterOperator(self):
        return self._str2bool(self._value_for_elem('MasterOperator'))
    @MasterOperator.setter
    def MasterOperator(self, newvalue):
        if not self._exists_child_elem('MasterOperator'):
            self._create_child_elem('MasterOperator')
        self._set_newvalue_for_elem('MasterOperator', self._bool2str(newvalue))

    @property
    def CustomContent(self):
        return self._str2bool(self._value_for_elem('CustomContent'))
    @CustomContent.setter
    def CustomContent(self, newvalue):
        if not self._exists_child_elem('CustomContent'):
            self._create_child_elem('CustomContent')
        self._set_newvalue_for_elem('CustomContent', self._bool2str(newvalue))

    @property
    def ShowOtherActions(self):
        return self._str2bool(self._value_for_elem('ShowOtherActions'))
    @ShowOtherActions.setter
    def ShowOtherActions(self, newvalue):
        if not self._exists_child_elem('ShowOtherActions'):
            self._create_child_elem('ShowOtherActions')
        self._set_newvalue_for_elem('ShowOtherActions', self._bool2str(newvalue))

    @property
    def CanCreateActions(self):
        return self._str2bool(self._value_for_elem('CanCreateActions'))
    @CanCreateActions.setter
    def CanCreateActions(self, newvalue):
        if not self._exists_child_elem('CanCreateActions'):
            self._create_child_elem('CanCreateActions')
        self._set_newvalue_for_elem('CanCreateActions', self._bool2str(newvalue))

    @property
    def PostActionBehaviorPrivilege(self):
        return self._value_for_elem('PostActionBehaviorPrivilege')
    @PostActionBehaviorPrivilege.setter
    def PostActionBehaviorPrivilege(self, newvalue):
        if newvalue not in ('AllowRestartAndShutdown', 'AllowRestartOnly', 'None'):
            raise ValueError('PostActionBehaviorPrivilege can be one of "AllowRestartAndShutdown", "AllowRestartOnly", "None"')
        if not self._exists_child_elem('PostActionBehaviorPrivilege'):
            self._create_child_elem('PostActionBehaviorPrivilege')
        self._set_newvalue_for_elem('PostActionBehaviorPrivilege', newvalue)

    @property
    def ActionScriptCommandsPrivilege(self):
        return self._value_for_elem('ActionScriptCommandsPrivilege')
    @ActionScriptCommandsPrivilege.setter
    def ActionScriptCommandsPrivilege(self, newvalue):
        if newvalue not in ('AllowRestartAndShutdown', 'AllowRestartOnly', 'None'):
            raise ValueError('ActionScriptCommandsPrivilege can be one of "AllowRestartAndShutdown", "AllowRestartOnly", "None"')
        if not self._exists_child_elem('ActionScriptCommandsPrivilege'):
            self._create_child_elem('ActionScriptCommandsPrivilege')
        self._set_newvalue_for_elem('ActionScriptCommandsPrivilege', newvalue)

    @property
    def CanLock(self):
        return self._str2bool(self._value_for_elem('CanLock'))
    @CanLock.setter
    def CanLock(self, newvalue):
        if not self._exists_child_elem('CanLock'):
            self._create_child_elem('CanLock')
        self._set_newvalue_for_elem('CanLock', self._bool2str(newvalue))

    @property
    def CanSendMultipleRefresh(self):
        return self._str2bool(self._value_for_elem('CanSendMultipleRefresh'))
    @CanSendMultipleRefresh.setter
    def CanSendMultipleRefresh(self, newvalue):
        if not self._exists_child_elem('CanSendMultipleRefresh'):
            self._create_child_elem('CanSendMultipleRefresh')
        self._set_newvalue_for_elem('CanSendMultipleRefresh', self._bool2str(newvalue))

    @property
    def LoginPermission(self):
        return self._str2bool(self._value_for_elem('LoginPermission'))
    @LoginPermission.setter
    def LoginPermission(self, newvalue):
        if newvalue not in ('Unrestricted', 'RoleRestricted', 'Disabled'):
            raise ValueError('LoginPermission can be one of "Unrestricted", "RoleRestricted", "Disabled"')
        if not self._exists_child_elem('LoginPermission'):
            self._create_child_elem('LoginPermission')
        self._set_newvalue_for_elem('LoginPermission', self._bool2str(newvalue))

    @property
    def UnmanagedAssetPrivilege(self):
        return self._value_for_elem('UnmanagedAssetPrivilege')
    @UnmanagedAssetPrivilege.setter
    def UnmanagedAssetPrivilege(self, newvalue):
        if newvalue not in ('ShowNone', 'ScanPoint', 'ShowAll'):
            raise ValueError('UnmanagedAssetPrivilege can be one of "ShowNone", "ScanPoint", "ShowAll"')
        if not self._exists_child_elem('UnmanagedAssetPrivilege'):
            self._create_child_elem('UnmanagedAssetPrivilege')
        self._set_newvalue_for_elem('UnmanagedAssetPrivilege', newvalue)

    @property
    def InterfaceLogins(self):
        if not self._exists_child_elem('InterfaceLogins'):
            self._create_child_elem('InterfaceLogins', False)
        try:
            return self._interface_logins_o
        except AttributeError as e:
            self._interface_logins_o = OperatorInterfaceLogins(self._get_child_elem('InterfaceLogins'))
            return self._interface_logins_o

    @property
    def ApproverRoleID(self):
        return self._value_for_elem('ApproverRoleID')
    @ApproverRoleID.setter
    def ApproverRoleID(self, newvalue):
        try:
            tmp = int(newvalue)
        except (ValueError, TypeError) as e:
            raise ValueError('ApproverRoleID must be a positive integer')
        if tmp < 0:
            raise ValueError('ApproverRoleID must be positive integer')
        if not self._exists_child_elem('ApproverRoleID'):
            self._create_child_elem('ApproverRoleID')
        self._set_newvalue_for_elem('ApproverRoleID', newvalue)

    @property
    def ComputerAssignments(self):
        if not self._exists_child_elem('ComputerAssignments'):
            self._create_child_elem('ComputerAssignments', False)
        try:
            return self._computer_assignments_o
        except AttributeError as e:
            self._computer_assignments_o = OperatorComputerAssignments(self._get_child_elem('ComputerAssignments'))
            return self._computer_assignments_o



    @property
    def Resource(self):
        return self.base_node.getAttribute('Resource')
    @Resource.setter
    def Resource(self, newvalue):
        self.base_node.setAttribute('Resource', newvalue)



class Role(BESCoreElement):
    def __init__(self, *args, **kwargs):
        self._base_node_name = 'Role'
        super(Role, self).__init__(*args, **kwargs)
        self._field_order = ('Name', 'ID', 'Description', 'MasterOperator', 'CustomContent', 'ShowOtherActions', 'StopOtherActions', 'CanCreateActions', 'PostActionBehaviorPrivilege', 'ActionScriptCommandsPrivilege', 'CanSendMultipleRefresh', 'CanSubmitQueries', 'CanLock', 'UnmanagedAssetPrivilege', 'InterfaceLogins', 'Operators', 'LDAPGroups', 'Sites', 'ComputerAssignments')

    @property
    def Name(self):
        return self._value_for_elem('Name')
    @Name.setter
    def Name(self, newvalue):
        if len(newvalue) > 255:
            raise ValueError('Name can only be 255 characters')
        if not self._exists_child_elem('Name'):
            self._create_child_elem('Name')
        self._set_newvalue_for_elem('Name', newvalue)

    @property
    def ID(self):
        return self._value_for_elem('ID')
    @ID.setter
    def ID(self, newvalue):
        try:
            tmp = int(newvalue)
        except (ValueError, TypeError) as e:
            raise ValueError('ID must be a positive integer')
        if tmp < 0:
            raise ValueError('ID must be positive integer')
        if not self._exists_child_elem('ID'):
            self._create_child_elem('ID')
        self._set_newvalue_for_elem('ID', newvalue)

    @property
    def MasterOperator(self):
        return self._str2bool(self._value_for_elem('MasterOperator'))
    @MasterOperator.setter
    def MasterOperator(self, newvalue):
        if not self._exists_child_elem('MasterOperator'):
            self._create_child_elem('MasterOperator')
        self._set_newvalue_for_elem('MasterOperator', self._bool2str(newvalue))

    @property
    def CustomContent(self):
        return self._str2bool(self._value_for_elem('CustomContent'))
    @CustomContent.setter
    def CustomContent(self, newvalue):
        if not self._exists_child_elem('CustomContent'):
            self._create_child_elem('CustomContent')
        self._set_newvalue_for_elem('CustomContent', self._bool2str(newvalue))

    @property
    def ShowOtherActions(self):
        return self._str2bool(self._value_for_elem('ShowOtherActions'))
    @ShowOtherActions.setter
    def ShowOtherActions(self, newvalue):
        if not self._exists_child_elem('ShowOtherActions'):
            self._create_child_elem('ShowOtherActions')
        self._set_newvalue_for_elem('ShowOtherActions', self._bool2str(newvalue))

    @property
    def StopOtherActions(self):
        return self._str2bool(self._value_for_elem('StopOtherActions'))
    @StopOtherActions.setter
    def StopOtherActions(self, newvalue):
        if not self._exists_child_elem('StopOtherActions'):
            self._create_child_elem('StopOtherActions')
        self._set_newvalue_for_elem('StopOtherActions', self._bool2str(newvalue))

    @property
    def CanCreateActions(self):
        return self._str2bool(self._value_for_elem('CanCreateActions'))
    @CanCreateActions.setter
    def CanCreateActions(self, newvalue):
        if not self._exists_child_elem('CanCreateActions'):
            self._create_child_elem('CanCreateActions')
        self._set_newvalue_for_elem('CanCreateActions', self._bool2str(newvalue))

    @property
    def PostActionBehaviorPrivilege(self):
        return self._value_for_elem('PostActionBehaviorPrivilege')
    @PostActionBehaviorPrivilege.setter
    def PostActionBehaviorPrivilege(self, newvalue):
        if newvalue not in ('AllowRestartAndShutdown', 'AllowRestartOnly', 'None'):
            raise ValueError('PostActionBehaviorPrivilege can be one of "AllowRestartAndShutdown", "AllowRestartOnly", "None"')
        if not self._exists_child_elem('PostActionBehaviorPrivilege'):
            self._create_child_elem('PostActionBehaviorPrivilege')
        self._set_newvalue_for_elem('PostActionBehaviorPrivilege', newvalue)

    @property
    def ActionScriptCommandsPrivilege(self):
        return self._value_for_elem('ActionScriptCommandsPrivilege')
    @ActionScriptCommandsPrivilege.setter
    def ActionScriptCommandsPrivilege(self, newvalue):
        if newvalue not in ('AllowRestartAndShutdown', 'AllowRestartOnly', 'None'):
            raise ValueError('ActionScriptCommandsPrivilege can be one of "AllowRestartAndShutdown", "AllowRestartOnly", "None"')
        if not self._exists_child_elem('ActionScriptCommandsPrivilege'):
            self._create_child_elem('ActionScriptCommandsPrivilege')
        self._set_newvalue_for_elem('ActionScriptCommandsPrivilege', newvalue)

    @property
    def CanSendMultipleRefresh(self):
        return self._str2bool(self._value_for_elem('CanSendMultipleRefresh'))
    @CanSendMultipleRefresh.setter
    def CanSendMultipleRefresh(self, newvalue):
        if not self._exists_child_elem('CanSendMultipleRefresh'):
            self._create_child_elem('CanSendMultipleRefresh')
        self._set_newvalue_for_elem('CanSendMultipleRefresh', self._bool2str(newvalue))

    @property
    def CanSubmitQueries(self):
        return self._str2bool(self._value_for_elem('CanSubmitQueries'))
    @CanSubmitQueries.setter
    def CanSubmitQueries(self, newvalue):
        if not self._exists_child_elem('CanSubmitQueries'):
            self._create_child_elem('CanSubmitQueries')
        self._set_newvalue_for_elem('CanSubmitQueries', self._bool2str(newvalue))

    @property
    def CanLock(self):
        return self._str2bool(self._value_for_elem('CanLock'))
    @CanLock.setter
    def CanLock(self, newvalue):
        if not self._exists_child_elem('CanLock'):
            self._create_child_elem('CanLock')
        self._set_newvalue_for_elem('CanLock', self._bool2str(newvalue))

    @property
    def UnmanagedAssetPrivilege(self):
        return self._str2bool(self._value_for_elem('UnmanagedAssetPrivilege'))
    @UnmanagedAssetPrivilege.setter
    def UnmanagedAssetPrivilege(self, newvalue):
        if newvalue not in ('ShowNone', 'ScanPoint', 'ShowAll'):
            raise ValueError('UnmanagedAssetPrivilege can be one of "ShowNone", "ScanPoint", "ShowAll"')
        if not self._exists_child_elem('UnmanagedAssetPrivilege'):
            self._create_child_elem('UnmanagedAssetPrivilege')
        self._set_newvalue_for_elem('UnmanagedAssetPrivilege', self._bool2str(newvalue))

    @property
    def InterfaceLogins(self):
        if not self._exists_child_elem('InterfaceLogins'):
            self._create_child_elem('InterfaceLogins', False)
        try:
            return self._interface_logins_o
        except AttributeError as e:
            self._interface_logins_o = OperatorInterfaceLogins(self._get_child_elem('InterfaceLogins'))
            return self._interface_logins_o

    @property
    def Operators(self):
        if self._exists_child_elem('Operators'):
            op_node = self._get_child_elem('Operators')
            res = []
            for elem in op_node.childNodes:
                if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName in ('Explicit', 'Inherited'):
                    op_type = 'Explicit' if elem.nodeName == 'Explicit' else 'Inherited'
                    res.append( (op_type, elem.childNodes[0].nodeValue) )
            return tuple(res)
        else:
            return None
    @Operators.setter
    def Operators(self, newvalue):
        if type(newvalue) not in (tuple, list):
            raise ValueError('Operators need be provided as either list or tuple')
        # empty operators node or create if needed
        if self._exists_child_elem('Operators'):
            op_node = self._get_child_elem('Operators')
            while len(op_node.childNodes) > 0:
                op_node.removeChild(op_node.childNodes[0])
        else:
            op_node = self._create_child_elem('Operators', False)
        for opdef in newvalue:
            if isinstance(opdef, Operator):
                tmp_node = op_node.ownerDocument.createElement('Explicit')
                tmp_node.appendChild(tmp_node.ownerDocument.createTextNode(opdef.Name))
                op_node.appendChild(tmp_node)
            elif type(opdef) in (tuple, list) and len(opdef) == 2 and opdef[0] in ('Explicit', 'Inherited'):
                tmp_node = op_node.ownerDocument.createElement(opdef[0])
                tmp_node.appendChild(tmp_node.ownerDocument.createTextNode(opdef[1]))
                op_node.appendChild(tmp_node)
            else:
                raise ValueError('Incorrect operator definition')

    @property
    def LDAPGroups(self):
        if not self._exists_child_elem('LDAPGroups'):
            return None
        res = []
        main_node = self._get_child_elem('LDAPGroups')
        for elem in main_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Group':
                gr_name = None
                gr_dn = None
                gr_srvid = None
                for subelem in elem.childNodes:
                    if subelem.nodeType == Node.ELEMENT_NODE:
                        if subelem.nodeName == 'Name':
                            gr_name = subelem.childNodes[0].nodeValue
                        elif subelem.nodeName == 'DN':
                            gr_dn = subelem.childNodes[0].nodeValue
                        elif subelem.nodeName == 'ServerID':
                            gr_srvid = subelem.childNodes[0].nodeValue
                res.append({'Name': gr_name, 'DN': gr_dn, 'ServerID': gr_srvid})
        return tuple(res)
    @LDAPGroups.setter
    def LDAPGroups(self, newvalue):
        if type(newvalue) not in (tuple, list):
            raise ValueError('LDAPGroups need to be provided with either tuple or list')
        # empty the LDAPGroups node or create one if needed
        if self._exists_child_elem('LDAPGroups'):
            main_node = self._get_child_elem('LDAPGroups')
            while len(main_node.childNodes) > 0:
                main_node.removeChild(main_node.childNodes[0])
        else:
            main_node = self._create_child_elem('LDAPGroups', False)
        for grdef in newvalue:
            if type(grdef) is not dict or not grdef.has_key('Name') or not grdef.has_key('DN') or not grdef.has_key('ServerID'):
                raise ValueError('Each LDAPGRoups component needs to be a dict with required following keys: "Name", "DN", "ServerID"')

            gr_node = main_node.ownerDocument.createElement('Group')
            gr_sub_name = main_node.ownerDocument.createElement('Name')
            gr_sub_name.appendChild(main_node.ownerDocument.createTextNode(grdef['Name']))
            gr_sub_dn = main_node.ownerDocument.createElement('DN')
            gr_sub_dn.appendChild(main_node.ownerDocument.createTextNode(grdef['DN']))
            gr_sub_srvid = main_node.ownerDocument.createElement('ServerID')
            gr_sub_srvid.appendChild(main_node.ownerDocument.createTextNode(grdef['ServerID']))

            main_node.appendChild(gr_node)
            gr_node.appendChild(gr_sub_name)
            gr_node.appendChild(gr_sub_dn)
            gr_node.appendChild(gr_sub_srvid)

    @property
    def Sites(self):
        if not self._exists_child_elem('Sites'):
            return None
        out = []
        main_node = self._get_child_elem('Sites')

        for site_node in main_node.childNodes:
            if site_node.nodeType == Node.ELEMENT_NODE:
                site_type = None
                site_name = None
                site_perm = None
                if site_node.nodeName == 'CustomSite':
                    site_type = 'Custom'
                elif site_node.nodeName == 'ExternalSite':
                    site_type = 'External'
                for prop_node in site_node.childNodes:
                    if prop_node.nodeType == Node.ELEMENT_NODE:
                        if prop_node.nodeName == 'Name':
                            site_name = prop_node.childNodes[0].nodeValue
                        elif prop_node.nodeName == 'Permission':
                            site_perm = prop_node.childNodes[0].nodeValue
                out.append( (site_type, site_name, site_perm) )
        return tuple(out)
    @Sites.setter
    def Sites(self, newvalue):
        if type(newvalue) not in (list, tuple):
            raise ValueError('Only list or tuple can be provided as Sites value')
        # now that we know it's a list, let's clear out all of the current sites
        # or we create new Site tag, if one does not exist yet
        if self._exists_child_elem('Sites'):
            main_node = self._get_child_elem('Sites')
            while len(main_node.childNodes) > 0:
                main_node.removeChild(main_node.childNodes[0])
        else:
            main_node = self._create_child_elem('Sites', False)
        # now to creating nodes
        for elem in newvalue:
            if type(elem) not in (list,tuple):
                raise ValueError('Sites component element can only be tuple or a list')
            if isinstance(elem[0], (APIExternalSite, APICustomSite)):
                if elem[1] not in ('Owner', 'Reader', 'Writer', 'None'):
                    raise ValueError('Sites component element can only be "Owner", "Reader", "Writer" or "None"')
                if isinstance(elem[0], APIExternalSite):
                    s_node = main_node.ownerDocument.createElement('ExternalSite')
                elif isinstance(elem[0], APICustomSite):
                    s_node = main_node.ownerDocument.createElement('CustomSite')
                site_name = elem[0].Name
                site_perm = elem[1]
            else:
                if elem[2] not in ('Owner', 'Reader', 'Writer', 'None'):
                    raise ValueError('Sites component element can only be "Owner", "Reader", "Writer" or "None"')

                if elem[0] == 'External':
                    s_node = main_node.ownerDocument.createElement('ExternalSite')
                elif elem[0] == 'Custom':
                    s_node = main_node.ownerDocument.createElement('CustomSite')
                site_name = elem[1]
                site_perm = elem[2]

            name_node = main_node.ownerDocument.createElement('Name')
            name_node.appendChild(main_node.ownerDocument.createTextNode(site_name))
            perm_node = main_node.ownerDocument.createElement('Permission')
            perm_node.appendChild(main_node.ownerDocument.createTextNode(site_perm))

            s_node.appendChild(name_node)
            s_node.appendChild(perm_node)
            main_node.appendChild(s_node)


    @property
    def ComputerAssignments(self):
        if not self._exists_child_elem('ComputerAssignments'):
            self._create_child_elem('ComputerAssignments', False)
        try:
            return self._computer_assignments_o
        except AttributeError as e:
            self._computer_assignments_o = OperatorComputerAssignments(self._get_child_elem('ComputerAssignments'))
            return self._computer_assignments_o





    @property
    def Resource(self):
        return self.base_node.getAttribute('Resource')
    @Resource.setter
    def Resource(self, newvalue):
        self.base_node.setAttribute('Resource', newvalue)




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
                    if len(elem.childNodes[0].nodeValue) == 31:
                        return datetime.strptime(elem.childNodes[0].nodeValue[:-6], date_format_notz)
                    else:
                        return datetime.strptime(elem.childNodes[0].nodeValue, date_format_notz)
    @LastReportTime.setter
    def LastReportTime(self, newval):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'LastReportTime':
                try:
                    elem.childNodes[0].nodeValue = datetime.strftime(newval, date_format).strip()
                except ValueError as e:
                    # once more, for the tz issue
                    elem.childNodes[0].nodeValue = '{0} +0000'.format(datetime.strftime(newval, date_format_notz))


class APIComputerGroup(BESAPICoreElement):
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
    def LastModified(self):
        return self.base_node.getAttirbute('LastModified')
    @LastModified.setter
    def LastModified(self, newvalue):
        self.base_node.setAttribute('LastModified', newvalue)

class APIManualComputerGroup(BESAPICoreElement):
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
    def EvaluateOnClient(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'EvaluateOnClient':
                return elem.childNodes[0].nodeValue
    @EvaluateOnClient.setter
    def EvaluateOnClient(self, newvalue):
        if newvalue not in ('true', 'false'):
            raise ValueError('EvaluateOnClient can only be set to "true" or "false"')
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'EvaluateOnClient':
                elem.childNodes[0].nodeValue = newvalue

    @property
    def Computers(self):
        out = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ComputerID':
                out.append(elem.childNodes[0].nodeValue.strip())
        return out
    @Computers.setter
    def Computers(self, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'ComputerID':
                self.base_node.removeChild(elem)
        for elem in newvalue:
            cid_node = self.base_node.ownerDocument.createElement('ComputerID')
            cid_node.appendChild(self.base_node.ownerDocument.createTextNode(elem))
            self.base_node.appendChild(cid_node)





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



class APIProperty(BESAPICoreElement):
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
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeID == 'ID':
                return elem.childNodes[0].nodeValue
    @ID.setter
    def ID(self, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeID == 'ID':
                elem.childNodes[0].nodeValue = newvalue

    @property
    def IsReserved(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeIsReserved == 'IsReserved':
                return elem.childNodes[0].nodeValue
    @IsReserved.setter
    def IsReserved(self, newvalue):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeIsReserved == 'IsReserved':
                elem.childNodes[0].nodeValue = newvalue




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



class APIQuery(BESAPICoreElement):
    @property
    def Error(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Error':
                return elem.childNodes[0].nodeValue
        return None

    @property
    def EvaluationTime(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Evaluation':
                #find the evaluation time node
                for subelem in elem.childNodes:
                    if subelem.nodeType == Node.ELEMENT_NODE and subelem.nodeName == 'Time':
                        return subelem.childNodes[0].nodeValue
        return None

    @property
    def EvaluationPlurality(self):
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Evaluation':
                #find the evaluation time node
                for subelem in elem.childNodes:
                    if subelem.nodeType == Node.ELEMENT_NODE and subelem.nodeName == 'Plurality':
                        return subelem.childNodes[0].nodeValue
        return None

    def _parse_result_element(self, element):
        if element.nodeName == 'Answer':
            return element.childNodes[0].nodeValue
        elif element.nodeName == 'Tuple':
            res = []
            for sube in element.childNodes:
                if sube.nodeType == Node.ELEMENT_NODE and sube.nodeName in ('Answer', 'Tuple'):
                    res.append(self._parse_result_element(sube))
            return res
        else:
            return None

    @property
    def Result(self):
        res = []
        for elem in self.base_node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE and elem.nodeName == 'Result':
                for subelem in elem.childNodes:
                    if subelem.nodeType == Node.ELEMENT_NODE and subelem.nodeName in ('Answer', 'Tuple'):
                        res.append(self._parse_result_element(subelem))
        return res





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
                elif elem.nodeName == 'Property':
                    self.elements.append(Property(elem))
                elif elem.nodeName == 'SingleAction':
                    self.elements.append(SingleAction(elem))
                elif elem.nodeName == 'ComputerGroup':
                    self.elements.append(ComputerGroup(elem))
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
                elif elem.nodeName == 'Action':
                    self.elements.append(APIAction(elem))
                elif elem.nodeName == 'Property':
                    self.elements.append(APIProperty(elem))
                elif elem.nodeName == 'Query':
                    self.elements.append(APIQuery(elem))
                elif elem.nodeName == 'ComputerGroup':
                    self.elements.append(APIComputerGroup(elem))
                elif elem.nodeName == 'ManualComputerGroup':
                    self.elements.append(APIManualComputerGroup(elem))
                elif elem.nodeName == 'Operator':
                    self.elements.append(Operator(elem))
                elif elem.nodeName == 'Role':
                    self.elements.append(Role(elem))
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
            raise ValueError('Not a boolean value')
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
        if o.code not in (200, 201):
            raise ValueError('Exit code: {0}'.format(o.code))
        else:
            contents = o.read()
            if raw_response:
                return contents
            if re.search(r'\<BESAPI\s+', contents[:150], re.MULTILINE) != None:
                return BESAPIContainer(contents)
            elif re.search(r'\<BES\s+', contents[:150], re.MULTILINE) != None:
                return BESContainer(contents)
            else:
                raise ValueError('Not BESAPI nor BES xml element found')

    def post(self, resource, data=None, raw_response=False):
        req = self._build_base_request(resource)
        if data is None:
            req.get_method = lambda: 'POST'
            raw_response = True
        elif data is not None:
            if isinstance(data, BESContainer) or isinstance(data, BESAPIContainer):
                req.add_data(data.base_node.toxml())
            else:
                req.add_data(data)

        o = urlopen(req, **self._urlopen_kwargs)
        if o.code not in (200, 201):
            raise ValueError('Exit code: {0}'.format(o.code))
        else:
            contents = o.read()
            if raw_response:
                return contents
            if re.search(r'\<BESAPI\s+', contents[:150], re.MULTILINE) != None:
                return BESAPIContainer(contents)
            elif re.search(r'\<BES\s+', contents[:150], re.MULTILINE) != None:
                return BESContainer(contents)
            else:
                raise ValueError('Not BESAPI nor BES xml element found')

    def put(self, resource, data=None, raw_response=False):
        req = self._build_base_request(resource)
        if data is None:
            raw_response = True
        elif data is not None:
            if isinstance(data, BESContainer) or isinstance(data, BESAPIContainer):
                req.add_data(data.base_node.toxml())
            else:
                req.add_data(data)
        req.get_method = lambda: 'PUT'

        o = urlopen(req, **self._urlopen_kwargs)
        if o.code not in (200, 201):
            raise ValueError('Exit code: {0}'.format(o.code))
        else:
            contents = o.read()
            if raw_response:
                return contents
            if re.search(r'\<BESAPI\s+', contents[:150], re.MULTILINE) != None:
                return BESAPIContainer(contents)
            elif re.search(r'\<BES\s+', contents[:150], re.MULTILINE) != None:
                return BESContainer(contents)
            else:
                raise ValueError('Not BESAPI nor BES xml element found')

    def delete(self, resource, raw_response=False):
        req = self._build_base_request(resource)
        req.get_method = lambda: 'DELETE'

        o = urlopen(req, **self._urlopen_kwargs)
        if o.code not in (200, 201):
            raise ValueError('Exit code: {0}'.format(o.code))
        else:
            contents = o.read()
            if raw_response:
                return contents
            if re.search(r'\<BESAPI\s+', contents, re.MULTILINE) != None:
                return BESAPIContainer(contents[:150])
            elif re.search(r'\<BES\s+', contents, re.MULTILINE) != None:
                return BESContainer(contents[:150])
            elif contents == 'ok':
                return True
            else:
                return contents
