# HTTP 请求重试

Pydantic AI 通过自定义 HTTP transports 为模型提供商发起的 HTTP 请求提供重试功能。
这对于处理限流、网络超时或临时服务器错误等瞬时故障特别有用。

## 概览

重试功能构建在 [tenacity](https://github.com/jd/tenacity) 库之上，并与 httpx clients 无缝集成。你可以为任何接受自定义 HTTP client 的 provider 配置重试行为。

## 安装

要使用 retry transports，需要安装 `tenacity`，可以通过 `retries` 依赖组安装：

```bash
pip/uv-add 'pydantic-ai-slim[retries]'
```

## 使用示例

下面是一个添加重试功能并使用智能重试处理的示例：

```python {title="smart_retry_example.py"}
from httpx import AsyncClient, HTTPStatusError
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after


def create_retrying_client():
    """Create a client with smart retry handling for multiple error types."""

    def should_retry_status(response):
        """Raise exceptions for retryable HTTP status codes."""
        if response.status_code in (429, 502, 503, 504):
            response.raise_for_status()  # This will raise HTTPStatusError

    transport = AsyncTenacityTransport(
        config=RetryConfig(
            # Retry on HTTP errors and connection issues
            retry=retry_if_exception_type((HTTPStatusError, ConnectionError)),
            # Smart waiting: respects Retry-After headers, falls back to exponential backoff
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=1, max=60),
                max_wait=300
            ),
            # Stop after 5 attempts
            stop=stop_after_attempt(5),
            # Re-raise the last exception if all retries fail
            reraise=True
        ),
        validate_response=should_retry_status
    )
    return AsyncClient(transport=transport)

# Use the retrying client with a model
client = create_retrying_client()
model = OpenAIChatModel('gpt-5.2', provider=OpenAIProvider(http_client=client))
agent = Agent(model)
```

## 等待策略

### wait_retry_after

`wait_retry_after` 函数是一种智能等待策略，会自动遵守 HTTP `Retry-After` headers：

```python {title="wait_strategy_example.py"}
from tenacity import wait_exponential

from pydantic_ai.retries import wait_retry_after

# Basic usage - respects Retry-After headers, falls back to exponential backoff
wait_strategy_1 = wait_retry_after()

# Custom configuration
wait_strategy_2 = wait_retry_after(
    fallback_strategy=wait_exponential(multiplier=2, max=120),
    max_wait=600  # Never wait more than 10 minutes
)
```

这个等待策略会：

- 自动解析 HTTP 429 响应中的 `Retry-After` headers
- 同时支持秒数格式（`"30"`）和 HTTP 日期格式（`"Wed, 21 Oct 2015 07:28:00 GMT"`）
- 当 header 不存在时，fallback 到你选择的策略
- 遵守 `max_wait` 限制，防止过长延迟

## Transport 类

### AsyncTenacityTransport

用于异步 HTTP clients（推荐用于大多数用例）：

```python {title="async_transport_example.py"}
from httpx import AsyncClient
from tenacity import stop_after_attempt

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig


def validator(response):
    """Treat responses with HTTP status 4xx/5xx as failures that need to be retried.
    Without a response validator, only network errors and timeouts will result in a retry.
    """
    response.raise_for_status()

# Create the transport
transport = AsyncTenacityTransport(
    config=RetryConfig(stop=stop_after_attempt(3), reraise=True),
    validate_response=validator
)

# Create a client using the transport:
client = AsyncClient(transport=transport)
```

### TenacityTransport

用于同步 HTTP clients：

```python {title="sync_transport_example.py"}
from httpx import Client
from tenacity import stop_after_attempt

from pydantic_ai.retries import RetryConfig, TenacityTransport


def validator(response):
    """Treat responses with HTTP status 4xx/5xx as failures that need to be retried.
    Without a response validator, only network errors and timeouts will result in a retry.
    """
    response.raise_for_status()

# Create the transport
transport = TenacityTransport(
    config=RetryConfig(stop=stop_after_attempt(3), reraise=True),
    validate_response=validator
)

# Create a client using the transport
client = Client(transport=transport)
```

## 常见重试模式

### 使用 Retry-After 支持处理限流

```python {title="rate_limit_handling.py"}
from httpx import AsyncClient, HTTPStatusError
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after


def create_rate_limit_client():
    """Create a client that respects Retry-After headers from rate limiting responses."""
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type(HTTPStatusError),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=1, max=60),
                max_wait=300  # Don't wait more than 5 minutes
            ),
            stop=stop_after_attempt(10),
            reraise=True
        ),
        validate_response=lambda r: r.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx
    )
    return AsyncClient(transport=transport)

# Example usage
client = create_rate_limit_client()
# Client is now ready to use with any HTTP requests and will respect Retry-After headers
```

`wait_retry_after` 函数会自动检测 429（rate limit）响应中的 `Retry-After` headers，并等待指定时间。如果不存在 header，则 fallback 到 exponential backoff。

### 网络错误处理

```python {title="network_error_handling.py"}
import httpx
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig


def create_network_resilient_client():
    """Create a client that handles network errors with retries."""
    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type((
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.ReadError
            )),
            wait=wait_exponential(multiplier=1, max=10),
            stop=stop_after_attempt(3),
            reraise=True
        )
    )
    return httpx.AsyncClient(transport=transport)

# Example usage
client = create_network_resilient_client()
# Client will now retry on timeout, connection, and read errors
```

### 自定义重试逻辑

```python {title="custom_retry_logic.py"}
import httpx
from tenacity import retry_if_exception, stop_after_attempt, wait_exponential

from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after


def create_custom_retry_client():
    """Create a client with custom retry logic."""
    def custom_retry_condition(exception):
        """Custom logic to determine if we should retry."""
        if isinstance(exception, httpx.HTTPStatusError):
            # Retry on server errors but not client errors
            return 500 <= exception.response.status_code < 600
        return isinstance(exception, httpx.TimeoutException | httpx.ConnectError)

    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception(custom_retry_condition),
            # Use wait_retry_after for smart waiting on rate limits,
            # with custom exponential backoff as fallback
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=2, max=30),
                max_wait=120
            ),
            stop=stop_after_attempt(5),
            reraise=True
        ),
        validate_response=lambda r: r.raise_for_status()
    )
    return httpx.AsyncClient(transport=transport)

client = create_custom_retry_client()
# Client will retry server errors (5xx) and network errors, but not client errors (4xx)
```

## 与不同 Providers 一起使用

Retry transports 可用于任何接受自定义 HTTP client 的 provider：

### OpenAI

```python {title="openai_with_retries.py" requires="smart_retry_example.py"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from smart_retry_example import create_retrying_client

client = create_retrying_client()
model = OpenAIChatModel('gpt-5.2', provider=OpenAIProvider(http_client=client))
agent = Agent(model)
```

### Anthropic

```python {title="anthropic_with_retries.py" requires="smart_retry_example.py"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from smart_retry_example import create_retrying_client

client = create_retrying_client()
model = AnthropicModel('claude-sonnet-4-5-20250929', provider=AnthropicProvider(http_client=client))
agent = Agent(model)
```

### 任何 OpenAI 兼容 Provider

```python {title="openai_compatible_with_retries.py" requires="smart_retry_example.py"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from smart_retry_example import create_retrying_client

client = create_retrying_client()
model = OpenAIChatModel(
    'your-model-name',  # Replace with actual model name
    provider=OpenAIProvider(
        base_url='https://api.example.com/v1',  # Replace with actual API URL
        api_key='your-api-key',  # Replace with actual API key
        http_client=client
    )
)
agent = Agent(model)
```

## 最佳实践

1. **保守起步**：从较少的重试次数（3-5 次）和合理等待时间开始。

2. **使用 Exponential Backoff**：这有助于在服务故障期间避免压垮服务器。

3. **设置最大等待时间**：通过合理的最大等待时间防止无限延迟。

4. **正确处理 Rate Limits**：尽可能遵守 `Retry-After` headers。

5. **记录重试尝试**：添加日志以在生产环境监控重试行为。（如果你对 httpx 进行了插桩，Logfire 会自动捕获这些信息。）

6. **考虑 Circuit Breakers**：对于高流量应用，可以考虑实现 circuit breaker 模式。

!!! tip "在生产环境监控重试"
    过多重试可能表明存在底层问题并增加成本。[Logfire](logfire.md) 可以帮助你跟踪重试模式：

    - 查看哪些请求触发了重试
    - 理解重试原因（rate limits、server errors、timeouts）
    - 随时间监控重试频率
    - 识别减少重试的机会

    启用 [HTTPX instrumentation](logfire.md#monitoring-http-requests) 后，重试尝试会自动捕获到你的 traces 中。

## 错误处理

如果所有重试尝试都失败，retry transports 会重新抛出最后一个异常。请确保在应用中适当处理这些异常：

```python {title="error_handling_example.py" requires="smart_retry_example.py"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from smart_retry_example import create_retrying_client

client = create_retrying_client()
model = OpenAIChatModel('gpt-5.2', provider=OpenAIProvider(http_client=client))
agent = Agent(model)
```

## 性能考虑

- 重试会增加请求延迟，尤其是在使用 exponential backoff 时
- 配置重试行为时，要考虑应用的总超时时间
- 监控重试率以检测系统性问题
- 处理多个请求时，使用 async transports 可获得更好的并发能力

关于更高级的重试配置，请参阅 [tenacity 文档](https://tenacity.readthedocs.io/)。

## Provider-Specific 重试行为

### AWS Bedrock

AWS Bedrock provider 使用 boto3 的内置重试机制，而不是 httpx。要为 Bedrock 配置重试，请使用 boto3 的 `Config`：

```python
from botocore.config import Config

config = Config(retries={'max_attempts': 5, 'mode': 'adaptive'})
```

完整示例见 [Bedrock: Configuring Retries](models/bedrock.md#configuring-retries)。
