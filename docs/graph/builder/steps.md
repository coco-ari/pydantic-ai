# Steps 步骤 {#steps}

Steps 是 graph 中的基本工作单元。它们是接收 [`StepContext`][pydantic_graph.step.StepContext] 并返回值的 async functions。

## 创建 Steps {#creating-steps}

Steps 通过 [`GraphBuilder`][pydantic_graph.graph_builder.GraphBuilder] 上的 [`@g.step`][pydantic_graph.graph_builder.GraphBuilder.step] 装饰器创建：

```python {title="basic_step.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class MyState:
    counter: int = 0

g = GraphBuilder(state_type=MyState, output_type=int)

@g.step
async def increment(ctx: StepContext[MyState, None, None]) -> int:
    ctx.state.counter += 1
    return ctx.state.counter

g.add(
    g.edge_from(g.start_node).to(increment),
    g.edge_from(increment).to(g.end_node),
)

graph = g.build()

async def main():
    state = MyState()
    result = await graph.run(state=state)
    print(result)
    #> 1
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## Step Context 步骤上下文 {#step-context}

每个 step function 都会将 [`StepContext`][pydantic_graph.step.StepContext] 作为第一个参数接收。context 提供对以下内容的访问：

- `ctx.state` - mutable graph state（类型：`StateT`）
- `ctx.deps` - 注入的 dependencies（类型：`DepsT`）
- `ctx.inputs` - 此 step 的 input data（类型：`InputT`）

### 访问 State {#accessing-state}

State 在 graph 中的所有 steps 之间共享，并且可以自由修改：

```python {title="state_access.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class AppState:
    messages: list[str]


async def main():
    g = GraphBuilder(state_type=AppState, output_type=list[str])

    @g.step
    async def add_hello(ctx: StepContext[AppState, None, None]) -> None:
        ctx.state.messages.append('Hello')

    @g.step
    async def add_world(ctx: StepContext[AppState, None, None]) -> None:
        ctx.state.messages.append('World')

    @g.step
    async def get_messages(ctx: StepContext[AppState, None, None]) -> list[str]:
        return ctx.state.messages

    g.add(
        g.edge_from(g.start_node).to(add_hello),
        g.edge_from(add_hello).to(add_world),
        g.edge_from(add_world).to(get_messages),
        g.edge_from(get_messages).to(g.end_node),
    )

    graph = g.build()
    state = AppState(messages=[])
    result = await graph.run(state=state)
    print(result)
    #> ['Hello', 'World']
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### 处理 Inputs {#working-with-inputs}

Steps 可以接收并转换 input data：

```python {title="step_inputs.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(
        state_type=SimpleState,
        input_type=int,
        output_type=str,
    )

    @g.step
    async def double_it(ctx: StepContext[SimpleState, None, int]) -> int:
        """将输入值加倍。"""
        return ctx.inputs * 2

    @g.step
    async def stringify(ctx: StepContext[SimpleState, None, int]) -> str:
        """转换为格式化字符串。"""
        return f'Result: {ctx.inputs}'

    g.add(
        g.edge_from(g.start_node).to(double_it),
        g.edge_from(double_it).to(stringify),
        g.edge_from(stringify).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=SimpleState(), inputs=21)
    print(result)
    #> Result: 42
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 依赖注入 {#dependency-injection}

Steps 可以通过 `ctx.deps` 访问注入的 dependencies：

```python {title="dependencies.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class AppState:
    pass


@dataclass
class AppDeps:
    """注入到 graph 中的 dependencies。"""

    multiplier: int


async def main():
    g = GraphBuilder(
        state_type=AppState,
        deps_type=AppDeps,
        input_type=int,
        output_type=int,
    )

    @g.step
    async def multiply(ctx: StepContext[AppState, AppDeps, int]) -> int:
        """用注入的 multiplier 乘以输入。"""
        return ctx.inputs * ctx.deps.multiplier

    g.add(
        g.edge_from(g.start_node).to(multiply),
        g.edge_from(multiply).to(g.end_node),
    )

    graph = g.build()
    deps = AppDeps(multiplier=10)
    result = await graph.run(state=AppState(), deps=deps, inputs=5)
    print(result)
    #> 50
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 自定义 Steps {#customizing-steps}

### 自定义 Node IDs {#custom-node-ids}

默认情况下，step node IDs 会从函数名推断。你可以覆盖它：

```python {title="custom_id.py" requires="basic_step.py"}
from pydantic_graph import StepContext

from basic_step import MyState, g


@g.step(node_id='my_custom_id')
async def my_step(ctx: StepContext[MyState, None, None]) -> int:
    return 42

# node ID 现在是 'my_custom_id'，而不是 'my_step'
```

### 人类可读 Labels {#human-readable-labels}

Labels 会为 diagram generation 提供文档：

```python {title="labels.py" requires="basic_step.py"}
from pydantic_graph import StepContext

from basic_step import MyState, g


@g.step(label='Increment the counter')
async def increment(ctx: StepContext[MyState, None, None]) -> int:
    ctx.state.counter += 1
    return ctx.state.counter

# 以编程方式访问 label
print(increment.label)
#> Increment the counter
```

## 顺序 Steps {#sequential-steps}

多个 steps 可以按顺序串联：

```python {title="sequential.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class MathState:
    operations: list[str]


async def main():
    g = GraphBuilder(
        state_type=MathState,
        input_type=int,
        output_type=int,
    )

    @g.step
    async def add_five(ctx: StepContext[MathState, None, int]) -> int:
        ctx.state.operations.append('add 5')
        return ctx.inputs + 5

    @g.step
    async def multiply_by_two(ctx: StepContext[MathState, None, int]) -> int:
        ctx.state.operations.append('multiply by 2')
        return ctx.inputs * 2

    @g.step
    async def subtract_three(ctx: StepContext[MathState, None, int]) -> int:
        ctx.state.operations.append('subtract 3')
        return ctx.inputs - 3

    # 按顺序连接 steps
    g.add(
        g.edge_from(g.start_node).to(add_five),
        g.edge_from(add_five).to(multiply_by_two),
        g.edge_from(multiply_by_two).to(subtract_three),
        g.edge_from(subtract_three).to(g.end_node),
    )

    graph = g.build()
    state = MathState(operations=[])
    result = await graph.run(state=state, inputs=10)

    print(f'Result: {result}')
    #> Result: 27
    print(f'Operations: {state.operations}')
    #> Operations: ['add 5', 'multiply by 2', 'subtract 3']
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

计算过程是：`(10 + 5) * 2 - 3 = 27`

## Streaming Steps 流式步骤 {#streaming-steps}

除了返回单个值的普通 steps，你还可以使用 [`@g.stream`][pydantic_graph.graph_builder.GraphBuilder.stream] 装饰器创建 streaming steps，让它们随时间 yield 多个值：

```python {title="streaming_step.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class SimpleState:
    pass


g = GraphBuilder(state_type=SimpleState, output_type=list[int])

@g.stream
async def generate_stream(ctx: StepContext[SimpleState, None, None]):
    """流式生成 1 到 5 的数字。"""
    for i in range(1, 6):
        yield i

@g.step
async def square(ctx: StepContext[SimpleState, None, int]) -> int:
    return ctx.inputs * ctx.inputs

collect = g.join(reduce_list_append, initial_factory=list[int])

g.add(
    g.edge_from(g.start_node).to(generate_stream),
    # stream output 是 AsyncIterable，因此可以对它 map
    g.edge_from(generate_stream).map().to(square),
    g.edge_from(square).to(collect),
    g.edge_from(collect).to(g.end_node),
)

graph = g.build()

async def main():
    result = await graph.run(state=SimpleState())
    print(sorted(result))
    #> [1, 4, 9, 16, 25]
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### Streaming Steps 如何工作 {#how-streaming-steps-work}

Streaming steps 会返回随时间 yield 值的 `AsyncIterable`。当你对 streaming step 的 output 使用 `.map()` 时，graph 会在每个 yielded value 可用时处理它，并动态创建 parallel tasks。这对以下场景尤其有用：

- 处理来自 streaming responses API 的数据
- 处理实时数据 feeds
- 渐进式处理大型数据集
- 任何希望在所有数据可用前就开始处理结果的场景

与普通 steps 一样，streaming steps 也可以有自定义 node IDs 和 labels：

```python {title="labeled_stream.py" requires="streaming_step.py"}
from pydantic_graph import StepContext

from streaming_step import SimpleState, g


@g.stream(node_id='my_stream', label='Generate numbers progressively')
async def labeled_stream(ctx: StepContext[SimpleState, None, None]):
    for i in range(10):
        yield i
```

## Edge 构建便捷方法 {#edge-building-convenience-methods}

builder 为常见 edge patterns 提供 helper methods：

### 使用 `add_edge()` 创建简单 Edges {#simple-edges-with-add_edge}

```python {title="add_edge_example.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class SimpleState:
    pass


async def main():
    g = GraphBuilder(state_type=SimpleState, output_type=int)

    @g.step
    async def step_a(ctx: StepContext[SimpleState, None, None]) -> int:
        return 10

    @g.step
    async def step_b(ctx: StepContext[SimpleState, None, int]) -> int:
        return ctx.inputs + 5

    # 使用 add_edge() 创建简单连接
    g.add_edge(g.start_node, step_a)
    g.add_edge(step_a, step_b, label='from a to b')
    g.add_edge(step_b, g.end_node)

    graph = g.build()
    result = await graph.run(state=SimpleState())
    print(result)
    #> 15
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 类型安全 {#type-safety}

graph builder API 通过 generics 提供强类型检查。[`StepContext`][pydantic_graph.step.StepContext] 上的类型参数可以确保：

- State access 具有正确类型
- Dependencies 具有正确类型
- Input/output 类型在 edges 之间匹配

```python
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class MyState:
    pass

g = GraphBuilder(state_type=MyState, output_type=str)

# 类型检查器会捕获不匹配
@g.step
async def expects_int(ctx: StepContext[MyState, None, int]) -> str:
    return str(ctx.inputs)

@g.step
async def returns_str(ctx: StepContext[MyState, None, None]) -> str:
    return 'hello'

# 这会是类型错误：expects_int 需要 int input，但 returns_str 输出 str
# g.add(g.edge_from(returns_str).to(expects_int))  # 类型错误！
```

## 后续步骤 {#next-steps}

- 了解使用 broadcasting 和 mapping 的[并行执行](parallel.md)
- 理解用于聚合并行结果的 [join nodes](joins.md)
- 探索使用 decision nodes 的[条件分支](decisions.md)
