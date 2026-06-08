# OpenRouter

## 安装

要使用 `OpenRouterModel`，你需要安装 `pydantic-ai`，或安装带 `openrouter` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[openrouter]"
```

## 配置

要使用 [OpenRouter](https://openrouter.ai)，请先在 [openrouter.ai/keys](https://openrouter.ai/keys) 创建 API key。

你可以设置 `OPENROUTER_API_KEY` 环境变量，并通过名称使用 [`OpenRouterProvider`][pydantic_ai.providers.openrouter.OpenRouterProvider]：

```python
from pydantic_ai import Agent

agent = Agent('openrouter:anthropic/claude-sonnet-4-5')
...
```

也可以直接初始化模型和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

model = OpenRouterModel(
    'anthropic/claude-sonnet-4-5',
    provider=OpenRouterProvider(api_key='your-openrouter-api-key'),
)
agent = Agent(model)
...
```

## 应用归因

OpenRouter 提供[应用归因](https://openrouter.ai/docs/app-attribution)功能，可在其公开排名和分析中跟踪你的应用。

初始化 provider 时，可以传入 `app_url` 和 `app_title` 来启用应用归因。

```python
from pydantic_ai.providers.openrouter import OpenRouterProvider

provider=OpenRouterProvider(
    api_key='your-openrouter-api-key',
    app_url='https://your-app.com',
    app_title='Your App',
),
...
```

## 模型设置

你可以使用 [`OpenRouterModelSettings`][pydantic_ai.models.openrouter.OpenRouterModelSettings] 自定义模型行为：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings

settings = OpenRouterModelSettings(
    openrouter_reasoning={
        'effort': 'high',
    },
    openrouter_usage={
        'include': True,
    }
)
model = OpenRouterModel('openai/gpt-5.2')
agent = Agent(model, model_settings=settings)
...
```

### 急切输入流式传输

对于通过 OpenRouter 使用的 Anthropic 模型，可以启用急切输入流式传输，以降低大输入工具调用的延迟。
请在 [`AnthropicModelSettings`][pydantic_ai.models.anthropic.AnthropicModelSettings] 中设置 [`anthropic_eager_input_streaming`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_eager_input_streaming]：

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings
from pydantic_ai.models.openrouter import OpenRouterModel

model = OpenRouterModel('anthropic/claude-sonnet-4-5')
settings = AnthropicModelSettings(anthropic_eager_input_streaming=True)
agent = Agent(model, model_settings=settings)
...
```

## 网页搜索

OpenRouter 通过其[插件](https://openrouter.ai/docs/guides/features/plugins/web-search)支持网页搜索。你可以使用 [`WebSearchTool`][pydantic_ai.native_tools.WebSearchTool] 启用它。

### 网页搜索参数

你可以使用 [`WebSearchTool`][pydantic_ai.native_tools.WebSearchTool] 上的 `search_context_size` 参数自定义网页搜索行为：

```python
from pydantic_ai import Agent
from pydantic_ai.capabilities import NativeTool
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.native_tools import WebSearchTool

tool = WebSearchTool(search_context_size='high')
model = OpenRouterModel('openai/gpt-4.1')
agent = Agent(
    model,
    capabilities=[NativeTool(tool)],
)
result = agent.run_sync('What is the latest news in AI?')
```
