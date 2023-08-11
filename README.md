# Marble python client
A python library to access information about the Marble climate infomatics network. The library provides a pythonic interface to the Marble network's [central registry](https://github.com/DACCS-Climate/Marble-node-registry). Users of the network are encouraged to use this library to access the network information and avoid hardcoding URLs to various nodes or services.

## Basic usage

The first thing to do is to get a `client` object:

```python
>>> from marble_client import MarbleClient

>>> client = MarbleClient()
```

All the information about the network can now be retrieved from the `client` object. E.g. the nodes available in the network can be accessed as:
```python
>>> client.nodes
{'UofT': <marble_client.node.MarbleNode at 0x10c129990>,
 'PAVICS': <marble_client.node.MarbleNode at 0x10c6dd690>,
 'Hirondelle': <marble_client.node.MarbleNode at 0x10c6dd890>}
```
The returned object is a python `dict` with node names for keys and `MarbleNode` objects as values. A particular node can be accessed as:

```python
>>> mynode = client['UofT']
>>> type(mynode)
marble_client.node.MarbleNode
```

Now that one has a Marble node of interest, a useful operation would be to check if that node is online in realtime, this can be done as:

```python
>>> mynode.is_online()
True
```

The URL for the node can be retrieved as:
```python
>>> mynode.url
'https://daccs.cs.toronto.edu'
```

Various other qualities about the node can be accessed as shown below (see [implementation](https://github.com/DACCS-Climate/marble_client_python/blob/main/marble_client/node.py) for the full list of available attributes).

```python
>>> mynode.affiliation
'University of Toronto'
>>> mynode.contact
'daccs-info@cs.toronto.edu'
>>> mynode.marble_version  # The version of the software stack available on this node
'1.27.0'
>>> mynode.location
{'longitude': -79.39, 'latitude': 43.65}
```

The "services" that a Marble node offers can differ from one node to another. A list of which services are offered at a given node can be inquired as follows:
```python
>>> mynode.services
['geoserver',
 'flyingpigeon',
 'finch',
 'raven',
 'hummingbird',
 'thredds',
 'jupyterhub',
 'weaver']
```

To get further information on one of the services, first retrieve that service. This can be done in one of two ways:
```python
>>> service = mynode['thredds']
>>> type(service)
marble_client.services.MarbleService
>>> 
>>> service = mynode.thredds
>>> type(service)
marble_client.services.MarbleService
```

The most important thing one needs from the service is the endpoint at which the service is located:
```python
>>> service.url
'https://daccs.cs.toronto.edu/thredds/'
```

The service URL can also be accessed directly using the service object's name:
```python
>>> service
'https://daccs.cs.toronto.edu/thredds/'
```

Various attributes that can be accessed on the `MarbleService` object can be found by consulting the [implementation](https://github.com/DACCS-Climate/marble_client_python/blob/main/marble_client/services.py).

Of course, all operations can be chained, so if you don't need `MarbleClient`, `MarbleNode` or `MarbleService` objects for future operations, then to get, for example, the weaver service endpoint for the "PAVICS" node, one can do:
```python
>>> url = MarbleClient()["PAVICS"].weaver.url # returns a string object
>>> print(f"Weaver URL is {url}")
Weaver URL is https://pavics.ouranos.ca/weaver/
>>> # A MarbleService object is returned that can be used wherever a string can be used
>>> print(f"Weaver URL is {MarbleClient()['PAVICS'].weaver}")
Weaver URL is https://pavics.ouranos.ca/weaver/
```