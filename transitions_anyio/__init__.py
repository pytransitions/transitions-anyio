from anyio import create_task_group, get_cancelled_exc_class, open_cancel_scope
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
                await tg.spawn(with_result, par)

        return results

    async def process_context(self, func, model):
        if self.current_context.get() is None:
            try:
                async with open_cancel_scope() as scope:
                    self.current_context.set(scope)
                    return await func()
            except get_cancelled_exc_class():
                return False
        return await func()

    def switch_model_context(self, model):
        current_scope = self.current_context.get()
        running_scope = self.async_tasks.get(model, None)
        if current_scope != running_scope:
            if running_scope is not None:
                self.async_tasks[model].cancel()
            self.async_tasks[model] = self.current_context.get()


class AnyIOGraphMachine(GraphMachine, AnyIOMachine):
    transition_cls = AsyncTransition


class HierarchicalAnyIOMachine(AnyIOMachine, HierarchicalAsyncMachine):
    pass


class HierarchicalAnyIOGraphMachine(GraphMachine, HierarchicalAnyIOMachine):
    transition_cls = NestedAsyncTransition
