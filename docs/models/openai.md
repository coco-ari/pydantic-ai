# OpenAI

## 安装 {#install}

要使用 OpenAI models 或 OpenAI-compatible APIs，你需要安装 `pydantic-ai`，或安装带 `openai` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[openai]"
```

## 配置 {#configuration}

要通过 OpenAI API 使用 `OpenAIChatModel`，请前往 [platform.openai.com](https://platform.openai.com/) 并找到生成 API key 的位置。

## 环境变量 {#environment-variable}

拿到 API key 后，可以将其设置为环境变量：

```bash
export OPENAI_API_KEY='your-api-key'
```

然后你可以按名称使用 `OpenAIChatModel`：

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')
...
```

或者只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

model = OpenAIChatModel('gpt-5.2')
agent = Agent(model)
...
```

默认情况下，`OpenAIChatModel` 使用 `OpenAIProvider`，其 `base_url` 设置为 `https://api.openai.com/v1`。

## 配置 provider {#configure-the-provider}

如果你想在代码中向 provider 传入参数，可以以编程方式实例化
[OpenAIProvider][pydantic_ai.providers.openai.OpenAIProvider] 并传给 model：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel('gpt-5.2', provider=OpenAIProvider(api_key='your-api-key'))
agent = Agent(model)
...
```

## 自定义 OpenAI Client {#custom-openai-client}

`OpenAIProvider` 也接受通过 `openai_client` 参数传入自定义 `AsyncOpenAI` client，因此你可以按 [OpenAI API docs](https://platform.openai.com/docs/api-reference) 中的定义自定义 `organization`、`project`、`base_url` 等。

```python {title="custom_openai_client.py"}
from openai import AsyncOpenAI

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

client = AsyncOpenAI(max_retries=3)
model = OpenAIChatModel('gpt-5.2', provider=OpenAIProvider(openai_client=client))
agent = Agent(model)
...
```

你也可以使用 [`AsyncAzureOpenAI`](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/switching-endpoints) client
来使用 Azure OpenAI API。注意，`AsyncAzureOpenAI` 是 `AsyncOpenAI` 的子类。

```python
from openai import AsyncAzureOpenAI

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

client = AsyncAzureOpenAI(
    azure_endpoint='...',
    api_version='2024-07-01-preview',
    api_key='your-api-key',
)

model = OpenAIChatModel(
    'gpt-5.2',
    provider=OpenAIProvider(openai_client=client),
)
agent = Agent(model)
...
```

## 模型设置 {#model-settings}

你可以使用 [`OpenAIChatModelSettings`][pydantic_ai.models.openai.OpenAIChatModelSettings] 定制模型行为：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings

model = OpenAIChatModel('gpt-5.2')
settings = OpenAIChatModelSettings(
    temperature=0.2,
    service_tier='flex',
)
agent = Agent(model, model_settings=settings)
...
```

### 服务层级 {#service-tier}

