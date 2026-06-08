# Graph Builder API {#graph-builder-api}

graph builder API 提供了强大的 builder pattern，用于构建并行执行图。原始的基于 [`BaseNode`][pydantic_graph.basenode.BaseNode] 的 graph API 仍然可用（并且可与 builder API 互操作），其文档位于[主 graph 文档](../../graph.md)。

## 概览 {#overview}

`pydantic-graph` 中的 graph builder API 提供：

- **Step nodes**：用于执行 async functions
- **Decision nodes**：用于条件分支
- **Spread operations**：用于并行处理 iterables
- **Broadcast operations**：用于将相同数据发送到多个并行路径
- **Join nodes and Reducers**：用于聚合并行执行结果

该 API 面向高级 workflows 设计，适合需要声明式控制并行性、路由和数据聚合的场景。

## 安装 {#installation}

graph builder API 随 `pydantic-graph` 提供：

```bash
pip install pydantic-graph
```

也作为 `pydantic-ai` 的一部分提供：

```bash
pip install pydantic-ai
```

## 快速开始 {#quick-start}

下面是一个帮助你入门的简单示例：

```python {title="simple_counter.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class CounterState:
    """State for tracking a counter value."""

    value: int = 0


async def main():
    # 创建带 state 和 output types 的 graph builder
    g = GraphBuilder(state_type=CounterState, output_type=int)

    # 使用装饰器定义 steps
    @g.step
    async def increment(ctx: StepContext[CounterState, None, None]) -> int:
        """Increment the counter and return its value."""
        ctx.state.value += 1
        return ctx.state.value

    @g.step
    async def double_it(ctx: StepContext[CounterState, None, int]) -> int:
        """Double the input value."""
        return ctx.inputs * 2

    # 添加连接 nodes 的 edges
    g.add(
        g.edge_from(g.start_node).to(increment),
        g.edge_from(increment).to(double_it),
        g.edge_from(double_it).to(g.end_node),
    )

    # 构建并运行 graph
    graph = g.build()
    state = CounterState()
    result = await graph.run(state=state)
    print(f'Result: {result}')
    #> Result: 2
    print(f'Final state: {state.value}')
    #> Final state: 1
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 核心概念 {#key-concepts}

### GraphBuilder {#graphbuilder}

[`GraphBuilder`][pydantic_graph.graph_builder.GraphBuilder] 是构建 graphs 的主要入口。它对以下类型泛型化：

- `StateT` - 所有 nodes 共享的 mutable state 类型
- `DepsT` - 注入到 nodes 中的 dependencies 类型
- `InputT` - graph 的 initial input 类型
- `OutputT` - graph 的 final output 类型

### Steps {#steps}

Steps 是用 [`@g.step`][pydantic_graph.graph_builder.GraphBuilder.step] 装饰的 async functions，用于定义每个 node 中要完成的实际工作。它们会接收 [`StepContext`][pydantic_graph.step.StepContext]，可访问：

- `ctx.state` - mutable graph state
- `ctx.deps` - 注入的 dependencies
- `ctx.inputs` - 此 step 的 input data

### Edges {#edges}

Edges 定义 nodes 之间的连接。builder 提供多种创建 edges 的方式：

- [`g.add()`][pydantic_graph.graph_builder.GraphBuilder.add] - 添加一个或多个 edge paths
- [`g.add_edge()`][pydantic_graph.graph_builder.GraphBuilder.add_edge] - 在两个 nodes 之间添加简单 edge
- [`g.edge_from()`][pydantic_graph.graph_builder.GraphBuilder.edge_from] - 开始构建复杂 edge path

### Start 和 End Nodes {#start-and-end-nodes}

每个 graph 都有：

- [`g.start_node`][pydantic_graph.graph_builder.GraphBuilder.start_node] - 接收 initial inputs 的入口点
- [`g.end_node`][pydantic_graph.graph_builder.GraphBuilder.end_node] - 产生 final outputs 的出口点

## 更复杂的示例 {#a-more-complex-example}

下面的示例展示如何用 map operation 进行并行执行：

```python {title="parallel_processing.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, reduce_list_append


@dataclass
class ProcessingState:
    """State for tracking processing metrics."""

    items_processed: int = 0


async def main():
    g = GraphBuilder(
        state_type=ProcessingState,
        input_type=list[int],
        output_type=list[int],
    )

    @g.step
    async def square(ctx: StepContext[ProcessingState, None, int]) -> int:
        """Square a number and track that we processed it."""
        ctx.state.items_processed += 1
        return ctx.inputs * ctx.inputs

    # 创建 join 以收集结果
    collect_results = g.join(reduce_list_append, initial_factory=list[int])

    # 使用 map operation 构建 graph
    g.add(
        g.edge_from(g.start_node).map().to(square),
        g.edge_from(square).to(collect_results),
        g.edge_from(collect_results).to(g.end_node),
    )

    graph = g.build()
    state = ProcessingState()
    result = await graph.run(state=state, inputs=[1, 2, 3, 4, 5])

    print(f'Results: {sorted(result)}')
    #> Results: [1, 4, 9, 16, 25]
    print(f'Items processed: {state.items_processed}')
    #> Items processed: 5
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

在此示例中：

1. start node 接收整数列表
2. `.map()` operation 将每个 item fan out 到单独的 `square` step 并行执行
3. 所有结果使用 [`reduce_list_append`][pydantic_graph.join.reduce_list_append] 收集回来
4. joined results 流向 end node

## 后续步骤 {#next-steps}

继续阅读各功能的详细文档：

- [**Steps**](steps.md) - 了解 step nodes 和 execution contexts
- [**Joins**](joins.md) - 理解 join nodes 和 reducer patterns
- [**Decisions**](decisions.md) - 实现条件分支
- [**Parallel Execution**](parallel.md) - 掌握 broadcasting 和 mapping

## 高级执行控制 {#advanced-execution-control}

除了基本的 [`graph.run()`][pydantic_graph.graph_builder.Graph.run] 方法，builder API 还提供对 graph execution 的细粒度控制。

### 逐步执行 {#step-by-step-execution}

使用 [`graph.iter()`][pydantic_graph.graph_builder.Graph.iter] 一次执行 graph 的一个 step：

```python {title="step_by_step.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class CounterState:
    value: int = 0


async def main():
    g = GraphBuilder(state_type=CounterState, output_type=int)

    @g.step
    async def increment(ctx: StepContext[CounterState, None, None]) -> int:
        ctx.state.value += 1
        return ctx.state.value

    @g.step
    async def double_it(ctx: StepContext[CounterState, None, int]) -> int:
        return ctx.inputs * 2

    g.add(
        g.edge_from(g.start_node).to(increment),
        g.edge_from(increment).to(double_it),
        g.edge_from(double_it).to(g.end_node),
    )

    graph = g.build()
    state = CounterState()

    # 使用 iter() 进行逐步执行
    async with graph.iter(state=state) as graph_run:
        print(f'Initial state: {state.value}')
        #> Initial state: 0

        # 逐步推进执行
        async for event in graph_run:
            print(f'{state.value=} | {event=}')
            #> state.value=0 | event=[GraphTask(node_id='increment', inputs=None)]
            #> state.value=1 | event=[GraphTask(node_id='double_it', inputs=1)]
            #> state.value=1 | event=[GraphTask(node_id='__end__', inputs=2)]
            #> state.value=1 | event=EndMarker(_value=2)
            if graph_run.output is not None:
                print(f'Final output: {graph_run.output}')
                #> Final output: 2
                break
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

[`GraphRun`][pydantic_graph.graph_builder.GraphRun] 对象提供：

- **Async iteration**：迭代 execution events
- **`next_task` property**：检查即将执行的 tasks
- **`output` property**：检查 graph 是否已完成并获取 final output
- **`next()` method**：手动推进执行，并可选择注入值

### 可视化 Graphs {#visualizing-graphs #mermaid-diagrams}

使用 [`graph.render()`][pydantic_graph.graph_builder.Graph.render] 生成 graph 结构的 Mermaid diagrams：

```python {title="visualize_graph.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class SimpleState:
    pass


g = GraphBuilder(state_type=SimpleState, output_type=str)

@g.step
async def step_a(ctx: StepContext[SimpleState, None, None]) -> int:
    return 10

@g.step
async def step_b(ctx: StepContext[SimpleState, None, int]) -> str:
    return f'Result: {ctx.inputs}'

g.add(
    g.edge_from(g.start_node).to(step_a),
    g.edge_from(step_a).to(step_b),
    g.edge_from(step_b).to(g.end_node),
)

graph = g.build()

# 生成 Mermaid diagram
mermaid_diagram = graph.render(title='My Graph', direction='LR')
print(mermaid_diagram)
"""
---
title: My Graph
---
stateDiagram-v2
  direction LR
  step_a
  step_b

  [*] --> step_a
  step_a --> step_b
  step_b --> [*]
"""
```

渲染后的 diagram 可以显示在文档、notebooks 或任何支持 Mermaid syntax 的工具中。

## 与原始 API 对比 {#comparison-with-original-api}

原始 graph API（记录在[主 graph 页面](../../graph.md)）使用基于 [`BaseNode`][pydantic_graph.basenode.BaseNode] 子类的 class-based approach。builder API 使用带装饰函数的 builder pattern，提供：

**优势：**

- 简单 workflows 的语法更简洁
- 通过 map/broadcast 显式控制并行性
- 为常见聚合模式提供 native reducers
- 更容易可视化复杂数据流

**权衡：**

- 需要理解 builder patterns
- 面向对象程度较低，更偏函数式风格

两个 APIs 都得到完整支持，并且在需要时甚至可以集成在一起。

## 持久化和可恢复性 {#persistence-and-resumability}

!!! info "没有原生持久化"
    不同于[原始 Graph API](../../graph.md#state-persistence)，graph builder API 不包含内置 state persistence。这是因为[在并行执行中实现一致 snapshotting 很复杂](https://github.com/pydantic/pydantic-ai/issues/530#issuecomment-3504609992)。

对于需要在失败、重启或长时间运行操作期间保留进度的 workflows，请使用支持的[持久化执行](../../durable_execution/overview.md)方案之一。
