=================
transitions-anyio
=================

An extension for the `transitions`_ state machine library
which runs asynchronous state machines using `anyio`_.

This library provides the `AnyIOMachine`, `AnyIOGraphMachine`, `HierarchicalAnyIOMachine`
and the `HierarchicalAnyIOGraphMachine` variants.
They function exactly like their respective `Async*` variants.
Please refer to transitions' documentation for usage examples.

.. _transitions: https://github.com/pytransitions/transitions
.. _anyio: https://github.com/agronholm/anyio