OpenAI 支持控制 [service tier](https://platform.openai.com/docs/api-reference/chat/create#chat-create-service_tier)，用于在延迟和成本之间权衡。
你可以使用统一的 [`service_tier`][pydantic_ai.settings.ModelSettings.service_tier] 字段，或 provider 专用的 [`openai_service_tier`][pydantic_ai.models.openai.OpenAIChatModelSettings.openai_service_tier] 字段。两者都接受 `'auto'`、`'default'`、`'flex'` 和 `'priority'`，并原样传递。当两者同时设置时，`openai_service_tier` 优先于统一字段。

## OpenAI Responses API {#openai-responses-api}

Pydantic AI 还通过 [`OpenAIResponsesModel`][pydantic_ai.models.openai.OpenAIResponsesModel] 支持 OpenAI 的 [Responses API](https://platform.openai.com/docs/api-reference/responses)：

```python
from pydantic_ai import Agent

agent = Agent('openai-responses:gpt-5.2')
...
```

!!! note "v2 默认变更"
    在 Pydantic AI v2 中，裸 `'openai:'` prefix 会解析为 `OpenAIResponsesModel`，而不是 `OpenAIChatModel`。在 v2 之前，只要使用裸 `'openai:'`，`pydantic-ai` 就会发出 `PydanticAIDeprecationWarning`；请选择显式 prefix 以静默警告并固定行为：

    - `'openai-chat:gpt-5.2'` 保持 Chat Completions routing。
    - `'openai-responses:gpt-5.2'` 现在就选择 Responses API（并匹配即将到来的 v2 默认行为）。

或者只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel

model = OpenAIResponsesModel('gpt-5.2')
agent = Agent(model)
...
```

你可以在 [OpenAI API docs](https://platform.openai.com/docs/guides/migrate-to-responses) 中了解 Responses API 与 Chat Completions API 的区别。

### 原生工具 {#native-tools}

Responses API 提供可直接使用的 native tools，无需自己构建：

- [Web search](https://platform.openai.com/docs/guides/tools-web-search)：允许 models 在生成响应前搜索 web 以获取最新信息。
- [Code interpreter](https://platform.openai.com/docs/guides/tools-code-interpreter)：允许 models 在生成响应前，在 sandboxed environment 中编写并运行 Python code。
- [Image generation](https://platform.openai.com/docs/guides/tools-image-generation)：允许 models 基于 text prompt 生成 images。
- [File search](https://platform.openai.com/docs/guides/tools-file-search)：允许 models 在生成响应前搜索你的 files 以获取相关信息。
- [Computer use](https://platform.openai.com/docs/guides/tools-computer-use)：允许 models 代表你使用 computer 执行 tasks。

Web search、Code interpreter、Image generation 和 File search 通过 [Native tools](../native-tools.md) 功能获得原生支持。

Computer use 可以通过在 [`OpenAIResponsesModelSettings`][pydantic_ai.models.openai.OpenAIResponsesModelSettings] 的 `openai_native_tools` 设置中传入 [`openai.types.responses.ComputerToolParam`](https://github.com/openai/openai-python/blob/main/src/openai/types/responses/computer_tool_param.py) 来启用。它目前不会在 message history 或 streamed events 中生成 [`NativeToolCallPart`][pydantic_ai.messages.NativeToolCallPart] 或 [`NativeToolReturnPart`][pydantic_ai.messages.NativeToolReturnPart] parts；如果你需要对此 native tool 的原生支持，请提交 issue。

```python {title="computer_use_tool.py" test="skip"}
from openai.types.responses import ComputerToolParam

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model_settings = OpenAIResponsesModelSettings(
    openai_native_tools=[
        ComputerToolParam(
            type='computer_use',
        )
    ],
)
model = OpenAIResponsesModel('gpt-5.2')
agent = Agent(model=model, model_settings=model_settings)

result = agent.run_sync('Open a new browser tab')
print(result.output)
```

#### 引用较早的 responses {#referencing-earlier-responses}

Responses API 支持在新请求中通过 `previous_response_id` 参数引用较早的 model responses，从而确保完整的 [conversation state](https://platform.openai.com/docs/guides/conversation-state?api-mode=responses#passing-context-from-the-previous-response)，包括 [reasoning items](https://platform.openai.com/docs/guides/reasoning#keeping-reasoning-items-in-context)，保留在上下文中，而无需重新发送它。这可以通过
[`OpenAIResponsesModelSettings`][pydantic_ai.models.openai.OpenAIResponsesModelSettings] 中的 [`openai_previous_response_id`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_previous_response_id] 字段使用。

当该字段设置为 `'auto'` 时，Pydantic AI 会自动从 message history 中选择最近的 `provider_response_id`，并省略它之前的 messages，让 OpenAI API 根据 server-side state 重建它们。相同的 chaining 也会在一次 run 内跨 tool-call continuations 和 retries 应用，因此 OpenAI 不会看到相同 messages 的重复副本。

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5.2')
agent = Agent(model=model)

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

model_settings = OpenAIResponsesModelSettings(openai_previous_response_id='auto')
result2 = agent.run_sync(
    'Explain?',
    message_history=result1.new_messages(),
    model_settings=model_settings
)
print(result2.output)
#> This is an excellent joke invented by Samuel Colvin, it needs no explanation.
```

作为传入 `message_history` 的替代方案，你可以将较早 run 中的具体 `provider_response_id` 作为 seed 传入。Pydantic AI 会在新 run 的第一个请求中使用该 seed，然后在任何后续 run 内 calls 中自动 chain 到该请求返回的 response；因此即使 run 包含 tool-call continuations 或 retries，chain 仍会正确延伸。

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5.2')
agent = Agent(model=model)

result = agent.run_sync('The secret is 1234')
model_settings = OpenAIResponsesModelSettings(
    openai_previous_response_id=result.all_messages()[-1].provider_response_id
)
result = agent.run_sync('What is the secret code?', model_settings=model_settings)
print(result.output)
#> 1234
```

!!! note
    引用已存储 response 要求该 response 确实已被存储。OpenAI 默认会存储 responses；如果你通过 [`openai_store=False`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_store] 禁用了 storage，或你的 organization 启用了 Zero Data Retention，则 chaining 不可用，每个请求都必须发送完整 message history。

#### 使用持久对话 {#using-durable-conversations}

OpenAI 的 [Conversations API](https://platform.openai.com/docs/guides/conversation-state?api-mode=responses#using-the-conversations-api) 与 Responses API 配合使用，将 conversation state 持久化到 durable conversation object 中。如果你已经有 OpenAI conversation ID，请通过 [`openai_conversation_id`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_conversation_id] 传入：

```python {test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5.2')
agent = Agent(model=model)

model_settings = OpenAIResponsesModelSettings(openai_conversation_id='conv_...')
result = agent.run_sync('What did we discuss last time?', model_settings=model_settings)
print(result.output)
```

当 response 属于某个 conversation 时，Pydantic AI 会把返回的 ID 存储在 `ModelResponse.provider_details['conversation_id']` 中。设置 `openai_conversation_id='auto'` 会从 message history 中使用最近的同 provider conversation ID，并且只发送该 response 之后的新 input items。

当 message-level [`conversation_id`][pydantic_ai.messages.ModelResponse.conversation_id] values 可用时，`auto` 只会复用当前 Pydantic AI conversation 中的 OpenAI conversation；如果要显式复用某个 OpenAI conversation ID，请传入具体值：

```python {test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5.2')
agent = Agent(model=model)

model_settings = OpenAIResponsesModelSettings(openai_conversation_id='conv_...')
result = agent.run_sync('What did we discuss last time?', model_settings=model_settings)

follow_up_settings = OpenAIResponsesModelSettings(openai_conversation_id='auto')
result2 = agent.run_sync(
    'Summarize the next step.',
    message_history=result.new_messages(),
    model_settings=follow_up_settings,
)
print(result2.output)
```

Pydantic AI 不会替你创建 OpenAI conversations。请使用 OpenAI client 创建 conversation，然后把其 ID 传给 `openai_conversation_id`。OpenAI API 中的 `conversation` 和 `previous_response_id` 参数互斥，因此 `openai_conversation_id` 不能与 [`openai_previous_response_id`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_previous_response_id] 组合。

#### 消息压缩 {#message-compaction}

Responses API 支持[压缩 message history](https://developers.openai.com/api/docs/guides/compaction)，以减少长对话中的 token usage。压缩会生成一个加密摘要，用其替换较旧 messages，同时保留上下文。

启用 compaction 最简单的方法是使用 [`OpenAICompaction`][pydantic_ai.models.openai.OpenAICompaction] capability：

```python {title="openai_compaction.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAICompaction

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[OpenAICompaction()],
)
```

默认情况下，`OpenAICompaction` 以**有状态模式**运行：它通过普通 `/responses` 请求上的 `context_management` 字段配置 OpenAI 的 server-side auto-compaction，并且当 input token count 跨过 OpenAI 为你管理的阈值时触发 compaction。此模式兼容 [`openai_previous_response_id='auto'`](#referencing-earlier-responses) 和 [`openai_conversation_id`](#using-durable-conversations)。

要覆盖阈值，请传入 [`token_threshold`][pydantic_ai.models.openai.OpenAICompaction]：

```python {title="openai_compaction_token_threshold.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAICompaction

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[OpenAICompaction(token_threshold=100_000)],
)
```

作为替代方案，`OpenAICompaction` 支持**无状态模式**（`stateless=True`），它会通过 `before_model_request` hook 调用 stateless `/responses/compact` endpoint。在 [ZDR](https://openai.com/enterprise-privacy/) environments、使用 [`openai_store=False`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_store] 时，或你需要明确的 out-of-band control 来决定何时运行 compaction 时使用此模式。无状态模式要求你指定 [`message_count_threshold`][pydantic_ai.models.openai.OpenAICompaction] 或自定义 `trigger` callable：

```python {title="openai_compaction_stateless.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAICompaction

agent = Agent(
    'openai-responses:gpt-5.2',
    capabilities=[OpenAICompaction(message_count_threshold=20)],
)
```

模式会根据你传入的参数推断：提供 `message_count_threshold` 或 `trigger` 表示无状态模式，否则使用有状态模式。你也可以显式传入 `stateless=True` 或 `stateless=False`。混用不同模式的参数会引发 [`UserError`][pydantic_ai.exceptions.UserError]。

!!! tip
    有状态压缩与 [`openai_previous_response_id='auto'`](#referencing-earlier-responses) 或 [`openai_conversation_id`](#using-durable-conversations) 尤其搭配良好。二者都依赖 OpenAI 的 server-side conversation state，因此 OpenAI 可以用先前压缩后的 context 作为下一轮的起点，而无需你重新发送。

对于更底层的用例，你可以直接在 model 上调用 [`compact_messages`][pydantic_ai.models.openai.OpenAIResponsesModel.compact_messages]。

## OpenAI 兼容模型 {#openai-compatible-models}

许多 providers 和 models 与 OpenAI API 兼容，可以在 Pydantic AI 中与 `OpenAIChatModel` 搭配使用。
开始前，请查看上面的[安装和配置](#install)说明。

要使用另一个 OpenAI 兼容 API，你可以设置 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY` 环境变量，或使用 [`OpenAIProvider`][pydantic_ai.providers.openai.OpenAIProvider] 的 `base_url` 和 `api_key` 参数：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    'model_name',
    provider=OpenAIProvider(
        base_url='https://<openai-compatible-api-endpoint>', api_key='your-api-key'
    ),
)
agent = Agent(model)
...
```

多种 providers 也有自己的 provider classes，因此你无需自己指定 base URL，并且可以使用标准 `<PROVIDER>_API_KEY` 环境变量设置 API key。
当 provider 有自己的 provider class 时，你可以使用 `Agent("<provider>:<model>")` 简写，例如 `Agent("deepseek:deepseek-chat")` 或 `Agent("moonshotai:kimi-k2-0711-preview")`，而不是显式构建 `OpenAIChatModel`。同样，你也可以把 provider name 作为字符串传给 `OpenAIChatModel` 上的 `provider` 参数，而不是显式实例化 provider class。

### 模型配置档案 {#model-profile}

有时，你使用的 provider 或 model 会与 OpenAI API 或 models 有细微不同的要求，例如对 tool definitions 的 JSON schemas 有不同限制，或不支持将 tool definitions 标记为 strict。

使用 Pydantic AI 提供的替代 provider class 时，通常会根据 model name 自动选择合适的 model profile。
如果你使用的模型开箱后不能正常工作，可以通过提供自己的 [`ModelProfile`][pydantic_ai.profiles.ModelProfile]（用于所有 model classes 共享的行为）或 [`OpenAIModelProfile`][pydantic_ai.profiles.openai.OpenAIModelProfile]（用于 `OpenAIChatModel` 专属行为）来调整 model requests 构造方式的各个方面：

```py
from pydantic_ai import Agent, InlineDefsJsonSchemaTransformer
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    'model_name',
    provider=OpenAIProvider(
        base_url='https://<openai-compatible-api-endpoint>.com', api_key='your-api-key'
    ),
    profile=OpenAIModelProfile(
        json_schema_transformer=InlineDefsJsonSchemaTransformer,  # Supported by any model class via the base ModelProfile
        openai_supports_strict_tool_definition=False,  # Supported by OpenAIChatModel and OpenAIResponsesModel
        openai_chat_supports_multiple_system_messages=False,  # Supported by OpenAIChatModel only — for strict providers (e.g. some vLLM/LiteLLM setups) that require exactly one initial system message
    )
)
agent = Agent(model)
```

### DeepSeek

要使用 [DeepSeek](https://deepseek.com) provider，请先按照[快速开始指南](https://api-docs.deepseek.com/)创建 API key。

然后你可以设置 `DEEPSEEK_API_KEY` 环境变量，并按名称使用 [`DeepSeekProvider`][pydantic_ai.providers.deepseek.DeepSeekProvider]：

```python
from pydantic_ai import Agent

agent = Agent('deepseek:deepseek-chat')
...
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider

model = OpenAIChatModel(
    'deepseek-chat',
    provider=DeepSeekProvider(api_key='your-deepseek-api-key'),
)
agent = Agent(model)
...
```

你也可以用自定义 `http_client` 定制任何 provider：

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.deepseek import DeepSeekProvider

custom_http_client = AsyncClient(timeout=30)
model = OpenAIChatModel(
    'deepseek-chat',
    provider=DeepSeekProvider(
        api_key='your-deepseek-api-key', http_client=custom_http_client
    ),
)
agent = Agent(model)
...
```

### Alibaba Cloud Model Studio (DashScope)

要通过 [Alibaba Cloud Model Studio (DashScope)](https://www.alibabacloud.com/en/product/modelstudio) 使用 Qwen models，可以设置 `ALIBABA_API_KEY`（或 `DASHSCOPE_API_KEY`）环境变量，并按名称使用 [`AlibabaProvider`][pydantic_ai.providers.alibaba.AlibabaProvider]：

```python
from pydantic_ai import Agent

agent = Agent('alibaba:qwen-max')
...
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.alibaba import AlibabaProvider

model = OpenAIChatModel(
    'qwen-max',
    provider=AlibabaProvider(api_key='your-api-key'),
)
agent = Agent(model)
...
```

`AlibabaProvider` 默认使用国际版 DashScope compatible endpoint `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`。你可以传入自定义 `base_url` 覆盖它：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.alibaba import AlibabaProvider

model = OpenAIChatModel(
    'qwen-max',
    provider=AlibabaProvider(
        api_key='your-api-key',
        base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',  # China region
    ),
)
agent = Agent(model)
...
```

### Ollama

有关 structured output 和 Ollama Cloud limitations 等专门 Ollama 文档，请参阅 [Ollama](ollama.md)。

### Azure AI Foundry

要使用 [Azure AI Foundry](https://ai.azure.com/) 作为 provider，请将 `AZURE_OPENAI_ENDPOINT` 设置为路径以 `/v1` 结尾的 URL（例如 `https://<resource>.openai.azure.com/openai/v1/` 或 `https://<resource>.services.ai.azure.com/openai/v1/`），设置 `AZURE_OPENAI_API_KEY`，并按名称使用 [`AzureProvider`][pydantic_ai.providers.azure.AzureProvider]：

```python
from pydantic_ai import Agent

agent = Agent('azure:gpt-5.2')
...
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

model = OpenAIChatModel(
    'gpt-5.2',
    provider=AzureProvider(
        azure_endpoint='https://your-resource.openai.azure.com/openai/v1/',
        api_key='your-api-key',
    ),
)
agent = Agent(model)
...
```

这会指向 Microsoft 建议所有新项目使用的 [Azure OpenAI v1 API](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/api-version-lifecycle)。它也自然适配 Responses API；见下面的[将 Azure 与 Responses API 搭配使用](#using-azure-with-the-responses-api)。

[`AzureProvider`][pydantic_ai.providers.azure.AzureProvider] 也能识别位于 `https://<model>.<region>.models.ai.azure.com` 的 [Azure AI Foundry serverless model deployments](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/concepts/endpoints)，并以相同方式连接。

#### 连接到现有基于 `api-version` 的 deployment {#connecting-to-an-existing-api-version-based-deployment}

如果你的 resource 仍使用带日期的 `api-version` API，请传入 `api_version`（或设置 `OPENAI_API_VERSION` 环境变量），并将 `azure_endpoint` 指向 resource root：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider

model = OpenAIChatModel(
    'gpt-5.2',
    provider=AzureProvider(
        azure_endpoint='https://your-resource.openai.azure.com/',
        api_version='2024-12-01-preview',
        api_key='your-api-key',
    ),
)
agent = Agent(model)
...
```

#### 将 Azure 与 Responses API 搭配使用 {#using-azure-with-the-responses-api}

Azure AI Foundry 也通过 [`OpenAIResponsesModel`][pydantic_ai.models.openai.OpenAIResponsesModel] 支持 OpenAI Responses API。当处理 document inputs（[`DocumentUrl`][pydantic_ai.DocumentUrl] 和 [`BinaryContent`][pydantic_ai.BinaryContent]）时尤其推荐，因为 Azure 的 Chat Completions API 不支持这些 input types。

??? example "使用 Responses API 通过 Azure 处理文档"
    ```python
    from pydantic_ai import Agent, BinaryContent
    from pydantic_ai.models.openai import OpenAIResponsesModel
    from pydantic_ai.providers.azure import AzureProvider

    pdf_bytes = b'%PDF-1.4 ...'  # Your PDF content

    model = OpenAIResponsesModel(
        'gpt-5.2',
        provider=AzureProvider(
            azure_endpoint='https://your-resource.openai.azure.com/openai/v1/',
            api_key='your-api-key',
        ),
    )
    agent = Agent(model)
    result = agent.run_sync([
        'Summarize this document',
        BinaryContent(data=pdf_bytes, media_type='application/pdf'),
    ])
    ```

### Vercel AI Gateway

要使用 [Vercel AI Gateway](https://vercel.com/docs/ai-gateway)，请先按照[文档](https://vercel.com/docs/ai-gateway)说明获取 API key 或 OIDC token。

你可以设置 `VERCEL_AI_GATEWAY_API_KEY` 和 `VERCEL_OIDC_TOKEN` 环境变量，并按名称使用 [`VercelProvider`][pydantic_ai.providers.vercel.VercelProvider]：

```python
from pydantic_ai import Agent

agent = Agent('vercel:anthropic/claude-sonnet-4-5')
...
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.vercel import VercelProvider

model = OpenAIChatModel(
    'anthropic/claude-sonnet-4-5',
    provider=VercelProvider(api_key='your-vercel-ai-gateway-api-key'),
)
agent = Agent(model)
...
```

### MoonshotAI

在 [Moonshot Console](https://platform.moonshot.ai/console) 中创建 API key。

你可以设置 `MOONSHOTAI_API_KEY` 环境变量，并按名称使用 [`MoonshotAIProvider`][pydantic_ai.providers.moonshotai.MoonshotAIProvider]：

```python
from pydantic_ai import Agent

agent = Agent('moonshotai:kimi-k2-0711-preview')
...
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.moonshotai import MoonshotAIProvider

model = OpenAIChatModel(
    'kimi-k2-0711-preview',
    provider=MoonshotAIProvider(api_key='your-moonshot-api-key'),
)
agent = Agent(model)
...
```

### GitHub Models

要使用 [GitHub Models](https://docs.github.com/en/github-models)，你需要具有 `models: read` 权限的 GitHub personal access token。

你可以设置 `GITHUB_API_KEY` 环境变量，并按名称使用 [`GitHubProvider`][pydantic_ai.providers.github.GitHubProvider]：

```python
from pydantic_ai import Agent

agent = Agent('github:xai/grok-3-mini')
...
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.github import GitHubProvider

model = OpenAIChatModel(
    'xai/grok-3-mini',  # GitHub Models uses prefixed model names
    provider=GitHubProvider(api_key='your-github-token'),
)
agent = Agent(model)
...
```

GitHub Models 支持具有不同 prefixes 的多种 model families。你可以在 [GitHub Marketplace](https://github.com/marketplace?type=models) 或公开的 [catalog endpoint](https://models.github.ai/catalog/models) 上查看完整列表。

### Perplexity

按照 Perplexity [getting started](https://docs.perplexity.ai/guides/getting-started)
指南创建 API key，然后直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    'sonar-pro',
    provider=OpenAIProvider(
        base_url='https://api.perplexity.ai',
        api_key='your-perplexity-api-key',
    ),
)
agent = Agent(model)
...
```

### Fireworks AI

前往 [Fireworks.AI](https://fireworks.ai/) 并在账户设置中创建 API key。

你可以设置 `FIREWORKS_API_KEY` 环境变量，并按名称使用 [`FireworksProvider`][pydantic_ai.providers.fireworks.FireworksProvider]：

```python
from pydantic_ai import Agent

agent = Agent('fireworks:accounts/fireworks/models/qwq-32b')
...
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.fireworks import FireworksProvider

model = OpenAIChatModel(
    'accounts/fireworks/models/qwq-32b',  # model library available at https://fireworks.ai/models
    provider=FireworksProvider(api_key='your-fireworks-api-key'),
)
agent = Agent(model)
...
```

### Together AI

前往 [Together.ai](https://www.together.ai/) 并在账户设置中创建 API key。

你可以设置 `TOGETHER_API_KEY` 环境变量，并按名称使用 [`TogetherProvider`][pydantic_ai.providers.together.TogetherProvider]：

```python
from pydantic_ai import Agent

agent = Agent('together:meta-llama/Llama-3.3-70B-Instruct-Turbo-Free')
...
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.together import TogetherProvider

model = OpenAIChatModel(
    'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free',  # model library available at https://www.together.ai/models
    provider=TogetherProvider(api_key='your-together-api-key'),
)
agent = Agent(model)
...
```

### Heroku AI

要使用 [Heroku AI](https://www.heroku.com/ai)，请先创建 API key。

你可以设置 `HEROKU_INFERENCE_KEY` 和（可选的）`HEROKU_INFERENCE_URL` 环境变量，并按名称使用 [`HerokuProvider`][pydantic_ai.providers.heroku.HerokuProvider]：

```python
from pydantic_ai import Agent

agent = Agent('heroku:claude-sonnet-4-5')
...
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.heroku import HerokuProvider

model = OpenAIChatModel(
    'claude-sonnet-4-5',
    provider=HerokuProvider(api_key='your-heroku-inference-key'),
)
agent = Agent(model)
...
```

### LiteLLM

要使用 [LiteLLM](https://www.litellm.ai/)，请按[文档](https://docs.litellm.ai/docs/set_keys)中的说明设置 configs。在 `LiteLLMProvider` 中，你可以传入 `api_base` 和 `api_key`。这些 configs 的值取决于你的 setup。例如，如果你使用 OpenAI models，则需要把 `https://api.openai.com/v1` 作为 `api_base`，并把你的 OpenAI API key 作为 `api_key`。如果你使用在本机运行的 LiteLLM proxy server，则需要把 `http://localhost:<port>` 作为 `api_base`，并把你的 LiteLLM API key（或 placeholder）作为 `api_key`。

要使用自定义 LLMs，请在 model name 中使用 `custom/` prefix。

拿到 configs 后，按如下方式使用 [`LiteLLMProvider`][pydantic_ai.providers.litellm.LiteLLMProvider]：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.litellm import LiteLLMProvider

model = OpenAIChatModel(
    'openai/gpt-5.2',
    provider=LiteLLMProvider(
        api_base='<api-base-url>',
        api_key='<api-key>'
    )
)
agent = Agent(model)

result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
...
```

### Nebius AI Studio

前往 [Nebius AI Studio](https://studio.nebius.com/) 并创建 API key。

你可以设置 `NEBIUS_API_KEY` 环境变量，并按名称使用 [`NebiusProvider`][pydantic_ai.providers.nebius.NebiusProvider]：

```python
from pydantic_ai import Agent

agent = Agent('nebius:Qwen/Qwen3-32B-fast')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.nebius import NebiusProvider

model = OpenAIChatModel(
    'Qwen/Qwen3-32B-fast',
    provider=NebiusProvider(api_key='your-nebius-api-key'),
)
agent = Agent(model)
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

### OVHcloud AI Endpoints

要使用 OVHcloud AI Endpoints，你需要创建新的 API key。为此，请前往 [OVHcloud manager](https://ovh.com/manager)，然后进入 Public Cloud > AI Endpoints > API keys。点击 `Create a new API key` 并复制新 key。

你可以浏览 [catalog](https://endpoints.ai.cloud.ovh.net/catalog) 查看可用 models。

你可以设置 `OVHCLOUD_API_KEY` 环境变量，并按名称使用 [`OVHcloudProvider`][pydantic_ai.providers.ovhcloud.OVHcloudProvider]：

```python
from pydantic_ai import Agent

agent = Agent('ovhcloud:gpt-oss-120b')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

如果需要配置 provider，可以使用 [`OVHcloudProvider`][pydantic_ai.providers.ovhcloud.OVHcloudProvider] 类：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ovhcloud import OVHcloudProvider

model = OpenAIChatModel(
    'gpt-oss-120b',
    provider=OVHcloudProvider(api_key='your-api-key'),
)
agent = Agent(model)
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

### SambaNova

要使用 [SambaNova Cloud](https://cloud.sambanova.ai/)，你需要从 [SambaNova Cloud dashboard](https://cloud.sambanova.ai/dashboard) 获取 API key。

SambaNova 提供对多个 model families 的访问，包括 Meta Llama、DeepSeek、Qwen 和 Mistral models，并提供较快的推理速度。

你可以设置 `SAMBANOVA_API_KEY` 环境变量，并按名称使用 [`SambaNovaProvider`][pydantic_ai.providers.sambanova.SambaNovaProvider]：

```python
from pydantic_ai import Agent

agent = Agent('sambanova:Meta-Llama-3.1-8B-Instruct')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

或者直接初始化 model 和 provider：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.sambanova import SambaNovaProvider

model = OpenAIChatModel(
    'Meta-Llama-3.1-8B-Instruct',
    provider=SambaNovaProvider(api_key='your-api-key'),
)
agent = Agent(model)
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

完整可用模型列表请参阅 [SambaNova 支持模型文档](https://docs.sambanova.ai/docs/en/models/sambacloud-models)。

如果需要，你可以自定义 base URL：

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.sambanova import SambaNovaProvider

model = OpenAIChatModel(
    'DeepSeek-R1-0528',
    provider=SambaNovaProvider(
        api_key='your-api-key',
        base_url='https://custom.endpoint.com/v1',
    ),
)
agent = Agent(model)
...
```
