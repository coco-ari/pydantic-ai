---
title: Pydantic AI
---

# Pydantic AI {.hide}

--8<-- "docs/.partials/index-header.html"

FastAPI 基于 [Pydantic Validation](https://docs.pydantic.dev) 和类型提示等现代 Python 特性，以创新且符合人体工程学的设计革新了 Web 开发。

然而，尽管几乎每个 Python 智能体框架和 LLM 库都在使用 Pydantic Validation，当我们开始在 [Pydantic Logfire](https://pydantic.dev/logfire) 中使用 LLM 时，却找不到任何一个能带来同样体验的工具。

我们构建 Pydantic AI 的目标很简单：把那种 FastAPI 式的体验带到 GenAI 应用和智能体开发中。

## 为什么使用 Pydantic AI

1. **由 Pydantic 团队构建**：
[Pydantic Validation](https://docs.pydantic.dev/latest/) 是 OpenAI SDK、Google ADK、Anthropic SDK、LangChain、LlamaIndex、AutoGPT、Transformers、CrewAI、Instructor 以及更多项目的校验层。_既然可以直达源头，为什么还要用衍生品呢？_ :smiley:

2. **模型无关**：
支持几乎所有[模型](models/overview.md)和提供商：OpenAI、Anthropic、Gemini、DeepSeek、Grok、Cohere、Mistral 和 Perplexity；Azure AI Foundry、Amazon Bedrock、Google Cloud、Ollama、LiteLLM、Groq、OpenRouter、Together AI、Fireworks AI、Cerebras、Hugging Face、GitHub、Heroku、Vercel、Nebius、OVHcloud、Alibaba Cloud 和 SambaNova。如果你喜欢的模型或提供商不在列表中，也可以轻松实现[自定义模型](models/overview.md#custom-models)。

3. **无缝可观测性**：
与我们的通用 OpenTelemetry 可观测性平台 [Pydantic Logfire](https://pydantic.dev/logfire) 深度[集成](logfire.md)，支持实时调试、基于评估的性能监控，以及行为、追踪和成本跟踪。如果你已经有支持 OTel 的可观测性平台，也可以[继续使用它](logfire.md#alternative-observability-backends)。

4. **完全类型安全**：
设计目标是尽可能为你的 IDE 或 AI 编码智能体提供上下文，用于自动补全和[类型检查](agent.md#static-type-checking)，把整类错误从运行时提前到编写代码时发现，带来一点 Rust 中“能编译就能运行”的体验。

5. **强大的评估能力**：
让你能够系统地测试和[评估](evals.md)所构建智能体系统的性能和准确性，并在 Pydantic Logfire 中持续监控性能变化。

6. **为可扩展性而设计**：
使用可组合的[能力](capabilities.md)构建智能体，这些能力会把工具、钩子、指令和模型设置打包成可复用单元。你可以使用内置的[网页搜索](capabilities.md#provider-adaptive-tools)、[思考](capabilities.md#thinking)和 [MCP](capabilities.md#provider-adaptive-tools) 能力，从 [Pydantic AI Harness](harness/overview.md) 能力库中选择，构建自己的能力，或安装[第三方能力包](extensibility.md)。还可以完全通过 [YAML/JSON](agent-spec.md) 定义智能体，不需要写代码。

7. **MCP、A2A 和 UI**：
集成 [Model Context Protocol](mcp/overview.md)、[Agent2Agent](a2a.md) 和多种 [UI 事件流](ui/overview.md)标准，让你的智能体可以访问外部工具和数据，与其他智能体互操作，并通过基于事件的流式通信构建交互式应用。

8. **人在回路中的工具审批**：
可以轻松标记某些工具调用在继续执行前[需要审批](deferred-tools.md#human-in-the-loop-tool-approval)，审批条件还可以取决于工具调用参数、对话历史或用户偏好。

9. **持久化执行**：
让你能够构建[持久化智能体](durable_execution/overview.md)，在短暂的 API 故障、应用错误或重启后保留执行进度，并以生产级可靠性处理长时间运行、异步以及人在回路中的工作流。

10. **流式输出**：
支持持续[流式传输](output.md#streamed-results)结构化输出，并立即进行校验，确保可以实时访问生成的数据。

11. **图支持**：
提供一种基于类型提示定义[图](graph.md)的强大方式，适用于标准控制流可能退化成意大利面代码的复杂应用。

不过现实地说，再多列表也不如[亲自试一试](#下一步)，看看它带给你的感觉！

**订阅我们的 newsletter _The Pydantic Stack_，获取 Pydantic AI、Logfire 和 Pydantic 的更新与教程：**

  <form method="POST" action="https://eu.customerioforms.com/forms/submit_action?site_id=53d2086c3c4214eaecaa&form_id=14b22611745b458&success_url=https://ai.pydantic.dev/" class="md-typeset" style="display: flex; align-items: center; gap: 0.5rem; width: 100%;">
      <input
      type="email"
      id="email_input"
      name="email"
      class="md-input md-input--stretch"
      style="flex: 1; background: var(--md-default-bg-color); color: var(--md-default-fg-color);"
      required
      placeholder="Email"
      data-1p-ignore
      data-lpignore="true"
      data-protonpass-ignore="true"
      data-bwignore="true"
      />
      <input type="hidden" id="source_input" name="source" value="pydantic-ai" />
      <button type="submit" class="md-button md-button--primary">Subscribe</button>
  </form>

## Hello World 示例

下面是一个最小化的 Pydantic AI 示例：

```python {title="hello_world.py"}
from pydantic_ai import Agent

agent = Agent(  # (1)!
    'anthropic:claude-sonnet-4-6',
    instructions='Be concise, reply with one sentence.',  # (2)!
)

result = agent.run_sync('Where does "hello world" come from?')  # (3)!
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

1. 我们将智能体配置为使用 [Anthropic 的 Claude Sonnet 4.6](api/models/anthropic.md) 模型，但你也可以在运行智能体时设置模型。
2. 使用智能体的关键字参数注册静态[指令](agent.md#instructions)。
3. 同步[运行智能体](agent.md#running-agents)，开始与 LLM 对话。

_（这个示例是完整的；假设你已经[安装了 `pydantic_ai` 包](install.md)，它可以“原样”运行。）_

这次交互会非常短：Pydantic AI 会把指令和用户提示发送给 LLM，模型会返回一段文本响应。

目前还不算很有趣，但我们可以轻松添加[工具](tools.md)、[动态指令](agent.md#instructions)、[结构化输出](output.md)，或者可组合的[能力](capabilities.md)，来构建更强大的智能体。

下面是同一个智能体，增加了[思考](capabilities.md#thinking)和[网页搜索](capabilities.md#provider-adaptive-tools)能力：

```python {title="hello_world_capabilities.py"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking, WebSearch

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    instructions='Be concise, reply with one sentence.',
    capabilities=[Thinking(), WebSearch(local='duckduckgo')],
)

result = agent.run_sync('What was the mass of the largest meteorite found this year?')
print(result.output)
"""
The largest meteorite recovered this year weighed approximately 7.6 kg, found in the Sahara Desert in January.
"""
```

## 工具和依赖注入示例

下面是一个使用 Pydantic AI 为银行构建支持智能体的简洁示例：

```python {title="bank_support.py"}
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn


@dataclass
class SupportDependencies:  # (3)!
    customer_id: int
    db: DatabaseConn  # (12)!


class SupportOutput(BaseModel):  # (13)!
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description="Whether to block the customer's card")
    risk: int = Field(description='Risk level of query', ge=0, le=10)


support_agent = Agent(  # (1)!
    'openai:gpt-5.2',  # (2)!
    deps_type=SupportDependencies,
    output_type=SupportOutput,  # (9)!
    instructions=(  # (4)!
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)


@support_agent.instructions  # (5)!
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"


@support_agent.tool  # (6)!
async def customer_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool
) -> float:
    """Returns the customer's current account balance."""  # (7)!
    return await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )


...  # (11)!


async def main():
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    result = await support_agent.run('What is my balance?', deps=deps)  # (8)!
    print(result.output)  # (10)!
    """
    support_advice='Hello John, your current account balance, including pending transactions, is $123.45.' block_card=False risk=1
    """

    result = await support_agent.run('I just lost my card!', deps=deps)
    print(result.output)
    """
    support_advice="I'm sorry to hear that, John. We are temporarily blocking your card to prevent unauthorized transactions." block_card=True risk=8
    """
```

1. 这个[智能体](agent.md)会充当银行的一线支持。智能体会根据它接受的依赖类型和返回的输出类型进行泛型化。在这个例子中，支持智能体的类型是 `#!python Agent[SupportDependencies, SupportOutput]`。
2. 这里我们将智能体配置为使用 [OpenAI 的 GPT-5 模型](api/models/openai.md)；你也可以在运行智能体时设置模型。
3. `SupportDependencies` dataclass 用于把运行[指令](agent.md#instructions)和[工具](tools.md)函数时需要的数据、连接和逻辑传入模型。Pydantic AI 的依赖注入系统提供了一种[类型安全](agent.md#static-type-checking)的方式来自定义智能体行为，并且在运行[单元测试](testing.md)和 evals 时尤其有用。
4. 静态[指令](agent.md#instructions)可以通过 [`instructions` 关键字参数][pydantic_ai.agent.Agent.__init__]注册到智能体。
5. 动态[指令](agent.md#instructions)可以通过 [`@agent.instructions`][pydantic_ai.agent.Agent.instructions] 装饰器注册，并且可以使用依赖注入。依赖通过 [`RunContext`][pydantic_ai.tools.RunContext] 参数传递，该参数使用上面的 `deps_type` 进行参数化。如果这里的类型注解错误，静态类型检查器会捕获它。
6. [`@agent.tool`](tools.md) 装饰器允许你注册 LLM 在响应用户时可以调用的函数。同样，依赖通过 [`RunContext`][pydantic_ai.tools.RunContext] 传递，其他参数会成为传给 LLM 的工具 schema。Pydantic 会校验这些参数，错误会被传回给 LLM，以便它重试。
7. 工具的 docstring 也会作为工具描述传给 LLM。参数描述会从 docstring 中[提取](tools.md#function-tools-and-schema)，并添加到发送给 LLM 的参数 schema 中。
8. 异步[运行智能体](agent.md#running-agents)，与 LLM 进行对话，直到得到最终响应。即使在这个相当简单的例子中，智能体也会随着工具调用交换多条 LLM 消息，以检索输出。
9. 智能体的响应会被保证为 `SupportOutput`。如果[反思](agent.md#reflection-and-self-correction)校验失败，智能体会被提示再次尝试。
10. 输出会通过 Pydantic 校验，以保证它是 `SupportOutput`；因为智能体是泛型的，所以它也会被标注为 `SupportOutput`，以帮助静态类型检查。
11. 在真实用例中，你会向智能体添加更多工具和更长的指令，以扩展它具备的上下文和可以提供的支持。
12. 这是数据库连接的简化草图，用于让示例保持简短可读。现实中，你会连接到外部数据库（例如 PostgreSQL）来获取客户信息。
13. 这个 [Pydantic](https://docs.pydantic.dev) 模型用于约束智能体返回的结构化数据。基于这个简单定义，Pydantic 会构建 JSON Schema，告诉 LLM 如何返回数据，并在运行结束时执行校验以保证数据正确。

!!! tip "完整的 `bank_support.py` 示例"
    为了简洁，这里的代码并不完整（缺少 `DatabaseConn` 的定义）；你可以在[这里](examples/bank-support.md)找到完整的 `bank_support.py` 示例。

## 使用 Pydantic Logfire 进行插桩

即使一个简单智能体只有少量工具，也可能与 LLM 发生大量来回交互，让人几乎无法仅靠阅读代码就确信发生了什么。
为了理解上述运行流程，我们可以使用 Pydantic Logfire 观察智能体的实际行为。

为此，我们需要[设置 Logfire](logfire.md#using-logfire)，并在代码中添加以下内容：

```python {title="bank_support_with_logfire.py" hl_lines="6-10" test="skip" lint="skip"}
...
from pydantic_ai import Agent, RunContext

from bank_database import DatabaseConn

import logfire

logfire.configure()  # (1)!
logfire.instrument_pydantic_ai()  # (2)!
logfire.instrument_sqlite3()  # (3)!

...

support_agent = Agent(
    'openai:gpt-5.2',
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    instructions=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query.'
    ),
)
```

1. 配置 Logfire SDK；如果项目尚未设置，这会失败。
2. 这会对从此处开始使用的所有 Pydantic AI agents 进行插桩。若只想对特定 agent 插桩，请向该 agent 的 `capabilities=[...]` 添加 [`Instrumentation`][pydantic_ai.capabilities.Instrumentation] 条目。
3. 在我们的演示中，`DatabaseConn` 使用 [`sqlite3`][] 连接到 PostgreSQL 数据库，因此使用 [`logfire.instrument_sqlite3()`](https://logfire.pydantic.dev/docs/integrations/databases/sqlite3/) 记录数据库查询。

这足以让你看到如下智能体运行视图：

/// public-trace | https://logfire-eu.pydantic.dev/public-trace/a2957caa-b7b7-4883-a529-777742649004?spanId=31aade41ab896144
    title: 'Logfire instrumentation for the bank agent'
///

参见[监控和性能](logfire.md)了解更多信息。

## `llms.txt`

Pydantic AI 文档以 [llms.txt](https://llmstxt.org/) 格式提供。
该格式以 Markdown 定义，适合 LLM、AI 编码助手和智能体使用。

提供两种格式：

- [`llms.txt`](https://ai.pydantic.dev/llms.txt)：包含项目简要描述以及文档各章节链接的文件。该文件结构在[这里](https://llmstxt.org/#format)有详细说明。
- [`llms-full.txt`](https://ai.pydantic.dev/llms-full.txt)：与 `llms.txt` 文件类似，但包含每个链接的内容。请注意，该文件对某些 LLM 来说可能太大。

截至目前，这些文件尚不会被 IDE 或编码智能体自动利用，但如果你提供链接或全文，它们会使用。


## 下一步

要亲自尝试 Pydantic AI，请先[安装它](install.md)，然后按照[示例中的说明](examples/setup.md)操作。

阅读[文档](agent.md)，了解更多关于使用 Pydantic AI 构建应用的信息。

阅读 [API 参考](api/agent.md)，了解 Pydantic AI 的接口。

如果你有任何问题，可以加入 [Slack](https://logfire.pydantic.dev/docs/join-slack/) 或在 [:simple-github: GitHub](https://github.com/pydantic/pydantic-ai/issues) 上提交 issue。
