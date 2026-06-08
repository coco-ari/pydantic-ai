# 原生工具 {#native-tools}

原生工具是 LLM providers 提供的工具，可用于增强 agent 的能力。与由 Pydantic AI 执行的自定义实现 [common tools](common-tools.md) 不同，原生工具由模型提供商直接执行。

## 概览 {#overview}

Pydantic AI 支持以下原生工具：

- **[`WebSearchTool`][pydantic_ai.native_tools.WebSearchTool]**：允许 agents 搜索 Web
- **[`XSearchTool`][pydantic_ai.native_tools.XSearchTool]**：允许 agents 搜索 X/Twitter（仅 xAI）
- **[`CodeExecutionTool`][pydantic_ai.native_tools.CodeExecutionTool]**：允许 agents 在安全环境中执行代码
- **[`ImageGenerationTool`][pydantic_ai.native_tools.ImageGenerationTool]**：允许 agents 生成图片
- **[`WebFetchTool`][pydantic_ai.native_tools.WebFetchTool]**：允许 agents 获取网页
- **[`MemoryTool`][pydantic_ai.native_tools.MemoryTool]**：允许 agents 使用 memory
- **[`MCPServerTool`][pydantic_ai.native_tools.MCPServerTool]**：允许 agents 使用远程 MCP servers，并由模型提供商处理通信
- **[`FileSearchTool`][pydantic_ai.native_tools.FileSearchTool]**：允许 agents 使用 vector search（RAG）搜索已上传文件

这些工具会包装在 [`NativeTool`][pydantic_ai.capabilities.NativeTool] 中，并传给 agent 的 `capabilities` list；它们由模型提供商的基础设施执行。

!!! warning "Provider 支持"
    并非所有模型提供商都支持原生工具。如果你在不支持的 provider 上使用原生工具，Pydantic AI 会在你尝试运行 agent 时引发 [`UserError`][pydantic_ai.exceptions.UserError]。

    如果某个 provider 支持的原生工具目前还未被 Pydantic AI 支持，请提交 issue。

