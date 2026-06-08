# 客户端 {#client}

Pydantic AI 可以作为 [MCP client](https://modelcontextprotocol.io/quickstart/client)，连接到 MCP servers
并使用它们的工具。

## 安装 {#install}

你需要安装 [`pydantic-ai`](../install.md)，或安装带 `mcp` 可选组的 [`pydantic-ai-slim`](../install.md#slim-install)：

```bash
pip/uv-add "pydantic-ai-slim[mcp]"
```

## 用法 {#usage}

Pydantic AI 提供三种连接 MCP servers 的方式：

- [`MCPServerStreamableHTTP`][pydantic_ai.mcp.MCPServerStreamableHTTP]，使用 [Streamable HTTP](https://modelcontextprotocol.io/introduction#streamable-http) transport 连接到 MCP server
- [`MCPServerSSE`][pydantic_ai.mcp.MCPServerSSE]，使用 [HTTP SSE](https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse) transport 连接到 MCP server
- [`MCPServerStdio`][pydantic_ai.mcp.MCPServerStdio]，将 server 作为 subprocess 运行，并使用 [stdio](https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#stdio) transport 连接

下面展示了这三种方式的示例。

每个 MCP server 实例都是一个 [toolset](../toolsets.md)，可以使用 `toolsets` 参数注册到 [`Agent`][pydantic_ai.Agent]。

你可以使用 [`async with agent`][pydantic_ai.agent.Agent.__aenter__] context manager，在 agent runs 会使用这些 servers 的上下文范围内打开并关闭所有已注册 server 的连接（对于 stdio servers，也会启动和停止 subprocesses）。你也可以使用 [`async with server`][pydantic_ai.mcp.MCPServer.__aenter__] 管理某个特定 server 的连接或 subprocess，例如当你想让它被多个 agents 使用时。如果你没有显式进入这些 context managers 来设置 server，Pydantic AI 会在需要时自动完成（例如列出可用工具或调用特定工具时），但围绕整个预期使用 servers 的上下文显式管理会更高效。

### Streamable HTTP Client {#streamable-http-client}

[`MCPServerStreamableHTTP`][pydantic_ai.mcp.MCPServerStreamableHTTP] 通过 HTTP 使用
[Streamable HTTP](https://modelcontextprotocol.io/introduction#streamable-http) transport 连接到 server。

!!! note
    [`MCPServerStreamableHTTP`][pydantic_ai.mcp.MCPServerStreamableHTTP] 要求在运行 agent 前，MCP server 已经运行并接受 HTTP 连接。运行 server 不由 Pydantic AI 管理。

创建 Streamable HTTP client 前，我们需要先运行一个支持 Streamable HTTP transport 的 server。

```python {title="streamable_http_server.py" dunder_name="not_main"}
from mcp.server.fastmcp import FastMCP

app = FastMCP()

@app.tool()
def add(a: int, b: int) -> int:
    return a + b

if __name__ == '__main__':
    app.run(transport='streamable-http')
```

然后可以创建 client：

```python {title="mcp_streamable_http_client.py"}
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp')  # (1)!
agent = Agent('openai:gpt-5.2', toolsets=[server])  # (2)!

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.
```

1. 使用连接 URL 定义 MCP server。
2. 创建附加了 MCP server 的 agent。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

**这里发生了什么？**

- 模型收到 prompt "What is 7 plus 5?"
- 模型判断："我有这个 `add` 工具，用它回答这个问题很合适"
- 模型返回 tool call
- Pydantic AI 使用 Streamable HTTP transport 将 tool call 发送到 MCP server
- 模型再次被调用，并接收运行 `add` 工具的返回值（12）
- 模型返回最终答案

你可以通过添加三行代码，用 [logfire](https://logfire.pydantic.dev/docs) 为示例增加 instrumentation，从而清楚地可视化这个过程，甚至看到 tool call：

```python {title="mcp_sse_client_logfire.py" test="skip"}
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()
```

### SSE Client {#sse-client}

[`MCPServerSSE`][pydantic_ai.mcp.MCPServerSSE] 通过 HTTP 使用 [HTTP + Server Sent Events transport](https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#http-with-sse) 连接到 server。

!!! note
    MCP 中的 SSE transport 已弃用，应改用 Streamable HTTP。

创建 SSE client 前，我们需要先运行一个支持 SSE transport 的 server。


```python {title="sse_server.py" dunder_name="not_main"}
from mcp.server.fastmcp import FastMCP

app = FastMCP()

@app.tool()
def add(a: int, b: int) -> int:
    return a + b

if __name__ == '__main__':
    app.run(transport='sse')
```

然后可以创建 client：

```python {title="mcp_sse_client.py"}
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE

server = MCPServerSSE('http://localhost:3001/sse')  # (1)!
agent = Agent('openai:gpt-5.2', toolsets=[server])  # (2)!


async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
    #> The answer is 12.
```

1. 使用连接 URL 定义 MCP server。
2. 创建附加了 MCP server 的 agent。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

### MCP "stdio" Server {#mcp-stdio-server}

MCP 还提供 [stdio transport](https://spec.modelcontextprotocol.io/specification/2024-11-05/basic/transports/#stdio)，其中 server 作为 subprocess 运行，并通过 `stdin` 和 `stdout` 与 client 通信。在这种情况下，你会使用 [`MCPServerStdio`][pydantic_ai.mcp.MCPServerStdio] 类。

在此示例中，我们使用一个提供天气工具的简单 MCP server。

```python {title="mcp_stdio_client.py"}
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio('python', args=['mcp_server.py'], timeout=10)
agent = Agent('openai:gpt-5.2', toolsets=[server])


async def main():
    result = await agent.run('What is the weather in Paris?')
    print(result.output)
    #> The weather in Paris is sunny and 26 degrees Celsius.
```

## 从配置加载 MCP Servers {#loading-mcp-servers-from-configuration}

除了在代码中逐个创建 MCP server 实例，你也可以使用 [`load_mcp_servers()`][pydantic_ai.mcp.load_mcp_servers] 从 JSON 配置文件加载多个 servers。

当你需要管理多个 MCP servers，或想在不修改代码的情况下从外部配置 servers 时，这尤其有用。

### 配置格式 {#configuration-format}

配置文件应是一个 JSON 文件，其中包含 `mcpServers` 对象，内部是 server definitions。每个 server 由唯一 key 标识，并包含该 server 类型的配置：

```json {title="mcp_config.json"}
{
  "mcpServers": {
    "python-runner": {
        "command": "uv",
        "args": ["run", "mcp-run-python", "stdio"]
    },
    "weather": {
      "command": "python",
      "args": ["mcp_server.py"]
    },
    "weather-api": {
      "url": "http://localhost:3001/sse"
    },
    "calculator": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

!!! note
    只有带 `/sse` 后缀时，MCP server 才会被推断为 SSE server。
    任何其他带 `"url"` 字段的 server 都会被推断为 Streamable HTTP server。

    我们做出这个决定，是因为 SSE transport 已经弃用。

### 环境变量 {#environment-variables}

配置文件支持使用 `${VAR}` 和 `${VAR:-default}` 语法展开环境变量，
[与 Claude Code 类似](https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcp-json)。
这有助于避免把 API keys 或 host names 等敏感信息放进配置文件：

```json {title="mcp_config_with_env.json"}
{
  "mcpServers": {
    "python-runner": {
      "command": "${PYTHON_CMD:-python3}",
      "args": ["run", "${MCP_MODULE}", "stdio"],
      "env": {
        "API_KEY": "${MY_API_KEY}"
      }
    },
    "weather-api": {
      "url": "https://${SERVER_HOST:-localhost}:${SERVER_PORT:-8080}/sse"
    }
  }
}
```

使用 [`load_mcp_servers()`][pydantic_ai.mcp.load_mcp_servers] 加载此配置时：

- `${VAR}` references 会被替换为对应的环境变量值。
- `${VAR:-default}` references 会在环境变量已设置时使用其值，否则使用默认值。

!!! warning
    如果使用 `${VAR}` 语法引用的环境变量未定义，会引发 `ValueError`。请使用 `${VAR:-default}` 语法提供 fallback 值。

### 用法 {#configuration-usage}

```python {title="mcp_config_loader.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.mcp import load_mcp_servers

# Load all servers from configuration file
servers = load_mcp_servers('mcp_config.json')

# Create agent with all loaded servers
agent = Agent('openai:gpt-5.2', toolsets=servers)

async def main():
    result = await agent.run('What is 7 plus 5?')
    print(result.output)
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

## Tool call 定制 {#tool-call-customization}

MCP servers 提供设置 `process_tool_call` 的能力，用于定制 tool call 请求及其响应。

一个常见用例是向 server call 所需的请求中注入 metadata：

```python {title="mcp_process_tool_call.py"}
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import CallToolFunc, MCPServerStdio, ToolResult
from pydantic_ai.models.test import TestModel


async def process_tool_call(
    ctx: RunContext[int],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """A tool call processor that passes along the deps."""
    return await call_tool(name, tool_args, {'deps': ctx.deps})


server = MCPServerStdio('python', args=['mcp_server.py'], process_tool_call=process_tool_call)
agent = Agent(
    model=TestModel(call_tools=['echo_deps']),
    deps_type=int,
    toolsets=[server]
)


async def main():
    result = await agent.run('Echo with deps set to 42', deps=42)
    print(result.output)
    #> {"echo_deps":{"echo":"This is an echo message","deps":42}}
```

如何访问 metadata 取决于 MCP server SDK。例如在 [MCP Python
SDK](https://github.com/modelcontextprotocol/python-sdk) 中，可以通过工具调用 handlers 上可包含的
[`ctx: Context`](https://github.com/modelcontextprotocol/python-sdk#context)
参数访问：

```python {title="mcp_server.py"}
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

mcp = FastMCP('Pydantic AI MCP Server')
log_level = 'unset'


@mcp.tool()
async def echo_deps(ctx: Context[ServerSession, None]) -> dict[str, Any]:
    """Echo the run context.

    Args:
        ctx: Context object containing request and session information.

    Returns:
        Dictionary with an echo message and the deps.
    """
    await ctx.info('This is an info message')

    deps: Any = getattr(ctx.request_context.meta, 'deps')
    return {'echo': 'This is an echo message', 'deps': deps}

if __name__ == '__main__':
    mcp.run()
```

## 使用工具前缀避免命名冲突 {#using-tool-prefixes-to-avoid-naming-conflicts}

连接到多个可能提供同名工具的 MCP servers 时，可以使用 `tool_prefix` 参数避免命名冲突。该参数会向来自特定 server 的所有工具名添加前缀。

这允许你使用多个可能有重叠工具名的 servers，而不会发生冲突：

```python {title="mcp_tool_prefix_http_client.py"}
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE

# Create two servers with different prefixes
weather_server = MCPServerSSE(
    'http://localhost:3001/sse',
    tool_prefix='weather'  # Tools will be prefixed with 'weather_'
)

calculator_server = MCPServerSSE(
    'http://localhost:3002/sse',
    tool_prefix='calc'  # Tools will be prefixed with 'calc_'
)

# Both servers might have a tool named 'get_data', but they'll be exposed as:
# - 'weather_get_data'
# - 'calc_get_data'
agent = Agent('openai:gpt-5.2', toolsets=[weather_server, calculator_server])
```

## Server Instructions {#server-instructions}

MCP servers 可以在初始化期间提供 instructions，用于说明如何最好地与 server 的工具交互。这些 instructions 会在连接建立后通过 [`instructions`][pydantic_ai.mcp.MCPServer.instructions] 属性访问；创建 server 时设置 `include_instructions=True` 可以将它们自动注入 agent 的 instructions。

```python {title="mcp_server_include_instructions.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP('http://localhost:8000/mcp', include_instructions=True)
agent = Agent('openai:gpt-5.2', toolsets=[server])
```

## 工具 metadata {#tool-metadata}

MCP tools 可以包含 metadata，以提供有关工具特征的额外信息；这在[过滤工具][pydantic_ai.toolsets.FilteredToolset]时很有用。传给 filter functions 的 [`ToolDefinition`][pydantic_ai.tools.ToolDefinition] 对象上，`metadata` dict 包含 `meta` 和 `annotations` 字段；工具的 output schema（如果有）可通过 `return_schema` 字段获得。

[`MCPToolset`][pydantic_ai.mcp.MCPToolset] 还额外暴露一个 `task: bool` 标志，用于表示 server 是否声明该工具支持[任务增强执行](#background-tasks)。

## 后台任务 {#background-tasks}

[`MCPToolset`][pydantic_ai.mcp.MCPToolset] 支持 MCP [task-augmented execution](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks) (SEP-1686)。Servers 可以通过 `execution.taskSupport` 声明 per-tool task support，`MCPToolset` 会相应路由调用：

| `execution.taskSupport` | 行为 |
| --- | --- |
| `"required"` | 始终以 `task=True` 调用。Server 会创建 task，client 通过 `tasks/result` 等待最终结果。 |
| `"optional"` | 始终以 `task=True` 调用，以选择启用 durability、cancellation 和 progress notifications。 |
| `"forbidden"` 或缺失 | 正常调用。 |

对于 [FastMCP](https://gofastmcp.com/) servers，可以用 `task=TaskConfig(mode=...)` 为每个工具声明 task support：

```python {title="background_task_server.py" dunder_name="not_main"}
from fastmcp import FastMCP
from fastmcp.server.tasks import TaskConfig

mcp = FastMCP('long_running_server')


@mcp.tool(task=TaskConfig(mode='required'))
async def deep_research(topic: str) -> str:
    import asyncio
    await asyncio.sleep(0)
    return f'Researched {topic}'


if __name__ == '__main__':
    mcp.run(transport='streamable-http')
```

Client 侧无需额外配置；`MCPToolset` 会根据 server 的声明自动发送 `task=True`：

```python {title="background_task_client.py"}
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

toolset = MCPToolset('http://localhost:8000/mcp')
agent = Agent('openai:gpt-5.2', toolsets=[toolset])
```

## Resources {#resources}

MCP servers 可以提供 [resources](https://modelcontextprotocol.io/docs/concepts/resources)，也就是 client 可以访问的文件、数据或内容。MCP 中的 resources 由应用驱动，host applications 会根据自身需要决定如何手动纳入上下文。这意味着它们**不会**自动暴露给 LLM（除非某个工具返回 `ResourceLink` 或 `EmbeddedResource`）。

Pydantic AI 提供了从 MCP servers 发现和读取 resources 的方法：

- [`list_resources()`][pydantic_ai.mcp.MCPServer.list_resources] - 列出 server 上所有可用 resources
- [`list_resource_templates()`][pydantic_ai.mcp.MCPServer.list_resource_templates] - 列出带参数 placeholders 的 resource templates
- [`read_resource(uri)`][pydantic_ai.mcp.MCPServer.read_resource] - 通过 URI 读取特定 resource 的内容

Resources 会被自动转换：文本内容返回为 `str`，二进制内容返回为 [`BinaryContent`][pydantic_ai.messages.BinaryContent]。

在消费 resources 前，我们需要先运行一个暴露这些 resources 的 server：

```python {title="mcp_resource_server.py"}
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('Pydantic AI MCP Server')
log_level = 'unset'


@mcp.resource('resource://user_name.txt', mime_type='text/plain')
async def user_name_resource() -> str:
    return 'Alice'


if __name__ == '__main__':
    mcp.run()
```

然后可以创建 client：

```python {title="mcp_resources.py", requires="mcp_resource_server.py"}
import asyncio

from pydantic_ai.mcp import MCPServerStdio


async def main():
    server = MCPServerStdio('python', args=['-m', 'mcp_resource_server'])

    async with server:
        # List all available resources
        resources = await server.list_resources()
        for resource in resources:
            print(f' - {resource.name}: {resource.uri} ({resource.mime_type})')
            #>  - user_name_resource: resource://user_name.txt (text/plain)

        # Read a text resource
        user_name = await server.read_resource('resource://user_name.txt')
        print(f'Text content: {user_name}')
        #> Text content: Alice


if __name__ == '__main__':
    asyncio.run(main())
```

_（这个示例是完整的，可以"原样"运行）_


## 自定义 TLS / SSL 配置 {#custom-tls-ssl-configuration}

在某些环境中，你需要调整 HTTPS 连接的建立方式；
例如，信任内部 Certificate Authority、为 **mTLS** 提供 client
certificate，或者（仅限本地开发！）完全禁用
certificate verification。
所有基于 HTTP 的 MCP client classes
（[`MCPServerStreamableHTTP`][pydantic_ai.mcp.MCPServerStreamableHTTP] 和
[`MCPServerSSE`][pydantic_ai.mcp.MCPServerSSE]）都暴露 `http_client`
参数，让你可以传入自己预配置的
[`httpx.AsyncClient`](https://www.python-httpx.org/async/)。

```python {title="mcp_custom_tls_client.py"}
import ssl

import httpx

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE

# Trust an internal / self-signed CA
ssl_ctx = ssl.create_default_context(cafile='/etc/ssl/private/my_company_ca.pem')

# OPTIONAL: if the server requires **mutual TLS** load your client certificate
ssl_ctx.load_cert_chain(certfile='/etc/ssl/certs/client.crt', keyfile='/etc/ssl/private/client.key',)

http_client = httpx.AsyncClient(
    verify=ssl_ctx,
    timeout=httpx.Timeout(10.0),
)

server = MCPServerSSE(
    'http://localhost:3001/sse',
    http_client=http_client,  # (1)!
)
agent = Agent('openai:gpt-5.2', toolsets=[server])

async def main():
    result = await agent.run('How many days between 2000-01-01 and 2025-03-18?')
    print(result.output)
    #> There are 9,208 days between January 1, 2000, and March 18, 2025.
```

1. 当你提供 `http_client` 时，Pydantic AI 会为每个请求复用这个 client。
   因此，**httpx** 支持的任何内容（`verify`、`cert`、custom
   proxies、timeouts 等）都会应用到所有 MCP traffic。

## Client Identification {#client-identification}

连接到 MCP server 时，你可以选择指定一个 [Implementation](https://modelcontextprotocol.io/specification/2025-11-25/schema#implementation) 对象作为 client information，并在初始化期间发送给 server。这适用于：

- 在 server logs 中识别你的应用
- 允许 servers 根据 client 提供自定义行为
- 调试和监控 MCP connections
- 版本特定的 feature negotiation

所有 MCP client classes（[`MCPServerStdio`][pydantic_ai.mcp.MCPServerStdio]、[`MCPServerStreamableHTTP`][pydantic_ai.mcp.MCPServerStreamableHTTP] 和 [`MCPServerSSE`][pydantic_ai.mcp.MCPServerSSE]）都支持 `client_info` 参数：

```python {title="mcp_client_with_name.py"}
from mcp import types as mcp_types

from pydantic_ai.mcp import MCPServerSSE

server = MCPServerSSE(
    'http://localhost:3001/sse',
    client_info=mcp_types.Implementation(
        name='MyApplication',
        version='2.1.0',
    ),
)
```

## MCP Sampling {#mcp-sampling}

!!! info "什么是 MCP Sampling？"
    在 MCP 中，[sampling](https://modelcontextprotocol.io/docs/concepts/sampling) 是一种机制，MCP server 可以通过 MCP client 发起 LLM calls；实际效果是通过正在使用的 transport，把对 LLM 的请求经由 client 代理出去。

    当 MCP servers 需要使用 Gen AI，但你不想为每个 server 单独配置 LLM credentials，或者某个公共 MCP server 希望由连接它的 client 支付 LLM calls 成本时，Sampling 非常有用。

    容易混淆的是，它与 observability 中的 "sampling" 概念无关，也坦率地说与其他领域的 "sampling" 概念无关。

    ??? info "Sampling Diagram"
        下面这个 mermaid diagram 可能会，也可能不会，让数据流更清楚：

        ```mermaid
        sequenceDiagram
            participant LLM
            participant MCP_Client as MCP client
            participant MCP_Server as MCP server

            MCP_Client->>LLM: LLM call
            LLM->>MCP_Client: LLM tool call response

            MCP_Client->>MCP_Server: tool call
            MCP_Server->>MCP_Client: sampling "create message"

            MCP_Client->>LLM: LLM call
            LLM->>MCP_Client: LLM text response

            MCP_Client->>MCP_Server: sampling response
            MCP_Server->>MCP_Client: tool call response
        ```

Pydantic AI 同时支持作为 client 和 server 进行 sampling。有关如何在 server 中使用 sampling 的细节，请参阅 [server](./server.md#mcp-sampling) 文档。

当 Pydantic AI agents 作为 client 时，会自动支持 sampling。

要使用 sampling，MCP server 实例需要设置 [`sampling_model`][pydantic_ai.mcp.MCPServer.sampling_model]。可以直接通过 server 的 constructor keyword argument 或 property 设置，也可以使用 [`agent.set_mcp_sampling_model()`][pydantic_ai.agent.Agent.set_mcp_sampling_model]，将 agent 的模型或参数中指定的模型设置为该 agent 注册的所有 MCP servers 的 sampling model。

假设我们有一个希望使用 sampling 的 MCP server（在此例中按工具参数生成 SVG）。

??? example "Sampling MCP Server"

    ```python {title="generate_svg.py"}
    import re
    from pathlib import Path

    from mcp import SamplingMessage
    from mcp.server.fastmcp import Context, FastMCP
    from mcp.types import TextContent

    app = FastMCP()


    @app.tool()
    async def image_generator(ctx: Context, subject: str, style: str) -> str:
        prompt = f'{subject=} {style=}'
        # `ctx.session.create_message` is the sampling call
        result = await ctx.session.create_message(
            [SamplingMessage(role='user', content=TextContent(type='text', text=prompt))],
            max_tokens=1_024,
            system_prompt='Generate an SVG image as per the user input',
        )
        assert isinstance(result.content, TextContent)

        path = Path(f'{subject}_{style}.svg')
        # remove triple backticks if the svg was returned within markdown
        if m := re.search(r'^```\w*$(.+?)```$', result.content.text, re.S | re.M):
            path.write_text(m.group(1), encoding='utf-8')
        else:
            path.write_text(result.content.text, encoding='utf-8')
        return f'See {path}'


    if __name__ == '__main__':
        # run the server via stdio
        app.run()
    ```

把这个 server 与 `Agent` 一起使用时，会自动允许 sampling：

```python {title="sampling_mcp_client.py" requires="generate_svg.py"}
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio('python', args=['generate_svg.py'])
agent = Agent('openai:gpt-5.2', toolsets=[server])


async def main():
    agent.set_mcp_sampling_model()
    result = await agent.run('Create an image of a robot in a punk style.')
    print(result.output)
    #> Image file written to robot_punk.svg.
```

_（这个示例是完整的，可以"原样"运行）_

你可以在创建 server reference 时设置 [`allow_sampling=False`][pydantic_ai.mcp.MCPServer.allow_sampling] 来禁止 sampling，例如：

```python {title="sampling_disallowed.py" hl_lines="6"}
from pydantic_ai.mcp import MCPServerStdio

server = MCPServerStdio(
    'python',
    args=['generate_svg.py'],
    allow_sampling=False,
)
```

## Elicitation {#elicitation}

在 MCP 中，[elicitation](https://modelcontextprotocol.io/docs/concepts/elicitation) 允许 server 在 session 期间，从 client 请求缺失或额外上下文所需的[结构化输入](https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation#supported-schema-types)。

Elicitation 本质上让模型可以说"等一下，我需要先知道 X 才能继续"，而不是要求一开始就提供所有信息，或在信息不足时盲猜。

### Elicitation 如何工作 {#how-elicitation-works}

Elicitation 引入了一种新的 protocol message 类型，称为 [`ElicitRequest`](https://modelcontextprotocol.io/specification/2025-06-18/schema#elicitrequest)。当 server 需要额外信息时，它会从 server 发送到 client。随后 client 可以用 [`ElicitResult`](https://modelcontextprotocol.io/specification/2025-06-18/schema#elicitresult) 或 `ErrorData` message 响应。

一个典型交互如下：

- User 向 MCP server 发起请求（例如 "Book a table at that Italian place"）
- Server 发现需要更多信息（例如 "Which Italian place?"、"What date and time?"）
- Server 向 client 发送 `ElicitRequest`，请求缺失信息。
- Client 收到请求，并将其展示给 user（例如通过 terminal prompt、GUI dialog 或 web interface）。
- User 提供请求的信息，或 `decline` / `cancel` 该请求。
- Client 将包含 user 响应的 `ElicitResult` 发回 server。
- 拿到结构化数据后，server 可以继续处理原始请求。

这可以带来更交互式、更友好的体验，尤其适用于多阶段 workflows。Server 不必要求一开始就提供所有信息，而是可以在需要时询问，让交互感觉更自然。

### 设置 Elicitation {#setting-up-elicitation}

要启用 elicitation，在创建 MCP server 实例时提供 [`elicitation_callback`][pydantic_ai.mcp.MCPServer.elicitation_callback] 函数：

```python {title="restaurant_server.py"}
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP(name='Restaurant Booking')


class BookingDetails(BaseModel):
    """Schema for restaurant booking information."""

    restaurant: str = Field(description='Choose a restaurant')
    party_size: int = Field(description='Number of people', ge=1, le=8)
    date: str = Field(description='Reservation date (DD-MM-YYYY)')


@mcp.tool()
async def book_table(ctx: Context) -> str:
    """Book a restaurant table with user input."""
    # Ask user for booking details using Pydantic schema
    result = await ctx.elicit(message='Please provide your booking details:', schema=BookingDetails)

    if result.action == 'accept' and result.data:
        booking = result.data
        return f'✅ Booked table for {booking.party_size} at {booking.restaurant} on {booking.date}'
    elif result.action == 'decline':
        return 'No problem! Maybe another time.'
    else:  # cancel
        return 'Booking cancelled.'


if __name__ == '__main__':
    mcp.run(transport='stdio')
```

这个 server 通过在调用 `book_table` 工具时向 client 请求结构化预订详情，演示 elicitation。下面是如何创建处理这些 elicitation requests 的 client：

```python {title="client_example.py" requires="restaurant_server.py" test="skip"}
import asyncio
from typing import Any

from mcp.client.session import ClientSession
from mcp.shared.context import RequestContext
from mcp.types import ElicitRequestParams, ElicitResult

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio


async def handle_elicitation(
    context: RequestContext[ClientSession, Any, Any],
    params: ElicitRequestParams,
) -> ElicitResult:
    """Handle elicitation requests from MCP server."""
    print(f'\n{params.message}')

    if not params.requestedSchema:
        response = input('Response: ')
        return ElicitResult(action='accept', content={'response': response})

    # Collect data for each field
    properties = params.requestedSchema['properties']
    data = {}

    for field, info in properties.items():
        description = info.get('description', field)

        value = input(f'{description}: ')

        # Convert to proper type based on JSON schema
        if info.get('type') == 'integer':
            data[field] = int(value)
        else:
            data[field] = value

    # Confirm
    confirm = input('\nConfirm booking? (y/n/c): ').lower()

    if confirm == 'y':
        print('Booking details:', data)
        return ElicitResult(action='accept', content=data)
    elif confirm == 'n':
        return ElicitResult(action='decline')
    else:
        return ElicitResult(action='cancel')


# Set up MCP server connection
restaurant_server = MCPServerStdio(
    'python', args=['restaurant_server.py'], elicitation_callback=handle_elicitation
)

# Create agent
agent = Agent('openai:gpt-5.2', toolsets=[restaurant_server])


async def main():
    """Run the agent to book a restaurant table."""
    result = await agent.run('Book me a table')
    print(f'\nResult: {result.output}')


if __name__ == '__main__':
    asyncio.run(main())
```

### 支持的 Schema 类型 {#supported-schema-types}

MCP elicitation 支持 string、number、boolean 和 enum 类型，并且仅支持 flat object structures。这些限制确保可靠的跨 client 兼容性。详情请参阅 [supported schema types](https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation#supported-schema-types)。

### 安全性 {#security}

MCP Elicitation 需要谨慎处理：servers 不得请求敏感信息，clients 必须实现带清晰说明的 user approval controls。详情请参阅 [security considerations](https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation#security-considerations)。
