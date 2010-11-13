========================
 Command Line Interface
========================

Framework for creating command line interfaces with basic readline
functionality.


Usage
=====

You can bind CLI to a terminal (console)::

    >>> from cli import Console, CLI
    >>> con = Console()
    >>> cli = CLI(con)
    >>> while True:
    ...     cli.read()
    ...

The ``Console`` class emulates a socket, you can also bind the CLI
to a (client) socket::

    >>> from cli import CLI
    >>> import socket
    >>> s = socket.socket()
    >>> s.bind(('0.0.0.0', 12345))
    >>> s.listen(1)
    >>> c, a = s.accept()
    >>> cli = CLI(c)
    >>> while True:
    ...     cli.read()
    ...


Features
========

* Both console and sockets are supported

* Tab completion

* History

  - History search

  - History completion

* Online help


TODO
====

* History persistance

