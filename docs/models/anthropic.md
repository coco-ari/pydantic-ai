# Anthropic

## 安装 {#install}

要使用 `AnthropicModel` 模型，你需要安装 `pydantic-ai`，或者安装带 `anthropic` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[anthropic]"
```

## 配置 {#configuration}

要通过 [Anthropic](https://anthropic.com) API 使用 Anthropic，请前往 [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) 生成 API key。

`AnthropicModelName` 包含可用 Anthropic 模型列表。

## 环境变量 {#environment-variable}

拿到 API key 后，可以将其设置为环境变量：

```bash
export ANTHROPIC_API_KEY='your-api-key'
```

然后你可以按名称使用 `AnthropicModel`：

```python
from pydantic_ai import Agent

agent = Agent('anthropic:claude-sonnet-4-6')
...
```

或者只用模型名称直接初始化模型：

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel

model = AnthropicModel('claude-sonnet-4-5')
agent = Agent(model)
...
```

!!! note "Claude Opus 4.7 / 4.8 迁移"
    Anthropic 的 [Claude Opus migration guide](https://platform.claude.com/docs/en/about-claude/models/migration-guide) 建议从 Opus 4.7 和 4.8 请求中移除 `temperature`、`top_p` 和 `top_k`。Pydantic AI 会针对 `claude-opus-4-7` 和 `claude-opus-4-8` 自动丢弃这些 keys，包括 `extra_body` overrides。

    同一指南还建议从 Opus 4.6 迁移时重新评估 `max_tokens` 和任何 token 计数假设，因为 Opus 4.7 引入了更新后的 tokenization（延续到 4.8）。如果你依赖 `count_tokens()` 或 `count_tokens_before_request`，请根据新模型验证你的阈值。

## `provider` 参数 {#provider-argument}

你可以通过 `provider` 参数提供自定义 `Provider`：

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

model = AnthropicModel(
    'claude-sonnet-4-5', provider=AnthropicProvider(api_key='your-api-key')
)
agent = Agent(model)
...
```

## 自定义 HTTP Client {#custom-http-client}

你可以使用自定义 `httpx.AsyncClient` 来定制 `AnthropicProvider`：

```python
from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

custom_http_client = AsyncClient(timeout=30)
model = AnthropicModel(
    'claude-sonnet-4-5',
    provider=AnthropicProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...
```

## 模型设置 {#model-settings}

你可以使用 [`AnthropicModelSettings`][pydantic_ai.models.anthropic.AnthropicModelSettings] 定制模型行为：

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings

model = AnthropicModel('claude-sonnet-4-5')
settings = AnthropicModelSettings(
    temperature=0.2,
    service_tier='auto',
)
agent = Agent(model, model_settings=settings)
...
```

### 服务层级 {#service-tier}

Anthropic 支持控制 [service tier](https://docs.anthropic.com/en/docs/build-with-claude/latency-and-throughput) 来管理延迟和吞吐量。
你可以使用统一的 [`service_tier`][pydantic_ai.settings.ModelSettings.service_tier] 字段，或 provider 专用的 [`anthropic_service_tier`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_service_tier] 字段。当两者同时设置时，`anthropic_service_tier` 优先于统一字段，并接受 Anthropic 的原生值（`'auto'` 或 `'standard_only'`）。

Anthropic 的统一字段映射如下：

- `'auto'`：原样传递为 `'auto'`（Anthropic 的原生值，会在可用时使用 priority capacity）。
- `'default'`：映射为 `'standard_only'`（强制使用 standard tier，不使用 priority capacity）。
- `'flex'` 和 `'priority'` 不属于 Anthropic 的 tier model，会被静默忽略。

## 云平台集成 {#cloud-platform-integrations}

你可以通过向 [`AnthropicProvider`][pydantic_ai.providers.anthropic.AnthropicProvider] 传入自定义 client，经由云平台使用 Anthropic 模型。

### AWS Bedrock {#aws-bedrock}

要通过 [AWS Bedrock](https://aws.amazon.com/bedrock/claude/) 使用 Claude 模型，请按照 [Anthropic documentation](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock) 设置 Bedrock client，然后将其传给 `AnthropicProvider`。较新的 `AsyncAnthropicBedrockMantle` client（Anthropic 推荐，使用 Messages API）和旧版 `AsyncAnthropicBedrock` client（使用带 ARN-versioned model IDs 的 `InvokeModel` API）均受支持：

```python {test="skip"}
from anthropic import AsyncAnthropicBedrockMantle

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

bedrock_client = AsyncAnthropicBedrockMantle()  # Uses AWS credentials from environment
provider = AnthropicProvider(anthropic_client=bedrock_client)
model = AnthropicModel('anthropic.claude-haiku-4-5', provider=provider)
agent = Agent(model)
...
```

!!! note "Bedrock 与 BedrockConverseModel"
    此方法使用 Anthropic 的 SDK 和 AWS Bedrock 凭据。如需直接使用 AWS SDK (boto3) 的替代方案，请参阅 [`BedrockConverseModel`](bedrock.md)。

!!! note "旧版 `AsyncAnthropicBedrock` client 上的工具搜索"
    旧版 `InvokeModel` API 不支持 `bm25` [工具搜索](../tools-advanced.md#tool-search)变体，因此 [`ToolSearch`][pydantic_ai.capabilities.ToolSearch] 在 `AsyncAnthropicBedrock` client 上默认使用 `'regex'`（而不是 `'bm25'`），传入 `ToolSearch(strategy='bm25')` 会引发 `UserError`。

### Google Cloud {#google-cloud}

要通过 [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/use-claude) 使用 Claude 模型，请按照 [Anthropic documentation](https://docs.anthropic.com/en/api/claude-on-vertex-ai) 设置 `AsyncAnthropicVertex` client，然后将其传给 `AnthropicProvider`：

```python {test="skip"}
from anthropic import AsyncAnthropicVertex

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

vertex_client = AsyncAnthropicVertex(region='us-east5', project_id='your-project-id')
provider = AnthropicProvider(anthropic_client=vertex_client)
model = AnthropicModel('claude-sonnet-4-5', provider=provider)
agent = Agent(model)
...
```

### Microsoft Foundry {#microsoft-foundry}

要通过 [Microsoft Foundry](https://ai.azure.com/) 使用 Claude 模型，请按照 [Anthropic documentation](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry) 设置 `AsyncAnthropicFoundry` client，然后将其传给 `AnthropicProvider`：

```python {test="skip"}
from anthropic import AsyncAnthropicFoundry

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

foundry_client = AsyncAnthropicFoundry(
    api_key='your-foundry-api-key',  # Or set ANTHROPIC_FOUNDRY_API_KEY
    resource='your-resource-name',
)
provider = AnthropicProvider(anthropic_client=foundry_client)
model = AnthropicModel('claude-sonnet-4-5', provider=provider)
agent = Agent(model)
...
```

有关包括 Entra ID authentication 在内的设置说明，请参阅 [Anthropic's Microsoft Foundry documentation](https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry)。

## 任务预算（Beta） {#task-budgets-beta}

Anthropic 的 [task budgets](https://platform.claude.com/docs/en/build-with-claude/task-budgets) 允许你为完整 agentic loop 提供一个建议性 token budget，包括 thinking、tool calls、tool results 和 output，从而让模型随着预算消耗调整节奏并优雅完成。通过 [`AnthropicModelSettings.anthropic_task_budget`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_task_budget] 配置它们；该字段接受 [`AnthropicTaskBudget`][pydantic_ai.models.anthropic.AnthropicTaskBudget] payload，并映射到 `output_config.task_budget`。

当此设置存在时，Pydantic AI 会自动启用 Anthropic 所需的 `task-budgets-2026-03-13` beta。当前支持仅限原生 Anthropic `claude-opus-4-7` 和 `claude-opus-4-8` 请求，不支持 Bedrock、Vertex 或 Microsoft Foundry Anthropic model IDs。

```python {title="anthropic_task_budget.py"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings

model = AnthropicModel('claude-opus-4-8')
settings = AnthropicModelSettings(
    anthropic_task_budget={'type': 'tokens', 'total': 20_000},
)
agent = Agent(model, model_settings=settings)
...
```

Task budgets 可以与 [`anthropic_effort`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_effort] 组合：effort 调整每一步的推理深度，而 task budgets 限制整个 loop 的总工作量。两个字段最终都会位于同一个 `output_config` 对象下。

!!! note
    Task budgets 是建议性的，而不是硬性上限；请配合 [`max_tokens`][pydantic_ai.settings.ModelSettings.max_tokens] 使用，以获得强制 ceiling。

### 跨 compaction 携带预算 {#carrying-budgets-across-compaction}

如果你使用 [`AnthropicCompaction`][pydantic_ai.models.anthropic.AnthropicCompaction] 进行 server-side compaction，可以跳过本节：服务器会自行跟踪倒计时，因此让 `remaining` 保持未设置，并让 `total` 自我调节即可。

`task_budget` 上的 `remaining` 字段适用于 *client-side* compaction 模式，即你在请求之间自行总结早期轮次，因此服务器不知道 rewrite 之前已经花费了多少预算。Pydantic AI 不会替你跟踪 `remaining`；请自行跨请求累计 token usage（例如从每次 run 的 [`RunUsage`][pydantic_ai.usage.RunUsage] 获取），并在下一次请求中传入更新后的值，让倒计时从上次停止的位置继续，而不是重置为 `total`。设置 `remaining` 还会使包含预算的任何 prompt-cache prefix 失效，因此如果你想保留 caching，请只设置一次 `total`，并让服务器按运行中的倒计时自我调节。

!!! warning
    `task_budget.remaining` 与 [`AnthropicCompaction`][pydantic_ai.models.anthropic.AnthropicCompaction] 互斥：Anthropic 会拒绝将两者组合的请求，因为 server-side compaction 会自行跟踪预算。当配置了这种组合时，Pydantic AI 会在发送请求前引发 [`UserError`][pydantic_ai.exceptions.UserError]。请选择其一：使用 `remaining` 进行 client-side budget tracking，或使用 [`AnthropicCompaction`][pydantic_ai.models.anthropic.AnthropicCompaction] 进行 server-side compaction。

## Prompt Caching 提示缓存 {#prompt-caching}

Anthropic 支持 [prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)，可通过缓存部分 prompts 来降低成本。Pydantic AI 支持 automatic caching、per-block message caching 和 explicit cache breakpoints：

### Automatic Caching 自动缓存 {#automatic-caching}

启用 prompt caching 的最简单方式是使用 [`AnthropicModelSettings.anthropic_cache`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_cache]。这会使用 Anthropic 的 [automatic caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching#automatic-caching)，传入顶层 `cache_control` 参数，让服务器自动对每个请求中最后一个可缓存 block 应用 cache breakpoint：

```python {test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    instructions='You are a helpful assistant.',
    model_settings=AnthropicModelSettings(
        anthropic_cache=True,
    ),
)

result1 = agent.run_sync('What is the capital of France?')

result2 = agent.run_sync(
    'What is the capital of Germany?', message_history=result1.all_messages()
)
print(f'Cache write: {result1.usage.cache_write_tokens}')
print(f'Cache read: {result2.usage.cache_read_tokens}')
```

这非常适合多轮对话，因为 cache breakpoint 应随着对话增长向前移动。你也可以用 `anthropic_cache='1h'` 指定自定义 TTL。

!!! note "Bedrock 和 Vertex"
    Bedrock 和 Vertex [尚不支持 automatic caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching#automatic-caching)。在这些平台上，`anthropic_cache` 会回退为在最后一条 user message 上进行 per-block caching，从而为多轮对话提供相同收益。

### Per-block Message Caching 分块消息缓存 {#per-block-message-caching}

作为 `anthropic_cache` 的替代方案，[`AnthropicModelSettings.anthropic_cache_messages`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_cache_messages] 会把 per-block `cache_control` 添加到最后一条 message 的最后一个 content block，而不是使用 Anthropic 的顶层 automatic caching 参数。对于接受 Anthropic message format 但不支持顶层 automatic caching 的 Anthropic-compatible gateways 和 proxies（例如 MiniMax、OpenRouter 或 LiteLLM），请使用此方式：

```python {test="skip"}
from anthropic import AsyncAnthropic

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.providers.anthropic import AnthropicProvider

client = AsyncAnthropic(
    api_key='your-api-key',
    base_url='https://your-anthropic-compatible-gateway.example.com',
)

model = AnthropicModel(
    'claude-sonnet-4-6',
    provider=AnthropicProvider(anthropic_client=client),
)
agent = Agent(
    model,
    model_settings=AnthropicModelSettings(
        anthropic_cache_messages=True,
    ),
)

result = agent.run_sync('What is the capital of France?')
print(result.output)
```

你也可以用 `anthropic_cache_messages='1h'` 指定自定义 TTL。`anthropic_cache_messages` 不能与 `anthropic_cache` 组合使用。

### 显式 Cache Breakpoints {#explicit-cache-breakpoints}

除 automatic caching 外，Pydantic AI 还提供了几种在特定内容上放置 cache breakpoints 的方式：

1. **使用 [`CachePoint`][pydantic_ai.messages.CachePoint] 缓存 User Messages**：在 user messages 中插入 `CachePoint` 标记，以缓存其之前的所有内容
2. **缓存最终 Message Block**：将 [`AnthropicModelSettings.anthropic_cache_messages`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_cache_messages] 设置为 `True`（默认使用 5m TTL），或直接指定 `'5m'` / `'1h'`
3. **缓存 System Instructions**：将 [`AnthropicModelSettings.anthropic_cache_instructions`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_cache_instructions] 设置为 `True`（默认使用 5m TTL），或直接指定 `'5m'` / `'1h'`
4. **缓存 Tool Definitions**：将 [`AnthropicModelSettings.anthropic_cache_tool_definitions`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_cache_tool_definitions] 设置为 `True`（默认使用 5m TTL），或直接指定 `'5m'` / `'1h'`

#### 示例：综合 Caching 策略 {#example-comprehensive-caching-strategy}

将 automatic caching 与 explicit breakpoints 组合以最大化节省。Automatic caching 处理对话，而 explicit breakpoints 固定 system instructions 和 tool definitions：

```python {test="skip"}
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    instructions='Detailed instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache=True,                   # Server auto-caches last block
        anthropic_cache_instructions=True,      # Explicitly cache system instructions
        anthropic_cache_tool_definitions='1h',  # Explicitly cache tool definitions with 1h TTL
    ),
)

@agent.tool
def search_docs(ctx: RunContext, query: str) -> str:
    """Search documentation."""
    return f'Results for {query}'


result = agent.run_sync('Search for Python best practices')
print(result.output)
```

### 智能 Instruction Caching {#smart-instruction-caching}

当你对静态和动态 [instructions](../agent.md#instructions) 同时使用 `anthropic_cache_instructions` 时，Pydantic AI 会自动把 cache boundary 放到最佳位置。静态 instructions（来自 `Agent(instructions=...)`）会排在动态 instructions（来自 `@agent.instructions` 函数或 [toolsets](../toolsets.md)）之前，cache point 会放在最后一个静态 instruction block 之后。

这意味着稳定的静态 instructions 会被高效缓存，而动态 instructions（可能在请求之间变化）会保留在 cache boundary 之外，不会导致 cache invalidation。

```python {test="skip"}
from datetime import date

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    deps_type=str,
    instructions='You are a helpful customer service agent. Follow company policy.',  # (1)!
    model_settings=AnthropicModelSettings(
        anthropic_cache_instructions=True,  # (2)!
    ),
)


@agent.instructions
def dynamic_context(ctx: RunContext[str]) -> str:  # (3)!
    return f"Customer name: {ctx.deps}. Today's date: {date.today()}."


result = agent.run_sync('What is your return policy?', deps='Alice')
print(result.output)
```

1. 静态 instructions 会跨请求缓存。
2. 在 static/dynamic boundary 启用智能 cache placement。
3. 动态 instructions 每次请求都会变化，不会被缓存。

### 使用 CachePoint 进行细粒度控制 {#fine-grained-control-with-cachepoint}

使用手动 `CachePoint` markers 精确控制 cache locations：

```python {test="skip"}
from pydantic_ai import Agent, CachePoint

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    instructions='Instructions...',
)

# Manually control cache points for specific content blocks
result = agent.run_sync([
    'Long context from documentation...',
    CachePoint(),  # Cache everything up to this point
    'First question'
])
print(result.output)
```

### 访问 Cache Usage 统计 {#accessing-cache-usage-statistics}

通过 `result.usage` 访问 cache usage statistics：

```python {test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    instructions='Instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache=True,
    ),
)

result = agent.run_sync('Your question')
usage = result.usage
print(f'Cache write tokens: {usage.cache_write_tokens}')
print(f'Cache read tokens: {usage.cache_read_tokens}')
```

### Cache Point 限制 {#cache-point-limits}

Anthropic 对每个请求最多强制 4 个 cache points。Pydantic AI 会自动管理此限制，确保你的请求始终合规且不会出错。

#### Cache Points 如何分配 {#how-cache-points-are-allocated}

Cache points 可能来自多个来源：

1. **Automatic caching**：通过 `anthropic_cache`（服务器向最后一个可缓存 block 应用 1 个 cache point）
2. **Final message block**：通过 `anthropic_cache_messages` 设置（向最后一条 message content block 添加 cache point）
3. **System Prompt**：通过 `anthropic_cache_instructions` 设置（向最后一个 system prompt block 添加 cache point）
4. **Tool Definitions**：通过 `anthropic_cache_tool_definitions` 设置（向最后一个 tool definition 添加 cache point）
5. **Messages**：通过 `CachePoint` markers（向 message content 添加 cache points）

每个设置**最多使用 1 个 cache point**，但你可以组合它们；例外是 `anthropic_cache` 和 `anthropic_cache_messages` 互斥。如果总数超过 4，Pydantic AI 会自动从较旧的 messages 中裁剪多余 cache points。

#### 示例：组合 Automatic 和 Explicit Caching {#example-combining-automatic-and-explicit-caching}

定义一个带 automatic caching 和 explicit breakpoints 的智能体：

```python {test="skip"}
from pydantic_ai import Agent, CachePoint
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    instructions='Detailed instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache=True,                   # 1 cache point (server-applied)
        anthropic_cache_instructions=True,      # 1 cache point
        anthropic_cache_tool_definitions=True,  # 1 cache point
    ),
)

@agent.tool_plain
def my_tool() -> str:
    return 'result'


# 3 of 4 slots used (1 automatic + 1 instructions + 1 tools)
# Room for 1 more explicit CachePoint marker
result = agent.run_sync([
    'Context', CachePoint(),  # 4th cache point - OK
    'Question'
])
print(result.output)
usage = result.usage
print(f'Cache write tokens: {usage.cache_write_tokens}')
print(f'Cache read tokens: {usage.cache_read_tokens}')
```

#### 自动 Cache Point 限制 {#automatic-cache-point-limiting}

当来自所有来源（settings + `CachePoint` markers）的 explicit cache points 超过可用预算时，Pydantic AI 会自动从**较旧的 message content** 中移除多余 cache points（保留最近的）。

定义一个由 settings 提供 2 个 explicit cache points 的智能体：

```python {test="skip"}
from pydantic_ai import Agent, CachePoint
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    instructions='Instructions...',
    model_settings=AnthropicModelSettings(
        anthropic_cache_instructions=True,      # 1 cache point
        anthropic_cache_tool_definitions=True,  # 1 cache point
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
usage = result.usage
print(f'Cache write tokens: {usage.cache_write_tokens}')
print(f'Cache read tokens: {usage.cache_read_tokens}')
```

**关键点**：
- System 和 tool cache points **始终保留**
- `anthropic_cache` 与 `anthropic_cache_instructions` 和 `anthropic_cache_tool_definitions` 一样计为 1 个 cache point
- 当超出限制时，message 中多余的 `CachePoint` markers 会按从旧到新的顺序移除
- 这确保 critical caching（instructions/tools）得以保留，同时仍能受益于 message-level caching

## Fast mode 快速模式 {#fast-mode}

Fast mode 提供更高的每秒输出 tokens，当前支持 **Claude Opus 4.6**、**Claude Opus 4.7** 和 **Claude Opus 4.8**。它是一个 research preview。将 [`anthropic_speed`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_speed] 设置为 `'fast'` 即可启用；Pydantic AI 会自动添加所需的 `fast-mode-2026-02-01` beta。在不支持的模型上，`anthropic_speed='fast'` 会被忽略并发出 `UserWarning`。关于价格、速率限制和最新支持模型列表，请参阅 [Anthropic fast mode docs](https://platform.claude.com/docs/en/build-with-claude/fast-mode)。

```python
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-opus-4-8',
    model_settings=AnthropicModelSettings(anthropic_speed='fast'),
)
...
```

!!! note "Prompt cache 交互"
    在 `'fast'` 和 `'standard'` 之间切换会使 prompt cache 失效。不同 speed 的请求不会共享 cached prefixes，因此请为 cache-sensitive conversation 选择一种 speed。

!!! note "Bedrock、Vertex 和 Foundry"
    Fast mode 仅适用于直接的 Anthropic API。Bedrock、Vertex 和 Foundry clients 不支持 `speed` 参数，因此在这些 clients 上 `anthropic_speed='fast'` 会被忽略并发出 `UserWarning`。

## Message Compaction 消息压缩 {#message-compaction}

Anthropic 支持 [automatic context compaction](https://docs.anthropic.com/en/docs/build-with-claude/compaction)，用于管理长对话。当 input tokens 超过配置阈值时，API 会自动生成摘要，用其替换较旧 messages，同时保留上下文。

启用 compaction 最简单的方法是使用 [`AnthropicCompaction`][pydantic_ai.models.anthropic.AnthropicCompaction] capability：

```python {title="anthropic_compaction.py"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicCompaction

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    capabilities=[AnthropicCompaction(token_threshold=100_000)],
)
```

该 capability 接受：

- **`token_threshold`**（默认：150,000，最小：50,000）：当 input tokens 超过此值时触发 compaction。
- **`instructions`**：关于如何生成摘要的自定义 instructions。
- **`pause_after_compaction`**：当为 `True` 时，响应会在 compaction block 后停止，并带有 `stop_reason='compaction'`，允许你在继续前显式处理。

或者，你可以使用 [`anthropic_context_management`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_context_management] 通过 model settings 直接配置 compaction：

```python {title="anthropic_compaction_settings.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent('anthropic:claude-sonnet-4-6')
result = agent.run_sync(
    'Hello!',
    model_settings=AnthropicModelSettings(
        anthropic_context_management={
            'edits': [{'type': 'compact_20260112', 'trigger': {'type': 'input_tokens', 'value': 100_000}}]
        }
    ),
)
```

!!! note
    Anthropic 返回的 compaction blocks 包含可读文本摘要。只要包含在 message history 中，它们会在后续请求中自动 round-trip。

## 代码执行工具版本 {#code-execution-tool-version}

默认情况下，Pydantic AI 会为所选模型选择兼容的 Anthropic code execution tool version。当你需要某个特定支持版本时，可以使用 [`AnthropicModelSettings.anthropic_code_execution_tool_version`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_code_execution_tool_version] 覆盖它：

```py {title="anthropic_code_execution_tool_version.py"}
from pydantic_ai import Agent, CodeExecutionTool
from pydantic_ai.capabilities import NativeTool
from pydantic_ai.models.anthropic import AnthropicModelSettings

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    capabilities=[NativeTool(CodeExecutionTool())],
    model_settings=AnthropicModelSettings(anthropic_code_execution_tool_version='20260120'),
)
```

如果你显式选择了模型不支持的工具版本，Pydantic AI 会引发 [`UserError`][pydantic_ai.exceptions.UserError]。
