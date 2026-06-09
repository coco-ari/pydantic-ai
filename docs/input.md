# 图片、音频、视频和文档输入


## 图片输入

!!! info
    有些模型不支持图片输入。请查看模型文档，确认它是否支持图片输入。

如果你有图片的直接 URL，可以使用 [`ImageUrl`][pydantic_ai.ImageUrl]：

```py {title="image_input.py" test="skip" lint="skip"}
from pydantic_ai import Agent, ImageUrl

agent = Agent(model='openai:gpt-5.2')
result = agent.run_sync(
    [
        'What company is this logo from?',
        ImageUrl(url='https://iili.io/3Hs4FMg.png'),
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.
```

如果图片在本地，也可以使用 [`BinaryContent`][pydantic_ai.BinaryContent]：

```py {title="local_image_input.py" test="skip" lint="skip"}
import httpx

from pydantic_ai import Agent, BinaryContent

image_response = httpx.get('https://iili.io/3Hs4FMg.png')  # Pydantic logo

agent = Agent(model='openai:gpt-5.2')
result = agent.run_sync(
    [
        'What company is this logo from?',
        BinaryContent(data=image_response.content, media_type='image/png'),  # (1)!
    ]
)
print(result.output)
#> This is the logo for Pydantic, a data validation and settings management library in Python.
```

1. 为了确保示例可运行，我们从网上下载这张图片；你也可以使用 `Path().read_bytes()` 读取本地文件内容。

## 音频输入

!!! info
    有些模型不支持音频输入。请查看模型文档，确认它是否支持音频输入。

你可以使用 [`AudioUrl`][pydantic_ai.AudioUrl] 或 [`BinaryContent`][pydantic_ai.BinaryContent] 提供音频输入。流程与上面的示例类似。

## 视频输入

!!! info
    有些模型不支持视频输入。请查看模型文档，确认它是否支持视频输入。

你可以使用 [`VideoUrl`][pydantic_ai.VideoUrl] 或 [`BinaryContent`][pydantic_ai.BinaryContent] 提供视频输入。流程与上面的示例类似。

## 文档输入

!!! info
    有些模型不支持文档输入。请查看模型文档，确认它是否支持文档输入。

你可以使用 [`DocumentUrl`][pydantic_ai.DocumentUrl] 或 [`BinaryContent`][pydantic_ai.BinaryContent] 提供文档输入。流程与上面的示例类似。

如果你有文档的直接 URL，可以使用 [`DocumentUrl`][pydantic_ai.DocumentUrl]：

```py {title="document_input.py" test="skip" lint="skip"}
from pydantic_ai import Agent, DocumentUrl

agent = Agent(model='anthropic:claude-sonnet-4-6')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        DocumentUrl(url='https://storage.googleapis.com/cloud-samples-data/generative-ai/pdf/2403.05530.pdf'),
    ]
)
print(result.output)
#> This document is the technical report introducing Gemini 1.5, Google's latest large language model...
```

支持的文档格式因模型而异。

你也可以使用 [`BinaryContent`][pydantic_ai.BinaryContent] 直接传入文档数据：

```py {title="binary_content_input.py" test="skip" lint="skip"}
from pathlib import Path
from pydantic_ai import Agent, BinaryContent

pdf_path = Path('document.pdf')
agent = Agent(model='anthropic:claude-sonnet-4-6')
result = agent.run_sync(
    [
        'What is the main content of this document?',
        BinaryContent(data=pdf_path.read_bytes(), media_type='application/pdf'),
    ]
)
print(result.output)
#> The document discusses...
```

!!! tip
    如果 `DocumentUrl` 和 `BinaryContent` 都不适合你的用例（例如模型不支持 `DocumentUrl`，或你想以非二进制格式提供文档），仍然可以自行提取文本，并将其作为字符串或 [`TextContent`][pydantic_ai.TextContent] 传入，从而把文档内容作为文本输入提供。


## 文本输入

你可以使用 [`TextContent`][pydantic_ai.TextContent] 提供带额外 metadata 的文本输入：

```py {title="text_content_input.py" test="skip" lint="skip"}
from pydantic_ai import Agent, TextContent

agent = Agent(model='openai:gpt-5.2')
result = agent.run_sync([
    'Summarize the key points from this text.',
    TextContent(
        content=(
            'Pydantic AI is a Python agent framework. '
            'It supports text, image, audio, video, and document input.'
        ),
        metadata={'source': 'pydantic_ai_inputs.txt'},
    ),
])
```

这等价于把文本作为 `str` 传入，但允许你包含额外的 `metadata`，这些 metadata 可在智能体逻辑中以编程方式访问。

