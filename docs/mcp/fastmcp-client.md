# FastMCP Client 客户端 {#fastmcp-client}

[FastMCP](https://gofastmcp.com/) 是一个更高层次的 MCP 框架，自称是"构建 MCP server 和 client 的快速、Pythonic 方式"。它在 MCP 规范之上支持额外能力，例如 [Tool Transformation](https://gofastmcp.com/patterns/tool-transformation)、[OAuth](https://gofastmcp.com/clients/auth/oauth) 等。

作为 Pydantic AI 基于 [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) 构建的标准 [`MCPServer` MCP client](client.md) 的替代方案，你可以使用 [`FastMCPToolset`][pydantic_ai.toolsets.fastmcp.FastMCPToolset] [toolset](../toolsets.md)。它利用 [FastMCP Client](https://gofastmcp.com/clients/) 连接到本地和远程 MCP server，无论这些 server 是否使用 [FastMCP Server](https://gofastmcp.com/servers/) 构建。

注意，它尚不支持 integration elicitation 或 sampling，而这些能力由[标准 `MCPServer` client](client.md) 支持。

## 安装

要使用 `FastMCPToolset`，你需要安装带 `fastmcp` 可选组的 [`pydantic-ai-slim`](../install.md#slim-install)：

```bash
pip/uv-add "pydantic-ai-slim[fastmcp]"
```

## 使用

随后可以从以下来源创建 `FastMCPToolset`：

- FastMCP Server 服务端：`#!python FastMCPToolset(fastmcp.FastMCP('my_server'))`
- FastMCP Client 客户端：`#!python FastMCPToolset(fastmcp.Client(...))`
- FastMCP Transport 传输：`#!python FastMCPToolset(fastmcp.StdioTransport(command='python', args=['mcp_server.py']))`
- Streamable HTTP URL 地址：`#!python FastMCPToolset('http://localhost:8000/mcp')`
- HTTP SSE URL：`#!python FastMCPToolset('http://localhost:8000/sse')`
- Python Script 脚本：`#!python FastMCPToolset('my_server.py')`
- Node.js Script 脚本：`#!python FastMCPToolset('my_server.js')`
- JSON MCP Configuration 配置：`#!python FastMCPToolset({'mcpServers': {'my_server': {'command': 'python', 'args': ['mcp_server.py']}}})`

如果你的 Pydantic AI 智能体所在代码库中已经有 [FastMCP Server](https://gofastmcp.com/servers)，可以直接从它创建 `FastMCPToolset`，从而省去智能体的一次网络往返：

```python
from fastmcp import FastMCP

from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

fastmcp_server = FastMCP('my_server')
@fastmcp_server.tool()
async def add(a: int, b: int) -> int:
    return a + b

toolset = FastMCPToolset(fastmcp_server)

agent = Agent('openai:gpt-5.2', toolsets=[toolset])

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.
```

_（此示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

将智能体连接到 Streamable HTTP MCP Server 非常简单：

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

toolset = FastMCPToolset('http://localhost:8000/mcp')

agent = Agent('openai:gpt-5.2', toolsets=[toolset])
```

_（此示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

你也可以从 JSON MCP Configuration 创建 `FastMCPToolset`：

```python
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

mcp_config = {
    'mcpServers': {
        'time_mcp_server': {
            'command': 'uvx',
            'args': ['mcp-run-python', 'stdio']
        },
        'weather_server': {
            'command': 'python',
            'args': ['mcp_server.py']
        }
    }
}

toolset = FastMCPToolset(mcp_config)

agent = Agent('openai:gpt-5.2', toolsets=[toolset])
```

_（此示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_
