# README
This library allows for executing queries to BigFix REST Api without much knowledge of xml schema constructions. At this moment the coverage of xml schema objects is scarce, but will be extended over time. For details, read source code. Hint: Start with Client class.

# DISCLAIMER
This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# HOWTO
## Client
To communicate with BigFix server, Client class is used. It supports all request methods: get, post, put and delete. It assumes connections are made over HTTPS protocol. Constructor accepts following parameters:
* hostname (required): hostname of ip address of BigFix server
* port (required): port over which connections will be made
* username (required): username for authentication
* password (required): password for authentication
* rewrite_resource (optional)(default: False)(not implemented): It will force client to rewrite each object's request to always contain hostname and port from client parameters instead of what is returned by API
* verify_certificate (optional)(default: False): If set to true, urllib will verify if SSL certificate is correct upon each request

Client object has one method per each request defined. First argument to those methods is always a resource url. So to get the list of computers, the code could look like this:

```python
from barc import Client

c = Client('localhost', 443, 'temadmin', 'secretpassword')
computer_list = c.get('https://localhost:443/api/computers')
```

Client is smart enough to build it's own resource urls, so the request may as well look like this:

```python
computer_list = c.get('/api/computers')
```

or even this:

```python
computer_list = c.get('/computers')
```

With any of those requests, Client will build rest of the resource url. All of the request methods will return container objects (more on those later on) for either BES xml or BESAPI xml schema, depending on the type of request. If the direct xml string response is required from the resource, an optional parameter raw_response can be set to true. Additionally post and put methods also require data as parameter in form of container object. List of the request methods and their parameters:

* get(resource, raw_response=False)
   * resource (required): a string containing resource url
   * raw_response (optional): if set to true, get method will return xml string instead of container object
* post(resource, data, raw_response=False)
   * resource (required): a string containing resource url
   * data (required): a container object
   * raw_response (optional): if set to true, get method will return xml string instead of container object
* put(resource, data, raw_response=False)
   * resource (required): a string containing resource url
   * data (required): a container object
   * raw_response (optional): if set to true, get method will return xml string instead of container object
* delete(resource, raw_response=False)
   * resource (required): a string containing resource url
   * raw_response (optional): if set to true, get method will return xml string instead of container object

## Container objects
There are 2 classes for container objects: BESContainer and BESAPIContainer which are representing BES xml nodes and BESAPI xml nodes respectively. Both clases can be used to either parse responses from api as well as creating new empty containers for future use with requests. As mentioned above, Client object will return object based on either of those classes, depending on what type of content API will return. The classes accept string containing xml or file descriptor to a file containing xml for parsing. Every object will contain base_node property, which is a xmldom object with parsed/generated xml. At any moment, this property can be used to view, or modify xml manually. Example:

```python
from barc import BESContainer

payload = BESContainer()
print payload.base_node.toxml()
```

This would produce:

```xml
<BES xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BES.xsd"></BES>
```

Container objects behave a bit like lists. You can append elements to it, remove them, and iterate over all of the elements. When appending and deleting objects, object will take care of properly modifying the xml structure inside base_node. Container objects returned from requests will also contain a list of requested/processed elements. Example:

```python
from barc import Client

c = Client('localhost', 443, 'temadmin', 'secretpassword')
computers_payload = c.get('/computers')

print computers_payload.base_node.toxml()

for comp in computers_payload:
    print comp.Resource

del(computers_payload[0])
print computers_payload.base_node.toxml()
```

## Element objects
Element objects are representing all of the nodes which are available via REST api and reflect actual things from BigFix server. For instance a single computer, a single task, etc. Each of those elements is supposed to have a dedicated class. For instance APIComputer class represents Computer node returned inside BESAPI xml schema when requesting for a list of computers; APIFixlet class represents Fixlet node returned inside BESAPI xml schema when requesting for list of fixlets; Fixlet class represents Fixlet node returned inside BES xml schema when requesting for a specific fixlet by it's id; Fixlet class can also be used as a building block for a new fixlet and used with post method to create new fixlet inside BigFix server.

