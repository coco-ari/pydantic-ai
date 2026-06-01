<div align="center">
  <a href="https://ai.pydantic.dev/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://pydantic.dev/docs/ai/img/pydantic-ai-dark.svg">
      <img src="https://pydantic.dev/docs/ai/img/pydantic-ai-light.svg" alt="Pydantic AI">
    </picture>
  </a>
</div>
<div align="center">
  <h3>GenAI Agent Framework, the Pydantic way</h3>
</div>
<div align="center">
  <a href="https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml?query=branch%3Amain"><img src="https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml/badge.svg?event=push" alt="CI"></a>
  <a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/pydantic/pydantic-ai"><img src="https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic-ai.svg" alt="Coverage"></a>
  <a href="https://pypi.python.org/pypi/pydantic-ai"><img src="https://img.shields.io/pypi/v/pydantic-ai.svg" alt="PyPI"></a>
  <a href="https://github.com/pydantic/pydantic-ai"><img src="https://img.shields.io/pypi/pyversions/pydantic-ai.svg" alt="versions"></a>
  <a href="https://github.com/pydantic/pydantic-ai/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pydantic/pydantic-ai.svg?v" alt="license"></a>
  <a href="https://logfire.pydantic.dev/docs/join-slack/"><img src="https://img.shields.io/badge/Slack-Join%20Slack-4A154B?logo=slack" alt="Join Slack" /></a>
</div>

---

