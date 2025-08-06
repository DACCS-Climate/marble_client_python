# Marble python client
A python library to access information about the Marble climate infomatics network. The library provides a pythonic interface to the Marble network's [central registry](https://github.com/DACCS-Climate/Marble-node-registry). Users of the network are encouraged to use this library to access the network information and avoid hardcoding URLs to various nodes or services.

## Installation

To install `marble_client` issue this command:
```shell
pip install marble-client
``` 

## Basic usage

The first thing to do is to get a `client` object:

```python
>>> from marble_client import MarbleClient

>>> client = MarbleClient()
```

All the information about the network can now be retrieved from the `client` object. E.g. the nodes available in the network can be accessed as:
```python
>>> client.nodes
{'UofTRedOak': <MarbleNode(id: 'UofTRedOak', name: 'Red Oak')>, 
 'PAVICS': <MarbleNode(id: 'PAVICS', name: 'PAVICS')>, 
 'Hirondelle': <MarbleNode(id: 'Hirondelle', name: 'Hirondelle')>}
```
The returned object is a python `dict` with node names for keys and `MarbleNode` objects as values. A particular node can be accessed as:

```python
>>> mynode = client['UofTRedOak']
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
'https://redoak.cs.toronto.edu'
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

## Jupyterlab functionality

When running in a Marble Jupyterlab environment, the client can take advantage of various environment variables and 
Jupyter's API to provide some additional functionality. 

> [!WARNING]
> Calling any of the methods described below outside a Marble Jupyterlab environment will raise a 
> `JupyterEnvironmentError`.

Get the node your notebook/script is currently running on:

```python
>>> client = MarbleClient()
>>> client.this_node
<MarbleNode(id: 'UofTRedOak', name: 'Red Oak')>
```

Add session cookies to a `requests.Session` object. This means that any request made with that session variable will
be made as if you were logged in to the current Marble node. This is the recommended way to access protected resources
programmatically in your scripts:

```python
>>> client = MarbleClient()
>>> session = requests.Session()
>>> client.this_session(session)
>>> session.cookies.get_dict()
{...} # session cookiejar now includes cookies
```

You can also use the `this_session` method to create a new `requests.Session` object:

```python
>>> client = MarbleClient()
>>> session = client.this_session()
>>> session.cookies.get_dict()
{...} # now includes session cookies
```

You can now make a request to a protected resource on the current node using this session object. You will be able to 
access the resource if you have permission:

```python
>>> session.get(f"{client.this_node.url}/some/protected/subpath")
```

## Interactively logging in to a node

In order to login to a different node or if you're running a script or notebook from outside a Marble
Jupyterlab environment, use the `MarbleNode.login` function to generate a `requests.Session` object.

This will prompt you to input your credentials to `stdin` or an input widget if you're in a compatible 
Jupyter environment.

## Contributing

We welcome any contributions to this codebase. To submit suggested changes, please do the following:

- create a new feature branch off of `main`
- update the code, write/update tests, write/update documentation
- submit a pull request targetting the `main` branch

To develop this project locally, first clone this repository and install the testing and development
dependencies:

```sh
pip install -e .[dev,test]
```

### Testing

Tests are located in the `tests/` folder can be run using `pytest`:

```sh
pytest tests/
```

### Coding Style

This codebase uses the [`ruff`](https://docs.astral.sh/ruff/) formatter and linter to enforce style policies.

To check that your changes conform to these policies please run:

```sh
ruff format
ruff check
```

You can also set up pre-commit hooks that will run these checks before you create any commit in this repo:

```sh
pre-commit install
```