For now there is a limited coverage of elements available via BigFix, but even if the library does not have coverage (which means dedicated class) for a specific element, it will still return either BESCoreElement or BESAPICoreElement. While those objects do not provide easy possibility to modify specific objects, those still provide base_node property, which allows xml schema modification. Those CoreElement classes also provide possibility to interact with client requests put and post methods. This means, that while there is no full coverage at the moment, the library will still do it's best not to crash unexpectedly, and still provide as much help with interfacing with the api, as possible.

Element objects provide properties to easily manipulate with data available there. For now there is no index of all properties of all elements. Still python comes with batteries included, so you have all the tools you would ever need to dissect those objects. As an example, let's look at the class responsible for custom site coverage:

```python
from barc import CustomSite

site = CustomSite() # we're creating an empty site here
site.Name = 'TestSite1'
site.Subscription.Mode = 'All'
site.Domain = 'BESC'
site.Description = 'Generated with barc library'

print site.base_node.toxml()
```

The code will produce following xml schema:

```xml
<CustomSite><Name>TestSite1</Name><Description>Generated with barc library</Description><Domain>BESC</Domain><Subscription><Mode>All</Mode></Subscription></CustomSite>
```

First thing you will notice is that even though the properties have been updated with random order, the xml defined has a specific order of nodes inside. This is because BES.xsd schema for REST api actually defines exact order of nodes inside each element, and will not accept requests with incorrectly ordered nodes. This library will take care of this, and make sure that no matter how you define the element (given that you do not touch base_node directly) all of the nodes stay in correct order. Some of the properties will also perform some basic sanity check. Try updating a Domain property for the site with following value: 'BigFix Domain' and it will throw an exception, stating that Domain can only be 4 characters in size.

Elements can be appended to the container object to form a payload. This payload can be used to perform requests and create or modify content inside BigFix server. An example code for creating a site could look like this:

```python
from barc import Client, BESContainer, CustomSite

c = Client('localhost', 443, 'temadmin', 'password')

site = CustomSite()
site.Name = 'TestSite1'
site.Subscription.Mode = 'All'
site.Domain = 'BESC'
site.Description = 'Generated with barc library'

payload = BESContainer()
payload.append(site)

response = c.post(payload)
```

This is enough code to create a custom site, and there is not a single line of actual xml code. Everything is taken care of by the library. Additionally, once site is appended to the payload object, their base_node properties become connected in a way, so every future modification will result in the payload xml to be modified as well. Let's consider the following code:

```python
from barc import BESContainer, CustomSite

site = CustomSite()
site.Name = 'TestSite1'
site.Subscription.Mode = 'All'
site.Domain = 'BESC'
site.Description = 'Generated with barc library'

payload = BESContainer()
payload.append(site)

print payload.base_node.toxml()

site.Name = 'SiteForTest'
site.Description = 'Generated and modified later on'

print payload.base_node.toxml()
```

The first print will produce the following xml

```xml
<BES xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BES.xsd"><CustomSite><Name>TestSite1</Name><Description>Created with barc library</Description><Domain>BESC</Domain><Subscription><Mode>All</Mode></Subscription></CustomSite></BES>
```

While the second print will produce this:

```xml
<BES xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="BES.xsd"><CustomSite><Name>SiteForTest</Name><Description>Generated and modified later on</Description><Domain>BESC</Domain><Subscription><Mode>All</Mode></Subscription></CustomSite></BES>
```

This clearly shows that after the site has been generated and appended to payload container, any modification to the site object, will also update the payload, even though the payload itself was not interacted with directly. Container objects can accept an unlimited number of elements, so there is nothing stopping anyone from defining multiple custom sites, for instance, and appending those to the single payload. It will be updated with the contents of all of those elements. Elements can also be removed in a same way as it is with standard python lists, for instance by invoking: `del(payload[0])` and payload will also be updated and proper xml nodes removed from it. As a bonus, container objects, with a list of fixlets, tasks and analyses, can be saved into .bes file, and such file can be later imported using BigFix Console in a standard way.

# Known limitations
* When moving elements from one container to the other, it needs to be explicitly removed from one container, using del and then appended to the other container. In some rare cases the code can act unexpectedly and will not cleanup one container after it's element is moved to the other one.
