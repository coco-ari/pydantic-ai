# 模型上下文协议（MCP） {#model-context-protocol-mcp}

Pydantic AI 通过多种方式支持 [Model Context Protocol（MCP）](https://modelcontextprotocol.io)：

1. [智能体](../agent.md)可以通过三种不同方式连接到 MCP server 并使用其工具：
    1. Pydantic AI 可以充当 MCP client，并直接连接到本地和远程 MCP server。进一步了解 [`MCPServer`][pydantic_ai.mcp.MCPServer] 请参见[这里](client.md)。
    2. Pydantic AI 可以使用 [FastMCP Client](https://gofastmcp.com/clients/client/) 连接到本地和远程 MCP server，无论这些 server 是否使用 [FastMCP Server](https://gofastmcp.com/servers) 构建。进一步了解 [`FastMCPToolset`][pydantic_ai.toolsets.fastmcp.FastMCPToolset] 请参见[这里](fastmcp-client.md)。
    3. 一些模型提供商本身可以使用"原生工具"连接到远程 MCP server。进一步了解 [`MCPServerTool`][pydantic_ai.native_tools.MCPServerTool] 请参见[这里](../native-tools.md#mcp-server-tool)。
2. 智能体也可以在 MCP server 内使用。进一步了解请参见[这里](server.md)。

## 什么是 MCP？

Model Context Protocol 是一种标准化协议，允许 AI 应用（包括 Pydantic AI 这类编程式智能体、[Cursor](https://www.cursor.com/) 这类编码智能体，以及 [Claude Desktop](https://claude.ai/download) 这类桌面应用）通过通用接口连接到外部工具和服务。

与其他协议一样，MCP 的愿景是让各种应用无需专门集成即可相互通信。

你可以在 [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) 找到一份不错的 MCP server 列表。

下面是一些具体含义示例：

- Pydantic AI 可以使用作为 MCP server 实现的网页搜索服务，来实现深度研究智能体
- Cursor 可以连接到 [Pydantic Logfire](https://github.com/pydantic/logfire-mcp) MCP server，搜索日志、追踪和指标，以便在修复 bug 时获取上下文
- Pydantic AI 或任何其他 MCP client 都可以连接到我们的 [Run Python](https://github.com/pydantic/mcp-run-python) MCP server，在沙箱环境中运行任意 Python 代码
