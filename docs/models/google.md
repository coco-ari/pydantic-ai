# Google

`GoogleModel` 是一个底层使用 [`google-genai`](https://pypi.org/project/google-genai/) 包的模型，
可通过 Gemini API 和 Google Cloud（以前称为 Vertex AI）访问 Google 的 Gemini 模型。

两个 provider 会包装这些端点：

- [`GoogleProvider`][pydantic_ai.providers.google.GoogleProvider] - Gemini API（Google AI Studio），通过 `'google:'` 前缀暴露。
- [`GoogleCloudProvider`][pydantic_ai.providers.google_cloud.GoogleCloudProvider] - Google Cloud（以前称为 Vertex AI），通过 `'google-cloud:'` 前缀暴露。

!!! note "已重命名前缀（1.x -> v2）"
    `'google-gla:'` 和 `'google-vertex:'` 前缀在 1.x 中仍可使用，但会发出 `DeprecationWarning`。请改用 `'google:'` 和 `'google-cloud:'`。同样，带有任何仅适用于 Google Cloud 的参数（`vertexai=True`、`location`、`project` 或 `credentials`）的 `GoogleProvider(...)` 已弃用，请改用 `GoogleCloudProvider(...)`。

## 安装

要使用 `GoogleModel`，你需要安装 `pydantic-ai`，或安装带 `google` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[google]"
```


## 配置

`GoogleModel` 允许你通过 [Gemini API](https://ai.google.dev/api/all-methods)（`generativelanguage.googleapis.com`）或 [Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models)（`*-aiplatform.googleapis.com`，以前称为 Vertex AI）使用 Google 的 Gemini 模型。

### API Key（Gemini API）

要通过 Gemini API 使用 Gemini，请前往 [aistudio.google.com](https://aistudio.google.com/apikey) 创建 API key。

取得 API key 后，将其设置为环境变量：

```bash
export GOOGLE_API_KEY=your-api-key
```

然后即可按名称使用 `GoogleModel`：

```python
from pydantic_ai import Agent

agent = Agent('google:gemini-3-pro-preview')
...
```

或者显式创建 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

provider = GoogleProvider(api_key='your-api-key')
model = GoogleModel('gemini-3-pro-preview', provider=provider)
agent = Agent(model)
...
```

### Google Cloud（企业） {#google-cloud-enterprise}

如果你是企业用户，也可以使用 `GoogleModel` 通过 Google Cloud（以前称为 Vertex AI）访问 Gemini。

相比 Gemini API，这个接口有一些优势：

1. Google Cloud API 提供更多企业就绪保障。
2. 你可以通过 Google Cloud [购买预置吞吐量](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput#purchase-provisioned-throughput)来保证容量。
3. 如果你在 Google Cloud 内运行 Pydantic AI，则无需设置身份验证，通常可以"直接工作"。
4. 你可以决定使用哪个区域，这可能对监管合规很重要，也可能改善延迟。

你可以使用[应用默认凭据](https://cloud.google.com/docs/authentication/application-default-credentials)、服务账号或 [API key](https://cloud.google.com/vertex-ai/generative-ai/docs/start/api-keys?usertype=expressmode) 进行身份验证。

无论采用哪种身份验证方式，你都需要在 Google Cloud 账号中启用 Vertex AI API（现在品牌名为 Google Cloud AI）。

#### 应用默认凭据

如果你已安装并配置 [`gcloud` CLI](https://cloud.google.com/sdk/gcloud)，可以按名称使用 `GoogleCloudProvider`：

```python {test="ci_only"}
from pydantic_ai import Agent

agent = Agent('google-cloud:gemini-3-pro-preview')
...
```

或者显式创建 provider 和 model：

```python {test="ci_only"}
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

provider = GoogleCloudProvider()
model = GoogleModel('gemini-3-pro-preview', provider=provider)
agent = Agent(model)
...
```

#### 服务账号

要使用服务账号 JSON 文件，请显式创建 provider 和 model：

```python {title="google_model_service_account.py" test="skip"}
from google.oauth2 import service_account

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

credentials = service_account.Credentials.from_service_account_file(
    'path/to/service-account.json',
    scopes=['https://www.googleapis.com/auth/cloud-platform'],
)
provider = GoogleCloudProvider(credentials=credentials, project='your-project-id')
model = GoogleModel('gemini-3-flash-preview', provider=provider)
agent = Agent(model)
...
```

#### API Key

要使用 API key 访问 Google Cloud，请[创建一个 key](https://cloud.google.com/vertex-ai/generative-ai/docs/start/api-keys?usertype=expressmode)，并将其设置为环境变量：

```bash
export GOOGLE_API_KEY=your-api-key
```

然后即可按名称通过 `GoogleCloudProvider` 使用 `GoogleModel`：

```python {test="ci_only"}
from pydantic_ai import Agent

agent = Agent('google-cloud:gemini-3-pro-preview')
...
```

或者显式创建 provider 和 model：

```python {test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

provider = GoogleCloudProvider(api_key='your-api-key')
model = GoogleModel('gemini-3-pro-preview', provider=provider)
agent = Agent(model)
...
```

#### 自定义 Location 或 Project

使用 Google Cloud 时，可以指定 location 和/或 project：

```python {title="google_model_location.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

provider = GoogleCloudProvider(location='asia-east1', project='your-google-cloud-project-id')
model = GoogleModel('gemini-3-pro-preview', provider=provider)
agent = Agent(model)
...
```

#### 服务层级（`service_tier`、`google_cloud_service_tier`）

统一的 [`service_tier`][pydantic_ai.settings.ModelSettings.service_tier] 字段可用于 Google 的两个子系统；[`google_cloud_service_tier`][pydantic_ai.models.google.GoogleModelSettings.google_cloud_service_tier] 则可用于更细粒度的 Google Cloud 路由控制。当两者同时设置时，提供商专用字段优先。

**Gemini API** - 作为请求的 `service_tier` 字段发送：

| `service_tier` | 发送给 Gemini API |
|---|---|
| `'auto'` | _（省略，使用服务端默认值）_ |
| `'default'` | `'standard'` |
| `'flex'` | `'flex'` |
| `'priority'` | `'priority'` |

**Google Cloud** - 作为 HTTP 路由 headers 发送；`'flex'` 和 `'priority'` 始终选择 **PT-with-spillover** 变体，因此拥有[预置吞吐量](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput/use-provisioned-throughput)（PT）的客户会优先继续使用预留容量：

| `service_tier` | Google Cloud routing headers | 实际行为 |
|---|---|---|
| `'auto'` / `'default'` | _（无）_ | 优先使用 PT，然后溢出到标准按需 |
| `'flex'` | `X-Vertex-AI-LLM-Shared-Request-Type: flex` | 优先使用 PT，然后溢出到 [Flex PayGo](https://cloud.google.com/vertex-ai/generative-ai/docs/flex-paygo) |
| `'priority'` | `X-Vertex-AI-LLM-Shared-Request-Type: priority` | 优先使用 PT，然后溢出到 [Priority PayGo](https://cloud.google.com/vertex-ai/generative-ai/docs/priority-paygo) |

要完全绕过 PT（或仅使用 PT，或使用其他任何 Google Cloud 专用路由组合），请直接设置 [`google_cloud_service_tier`][pydantic_ai.models.google.GoogleModelSettings.google_cloud_service_tier]；统一字段有意限制为安全的 PT-with-spillover 变体。

**Google Cloud - 完整路由值集合**

完整的 [`google_cloud_service_tier`][pydantic_ai.models.google.GoogleModelSettings.google_cloud_service_tier] 值会映射为这些 HTTP headers：

- `'pt_only'`: 仅 PT（`X-Vertex-AI-LLM-Request-Type: dedicated`）。
- `'pt_then_flex'`: 配额允许时使用 PT，然后溢出到 [Flex PayGo](https://cloud.google.com/vertex-ai/generative-ai/docs/flex-paygo)（`X-Vertex-AI-LLM-Shared-Request-Type: flex`）。
- `'pt_then_priority'`: 配额允许时使用 PT，然后溢出到 [Priority PayGo](https://cloud.google.com/vertex-ai/generative-ai/docs/priority-paygo)（`X-Vertex-AI-LLM-Shared-Request-Type: priority`）。
- `'on_demand'`: 仅标准按需（`X-Vertex-AI-LLM-Request-Type: shared`）。
- `'flex_only'`: 仅 [Flex PayGo](https://cloud.google.com/vertex-ai/generative-ai/docs/flex-paygo)（`X-Vertex-AI-LLM-Request-Type: shared` 和 `X-Vertex-AI-LLM-Shared-Request-Type: flex`）。
- `'priority_only'`: 仅 [Priority PayGo](https://cloud.google.com/vertex-ai/generative-ai/docs/priority-paygo)（`X-Vertex-AI-LLM-Request-Type: shared` 和 `X-Vertex-AI-LLM-Shared-Request-Type: priority`）。

**示例**

```python {test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

provider = GoogleCloudProvider(location='global')
model = GoogleModel('gemini-3-flash-preview', provider=provider)
agent = Agent(model)

result = agent.run_sync(
    'Hello!',
    model_settings=GoogleModelSettings(google_cloud_service_tier='pt_then_flex'),
)
```

可将 `'pt_then_flex'` 替换为任意 [`GoogleCloudServiceTier`][pydantic_ai.models.google.GoogleCloudServiceTier] 值，例如使用 `'pt_then_priority'` 溢出到 [Priority PayGo](https://cloud.google.com/vertex-ai/generative-ai/docs/priority-paygo)，或使用 `'flex_only'` / `'priority_only'` 完全绕过 PT。

[`google_service_tier`][pydantic_ai.models.google.GoogleModelSettings.google_service_tier] 字段已弃用，请改用这些更具体的字段。

请求完成后，可检查 [`ModelResponse`][pydantic_ai.messages.ModelResponse] 的 `provider_details.get('traffic_type')`（例如 `ON_DEMAND_FLEX`、`ON_DEMAND_PRIORITY`），在 API 返回该值时确认由哪个层级提供服务。

#### Model Garden 模型库 {#model-garden}

你可以访问 [Model Garden](https://cloud.google.com/model-garden?hl=en) 中支持 `generateContent` API、并且在你的 Google Cloud project 下可用的模型，包括但不限于 Gemini。可以使用以下 `model_name` 模式之一：

- `{model_id}` 用于 Gemini 模型
- `{publisher}/{model_id}`
- `publishers/{publisher}/models/{model_id}`
- `projects/{project}/locations/{location}/publishers/{publisher}/models/{model_id}`

```python {test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

provider = GoogleCloudProvider(
    project='your-google-cloud-project-id',
    location='us-central1',  # the region where the model is available
)
model = GoogleModel('meta/llama-3.3-70b-instruct-maas', provider=provider)
agent = Agent(model)
...
```

## 自定义 HTTP Client

你可以使用自定义 `httpx.AsyncClient` 配置 `GoogleProvider`：

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

custom_http_client = AsyncClient(timeout=30)
model = GoogleModel(
    'gemini-3-pro-preview',
    provider=GoogleProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```


## 文档、图像、音频和视频输入 {#document-image-audio-and-video-input}

`GoogleModel` 支持多模态输入，包括文档、图像、音频和视频。

YouTube 视频 URL 可以直接传给 Google 模型：

```py {title="youtube_input.py" test="skip" lint="skip"}
from pydantic_ai import Agent, VideoUrl
from pydantic_ai.models.google import GoogleModel

agent = Agent(GoogleModel('gemini-3-flash-preview'))
result = agent.run_sync(
    [
        'What is this video about?',
        VideoUrl(url='https://www.youtube.com/watch?v=dQw4w9WgXcQ'),
    ]
)
print(result.output)
```

文件可以通过 [Files API](https://ai.google.dev/gemini-api/docs/files) 上传，并作为 URL 传入：

```py {title="file_upload.py" test="skip"}
from pydantic_ai import Agent, DocumentUrl
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

provider = GoogleProvider()
file = provider.client.files.upload(file='pydantic-ai-logo.png')
assert file.uri is not None

agent = Agent(GoogleModel('gemini-3-flash-preview', provider=provider))
result = agent.run_sync(
    [
        'What company is this logo from?',
        DocumentUrl(url=file.uri, media_type=file.mime_type),
    ]
)
print(result.output)
```

更多细节和示例请参阅[输入文档](../input.md)。

## 模型设置

你可以使用 [`GoogleModelSettings`][pydantic_ai.models.google.GoogleModelSettings] 自定义模型行为：

```python
from google.genai.types import HarmBlockThreshold, HarmCategory

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

settings = GoogleModelSettings(
    temperature=0.2,
    max_tokens=1024,
    google_safety_settings=[
        {
            'category': HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            'threshold': HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        }
    ]
)
model = GoogleModel('gemini-3-pro-preview')
agent = Agent(model, model_settings=settings)
...
```

### 配置思考 {#configure-thinking}

使用与 provider 无关的 [`Thinking`][pydantic_ai.capabilities.Thinking] capability 启用思考：

```python
from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking

agent = Agent('google:gemini-3.5-flash', capabilities=[Thinking(effort='medium')])
...
```

高级用法可以通过 [`GoogleModelSettings.google_thinking_config`][pydantic_ai.models.google.GoogleModelSettings.google_thinking_config] 传入 Google 的原生 thinking config：

```python
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

model = GoogleModel('gemini-3.5-flash')
model_settings = GoogleModelSettings(google_thinking_config={'include_thoughts': True, 'thinking_level': 'MEDIUM'})
agent = Agent(model, model_settings=model_settings)
...
```

统一 API 请参阅 [Thinking](../thinking.md)，Google 原生 thinking 配置请参阅 [Gemini API docs](https://ai.google.dev/gemini-api/docs/thinking)。

### 安全设置

你可以通过设置 `google_safety_settings` 字段来自定义安全设置。

```python
from google.genai.types import HarmBlockThreshold, HarmCategory

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

model_settings = GoogleModelSettings(
    google_safety_settings=[
        {
            'category': HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            'threshold': HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        }
    ]
)
model = GoogleModel('gemini-3-flash-preview')
agent = Agent(model, model_settings=model_settings)
...
```

更多安全设置说明请参阅 [Gemini API docs](https://ai.google.dev/gemini-api/docs/safety-settings)。


### Logprobs 对数概率 {#logprobs}

你可以在 [`GoogleModelSettings`][pydantic_ai.models.google.GoogleModelSettings] 中设置 `google_logprobs` 和 `google_top_logprobs`，让模型在响应中返回 logprobs。

此功能只支持非流式请求，并且只支持 Google Cloud。

```python {test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

model_settings = GoogleModelSettings(
    google_logprobs=True, google_top_logprobs=2,
)

model = GoogleModel(
    model_name='gemini-2.5-flash',
    provider=GoogleCloudProvider(location='europe-west1'),
)
agent = Agent(model, model_settings=model_settings)

result = agent.run_sync('Your prompt here')
# Access logprobs from provider_details
logprobs = result.response.provider_details.get('logprobs')
avg_logprobs = result.response.provider_details.get('avg_logprobs')
```

更多信息请参阅 [Google Dev Blog](https://developers.googleblog.com/unlock-gemini-reasoning-with-logprobs-on-vertex-ai/)。

## 流式取消 {#streaming-cancellation}

!!! warning "取消限制"
    `google-genai` SDK 只把流式响应暴露为异步迭代器，没有单独的句柄可用于关闭底层 HTTP transport。由于 [Python 对异步生成器的语言规则](https://peps.python.org/pep-0525/)，当另一个协程正在迭代流时，[`cancel()`][pydantic_ai.result.StreamedRunResult.cancel] 无法中断正在进行的 chunk 读取。Pydantic AI 会把响应标记为 `state='interrupted'`，但上游生成可能会持续到外围的 `async with agent.run_stream(...)` 块退出。

    要可靠取消，请向 [`stream_text()`][pydantic_ai.result.StreamedRunResult.stream_text]、[`stream_output()`][pydantic_ai.result.StreamedRunResult.stream_output] 或 [`stream_response()`][pydantic_ai.result.StreamedRunResult.stream_response] 传入 `debounce_by=None`，并在执行迭代的同一个 task 中调用 `cancel()`：

    ```python {title="cancel_google.py" test="skip"}
    from pydantic_ai import Agent

    agent = Agent('google:gemini-3-pro-preview')


    def should_stop(chunk: str) -> bool:
        return len(chunk) > 100


    async def main():
        async with agent.run_stream('Write a long essay about Python') as result:
            async for chunk in result.stream_text(debounce_by=None):
                if should_stop(chunk):
                    await result.cancel()
                    break
    ```

    或者，如果你需要保留 debouncing，请用 [`contextlib.aclosing`](https://docs.python.org/3/library/contextlib.html#contextlib.aclosing) 包装流，让迭代器在 `cancel()` 运行前关闭：

    ```python {title="cancel_google_aclosing.py" test="skip"}
    from contextlib import aclosing

    from pydantic_ai import Agent

    agent = Agent('google:gemini-3-pro-preview')


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

    当前，在这个 provider 上，从另一个 task 调用 `cancel()` 并且同时仍在迭代时并不可靠。
