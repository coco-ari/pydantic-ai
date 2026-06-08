# Mistral

## 安装

要使用 `MistralModel`，你需要安装 `pydantic-ai`，或安装带 `mistral` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[mistral]"
```

## 配置

要通过 API 使用 [Mistral](https://mistral.ai)，请前往 [console.mistral.ai/api-keys/](https://console.mistral.ai/api-keys/)，按页面指引生成 API key。

`LatestMistralModelNames` 包含最常用 Mistral 模型的列表。

## 环境变量

获得 API key 后，可以将其设置为环境变量：

```bash
export MISTRAL_API_KEY='your-api-key'
```

然后你可以通过名称使用 `MistralModel`：

```python
from pydantic_ai import Agent

agent = Agent('mistral:mistral-large-latest')
...
```

也可以只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel

model = MistralModel('mistral-small-latest')
agent = Agent(model)
...
```

## `provider` 参数

你可以通过 `provider` 参数提供自定义 `Provider`：

```python
from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

model = MistralModel(
    'mistral-large-latest', provider=MistralProvider(api_key='your-api-key', base_url='https://<mistral-provider-endpoint>')
)
agent = Agent(model)
...
```

也可以使用自定义 `httpx.AsyncClient` 来定制 provider：

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider

custom_http_client = AsyncClient(timeout=30)
model = MistralModel(
    'mistral-large-latest',
    provider=MistralProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```
