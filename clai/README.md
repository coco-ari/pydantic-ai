# clai

[![CI](https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml/badge.svg?event=push)](https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml?query=branch%3Amain)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic-ai.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/pydantic/pydantic-ai)
[![PyPI](https://img.shields.io/pypi/v/clai.svg)](https://pypi.python.org/pypi/clai)
[![versions](https://img.shields.io/pypi/pyversions/clai.svg)](https://github.com/pydantic/pydantic-ai)
[![license](https://img.shields.io/github/license/pydantic/pydantic-ai.svg?v)](https://github.com/pydantic/pydantic-ai/blob/main/LICENSE)

（发音为 "clay"）

用于与 LLM 聊天的命令行界面，是 [Pydantic AI 项目](https://github.com/pydantic/pydantic-ai)的一部分。

## 使用

<!-- Keep this in sync with docs/cli.md -->

你需要根据打算使用的提供商设置一个环境变量。

例如，如果你使用 OpenAI，请设置 `OPENAI_API_KEY` 环境变量：

```bash
export OPENAI_API_KEY='your-api-key-here'
```

然后使用 [`uvx`](https://docs.astral.sh/uv/guides/tools/) 运行：

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

无论哪种方式，运行 `clai` 都会启动一个交互式会话，你可以在其中与 AI 模型聊天。交互模式中可用的特殊命令：

- `/exit`：退出会话
- `/markdown`：以 Markdown 格式显示上一条响应
- `/multiline`：切换多行输入模式（使用 Ctrl+D 提交）
- `/cp`：将上一条响应复制到剪贴板

## 帮助

```
usage: clai [-h] [-l] [--version] [-m MODEL] [-a AGENT] [-t CODE_THEME] [--no-stream] [prompt]

Pydantic AI CLI v...

subcommands:
  web           Start a web-based chat interface for an agent
                Run "clai web --help" for more information

positional arguments:
  prompt                AI prompt for one-shot mode. If omitted, starts interactive mode.

options:
  -h, --help            show this help message and exit
  -l, --list-models     List all available models and exit
  --version             Show version and exit
  -m MODEL, --model MODEL
                        Model to use, in format "<provider>:<model>" e.g. "openai:gpt-5" or "anthropic:claude-sonnet-4-6". Defaults to "openai-chat:gpt-5".
  -a AGENT, --agent AGENT
                        Custom Agent to use: a module path like "module:variable" or a YAML/JSON spec file like "agent.yml"
  -t CODE_THEME, --code-theme CODE_THEME
                        Which colors to use for code, can be "dark", "light" or any theme from pygments.org/styles/. Defaults to "dark" which works well on dark terminals.
  --no-stream           Disable streaming from the model
```

关于如何使用它的更多信息，请参见 [CLI 文档](https://ai.pydantic.dev/cli/)。

## Web Chat UI

启动基于 Web 的聊天界面：

```bash
clai web -m openai:gpt-5.2
```

![Web Chat UI](https://ai.pydantic.dev/img/web-chat-ui.png)

这会启动一个带聊天界面的 Web 服务器（默认地址：http://127.0.0.1:7932）。

你也可以托管已有智能体。例如，如果你在 `my_agent.py` 中定义了一个智能体：

```python
from pydantic_ai import Agent

my_agent = Agent('openai:gpt-5.2', instructions='You are a helpful assistant.')
```

使用以下命令启动 Web UI：

```bash
clai web --agent my_agent:my_agent
```

完整的 Web UI 文档见 [Web Chat UI](https://ai.pydantic.dev/web/)。
