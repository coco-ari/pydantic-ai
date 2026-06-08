# Bedrock

## 安装 {#install}

要使用 `BedrockConverseModel`，你需要安装 `pydantic-ai`，或安装带 `bedrock` 可选依赖组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[bedrock]"
```

## 配置 {#configuration}

要使用 [AWS Bedrock](https://aws.amazon.com/bedrock/)，你需要一个已启用 Bedrock 且具备适当凭据的 AWS 账号。你可以直接使用 AWS 凭据，也可以使用预配置的 boto3 client。

`BedrockModelName` 包含可用 Bedrock 模型列表，包括来自 Anthropic、Amazon、Cohere、Meta 和 Mistral 的模型。

## 环境变量 {#environment-variables}

你可以把 AWS 凭据设置为环境变量（也可以使用[其他选项](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables)）：

```bash
export AWS_BEARER_TOKEN_BEDROCK='your-api-key'
# or:
export AWS_ACCESS_KEY_ID='your-access-key'
export AWS_SECRET_ACCESS_KEY='your-secret-key'
export AWS_DEFAULT_REGION='us-east-1'  # or your preferred region
```

然后可以按名称使用 `BedrockConverseModel`：

```python
from pydantic_ai import Agent

agent = Agent('bedrock:anthropic.claude-sonnet-4-5-20250929-v1:0')
...
```

或者只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel

model = BedrockConverseModel('anthropic.claude-sonnet-4-5-20250929-v1:0')
agent = Agent(model)
...
```

## 自定义 Bedrock Runtime API {#customizing-bedrock-runtime-api}

