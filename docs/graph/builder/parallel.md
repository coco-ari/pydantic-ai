# 并行执行 {#parallel-execution}

graph builder API 为并行执行提供了两种强大机制：**broadcasting** 和 **mapping**。

## 概览 {#overview}

- **Broadcasting** - 将相同数据发送到多个并行路径
- **Spreading** - 将 iterable 中的 items fan out 到并行路径

二者都会在 execution graph 中创建 "forks"，随后可用 [join nodes](joins.md) 同步。

## Broadcasting 广播 {#broadcasting}

Broadcasting 会同时将相同数据发送到多个目标：

```python {title="basic_broadcast.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[int])

    @g.step
    async def source(ctx: StepContext[SimpleState, None, None]) -> int:
        return 10

    @g.step
    async def add_one(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs + 1

    @g.step
    async def add_two(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs + 2

    @g.step
    async def add_three(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs + 3

    collect = g.join(reduce_list_append, initial_factory=list[int])

    # Broadcasting：将 source 中的值发送到全部三个 steps
    g.add(
        g.edge_from(g.start_node).to(source),
        g.edge_from(source).to(add_one, add_two, add_three),
        g.edge_from(add_one, add_two, add_three).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> [11, 12, 13]
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

三个 steps 都会接收相同 input value（`10`）并并行执行。

## Spreading 展开 {#spreading}

Spreading 会 fan out iterable 中的元素，并行处理每个元素：

```python {title="basic_map.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[int])

    @g.step
    async def generate_list(ctx: StepContext[SimpleState, None, None]) -> list[int]:
        return [1, 2, 3, 4, 5]

    @g.step
    async def square(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs * ctx.inputs

    collect = g.join(reduce_list_append, initial_factory=list[int])

    # Spreading：列表中每个 item 都获得自己的并行执行
    g.add(
        g.edge_from(g.start_node).to(generate_list),
        g.edge_from(generate_list).map().to(square),
        g.edge_from(square).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> [1, 4, 9, 16, 25]
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### Spreading AsyncIterables 展开异步可迭代对象 {#spreading-asynciterables}

`.map()` operation 也适用于 `AsyncIterable` values。对 async iterable 进行 mapping 时，graph 会在 values 被 yielded 时动态创建 parallel tasks。这对于 streaming data 或处理动态生成的数据尤其有用：

```python {title="async_iterable_map.py"}
import asyncio
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[int])

    @g.stream
    async def stream_numbers(ctx: StepContext[SimpleState, None, None]):
        """带延迟地流式生成数字，以模拟实时数据。"""
        for i in range(1, 4):
            await asyncio.sleep(0.05)  # 模拟延迟
            yield i

    @g.step
    async def triple(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs * 3

    collect = g.join(reduce_list_append, initial_factory=list[int])

    g.add(
        g.edge_from(g.start_node).to(stream_numbers),
        # 对 async iterable map：items yield 时创建 tasks
        g.edge_from(stream_numbers).map().to(triple),
        g.edge_from(triple).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> [3, 6, 9]
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

这允许渐进式处理：当后续结果仍在生成时，下游 steps 可以先开始处理早期结果。

### 使用 `add_mapping_edge()` {#using-add_mapping_edge}

便捷方法 [`add_mapping_edge()`][pydantic_graph.graph_builder.GraphBuilder.add_mapping_edge] 提供了更简单的语法：

```python {title="mapping_convenience.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[str])

    @g.step
    async def generate_numbers(ctx: StepContext[SimpleState, None, None]) -> list[int]:
        return [10, 20, 30]

    @g.step
    async def stringify(ctx: StepContext[SimpleState, None, int]) -> str:
        return f'Value: {ctx.inputs}'

    collect = g.join(reduce_list_append, initial_factory=list[str])

    g.add(g.edge_from(g.start_node).to(generate_numbers))
    g.add_mapping_edge(generate_numbers, stringify)
    g.add(
        g.edge_from(stringify).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> ['Value: 10', 'Value: 20', 'Value: 30']
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 空 Iterables {#empty-iterables}

对空 iterable 进行 mapping 时，可以指定 `downstream_join_id`，以确保 join 仍会执行：

```python {title="empty_map.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[int])

    @g.step
    async def generate_empty(ctx: StepContext[SimpleState, None, None]) -> list[int]:
        return []

    @g.step
    async def double(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs * 2

    collect = g.join(reduce_list_append, initial_factory=list[int])

    g.add(g.edge_from(g.start_node).to(generate_empty))
    g.add_mapping_edge(generate_empty, double, downstream_join_id=collect.id)
    g.add(
        g.edge_from(double).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(result)
    #> []
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 嵌套并行操作 {#nested-parallel-operations}

你可以嵌套 broadcasts 和 maps，以表达复杂并行模式：

### 先 Spread 再 Broadcast {#spread-then-broadcast}

```python {title="map_then_broadcast.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[int])

    @g.step
    async def generate_list(ctx: StepContext[SimpleState, None, None]) -> list[int]:
        return [10, 20]

    @g.step
    async def add_one(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs + 1

    @g.step
    async def add_two(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs + 2

    collect = g.join(reduce_list_append, initial_factory=list[int])

    g.add(
        g.edge_from(g.start_node).to(generate_list),
        # spread 列表，然后将每个 item broadcast 到两个 steps
        g.edge_from(generate_list).map().to(add_one, add_two),
        g.edge_from(add_one, add_two).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> [11, 12, 21, 22]
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

结果包含：

- 来自 10：`10+1=11` 和 `10+2=12`
- 来自 20：`20+1=21` 和 `20+2=22`

### 多个连续 Spreads {#multiple-sequential-spreads}

```python {title="sequential_maps.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[str])

    @g.step
    async def generate_pairs(ctx: StepContext[SimpleState, None, None]) -> list[tuple[int, int]]:
        return [(1, 2), (3, 4)]

    @g.step
    async def unpack_pair(ctx: StepContext[SimpleState, None, tuple[int, int]]) -> list[int]:
        return [ctx.inputs[0], ctx.inputs[1]]

    @g.step
    async def stringify(ctx: StepContext[SimpleState, None, int]) -> str:
        return f'num:{ctx.inputs}'

    collect = g.join(reduce_list_append, initial_factory=list[str])

    g.add(
        g.edge_from(g.start_node).to(generate_pairs),
        # 第一次 map：每个 tuple 一个 task
        g.edge_from(generate_pairs).map().to(unpack_pair),
        # 第二次 map：每个 tuple 中的每个数字一个 task
        g.edge_from(unpack_pair).map().to(stringify),
        g.edge_from(stringify).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> ['num:1', 'num:2', 'num:3', 'num:4']
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## Edge Labels 边标签 {#edge-labels}

为 parallel edges 添加 labels，以改善文档：

```python {title="labeled_parallel.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[str])

    @g.step
    async def generate(ctx: StepContext[SimpleState, None, None]) -> list[int]:
        return [1, 2, 3]

    @g.step
    async def process(ctx: StepContext[SimpleState, None, int]) -> str:
        return f'item-{ctx.inputs}'

    collect = g.join(reduce_list_append, initial_factory=list[str])

    g.add(g.edge_from(g.start_node).to(generate))
    g.add_mapping_edge(
        generate,
        process,
        pre_map_label='before map',
        post_map_label='after map',
    )
    g.add(
        g.edge_from(process).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> ['item-1', 'item-2', 'item-3']
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 并行执行中的 State 共享 {#state-sharing-in-parallel-execution}

所有 parallel tasks 共享同一个 graph state。修改时要小心：

```python {title="parallel_state.py"}
from dataclasses import dataclass, field

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class CounterState:
    values: list[int] = field(default_factory=list)


async def main():
    g = GraphBuilder(state_type=CounterState, output_type=list[int])

    @g.step
    async def generate(ctx: StepContext[CounterState, None, None]) -> list[int]:
        return [1, 2, 3]

    @g.step
    async def track_and_square(ctx: StepContext[CounterState, None, int]) -> int:
        # 所有 parallel tasks 都会修改同一个 state
        ctx.state.values.append(ctx.inputs)
        return ctx.inputs * ctx.inputs

    collect = g.join(reduce_list_append, initial_factory=list[int])

    g.add(
        g.edge_from(g.start_node).to(generate),
        g.edge_from(generate).map().to(track_and_square),
        g.edge_from(track_and_square).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    state = CounterState()
    result = await graph.run(state=state)

    print(f'Squared: {sorted(result)}')
    #> Squared: [1, 4, 9]
    print(f'Tracked: {sorted(state.values)}')
    #> Tracked: [1, 2, 3]
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## Edge Transformations 边转换 {#edge-transformations}

你可以使用 `.transform()` 方法，在数据沿 edges 流动时进行 inline 转换：

```python {title="edge_transform.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=str)

    @g.step
    async def generate_number(ctx: StepContext[SimpleState, None, None]) -> int:
        return 42

    @g.step
    async def format_output(ctx: StepContext[SimpleState, None, str]) -> str:
        return f'The answer is: {ctx.inputs}'

    # inline 将数字转换为字符串
    g.add(
        g.edge_from(g.start_node).to(generate_number),
        g.edge_from(generate_number).transform(lambda ctx: str(ctx.inputs * 2)).to(format_output),
        g.edge_from(format_output).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(result)
    #> The answer is: 84
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

transform function 会接收包含当前 inputs 的 [`StepContext`][pydantic_graph.step.StepContext]，并可访问 state 和 dependencies。这适用于：

- 在不兼容 steps 之间转换数据类型
- 从复杂对象中提取特定字段
- 不创建完整 step 就应用简单计算
- 在路由期间适配数据格式

Transforms 可以链式调用，并与 `.map()` 和 `.label()` 等其他 edge operations 组合：

```python {title="chained_transforms.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=list[str])

    @g.step
    async def generate_data(ctx: StepContext[SimpleState, None, None]) -> list[dict[str, int]]:
        return [{'value': 10}, {'value': 20}, {'value': 30}]

    @g.step
    async def process_number(ctx: StepContext[SimpleState, None, int]) -> str:
        return f'Processed: {ctx.inputs}'

    collect = g.join(reduce_list_append, initial_factory=list[str])

    g.add(
        g.edge_from(g.start_node).to(generate_data),
        # 转换以提取 values，然后对它们 map
        g.edge_from(generate_data)
        .transform(lambda ctx: [item['value'] for item in ctx.inputs])
        .label('Extract values')
        .map()
        .to(process_number),
        g.edge_from(process_number).to(collect),
        g.edge_from(collect).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> ['Processed: 10', 'Processed: 20', 'Processed: 30']
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 后续步骤 {#next-steps}

- 了解用于聚合并行结果的 [join nodes](joins.md)
- 探索使用 decision nodes 的[条件分支](decisions.md)
- 查看 [steps documentation](steps.md) 了解更多 step execution 内容
