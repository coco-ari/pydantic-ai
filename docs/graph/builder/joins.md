# Join 与 Reducer

Join 节点用于同步并聚合来自并行执行路径的数据。它们使用 **Reducers** 将多个输入合并为单个输出。

## 概览 {#overview}

使用[并行执行](parallel.md)（广播或映射）时，你经常需要收集并合并结果。Join 节点用于完成这一工作：

1. 等待所有并行任务完成
2. 使用 [`ReducerFunction`][pydantic_graph.join.ReducerFunction] 聚合它们的输出
3. 将聚合后的结果传给下一个节点

## 创建 Joins {#creating-joins}

使用 `GraphBuilder.join`，并传入 reducer 函数和初始值或初始值工厂来创建 join：

```python {title="basic_join.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


g = GraphBuilder(state_type=SimpleState, output_type=list[int])

@g.step
async def generate_numbers(ctx: StepContext[SimpleState, None, None]) -> list[int]:
    return [1, 2, 3, 4, 5]

@g.step
async def square(ctx: StepContext[SimpleState, None, int]) -> int:
    return ctx.inputs * ctx.inputs

# Create a join to collect all squared values
collect = g.join(reduce_list_append, initial_factory=list[int])

g.add(
    g.edge_from(g.start_node).to(generate_numbers),
    g.edge_from(generate_numbers).map().to(square),
    g.edge_from(square).to(collect),
    g.edge_from(collect).to(g.end_node),
)

graph = g.build()

async def main():
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> [1, 4, 9, 16, 25]
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 内置 Reducers {#built-in-reducers}

Pydantic Graph 开箱即用地提供几种常见 reducer 类型：

### `reduce_list_append`

[`reduce_list_append`][pydantic_graph.join.reduce_list_append] 会把所有输入收集到一个列表：

```python {title="list_reducer.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[str])

    @g.step
    async def generate(ctx: StepContext[SimpleState, None, None]) -> list[int]:
        return [10, 20, 30]

    @g.step
    async def to_string(ctx: StepContext[SimpleState, None, int]) -> str:
        return f'value-{ctx.inputs}'

    collect = g.join(reduce_list_append, initial_factory=list[str])

    g.add(
        g.edge_from(g.start_node).to(generate),
        g.edge_from(generate).map().to(to_string),
        g.edge_from(to_string).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> ['value-10', 'value-20', 'value-30']
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### `reduce_list_extend`

[`reduce_list_extend`][pydantic_graph.join.reduce_list_extend] 会使用一个 item iterable 扩展列表：

```python {title="list_extend_reducer.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_extend


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[int])

    @g.step
    async def generate(ctx: StepContext[SimpleState, None, None]) -> list[int]:
        return [1, 2, 3]

    @g.step
    async def create_range(ctx: StepContext[SimpleState, None, int]) -> list[int]:
        """Create a range from 0 to the input value."""
        return list(range(ctx.inputs))

    collect = g.join(reduce_list_extend, initial_factory=list[int])

    g.add(
        g.edge_from(g.start_node).to(generate),
        g.edge_from(generate).map().to(create_range),
        g.edge_from(create_range).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> [0, 0, 0, 1, 1, 2]
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### `reduce_dict_update`

[`reduce_dict_update`][pydantic_graph.join.reduce_dict_update] 会合并字典：

```python {title="dict_reducer.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_dict_update


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=dict[str, int])

    @g.step
    async def generate_keys(ctx: StepContext[SimpleState, None, None]) -> list[str]:
        return ['apple', 'banana', 'cherry']

    @g.step
    async def create_entry(ctx: StepContext[SimpleState, None, str]) -> dict[str, int]:
        return {ctx.inputs: len(ctx.inputs)}

    merge = g.join(reduce_dict_update, initial_factory=dict[str, int])

    g.add(
        g.edge_from(g.start_node).to(generate_keys),
        g.edge_from(generate_keys).map().to(create_entry),
        g.edge_from(create_entry).to(merge),
        g.edge_from(merge).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    result = {k: result[k] for k in sorted(result)}  # force deterministic ordering
    print(result)
    #> {'apple': 5, 'banana': 6, 'cherry': 6}
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### `reduce_null`

[`reduce_null`][pydantic_graph.join.reduce_null] 会丢弃所有输入并返回 `None`。当你只关心副作用时很有用：

```python {title="null_reducer.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_null


@dataclass
class CounterState:
    total: int = 0


async def main():
    g = GraphBuilder(state_type=CounterState, output_type=int)

    @g.step
    async def generate(ctx: StepContext[CounterState, None, None]) -> list[int]:
        return [1, 2, 3, 4, 5]

    @g.step
    async def accumulate(ctx: StepContext[CounterState, None, int]) -> int:
        ctx.state.total += ctx.inputs
        return ctx.inputs

    # We don't care about the outputs, only the side effect on state
    ignore = g.join(reduce_null, initial=None)

    @g.step
    async def get_total(ctx: StepContext[CounterState, None, None]) -> int:
        return ctx.state.total

    g.add(
        g.edge_from(g.start_node).to(generate),
        g.edge_from(generate).map().to(accumulate),
        g.edge_from(accumulate).to(ignore),
        g.edge_from(ignore).to(get_total),
        g.edge_from(get_total).to(g.end_node),
    )

    graph = g.build()
    state = CounterState()
    result = await graph.run(state=state)
    print(result)
    #> 15
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### `reduce_sum`

[`reduce_sum`][pydantic_graph.join.reduce_sum] 会对数值求和：

```python {title="sum_reducer.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_sum


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=int)

    @g.step
    async def generate(ctx: StepContext[SimpleState, None, None]) -> list[int]:
        return [10, 20, 30, 40]

    @g.step
    async def identity(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs

    sum_join = g.join(reduce_sum, initial=0)

    g.add(
        g.edge_from(g.start_node).to(generate),
        g.edge_from(generate).map().to(identity),
        g.edge_from(identity).to(sum_join),
        g.edge_from(sum_join).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(result)
    #> 100
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### `ReduceFirstValue`

[`ReduceFirstValue`][pydantic_graph.join.ReduceFirstValue] 会返回收到的第一个值，并取消所有其他并行任务。这适合你想获得第一个成功结果的 "race" 场景：

```python {title="first_value_reducer.py"}
import asyncio
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, ReduceFirstValue, StepContext


@dataclass
class SimpleState:
    tasks_completed: int = 0


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=str)

    @g.step
    async def generate(ctx: StepContext[SimpleState, None, None]) -> list[int]:
        return [1, 12, 13, 14, 15]

    @g.step
    async def slow_process(ctx: StepContext[SimpleState, None, int]) -> str:
        """Simulate variable processing times."""
        # Simulate different delays
        await asyncio.sleep(ctx.inputs * 0.1)
        ctx.state.tasks_completed += 1
        return f'Result from task {ctx.inputs}'

    # Use ReduceFirstValue to get the first result and cancel the rest
    first_result = g.join(ReduceFirstValue[str](), initial=None, node_id='first_result')

    g.add(
        g.edge_from(g.start_node).to(generate),
        g.edge_from(generate).map().to(slow_process),
        g.edge_from(slow_process).to(first_result),
        g.edge_from(first_result).to(g.end_node),
    )

    graph = g.build()
    state = SimpleState()
    result = await graph.run(state=state)

    print(result)
    #> Result from task 1
    print(f'Tasks completed: {state.tasks_completed}')
    #> Tasks completed: 1
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 自定义 Reducers {#custom-reducers}

通过定义 [`ReducerFunction`][pydantic_graph.join.ReducerFunction] 来创建自定义 reducers：

```python {title="custom_reducer.py"}

from pydantic_graph import GraphBuilder, StepContext


def reduce_sum(current: int, inputs: int) -> int:
    """A reducer that sums numbers."""
    return current + inputs


async def main():
    g = GraphBuilder(output_type=int)

    @g.step
    async def generate(ctx: StepContext[None, None, None]) -> list[int]:
        return [5, 10, 15, 20]

    @g.step
    async def identity(ctx: StepContext[None, None, int]) -> int:
        return ctx.inputs

    sum_join = g.join(reduce_sum, initial=0)

    g.add(
        g.edge_from(g.start_node).to(generate),
        g.edge_from(generate).map().to(identity),
        g.edge_from(identity).to(sum_join),
        g.edge_from(sum_join).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run()
    print(result)
    #> 50
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 可访问状态的 Reducers {#reducers-with-state-access}

Reducers 可以访问并修改图状态：

```python {title="stateful_reducer.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, ReducerContext, StepContext


@dataclass
class MetricsState:
    total_count: int = 0
    total_sum: int = 0


@dataclass
class ReducedMetrics:
    count: int = 0
    sum: int = 0


def reduce_metrics_sum(ctx: ReducerContext[MetricsState, None], current: ReducedMetrics, inputs: int) -> ReducedMetrics:
    ctx.state.total_count += 1
    ctx.state.total_sum += inputs
    return ReducedMetrics(count=current.count + 1, sum=current.sum + inputs)

def reduce_metrics_max(current: ReducedMetrics, inputs: ReducedMetrics) -> ReducedMetrics:
    return ReducedMetrics(count=max(current.count, inputs.count), sum=max(current.sum, inputs.sum))


async def main():
    g = GraphBuilder(state_type=MetricsState, output_type=dict[str, int])

    @g.step
    async def generate(ctx: StepContext[object, None, None]) -> list[int]:
        return [1, 3, 5, 7, 9, 10, 20, 30, 40]

    @g.step
    async def process_even(ctx: StepContext[MetricsState, None, int]) -> int:
        return ctx.inputs * 2

    @g.step
    async def process_odd(ctx: StepContext[MetricsState, None, int]) -> int:
        return ctx.inputs * 3

    metrics_even = g.join(reduce_metrics_sum, initial_factory=ReducedMetrics, node_id='metrics_even')
    metrics_odd = g.join(reduce_metrics_sum, initial_factory=ReducedMetrics, node_id='metrics_odd')
    metrics_max = g.join(reduce_metrics_max, initial_factory=ReducedMetrics, node_id='metrics_max')

    g.add(
        g.edge_from(g.start_node).to(generate),
        # Send even and odd numbers to their respective `process` steps
        g.edge_from(generate).map().to(
            g.decision()
            .branch(g.match(int, matches=lambda x: x % 2 == 0).label('even').to(process_even))
            .branch(g.match(int, matches=lambda x: x % 2 == 1).label('odd').to(process_odd))
        ),
        # Reduce metrics for even and odd numbers separately
        g.edge_from(process_even).to(metrics_even),
        g.edge_from(process_odd).to(metrics_odd),
        # Aggregate the max values for each field
        g.edge_from(metrics_even).to(metrics_max),
        g.edge_from(metrics_odd).to(metrics_max),
        # Finish the graph run with the final reduced value
        g.edge_from(metrics_max).to(g.end_node),
    )

    graph = g.build()
    state = MetricsState()
    result = await graph.run(state=state)

    print(f'Result: {result}')
    #> Result: ReducedMetrics(count=5, sum=200)
    print(f'State total_count: {state.total_count}')
    #> State total_count: 9
    print(f'State total_sum: {state.total_sum}')
    #> State total_sum: 275
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### 取消同级任务 {#canceling-sibling-tasks}

可访问 [`ReducerContext`][pydantic_graph.join.ReducerContext] 的 reducers 可以调用 [`ctx.cancel_sibling_tasks()`][pydantic_graph.join.ReducerContext.cancel_sibling_tasks]，取消同一个 fork 中的所有其他并行任务。当你已经找到所需内容并希望提前终止时，这很有用：

```python {title="cancel_siblings.py"}
import asyncio
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, ReducerContext, StepContext


@dataclass
class SearchState:
    searches_completed: int = 0


def reduce_find_match(ctx: ReducerContext[SearchState, None], current: str | None, inputs: str) -> str | None:
    """Return the first input that contains 'target' and cancel remaining tasks."""
    if current is not None:
        # We already found a match, ignore subsequent inputs
        return current
    if 'target' in inputs:
        # Found a match! Cancel all other parallel tasks
        ctx.cancel_sibling_tasks()
        return inputs
    return None


async def main():
    g = GraphBuilder(state_type=SearchState, output_type=str | None)

    @g.step
    async def generate_searches(ctx: StepContext[SearchState, None, None]) -> list[str]:
        return ['item1', 'item2', 'target_item', 'item4', 'item5']

    @g.step
    async def search(ctx: StepContext[SearchState, None, str]) -> str:
        """Simulate a slow search operation."""
        # make the search artificially slower for 'item4' and 'item5'
        search_duration = 0.1 if ctx.inputs not in {'item4', 'item5'} else 1.0
        await asyncio.sleep(search_duration)
        ctx.state.searches_completed += 1
        return ctx.inputs

    find_match = g.join(reduce_find_match, initial=None)

    g.add(
        g.edge_from(g.start_node).to(generate_searches),
        g.edge_from(generate_searches).map().to(search),
        g.edge_from(search).to(find_match),
        g.edge_from(find_match).to(g.end_node),
    )

    graph = g.build()
    state = SearchState()
    result = await graph.run(state=state)

    print(f'Found: {result}')
    #> Found: target_item
    print(f'Searches completed: {state.searches_completed}')
    #> Searches completed: 3
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

注意这里只有 3 次搜索完成，而不是全部 5 次，因为 reducer 在找到匹配项后取消了剩余任务。

## 多个 Joins {#multiple-joins}

一个图可以拥有多个相互独立的 joins：

```python {title="multiple_joins.py"}
from dataclasses import dataclass, field

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class MultiState:
    results: dict[str, list[int]] = field(default_factory=dict)


async def main():
    g = GraphBuilder(state_type=MultiState, output_type=dict[str, list[int]])

    @g.step
    async def source_a(ctx: StepContext[MultiState, None, None]) -> list[int]:
        return [1, 2, 3]

    @g.step
    async def source_b(ctx: StepContext[MultiState, None, None]) -> list[int]:
        return [10, 20]

    @g.step
    async def process_a(ctx: StepContext[MultiState, None, int]) -> int:
        return ctx.inputs * 2

    @g.step
    async def process_b(ctx: StepContext[MultiState, None, int]) -> int:
        return ctx.inputs * 3

    join_a = g.join(reduce_list_append, initial_factory=list[int], node_id='join_a')
    join_b = g.join(reduce_list_append, initial_factory=list[int], node_id='join_b')

    @g.step
    async def store_a(ctx: StepContext[MultiState, None, list[int]]) -> None:
        ctx.state.results['a'] = ctx.inputs

    @g.step
    async def store_b(ctx: StepContext[MultiState, None, list[int]]) -> None:
        ctx.state.results['b'] = ctx.inputs

    @g.step
    async def combine(ctx: StepContext[MultiState, None, None]) -> dict[str, list[int]]:
        return ctx.state.results

    g.add(
        g.edge_from(g.start_node).to(source_a, source_b),
        g.edge_from(source_a).map().to(process_a),
        g.edge_from(source_b).map().to(process_b),
        g.edge_from(process_a).to(join_a),
        g.edge_from(process_b).to(join_b),
        g.edge_from(join_a).to(store_a),
        g.edge_from(join_b).to(store_b),
        g.edge_from(store_a, store_b).to(combine),
        g.edge_from(combine).to(g.end_node),
    )

    graph = g.build()
    state = MultiState()
    result = await graph.run(state=state)

    print(f"Group A: {sorted(result['a'])}")
    #> Group A: [2, 4, 6]
    print(f"Group B: {sorted(result['b'])}")
    #> Group B: [30, 60]
```

_（这个示例是完整的，可以"按原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 自定义 Join 节点 {#customizing-join-nodes}

### 自定义节点 ID {#custom-node-ids}

与 steps 一样，joins 也可以有自定义 ID：

```python {title="join_custom_id.py" requires="basic_join.py"}
from pydantic_graph import reduce_list_append

from basic_join import g

my_join = g.join(reduce_list_append, initial_factory=list[int], node_id='my_custom_join_id')
```

## Joins 如何工作 {#how-joins-work}

在内部，图会跟踪每个并行任务属于哪个 "fork"。一个 join 会：

1. 识别其父 fork（创建并行路径的 fork）
2. 等待来自该 fork 的所有任务到达 join
3. 对每个传入值调用 `reduce()`
4. 在收到所有值后调用 `finalize()`
5. 将最终结果传给下游节点

这可以确保即便存在嵌套并行操作，也能正确同步。

## 下一步 {#next-steps}

- 了解带广播和映射的[并行执行](parallel.md)
- 通过 decision nodes 探索[条件分支](decisions.md)
- 查看 [API 参考][pydantic_graph.join]，了解完整 reducer 文档