你可以通过添加额外参数来自定义 Bedrock Runtime API 调用，例如 [guardrail 配置](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)和[性能设置](https://docs.aws.amazon.com/bedrock/latest/userguide/latency-optimized-inference.html)。完整的可配置参数列表请参考 [`BedrockModelSettings`][pydantic_ai.models.bedrock.BedrockModelSettings] 文档。

```python {title="customize_bedrock_model_settings.py"}
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings

# Define Bedrock model settings with guardrail and performance configurations
bedrock_model_settings = BedrockModelSettings(
    bedrock_guardrail_config={
        'guardrailIdentifier': 'v1',
        'guardrailVersion': 'v1',
        'trace': 'enabled'
    },
    bedrock_performance_configuration={
        'latency': 'optimized'
    }
)


model = BedrockConverseModel(model_name='us.amazon.nova-pro-v1:0')

agent = Agent(model=model, model_settings=bedrock_model_settings)
```

## 服务层级 {#service-tier}

Bedrock 支持控制[服务层级](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)，用于管理吞吐量和成本。
你可以使用统一的 [`service_tier`][pydantic_ai.settings.ModelSettings.service_tier] 字段，也可以使用 provider-specific 的 [`bedrock_service_tier`][pydantic_ai.models.bedrock.BedrockModelSettings.bedrock_service_tier] 字段。两者同时设置时，`bedrock_service_tier` 优先于统一字段。

Bedrock 对统一字段的映射如下：

- `'auto'`：请求中省略 `serviceTier` 字段，因此 AWS 会应用其服务端默认值（Standard tier）。
- `'default'`：显式发送为 `{'type': 'default'}`，表示退出任何未来可能的服务端自动晋升到高级层级行为。
- `'flex'`：发送为 `{'type': 'flex'}`。
- `'priority'`：发送为 `{'type': 'priority'}`。

要请求 Bedrock 的 `'reserved'` tier（需要预先购买的容量预留），请直接设置 [`bedrock_service_tier`][pydantic_ai.models.bedrock.BedrockModelSettings.bedrock_service_tier]；它无法通过统一字段访问。

## Prompt 缓存 {#prompt-caching}

Bedrock 在 Anthropic 模型上支持 [prompt caching](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)，让你可以跨请求复用昂贵的上下文。Pydantic AI 提供四种使用 prompt caching 的方式：

1. **使用 [`CachePoint`][pydantic_ai.messages.CachePoint] 缓存用户消息**：插入 `CachePoint` 标记，以缓存当前用户消息中它之前的所有内容。传入 `CachePoint(ttl='1h')` 可以启用扩展缓存时长。
2. **缓存系统 instructions**：将 [`BedrockModelSettings.bedrock_cache_instructions`][pydantic_ai.models.bedrock.BedrockModelSettings.bedrock_cache_instructions] 设置为 `True`（默认使用 5m TTL），或直接指定 `'5m'` / `'1h'`。当你同时拥有静态和动态 [instructions](../agent.md#instructions) 时，缓存点会放在最后一个静态 instruction 之后，因此动态 instructions 可以变化而不会使静态缓存失效。
3. **缓存工具定义**：将 [`BedrockModelSettings.bedrock_cache_tool_definitions`][pydantic_ai.models.bedrock.BedrockModelSettings.bedrock_cache_tool_definitions] 设置为 `True`（默认使用 5m TTL），或直接指定 `'5m'` / `'1h'`。
4. **缓存所有消息**：将 [`BedrockModelSettings.bedrock_cache_messages`][pydantic_ai.models.bedrock.BedrockModelSettings.bedrock_cache_messages] 设置为 `True`（默认使用 5m TTL），或直接指定 `'5m'` / `'1h'`，以自动缓存最后一条用户消息。

!!! note "最小 token 阈值"
    AWS 只有在某个片段超过 provider-specific 的最小 token 阈值后才会提供缓存内容（见 [Bedrock prompt caching 文档](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)）。低于这些限制的短 prompt 或工具定义会绕过缓存，因此不要期待小载荷能节省成本。

### 示例 1：自动消息缓存 {#example-1-automatic-message-caching}

使用 `bedrock_cache_messages` 自动缓存最后一条用户消息：

```python {test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockModelSettings

agent = Agent(
    'bedrock:us.anthropic.claude-sonnet-4-5-20250929-v1:0',
    system_prompt='You are a helpful assistant.',
    model_settings=BedrockModelSettings(
        bedrock_cache_messages=True,  # Automatically caches the last message
    ),
)

# The last message is automatically cached - no need for manual CachePoint
result1 = agent.run_sync('What is the capital of France?')

# Subsequent calls with similar conversation benefit from cache
result2 = agent.run_sync('What is the capital of Germany?')
print(f'Cache write: {result1.usage.cache_write_tokens}')
print(f'Cache read: {result2.usage.cache_read_tokens}')
```

### 示例 2：全面缓存策略 {#example-2-comprehensive-caching-strategy}

组合多个缓存设置以最大化节省：

```python {test="skip"}
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings

model = BedrockConverseModel('us.anthropic.claude-sonnet-4-5-20250929-v1:0')
agent = Agent(
    model,
    system_prompt='Detailed instructions...',
    model_settings=BedrockModelSettings(
        bedrock_cache_instructions=True,       # Cache system instructions
        bedrock_cache_tool_definitions='1h',   # Cache tool definitions with 1h TTL
        bedrock_cache_messages=True,           # Also cache the last message
    ),
)


@agent.tool
def search_docs(ctx: RunContext, query: str) -> str:
    """Search documentation."""
    return f'Results for {query}'


result = agent.run_sync('Search for Python best practices')
print(result.output)
```

### 示例 3：使用 CachePoint 进行细粒度控制 {#example-3-fine-grained-control-with-cachepoint}

使用手动 `CachePoint` 标记精确控制缓存位置：

```python {test="skip"}
from pydantic_ai import Agent, CachePoint

agent = Agent(
    'bedrock:us.anthropic.claude-sonnet-4-5-20250929-v1:0',
    system_prompt='Instructions...',
)

# Manually control cache points for specific content blocks
result = agent.run_sync([
    'Long context from documentation...',
    CachePoint(),  # Cache everything up to this point
    'First question'
])
print(result.output)
```

### 访问缓存用量统计 {#accessing-cache-usage-statistics}

通过 [`RequestUsage`][pydantic_ai.usage.RequestUsage] 访问缓存用量统计：

```python {test="skip"}
from pydantic_ai import Agent, CachePoint

agent = Agent('bedrock:us.anthropic.claude-sonnet-4-5-20250929-v1:0')


async def main():
    result = await agent.run(
        [
            'Reference material...',
            CachePoint(),
            'What changed since last time?',
        ]
    )
    usage = result.usage
    print(f'Cache writes: {usage.cache_write_tokens}')
    print(f'Cache reads: {usage.cache_read_tokens}')
```

### 缓存点限制 {#cache-point-limits}

Bedrock 每个请求最多允许 4 个缓存点。Pydantic AI 会自动管理这个限制，确保你的请求始终合规且不会出错。

#### 缓存点如何分配 {#how-cache-points-are-allocated}

缓存点可以放在三个位置：

1. **System Prompt**：通过 `bedrock_cache_instructions` 设置（向最后一个 system prompt block 添加缓存点）
2. **工具定义**：通过 `bedrock_cache_tool_definitions` 设置（向最后一个工具定义添加缓存点）
3. **消息**：通过 `CachePoint` 标记或 `bedrock_cache_messages` 设置（向消息内容添加缓存点）

每个设置**最多使用 1 个缓存点**，但你可以组合它们。

#### 自动限制缓存点 {#automatic-cache-point-limiting}

当所有来源（设置 + `CachePoint` 标记）的缓存点超过 4 个时，Pydantic AI 会自动从**较旧的消息内容**中移除多余缓存点（保留最近的缓存点）。

```python {test="skip"}
from pydantic_ai import Agent, CachePoint
from pydantic_ai.models.bedrock import BedrockModelSettings

agent = Agent(
    'bedrock:us.anthropic.claude-sonnet-4-5-20250929-v1:0',
    system_prompt='Instructions...',
    model_settings=BedrockModelSettings(
        bedrock_cache_instructions=True,      # 1 cache point
        bedrock_cache_tool_definitions=True,  # 1 cache point
    ),
)

@agent.tool_plain
def search() -> str:
    return 'data'


# Already using 2 cache points (instructions + tools)
# Can add 2 more CachePoint markers (4 total limit)
result = agent.run_sync([
    'Context 1', CachePoint(),  # Oldest - will be removed
    'Context 2', CachePoint(),  # Will be kept (3rd point)
    'Context 3', CachePoint(),  # Will be kept (4th point)
    'Question'
])
# Final cache points: instructions + tools + Context 2 + Context 3 = 4
print(result.output)
```

**要点**：

- System 和工具缓存点会**始终保留**
- `bedrock_cache_messages` 创建的缓存点会**始终保留**（因为它是最新的消息缓存点）
- 当超过限制时，消息中的额外 `CachePoint` 标记会从旧到新移除
- 这会确保关键缓存（instructions/tools）得到保留，同时仍然能从消息级缓存获益

## `provider` 参数 {#provider-argument}

你可以通过 `provider` 参数提供自定义 `BedrockProvider`。当你想直接指定凭据或使用自定义 boto3 client 时，这很有用：

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

# Using AWS credentials directly
model = BedrockConverseModel(
    'anthropic.claude-sonnet-4-5-20250929-v1:0',
    provider=BedrockProvider(
        region_name='us-east-1',
        aws_access_key_id='your-access-key',
        aws_secret_access_key='your-secret-key',
    ),
)
agent = Agent(model)
...
```

也可以传入预配置的 boto3 client：

```python
import boto3

from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

# Using a pre-configured boto3 client
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
model = BedrockConverseModel(
    'anthropic.claude-sonnet-4-5-20250929-v1:0',
    provider=BedrockProvider(bedrock_client=bedrock_client),
)
agent = Agent(model)
...
```

## 使用 AWS Application Inference Profiles {#using-aws-application-inference-profiles}

AWS Bedrock 支持用于成本跟踪和资源管理的[自定义 application inference profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-create.html)。设置 [`bedrock_inference_profile`][pydantic_ai.models.bedrock.BedrockModelSettings.bedrock_inference_profile] 可通过 inference profile 路由请求，同时保留基础模型名称用于检测模型能力：

```python
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

provider = BedrockProvider(region_name='us-east-2')

model = BedrockConverseModel(
    'us.anthropic.claude-opus-4-5-20251101-v1:0',
    provider=provider,
    settings={
        'bedrock_inference_profile': 'arn:aws:bedrock:us-east-2:123456789012:application-inference-profile/my-profile',
    },
)

agent = Agent(model)
```

## 配置重试 {#configuring-retries}

Bedrock 使用 boto3 内置的重试机制。你可以通过传入带重试设置的自定义 boto3 client 来配置重试行为：

```python
import boto3
from botocore.config import Config

from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

# Configure retry settings
config = Config(
    retries={
        'max_attempts': 5,
        'mode': 'adaptive'  # Recommended for rate limiting
    }
)

bedrock_client = boto3.client(
    'bedrock-runtime',
    region_name='us-east-1',
    config=config
)

model = BedrockConverseModel(
    'us.amazon.nova-micro-v1:0',
    provider=BedrockProvider(bedrock_client=bedrock_client),
)
agent = Agent(model)
```

### 重试模式 {#retry-modes}

- `'legacy'`（默认）：5 次尝试，基础重试行为
- `'standard'`：3 次尝试，覆盖更全面的错误
- `'adaptive'`：3 次尝试，并带客户端侧限流（推荐用于处理 `ThrottlingException`）

关于 boto3 重试配置的更多细节，请参阅 [AWS boto3 文档](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/retries.html)。

!!! note
    与其他使用 httpx 进行 HTTP 请求的 providers 不同，Bedrock 使用 boto3 的原生重试机制。[HTTP 请求重试](../retries.md)中描述的重试策略不适用于 Bedrock。
