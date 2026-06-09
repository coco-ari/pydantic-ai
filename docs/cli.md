# 命令行界面（CLI）

**Pydantic AI** 附带一个 CLI：`clai`（发音为 "clay"）。你可以直接从命令行用它与各种 LLM 聊天并快速获得答案，也可以启动 uvicorn server，通过浏览器与你的 Pydantic AI agents 聊天。

## 安装

你可以使用 [`uvx`](https://docs.astral.sh/uv/guides/tools/) 运行 `clai`：

```bash
uvx clai
```

或者[使用 `uv`](https://docs.astral.sh/uv/guides/tools/#installing-tools) 全局安装 `clai`：

```bash
uv tool install clai
...
clai
```

或者使用 `pip`：

```bash
pip install clai
...
clai
```

## CLI 用法

<!-- clai/README.md 在这里链接完整文档 -->

你需要根据打算使用的 provider 设置一个环境变量。

例如，如果你使用 OpenAI，请设置 `OPENAI_API_KEY` 环境变量：

```bash
export OPENAI_API_KEY='your-api-key-here'
```

然后运行 `clai` 会启动一个交互式会话，你可以在其中与 AI 模型聊天。交互模式中可用的特殊命令：

- `/exit`：退出会话
- `/markdown`：以 Markdown 格式显示上一条响应
- `/multiline`：切换多行输入模式（使用 Ctrl+D 提交）
- `/cp`：将上一条响应复制到剪贴板

### CLI 选项

| 选项 | 说明 |
|--------|------|
| `prompt` | one-shot 模式的 AI prompt（位置参数）。省略时启动交互模式。 |
| `-m`, `--model` | 要使用的模型，格式为 `provider:model`（例如 `openai:gpt-5.2`） |
| `-a`, `--agent` | `module:variable` 格式的自定义 agent |
| `-t`, `--code-theme` | 语法高亮主题（`dark`、`light` 或 [pygments theme](https://pygments.org/styles/)） |
| `--no-stream` | 禁用模型流式输出 |
| `-l`, `--list-models` | 列出所有可用模型并退出 |
| `--version` | 显示版本并退出 |

### 选择模型

你可以用 `--model` 标志指定要使用的模型：

```bash
clai --model anthropic:claude-sonnet-4-6
```

（可用模型的完整列表可以通过 `clai --list-models` 打印。）

### 自定义 Agents {#自定义-agents}

你可以使用 `--agent` 标志，通过模块路径和变量名指定自定义 agent：

```python {title="custom_agent.py" test="skip"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='You always respond in Italian.')
```

然后运行：

```bash
clai --agent custom_agent:agent "What's the weather today?"
```

格式必须是 `module:variable`，其中：

- `module` 是可导入的 Python module path
- `variable` 是该模块中 Agent 实例的名称

此外，你可以使用 `Agent.to_cli_sync()` 从 `Agent` 实例直接启动 CLI 模式：

```python {title="agent_to_cli_sync.py" test="skip" hl_lines=4}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='You always respond in Italian.')
agent.to_cli_sync()
```

你也可以使用 async 接口 `Agent.to_cli()`：

```python {title="agent_to_cli.py" test="skip" hl_lines=6}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='You always respond in Italian.')

async def main():
    await agent.to_cli()
```

_（你需要添加 `asyncio.run(main())` 来运行 `main`。）_

### 消息历史 {#message-history}

`Agent.to_cli()` 和 `Agent.to_cli_sync()` 都支持 `message_history` 参数，允许你继续现有对话或提供对话上下文：

```python {title="agent_with_history.py" test="skip"}
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

agent = Agent('openai:gpt-5.2')

# Create some conversation history
message_history: list[ModelMessage] = [
    ModelRequest([UserPromptPart(content='What is 2+2?')]),
    ModelResponse([TextPart(content='2+2 equals 4.')])
]

# Start CLI with existing conversation context
agent.to_cli_sync(message_history=message_history)
```

CLI 会从提供的对话历史开始，让 agent 能在整个会话中引用之前的交流并保持上下文。

## Web 聊天界面 {#web-chat-ui}

运行以下命令启动基于 Web 的聊天界面：

```bash
clai web -m openai:gpt-5.2
```

这会启动一个带聊天界面的 Web server（默认：http://127.0.0.1:7932）。

你也可以托管已有 agent。例如，如果你在 `my_agent.py` 中定义了一个 agent：

```python
from pydantic_ai import Agent

my_agent = Agent('openai:gpt-5.2', instructions='You are a helpful assistant.')
```

启动 Web UI：

```bash
# With a custom agent
clai web --agent my_module:my_agent

# With specific models (first is default when no --agent)
clai web -m openai:gpt-5.2 -m anthropic:claude-sonnet-4-6

# With native tools
clai web -m openai:gpt-5.2 -t web_search -t code_execution

# Generic agent with system instructions
clai web -m openai:gpt-5.2 -i 'You are a helpful coding assistant'

# Custom agent with extra instructions for each run
clai web --agent my_module:my_agent -i 'Always respond in Spanish'
```

!!! note "内存工具"
    [`memory`](native-tools.md#memory-tool) 原生工具不能通过 `-t memory` 启用。如果你的 agent 需要 memory，请直接在 agent 上配置 [`MemoryTool`][pydantic_ai.native_tools.MemoryTool] 并通过 `--agent` 提供它。

### Web UI 选项

| 选项 | 说明 |
|--------|------|
| `--agent`, `-a` | 要托管的 agent，使用 [`module:variable` 格式](#自定义-agents) |
| `--model`, `-m` | 在 UI 中列为选项的模型（可重复） |
| `--tool`, `-t` | 在 UI 中列为选项的[原生工具](native-tools.md)（可重复）。参见[可用工具](web.md#native-tool-support)。 |
| `--instructions`, `-i` | System instructions。指定 `--agent` 时，这些会追加到 agent 现有 instructions。 |
| `--host` | server 绑定的 host（默认：127.0.0.1） |
| `--port` | server 绑定的 port（默认：7932） |
| `--html-source` | chat UI HTML 的 URL 或文件路径。 |

使用 `--agent` 时，agent 配置的模型会成为默认模型。CLI models（`-m`）是额外选项。不使用 `--agent` 时，第一个 `-m` 模型是默认模型。

Web chat UI 也可以用 [`Agent.to_web()`][pydantic_ai.agent.Agent.to_web] 以编程方式启动；参见 [Web UI 文档](web.md)。

运行带 `--help` 的 `web` 命令查看所有可用选项：

```bash
clai web --help
```
