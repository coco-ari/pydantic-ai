# Decision Nodes 决策节点 {#decision-nodes}

Decision nodes 允许你根据流经 graph 的数据类型或值进行条件分支。

## 概览 {#overview}

decision node 会评估传入数据，并基于以下条件将其路由到不同分支：

- 类型匹配（使用 `isinstance`）
- Literal 值匹配
- 自定义 predicate functions

会采用第一个匹配的 branch，类似 pattern matching 或 `if-elif-else` 链。

## 创建 Decisions {#creating-decisions}

使用 [`g.decision()`][pydantic_graph.graph_builder.GraphBuilder.decision] 创建 decision node，然后用 [`g.match()`][pydantic_graph.graph_builder.GraphBuilder.match] 添加 branches：

```python {title="simple_decision.py"}
from dataclasses import dataclass
from typing import Literal

from pydantic_graph import GraphBuilder, StepContext, TypeExpression


@dataclass
class DecisionState:
    path_taken: str | None = None


async def main():
    g = GraphBuilder(state_type=DecisionState, output_type=str)

    @g.step
    async def choose_path(ctx: StepContext[DecisionState, None, None]) -> Literal['left', 'right']:
        return 'left'

    @g.step
    async def left_path(ctx: StepContext[DecisionState, None, object]) -> str:
        ctx.state.path_taken = 'left'
        return 'Went left'

    @g.step
    async def right_path(ctx: StepContext[DecisionState, None, object]) -> str:
        ctx.state.path_taken = 'right'
        return 'Went right'

    g.add(
        g.edge_from(g.start_node).to(choose_path),
        g.edge_from(choose_path).to(
            g.decision()
            .branch(g.match(TypeExpression[Literal['left']]).to(left_path))
            .branch(g.match(TypeExpression[Literal['right']]).to(right_path))
        ),
        g.edge_from(left_path, right_path).to(g.end_node),
    )

    graph = g.build()
    state = DecisionState()
    result = await graph.run(state=state)
    print(result)
    #> Went left
    print(state.path_taken)
    #> left
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 类型匹配 {#type-matching}

使用普通 Python types 按类型匹配：

```python {title="type_matching.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext


@dataclass
class DecisionState:
    pass


async def main():
    g = GraphBuilder(state_type=DecisionState, output_type=str)

    @g.step
    async def return_int(ctx: StepContext[DecisionState, None, None]) -> int:
        return 42

    @g.step
    async def handle_int(ctx: StepContext[DecisionState, None, int]) -> str:
        return f'Got int: {ctx.inputs}'

    @g.step
    async def handle_str(ctx: StepContext[DecisionState, None, str]) -> str:
        return f'Got str: {ctx.inputs}'

    g.add(
        g.edge_from(g.start_node).to(return_int),
        g.edge_from(return_int).to(
            g.decision()
            .branch(g.match(int).to(handle_int))
            .branch(g.match(str).to(handle_str))
        ),
        g.edge_from(handle_int, handle_str).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=DecisionState())
    print(result)
    #> Got int: 42
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

### 匹配 Union Types {#matching-union-types}

对于 unions 等更复杂的 type expressions，你需要使用 [`TypeExpression`][pydantic_graph.util.TypeExpression]，因为 Python 的类型系统不允许 union types 直接作为 runtime values 使用：

```python {title="union_type_matching.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, TypeExpression


@dataclass
class DecisionState:
    pass


async def main():
    g = GraphBuilder(state_type=DecisionState, output_type=str)

    @g.step
    async def return_value(ctx: StepContext[DecisionState, None, None]) -> int | str:
        """返回 int 或 str。"""
        return 42

    @g.step
    async def handle_number(ctx: StepContext[DecisionState, None, int | float]) -> str:
        return f'Got number: {ctx.inputs}'

    @g.step
    async def handle_text(ctx: StepContext[DecisionState, None, str]) -> str:
        return f'Got text: {ctx.inputs}'

    g.add(
        g.edge_from(g.start_node).to(return_value),
        g.edge_from(return_value).to(
            g.decision()
            # 对 union types 使用 TypeExpression
            .branch(g.match(TypeExpression[int | float]).to(handle_number))
            .branch(g.match(str).to(handle_text))
        ),
        g.edge_from(handle_number, handle_text).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=DecisionState())
    print(result)
    #> Got number: 42
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

!!! note
    [`TypeExpression`][pydantic_graph.util.TypeExpression] 只在 unions（`int | str`）、`Literal` 以及其他不能作为 runtime `type` objects 的 type forms 这类复杂 type expressions 中必要。对于 `int`、`str` 或自定义 classes 这样的简单类型，可以直接传给 `g.match()`。

    [PEP 747](https://peps.python.org/pep-0747/) 中引入的 `TypeForm` 类最终应该会消除对此 workaround 的需求。


## 自定义 Matchers {#custom-matchers}

使用 `matches` 参数提供自定义匹配逻辑：

```python {title="custom_matcher.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, TypeExpression


@dataclass
class DecisionState:
    pass


async def main():
    g = GraphBuilder(state_type=DecisionState, output_type=str)

    @g.step
    async def return_number(ctx: StepContext[DecisionState, None, None]) -> int:
        return 7

    @g.step
    async def even_path(ctx: StepContext[DecisionState, None, int]) -> str:
        return f'{ctx.inputs} is even'

    @g.step
    async def odd_path(ctx: StepContext[DecisionState, None, int]) -> str:
        return f'{ctx.inputs} is odd'

    g.add(
        g.edge_from(g.start_node).to(return_number),
        g.edge_from(return_number).to(
            g.decision()
            .branch(g.match(TypeExpression[int], matches=lambda x: x % 2 == 0).to(even_path))
            .branch(g.match(TypeExpression[int], matches=lambda x: x % 2 == 1).to(odd_path))
        ),
        g.edge_from(even_path, odd_path).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=DecisionState())
    print(result)
    #> 7 is odd
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## Branch 优先级 {#branch-priority}

Branches 会按添加顺序评估。会采用第一个匹配的 branch：

```python {title="branch_priority.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, TypeExpression


@dataclass
class DecisionState:
    pass


async def main():
    g = GraphBuilder(state_type=DecisionState, output_type=str)

    @g.step
    async def return_value(ctx: StepContext[DecisionState, None, None]) -> int:
        return 10

    @g.step
    async def branch_a(ctx: StepContext[DecisionState, None, int]) -> str:
        return 'Branch A'

    @g.step
    async def branch_b(ctx: StepContext[DecisionState, None, int]) -> str:
        return 'Branch B'

    g.add(
        g.edge_from(g.start_node).to(return_value),
        g.edge_from(return_value).to(
            g.decision()
            .branch(g.match(TypeExpression[int], matches=lambda x: x >= 5).to(branch_a))
            .branch(g.match(TypeExpression[int], matches=lambda x: x >= 0).to(branch_b))
        ),
        g.edge_from(branch_a, branch_b).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=DecisionState())
    print(result)
    #> Branch A
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

两个 branches 都可以匹配 `10`，但 Branch A 在前，因此会采用它。

## Catch-All Branches（兜底分支） {#catch-all-branches}

使用 `object` 或 `Any` 创建 catch-all branch：

```python {title="catch_all.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, TypeExpression


@dataclass
class DecisionState:
    pass


async def main():
    g = GraphBuilder(state_type=DecisionState, output_type=str)

    @g.step
    async def return_value(ctx: StepContext[DecisionState, None, None]) -> int:
        return 100

    @g.step
    async def catch_all(ctx: StepContext[DecisionState, None, object]) -> str:
        return f'Caught: {ctx.inputs}'

    g.add(
        g.edge_from(g.start_node).to(return_value),
        g.edge_from(return_value).to(g.decision().branch(g.match(TypeExpression[object]).to(catch_all))),
        g.edge_from(catch_all).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=DecisionState())
    print(result)
    #> Caught: 100
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 嵌套 Decisions {#nested-decisions}

Decisions 可以嵌套，以表达复杂条件逻辑：

```python {title="nested_decisions.py"}
from dataclasses import dataclass

from pydantic_graph import GraphBuilder, StepContext, TypeExpression


@dataclass
class DecisionState:
    pass


async def main():
    g = GraphBuilder(state_type=DecisionState, output_type=str)

    @g.step
    async def get_number(ctx: StepContext[DecisionState, None, None]) -> int:
        return 15

    @g.step
    async def is_positive(ctx: StepContext[DecisionState, None, int]) -> int:
        return ctx.inputs

    @g.step
    async def is_negative(ctx: StepContext[DecisionState, None, int]) -> str:
        return 'Negative'

    @g.step
    async def small_positive(ctx: StepContext[DecisionState, None, int]) -> str:
        return 'Small positive'

    @g.step
    async def large_positive(ctx: StepContext[DecisionState, None, int]) -> str:
        return 'Large positive'

    g.add(
        g.edge_from(g.start_node).to(get_number),
        g.edge_from(get_number).to(
            g.decision()
            .branch(g.match(TypeExpression[int], matches=lambda x: x > 0).to(is_positive))
            .branch(g.match(TypeExpression[int], matches=lambda x: x <= 0).to(is_negative))
        ),
        g.edge_from(is_positive).to(
            g.decision()
            .branch(g.match(TypeExpression[int], matches=lambda x: x < 10).to(small_positive))
            .branch(g.match(TypeExpression[int], matches=lambda x: x >= 10).to(large_positive))
        ),
        g.edge_from(is_negative, small_positive, large_positive).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=DecisionState())
    print(result)
    #> Large positive
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 使用 Labels 的分支 {#branching-with-labels}

为 branches 添加 labels，用于文档和 diagram generation：

```python {title="labeled_branches.py"}
from dataclasses import dataclass
from typing import Literal

from pydantic_graph import GraphBuilder, StepContext, TypeExpression


@dataclass
class DecisionState:
    pass


async def main():
    g = GraphBuilder(state_type=DecisionState, output_type=str)

    @g.step
    async def choose(ctx: StepContext[DecisionState, None, None]) -> Literal['a', 'b']:
        return 'a'

    @g.step
    async def path_a(ctx: StepContext[DecisionState, None, object]) -> str:
        return 'Path A'

    @g.step
    async def path_b(ctx: StepContext[DecisionState, None, object]) -> str:
        return 'Path B'

    g.add(
        g.edge_from(g.start_node).to(choose),
        g.edge_from(choose).to(
            g.decision()
            .branch(g.match(TypeExpression[Literal['a']]).label('Take path A').to(path_a))
            .branch(g.match(TypeExpression[Literal['b']]).label('Take path B').to(path_b))
        ),
        g.edge_from(path_a, path_b).to(g.end_node),
    )

    graph = g.build()
    result = await graph.run(state=DecisionState())
    print(result)
    #> Path A
```

_（此示例是完整的，可以"原样"运行；你需要添加 `import asyncio; asyncio.run(main())` 来运行 `main`）_

## 后续步骤 {#next-steps}

- 了解使用 broadcasting 和 mapping 的[并行执行](parallel.md)
- 理解用于聚合并行结果的 [join nodes](joins.md)
- 查看 [API reference][pydantic_graph.decision] 获取完整 decision 文档
