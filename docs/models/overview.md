# 模型提供商 {#model-providers}

Pydantic AI 与模型无关，并内置支持多个模型提供商：

* [OpenAI](openai.md)
* [Anthropic](anthropic.md)
* [Gemini](google.md)（通过两种不同 API：Gemini API 和 Google Cloud，后者曾称为 Vertex AI）
* [xAI](xai.md)
* [Bedrock](bedrock.md)
* [Cerebras](cerebras.md)
* [Cohere](cohere.md)
* [Groq](groq.md)
* [Hugging Face](huggingface.md)
* [Mistral](mistral.md)
* [OpenRouter](openrouter.md)
* [Outlines](outlines.md)（已弃用，将在 v2 中移除）

## OpenAI 兼容提供商 {#openai-compatible-providers}

此外，许多提供商与 OpenAI API 兼容，可以在 Pydantic AI 中配合 `OpenAIChatModel` 使用：

- [Alibaba Cloud Model Studio (DashScope)](openai.md#alibaba-cloud-model-studio-dashscope)
- [Azure AI Foundry](openai.md#azure-ai-foundry)
- [DeepSeek](openai.md#deepseek)
- [Fireworks AI](openai.md#fireworks-ai)
- [GitHub Models](openai.md#github-models)
- [Heroku](openai.md#heroku-ai)
- [LiteLLM](openai.md#litellm)
- [Nebius AI Studio](openai.md#nebius-ai-studio)
- [Ollama](openai.md#ollama)
- [OVHcloud AI Endpoints](openai.md#ovhcloud-ai-endpoints)
- [Perplexity](openai.md#perplexity)
- [SambaNova](openai.md#sambanova)
- [Together AI](openai.md#together-ai)
- [Vercel AI Gateway](openai.md#vercel-ai-gateway)

Pydantic AI 还提供 [`TestModel`](../api/models/test.md) 和 [`FunctionModel`](../api/models/function.md)，
用于测试和开发。

要使用各个模型提供商，你需要配置本地环境，并确保安装了正确的软件包。如果你在未完成配置时尝试使用模型，Pydantic AI 会提示需要安装什么。

## 模型和提供商 {#models-and-providers}

Pydantic AI 使用几个关键术语来描述它如何与不同 LLM 交互：

- **Model**：指 Pydantic AI 中用于按特定 LLM API 发起请求的类
  （通常通过封装厂商提供的 SDK，例如 `openai` Python SDK）。这些类实现了一个
  与厂商 SDK 无关的 API，因此只要替换所使用的 Model，同一个 Pydantic AI 智能体就可以移植到不同 LLM 厂商，
  无需其他代码变更。Model 类的命名大致采用 `<VendorSdk>Model` 格式，例如 `OpenAIChatModel`、`AnthropicModel`、`GoogleModel`
  等。使用 Model 类时，你需要把实际的 LLM 模型名称（例如 `gpt-5`、
  `claude-sonnet-4-5`、`gemini-3-flash-preview`）作为参数指定。
- **Provider**：指处理与 LLM 厂商认证和连接的提供商专用类。向 Model 传入非默认的 _Provider_ 参数，
  可以确保你的智能体向特定端点发起请求，或者使用特定认证方式
  （例如，你可以通过 `AzureProvider` 让 `OpenAIChatModel` 使用 Azure 认证）。
  这尤其适用于使用 AI 网关，或者使用某个与现有 Model 所用厂商 SDK 兼容的 LLM 厂商
  （例如 `OpenAIChatModel`）时。
- **Profile**：指如何构造对特定模型或模型家族的请求以获得最佳结果的描述，
  它独立于所使用的 model 和 provider 类。
  例如，不同模型对工具可用的 JSON schema 有不同限制；无论你是使用
  model name 为 `gemini-3-pro-preview` 的 `GoogleModel`，还是使用
  `OpenAIChatModel` 搭配 `OpenRouterProvider` 和 model name `google/gemini-3-pro-preview`，
  Gemini 模型都需要使用同一个 schema transformer。

当你只用 `<provider>:<model>` 格式的名称实例化 [`Agent`][pydantic_ai.Agent] 时，例如 `openai:gpt-5.2` 或 `openrouter:google/gemini-3-pro-preview`，
Pydantic AI 会自动选择合适的 model class、provider 和 profile。
如果你想使用不同的 provider 或 profile，可以直接实例化 model class，并传入 `provider` 和/或 `profile` 参数。

## HTTP 客户端生命周期 {#http-client-lifecycle}

当 [`Provider`][pydantic_ai.providers.Provider] 创建自己的 HTTP client 时（也就是你没有传入自定义 `http_client`），它会拥有该 client 的生命周期。把 [`Agent`][pydantic_ai.Agent] 作为 async context manager 使用，可以确保退出时干净关闭 HTTP client：

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

async def main():
    async with agent:
        result = await agent.run('What is the capital of France?')
        print(result.output)
        #> The capital of France is Paris.
```

你也可以把 [`Model`][pydantic_ai.models.Model] 或 [`Provider`][pydantic_ai.providers.Provider] 直接作为 async context manager 使用，效果相同。

如果你提供自己的 `http_client`，则需要自行负责关闭它。

## 自定义模型 {#custom-models}

!!! note
    如果某个模型 API 与 OpenAI API 兼容，你不需要自定义 model class，可以改为提供自己的[自定义 provider](openai.md#openai-compatible-models)。

要为尚未支持的模型 API 实现支持，你需要继承 [`Model`][pydantic_ai.models.Model] 抽象基类。
对于流式响应，还需要实现 [`StreamedResponse`][pydantic_ai.models.StreamedResponse] 抽象基类。

最好的起点是查看现有实现的源代码，例如 [`OpenAIChatModel`](https://github.com/pydantic/pydantic-ai/blob/main/pydantic_ai_slim/pydantic_ai/models/openai.py)。

关于我们何时接受向 Pydantic AI 添加新模型的贡献，请参阅[贡献指南](../contributing.md#new-model-rules)。

## HTTP 请求并发 {#http-request-concurrency}

你可以使用 [`ConcurrencyLimitedModel`][pydantic_ai.ConcurrencyLimitedModel] 包装器限制对模型的并发 HTTP 请求数量。
当并行运行多个智能体时，这对于遵守速率限制或管理资源使用很有用。

```python {title="model_concurrency.py"}
import asyncio

from pydantic_ai import Agent, ConcurrencyLimitedModel

# Wrap a model with concurrency limiting
model = ConcurrencyLimitedModel('openai:gpt-4o', limiter=5)

# Multiple agents can share this rate-limited model
agent = Agent(model)


async def main():
    # These will be rate-limited to 5 concurrent HTTP requests
    results = await asyncio.gather(
        *[agent.run(f'Question {i}') for i in range(20)]
    )
    print(len(results))
    #> 20
```

`limiter` 参数接受：

- 用于简单限制的整数（例如 `limiter=5`）
- 用于带 backpressure 控制的高级配置的 [`ConcurrencyLimit`][pydantic_ai.ConcurrencyLimit]
- 用于在多个模型之间共享限制的 [`ConcurrencyLimiter`][pydantic_ai.ConcurrencyLimiter]

### 共享并发限制 {#shared-concurrency-limits}

要在多个模型之间共享并发限制（例如同一个提供商的不同模型），
你可以创建一个 [`ConcurrencyLimiter`][pydantic_ai.ConcurrencyLimiter]，并把它传给
多个 `ConcurrencyLimitedModel` 实例：

```python {title="shared_concurrency.py"}
import asyncio

from pydantic_ai import Agent, ConcurrencyLimitedModel, ConcurrencyLimiter

# Create a shared limiter with a descriptive name
shared_limiter = ConcurrencyLimiter(max_running=10, name='openai-pool')

# Both models share the same concurrency limit
model1 = ConcurrencyLimitedModel('openai:gpt-4o', limiter=shared_limiter)
model2 = ConcurrencyLimitedModel('openai:gpt-4o-mini', limiter=shared_limiter)

agent1 = Agent(model1)
agent2 = Agent(model2)


async def main():
    # Total concurrent requests across both agents limited to 10
    results = await asyncio.gather(
        *[agent1.run(f'Question {i}') for i in range(10)],
        *[agent2.run(f'Question {i}') for i in range(10)],
    )
    print(len(results))
    #> 20
```

启用 instrumentation 时，正在等待并发槽位的请求会显示为 spans，
其 attributes 会展示队列深度和配置的限制。`ConcurrencyLimiter` 上的 `name` 参数
有助于在 traces 中识别共享 limiter。

<!-- TODO(Marcelo): We need to create a section in the docs about reliability. -->

## 回退模型 {#fallback-model}

你可以使用 [`FallbackModel`][pydantic_ai.models.fallback.FallbackModel] 按顺序尝试多个模型，
直到其中一个成功。当前模型引发异常（例如 4xx/5xx API 错误）**或**响应内容表明语义失败
（例如响应被截断或原生工具调用失败）时，Pydantic AI 可以切换到下一个模型。

默认情况下，fallback 会在 [`ModelAPIError`][pydantic_ai.exceptions.ModelAPIError]（4xx/5xx API 错误）上触发，
因此最常见的用例无需任何配置。

此行为由 `fallback_on` 参数控制（参见
[`FallbackModel`][pydantic_ai.models.fallback.FallbackModel]），该参数接受异常类型、
异常处理器和响应处理器；它们都可以是同步或异步的。

!!! note
    Model 所基于的 provider SDK（例如 OpenAI、Anthropic 等）通常内置重试逻辑，这可能会延迟 `FallbackModel` 的激活。

    使用 `FallbackModel` 时，建议禁用 provider SDK retries，以确保能立即 fallback，例如在[自定义 OpenAI client](openai.md#custom-openai-client) 上设置 `max_retries=0`。

在下面的示例中，智能体先向 OpenAI 模型发起请求（由于 API key 无效而失败），然后回退到 Anthropic 模型。

<!-- TODO(Marcelo): Do not skip this test. For some reason it becomes a flaky test if we don't skip it. -->

```python {title="fallback_model.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel

openai_model = OpenAIChatModel('gpt-5.2')
anthropic_model = AnthropicModel('claude-sonnet-4-5')
fallback_model = FallbackModel(openai_model, anthropic_model)

agent = Agent(fallback_model)
response = agent.run_sync('What is the capital of France?')
print(response.data)
#> Paris

print(response.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='What is the capital of France?',
                timestamp=datetime.datetime(...),
                part_kind='user-prompt',
            )
        ],
        kind='request',
    ),
    ModelResponse(
        parts=[TextPart(content='Paris', part_kind='text')],
        model_name='claude-sonnet-4-5',
        timestamp=datetime.datetime(...),
        kind='response',
        provider_response_id=None,
    ),
]
"""
```

上面的 `ModelResponse` 消息在 `model_name` 字段中表明，输出由 `FallbackModel` 中指定的第二个模型 Anthropic 模型返回。

!!! note
    每个模型的选项都应单独配置。例如，`base_url`、`api_key` 和自定义 clients 应设置在各自模型本身上，而不是设置在 `FallbackModel` 上。

### 每个模型的设置 {#per-model-settings}

你可以在创建 fallback chain 中的每个模型时传入 `settings` 参数，为每个模型配置不同的 [`ModelSettings`][pydantic_ai.settings.ModelSettings]。当不同 provider 有不同的最佳配置时，这尤其有用：

```python {title="fallback_model_per_settings.py"}
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel

# Configure each model with provider-specific optimal settings
openai_model = OpenAIChatModel(
    'gpt-5.2',
    settings=ModelSettings(temperature=0.7, max_tokens=1000)  # Higher creativity for OpenAI
)
anthropic_model = AnthropicModel(
    'claude-sonnet-4-5',
    settings=ModelSettings(temperature=0.2, max_tokens=1000)  # Lower temperature for consistency
)

fallback_model = FallbackModel(openai_model, anthropic_model)
agent = Agent(fallback_model)

result = agent.run_sync('Write a creative story about space exploration')
print(result.output)
"""
In the year 2157, Captain Maya Chen piloted her spacecraft through the vast expanse of the Andromeda Galaxy. As she discovered a planet with crystalline mountains that sang in harmony with the cosmic winds, she realized that space exploration was not just about finding new worlds, but about finding new ways to understand the universe and our place within it.
"""
```

在此示例中，如果 OpenAI 模型失败，智能体会自动回退到 Anthropic 模型，并使用 Anthropic 模型自己的配置。`FallbackModel` 本身没有 settings；它使用成功处理请求的具体模型上的独立 settings。

### 异常处理 {#exception-handling}

下一个示例演示 `FallbackModel` 的异常处理能力。
如果所有模型都失败，会引发 [`FallbackExceptionGroup`][pydantic_ai.exceptions.FallbackExceptionGroup]，
其中包含 `run` 执行期间遇到的所有异常。

=== "Python >=3.11"

    ```python {title="fallback_model_failure.py" py="3.11"}
    from pydantic_ai import Agent, ModelAPIError
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.models.fallback import FallbackModel
    from pydantic_ai.models.openai import OpenAIChatModel

    openai_model = OpenAIChatModel('gpt-5.2')
    anthropic_model = AnthropicModel('claude-sonnet-4-5')
    fallback_model = FallbackModel(openai_model, anthropic_model)

    agent = Agent(fallback_model)
    try:
        response = agent.run_sync('What is the capital of France?')
    except* ModelAPIError as exc_group:
        for exc in exc_group.exceptions:
            print(exc)
    ```

=== "Python <3.11"

    由于 [`except*`](https://docs.python.org/3/reference/compound_stmts.html#except-star) 仅在
    Python 3.11+ 中受支持，较早 Python 版本使用 [`exceptiongroup`](https://github.com/agronholm/exceptiongroup) backport
    软件包：

    ```python {title="fallback_model_failure.py" noqa="F821" test="skip"}
    from exceptiongroup import catch

    from pydantic_ai import Agent, ModelAPIError
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.models.fallback import FallbackModel
    from pydantic_ai.models.openai import OpenAIChatModel


    def model_status_error_handler(exc_group: BaseExceptionGroup) -> None:
        for exc in exc_group.exceptions:
            print(exc)


    openai_model = OpenAIChatModel('gpt-5.2')
    anthropic_model = AnthropicModel('claude-sonnet-4-5')
    fallback_model = FallbackModel(openai_model, anthropic_model)

    agent = Agent(fallback_model)
    with catch({ModelAPIError: model_status_error_handler}):
        response = agent.run_sync('What is the capital of France?')
    ```

默认情况下，`FallbackModel` 只有在当前模型引发
[`ModelAPIError`][pydantic_ai.exceptions.ModelAPIError] 时才会切换到下一个模型，其中包括
[`ModelHTTPError`][pydantic_ai.exceptions.ModelHTTPError]。你可以通过向
`FallbackModel` 构造函数传入自定义 `fallback_on` 参数来定制此行为。

!!! note
    验证错误（来自[结构化输出](../output.md#structured-output)或[工具参数](../tools.md)）**不会**触发 fallback。这些错误会改用[重试机制](../agent.md#reflection-and-self-correction)，即重新提示同一个模型再试一次。这是有意设计的：验证错误源于 LLM 的非确定性，重试后可能成功；而 API 错误（4xx/5xx）通常表示继续重试同一请求也无法解决的问题。

### 基于响应的回退 {#response-based-fallback}

除了基于异常的 fallback，你也可以根据模型响应的**内容**触发 fallback。当模型返回成功的 HTTP 响应（没有异常），但响应内容表明存在语义失败时，这很有用，例如意外的 finish reason 或原生工具报告失败。

!!! note "仅限非流式"
    基于响应的 fallback 目前仅适用于非流式请求（`agent.run()` 和 `agent.run_sync()`）。
    对于流式请求（`agent.run_stream()`），仅支持基于异常的 fallback。

`fallback_on` 参数接受：

- 异常类型元组：`(ModelAPIError, ModelHTTPError)`
- 异常处理器（同步或异步）：`lambda exc: isinstance(exc, MyError)`
- 响应处理器（同步或异步）：`def check(r: ModelResponse) -> bool`
- 混合以上内容的列表：`[ModelAPIError, exc_handler, response_handler]`

处理器类型会通过检查第一个参数的 type hints 自动检测。如果第一个参数标注为 [`ModelResponse`][pydantic_ai.messages.ModelResponse]，它就是响应处理器。否则（包括未类型标注的处理器和 lambdas），它就是异常处理器。

#### Finish reason 示例 {#finish-reason-example}

一个简单用例是检查模型的 finish reason，例如当响应因长度限制被截断时 fallback：

```python {title="fallback_on_finish_reason.py"}
from pydantic_ai import Agent
from pydantic_ai.messages import FinishReason, ModelResponse
from pydantic_ai.models.fallback import FallbackModel


def bad_finish_reason(response: ModelResponse) -> bool:
    """Fallback if the model stopped due to length limit, content filter, or error."""
    reason: FinishReason | None = response.finish_reason
    # Trigger fallback for problematic finish reasons
    return reason in ('length', 'content_filter', 'error')


fallback_model = FallbackModel(
    'openai:gpt-5.2',
    'anthropic:claude-sonnet-4-5',
    fallback_on=bad_finish_reason,
)

agent = Agent(fallback_model)
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

!!! warning "单独的响应处理器会替换默认异常 fallback"
    当你像上面那样把单个响应处理器作为 `fallback_on` 传入时，它会**完全替换**默认的 `(ModelAPIError,)` 异常 fallback。这意味着 API 错误（4xx/5xx）会作为异常向外传播，而不会触发到下一个模型的 fallback。

    要在响应处理器之外保留基于异常的 fallback，请把它们一起作为列表传入；参见下面的[混合示例](#combining-handlers)。

!!! note
    注意，Pydantic AI 已经在[智能体循环](../agent.md)中自动处理了一些 finish reasons：
    finish reason 为 `'length'` 或 `'content_filter'` 的响应会引发异常（`FallbackModel`
    默认会捕获这些异常），空响应会被重试。响应处理器适用于这些内置行为之外的自定义检查。

#### 原生工具失败示例 {#native-tool-failure-example}

更复杂的用例是使用 web search 或 URL fetching 等原生工具。例如，Google 的 [`WebFetchTool`][pydantic_ai.native_tools.WebFetchTool] 可能返回成功响应，但其中的状态表明 URL fetch 失败：

```python {title="fallback_on_native_tool.py"}
from pydantic_ai import Agent
from pydantic_ai.messages import ModelResponse
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel


def web_fetch_failed(response: ModelResponse) -> bool:
    """Check if a web_fetch native tool failed to retrieve content."""
    for call, result in response.native_tool_calls:
        if call.tool_name != 'web_fetch':
            continue
        if not isinstance(result.content, list):
            continue
        for item in result.content:
            if isinstance(item, dict):
                status = item.get('url_retrieval_status', '')
                if status and status != 'URL_RETRIEVAL_STATUS_SUCCESS':
                    return True
    return False


google_model = GoogleModel('gemini-2.5-flash')
anthropic_model = AnthropicModel('claude-sonnet-4-5')

# Auto-detected as response handler via type hint
fallback_model = FallbackModel(
    google_model,
    anthropic_model,
    fallback_on=web_fetch_failed,
)

agent = Agent(fallback_model)

# If Google's web_fetch fails, automatically falls back to Anthropic
result = agent.run_sync('Summarize https://ai.pydantic.dev')
print(result.output)
"""
Pydantic AI is a Python agent framework for building production-grade LLM applications.
"""
```

响应处理器会接收模型返回的 [`ModelResponse`][pydantic_ai.messages.ModelResponse]，并应返回 `True` 来触发到下一个模型的 fallback，或返回 `False` 接受该响应。

#### 组合处理器 {#combining-handlers}

你可以在单个列表中组合异常类型、异常处理器和响应处理器：

```python {title="fallback_on_mixed.py" requires="fallback_on_native_tool.py"}
from pydantic_ai.exceptions import ModelAPIError
from pydantic_ai.models.fallback import FallbackModel

from fallback_on_native_tool import anthropic_model, google_model, web_fetch_failed

fallback_model = FallbackModel(
    google_model,
    anthropic_model,
    fallback_on=[
        ModelAPIError,  # Exception type
        lambda exc: 'rate limit' in str(exc).lower(),  # Exception handler (untyped lambda)
        web_fetch_failed,  # Response handler (auto-detected via type hint)
    ],
)
```

### Middleware 和装饰器中的异常处理 {#exception-handling-in-middleware-and-decorators}

使用 `FallbackModel` 时，一个重要点是：[`FallbackExceptionGroup`][pydantic_ai.exceptions.FallbackExceptionGroup]
继承自 Python 的 [`ExceptionGroup`](https://docs.python.org/3/library/exceptions.html#ExceptionGroup)。这意味着
现有捕获特定异常（例如 `ModelAPIError`）的异常处理代码，不会自动捕获 group 中包装的各个异常。

例如，如果你有捕获 `ModelAPIError` 的 middleware 或装饰器：

```python {title="middleware_without_fallback.py"}
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from pydantic_ai import ModelAPIError

T = TypeVar('T')


# This handler will NOT catch ModelAPIError when using FallbackModel!
def handle_api_errors(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except ModelAPIError as e:  # Won't catch FallbackExceptionGroup
            print(f'API error: {e}')
            raise

    return wrapper
```

这个装饰器在使用 `FallbackModel` 时会漏掉 `ModelAPIError` 异常，因为这些异常被包装在
`FallbackExceptionGroup` 中，其中每个失败模型对应一个异常，顺序与尝试模型的顺序一致。

要同时处理两种情况，可以使用 Python 3.11+ 的 `except*` 语法；它既能捕获 exception groups 中匹配的异常，也能捕获裸异常。注意，`except*` 总是把捕获到的异常作为
`ExceptionGroup` 交付（即使原始异常是裸异常），因此重新抛出时会传播 `ExceptionGroup`
而不是原始异常类型：

=== "Python >=3.11"

    ```python {title="middleware_with_fallback.py" py="3.11"}
    from collections.abc import Callable
    from functools import wraps
    from typing import TypeVar

    from pydantic_ai import ModelAPIError

    T = TypeVar('T')


    def handle_api_errors(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except* ModelAPIError as exc_group:
                for exc in exc_group.exceptions:
                    print(f'API error: {exc}')
                raise

        return wrapper
    ```

=== "Python <3.11"

    ```python {title="middleware_with_fallback.py" noqa="F821" test="skip"}
    from collections.abc import Callable
    from functools import wraps
    from typing import TypeVar

    from pydantic_ai import FallbackExceptionGroup, ModelAPIError

    T = TypeVar('T')


    def handle_api_errors(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except FallbackExceptionGroup as exc_group:
                for exc in exc_group.exceptions:
                    if isinstance(exc, ModelAPIError):
                        print(f'API error from fallback: {exc}')
                raise
            except ModelAPIError as e:
                print(f'API error: {e}')
                raise

        return wrapper
    ```

你也可以直接捕获 `FallbackExceptionGroup`，如果你想专门处理它：

```python {title="catch_fallback_exception_group.py" test="skip"}
from pydantic_ai import Agent, FallbackExceptionGroup
from pydantic_ai.models.fallback import FallbackModel

agent = Agent(FallbackModel('openai:gpt-5-mini', 'anthropic:claude-sonnet-4-6'))

try:
    response = agent.run_sync('What is the capital of France?')
except FallbackExceptionGroup as exc_group:
    print(f'All {len(exc_group.exceptions)} models failed:')
    for exc in exc_group.exceptions:
        print(f'  - {exc}')
```
