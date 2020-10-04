from unittest.mock import MagicMock

import anyio
import pytest
from transitions import MachineError

from transitions_anyio import HierarchicalAnyIOMachine

pytestmark = pytest.mark.anyio


async def await_true():
    await anyio.sleep(0.1)
    return True


async def await_false():
    await anyio.sleep(0.1)
    return False


def synced_true():
    return True


async def cancel_soon():
    await anyio.sleep(1)
    raise TimeoutError("Callback was not cancelled!")


async def call_delayed(func, time):
    await anyio.sleep(time)
    await func()


class DummyModel(object):
    pass


async def test_async_machine_cb(m):
    mock = MagicMock()

    async def async_process():
        await anyio.sleep(0.1)
        mock()

    m.after_state_change = async_process
    await m.go()
    assert m.state == 'B'
    mock.assert_called_once_with()


async def test_async_condition(m):
    m.add_transition('proceed', 'A', 'C', conditions=await_true, unless=await_false)
    await m.proceed()
    assert m.state == 'C'


async def test_async_enter_exit(m):
    enter_mock = MagicMock()
    exit_mock = MagicMock()

    async def async_enter():
        await anyio.sleep(0.1)
        enter_mock()

    async def async_exit():
        await anyio.sleep(0.1)
        exit_mock()

    m.on_exit_A(async_exit)
    m.on_enter_B(async_enter)
    await m.go()

    enter_mock.assert_called_once_with()
    exit_mock.assert_called_once_with()


async def test_async_conditions(m):
    mock = MagicMock()

    m.add_transition('proceed', 'A', 'C', conditions=synced_true, after=mock)

    await m.proceed()

    assert m.state == 'C'
    mock.assert_called_once_with()


@pytest.mark.xfail(reason="we should investigate")
async def test_multiple_models(machine_cls):
    m1 = machine_cls(states=['A', 'B', 'C'], initial='A', name="m1")
    m2 = machine_cls(states=['A'], initial='A', name='m2')
    m1.add_transition(trigger='go', source='A', dest='B', before=cancel_soon)
    m1.add_transition(trigger='fix', source='A', dest='C', after=cancel_soon)
    m1.add_transition(trigger='check', source='C', dest='B', conditions=await_false)
    m1.add_transition(trigger='reset', source='C', dest='A')
    m2.add_transition(trigger='go', source='A', dest=None, conditions=m1.is_C, after=m1.reset)

    async with anyio.create_task_group() as tg:
        await tg.spawn(m1.go)
        await tg.spawn(call_delayed, m1.fix, 0.05)
        await tg.spawn(call_delayed, m1.check, 0.07)
        await tg.spawn(call_delayed, m2.go, 0.1)

    assert m1.is_A()


async def test_async_callback_arguments(m):
    async def process(should_fail=True):
        if should_fail is not False:
            raise ValueError("should_fail has been set")

    m.on_enter_B(process)
    with pytest.raises(ValueError):
        await m.go()
    await m.to_A()
    await m.go(should_fail=False)


async def test_async_callback_event_data(machine_cls):
    state_a = machine_cls.state_cls('A')
    state_b = machine_cls.state_cls('B')

    def sync_condition(event_data):
        return event_data.state == state_a

    async def async_conditions(event_data):
        return event_data.state == state_a

    async def async_callback(event_data):
        assert event_data.state == state_b

    def sync_callback(event_data):
        assert event_data.state == state_b

    m = machine_cls(states=[state_a, state_b], initial='A', send_event=True)
    m.add_transition('go', 'A', 'B', conditions=[sync_condition, async_conditions],
                     after=[sync_callback, async_callback])
    m.add_transition('go', 'B', 'A', conditions=sync_condition)
    await m.go()
    assert m.is_B() is True
    await m.go()
    assert m.is_B() is True


async def test_async_invalid_triggers(m):
    await m.to_B()

    with pytest.raises(MachineError):
        await m.go()

    m.ignore_invalid_triggers = True
    await m.go()

    assert m.is_B() is True


