# Cohere

## 安装

要使用 `CohereModel`，你需要安装 `pydantic-ai`，或安装带 `cohere` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[cohere]"
```

## 配置

要通过 API 使用 [Cohere](https://cohere.com/)，请前往 [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)，按页面指引生成 API key。

`CohereModelName` 包含最常用 Cohere 模型的列表。

## 环境变量

获得 API key 后，可以将其设置为环境变量：

```bash
export CO_API_KEY='your-api-key'
```

然后你可以通过名称使用 `CohereModel`：

```python
from pydantic_ai import Agent

agent = Agent('cohere:command-r7b-12-2024')
...
```

也可以只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.cohere import CohereModel

model = CohereModel('command-r7b-12-2024')
agent = Agent(model)
...
```

## `provider` 参数

你可以通过 `provider` 参数提供自定义 `Provider`：

```python
from pydantic_ai import Agent
from pydantic_ai.models.cohere import CohereModel
from pydantic_ai.providers.cohere import CohereProvider

model = CohereModel('command-r7b-12-2024', provider=CohereProvider(api_key='your-api-key'))
agent = Agent(model)
...
```

也可以使用自定义 `http_client` 来定制 `CohereProvider`：

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.cohere import CohereModel
from pydantic_ai.providers.cohere import CohereProvider

custom_http_client = AsyncClient(timeout=30)
model = CohereModel(
    'command-r7b-12-2024',
    provider=CohereProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```
