# Pydantic Graph

[![CI](https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml/badge.svg?event=push)](https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml?query=branch%3Amain)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic-ai.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/pydantic/pydantic-ai)
[![PyPI](https://img.shields.io/pypi/v/pydantic-graph.svg)](https://pypi.python.org/pypi/pydantic-graph)
[![python versions](https://img.shields.io/pypi/pyversions/pydantic-graph.svg)](https://github.com/pydantic/pydantic-ai)
[![license](https://img.shields.io/github/license/pydantic/pydantic-ai.svg)](https://github.com/pydantic/pydantic-ai/blob/main/LICENSE)

图和有限状态机库。

这个库作为 [Pydantic AI](https://ai.pydantic.dev) 的一部分开发，但它不依赖 `pydantic-ai` 或相关包，也可以视为一个纯粹的基于图的状态机库。无论你是否使用 Pydantic AI，甚至是否在构建 GenAI 应用，它都可能对你有用。

和 Pydantic AI 一样，这个库优先考虑类型安全和常见 Python 语法的使用，而不是晦涩、领域特定的 Python 语法用法。

`pydantic-graph` 允许你使用标准 Python 语法定义图。具体来说，边是通过节点的返回类型提示定义的。

完整文档见 [ai.pydantic.dev/graph](https://ai.pydantic.dev/graph)。

下面是一个基础示例：

```python {noqa="I001"}
from __future__ import annotations

from dataclasses import dataclass

from pydantic_graph import BaseNode, End, GraphBuilder, GraphRunContext, StepContext


@dataclass
class DivisibleBy5(BaseNode[None, None, int]):
    foo: int

    async def run(
        self,
        ctx: GraphRunContext,
    ) -> Increment | End[int]:
        if self.foo % 5 == 0:
            return End(self.foo)
        else:
            return Increment(self.foo)


@dataclass
class Increment(BaseNode):
    foo: int

    async def run(self, ctx: GraphRunContext) -> DivisibleBy5:
        return DivisibleBy5(self.foo + 1)


g = GraphBuilder(input_type=int, output_type=int)


@g.step
async def start(ctx: StepContext[None, None, int]) -> DivisibleBy5:
    return DivisibleBy5(ctx.inputs)


g.add(
    g.node(DivisibleBy5),
    g.node(Increment),
    g.edge_from(g.start_node).to(start),
)

fives_graph = g.build()


async def main():
    result = await fives_graph.run(inputs=4)
    print(result)
    #> 5
```
