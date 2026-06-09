# Web Chat UI 网页聊天界面 {#web-chat-ui}

Pydantic AI 内置了一个 Web 聊天界面，你可以通过浏览器与自己的 agents 交互。

![Web Chat UI 网页聊天界面](img/web-chat-ui.png)

关于使用 `clai web` 的 CLI 用法，请参见 [CLI - Web Chat UI 文档](cli.md#web-chat-ui)。

!!! note
    Web UI 主要用于本地开发和调试。在生产环境中，可以使用某个 [UI Event Stream integrations](ui/overview.md)，将智能体连接到自定义前端。

## 安装

安装 `web` extra（会安装 Starlette 和 Uvicorn）：

```bash
pip/uv-add 'pydantic-ai-slim[web]'
```

## 基础用法

使用 [`Agent.to_web()`][pydantic_ai.agent.Agent.to_web] 从 agent 实例创建 Web app：

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='You are a helpful assistant.')

@agent.tool_plain
def get_weather(city: str) -> str:
    return f'The weather in {city} is sunny'

app = agent.to_web()
```

使用任意 ASGI server 运行 app：

```bash
uvicorn my_module:app --host 127.0.0.1 --port 7932
```

## 配置模型

你可以指定额外模型，让它们在 UI 中可用。Models 可以以模型名称/实例列表提供，也可以以 display labels 到模型名称/实例的字典提供。

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

# Model with custom configuration
anthropic_model = AnthropicModel('claude-sonnet-4-5')

agent = Agent('openai:gpt-5.2')

app = agent.to_web(
    models=['openai:gpt-5.2', anthropic_model],
)

# Or with custom display labels
app = agent.to_web(
    models={'GPT 5.2': 'openai:gpt-5.2', 'Claude': anthropic_model},
)
```

## 原生工具支持 {#native-tool-support}

在 agent 上使用 `capabilities=[NativeTool(...)]` 配置[原生工具](native-tools.md)，可将它们作为 UI 中的选项暴露出来（仅对支持相应工具的模型显示）：

```python
from pydantic_ai import Agent
from pydantic_ai.capabilities import NativeTool
from pydantic_ai.native_tools import CodeExecutionTool, WebSearchTool

agent = Agent(
    'openai:gpt-5.2',
    capabilities=[NativeTool(CodeExecutionTool()), NativeTool(WebSearchTool())],
)

app = agent.to_web(models=['anthropic:claude-sonnet-4-6'])
```

!!! note "Memory Tool 记忆工具"
    `memory` 原生工具不支持通过 `to_web()` 或 `clai web` 使用。如果你的 agent 需要 memory，请在构造 agent 时直接配置 [`MemoryTool`][pydantic_ai.native_tools.MemoryTool]。

## 额外 Instructions

你可以传入额外 instructions，它们会包含在每次 agent run 中：

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

app = agent.to_web(instructions='Always respond in a friendly tone.')
```

## 保留路由

Web UI app 使用以下路由，不应覆盖：

- `/` 和 `/{id}` - 提供 chat UI
- `/api/chat` - 聊天 endpoint（POST、OPTIONS）
- `/api/configure` - 前端配置（GET）
- `/api/health` - 健康检查（GET）

当前 app 不能挂载在子路径（例如 `/chat`），因为 UI 期望这些路由位于根路径。你可以向 app 添加其他路由，但要避免与这些保留路径冲突。

## 自定义 HTML 来源

默认情况下，Web UI 会从 CDN 获取并缓存在本地。你可以提供 `html_source` 来覆盖它，以支持离线使用或企业环境。

离线使用时，请在有网络访问时先下载一次 html 文件：

```python
from pydantic_ai.ui import DEFAULT_HTML_URL

print(DEFAULT_HTML_URL)  # Use this URL to download the UI HTML file
#> https://cdn.jsdelivr.net/npm/@pydantic/ai-chat-ui@1.2.0/dist/index.html
```

然后可以使用上面打印的 URL 下载文件：

```bash
curl -o ~/pydantic-ai-ui.html <chat_ui_url>
```

然后使用 `html_source` 指向本地文件或自定义 URL：

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

# Use a local file (e.g., for offline usage)
app = agent.to_web(html_source='~/pydantic-ai-ui.html')

# Or use a custom URL (e.g., for enterprise environments)
app = agent.to_web(html_source='https://cdn.example.com/ui/index.html')
```
