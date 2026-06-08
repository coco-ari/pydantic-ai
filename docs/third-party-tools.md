# 第三方工具 {#third-party-tools}

Pydantic AI 支持与各种第三方工具库集成，让你可以在智能体中利用现有工具生态。第三方工具也可以作为[能力](capabilities.md#third-party-capabilities)使用，完整生态请参见[可扩展性](extensibility.md)。

## MCP Tools {#mcp-tools}

如何将 MCP server 作为 [toolsets](toolsets.md) 与 Pydantic AI 一起使用，请参见 [MCP Client](./mcp/client.md) 文档。

## LangChain Tools {#langchain-tools}

如果你想在 Pydantic AI 中使用 LangChain [社区工具库](https://python.langchain.com/docs/integrations/tools/)中的工具，可以使用 [`tool_from_langchain`][pydantic_ai.ext.langchain.tool_from_langchain] 便捷方法。注意，在这种情况下 Pydantic AI 不会校验参数，模型需要提供匹配 LangChain 工具指定 schema 的参数，而 LangChain 工具负责在参数无效时抛出错误。

你需要安装 `langchain-community` 包，以及相关工具所需的其他包。

下面展示如何使用 LangChain 的 `DuckDuckGoSearchRun` 工具，该工具需要 `ddgs` 包：

```python {test="skip"}
from langchain_community.tools import DuckDuckGoSearchRun

from pydantic_ai import Agent
from pydantic_ai.ext.langchain import tool_from_langchain

search = DuckDuckGoSearchRun()
search_tool = tool_from_langchain(search)

agent = Agent(
    'google:gemini-3-flash-preview',
    tools=[search_tool],
)

result = agent.run_sync('What is the release date of Elden Ring Nightreign?')  # (1)!
print(result.output)
#> Elden Ring Nightreign is planned to be released on May 30, 2025.
```

1. 这款游戏的发布日期是 2025 年 5 月 30 日，晚于 Gemini 2.0 的知识截止时间（2024 年 8 月）。

如果你想使用多个 LangChain 工具或 LangChain [toolkit](https://python.langchain.com/docs/concepts/tools/#toolkits)，可以使用 [`LangChainToolset`][pydantic_ai.ext.langchain.LangChainToolset] [toolset](toolsets.md)，它接受一个 LangChain 工具列表：

```python {test="skip"}
from langchain_community.agent_toolkits import SlackToolkit

from pydantic_ai import Agent
from pydantic_ai.ext.langchain import LangChainToolset

toolkit = SlackToolkit()
toolset = LangChainToolset(toolkit.get_tools())

agent = Agent('openai:gpt-5.2', toolsets=[toolset])
# ...
```

## ACI.dev Tools {#aci-tools}

!!! warning "在 1.x 中已弃用，将在 2.0 中移除"
    `pydantic_ai.ext.aci`（`tool_from_aci` 和 `ACIToolset`）已弃用，并将在 2.0 中移除（见 [#5467](https://github.com/pydantic/pydantic-ai/pull/5467)）。请使用 [`Tool.from_schema`][pydantic_ai.tools.Tool.from_schema] 基于 `aci.ACI().functions.get_definition(...)` 自行包装 ACI.dev 工具，或直接调用上游 `aci-sdk` 集成。

如果你想在 Pydantic AI 中使用 [ACI.dev 工具库](https://www.aci.dev/tools)中的工具，可以使用 [`tool_from_aci`][pydantic_ai.ext.aci.tool_from_aci] 便捷方法。注意，在这种情况下 Pydantic AI 不会校验参数，模型需要提供匹配 ACI 工具指定 schema 的参数，而 ACI 工具负责在参数无效时抛出错误。

你需要安装 `aci-sdk` 包，在 `ACI_API_KEY` 环境变量中设置 ACI API key，并将 ACI 的"linked account owner ID"传给该函数。

下面展示如何使用 ACI.dev 的 `TAVILY__SEARCH` 工具：

```python {test="skip"}
import os

from pydantic_ai import Agent
from pydantic_ai.ext.aci import tool_from_aci

tavily_search = tool_from_aci(
    'TAVILY__SEARCH',
    linked_account_owner_id=os.getenv('LINKED_ACCOUNT_OWNER_ID'),
)

agent = Agent(
    'google:gemini-3-flash-preview',
    tools=[tavily_search],
)

result = agent.run_sync('What is the release date of Elden Ring Nightreign?')  # (1)!
print(result.output)
#> Elden Ring Nightreign is planned to be released on May 30, 2025.
```

1. 这款游戏的发布日期是 2025 年 5 月 30 日，晚于 Gemini 2.0 的知识截止时间（2024 年 8 月）。

如果你想使用多个 ACI.dev 工具，可以使用 [`ACIToolset`][pydantic_ai.ext.aci.ACIToolset] [toolset](toolsets.md)，它接受 ACI 工具名称列表以及 `linked_account_owner_id`：

```python {test="skip"}
import os

from pydantic_ai import Agent
from pydantic_ai.ext.aci import ACIToolset

toolset = ACIToolset(
    [
        'OPEN_WEATHER_MAP__CURRENT_WEATHER',
        'OPEN_WEATHER_MAP__FORECAST',
    ],
    linked_account_owner_id=os.getenv('LINKED_ACCOUNT_OWNER_ID'),
)

agent = Agent('openai:gpt-5.2', toolsets=[toolset])
```

## 另请参见

- [函数工具](tools.md) - 基本工具概念和注册
- [Toolsets](toolsets.md) - 管理工具集合
- [MCP Client](mcp/client.md) - 将 MCP server 与 Pydantic AI 一起使用
- [LangChain Toolsets](toolsets.md#langchain-tools) - 使用 LangChain toolsets
- [ACI.dev Toolsets](toolsets.md#aci-tools) - 使用 ACI.dev toolsets
