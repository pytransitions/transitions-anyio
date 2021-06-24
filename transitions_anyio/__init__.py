from anyio import create_task_group, CancelScope
from transitions.extensions import GraphMachine
from transitions.extensions.asyncio import (AsyncMachine, AsyncTransition,
                                            HierarchicalAsyncMachine,
                                            NestedAsyncTransition)


class AnyIOMachine(AsyncMachine):

    @staticmethod
    async def await_all(partials):
        results = []

        async def with_result(func):
            results.append(await func())

        async with create_task_group() as tg:
            for par in partials:
                tg.start_soon(with_result, par)

        return results

    async def process_context(self, func, model):
        current = self.current_context.get()
        if current is None:
            # If `res` is not set farther below by `await self._process(func, model)`
            # then there was probably a cancellation, for which `False` should be the
            # correct return value.
            res = False
            with CancelScope() as scope:
                self.current_context.set(scope)
                if model in self.async_tasks:
                    self.async_tasks[model].append(scope)
                else:
                    self.async_tasks[model] = [scope]
                res = await self._process(func, model)
            self.async_tasks[model].remove(scope)
            if len(self.async_tasks[model]) == 0:
                del self.async_tasks[model]
            return res
        return await self._process(func, model)

    async def switch_model_context(self, model):
        for running_task in self.async_tasks.get(model, []):
            if self.current_context.get() == running_task or running_task in self.protected_tasks:
                continue
            running_task.cancel()


class AnyIOGraphMachine(GraphMachine, AnyIOMachine):
    transition_cls = AsyncTransition


class HierarchicalAnyIOMachine(AnyIOMachine, HierarchicalAsyncMachine):
    pass


class HierarchicalAnyIOGraphMachine(GraphMachine, HierarchicalAnyIOMachine):
    transition_cls = NestedAsyncTransition
