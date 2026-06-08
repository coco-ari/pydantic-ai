# Ollama

## 安装

要使用 [`OllamaModel`][pydantic_ai.models.ollama.OllamaModel]，你需要安装 `pydantic-ai`，或安装带 `openai` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[openai]"
```

## 配置

Pydantic AI 同时支持自托管的 [Ollama](https://ollama.com/) 服务器（本地或远程运行）和 [Ollama Cloud](https://ollama.com/cloud)。

对于本地运行的服务器，请使用 `http://localhost:11434/v1` base URL。对于 Ollama Cloud，请使用 `https://ollama.com/v1`，并确保已设置 API key。

为保持向后兼容，[`OllamaModel`][pydantic_ai.models.ollama.OllamaModel] 使用 Ollama 兼容 OpenAI 的 Chat Completions API（`/v1/chat/completions`）。

## 环境变量

设置 `OLLAMA_BASE_URL` 和（可选的）`OLLAMA_API_KEY` 环境变量：

```bash
export OLLAMA_BASE_URL='http://localhost:11434/v1'
export OLLAMA_API_KEY='your-api-key'  # required for Ollama Cloud
```

然后你可以通过名称使用 `OllamaModel`：

```python
from pydantic_ai import Agent

agent = Agent('ollama:qwen3')
...
```

也可以只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel

model = OllamaModel('qwen3')
agent = Agent(model)
...
```

## `provider` 参数

你可以通过 `provider` 参数提供自定义 `Provider`：

```python
from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

model = OllamaModel(
    'qwen3', provider=OllamaProvider(base_url='http://localhost:11434/v1')
)
agent = Agent(model)
...
```

对于 Ollama Cloud，请使用 `base_url='https://ollama.com/v1'` 并设置 `OLLAMA_API_KEY` 环境变量（或直接传入 `api_key=`）。

## 结构化输出

自托管 Ollama（v0.5.0+，发布于 2024 年 12 月）会通过 `llama.cpp` 的语法约束解码器强制执行带 `json_schema` 的 `response_format`，因此 [`NativeOutput`][pydantic_ai.output.NativeOutput] 会在生成时产出符合 schema 的输出：

```python
from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.output import NativeOutput
from pydantic_ai.providers.ollama import OllamaProvider


class CityLocation(BaseModel):
    city: str
    country: str


model = OllamaModel(
    'qwen3',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)
agent = Agent(model, output_type=NativeOutput(CityLocation))
...
```

!!! note "Ollama Cloud 尚未强制执行 `json_schema`"
    Ollama Cloud 的推理后端会接受带 `json_schema` 的 `response_format` 且不报错，但不会应用语法约束解码，因此 schema 实际上不会被强制执行。上游跟踪 issue 请参见 [ollama/ollama#12362](https://github.com/ollama/ollama/issues/12362)。

    当 [`OllamaModel`][pydantic_ai.models.ollama.OllamaModel] 检测到 Cloud 路径（即 `ollama.com` 上的 `base_url`，或以 `-cloud` 结尾的模型名称）时，它会自动在 profile 上禁用 `supports_json_schema_output`。

    如果你将 [`NativeOutput`][pydantic_ai.output.NativeOutput] 与 Ollama Cloud 模型一起使用，会得到清晰的 [`UserError`][pydantic_ai.exceptions.UserError]，而不是静默重试循环。请改用默认的 [`ToolOutput`][pydantic_ai.output.ToolOutput] 或 [`PromptedOutput`][pydantic_ai.output.PromptedOutput]，两者都可在 Cloud 上工作。
