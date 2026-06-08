# Cerebras

## 安装

要使用 `CerebrasModel`，你需要安装 `pydantic-ai`，或安装带 `cerebras` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[cerebras]"
```

## 配置

要通过 API 使用 [Cerebras](https://cerebras.ai/)，请前往 [cloud.cerebras.ai](https://cloud.cerebras.ai/?utm_source=3pi_pydantic-ai&utm_campaign=partner_doc) 并生成 API key。

可用模型列表请参见 [Cerebras 模型文档](https://inference-docs.cerebras.ai/models)。

## 环境变量

获得 API key 后，可以将其设置为环境变量：

```bash
export CEREBRAS_API_KEY='your-api-key'
```

然后你可以通过名称使用 `CerebrasModel`：

```python
from pydantic_ai import Agent

agent = Agent('cerebras:llama-3.3-70b')
...
```

也可以只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.cerebras import CerebrasModel

model = CerebrasModel('llama-3.3-70b')
agent = Agent(model)
...
```

## `provider` 参数

你可以通过 `provider` 参数提供自定义 `Provider`：

```python
from pydantic_ai import Agent
from pydantic_ai.models.cerebras import CerebrasModel
from pydantic_ai.providers.cerebras import CerebrasProvider

model = CerebrasModel(
    'llama-3.3-70b', provider=CerebrasProvider(api_key='your-api-key')
)
agent = Agent(model)
...
```

也可以使用自定义 `httpx.AsyncClient` 来定制 `CerebrasProvider`：

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.cerebras import CerebrasModel
from pydantic_ai.providers.cerebras import CerebrasProvider

custom_http_client = AsyncClient(timeout=30)
model = CerebrasModel(
    'llama-3.3-70b',
    provider=CerebrasProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```
