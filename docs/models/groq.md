# Groq

## 安装

要使用 `GroqModel`，你需要安装 `pydantic-ai`，或安装带 `groq` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[groq]"
```

## 配置

要通过 API 使用 [Groq](https://groq.com/)，请前往 [console.groq.com/keys](https://console.groq.com/keys)，按页面指引生成 API key。

`GroqModelName` 包含可用 Groq 模型的列表。

## 环境变量

获得 API key 后，可以将其设置为环境变量：

```bash
export GROQ_API_KEY='your-api-key'
```

然后你可以通过名称使用 `GroqModel`：

```python
from pydantic_ai import Agent

agent = Agent('groq:llama-3.3-70b-versatile')
...
```

也可以只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

model = GroqModel('llama-3.3-70b-versatile')
agent = Agent(model)
...
```

## `provider` 参数

你可以通过 `provider` 参数提供自定义 `Provider`：

```python
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

model = GroqModel(
    'llama-3.3-70b-versatile', provider=GroqProvider(api_key='your-api-key')
)
agent = Agent(model)
...
```

也可以使用自定义 `httpx.AsyncClient` 来定制 `GroqProvider`：

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

custom_http_client = AsyncClient(timeout=30)
model = GroqModel(
    'llama-3.3-70b-versatile',
    provider=GroqProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```