async def test_async_dispatch(machine_cls):
    model1 = DummyModel()
    model2 = DummyModel()
    model3 = DummyModel()

    machine = machine_cls(model=None, states=['A', 'B', 'C'], transitions=[['go', 'A', 'B'],
                                                                           ['go', 'B', 'C'],
                                                                           ['go', 'C', 'A']], initial='A')
    machine.add_model(model1)
    machine.add_model(model2, initial='B')
    machine.add_model(model3, initial='C')
    await machine.dispatch('go')
    assert model1.is_B() is True
    assert 'C' == model2.state
    assert machine.initial == model3.state


@pytest.mark.xfail(reason="we should investigate")
async def test_queued(machine_cls):
    states = ['A', 'B', 'C', 'D']

    # Define with list of dictionaries

    async def change_state(machine):
        assert machine.state == 'A'
        if machine.has_queue:
            await machine.run(machine=machine)
            assert machine.state == 'A'
        else:
            with pytest.raises(MachineError):
                await machine.run(machine=machine)

    async def raise_machine_error(event_data):
        assert event_data.machine.has_queue is True
        await event_data.model.to_A()
        event_data.machine._queued = False
        await event_data.model.to_C()

    async def raise_exception(event_data):
        await event_data.model.to_C()
        raise ValueError("Clears queue")

    transitions = [
        {'trigger': 'walk', 'source': 'A', 'dest': 'B', 'before': change_state},
        {'trigger': 'run', 'source': 'B', 'dest': 'C'},
        {'trigger': 'sprint', 'source': 'C', 'dest': 'D'}
    ]

    m = machine_cls(states=states, transitions=transitions, initial='A')
    await m.walk(machine=m)
    assert 'B' == m.state
    m = machine_cls(states=states, transitions=transitions, initial='A', queued=True)
    await m.walk(machine=m)
    assert 'C' == m.state
    m = machine_cls(states=states, initial='A', queued=True, send_event=True,
                    before_state_change=raise_machine_error)
    with pytest.raises(MachineError):
        await m.to_C()
    m = machine_cls(states=states, initial='A', queued=True, send_event=True)
    m.add_transition('go', 'A', 'B', after='go')
    m.add_transition('go', 'B', 'C', before=raise_exception)
    with pytest.raises(ValueError):
        await m.go()
    assert 'B' == m.state


async def test_callback_order(machine_cls):
    finished = []

    class Model:
        async def before(self):
            await anyio.sleep(0.1)
            finished.append(2)

        async def after(self):
            await anyio.sleep(0.1)
            finished.append(3)

    async def after_state_change():
        finished.append(4)

    async def before_state_change():
        finished.append(1)

    model = Model()
    m = machine_cls(
        model=model,
        states=['start', 'end'],
        after_state_change=after_state_change,
        before_state_change=before_state_change,
        initial='start',
    )
    m.add_transition('transit', 'start', 'end', after='after', before='before')
    await model.transit()
    assert finished == [1, 2, 3, 4]


async def test_nested_async():
    mock = MagicMock()

    async def sleep_mock():
        await anyio.sleep(0.1)
        mock()

    states = ['A', 'B', {'name': 'C', 'children': ['1', {'name': '2', 'children': ['a', 'b'], 'initial': 'a'},
                                                   '3'], 'initial': '2'}]
    transitions = [{'trigger': 'go', 'source': 'A', 'dest': 'C',
                    'after': [sleep_mock] * 100}]
    machine = HierarchicalAnyIOMachine(states=states, transitions=transitions, initial='A')
    await machine.go()
    assert 'C{0}2{0}a'.format(machine.state_cls.separator) == machine.state
    assert 100 == mock.call_count


async def test_parallel_async():
    states = ['A', 'B', {'name': 'P',
                         'parallel': [
                             {'name': '1', 'children': ['a'], 'initial': 'a'},
                             {'name': '2', 'children': ['b', 'c'], 'initial': 'b'},
                             {'name': '3', 'children': ['x', 'y', 'z'], 'initial': 'y'}]}]
    machine = HierarchicalAnyIOMachine(states=states, initial='A')
    await machine.to_P()
    assert [
               'P{0}1{0}a'.format(machine.state_cls.separator),
               'P{0}2{0}b'.format(machine.state_cls.separator),
               'P{0}3{0}y'.format(machine.state_cls.separator)
           ] == machine.state
    await machine.to_B()
    assert machine.is_B() is True
