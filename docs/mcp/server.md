# 服务端 {#server}

Pydantic AI 模型也可以在 MCP servers 中使用。

## MCP server {#mcp-server}

下面是一个简单示例，展示如何在 [Python MCP server](https://github.com/modelcontextprotocol/python-sdk) 的工具调用中使用 Pydantic AI：

```py {title="mcp_server.py"}
from mcp.server.fastmcp import FastMCP

from pydantic_ai import Agent

server = FastMCP('Pydantic AI Server')
server_agent = Agent(
    'anthropic:claude-haiku-4-5', instructions='always reply in rhyme'
)


@server.tool()
async def poet(theme: str) -> str:
    """Poem generator"""
    r = await server_agent.run(f'write a poem about {theme}')
    return r.output


if __name__ == '__main__':
    server.run()
```

## 简单 client {#simple-client}

任何 MCP client 都可以查询这个 server。下面是一个直接使用 Python SDK 的示例：

```py {title="mcp_client.py" requires="mcp_server.py" dunder_name="not_main"}
import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def client():
    server_params = StdioServerParameters(
        command='python', args=['mcp_server.py'], env=os.environ
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool('poet', {'theme': 'socks'})
            print(result.content[0].text)
            """
            Oh, socks, those garments soft and sweet,
            That nestle softly 'round our feet,
            From cotton, wool, or blended thread,
            They keep our toes from feeling dread.
            """


if __name__ == '__main__':
    asyncio.run(client())
```

## MCP Sampling {#mcp-sampling}

!!! info "什么是 MCP Sampling？"
    MCP sampling 是什么，以及使用 Pydantic AI 作为 MCP client 时如何支持它，请参见 [MCP client 文档](./client.md#mcp-sampling)。

当 Pydantic AI 智能体在 MCP servers 中使用时，可以通过 [`MCPSamplingModel`][pydantic_ai.models.mcp_sampling.MCPSamplingModel] 使用 sampling。

我们可以扩展上面的示例来使用 sampling。这样智能体不再直接连接 LLM，而是通过 MCP client 回调来发起 LLM 调用。

```py {title="mcp_server_sampling.py"}
from mcp.server.fastmcp import Context, FastMCP

from pydantic_ai import Agent
from pydantic_ai.models.mcp_sampling import MCPSamplingModel

server = FastMCP('Pydantic AI Server with sampling')
server_agent = Agent(instructions='always reply in rhyme')


@server.tool()
async def poet(ctx: Context, theme: str) -> str:
    """Poem generator"""
    r = await server_agent.run(f'write a poem about {theme}', model=MCPSamplingModel(session=ctx.session))
    return r.output


if __name__ == '__main__':
    server.run()  # run the server over stdio
```

[上面的](#simple-client) client 不支持 sampling，因此如果尝试把它用于这个 server，会得到错误。

在 MCP client 中支持 sampling 的最简单方式，是[使用](./client.md#mcp-sampling) Pydantic AI 智能体作为 client；但如果你想用原生 MCP SDK 支持 sampling，也可以这样做：

```py {title="mcp_client_sampling.py" requires="mcp_server_sampling.py"}
import asyncio
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.context import RequestContext
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    ErrorData,
    TextContent,
)


async def sampling_callback(
    context: RequestContext[ClientSession, Any], params: CreateMessageRequestParams
) -> CreateMessageResult | ErrorData:
    print('sampling system prompt:', params.systemPrompt)
    #> sampling system prompt: always reply in rhyme
    print('sampling messages:', params.messages)
    """
    sampling messages:
    [
        SamplingMessage(
            role='user',
            content=TextContent(
                type='text',
                text='write a poem about socks',
                annotations=None,
                meta=None,
            ),
            meta=None,
        )
    ]
    """

    # TODO get the response content by calling an LLM...
    response_content = 'Socks for a fox.'

    return CreateMessageResult(
        role='assistant',
        content=TextContent(type='text', text=response_content),
        model='fictional-llm',
    )


async def client():
    server_params = StdioServerParameters(command='python', args=['mcp_server_sampling.py'])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write, sampling_callback=sampling_callback) as session:
            await session.initialize()
            result = await session.call_tool('poet', {'theme': 'socks'})
            print(result.content[0].text)
            #> Socks for a fox.


if __name__ == '__main__':
    asyncio.run(client())
```

_（此示例是完整的，可以"原样"运行）_