!!! note
    `content` 字段会作为输入传给模型，但 `metadata` **不会发送给模型**。
    它会保留在 messages 中，以便程序访问。


## 用户侧下载 vs. 直接文件 URL

使用 `ImageUrl`、`AudioUrl`、`VideoUrl` 或 `DocumentUrl` 之一时，Pydantic AI 默认会把 URL 发送给模型 provider，因此文件会在 provider 侧下载。

对文件 URL 的支持因类型和 provider 而异：

| 模型 | 直接发送 URL | 下载后发送字节内容 | 不支持 |
|------|----------------|----------------------|--------|
| [`OpenAIChatModel`][pydantic_ai.models.openai.OpenAIChatModel] | `ImageUrl` | `AudioUrl`, `DocumentUrl` | `VideoUrl`。`DocumentUrl` [不支持与 `AzureProvider` 搭配使用](models/openai.md#using-azure-with-the-responses-api) |
| [`OpenAIResponsesModel`][pydantic_ai.models.openai.OpenAIResponsesModel] | `ImageUrl`, `AudioUrl`, `DocumentUrl` | — | `VideoUrl` |
| [`AnthropicModel`][pydantic_ai.models.anthropic.AnthropicModel] | `ImageUrl`, `DocumentUrl`（PDF） | `DocumentUrl`（`text/plain`） | `AudioUrl`, `VideoUrl` |
| [`GoogleModel`][pydantic_ai.models.google.GoogleModel]（Google Cloud） | 所有 URL 类型 | — | — |
| [`GoogleModel`][pydantic_ai.models.google.GoogleModel]（Gemini API） | [YouTube](models/google.md#document-image-audio-and-video-input)、[Files API](models/google.md#document-image-audio-and-video-input) | 其他所有 URL | — |
| [`XaiModel`][pydantic_ai.models.xai.XaiModel] | `ImageUrl` | `DocumentUrl` | `AudioUrl`, `VideoUrl` |
| [`MistralModel`][pydantic_ai.models.mistral.MistralModel] | `ImageUrl`, `DocumentUrl`（PDF） | — | `AudioUrl`, `VideoUrl`, `DocumentUrl`（非 PDF） |
| [`BedrockConverseModel`][pydantic_ai.models.bedrock.BedrockConverseModel] | S3 URL（`s3://`） | `ImageUrl`, `DocumentUrl`, `VideoUrl` | `AudioUrl` |
| [`OpenRouterModel`][pydantic_ai.models.openrouter.OpenRouterModel] | `ImageUrl`, `DocumentUrl`, `VideoUrl` | `AudioUrl` | — |

即使模型 API 支持文件 URL，也可能无法下载某个文件（例如因为爬取或访问限制）。例如，Google Cloud 上的 [`GoogleModel`][pydantic_ai.models.google.GoogleModel] 将 YouTube 视频 URL 限制为每个请求一个 URL。

在这种情况下，你可以通过在 URL 对象上设置 `force_download`，指示 Pydantic AI 在本地下载文件内容，并发送内容而不是 URL：

```py {title="force_download.py" test="skip" lint="skip"}
from pydantic_ai import ImageUrl, AudioUrl, VideoUrl, DocumentUrl

ImageUrl(url='https://example.com/image.png', force_download=True)
AudioUrl(url='https://example.com/audio.mp3', force_download=True)
VideoUrl(url='https://example.com/video.mp4', force_download=True)
DocumentUrl(url='https://example.com/doc.pdf', force_download=True)
```

!!! warning "信任模型处理文件 URL"
    当 URL 被转发给 provider 时，provider 会使用自己的凭据获取它们。对于 `s3://`（Bedrock）和 `gs://`（Google Cloud）等云存储 scheme，这些凭据是你服务器的 IAM role 或 service account，因此控制 URL 的人实际上控制了 provider 可以代表你读取什么。

    不要在未校验 scheme 和 scope 的情况下，用不可信用户输入构造 [`ImageUrl`][pydantic_ai.messages.ImageUrl]、[`AudioUrl`][pydantic_ai.messages.AudioUrl]、[`VideoUrl`][pydantic_ai.messages.VideoUrl] 或 [`DocumentUrl`][pydantic_ai.messages.DocumentUrl]。对于前端发起并上传到云存储的文件，请先在服务端将 `s3://bucket/key` 之类的引用转换为预签名 `https://` URL，再构造 file URL part。`force_download=True` 只适用于 `http(s)://` URL（它会经过库的 HTTP client 并应用 SSRF 保护）；`s3://` 和 `gs://` 等云存储 scheme 不支持本地下载路径，会原样转发给 provider。只有对服务端生成的 URL 才使用 `force_download='allow-local'`，因为它允许本地网络访问。

    [UI adapters](ui/overview.md) 会通过 [`UIAdapter.allowed_file_url_schemes`][pydantic_ai.ui.UIAdapter.allowed_file_url_schemes] 和 [`UIAdapter.allowed_file_url_force_download`][pydantic_ai.ui.UIAdapter.allowed_file_url_force_download] 对客户端提交的 messages 自动应用这种清理。

## 已上传文件 {#uploaded-files}

有些模型 providers 有自己的文件存储 API，你可以上传文件并通过 ID 或 URL 引用它们。

使用 [`UploadedFile`][pydantic_ai.messages.UploadedFile] 引用已上传到 provider 文件存储 API 的文件。

!!! tip
    对于会返回文件 URL 的 providers（例如 Google Files API 或 Bedrock 的 S3 URLs），你也可以直接使用 [`DocumentUrl`][pydantic_ai.messages.DocumentUrl]、[`ImageUrl`][pydantic_ai.messages.ImageUrl] 或 [`VideoUrl`][pydantic_ai.messages.VideoUrl]。不过，我们推荐使用 `UploadedFile`，以便跨 providers 使用统一 API，并保持一致的 provider name validation。

### 支持的模型 {#supported-models}

| 模型 | 支持方式 |
|------|----------|
| [`AnthropicModel`][pydantic_ai.models.anthropic.AnthropicModel] | ✅ 通过 [Anthropic Files API](https://docs.anthropic.com/en/docs/build-with-claude/files) |
| [`OpenAIChatModel`][pydantic_ai.models.openai.OpenAIChatModel] | ✅ 通过 [OpenAI Files API](https://platform.openai.com/docs/api-reference/files) |
| [`OpenAIResponsesModel`][pydantic_ai.models.openai.OpenAIResponsesModel] | ✅ 通过 [OpenAI Files API](https://platform.openai.com/docs/api-reference/files) |
| [`GoogleModel`][pydantic_ai.models.google.GoogleModel] | ✅ 通过 [Google Files API](https://ai.google.dev/gemini-api/docs/files) |
| [`BedrockConverseModel`][pydantic_ai.models.bedrock.BedrockConverseModel] | ✅ 通过 S3 URL（`s3://bucket/key`） |
| [`XaiModel`][pydantic_ai.models.xai.XaiModel] | ✅ 通过 [xAI Files API](https://docs.x.ai/docs/guides/files) |
| 其他模型 | ❌ 不支持 |

### `provider_name` 要求 {#provider-name-requirements}

使用 [`UploadedFile`][pydantic_ai.messages.UploadedFile] 时必须设置 `provider_name`。Uploaded files 属于其上传到的系统，不能跨 providers 转移。如果尝试将包含 `UploadedFile` 的 message 用于不同 provider，会导致错误。

!!! tip "获取 provider name"
    使用 [`model.system`][pydantic_ai.models.Model.system] 动态获取正确的 provider name。这样可以确保即使 provider name 变化，代码也能正确工作。下面所有示例都展示了这种模式。

如果你想在智能体逻辑中引入可移植性，让同一 prompt history 能与不同 provider backends 一起工作，可以使用 [history processor](message-history.md#processing-message-history)，在将 messages 发送给不支持这些文件的 provider 之前，移除或重写 `UploadedFile` parts。注意，去掉 `UploadedFile` 实例可能会让模型困惑，尤其是文本中仍然引用这些文件时。

### `media_type` 推断 {#media-type-inference}

[`UploadedFile`][pydantic_ai.messages.UploadedFile] 的 `media_type` 参数是可选的。如果没有指定，Pydantic AI 会尝试从 `file_id` 推断：

1. 如果 `file_id` 是带有可识别文件扩展名（例如 `.pdf`、`.png`）的 URL 或路径，则自动推断 media type
2. 对于不透明文件 ID（例如 `'file-abc123'`），media type 默认为 `'application/octet-stream'`

!!! tip
    虽然 `media_type` 是可选的，但如果已知，我们建议显式设置，以确保模型 provider 正确处理。

### Anthropic

按照 [Anthropic Files API docs](https://docs.anthropic.com/en/docs/build-with-claude/files) 上传文件。你可以通过 `provider.client` 访问底层 Anthropic client。

!!! note "Beta 功能"
    Anthropic Files API 当前处于 beta。发起请求时需要包含 beta header `anthropic-beta: files-api-2025-04-14`。

```py {title="uploaded_file_anthropic.py" test="skip"}
import asyncio

from pydantic_ai import Agent, ModelSettings, UploadedFile
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider


async def main():
    provider = AnthropicProvider()
    model = AnthropicModel('claude-sonnet-4-5', provider=provider)

    # Upload a file using the provider's client (Anthropic client)
    with open('document.pdf', 'rb') as f:
        uploaded_file = await provider.client.beta.files.upload(file=f)

    # Reference the uploaded file, including the required beta header
    agent = Agent(model)
    result = await agent.run(
        [
            'Summarize this document',
            UploadedFile(file_id=uploaded_file.id, provider_name=model.system),
        ],
        model_settings=ModelSettings(extra_headers={'anthropic-beta': 'files-api-2025-04-14'}),
    )
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```

### OpenAI

按照 [OpenAI Files API docs](https://platform.openai.com/docs/api-reference/files/create) 上传文件。你可以通过 `provider.client` 访问底层 OpenAI client。

```py {title="uploaded_file_openai.py" test="skip"}
import asyncio

from pydantic_ai import Agent, UploadedFile
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider


async def main():
    provider = OpenAIProvider()
    model = OpenAIChatModel('gpt-5', provider=provider)

    # Upload a file using the provider's client (OpenAI client)
    with open('document.pdf', 'rb') as f:
        uploaded_file = await provider.client.files.create(file=f, purpose='user_data')

    # Reference the uploaded file
    agent = Agent(model)
    result = await agent.run(
        [
            'Summarize this document',
            UploadedFile(file_id=uploaded_file.id, provider_name=model.system),
        ]
    )
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```

### Google

按照 [Google Files API docs](https://ai.google.dev/gemini-api/docs/files) 上传文件。你可以通过 `provider.client` 访问底层 Google GenAI client。

```py {title="uploaded_file_google.py" test="skip"}
import asyncio

from pydantic_ai import Agent, UploadedFile
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider


async def main():
    provider = GoogleProvider()
    model = GoogleModel('gemini-2.5-flash', provider=provider)

    # Upload a file using the provider's client (Google GenAI client)
    with open('document.pdf', 'rb') as f:
        file = await provider.client.aio.files.upload(file=f)
        assert file.uri is not None

    # Reference the uploaded file by URI (media_type is optional for Google)
    agent = Agent(model)
    result = await agent.run(
        [
            'Summarize this document',
            UploadedFile(file_id=file.uri, media_type=file.mime_type, provider_name=model.system),
        ]
    )
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```

### Bedrock（S3） {#bedrock-s3}

对于 Bedrock，文件必须单独上传到 S3（例如使用 [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html)）。假设角色（assumed role）必须对 bucket 具有 `s3:GetObject` 权限。

!!! note "`media_type` 可能是必需的"
    当文件扩展名模糊或缺失时，Bedrock 要求提供 `media_type`。对于 `.pdf`、`.png` 等扩展名清晰的 S3 URLs，可以自动推断。

```py {title="uploaded_file_bedrock.py" test="skip"}
import asyncio

from pydantic_ai import Agent, UploadedFile
from pydantic_ai.models.bedrock import BedrockConverseModel


async def main():
    model = BedrockConverseModel('us.anthropic.claude-sonnet-4-20250514-v1:0')

    agent = Agent(model)
    result = await agent.run([
        'Summarize this document',
        UploadedFile(
            file_id='s3://my-bucket/document.pdf',
            provider_name=model.system,  # 'bedrock'
            media_type='application/pdf',  # Optional for .pdf, but recommended
        ),
    ])
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```

!!! note
    如果 bucket 不属于发起请求的 account，可以选择指定 `bucketOwner` query 参数：`s3://my-bucket/document.pdf?bucketOwner=123456789012`

### xAI

按照 [xAI Files API docs](https://docs.x.ai/docs/guides/files) 上传文件。你可以通过 `provider.client` 访问底层 xAI client。

```py {title="uploaded_file_xai.py" test="skip"}
import asyncio

from pydantic_ai import Agent, UploadedFile
from pydantic_ai.models.xai import XaiModel
from pydantic_ai.providers.xai import XaiProvider


async def main():
    provider = XaiProvider()
    model = XaiModel('grok-4-fast', provider=provider)

    # Upload a file using the provider's client (xAI client)
    with open('document.pdf', 'rb') as f:
        uploaded_file = await provider.client.files.upload(f, filename='document.pdf')

    # Reference the uploaded file
    agent = Agent(model)
    result = await agent.run(
        [
            'Summarize this document',
            UploadedFile(file_id=uploaded_file.id, provider_name=model.system),
        ]
    )
    print(result.output)
    #> The document discusses the main topics and key findings...


asyncio.run(main())
```
