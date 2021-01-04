=================
transitions-anyio
=================

.. image:: https://img.shields.io/badge/version-v0.1.0-orange.svg
        :alt: Version
        :target: https://github.com/pytransitions/transitions-anyio

.. image:: https://img.shields.io/pypi/v/transitions-anyio.svg
        :alt: PyPI
        :target: https://pypi.org/project/transitions-anyio

.. image:: https://img.shields.io/github/commits-since/pytransitions/transitions-anyio/0.1.0.svg
        :alt: GitHub Commits
        :target: https://github.com/pytransitions/transitions-anyio/compare/0.1.0...master

.. image:: https://img.shields.io/github/license/pytransitions/transitions-anyio.svg
         :alt: License
         :target: https://github.com/pytransitions/transitions-anyio/blob/master/LICENSE

An extension for the `transitions`_ state machine library
which runs asynchronous state machines using `anyio`_.

This library provides the `AnyIOMachine`, `AnyIOGraphMachine`, `HierarchicalAnyIOMachine`
and the `HierarchicalAnyIOGraphMachine` variants.
They function exactly like their respective `Async*` variants.
Please refer to transitions' documentation for usage examples.

.. _transitions: https://github.com/pytransitions/transitions
.. _anyio: https://github.com/agronholm/anyio