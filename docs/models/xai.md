# xAI

## 安装 {#install}

要使用 [`XaiModel`][pydantic_ai.models.xai.XaiModel]，你需要安装 `pydantic-ai`，或者安装带有 `xai` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[xai]"
```

## 配置 {#configuration}

要通过 [xAI](https://x.ai/api) API 使用 xAI models，请前往 [console.x.ai](https://console.x.ai/team/default/api-keys) 创建 API key。

[docs.x.ai](https://docs.x.ai/docs/models) 包含可用 xAI models 列表。

## 环境变量 {#environment-variable}

拿到 API key 后，可以将它设置为环境变量：

```bash
export XAI_API_KEY='your-api-key'
```

随后你可以按名称使用 [`XaiModel`][pydantic_ai.models.xai.XaiModel]：

```python
from pydantic_ai import Agent

agent = Agent('xai:grok-4-1-fast-non-reasoning')
...
```

也可以直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.xai import XaiModel

# 使用 XAI_API_KEY 环境变量
model = XaiModel('grok-4-1-fast-non-reasoning')
agent = Agent(model)
...
```

你也可以用自定义 provider 定制 [`XaiModel`][pydantic_ai.models.xai.XaiModel]：

```python
from pydantic_ai import Agent
from pydantic_ai.models.xai import XaiModel
from pydantic_ai.providers.xai import XaiProvider

# 自定义 API key
provider = XaiProvider(api_key='your-api-key')
model = XaiModel('grok-4-1-fast-non-reasoning', provider=provider)
agent = Agent(model)
...
```

或者使用自定义 `xai_sdk.AsyncClient`：

```python
from xai_sdk import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.xai import XaiModel
from pydantic_ai.providers.xai import XaiProvider

xai_client = AsyncClient(api_key='your-api-key')
provider = XaiProvider(xai_client=xai_client)
model = XaiModel('grok-4-1-fast-non-reasoning', provider=provider)
agent = Agent(model)
...
```

## X Search 搜索 {#x-search}

xAI models 支持搜索 X（原 Twitter）上的实时 posts 和内容。推荐用 [`XSearch`][pydantic_ai.capabilities.XSearch] capability 启用它。更多细节（包括跨 provider 用法）请参见 [capability 文档](../capabilities.md#provider-adaptive-tools)。支持选项的完整列表请参见 [xAI X Search 文档](https://docs.x.ai/developers/tools/x-search)。

```py {title="xai_x_search.py"}
from datetime import datetime

from pydantic_ai import Agent
from pydantic_ai.capabilities import XSearch

agent = Agent(
    'xai:grok-4-1-fast',
    capabilities=[
        XSearch(
            allowed_x_handles=['OpenAI', 'AnthropicAI', 'dasfacc'],
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 12, 31),
            enable_image_understanding=True,
            enable_video_understanding=True,
            include_output=True,
        )
    ],
)

result = agent.run_sync('What have AI companies been posting about?')
print(result.output)
"""
OpenAI announced their latest model updates, while Anthropic shared research on AI safety...
"""
```

_（此示例是完整的，可以"原样"运行）_

`XSearch` capability 接受：

- **`allowed_x_handles`** / **`excluded_x_handles`**：将结果过滤到（或排除）最多 10 个 X handles。二者互斥。
- **`from_date`** / **`to_date`**：将结果限制为给定 datetime 范围内创建的 posts（naive datetimes 会按 UTC 解释）。
- **`enable_image_understanding`**（默认：`False`）：分析 posts 附带的图片。
- **`enable_video_understanding`**（默认：`False`）：分析 posts 附带的视频内容。
- **`include_output`**（默认：`False`）：在可通过 [`ModelResponse.native_tool_calls`][pydantic_ai.messages.ModelResponse.native_tool_calls] 访问的 [`NativeToolReturnPart`][pydantic_ai.messages.NativeToolReturnPart] 上包含原始 X search 结果。若不启用，模型会在内部使用搜索结果，但只返回文本摘要；启用后可以通过程序访问搜索到的 posts、sources 和 metadata。

作为 capability 的替代方案，你可以通过 `capabilities=[NativeTool(XSearchTool(...))]` 直接传入更底层的 [`XSearchTool`][pydantic_ai.native_tools.XSearchTool]（参见 [X Search Tool 文档](../native-tools.md#x-search-tool)），也可以通过 [`XaiModelSettings.xai_include_x_search_output`][pydantic_ai.models.xai.XaiModelSettings.xai_include_x_search_output] [model setting](../agent.md#model-run-settings) 全局启用原始 output。

## 流式取消 {#streaming-cancellation}

!!! warning "取消限制"
    `xai-sdk` SDK 只以 async iterator 形式暴露流式响应，没有单独的 handle 可用于取消底层 gRPC 调用。由于 [Python 关于 async generators 的语言规则](https://peps.python.org/pep-0525/)，当另一个 coroutine 正在迭代 stream 时，[`cancel()`][pydantic_ai.result.StreamedRunResult.cancel] 无法中断正在进行的 chunk 读取。Pydantic AI 会用 `state='interrupted'` 标记响应，但上游生成可能会持续到外围的 `async with agent.run_stream(...)` 代码块退出。

    若要可靠取消，请向 [`stream_text()`][pydantic_ai.result.StreamedRunResult.stream_text]、[`stream_output()`][pydantic_ai.result.StreamedRunResult.stream_output] 或 [`stream_response()`][pydantic_ai.result.StreamedRunResult.stream_response] 传入 `debounce_by=None`，并从正在迭代的同一个 task 中调用 `cancel()`：

    ```python {title="cancel_xai.py" test="skip"}
    from pydantic_ai import Agent

    agent = Agent('xai:grok-4-1-fast-non-reasoning')


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

    ```python {title="cancel_xai_aclosing.py" test="skip"}
    from contextlib import aclosing

    from pydantic_ai import Agent

    agent = Agent('xai:grok-4-1-fast-non-reasoning')


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