**文档**：[ai.pydantic.dev](https://ai.pydantic.dev/)

---

### <em>Pydantic AI 是一个 Python 智能体框架，旨在帮助你快速、自信、轻松地使用生成式 AI 构建生产级应用和工作流。</em>


FastAPI 基于 [Pydantic Validation](https://docs.pydantic.dev) 和类型提示等现代 Python 特性，以创新且符合人体工程学的设计革新了 Web 开发。

然而，尽管几乎每个 Python 智能体框架和 LLM 库都在使用 Pydantic Validation，当我们开始在 [Pydantic Logfire](https://pydantic.dev/logfire) 中使用 LLM 时，却找不到任何一个能带来同样体验的工具。

我们构建 Pydantic AI 的目标很简单：把那种 FastAPI 式的体验带到 GenAI 应用和智能体开发中。

## 为什么使用 Pydantic AI

1. **由 Pydantic 团队构建**：
[Pydantic Validation](https://docs.pydantic.dev/latest/) 是 OpenAI SDK、Google ADK、Anthropic SDK、LangChain、LlamaIndex、AutoGPT、Transformers、CrewAI、Instructor 以及更多项目的校验层。_既然可以直达源头，为什么还要用衍生品呢？_ :smiley:

2. **模型无关**：
支持几乎所有[模型](https://ai.pydantic.dev/models/overview)和提供商：OpenAI、Anthropic、Gemini、DeepSeek、Grok、Cohere、Mistral 和 Perplexity；Azure AI Foundry、Amazon Bedrock、Google Cloud、Ollama、LiteLLM、Groq、OpenRouter、Together AI、Fireworks AI、Cerebras、Hugging Face、GitHub、Heroku、Vercel、Nebius、OVHcloud、Alibaba Cloud 和 SambaNova。如果你喜欢的模型或提供商不在列表中，也可以轻松实现[自定义模型](https://ai.pydantic.dev/models/overview#custom-models)。

3. **无缝可观测性**：
与我们的通用 OpenTelemetry 可观测性平台 [Pydantic Logfire](https://pydantic.dev/logfire) 深度[集成](https://ai.pydantic.dev/logfire)，支持实时调试、基于评估的性能监控，以及行为、追踪和成本跟踪。如果你已经有支持 OTel 的可观测性平台，也可以[继续使用它](https://ai.pydantic.dev/logfire#alternative-observability-backends)。

4. **完全类型安全**：
设计目标是尽可能为你的 IDE 或 AI 编码智能体提供上下文，用于自动补全和[类型检查](https://ai.pydantic.dev/agents#static-type-checking)，把整类错误从运行时提前到编写代码时发现，带来一点 Rust 中“能编译就能运行”的体验。

5. **强大的评估能力**：
让你能够系统地测试和[评估](https://ai.pydantic.dev/evals)所构建智能体系统的性能和准确性，并在 Pydantic Logfire 中持续监控性能变化。

6. **为可扩展性而设计**：
使用可组合的[能力](https://ai.pydantic.dev/capabilities)构建智能体，这些能力会把工具、钩子、指令和模型设置打包成可复用单元。你可以使用内置的[网页搜索](https://ai.pydantic.dev/capabilities#provider-adaptive-tools)、[思考](https://ai.pydantic.dev/capabilities#thinking)和 [MCP](https://ai.pydantic.dev/capabilities#provider-adaptive-tools) 能力，从 [Pydantic AI Harness](https://ai.pydantic.dev/harness/overview) 能力库中选择，构建自己的能力，或安装[第三方能力包](https://ai.pydantic.dev/extensibility)。还可以完全通过 [YAML/JSON](https://ai.pydantic.dev/agent-spec) 定义智能体，不需要写代码。

7. **MCP、A2A 和 UI**：
集成 [Model Context Protocol](https://ai.pydantic.dev/mcp/overview)、[Agent2Agent](https://ai.pydantic.dev/a2a) 和多种 [UI 事件流](https://ai.pydantic.dev/ui/overview)标准，让你的智能体可以访问外部工具和数据，与其他智能体互操作，并通过基于事件的流式通信构建交互式应用。

8. **人在回路中的工具审批**：
可以轻松标记某些工具调用在继续执行前[需要审批](https://ai.pydantic.dev/deferred-tools#human-in-the-loop-tool-approval)，审批条件还可以取决于工具调用参数、对话历史或用户偏好。

9. **持久化执行**：
让你能够构建[持久化智能体](https://ai.pydantic.dev/durable_execution/overview/)，在短暂的 API 故障、应用错误或重启后保留执行进度，并以生产级可靠性处理长时间运行、异步以及人在回路中的工作流。

10. **流式输出**：
支持持续[流式传输](https://ai.pydantic.dev/output#streamed-results)结构化输出，并立即进行校验，确保可以实时访问生成的数据。

11. **图支持**：
提供一种基于类型提示定义[图](https://ai.pydantic.dev/graph)的强大方式，适用于标准控制流可能退化成意大利面代码的复杂应用。

不过现实地说，再多列表也不如[亲自试一试](#下一步)，看看它带给你的感觉！

## Hello World 示例

下面是一个最小化的 Pydantic AI 示例：

```python
from pydantic_ai import Agent

# 定义一个非常简单的智能体，包括要使用的模型；你也可以在运行智能体时再设置模型。
agent = Agent(
    'anthropic:claude-sonnet-4-6',
    # 使用智能体的关键字参数注册静态指令。
    # 如果需要更复杂的动态生成指令，请参见下面的示例。
    instructions='Be concise, reply with one sentence.',
)

# 同步运行智能体，与 LLM 进行一次对话。
result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

_（这个示例是完整的；假设你已经[安装了 `pydantic_ai` 包](https://ai.pydantic.dev/install)，它可以“原样”运行。）_

这次交互会非常短：Pydantic AI 会把指令和用户提示发送给 LLM，模型会返回一段文本响应。

目前还不算很有趣，但我们可以轻松添加[工具](https://ai.pydantic.dev/tools)、[动态指令](https://ai.pydantic.dev/agents#instructions)、[结构化输出](https://ai.pydantic.dev/output)，或者可组合的[能力](https://ai.pydantic.dev/capabilities)，来构建更强大的智能体。

下面是同一个智能体，增加了[思考](https://ai.pydantic.dev/capabilities#thinking)和[网页搜索](https://ai.pydantic.dev/capabilities#provider-adaptive-tools)能力：

```python
from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking, WebSearch

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    instructions='Be concise, reply with one sentence.',
    capabilities=[Thinking(), WebSearch()],
)

result = agent.run_sync('What was the mass of the largest meteorite found this year?')
print(result.output)
```

## 工具和依赖注入示例

下面是一个使用 Pydantic AI 为银行构建支持智能体的简洁示例：

**（[文档中](https://ai.pydantic.dev/#tools-dependency-injection-example)有更完善的示例说明。）**

```python
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn


# SupportDependencies 用于把数据、连接和逻辑传入模型；
# 这些内容会在运行指令和工具函数时用到。
# 依赖注入提供了一种类型安全的方式来自定义智能体行为。
@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn


# 这个 Pydantic 模型定义了智能体返回输出的结构。
class SupportOutput(BaseModel):
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description="Whether to block the customer's card")
    risk: int = Field(description='Risk level of query', ge=0, le=10)


# 这个智能体会充当银行的一线支持。
# 智能体会根据它接受的依赖类型和返回的输出类型进行泛型化。
# 在这个例子中，支持智能体的类型是 `Agent[SupportDependencies, SupportOutput]`。
support_agent = Agent(
    'openai:gpt-5.2',
    deps_type=SupportDependencies,
    # 智能体的响应会被保证为 SupportOutput；
    # 如果校验失败，智能体会被提示再次尝试。
    output_type=SupportOutput,
    instructions=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)


# 动态指令可以使用依赖注入。
# 依赖通过 `RunContext` 参数传递，该参数使用上面的 `deps_type` 进行参数化。
# 如果这里的类型注解写错，静态类型检查器会捕获到。
@support_agent.instructions
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"


# `tool` 装饰器允许你注册 LLM 在响应用户时可以调用的函数。
# 同样，依赖通过 `RunContext` 传递，其他参数会成为传给 LLM 的工具 schema。
# Pydantic 会用于校验这些参数，错误会被传回给 LLM，以便它重试。
@support_agent.tool
async def customer_balance(
        ctx: RunContext[SupportDependencies], include_pending: bool
) -> float:
    """Returns the customer's current account balance."""
    # 工具的 docstring 也会作为工具描述传给 LLM。
    # 参数描述会从 docstring 中提取，并添加到发送给 LLM 的参数 schema 中。
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )
    return balance


...  # 在真实用例中，你会添加更多工具和更长的系统提示


async def main():
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    # 异步运行智能体，与 LLM 进行对话，直到得到最终响应。
    # 即使在这个相当简单的例子中，智能体也会随着工具调用交换多条 LLM 消息，以检索输出。
    result = await support_agent.run('What is my balance?', deps=deps)
    # `result.output` 会通过 Pydantic 校验，以保证它是 `SupportOutput`。
    # 因为智能体是泛型的，所以它也会被标注为 `SupportOutput`，以帮助静态类型检查。
    print(result.output)
    """
    support_advice='Hello John, your current account balance, including pending transactions, is $123.45.' block_card=False risk=1
    """

    result = await support_agent.run('I just lost my card!', deps=deps)
    print(result.output)
    """
    support_advice="I'm sorry to hear that, John. We are temporarily blocking your card to prevent unauthorized transactions." block_card=True risk=8
    """
```

## 下一步

要亲自尝试 Pydantic AI，请先[安装它](https://ai.pydantic.dev/install)，然后按照[示例中的说明](https://ai.pydantic.dev/examples/setup)操作。

阅读[文档](https://ai.pydantic.dev/agents/)，了解更多关于使用 Pydantic AI 构建应用的信息。

阅读 [API 参考](https://ai.pydantic.dev/api/agent/)，了解 Pydantic AI 的接口。

如果你有任何问题，可以加入 [Slack](https://logfire.pydantic.dev/docs/join-slack/) 或在 [GitHub](https://github.com/pydantic/pydantic-ai/issues) 上提交 issue。