!!! tip "Provider-adaptive capabilities（自适应 provider 的 capabilities）"
    如果想使用更高层、model-agnostic 的方式，请考虑 [provider-adaptive tool capabilities](capabilities.md#provider-adaptive-tools)：[`WebSearch`][pydantic_ai.capabilities.WebSearch]、[`WebFetch`][pydantic_ai.capabilities.WebFetch]、[`ImageGeneration`][pydantic_ai.capabilities.ImageGeneration] 和 [`MCP`][pydantic_ai.capabilities.MCP]。它们会在模型支持时自动使用原生工具，并在不支持时回退到本地实现，因此你的 agent 可以跨 providers 工作而无需修改代码。

## 动态配置 {#dynamic-configuration}

有时你需要基于 [run context][pydantic_ai.tools.RunContext]（例如 user dependencies）动态配置原生工具，或有条件地省略它。可以在 `capabilities` 中用 [`NativeTool`][pydantic_ai.capabilities.NativeTool] 包装一个函数来实现。该函数接受 [`RunContext`][pydantic_ai.tools.RunContext] 作为参数，并返回 [`AbstractNativeTool`][pydantic_ai.native_tools.AbstractNativeTool] 或 `None`。

这对 [`WebSearchTool`][pydantic_ai.native_tools.WebSearchTool] 这类工具尤其有用，因为你可能想根据当前请求设置用户位置，或在用户未提供位置时禁用该工具。

```python {title="dynamic_native_tool.py"}
from pydantic_ai import Agent, RunContext, WebSearchTool
from pydantic_ai.capabilities import NativeTool


async def prepared_web_search(ctx: RunContext[dict]) -> WebSearchTool | None:
    if not ctx.deps.get('location'):
        return None

    return WebSearchTool(
        user_location={'city': ctx.deps['location']},
    )

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[NativeTool(prepared_web_search)],
    deps_type=dict,
)

# Run with location
result = agent.run_sync(
    'What is the weather like?',
    deps={'location': 'London'},
)
print(result.output)
#> It's currently raining in London.

# Run without location (tool will be omitted)
result = agent.run_sync(
    'What is the capital of France?',
    deps={'location': None},
)
print(result.output)
#> The capital of France is Paris.
```

## Web Search Tool（Web 搜索工具） {#web-search-tool}

!!! tip
    如需带自动本地 fallback 的 model-agnostic 方式，请参阅 [`WebSearch`][pydantic_ai.capabilities.WebSearch] [capability](capabilities.md#provider-adaptive-tools)。

[`WebSearchTool`][pydantic_ai.native_tools.WebSearchTool] 允许 agent 搜索 Web，适合需要最新数据的查询。

### Provider 支持 {#provider-support}

| Provider | 支持 | Notes |
|----------|-----------|-------|
| OpenAI Responses | ✅ | Full feature support。若要在可通过 [`ModelResponse.native_tool_calls`][pydantic_ai.messages.ModelResponse.native_tool_calls] 访问的 [`NativeToolReturnPart`][pydantic_ai.messages.NativeToolReturnPart] 中包含 search results，请启用 [`OpenAIResponsesModelSettings.openai_include_web_search_sources`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_include_web_search_sources] [model setting](agent.md#model-run-settings)。 |
| Anthropic | ✅ | 完整功能支持 |
| Google | ✅ | 不支持参数。Streaming 时不会生成 [`NativeToolCallPart`][pydantic_ai.messages.NativeToolCallPart] 或 [`NativeToolReturnPart`][pydantic_ai.messages.NativeToolReturnPart]。不支持同时使用 native tools 和 function tools（包括 [output tools](output.md#tool-output)）；若要使用 structured output，请改用 [`PromptedOutput`](output.md#prompted-output)。 |
| xAI | ✅ | 支持 `blocked_domains` 和 `allowed_domains` 参数。 |
| Groq | ✅ | Limited parameter support。若要在 Groq 上使用 web search capabilities，需要使用 [compound models](https://console.groq.com/docs/compound)。 |
| OpenRouter | ✅ | 通过 [plugins](https://openrouter.ai/docs/features/web-search) 提供 Web search。支持 `search_context_size`。对受支持 providers（OpenAI、Anthropic、Perplexity、xAI）使用 native search，对其他 providers 使用 Exa。 |
| OpenAI Chat Completions | ❌ | 不支持 |
| Bedrock | ❌ | 不支持 |
| Mistral | ❌ | 不支持 |
| Cohere | ❌ | 不支持 |
| HuggingFace | ❌ | 不支持 |
| Outlines | ❌ | 不支持 |

### 用法 {#usage}

```py {title="web_search_anthropic.py"}
from pydantic_ai import Agent, WebSearchTool
from pydantic_ai.capabilities import NativeTool

agent = Agent('anthropic:claude-sonnet-4-6', capabilities=[NativeTool(WebSearchTool())])

result = agent.run_sync('Give me a sentence with the biggest news in AI this week.')
print(result.output)
#> Scientists have developed a universal AI detector that can identify deepfake videos.
```

_（这个示例是完整的，可以"原样"运行）_

使用 OpenAI 时，你必须通过 Responses API 访问 web search tool。

```py {title="web_search_openai.py"}
from pydantic_ai import Agent, WebSearchTool
from pydantic_ai.capabilities import NativeTool

agent = Agent('openai-responses:gpt-5.2', capabilities=[NativeTool(WebSearchTool())])

result = agent.run_sync('Give me a sentence with the biggest news in AI this week.')
print(result.output)
#> Scientists have developed a universal AI detector that can identify deepfake videos.
```

_（这个示例是完整的，可以"原样"运行）_

### 配置选项 {#configuration-options}

`WebSearchTool` 支持几个配置参数：

```py {title="web_search_configured.py"}
from pydantic_ai import Agent, WebSearchTool, WebSearchUserLocation
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    capabilities=[
        NativeTool(
            WebSearchTool(
                search_context_size='high',
                user_location=WebSearchUserLocation(
                    city='San Francisco',
                    country='US',
                    region='CA',
                    timezone='America/Los_Angeles',
                ),
                blocked_domains=['example.com', 'spam-site.net'],
                allowed_domains=None,  # Cannot use both blocked_domains and allowed_domains with Anthropic
                max_uses=5,  # Anthropic only: limit tool usage
            )
        )
    ],
)

result = agent.run_sync('Use the web to get the current time.')
print(result.output)
#> In San Francisco, it's 8:21:41 pm PDT on Wednesday, August 6, 2025.
```

_（这个示例是完整的，可以"原样"运行）_

#### Provider 支持 {#provider-support-1}

| 参数 | OpenAI | Anthropic | xAI | Groq | OpenRouter |
|-----------|--------|-----------|-----|------|------------|
| `search_context_size` | ✅ | ❌ | ❌ | ❌ | ✅ |
| `user_location` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `blocked_domains` | ❌ | ✅ | ✅ | ✅ | ❌ |
| `allowed_domains` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `max_uses` | ❌ | ✅ | ❌ | ❌ | ❌ |

!!! note "Anthropic domain filtering（Anthropic 域名过滤）"
    使用 Anthropic 时，只能使用 `blocked_domains` 或 `allowed_domains` 其中之一，不能同时使用。

## X Search Tool（X 搜索工具） {#x-search-tool}

!!! tip
    如需带 subagent fallback 的 model-agnostic 方式，请参阅 [`XSearch`][pydantic_ai.capabilities.XSearch] [capability](capabilities.md#provider-adaptive-tools)。

[`XSearchTool`][pydantic_ai.native_tools.XSearchTool] 允许 agent 搜索 X/Twitter 上的实时 posts 和内容。它由 xAI models 原生支持；在设置 `fallback_model` 后，也可通过 [`XSearch`][pydantic_ai.capabilities.XSearch] capability 用于其他 models。更多细节请参阅 [xAI X Search documentation](https://docs.x.ai/developers/tools/x-search)。

### 用法 {#usage-1}

```py {title="x_search_xai.py"}
from pydantic_ai import Agent, XSearchTool
from pydantic_ai.capabilities import NativeTool

agent = Agent('xai:grok-4-1-fast', capabilities=[NativeTool(XSearchTool())])

result = agent.run_sync('What are people saying about AI on X today?')
print(result.output)
#> There's a lot of excitement about new AI models being released...
```

_（这个示例是完整的，可以"原样"运行）_

### 配置选项 {#configuration-options-1}

`XSearchTool` 支持几个配置参数：

```py {title="x_search_configured.py"}
from datetime import datetime

from pydantic_ai import Agent, XSearchTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'xai:grok-4-1-fast',
    capabilities=[
        NativeTool(
            XSearchTool(
                allowed_x_handles=['OpenAI', 'AnthropicAI', 'dasfacc'],
                from_date=datetime(2024, 1, 1),
                to_date=datetime(2024, 12, 31),
                enable_image_understanding=True,
                enable_video_understanding=True,
            )
        )
    ],
)

result = agent.run_sync('What have AI companies been posting about?')
print(result.output)
"""
OpenAI announced their latest model updates, while Anthropic shared research on AI safety...
"""
```

_（这个示例是完整的，可以"原样"运行）_

!!! note "Handle filtering（handle 过滤）"
    `allowed_x_handles` 和 `excluded_x_handles` 只能二选一，不能同时使用。每个 list 最多包含 10 个 handles。

!!! note "包含原始搜索结果"
    默认情况下，xAI 只返回模型对搜索的文本摘要。若要通过程序访问底层 posts、sources 和 metadata，请在 [`XSearchTool`][pydantic_ai.native_tools.XSearchTool] 上设置 `include_output=True`（类似 OpenAI web search 的 [`OpenAIResponsesModelSettings.openai_include_web_search_sources`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_include_web_search_sources]）。之后可以在通过 [`ModelResponse.native_tool_calls`][pydantic_ai.messages.ModelResponse.native_tool_calls] 暴露的 [`NativeToolReturnPart`][pydantic_ai.messages.NativeToolReturnPart] 上获取原始结果。作为替代，也可以通过 [`XaiModelSettings.xai_include_x_search_output`][pydantic_ai.models.xai.XaiModelSettings.xai_include_x_search_output] [model setting](agent.md#model-run-settings) 全局启用。推荐的基于 `XSearch` capability 的方式见 [xAI docs](models/xai.md#x-search)。

## Code Execution Tool（代码执行工具） {#code-execution-tool}

[`CodeExecutionTool`][pydantic_ai.native_tools.CodeExecutionTool] 允许 agent 在安全环境中执行代码，非常适合计算任务、数据分析和数学运算。

### Provider 支持 {#provider-support-2}

| Provider | 支持 | Notes |
|----------|-----------|-------|
| OpenAI | ✅ | 若要在可通过 [`ModelResponse.native_tool_calls`][pydantic_ai.messages.ModelResponse.native_tool_calls] 访问的 [`NativeToolReturnPart`][pydantic_ai.messages.NativeToolReturnPart] 中包含 code execution output，请启用 [`OpenAIResponsesModelSettings.openai_include_code_execution_outputs`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_include_code_execution_outputs] [model setting](agent.md#model-run-settings)。如果 code execution 生成了图片（例如图表），它们会以 [`BinaryImage`][pydantic_ai.messages.BinaryImage] objects 形式出现在 [`ModelResponse.images`][pydantic_ai.messages.ModelResponse.images] 上。生成的图片也可以作为 agent run 的 [image output](output.md#image-output)。 |
| Google | ✅ | 不支持同时使用 native tools 和 function tools（包括 [output tools](output.md#tool-output)）；若要使用 structured output，请改用 [`PromptedOutput`](output.md#prompted-output)。 |
| Anthropic | ✅ | 可用于兼容的 Anthropic models。Pydantic AI 会自动选择兼容的 code execution tool version；如需覆盖，请参阅 [Anthropic code execution tool version](models/anthropic.md#code-execution-tool-version)。 |
| xAI | ✅ | 完整功能支持。 |
| Groq | ❌ | 不支持 |
| Bedrock | ✅ | 仅适用于 Nova 2.0 models。 |
| Mistral | ❌ | 不支持 |
| Cohere | ❌ | 不支持 |
| HuggingFace | ❌ | 不支持 |
| Outlines | ❌ | 不支持 |

### 用法 {#usage-2}

```py {title="code_execution_basic.py"}
from pydantic_ai import Agent, CodeExecutionTool
from pydantic_ai.capabilities import NativeTool

agent = Agent('anthropic:claude-sonnet-4-6', capabilities=[NativeTool(CodeExecutionTool())])

result = agent.run_sync('Calculate the factorial of 15.')
print(result.output)
#> The factorial of 15 is **1,307,674,368,000**.
print(result.response.native_tool_calls)
"""
[
    (
        NativeToolCallPart(
            tool_name='code_execution',
            args={'command': 'python3 -c "import math; print(math.factorial(15))"'},
            tool_call_id='srvtoolu_017qRH1J3XrhnpjP2XtzPCmJ',
            provider_name='anthropic',
            provider_details={'anthropic_tool_name': 'bash_code_execution'},
        ),
        NativeToolReturnPart(
            tool_name='code_execution',
            content={
                'content': [],
                'return_code': 0,
                'stderr': '',
                'stdout': '1307674368000\n',
                'type': 'bash_code_execution_result',
            },
            tool_call_id='srvtoolu_017qRH1J3XrhnpjP2XtzPCmJ',
            timestamp=datetime.datetime(...),
            provider_name='anthropic',
            provider_details={'anthropic_tool_name': 'bash_code_execution'},
        ),
    )
]
"""
```

_（这个示例是完整的，可以"原样"运行）_

除了文本输出之外，OpenAI 的 code execution 还可以在 response 中生成图片。若要通过 [`ModelResponse.images`][pydantic_ai.messages.ModelResponse.images] 或 [image output](output.md#image-output) 访问这张图片，需要启用 [`OpenAIResponsesModelSettings.openai_include_code_execution_outputs`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_include_code_execution_outputs] [model setting](agent.md#model-run-settings)。

```py {title="code_execution_openai.py"}
from pydantic_ai import Agent, BinaryImage, CodeExecutionTool
from pydantic_ai.capabilities import NativeTool
from pydantic_ai.models.openai import OpenAIResponsesModelSettings

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[NativeTool(CodeExecutionTool())],
    output_type=BinaryImage,
    model_settings=OpenAIResponsesModelSettings(openai_include_code_execution_outputs=True),
)

result = agent.run_sync('Generate a chart of y=x^2 for x=-5 to 5.')
assert isinstance(result.output, BinaryImage)
```

_（这个示例是完整的，可以"原样"运行）_

## Image Generation Tool（图片生成工具） {#image-generation-tool}

!!! tip
    如需带自动本地 fallback 的 model-agnostic 方式，请参阅 [`ImageGeneration`][pydantic_ai.capabilities.ImageGeneration] [capability](capabilities.md#provider-adaptive-tools)。

[`ImageGenerationTool`][pydantic_ai.native_tools.ImageGenerationTool] 允许 agent 生成图片。

### Provider 支持 {#provider-support-3}

| Provider | 支持 | Notes |
|----------|-----------|-------|
| OpenAI Responses | ✅ | Full feature support。仅支持比 `gpt-5.2` 更新的 models。关于生成图片的 metadata，例如发送给底层 image model 的 [`revised_prompt`](https://platform.openai.com/docs/guides/tools-image-generation#revised-prompt)，可在通过 [`ModelResponse.native_tool_calls`][pydantic_ai.messages.ModelResponse.native_tool_calls] 访问的 [`NativeToolReturnPart`][pydantic_ai.messages.NativeToolReturnPart] 上获得。 |
| Google | ✅ | Limited parameter support。仅支持 [image generation models](https://ai.google.dev/gemini-api/docs/image-generation)，例如 `gemini-3-pro-image-preview` 和 `gemini-3-pro-image-preview`。这些 models 不支持 [function tools](tools.md)，并且即使没有显式指定此原生工具，也始终可以生成图片。 |
| Anthropic | ❌ | 不支持 |
| xAI | ❌ | |
| Groq | ❌ | 不支持 |
| Bedrock | ❌ | 不支持 |
| Mistral | ❌ | 不支持 |
| Cohere | ❌ | 不支持 |
| HuggingFace | ❌ | 不支持 |

### 用法 {#usage-3}

生成的图片会作为 [`BinaryImage`][pydantic_ai.messages.BinaryImage] objects 出现在 [`ModelResponse.images`][pydantic_ai.messages.ModelResponse.images] 上：

```py {title="image_generation_openai.py"}
from pydantic_ai import Agent, BinaryImage, ImageGenerationTool
from pydantic_ai.capabilities import NativeTool

agent = Agent('openai-responses:gpt-5.2', capabilities=[NativeTool(ImageGenerationTool())])

result = agent.run_sync('Tell me a two-sentence story about an axolotl with an illustration.')
print(result.output)
"""
Once upon a time, in a hidden underwater cave, lived a curious axolotl named Pip who loved to explore. One day, while venturing further than usual, Pip discovered a shimmering, ancient coin that granted wishes!
"""

assert isinstance(result.response.images[0], BinaryImage)
```

_（这个示例是完整的，可以"原样"运行）_

使用 Google [image generation models](https://ai.google.dev/gemini-api/docs/image-generation) 进行 image generation 时，不需要显式指定 `ImageGenerationTool` 原生工具：

```py {title="image_generation_google.py"}
from pydantic_ai import Agent, BinaryImage

agent = Agent('google:gemini-3-pro-image-preview')

result = agent.run_sync('Tell me a two-sentence story about an axolotl with an illustration.')
print(result.output)
"""
Once upon a time, in a hidden underwater cave, lived a curious axolotl named Pip who loved to explore. One day, while venturing further than usual, Pip discovered a shimmering, ancient coin that granted wishes!
"""

assert isinstance(result.response.images[0], BinaryImage)
```

_（这个示例是完整的，可以"原样"运行）_

`ImageGenerationTool` 可与 `output_type=BinaryImage` 一起使用，以获取 [image output](output.md#image-output)。如果没有显式指定 `ImageGenerationTool` 原生工具，它会被自动启用：

```py {title="image_generation_output.py"}
from pydantic_ai import Agent, BinaryImage

agent = Agent('openai-responses:gpt-5.2', output_type=BinaryImage)

result = agent.run_sync('Generate an image of an axolotl.')
assert isinstance(result.output, BinaryImage)
```

_（这个示例是完整的，可以"原样"运行）_

### 配置选项 {#configuration-options-2}

`ImageGenerationTool` 支持几个配置参数：

```py {title="image_generation_configured.py"}
from pydantic_ai import Agent, BinaryImage, ImageGenerationTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[
        NativeTool(
            ImageGenerationTool(
                action='generate',
                background='transparent',
                input_fidelity='high',
                model='gpt-image-2',
                moderation='low',
                output_compression=100,
                output_format='png',
                partial_images=3,
                quality='high',
                size='1024x1024',
            )
        )
    ],
    output_type=BinaryImage,
)

result = agent.run_sync('Generate an image of an axolotl.')
assert isinstance(result.output, BinaryImage)
```

_（这个示例是完整的，可以"原样"运行）_

OpenAI Responses models 也会遵守 `aspect_ratio` 参数。由于 OpenAI API 只暴露离散 image sizes，
Pydantic AI 会将 `'1:1'` 映射为 `1024x1024`，`'2:3'` 映射为 `1024x1536`，并将 `'3:2'` 映射为 `1536x1024`。提供任何其他 aspect ratio
都会导致错误；如果你同时设置了 `size`，它必须与计算出的值匹配。

OpenAI Responses image generation tool 默认使用 `action='auto'`，由模型决定是生成新图片，还是编辑 context 中已有的图片。使用 `action='generate'` 或 `action='edit'` 可以强制其中一种行为。你也可以设置
`model` 来选择该工具使用的底层 image generation model，例如 `model='gpt-image-2'`；这不会改变 agent 的 conversational model。

使用 Gemini image models 时，如需控制 aspect ratio，请显式包含 `ImageGenerationTool`：

```py {title="image_generation_google_aspect_ratio.py"}
from pydantic_ai import Agent, BinaryImage, ImageGenerationTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'google:gemini-3-pro-image-preview',
    capabilities=[NativeTool(ImageGenerationTool(aspect_ratio='16:9'))],
    output_type=BinaryImage,
)

result = agent.run_sync('Generate a wide illustration of an axolotl city skyline.')
assert isinstance(result.output, BinaryImage)
```

_（这个示例是完整的，可以"原样"运行）_

若要使用 Google image generation models（从 Gemini 3 Pro Image 开始）控制 image resolution，请使用 `size` 参数：

```py {title="image_generation_google_resolution.py"}
from pydantic_ai import Agent, BinaryImage, ImageGenerationTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'google:gemini-3-pro-image-preview',
    capabilities=[NativeTool(ImageGenerationTool(aspect_ratio='16:9', size='4K'))],
    output_type=BinaryImage,
)

result = agent.run_sync('Generate a high-resolution wide landscape illustration of an axolotl.')
assert isinstance(result.output, BinaryImage)
```

_（这个示例是完整的，可以"原样"运行）_

更多细节请查看 [API documentation][pydantic_ai.native_tools.ImageGenerationTool]。

#### Provider 支持 {#provider-support-4}

| 参数 | OpenAI | Google |
|-----------|--------|--------|
| `action` | ✅ (auto（默认）、generate、edit) | ❌ |
| `background` | ✅ | ❌ |
| `input_fidelity` | ✅ | ❌ |
| `moderation` | ✅ | ❌ |
| `model` | ✅（gpt-image-2、gpt-image-1.5、gpt-image-1、gpt-image-1-mini，或另一个 OpenAI image model ID） | ❌ |
| `output_compression` | ✅（100（默认），仅 jpeg 或 webp） | ✅（75（默认），仅 jpeg，仅 Google Cloud） |
| `output_format` | ✅ | ✅（仅 Google Cloud） |
| `partial_images` | ✅ | ❌ |
| `quality` | ✅ | ❌ |
| `size` | ✅（auto（默认）、1024x1024、1024x1536、1536x1024） | ✅（512、1K（默认）、2K、4K） |
| `aspect_ratio` | ✅ (1:1, 2:3, 3:2) | ✅ (1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9) |

!!! note "Notes（说明）"
    - **OpenAI**：`auto` 允许模型选择值。
    - **Google Cloud**：如果未指定 `output_format`，设置 `output_compression` 会使其默认变为 `jpeg`。

## Web Fetch Tool（Web 获取工具） {#web-fetch-tool}

!!! tip
    如需带自动本地 fallback 的 model-agnostic 方式，请参阅 [`WebFetch`][pydantic_ai.capabilities.WebFetch] [capability](capabilities.md#provider-adaptive-tools)。

[`WebFetchTool`][pydantic_ai.native_tools.WebFetchTool] 允许 agent 把 URL 内容拉入其 context，从 Web 获取最新信息。

### Provider 支持 {#provider-support-5}

| Provider | 支持 | Notes |
|----------|-----------|-------|
| Anthropic | ✅ | Full feature support。内部使用 Anthropic 的 [Web Fetch Tool](https://docs.claude.com/en/docs/agents-and-tools/tool-use/web-fetch-tool) 获取 URL 内容。 |
| Google | ✅ | 不支持参数。限制固定为每个请求 20 个 URLs，且每个 URL 最大 34MB。不支持同时使用 native tools 和 function tools（包括 [output tools](output.md#tool-output)）；若要使用 structured output，请改用 [`PromptedOutput`](output.md#prompted-output)。 |
| xAI | ❌ | 在 xAI 中，web browsing 作为 [`WebSearchTool`](#web-search-tool) 的一部分实现。 |
| OpenAI | ❌ | 不支持 |
| Groq | ❌ | 不支持 |
| Bedrock | ❌ | 不支持 |
| Mistral | ❌ | 不支持 |
| Cohere | ❌ | 不支持 |
| HuggingFace | ❌ | 不支持 |
| Outlines | ❌ | 不支持 |

### 用法 {#usage-4}

```py {title="web_fetch_basic.py"}
from pydantic_ai import Agent, WebFetchTool
from pydantic_ai.capabilities import NativeTool

agent = Agent('google:gemini-3-flash-preview', capabilities=[NativeTool(WebFetchTool())])

result = agent.run_sync('What is this? https://ai.pydantic.dev')
print(result.output)
#> A Python agent framework for building Generative AI applications.
```

_（这个示例是完整的，可以"原样"运行）_

### 配置选项 {#configuration-options-3}

`WebFetchTool` 支持几个配置参数：

```py {title="web_fetch_configured.py"}
from pydantic_ai import Agent, WebFetchTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    capabilities=[
        NativeTool(
            WebFetchTool(
                allowed_domains=['ai.pydantic.dev', 'docs.pydantic.dev'],
                max_uses=10,
                enable_citations=True,
                max_content_tokens=50000,
            )
        )
    ],
)

result = agent.run_sync(
    'Compare the documentation at https://ai.pydantic.dev and https://docs.pydantic.dev'
)
print(result.output)
"""
Both sites provide comprehensive documentation for Pydantic projects. ai.pydantic.dev focuses on PydanticAI, a framework for building AI agents, while docs.pydantic.dev covers Pydantic, the data validation library. They share similar documentation styles and both emphasize type safety and developer experience.
"""
```

_（这个示例是完整的，可以"原样"运行）_

#### Provider 支持 {#provider-support-6}

| 参数 | Anthropic | Google |
|-----------|-----------|--------|
| `max_uses` | ✅ | ❌ |
| `allowed_domains` | ✅ | ❌ |
| `blocked_domains` | ✅ | ❌ |
| `enable_citations` | ✅ | ❌ |
| `max_content_tokens` | ✅ | ❌ |

!!! note "Anthropic domain filtering（Anthropic 域名过滤）"
    使用 Anthropic 时，只能使用 `blocked_domains` 或 `allowed_domains` 其中之一，不能同时使用。

## Memory Tool（记忆工具） {#memory-tool}

[`MemoryTool`][pydantic_ai.native_tools.MemoryTool] 允许 agent 使用 memory。

### Provider 支持 {#provider-support-7}

| Provider | 支持 | Notes |
|----------|-----------|-------|
| Anthropic | ✅ | 需要定义一个名为 `memory` 的工具，并实现[特定 sub-commands](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool#tool-commands)。你可以按下面文档所示，使用 [`anthropic.lib.tools.BetaAbstractMemoryTool`](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/lib/tools/_beta_builtin_memory_tool.py) 的 subclass。 |
| Google | ❌ | 不支持 |
| OpenAI | ❌ | 不支持 |
| Groq | ❌ | 不支持 |
| Bedrock | ❌ | 不支持 |
| Mistral | ❌ | 不支持 |
| Cohere | ❌ | 不支持 |
| HuggingFace | ❌ | 不支持 |

### 用法 {#usage-5}

Anthropic SDK 提供了一个 abstract [`BetaAbstractMemoryTool`](https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/lib/tools/_beta_builtin_memory_tool.py) class，你可以继承它来创建自己的 memory storage solution（例如 database、cloud storage、encrypted files 等）。其 [`LocalFilesystemMemoryTool`](https://github.com/anthropics/anthropic-sdk-python/blob/main/examples/memory/basic.py) 示例可以作为起点。

以下示例使用一个 hard-code 特定 memory 的 subclass。与 Pydantic AI 相关的部分是 `MemoryTool` 原生工具，以及把 commands 转发给 `BetaAbstractMemoryTool` subclass 的 `call` method 的 `memory` 工具定义。

```py {title="anthropic_memory.py"}
from typing import Any

from anthropic.lib.tools import BetaAbstractMemoryTool
from anthropic.types.beta import (
    BetaMemoryTool20250818CreateCommand,
    BetaMemoryTool20250818DeleteCommand,
    BetaMemoryTool20250818InsertCommand,
    BetaMemoryTool20250818RenameCommand,
    BetaMemoryTool20250818StrReplaceCommand,
    BetaMemoryTool20250818ViewCommand,
)

from pydantic_ai import Agent, MemoryTool
from pydantic_ai.capabilities import NativeTool


class FakeMemoryTool(BetaAbstractMemoryTool):
    def view(self, command: BetaMemoryTool20250818ViewCommand) -> str:
        return 'The user lives in Mexico City.'

    def create(self, command: BetaMemoryTool20250818CreateCommand) -> str:
        return f'File created successfully at {command.path}'

    def str_replace(self, command: BetaMemoryTool20250818StrReplaceCommand) -> str:
        return f'File {command.path} has been edited'

    def insert(self, command: BetaMemoryTool20250818InsertCommand) -> str:
        return f'Text inserted at line {command.insert_line} in {command.path}'

    def delete(self, command: BetaMemoryTool20250818DeleteCommand) -> str:
        return f'File deleted: {command.path}'

    def rename(self, command: BetaMemoryTool20250818RenameCommand) -> str:
        return f'Renamed {command.old_path} to {command.new_path}'

    def clear_all_memory(self) -> str:
        return 'All memory cleared'

fake_memory = FakeMemoryTool()

agent = Agent('anthropic:claude-sonnet-4-6', capabilities=[NativeTool(MemoryTool())])


@agent.tool_plain
def memory(**command: Any) -> Any:
    return fake_memory.call(command)


result = agent.run_sync('Remember that I live in Mexico City')
print(result.output)
"""
Got it! I've recorded that you live in Mexico City. I'll remember this for future reference.
"""

result = agent.run_sync('Where do I live?')
print(result.output)
#> You live in Mexico City.
```

_（这个示例是完整的，可以"原样"运行）_

## MCP Server Tool（MCP Server 工具） {#mcp-server-tool}

!!! tip
    如需带自动本地 fallback 的 model-agnostic 方式，请参阅 [`MCP`][pydantic_ai.capabilities.MCP] [capability](capabilities.md#provider-adaptive-tools)。

[`MCPServerTool`][pydantic_ai.native_tools.MCPServerTool] 允许 agent 使用远程 MCP servers，并由模型提供商处理通信。

这要求 MCP server 位于 provider 可以访问的公开 URL，且不支持 Pydantic AI agent-side [MCP support](mcp/client.md) 的许多高级功能；
但由于无需往返 Pydantic AI，它可以带来更优化的 context 使用和 caching，并提升性能。

### Provider 支持 {#provider-support-8}

| Provider | 支持 | Notes                 |
|----------|-----------|-----------------------|
| OpenAI Responses | ✅ | Full feature support。可以通过指定特殊的 `x-openai-connector:<connector_id>` URL 使用 [Connectors](https://platform.openai.com/docs/guides/tools-connectors-mcp#connectors)。 |
| Anthropic | ✅ | 完整功能支持 |
| xAI | ✅ | 完整功能支持 |
| Google  | ❌ | 不支持 |
| Groq  | ❌ | 不支持 |
| OpenAI Chat Completions | ❌ | 不支持 |
| Bedrock | ❌ | 不支持 |
| Mistral | ❌ | 不支持 |
| Cohere | ❌ | 不支持 |
| HuggingFace | ❌ | 不支持 |

### 用法 {#usage-6}

```py {title="mcp_server_anthropic.py"}
from pydantic_ai import Agent, MCPServerTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    capabilities=[
        NativeTool(
            MCPServerTool(
                id='deepwiki',
                url='https://mcp.deepwiki.com/mcp',  # (1)
            )
        )
    ]
)

result = agent.run_sync('Tell me about the pydantic/pydantic-ai repo.')
print(result.output)
"""
The pydantic/pydantic-ai repo is a Python agent framework for building Generative AI applications.
"""
```

1. [DeepWiki MCP server](https://docs.devin.ai/work-with-devin/deepwiki-mcp) 不需要 authorization。

_（这个示例是完整的，可以"原样"运行）_

使用 OpenAI 时，你必须通过 Responses API 访问 MCP server tool：

```py {title="mcp_server_openai.py"}
from pydantic_ai import Agent, MCPServerTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[
        NativeTool(
            MCPServerTool(
                id='deepwiki',
                url='https://mcp.deepwiki.com/mcp',  # (1)
            )
        )
    ]
)

result = agent.run_sync('Tell me about the pydantic/pydantic-ai repo.')
print(result.output)
"""
The pydantic/pydantic-ai repo is a Python agent framework for building Generative AI applications.
"""
```

1. [DeepWiki MCP server](https://docs.devin.ai/work-with-devin/deepwiki-mcp) 不需要 authorization。

_（这个示例是完整的，可以"原样"运行）_

### 配置选项 {#configuration-options-4}

`MCPServerTool` 支持几个用于自定义 MCP servers 的配置参数：

```py {title="mcp_server_configured_url.py"}
import os

from pydantic_ai import Agent, MCPServerTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[
        NativeTool(
            MCPServerTool(
                id='github',
                url='https://api.githubcopilot.com/mcp/',
                authorization_token=os.getenv('GITHUB_ACCESS_TOKEN', 'mock-access-token'),  # (1)
                allowed_tools=['search_repositories', 'list_commits'],
                description='GitHub MCP server',
                headers={'X-Custom-Header': 'custom-value'},
            )
        )
    ]
)

result = agent.run_sync('Tell me about the pydantic/pydantic-ai repo.')
print(result.output)
"""
The pydantic/pydantic-ai repo is a Python agent framework for building Generative AI applications.
"""
```

1. [GitHub MCP server](https://github.com/github/github-mcp-server) 需要 authorization token。

对于 OpenAI Responses，你可以通过指定特殊的 `x-openai-connector:` URL 使用 [connector](https://platform.openai.com/docs/guides/tools-connectors-mcp#connectors)：

_（这个示例是完整的，可以"原样"运行）_

```py {title="mcp_server_configured_connector_id.py"}
import os

from pydantic_ai import Agent, MCPServerTool
from pydantic_ai.capabilities import NativeTool

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[
        NativeTool(
            MCPServerTool(
                id='google-calendar',
                url='x-openai-connector:connector_googlecalendar',
                authorization_token=os.getenv('GOOGLE_API_KEY', 'mock-api-key'), # (1)
            )
        )
    ]
)

result = agent.run_sync('What do I have on my calendar today?')
print(result.output)
#> You're going to spend all day playing with Pydantic AI.
```

1. OpenAI 的 Google Calendar connector 需要 [authorization token](https://platform.openai.com/docs/guides/tools-connectors-mcp#authorizing-a-connector)。

_（这个示例是完整的，可以"原样"运行）_

#### Provider 支持 {#provider-support-9}

| 参数                  | OpenAI | Anthropic | xAI |
|-----------------------|--------|-----------|-----|
| `authorization_token` | ✅ | ✅ | ✅ |
| `allowed_tools`       | ✅ | ✅ | ✅ |
| `description`         | ✅ | ❌ | ✅ |
| `headers`             | ✅ | ❌ | ✅ |

## File Search Tool（文件搜索工具） {#file-search-tool}

[`FileSearchTool`][pydantic_ai.native_tools.FileSearchTool] 允许 agent 使用 vector search 搜索已上传文件，并提供完全托管的 Retrieval-Augmented Generation（RAG）系统。该工具会处理 file storage、chunking、embedding generation，以及把 context 注入 prompts。

### Provider 支持 {#provider-support-10}

| Provider | 支持 | Notes |
|----------|-----------|-------|
| OpenAI Responses | ✅ | Full feature support。需要通过 [OpenAI Files API](https://platform.openai.com/docs/api-reference/files) 将文件上传到 vector stores。若要在可通过 [`ModelResponse.native_tool_calls`][pydantic_ai.messages.ModelResponse.native_tool_calls] 访问的 [`NativeToolReturnPart`][pydantic_ai.messages.NativeToolReturnPart] 中包含 search results，请启用 [`OpenAIResponsesModelSettings.openai_include_file_search_results`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_include_file_search_results] [model setting](agent.md#model-run-settings)。 |
| Google (Gemini) | ✅ | 需要通过 [Gemini Files API](https://ai.google.dev/gemini-api/docs/files) 上传文件。文件会在 48 小时后自动删除。支持单文件最大 2 GB，每个项目最大 20 GB。不支持同时使用 native tools 和 function tools（包括 [output tools](output.md#tool-output)）；若要使用 structured output，请改用 [`PromptedOutput`](output.md#prompted-output)。 |
| xAI | ✅ | 映射到 xAI collections search。需要 collection IDs。若要在 [`NativeToolReturnPart`][pydantic_ai.messages.NativeToolReturnPart] 上包含 search results，请启用 [`XaiModelSettings.xai_include_collections_search_output`][pydantic_ai.models.xai.XaiModelSettings.xai_include_collections_search_output] [model setting](agent.md#model-run-settings)。 |
|| Google Cloud | ❌ | 不支持 |
| Anthropic | ❌ | 不支持 |
| Groq | ❌ | 不支持 |
| OpenAI Chat Completions | ❌ | 不支持 |
| Bedrock | ❌ | 不支持 |
| Mistral | ❌ | 不支持 |
| Cohere | ❌ | 不支持 |
| HuggingFace | ❌ | 不支持 |
| Outlines | ❌ | 不支持 |

### 用法 {#usage-7}

#### OpenAI Responses

使用 OpenAI 时，你需要先[将文件上传到 vector store](https://platform.openai.com/docs/assistants/tools/file-search)，然后在使用 `FileSearchTool` 时引用 vector store IDs。

```py {title="file_search_openai_upload.py" test="skip"}
import asyncio

from pydantic_ai import Agent, FileSearchTool
from pydantic_ai.capabilities import NativeTool
from pydantic_ai.models.openai import OpenAIResponsesModel


async def main():
    model = OpenAIResponsesModel('gpt-5.2')

    with open('my_document.txt', 'rb') as f:
        file = await model.client.files.create(file=f, purpose='assistants')

    vector_store = await model.client.vector_stores.create(name='my-docs')
    await model.client.vector_stores.files.create(
        vector_store_id=vector_store.id,
        file_id=file.id
    )

    agent = Agent(
        model,
        capabilities=[NativeTool(FileSearchTool(file_store_ids=[vector_store.id]))]
    )

    result = await agent.run('What information is in my documents about pydantic?')
    print(result.output)
    #> Based on your documents, Pydantic is a data validation library for Python...

asyncio.run(main())
```

#### Google (Gemini)

使用 Gemini 时，你需要先[通过 Files API 创建 file search store](https://ai.google.dev/gemini-api/docs/files)，然后引用 file search store names。

```py {title="file_search_google_upload.py" test="skip"}
import asyncio

from pydantic_ai import Agent, FileSearchTool
from pydantic_ai.capabilities import NativeTool
from pydantic_ai.models.google import GoogleModel


async def main():
    model = GoogleModel('gemini-3-flash-preview')

    store = await model.client.aio.file_search_stores.create(
        config={'display_name': 'my-docs'}
    )

    with open('my_document.txt', 'rb') as f:
        await model.client.aio.file_search_stores.upload_to_file_search_store(
            file_search_store_name=store.name,
            file=f,
            config={'mime_type': 'text/plain'}
        )

    agent = Agent(
        model,
        capabilities=[NativeTool(FileSearchTool(file_store_ids=[store.name]))]
    )

    result = await agent.run('Summarize the key points from my uploaded documents.')
    print(result.output)
    #> The documents discuss the following key points: ...

asyncio.run(main())
```

#### xAI

使用 xAI 时，`FileSearchTool` 会映射到 [collections search](https://docs.x.ai/developers/tools/collection-search) tool。请将 collection IDs 作为 `file_store_ids` 传入。

```py {title="file_search_xai.py" test="skip"}
import asyncio

from pydantic_ai import Agent, FileSearchTool
from pydantic_ai.capabilities import NativeTool


async def main():
    agent = Agent(
        'xai:grok-4-1-fast',
        capabilities=[NativeTool(FileSearchTool(file_store_ids=['collection_abc123']))]
    )

    result = await agent.run('What does the collection say about pydantic?')
    print(result.output)
    #> Based on the collection, Pydantic is ...

asyncio.run(main())
```

## API 参考 {#api-reference}

完整 API 文档请参阅 [API Reference](api/native_tools.md)。
