# Changelog

## Release 0.3.0b1 (June 2021)

- Minimum `anyio` version is `3.0`.
- Due to the minimum `anyio` version being `3.0`, `curio` support has been dropped, and hence `curio` has been removed as a project dependency.
- Minimum `Python` version is `3.7.1` because `contextvars` (not the backport) is dependency of `AsyncMachine` in `transitions>=0.8.6` due to the way that `AnyIOMachine` inherits from `AsyncMachine`.

## Release 0.2.0 (January 2021)

- This library now works without curio installed as it should have.

## Release 0.1.0 (January 2021)

Release 0.1.0 is the initial release:

- Introduced `AnyIOMachine`, `AnyIOGraphMachine`, `HierarchicalAnyIOMachine` and `HierarchicalAnyIOGraphMachine`
- Compatible with `transitions>=0.8.6`
- Published on [PyPI](https://pypi.org/project/transitions-anyio/)
