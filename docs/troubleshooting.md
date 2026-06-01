# 故障排查

下面是一些修复 Pydantic AI 使用过程中常见错误的建议。如果你遇到的问题没有列在下面，也没有在文档中说明，欢迎在 [Pydantic Slack](help.md) 提问，或在 [GitHub](https://github.com/pydantic/pydantic-ai/issues) 创建 issue。

## Jupyter Notebook 错误

### `RuntimeError: This event loop is already running`

**现代 Jupyter/IPython（7.0+）**：这个环境原生支持顶层 `await`。你可以直接在 notebook cell 中使用 [`Agent.run()`][pydantic_ai.agent.Agent.run]，无需额外设置：

```python {test="skip" lint="skip"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')
result = await agent.run('Who let the dogs out?')
```

**旧环境或特定集成**：如果遇到 event loop 冲突，请使用 [`nest-asyncio`](https://pypi.org/project/nest-asyncio/)：

```python {test="skip"}
import nest_asyncio

from pydantic_ai import Agent

nest_asyncio.apply()

agent = Agent('openai:gpt-5.2')
result = agent.run_sync('Who let the dogs out?')
```

**注意**：这也适用于 Google Colab 和 [Marimo](https://github.com/marimo-team/marimo) 环境。

## API Key 配置

### `UserError: API key must be provided or set in the [MODEL]_API_KEY environment variable`

如果你在为模型设置 API key 时遇到问题，请访问 [Models](models/overview.md) 页面，了解如何设置环境变量和/或传入 `api_key` 参数。

## 监控 HTTPX 请求

你可以在模型中使用自定义 `httpx` clients，以便在运行时访问具体请求、响应和 headers。

使用 `logfire` 的 [HTTPX integration](logfire.md#monitoring-http-requests) 监控上述内容会特别有帮助。
