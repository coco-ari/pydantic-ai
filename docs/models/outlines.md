# Outlines

!!! warning "已弃用"
    [`OutlinesModel`][pydantic_ai.models.outlines.OutlinesModel] 已弃用，并将在 Pydantic AI v2 中移除。

    如果你希望继续将 Outlines 与 Pydantic AI 一起使用，请在 <https://github.com/dottxt-ai/outlines/issues> 提交 issue。

## 安装 {#install}

Outlines 是一个允许你运行来自多个不同 providers 的模型的库，因此默认不包含任何 provider 所需的依赖。因此，要使用 [`OutlinesModel`][pydantic_ai.models.outlines.OutlinesModel]，必须安装带可选组的 `pydantic-ai-slim`；该可选组由 outlines、短横线以及你会通过 Outlines 使用的具体 model provider 名称组成。例如：

```bash
pip/uv-add "pydantic-ai-slim[outlines-transformers]"
```

或：

```bash
pip/uv-add "pydantic-ai-slim[outlines-mlxlm]"
```

通过 Outlines 支持的 5 个 model providers 分别有 5 个可选组：

- `outlines-transformers`
- `outlines-llamacpp`
- `outlines-mlxlm`
- `outlines-sglang`
- `outlines-vllm-offline`

## 模型初始化 {#model-initialization}

Outlines 不是 inference provider，而是一个让你运行本地模型和基于 API 的模型的库，因此实例化模型的方式与 Pydantic AI 中其他可用模型略有不同。

要通过 `__init__` 方法初始化 `OutlinesModel`，你提供的第一个参数必须是 `outlines.Model` 或 `outlines.AsyncModel` 实例。

例如：

```python {test="skip"}
import outlines
from transformers import AutoModelForCausalLM, AutoTokenizer

from pydantic_ai.models.outlines import OutlinesModel

outlines_model = outlines.from_transformers(
    AutoModelForCausalLM.from_pretrained('erwanf/gpt2-mini'),
    AutoTokenizer.from_pretrained('erwanf/gpt2-mini')
)
model = OutlinesModel(outlines_model)
```

由于你已经提供了 Outlines model 实例，因此不需要自己提供 `OutlinesProvider`。

### 模型加载方法 {#model-loading-methods}

或者，你可以使用一些 `OutlinesModel` 类方法，直接加载特定类型的 Outlines model。为此，你必须传入与对应 Outlines model 加载函数相同的参数（SGLang 除外）。

Pydantic AI 集成中正式支持 5 种 Outlines models，并为它们提供了对应方法：

- [`from_transformers`][pydantic_ai.models.outlines.OutlinesModel.from_transformers]
- [`from_llamacpp`][pydantic_ai.models.outlines.OutlinesModel.from_llamacpp]
- [`from_mlxlm`][pydantic_ai.models.outlines.OutlinesModel.from_mlxlm]
- [`from_sglang`][pydantic_ai.models.outlines.OutlinesModel.from_sglang]
- [`from_vllm_offline`][pydantic_ai.models.outlines.OutlinesModel.from_vllm_offline]

#### Transformers

```python {test="skip"}
from transformers import AutoModelForCausalLM, AutoTokenizer

from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_transformers(
    AutoModelForCausalLM.from_pretrained('microsoft/Phi-3-mini-4k-instruct'),
    AutoTokenizer.from_pretrained('microsoft/Phi-3-mini-4k-instruct')
)
```

#### LlamaCpp

```python {test="skip"}
from llama_cpp import Llama

from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_llamacpp(
    Llama.from_pretrained(
        repo_id='TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
        filename='mistral-7b-instruct-v0.2.Q5_K_M.gguf',
    )
)
```

#### MLXLM

```python {test="skip"}
from mlx_lm import load

from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_mlxlm(
    *load('mlx-community/TinyLlama-1.1B-Chat-v1.0-4bit')
)
```

#### SGLang

```python {test="skip"}
from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_sglang(
    'http://localhost:11434',
    'api_key',
    'meta-llama/Llama-3.1-8B'
)
```

#### vLLM Offline

```python {test="skip"}
from vllm import LLM

from pydantic_ai.models.outlines import OutlinesModel

model = OutlinesModel.from_vllm_offline(
    LLM('microsoft/Phi-3-mini-4k-instruct')
)
```

## 运行模型 {#running-the-model}

初始化 `OutlinesModel` 后，可以像使用其他 Pydantic AI models 一样，将它与 Agent 一起使用。

由于 Outlines 专注于 structured output，此 provider 通过 [`NativeOutput`][pydantic_ai.output.NativeOutput] 格式支持 `output_type` 组件。你不需要在 prompt 中包含所需 output 格式的信息；基于 `output_type` 的 instructions 会自动包含。

