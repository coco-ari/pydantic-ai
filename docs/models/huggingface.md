# Hugging Face

[Hugging Face](https://huggingface.co/) 是一个 AI 平台，包含主流开源模型、数据集、MCPs 和 demos。你可以使用 [Inference Providers](https://huggingface.co/docs/inference-providers)，在可扩展的 serverless 基础设施上运行 DeepSeek R1 等开源模型。

!!! tip "通过 Sentence Transformers 使用本地 embeddings"
    本页介绍通过 Hugging Face Inference Providers 使用 chat completions。若要在本地运行 Hugging Face **embedding** 模型（无需 API key，也不会发起网络调用），请参见 [Sentence Transformers embedding model](../embeddings.md#sentence-transformers-local)，它适用于 [sentence-transformers library](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html) 中的任何模型。

## 安装 {#install}

要使用 `HuggingFaceModel`，你需要安装 `pydantic-ai`，或者安装带有 `huggingface` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[huggingface]"
```

## 配置 {#configuration}

要使用 [Hugging Face](https://huggingface.co/) inference，你需要设置一个账号，该账号会为 [Inference Providers](https://huggingface.co/docs/inference-providers) 提供[免费层级](https://huggingface.co/docs/inference-providers/pricing)额度。按以下步骤设置 inference：

1. 前往 [Hugging Face](https://huggingface.co/join) 注册账号。
2. 在 [Hugging Face](https://huggingface.co/settings/tokens) 创建新的 access token。
3. 将 `HF_TOKEN` 环境变量设置为刚创建的 token。

拿到 Hugging Face access token 后，可以将它设置为环境变量：

```bash
export HF_TOKEN='hf_token'
```

## 用法 {#usage}

随后你可以按名称使用 [`HuggingFaceModel`][pydantic_ai.models.huggingface.HuggingFaceModel]：

```python
from pydantic_ai import Agent

agent = Agent('huggingface:Qwen/Qwen3-235B-A22B')
...
```

也可以只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.huggingface import HuggingFaceModel

model = HuggingFaceModel('Qwen/Qwen3-235B-A22B')
agent = Agent(model)
...
```

默认情况下，[`HuggingFaceModel`][pydantic_ai.models.huggingface.HuggingFaceModel] 使用 [`HuggingFaceProvider`][pydantic_ai.providers.huggingface.HuggingFaceProvider]，它会按照你在 <https://hf.co/settings/inference-providers> 中设置的偏好顺序，自动选择该模型可用的第一个 inference provider（Cerebras、Together AI、Cohere 等）。

## 配置 provider {#configure-the-provider}

如果你想在代码中向 provider 传递参数，可以通过程序实例化 [`HuggingFaceProvider`][pydantic_ai.providers.huggingface.HuggingFaceProvider] 并传给模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.huggingface import HuggingFaceModel
from pydantic_ai.providers.huggingface import HuggingFaceProvider

model = HuggingFaceModel('Qwen/Qwen3-235B-A22B', provider=HuggingFaceProvider(api_key='hf_token', provider_name='nebius'))
agent = Agent(model)
...
```

## 自定义 Hugging Face client {#custom-hugging-face-client}

[`HuggingFaceProvider`][pydantic_ai.providers.huggingface.HuggingFaceProvider] 还接受通过 `hf_client` 参数传入的自定义 [`AsyncInferenceClient`](https://huggingface.co/docs/huggingface_hub/v0.29.3/en/package_reference/inference_client#huggingface_hub.AsyncInferenceClient) client，因此你可以按照 [Hugging Face Hub python library 文档](https://huggingface.co/docs/huggingface_hub/package_reference/inference_client)中的定义，自定义 `headers`、`bill_to`（向你所属的 HF 组织计费）、`base_url` 等。

```python
from huggingface_hub import AsyncInferenceClient

from pydantic_ai import Agent
from pydantic_ai.models.huggingface import HuggingFaceModel
from pydantic_ai.providers.huggingface import HuggingFaceProvider

client = AsyncInferenceClient(
    bill_to='openai',
    api_key='hf_token',
    provider='fireworks-ai',
)

model = HuggingFaceModel(
    'Qwen/Qwen3-235B-A22B',
    provider=HuggingFaceProvider(hf_client=client),
)
agent = Agent(model)
...
```

## 流式取消 {#streaming-cancellation}

!!! warning "取消限制"
    `huggingface_hub.AsyncInferenceClient` 只以 async iterator 形式暴露流式响应，没有单独的 handle 用于关闭底层 HTTP transport。由于 [Python 关于 async generators 的语言规则](https://peps.python.org/pep-0525/)，当另一个 coroutine 正在迭代 stream 时，[`cancel()`][pydantic_ai.result.StreamedRunResult.cancel] 无法中断正在进行的 chunk 读取。Pydantic AI 会用 `state='interrupted'` 标记响应，但上游生成可能会持续到外围的 `async with agent.run_stream(...)` 代码块退出。

    若要可靠取消，请向 [`stream_text()`][pydantic_ai.result.StreamedRunResult.stream_text]、[`stream_output()`][pydantic_ai.result.StreamedRunResult.stream_output] 或 [`stream_response()`][pydantic_ai.result.StreamedRunResult.stream_response] 传入 `debounce_by=None`，并从正在迭代的同一个 task 中调用 `cancel()`：

    ```python {title="cancel_huggingface.py" test="skip"}
    from pydantic_ai import Agent

    agent = Agent('huggingface:Qwen/Qwen3-235B-A22B')


    def should_stop(chunk: str) -> bool:
        return len(chunk) > 100


    async def main():
        async with agent.run_stream('Write a long essay about Python') as result:
            async for chunk in result.stream_text(debounce_by=None):
                if should_stop(chunk):
                    await result.cancel()
                    break
    ```

    或者，如果需要保留 debouncing，请用 [`contextlib.aclosing`](https://docs.python.org/3/library/contextlib.html#contextlib.aclosing) 包装 stream，让 iterator 在 `cancel()` 运行前关闭：

    ```python {title="cancel_huggingface_aclosing.py" test="skip"}
    from contextlib import aclosing

    from pydantic_ai import Agent

    agent = Agent('huggingface:Qwen/Qwen3-235B-A22B')


    def should_stop(chunk: str) -> bool:
        return len(chunk) > 100


    async def main():
        async with agent.run_stream('Write a long essay about Python') as result:
            async with aclosing(result.stream_text()) as stream:
                async for chunk in stream:
                    if should_stop(chunk):
                        break
            await result.cancel()
    ```

    在迭代进行期间从另一个 task 调用 `cancel()`，目前在此 provider 上并不可靠。
