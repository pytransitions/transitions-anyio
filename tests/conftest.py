import pytest
from transitions.extensions import GraphMachine

from transitions_anyio import (AnyIOGraphMachine, AnyIOMachine,
                               HierarchicalAnyIOGraphMachine,
                               HierarchicalAnyIOMachine)

try:
    import graphviz
except ImportError:
    graphviz = None


@pytest.fixture(params=[
    pytest.param('asyncio'),
    pytest.param('trio'),
])
def anyio_backend(request):
    return request.param


@pytest.fixture(params=[
    pytest.param(AnyIOMachine),
    pytest.param(AnyIOGraphMachine),
    pytest.param(HierarchicalAnyIOMachine),
    pytest.param(HierarchicalAnyIOGraphMachine),
])
def machine_cls(request):
    cls = request.param
    if issubclass(cls, GraphMachine) and graphviz is None:
        pytest.skip("graphviz is not installed")
    return cls


@pytest.fixture
def m(machine_cls):
    return machine_cls(states=['A', 'B', 'C'], transitions=[['go', 'A', 'B']], initial='A')