```python {test="skip"}
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.outlines import OutlinesModel


class Box(BaseModel):
    """Class representing a box"""
    width: int
    height: int
    depth: int
    units: str

model = OutlinesModel.from_transformers(
    AutoModelForCausalLM.from_pretrained('microsoft/Phi-3-mini-4k-instruct'),
    AutoTokenizer.from_pretrained('microsoft/Phi-3-mini-4k-instruct')
)
agent = Agent(model, output_type=Box)

result = agent.run_sync(
    'Give me the dimensions of a box',
    model_settings=ModelSettings(extra_body={'max_new_tokens': 100})
)
print(result.output) # width=20 height=30 depth=40 units='cm'
```

Outlines 还不支持 tools，但未来会添加对此功能的支持。

## 多模态模型 {#multimodal-models}

如果通过 Outlines 运行的模型和所选 provider 支持，你可以用 [`ImageUrl`][pydantic_ai.messages.ImageUrl] 或 [`BinaryImage`][pydantic_ai.messages.BinaryImage] 在 prompts 中包含图片。在这种情况下，运行 agent 时提供的 prompt 应该是一个包含字符串以及一张或多张图片的列表。关于在 model inputs 中使用 assets 的细节和示例，请参见 [input 文档](../input.md)。

Outlines 中的 `SGLang` 和 `Transformers` models 支持此功能。如果你想通过 `transformers` 运行多模态模型，在用 `OutlinesModel.from_transformers` 方法初始化模型时，第二个参数必须提供 processor，而不是 tokenizer。

```python {test="skip"}
from datetime import date
from typing import Literal

import torch
from pydantic import BaseModel
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

from pydantic_ai import Agent, ModelSettings
from pydantic_ai.messages import ImageUrl
from pydantic_ai.models.outlines import OutlinesModel

MODEL_NAME = 'Qwen/Qwen2-VL-7B-Instruct'

class Item(BaseModel):
    name: str
    quantity: int | None
    price_per_unit: float | None
    total_price: float | None

class ReceiptSummary(BaseModel):
    store_name: str
    store_address: str
    store_number: int | None
    items: list[Item]
    tax: float | None
    total: float | None
    date: date
    payment_method: Literal['cash', 'credit', 'debit', 'check', 'other']

tf_model = Qwen2VLForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    device_map='auto',
    dtype=torch.bfloat16
)
tf_processor = AutoProcessor.from_pretrained(
    MODEL_NAME,
    device_map='auto'
)
model = OutlinesModel.from_transformers(tf_model, tf_processor)

agent = Agent(model, output_type=ReceiptSummary)

result = agent.run_sync(
    [
        'You are an expert at extracting information from receipts. Please extract the information from the receipt. Be as detailed as possible, do not miss any information',
        ImageUrl('https://raw.githubusercontent.com/dottxt-ai/outlines/refs/heads/main/docs/examples/images/trader-joes-receipt.jpg')
    ],
    model_settings=ModelSettings(extra_body={'max_new_tokens': 1000})
)
print(result.output)
# store_name="Trader Joe's"
# store_address='401 Bay Street, San Francisco, CA 94133'
# store_number=0
# items=[
#   Item(name='BANANA EACH', quantity=7, price_per_unit=0.23, total_price=1.61),
#   Item(name='BAREBELLS CHOCOLATE DOUG',quantity=1, price_per_unit=2.29, total_price=2.29),
#   Item(name='BAREBELLS CREAMY CRISP', quantity=1, price_per_unit=2.29, total_price=2.29),
#   Item(name='BAREBELLS CHOCOLATE DOUG', quantity=1, price_per_unit=2.29, total_price=2.29),
#   Item(name='BAREBELLS CARAMEL CASHEW', quantity=2, price_per_unit=2.29, total_price=4.58),
#   Item(name='BAREBELLS CREAMY CRISP', quantity=1, price_per_unit=2.29, total_price=2.29),
#   Item(name='T SPINDRIFT ORANGE MANGO 8', quantity=1, price_per_unit=7.49, total_price=7.49),
#   Item(name='T Bottle Deposit', quantity=8, price_per_unit=0.05, total_price=0.4),
#   Item(name='MILK ORGANIC GALLON WHOL', quantity=1, price_per_unit=6.79, total_price=6.79),
#   Item(name='CLASSIC GREEK SALAD', quantity=1, price_per_unit=3.49, total_price=3.49),
#   Item(name='COBB SALAD', quantity=1, price_per_unit=5.99, total_price=5.99),
#   Item(name='PEPPER BELL RED XL EACH', quantity=1, price_per_unit=1.29, total_price=1.29),
#   Item(name='BAG FEE.', quantity=1, price_per_unit=0.25, total_price=0.25),
#   Item(name='BAG FEE.', quantity=1, price_per_unit=0.25, total_price=0.25)]
# tax=7.89
# total=41.98
# date='2023-04-01'
# payment_method='credit'

```
