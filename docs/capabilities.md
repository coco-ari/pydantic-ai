# Capabilities（能力） {#capabilities}

Capability 是 agent behavior 中可复用、可组合的单元。与其把多个 arguments 分散传入 `Agent` constructor，例如这里传 [instructions](agent.md#instructions)、那里传 [model settings](agent.md#model-run-settings)、另一个地方传 [toolset](toolsets.md)、再用其他 parameter 传 [history processor](message-history.md#processing-message-history)，你可以把相关行为打包进单个 capability，并通过 [`capabilities`][pydantic_ai.agent.Agent.__init__] parameter 传入。

Capabilities 可以提供以下能力的任意组合：

* **Tools**：通过 [toolsets](toolsets.md) 或 [native tools](native-tools.md)
* **Lifecycle hooks**：拦截并修改 model requests、tool calls 和整体 run
* **Instructions**：添加 static 或 dynamic [instruction](agent.md#instructions)
* **Model settings**：static 或 per-step [model settings](agent.md#model-run-settings)

这使 capabilities 成为 Pydantic AI 的主要扩展点。无论你在构建 memory system、guardrail、cost tracker 还是 approval workflow，capability 都是合适的抽象。

## 原生 Capabilities {#native-capabilities}

Pydantic AI 随附了几个覆盖常见需求的 capabilities：

| Capability | 提供内容 | Spec |
|---|---|:---:|
| [`Thinking`][pydantic_ai.capabilities.Thinking] | 以可配置 effort 启用模型 [thinking/reasoning](thinking.md) | Yes |
| [`Hooks`][pydantic_ai.capabilities.Hooks] | 基于 decorator 的 [lifecycle hook](hooks.md) 注册 | — |
| [`Instrumentation`][pydantic_ai.capabilities.Instrumentation] | OpenTelemetry/Logfire tracing，参见 [Debugging and Monitoring](logfire.md) | Yes |
| [`WebSearch`][pydantic_ai.capabilities.WebSearch] | Web search；支持时使用 native，不支持时通过 [`duckduckgo` extra](install.md#slim-install) 使用 [local fallback](common-tools.md#duckduckgo-search-tool) | Yes |
| [`WebFetch`][pydantic_ai.capabilities.WebFetch] | URL fetching；支持时使用 native，不支持时通过 [`web-fetch` extra](install.md#slim-install) 使用 [local fallback](common-tools.md#web-fetch-tool) | Yes |
| [`ImageGeneration`][pydantic_ai.capabilities.ImageGeneration] | Image generation；支持时使用 native，否则通过 `fallback_model` 使用 subagent fallback | Yes |
| [`XSearch`][pydantic_ai.capabilities.XSearch] | X search；在 xAI 上使用 native，否则通过 `fallback_model` 显式使用 subagent fallback | Yes |
| [`MCP`][pydantic_ai.capabilities.MCP] | MCP server；支持时使用 native，否则直接连接 | Yes |
| [`ToolSearch`][pydantic_ai.capabilities.ToolSearch] | 发现 [deferred tools](tools-advanced.md#tool-search)；支持时使用 native，否则使用本地 `search_tools` function tool | Yes |
| [`PrepareTools`][pydantic_ai.capabilities.PrepareTools] | 按 step 过滤或修改 function [tool definitions](tools.md) | — |
| [`PrepareOutputTools`][pydantic_ai.capabilities.PrepareOutputTools] | 按 step 过滤或修改 [output tool][pydantic_ai.output.ToolOutput] definitions | — |
| [`PrefixTools`][pydantic_ai.capabilities.PrefixTools] | 包装 capability，并为其 tool names 添加前缀 | Yes |
| [`NativeTool`][pydantic_ai.capabilities.NativeTool] | 给 agent 注册 [native tool](native-tools.md) | Yes |
| [`Toolset`][pydantic_ai.capabilities.Toolset] | 包装 [`AbstractToolset`][pydantic_ai.toolsets.AbstractToolset] | — |
| [`IncludeToolReturnSchemas`][pydantic_ai.capabilities.IncludeToolReturnSchemas] | 在发送给模型的 tool definitions 中包含 return type schemas | Yes |
| [`SetToolMetadata`][pydantic_ai.capabilities.SetToolMetadata] | 把 metadata key-value pairs 合并到选定 tools 上 | Yes |
| [`HandleDeferredToolCalls`][pydantic_ai.capabilities.HandleDeferredToolCalls] | 使用 handler function inline 解析 [deferred tool calls](deferred-tools.md#resolving-deferred-calls-with-a-handler) | — |
| [`ProcessHistory`][pydantic_ai.capabilities.ProcessHistory] | 包装 [history processor](message-history.md#processing-message-history) | — |
| [`ProcessEventStream`][pydantic_ai.capabilities.ProcessEventStream] | 把 agent stream events 转发给 handler function | — |
| [`ThreadExecutor`][pydantic_ai.capabilities.ThreadExecutor] | 为 [sync functions](tools-advanced.md#thread-executor-for-long-running-servers) 使用自定义 thread executor | — |

**Spec** 列表示 capability 是否可用于 [agent specs](agent-spec.md)（YAML/JSON）。标记为 **—** 的 capabilities 接受不可序列化 arguments（callables、toolset objects），只能在 Python code 中使用。

```python {title="native_capabilities.py"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking, WebSearch

agent = Agent(
    'anthropic:claude-opus-4-6',
    instructions='You are a research assistant. Be thorough and cite sources.',
    capabilities=[
        Thinking(effort='high'),
        WebSearch(local='duckduckgo'),
    ],
)
```

[Instructions](agent.md#instructions) 和 [model settings](agent.md#model-run-settings) 会直接通过 `Agent`（或 [`AgentSpec`][pydantic_ai.agent.spec.AgentSpec]）上的 `instructions` 和 `model_settings` parameters 配置。Capabilities 用于超出简单配置的 behavior：tools、lifecycle hooks 和 custom extensions。它们组合性很好，尤其适合在多个 agents 之间复用同一配置，或从 [spec file](agent-spec.md) 加载配置。

### Thinking（思考） {#thinking}

[`Thinking`][pydantic_ai.capabilities.Thinking] capability 会以可配置 effort level 启用模型 [thinking/reasoning](thinking.md)。这是跨 providers 启用 thinking 的最简单方式：

```python {title="thinking_capability.py"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking

agent = Agent('anthropic:claude-sonnet-4-6', capabilities=[Thinking(effort='high')])
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

Provider-specific 细节和 [unified thinking settings](thinking.md#unified-thinking-settings) 请参阅 [Thinking](thinking.md)。

### Compaction（压缩） {#compaction}

Provider-specific compaction capabilities 会把较早 messages 压缩成 summaries，以管理 conversation context size：

| Provider | Capability | 详情 |
|----------|-----------|---------|
| OpenAI Responses API | [`OpenAICompaction`][pydantic_ai.models.openai.OpenAICompaction] | [OpenAI compaction（OpenAI 压缩）](models/openai.md#message-compaction) |
| Anthropic | [`AnthropicCompaction`][pydantic_ai.models.anthropic.AnthropicCompaction] | [Anthropic compaction（Anthropic 压缩）](models/anthropic.md#message-compaction) |

### ThreadExecutor（线程执行器） {#threadexecutor}

[`ThreadExecutor`][pydantic_ai.capabilities.ThreadExecutor] capability 提供自定义 [`Executor`][concurrent.futures.Executor]，用于在线程中运行 sync tool functions 和其他 sync callbacks。在 long-running servers（例如 FastAPI）中，这很有用，因为来自 [`anyio.to_thread.run_sync`][anyio.to_thread.run_sync] 的默认临时 threads 可能在持续负载下不断累积：

```python {test="skip"}
from concurrent.futures import ThreadPoolExecutor

from pydantic_ai import Agent
from pydantic_ai.capabilities import ThreadExecutor

executor = ThreadPoolExecutor(max_workers=16, thread_name_prefix='agent-worker')
agent = Agent('openai:gpt-5.2', capabilities=[ThreadExecutor(executor)])
```

更多细节请参阅 [Thread executor for long-running servers](tools-advanced.md#thread-executor-for-long-running-servers)。

### Hooks（钩子） {#hooks}

[`Hooks`][pydantic_ai.capabilities.Hooks] capability 提供基于 decorator 的 [lifecycle hook](#hooking-into-the-lifecycle) 注册；这是不 subclass [`AbstractCapability`][pydantic_ai.capabilities.AbstractCapability] 就能拦截 model requests、tool calls 和其他 events 的最简单方式：

```python {test="skip" lint="skip"}
from pydantic_ai import Agent, ModelRequestContext, RunContext
from pydantic_ai.capabilities import Hooks

hooks = Hooks()

@hooks.on.before_model_request
async def log_request(ctx: RunContext[None], request_context: ModelRequestContext) -> ModelRequestContext:
    agent_name = ctx.agent.name if ctx.agent else 'unknown'
    print(f'[{agent_name}] Sending {len(request_context.messages)} messages')
    return request_context

agent = Agent('openai:gpt-5.2', name='my_agent', capabilities=[hooks])
```

所有 hooks 都会接收 [`RunContext`][pydantic_ai.tools.RunContext]，它通过 [`ctx.agent`][pydantic_ai.tools.RunContext.agent] 提供对正在运行的 agent 的访问；这对 logging、metrics 以及需要识别当前运行 agent 的其他 cross-cutting concerns 很有用。

Hooks 也可以通过 [`RunContext.enqueue`][pydantic_ai.tools.RunContext.enqueue]
把 follow-up messages 推入 conversation。这适合 capability authors 在 mid-run
向模型暴露事件，同时不重建 cached system prompt。参见
[Injecting messages mid-run（在运行中注入消息）](message-history.md#injecting-messages-mid-run)。

完整 API 请参阅专门的 [Hooks](hooks.md) 页面：decorator 和 constructor registration、timeouts、tool filtering、wrap hooks、per-event hooks 等。

### Provider-adaptive tools（提供商自适应工具） {#provider-adaptive-tools}

[`WebSearch`][pydantic_ai.capabilities.WebSearch]、[`WebFetch`][pydantic_ai.capabilities.WebFetch]、[`ImageGeneration`][pydantic_ai.capabilities.ImageGeneration]、[`XSearch`][pydantic_ai.capabilities.XSearch] 和 [`MCP`][pydantic_ai.capabilities.MCP] 为常见 tool types 提供 model-agnostic 访问。当模型原生支持该 tool（作为 [native tool](native-tools.md)）时，会直接使用原生能力；不支持时，则由本地 function tool 处理。因此你的 agent 可以跨 providers 工作，无需改代码。

每个 capability 都接受 `native` 和 `local` keyword arguments 来控制使用哪一侧。[`ImageGeneration`][pydantic_ai.capabilities.ImageGeneration] 和 [`XSearch`][pydantic_ai.capabilities.XSearch] 还接受 `fallback_model`，用于启用默认 subagent fallbacks：

```python {title="provider_adaptive_tools.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import MCP, ImageGeneration, WebFetch, WebSearch, XSearch

agent = Agent(
    'anthropic:claude-sonnet-4-6',
    capabilities=[
        # Native when supported; falls back to DuckDuckGo locally
        WebSearch(local='duckduckgo'),
        # Native when supported; falls back to the markdownify-based local tool
        WebFetch(local=True),
        # Native when supported; falls back to a subagent running an
        # image-generation-capable model
        ImageGeneration(fallback_model='openai-responses:gpt-5.4'),
        # Native on xAI; on other models, explicitly delegate to an xAI model
        XSearch(fallback_model='xai:grok-4-1-fast-non-reasoning'),
        # Native when supported; falls back to a local MCP transport derived from the URL
        MCP(url='https://mcp.example.com/api', native=True),
    ],
)
```

[`XSearch`][pydantic_ai.capabilities.XSearch] 与 [`WebSearch`][pydantic_ai.capabilities.WebSearch] 和 [`WebFetch`][pydantic_ai.capabilities.WebFetch] 略有不同：它没有默认的 non-xAI fallback。如果你的 agent 没有运行在 xAI model 上，请把 `fallback_model` 显式设置为支持 [`XSearchTool`][pydantic_ai.native_tools.XSearchTool] 的 xAI model。

要强制 native-only（在不支持的模型上报错，而不是 fallback 到 local）：

```python {title="native_only.py" test="skip" lint="skip"}
MCP(url='https://mcp.example.com/api', native=True, local=False)
```

要强制 local-only（即使模型支持，也永不使用 native tool）：

```python {title="local_only.py" test="skip" lint="skip"}
MCP(url='https://mcp.example.com/api', native=False)
```

有些 constraint fields 需要 native tool，因为 local fallback 无法强制执行它们。当设置了这些字段但模型不支持 native tool 时，会 raise [`UserError`][pydantic_ai.exceptions.UserError]。例如，[`WebSearch`][pydantic_ai.capabilities.WebSearch] 的 domain constraints 需要 native tool，而 [`WebFetch`][pydantic_ai.capabilities.WebFetch] 会在本地强制执行它们：

```python {title="constraints.py" test="skip" lint="skip"}
# Only search example.com — requires native support
WebSearch(allowed_domains=['example.com'])

# Only fetch example.com — enforced locally when native is unavailable
WebFetch(allowed_domains=['example.com'])
```

所有这些 capabilities 都是 [`NativeOrLocalTool`][pydantic_ai.capabilities.NativeOrLocalTool] 的 subclasses；你可以直接使用它，也可以 subclass 它来构建自己的 provider-adaptive tools。例如，把 [`CodeExecutionTool`][pydantic_ai.native_tools.CodeExecutionTool] 与 local fallback 配对：

```python {title="custom_native_or_local.py" test="skip" lint="skip"}
from pydantic_ai.native_tools import CodeExecutionTool
from pydantic_ai.capabilities import NativeOrLocalTool

cap = NativeOrLocalTool(native=CodeExecutionTool(), local=my_local_executor)
```

### ToolSearch（工具搜索） {#toolsearch}

[`ToolSearch`][pydantic_ai.capabilities.ToolSearch] capability 负责发现标记为 `defer_loading=True` 的 tools，因此拥有大型 toolsets 的 agents 只会为模型所需 tools 支付 tokens。与上面的 [provider-adaptive tools](#provider-adaptive-tools) 一样，它会为当前模型选择最佳路径：在 Anthropic 和 OpenAI Responses 上使用 native server-executed search，其他位置使用本地 `search_tools` function tool；当不存在 deferred tools 时，它会以零开销自动注入每个 agent。

传入显式 [`ToolSearch`][pydantic_ai.capabilities.ToolSearch] 可以选择特定 [`strategy`][pydantic_ai.capabilities.ToolSearch.strategy]（`'keywords'`、`'bm25'`、`'regex'` 或 custom callable），或调优 local fallback：

```python {title="tool_search_capability.py"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import ToolSearch

agent = Agent('anthropic:claude-sonnet-4-6', capabilities=[ToolSearch(strategy='keywords')])
```

何时使用它、完整 strategy table 和 provider support 细节，请参阅 [Tool Search](tools-advanced.md#tool-search)。

### PrepareTools 和 PrepareOutputTools {#preparetools-and-prepareoutputtools}

[`PrepareTools`][pydantic_ai.capabilities.PrepareTools] 和 [`PrepareOutputTools`][pydantic_ai.capabilities.PrepareOutputTools] 会把 [`ToolsPrepareFunc`][pydantic_ai.tools.ToolsPrepareFunc] 包装为 capability，用于按 step 过滤或修改 [tool definitions](tools.md)。`PrepareTools` 处理 function tools；`PrepareOutputTools` 处理 [output tools][pydantic_ai.output.ToolOutput]。Agent constructor 的 [`prepare_tools`][pydantic_ai.tools.ToolsPrepareFunc] / [`prepare_output_tools`][pydantic_ai.tools.ToolsPrepareFunc] arguments 是语法糖，会自动注入这些 capabilities。这两个 capabilities 遵循与 [`prepare_tools`](tools-advanced.md#prepare-tools) 相同的返回值规则和 `None` warning behavior。

```python {title="prepare_tools_native.py"}
from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.capabilities import PrepareTools


async def hide_dangerous(ctx: RunContext[None], tool_defs: list[ToolDefinition]) -> list[ToolDefinition]:
    return [td for td in tool_defs if not td.name.startswith('delete_')]


agent = Agent('openai:gpt-5.2', capabilities=[PrepareTools(hide_dangerous)])


@agent.tool_plain
def delete_file(path: str) -> str:
    """Delete a file."""
    return f'deleted {path}'


@agent.tool_plain
def read_file(path: str) -> str:
    """Read a file."""
    return f'contents of {path}'


result = agent.run_sync('hello')
# The model only sees `read_file`, not `delete_file`
```

更复杂的 tool preparation logic 请参阅 lifecycle hooks 下的 [Tool preparation](#tool-preparation)。

### PrefixTools（工具前缀） {#prefixtools}

[`PrefixTools`][pydantic_ai.capabilities.PrefixTools] 会包装另一个 capability，并给它的所有 tool names 添加前缀。当组合多个可能存在 tool name 冲突的 capabilities 时，这对 namespacing 很有用：

```python {title="prefix_tools_example.py" test="skip" lint="skip"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import MCP, PrefixTools

agent = Agent(
    'openai:gpt-5.2',
    capabilities=[
        PrefixTools(MCP(url='https://api1.example.com', native=True), prefix='api1'),
        PrefixTools(MCP(url='https://api2.example.com', native=True), prefix='api2'),
    ],
)
```

每个 [`AbstractCapability`][pydantic_ai.capabilities.AbstractCapability] 都有一个便利 method [`prefix_tools`][pydantic_ai.capabilities.AbstractCapability.prefix_tools]，它会返回 [`PrefixTools`][pydantic_ai.capabilities.PrefixTools] wrapper：

```python {title="prefix_convenience.py" test="skip" lint="skip"}
MCP(url='https://mcp.example.com/api', native=True).prefix_tools('mcp')
```

### IncludeToolReturnSchemas（包含工具返回 schema） {#includetoolreturnschemas}

[`IncludeToolReturnSchemas`][pydantic_ai.capabilities.IncludeToolReturnSchemas] 会在发送给模型的 tool definitions 中包含 return type schemas。对于原生支持 return schemas 的模型（例如 Google Gemini），schema 会作为 API request 中的 structured field 传入。对于其他模型，它会以 JSON text 形式注入 tool description。

```python {title="include_return_schemas.py" lint="skip"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import IncludeToolReturnSchemas
from pydantic_ai.models.test import TestModel


test_model = TestModel()
agent = Agent(test_model, capabilities=[IncludeToolReturnSchemas()])


@agent.tool_plain
def get_temperature(city: str) -> float:
    """Get the temperature for a city."""
    return 21.0


result = agent.run_sync('What is the temperature in Paris?')
params = test_model.last_model_request_parameters
assert params is not None
td = params.function_tools[0]
assert td.include_return_schema is True
```

_（这个示例是完整的，可以"原样"运行）_

使用 `tools` parameter 可以选择哪些 tools 应包含 return schemas。它接受 tool names list、用于匹配的 metadata dict，或 callable predicate：

```python {title="include_return_schemas_selective.py" lint="skip"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import IncludeToolReturnSchemas
from pydantic_ai.models.test import TestModel


test_model = TestModel()
agent = Agent(
    test_model,
    capabilities=[IncludeToolReturnSchemas(tools=['get_temperature'])],
)


@agent.tool_plain
def get_temperature(city: str) -> float:
    """Get the temperature for a city."""
    return 21.0


@agent.tool_plain
def get_greeting(name: str) -> str:
    """Get a greeting."""
    return f'Hello, {name}!'


result = agent.run_sync('Hello')
params = test_model.last_model_request_parameters
assert params is not None
temp_tool = next(t for t in params.function_tools if t.name == 'get_temperature')
greet_tool = next(t for t in params.function_tools if t.name == 'get_greeting')
assert temp_tool.include_return_schema is True
assert greet_tool.include_return_schema is None
```

_（这个示例是完整的，可以"原样"运行）_

也可以在 toolset 层级使用 [`.include_return_schemas()`][pydantic_ai.toolsets.AbstractToolset.include_return_schemas] 达到同样效果；参见 [toolset composition](toolsets.md#including-return-schemas)。

### SetToolMetadata（设置工具 metadata） {#settoolmetadata}

[`SetToolMetadata`][pydantic_ai.capabilities.SetToolMetadata] 会把 metadata key-value pairs 合并到选定 tools 上。这适合给 tools 添加可由其他 capabilities 或 custom logic 检查的配置标签：

```python {title="set_tool_metadata.py" lint="skip"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import SetToolMetadata
from pydantic_ai.models.test import TestModel


test_model = TestModel()
agent = Agent(
    test_model,
    capabilities=[SetToolMetadata(tools=['search'], sensitive=True)],
)


@agent.tool_plain
def search(query: str) -> str:
    """Search for information."""
    return f'Results for: {query}'


@agent.tool_plain
def greet(name: str) -> str:
    """Greet someone."""
    return f'Hello, {name}!'


result = agent.run_sync('Search for pydantic')
params = test_model.last_model_request_parameters
assert params is not None
search_tool = next(t for t in params.function_tools if t.name == 'search')
greet_tool = next(t for t in params.function_tools if t.name == 'greet')
assert search_tool.metadata is not None and search_tool.metadata.get('sensitive') is True
assert greet_tool.metadata is None or greet_tool.metadata.get('sensitive') is None
```

_（这个示例是完整的，可以"原样"运行）_

也可以在 toolset 层级使用 [`.with_metadata()`][pydantic_ai.toolsets.AbstractToolset.with_metadata] 达到同样效果；参见 [toolset composition](toolsets.md#setting-tool-metadata)。

### ReinjectSystemPrompt（重新注入 system prompt） {#reinjectsystemprompt}

[`ReinjectSystemPrompt`][pydantic_ai.capabilities.ReinjectSystemPrompt] 会确保 agent 配置的 [`system_prompt`](agent.md#system-prompts) 位于每次 model request 中第一个 [`ModelRequest`][pydantic_ai.messages.ModelRequest] 的开头。默认情况下，如果 history 中已存在任何 [`SystemPromptPart`][pydantic_ai.messages.SystemPromptPart]，该 capability 会 no-op（因此 multi-agent handoff 和 user-managed system prompts 仍保持权威）。设置 `replace_existing=True` 后，会先移除任何现有 `SystemPromptPart`s，再把 agent 配置的 prompt 前置；当 history 来自不受信任来源且 server prompt 必须优先生效时，这很有用。

当 `message_history` 来自不会 round-trip system prompts 的来源时，这很有用，例如 UI frontends、database persistence layers、conversation compaction pipelines。没有这个 capability 时，如果 history 中尚未包含 system prompt，配置了 `system_prompt` 的 agent 会静默地在没有该 prompt 的情况下运行。

```python {title="reinject_system_prompt.py"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import ReinjectSystemPrompt
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

agent = Agent('test', system_prompt='You are a helpful assistant.', capabilities=[ReinjectSystemPrompt()])

# History that's missing the system prompt (e.g. reconstructed from a UI frontend).
history = [
    ModelRequest(parts=[UserPromptPart(content='Hi')]),
    ModelResponse(parts=[TextPart(content='Hello!')]),
]

# Without the capability, the agent would run without its configured system prompt.
# With the capability, the system prompt is reinjected at the head of the first request.
result = agent.run_sync('Follow up', message_history=history)
first_request = result.all_messages()[0]
assert isinstance(first_request, ModelRequest)
assert first_request.parts[0].content == 'You are a helpful assistant.'
```

_（这个示例是完整的，可以"原样"运行）_

[UI adapters](ui/ag-ui.md)（AG-UI、Vercel AI）会在 `manage_system_prompt='server'` mode 中自动添加此 capability，并设置 `replace_existing=True`。

## 构建自定义 Capabilities {#building-custom-capabilities}

要构建自己的 capability，请 subclass [`AbstractCapability`][pydantic_ai.capabilities.AbstractCapability] 并 override 所需 methods。它们分为两类：在 agent construction 时调用的 **configuration methods**（[`get_wrapper_toolset`][pydantic_ai.capabilities.AbstractCapability.get_wrapper_toolset] 例外，它按 run 调用），以及在每次 run 期间触发的 **lifecycle hooks**。

### 提供 Tools {#providing-tools}

提供 tools 的 capability 会从 [`get_toolset`][pydantic_ai.capabilities.AbstractCapability.get_toolset] 返回 [toolset](toolsets.md)。这可以是预先构建的 [`AbstractToolset`][pydantic_ai.toolsets.AbstractToolset] instance，也可以是接收 [`RunContext`][pydantic_ai.tools.RunContext] 并动态返回 toolset 的 callable：

```python {title="custom_capability_tools.py"}
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import AgentToolset, FunctionToolset

math_toolset = FunctionToolset()


@math_toolset.tool_plain
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@math_toolset.tool_plain
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@dataclass
class MathTools(AbstractCapability[Any]):
    """Provides basic math operations."""

    def get_toolset(self) -> AgentToolset[Any] | None:
        return math_toolset


agent = Agent('openai:gpt-5.2', capabilities=[MathTools()])
result = agent.run_sync('What is 2 + 3?')
print(result.output)
#> The answer is 5.0
```

对于 [native tools](native-tools.md)，请 override [`get_native_tools`][pydantic_ai.capabilities.AbstractCapability.get_native_tools]，返回 [`AgentNativeTool`][pydantic_ai.tools.AgentNativeTool] instances sequence（其中包含 [`AbstractNativeTool`][pydantic_ai.native_tools.AbstractNativeTool] objects，以及接收 [`RunContext`][pydantic_ai.tools.RunContext] 的 callables）。

#### Toolset wrapping（工具集包装） {#toolset-wrapping}

[`get_wrapper_toolset`][pydantic_ai.capabilities.AbstractCapability.get_wrapper_toolset] 允许 capability 用 [`WrapperToolset`](toolsets.md#changing-tool-execution) 包装 agent 已组装好的完整 toolset。这比提供 tools 更强大：它可以拦截 tool execution、添加 logging，或应用 cross-cutting behavior。

wrapper 会接收合并后的 non-output toolset（在 [`prepare_tools`](#tool-preparation) hook 包装之后）。Output tools 会单独添加，不受影响。

```python {title="wrapper_toolset_example.py"}
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import AbstractToolset
from pydantic_ai.toolsets.wrapper import WrapperToolset


@dataclass
class LoggingToolset(WrapperToolset[Any]):
    """Logs all tool calls."""

    async def call_tool(
        self, tool_name: str, tool_args: dict[str, Any], *args: Any, **kwargs: Any
    ) -> Any:
        print(f'  Calling tool: {tool_name}')
        return await super().call_tool(tool_name, tool_args, *args, **kwargs)


@dataclass
class LogToolCalls(AbstractCapability[Any]):
    """Wraps the agent's toolset to log all tool calls."""

    def get_wrapper_toolset(self, toolset: AbstractToolset[Any]) -> AbstractToolset[Any]:
        return LoggingToolset(wrapped=toolset)


agent = Agent('openai:gpt-5.2', capabilities=[LogToolCalls()])


@agent.tool_plain
def greet(name: str) -> str:
    """Greet someone."""
    return f'Hello, {name}!'


result = agent.run_sync('hello')
# Tool calls are logged as they happen
```

!!! note "注意"
    `get_wrapper_toolset` 每次 run 会包装 non-output *toolset* 一次（在 toolset assembly 期间）。[`prepare_tools`](#tool-preparation) 和 [`prepare_output_tools`](#tool-preparation) hooks 也会流经 `PreparedToolset` wrappers，因此三者都在 toolset 层级集成：`get_wrapper_toolset` 包在 `prepare_tools` 外侧（它看到 prepared defs），而 `prepare_output_tools` 会独立包装 output toolset。

### 提供 Instructions {#providing-instructions}

[`get_instructions`][pydantic_ai.capabilities.AbstractCapability.get_instructions] 会给 agent 添加 [instructions](agent.md#instructions)。由于它在 agent construction 时调用一次，如果需要 dynamic values，请返回 callable：

```python {title="custom_capability_config.py"}
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import AbstractCapability


@dataclass
class KnowsCurrentTime(AbstractCapability[Any]):
    """Tells the agent what time it is."""

    def get_instructions(self):
        def _get_time(ctx: RunContext[Any]) -> str:
            return f'The current date and time is {datetime.now().isoformat()}.'

        return _get_time


agent = Agent('openai:gpt-5.2', capabilities=[KnowsCurrentTime()])
result = agent.run_sync('What time is it?')
print(result.output)
#> The current time is 3:45 PM.
```

Instructions 也可以使用 [template strings](agent-spec.md#template-strings)（`TemplateStr('Hello {{name}}')`），以便针对 agent 的 [dependencies](dependencies.md) 渲染 Handlebars-style templates。在 Python code 中，通常更推荐使用带 [`RunContext`][pydantic_ai.tools.RunContext] 的 callable，以获得 IDE autocomplete。

### 提供 Model settings {#providing-model-settings}

[`get_model_settings`][pydantic_ai.capabilities.AbstractCapability.get_model_settings] 会把 [model settings](agent.md#model-run-settings) 作为 dict 返回，或返回用于 per-step settings 的 callable。

当 model settings 需要按 step 变化时，例如只在 retry 时启用 thinking，或在某个 tool 被调用前强制指定 [`tool_choice`](tools-advanced.md#dynamic-tool-choice-via-capabilities)，请返回 callable：

```python {title="dynamic_settings.py"}
from dataclasses import dataclass

from pydantic_ai import Agent, ModelSettings, RunContext
from pydantic_ai.capabilities import AbstractCapability


@dataclass
class ThinkingOnRetry(AbstractCapability[None]):
    """Enables thinking mode when the agent is retrying."""

    def get_model_settings(self):
        def resolve(ctx: RunContext[None]) -> ModelSettings:
            if ctx.run_step > 1:
                return ModelSettings(thinking='high')
            return ModelSettings()

        return resolve


agent = Agent('openai:gpt-5.2', capabilities=[ThinkingOnRetry()])
result = agent.run_sync('hello')
print(result.output)
#> Hello! How can I help you today?
```

该 callable 会接收 [`RunContext`][pydantic_ai.tools.RunContext]，其中 `ctx.model_settings` 包含在此 capability 之前已解析的所有层的合并结果（model defaults 和 agent-level settings）。

### Configuration methods reference（配置方法参考） {#configuration-methods-reference}

| Method | Return type | 目的 |
|---|---|---|
| [`get_toolset()`][pydantic_ai.capabilities.AbstractCapability.get_toolset] | [`AgentToolset`][pydantic_ai.toolsets.AgentToolset] ` \| None` | 要注册的 [toolset](toolsets.md)（或用于 [dynamic toolsets](toolsets.md#dynamically-building-a-toolset) 的 callable） |
| [`get_native_tools()`][pydantic_ai.capabilities.AbstractCapability.get_native_tools] | `Sequence[`[`AgentNativeTool`][pydantic_ai.tools.AgentNativeTool]`]` | 要注册的 [Native tools](native-tools.md)（包括 callables） |
| [`get_wrapper_toolset()`][pydantic_ai.capabilities.AbstractCapability.get_wrapper_toolset] | [`AbstractToolset`][pydantic_ai.toolsets.AbstractToolset] ` \| None` | [包装 agent 已组装的 toolset](#toolset-wrapping) |
| [`get_instructions()`][pydantic_ai.capabilities.AbstractCapability.get_instructions] | [`AgentInstructions`][pydantic_ai._instructions.AgentInstructions] ` \| None` | [Instructions](agent.md#instructions)（static strings、[template strings](agent-spec.md#template-strings) 或 callables） |
| [`get_model_settings()`][pydantic_ai.capabilities.AbstractCapability.get_model_settings] | [`AgentModelSettings`][pydantic_ai.agent.abstract.AgentModelSettings] ` \| None` | [Model settings](agent.md#model-run-settings) dict，或用于 per-step settings 的 callable |

### Hooking into the lifecycle（接入生命周期） {#hooking-into-the-lifecycle}

Capabilities 可以接入五个 lifecycle points，每个 point 最多有四种 variants：

* **`before_*`**：在 action 之前触发，可修改 inputs
* **`after_*`**：在 action 成功后触发（按 capability 逆序），可修改 outputs
* **`wrap_*`**：完整 middleware 控制：接收 `handler` callable，并决定是否/如何调用它
* **`on_*_error`**：在 action 失败时触发（在 `wrap_*` 有机会 recover 之后），可观察、转换或从 errors 中 recover

!!! tip "提示"
    如果需要快速添加 application-level hooks 且不想 subclass，请改用 [`Hooks`](hooks.md) capability。

#### Run hooks（运行钩子） {#run-hooks}

| Hook | Signature | 目的 |
|---|---|---|
| [`before_run`][pydantic_ai.capabilities.AbstractCapability.before_run] | `(ctx: RunContext) -> None` | 仅观察 run 即将开始的通知 |
| [`after_run`][pydantic_ai.capabilities.AbstractCapability.after_run] | `(ctx: RunContext, *, result: AgentRunResult) -> AgentRunResult` | 修改最终 result |
| [`wrap_run`][pydantic_ai.capabilities.AbstractCapability.wrap_run] | `(ctx: RunContext, *, handler: WrapRunHandler) -> AgentRunResult` | 包装整个 run |
| [`on_run_error`][pydantic_ai.capabilities.AbstractCapability.on_run_error] | `(ctx: RunContext, *, error: BaseException) -> AgentRunResult` | 处理 run errors（见 [error hooks](#error-hooks)） |

`wrap_run` 支持 error recovery：如果 `handler()` raises，而 `wrap_run` 捕获 exception 并改为返回 result，则 error 会被抑制，并使用 recovery result。这同时适用于 [`agent.run()`][pydantic_ai.agent.AbstractAgent.run] 和 [`agent.iter()`][pydantic_ai.agent.Agent.iter]。

#### Node hooks（节点钩子） {#node-hooks}

| Hook | Signature | 目的 |
|---|---|---|
| [`before_node_run`][pydantic_ai.capabilities.AbstractCapability.before_node_run] | `(ctx: RunContext, *, node: AgentNode) -> AgentNode` | 在执行前观察或替换 node |
| [`after_node_run`][pydantic_ai.capabilities.AbstractCapability.after_node_run] | `(ctx: RunContext, *, node: AgentNode, result: NodeResult) -> NodeResult` | 修改 result（下一个 node 或 `End`） |
| [`wrap_node_run`][pydantic_ai.capabilities.AbstractCapability.wrap_node_run] | `(ctx: RunContext, *, node: AgentNode, handler: WrapNodeRunHandler) -> NodeResult` | 包装每个 graph node execution |
| [`on_node_run_error`][pydantic_ai.capabilities.AbstractCapability.on_node_run_error] | `(ctx: RunContext, *, node: AgentNode, error: Exception) -> NodeResult` | 处理 node errors（见 [error hooks](#error-hooks)） |

[`wrap_node_run`][pydantic_ai.capabilities.AbstractCapability.wrap_node_run] 会针对 [agent graph](agent.md#iterating-over-an-agents-graph) 中的每个 node 触发（[`UserPromptNode`][pydantic_ai.UserPromptNode]、[`ModelRequestNode`][pydantic_ai.ModelRequestNode]、[`CallToolsNode`][pydantic_ai.CallToolsNode]）。Override 它可以观察 node transitions、添加 per-step logging，或修改 graph progression：

!!! note "注意"
    [`agent.run()`][pydantic_ai.agent.AbstractAgent.run]、[`agent.run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream] 和 [`agent_run.next()`][pydantic_ai.run.AgentRun.next] 会自动调用 `wrap_node_run` hooks。不过，当使用裸 `async for node in agent_run:` 遍历 [`agent.iter()`][pydantic_ai.agent.Agent.iter] 时不会调用这些 hooks，因为它使用 graph run 的内部 iteration。如果需要触发 `wrap_node_run` hooks，请始终使用 `agent_run.next(node)` 推进 run。

```python {title="node_logging_example.py"}
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import (
    AbstractCapability,
    AgentNode,
    NodeResult,
    WrapNodeRunHandler,
)


@dataclass
class NodeLogger(AbstractCapability[Any]):
    """Logs each node that executes during a run."""

    nodes: list[str] = field(default_factory=list)

    async def wrap_node_run(
        self, ctx: RunContext[Any], *, node: AgentNode[Any], handler: WrapNodeRunHandler[Any]
    ) -> NodeResult[Any]:
        self.nodes.append(type(node).__name__)
        return await handler(node)


logger = NodeLogger()
agent = Agent('openai:gpt-5.2', capabilities=[logger])
agent.run_sync('hello')
print(logger.nodes)
#> ['UserPromptNode', 'ModelRequestNode', 'CallToolsNode']
```

你也可以使用 `wrap_node_run` 修改 graph progression，例如限制每次 run 的 model requests 数量：

```python {title="node_modification_example.py" test="skip" lint="skip"}
from dataclasses import dataclass
from typing import Any

from pydantic_graph import End

from pydantic_ai import ModelRequestNode, RunContext
from pydantic_ai.capabilities import AbstractCapability, AgentNode, NodeResult, WrapNodeRunHandler
from pydantic_ai.result import FinalResult


@dataclass
class MaxModelRequests(AbstractCapability[Any]):
    """Limits the number of model requests per run by ending early."""

    max_requests: int = 5
    count: int = 0

    async def for_run(self, ctx: RunContext[Any]) -> 'MaxModelRequests':
        return MaxModelRequests(max_requests=self.max_requests)  # fresh per run

    async def wrap_node_run(
        self, ctx: RunContext[Any], *, node: AgentNode[Any], handler: WrapNodeRunHandler[Any]
    ) -> NodeResult[Any]:
        if isinstance(node, ModelRequestNode):
            self.count += 1
            if self.count > self.max_requests:
                return End(FinalResult(output='Max model requests reached'))
        return await handler(node)
```

关于 agent graph 及其 node types 的更多信息，请参阅 [Iterating Over an Agent's Graph](agent.md#iterating-over-an-agents-graph)。

#### Model request hooks（模型请求钩子） {#model-request-hooks}

| Hook | Signature | 目的 |
|---|---|---|
| [`before_model_request`][pydantic_ai.capabilities.AbstractCapability.before_model_request] | `(ctx: RunContext, request_context: ModelRequestContext) -> ModelRequestContext` | 在 model call 前修改 messages、settings、parameters 或 model |
| [`after_model_request`][pydantic_ai.capabilities.AbstractCapability.after_model_request] | `(ctx: RunContext, *, request_context: ModelRequestContext, response: ModelResponse) -> ModelResponse` | 修改模型的 response |
| [`wrap_model_request`][pydantic_ai.capabilities.AbstractCapability.wrap_model_request] | `(ctx: RunContext, *, request_context: ModelRequestContext, handler: WrapModelRequestHandler) -> ModelResponse` | 包装 model call |
| [`on_model_request_error`][pydantic_ai.capabilities.AbstractCapability.on_model_request_error] | `(ctx: RunContext, *, request_context: ModelRequestContext, error: Exception) -> ModelResponse` | 处理 model request errors（见 [error hooks](#error-hooks)） |

[`ModelRequestContext`][pydantic_ai.models.ModelRequestContext] 会把 `model`、`messages`、`model_settings` 和 `model_request_parameters` 打包到单个 object 中，使签名更 future-proof。要替换某个 request 使用的模型，请把 `request_context.model` 设置为不同的 [`Model`][pydantic_ai.models.Model] instance。

要完全跳过 model call 并提供替代 response，请从 `before_model_request` 或 `wrap_model_request` raise [`SkipModelRequest(response)`][pydantic_ai.exceptions.SkipModelRequest]。

#### Tool hooks（工具钩子） {#tool-hooks}

Tool processing 有两个阶段：**validation**（根据 tool schema 解析并验证模型的 JSON arguments）和 **execution**（运行 tool function）。每个阶段都有自己的 hooks。

所有 tool hooks 都会接收带有 [`ToolDefinition`][pydantic_ai.tools.ToolDefinition] 的 `tool_def` parameter。

**Validation hooks**：`args` 是 validation 前来自模型的原始 `str | dict[str, Any]`，或 validation 后的 `dict[str, Any]`：

| Hook | Signature | 目的 |
|---|---|---|
| [`before_tool_validate`][pydantic_ai.capabilities.AbstractCapability.before_tool_validate] | `(ctx: RunContext, *, call: ToolCallPart, tool_def: ToolDefinition, args: RawToolArgs) -> RawToolArgs` | 在 validation 前修改 raw args（例如 JSON repair） |
| [`after_tool_validate`][pydantic_ai.capabilities.AbstractCapability.after_tool_validate] | `(ctx: RunContext, *, call: ToolCallPart, tool_def: ToolDefinition, args: ValidatedToolArgs) -> ValidatedToolArgs` | 修改 validated args |
| [`wrap_tool_validate`][pydantic_ai.capabilities.AbstractCapability.wrap_tool_validate] | `(ctx: RunContext, *, call: ToolCallPart, tool_def: ToolDefinition, args: RawToolArgs, handler: WrapToolValidateHandler) -> ValidatedToolArgs` | 包装 validation step |
| [`on_tool_validate_error`][pydantic_ai.capabilities.AbstractCapability.on_tool_validate_error] | `(ctx: RunContext, *, call: ToolCallPart, tool_def: ToolDefinition, args: RawToolArgs, error: Exception) -> ValidatedToolArgs` | 处理 validation errors（见 [error hooks](#error-hooks)） |

要跳过 validation 并提供 pre-validated args，请从 `before_tool_validate` 或 `wrap_tool_validate` raise [`SkipToolValidation(args)`][pydantic_ai.exceptions.SkipToolValidation]。

**Execution hooks**：`args` 始终是 validated `dict[str, Any]`：

| Hook | Signature | 目的 |
|---|---|---|
| [`before_tool_execute`][pydantic_ai.capabilities.AbstractCapability.before_tool_execute] | `(ctx: RunContext, *, call: ToolCallPart, tool_def: ToolDefinition, args: ValidatedToolArgs) -> ValidatedToolArgs` | 在 execution 前修改 args |
| [`after_tool_execute`][pydantic_ai.capabilities.AbstractCapability.after_tool_execute] | `(ctx: RunContext, *, call: ToolCallPart, tool_def: ToolDefinition, args: ValidatedToolArgs, result: Any) -> Any` | 修改 execution result |
| [`wrap_tool_execute`][pydantic_ai.capabilities.AbstractCapability.wrap_tool_execute] | `(ctx: RunContext, *, call: ToolCallPart, tool_def: ToolDefinition, args: ValidatedToolArgs, handler: WrapToolExecuteHandler) -> Any` | 包装 execution |
| [`on_tool_execute_error`][pydantic_ai.capabilities.AbstractCapability.on_tool_execute_error] | `(ctx: RunContext, *, call: ToolCallPart, tool_def: ToolDefinition, args: ValidatedToolArgs, error: Exception) -> Any` | 处理 execution errors（见 [error hooks](#error-hooks)） |

要跳过 execution 并提供替代 result，请从 `before_tool_execute` 或 `wrap_tool_execute` raise [`SkipToolExecution(result)`][pydantic_ai.exceptions.SkipToolExecution]。

#### Output hooks（输出钩子） {#output-hooks}

与 tool processing 一样，[output](output.md) processing 也有两个阶段：**validation**（根据 output schema 解析模型的 raw output）和 **processing**（提取 value，并调用任何 [output function](output.md#output-functions)）。每个阶段都有自己的 hooks。

所有 output hooks 都会接收带有 [`OutputContext`][pydantic_ai.capabilities.OutputContext] 的 `output_context` parameter（包含 mode、output type、schema info，以及 [tool output](output.md#tool-output) 的 tool call details）。

**Validate hooks** 只会针对需要 parsing 的 structured output 触发（prompted、native、tool、union output）。它们不会针对 plain text 或 image output 触发。**Process hooks** 会针对**所有 output types** 触发，包括 text、structured 和 image output。对于 [tool output](output.md#tool-output)，只会触发 output hooks，tool hooks 会完全跳过。

**Validation hooks**：只针对 structured output 触发；`output` 是 `str`（raw text）或 `dict`（tool args）：

| Hook | Signature | 目的 |
|---|---|---|
| [`before_output_validate`][pydantic_ai.capabilities.AbstractCapability.before_output_validate] | `(ctx, *, output_context, output: RawOutput) -> RawOutput` | 在 validation 前修改 raw output（例如 JSON repair） |
| [`after_output_validate`][pydantic_ai.capabilities.AbstractCapability.after_output_validate] | `(ctx, *, output_context, output: Any) -> Any` | 修改 validated output |
| [`wrap_output_validate`][pydantic_ai.capabilities.AbstractCapability.wrap_output_validate] | `(ctx, *, output_context, output: RawOutput, handler) -> Any` | 包装 validation step |
| [`on_output_validate_error`][pydantic_ai.capabilities.AbstractCapability.on_output_validate_error] | `(ctx, *, output_context, output: RawOutput, error: ValidationError \| ModelRetry) -> Any` | 处理 validation errors（见 [error hooks](#error-hooks)） |

**Processing hooks**：针对所有 output types 触发；`output` 是 validated/raw output。Output validators（[`@agent.output_validator`][pydantic_ai.Agent.output_validator]）在 processing pipeline 内运行（位于 `wrap_output_process` 内），因此 `after_output_process` 会看到完全验证后的 result：

| Hook | Signature | 目的 |
|---|---|---|
| [`before_output_process`][pydantic_ai.capabilities.AbstractCapability.before_output_process] | `(ctx, *, output_context, output: Any) -> Any` | 在 processing 前修改 output |
| [`after_output_process`][pydantic_ai.capabilities.AbstractCapability.after_output_process] | `(ctx, *, output_context, output: Any) -> Any` | 修改 processed result |
| [`wrap_output_process`][pydantic_ai.capabilities.AbstractCapability.wrap_output_process] | `(ctx, *, output_context, output: Any, handler) -> Any` | 包装 processing |
| [`on_output_process_error`][pydantic_ai.capabilities.AbstractCapability.on_output_process_error] | `(ctx, *, output_context, output: Any, error: Exception) -> Any` | 处理 processing errors（见 [error hooks](#error-hooks)） |

Output validate 和 process hooks 可以 raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry]，要求模型用 custom message 重试；这与 [output functions](output.md#output-functions) 和 [output validators](output.md#output-validator-functions) 使用的模式相同。完整模式请参阅 [Triggering retries with `ModelRetry`](hooks.md#triggering-retries-with-modelretry)。

#### Tool preparation（工具准备） {#tool-preparation}

Capabilities 可以通过两个 hooks 过滤或修改模型在每一步看到的 tool definitions：

- [`prepare_tools`][pydantic_ai.capabilities.AbstractCapability.prepare_tools]：只接收 **function** tools。用于过滤或修改模型可直接调用的 tools。
- [`prepare_output_tools`][pydantic_ai.capabilities.AbstractCapability.prepare_output_tools]：只接收 [output tools][pydantic_ai.output.ToolOutput]，其中 `ctx.retry`/`ctx.max_retries` 反映 agent retry budget 的 **output** 侧，与 [output hook](#output-hooks) lifecycle 匹配。

两个 hooks 都在 toolset 层级运行；结果会同时流入模型的 request parameters 和 `ToolManager.tools`，因此过滤也会阻止 tool execution。

```python {title="prepare_tools_example.py"}
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.capabilities import AbstractCapability


@dataclass
class HideDangerousTools(AbstractCapability[Any]):
    """Hides tools matching certain name prefixes from the model."""

    hidden_prefixes: tuple[str, ...] = ('delete_', 'drop_')

    async def prepare_tools(
        self, ctx: RunContext[Any], tool_defs: list[ToolDefinition]
    ) -> list[ToolDefinition]:
        return [td for td in tool_defs if not any(td.name.startswith(p) for p in self.hidden_prefixes)]


agent = Agent('openai:gpt-5.2', capabilities=[HideDangerousTools()])


@agent.tool_plain
def delete_file(path: str) -> str:
    """Delete a file."""
    return f'deleted {path}'


@agent.tool_plain
def read_file(path: str) -> str:
    """Read a file."""
    return f'contents of {path}'


result = agent.run_sync('hello')
# The model only sees `read_file`, not `delete_file`
```

对于简单场景，内置 [`PrepareTools`][pydantic_ai.capabilities.PrepareTools] / [`PrepareOutputTools`][pydantic_ai.capabilities.PrepareOutputTools] capabilities 可以包装 callable，而无需自定义 subclass。

#### Event stream hook（事件流钩子） {#event-stream-hook}

对于带 event streaming 的 runs（[`run_stream_events`][pydantic_ai.agent.AbstractAgent.run_stream_events]、[`event_stream_handler`][pydantic_ai.agent.Agent.__init__]、[UI event streams](ui/overview.md)），capabilities 可以观察或转换 event stream：

| Hook | Signature | 目的 |
|---|---|---|
| [`wrap_run_event_stream`][pydantic_ai.capabilities.AbstractCapability.wrap_run_event_stream] | `(ctx: RunContext, *, stream: AsyncIterable[AgentStreamEvent]) -> AsyncIterable[AgentStreamEvent]` | 观察、过滤或转换 streamed events |

```python {title="event_stream_example.py"}
from collections.abc import AsyncIterable
from dataclasses import dataclass
from typing import Any

from pydantic_ai import AgentStreamEvent, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import (
    PartStartEvent,
    TextPart,
    ToolCallEvent,
    ToolResultEvent,
)


@dataclass
class StreamAuditor(AbstractCapability[Any]):
    """Logs tool calls and text output during streamed runs."""

    async def wrap_run_event_stream(
        self,
        ctx: RunContext[Any],
        *,
        stream: AsyncIterable[AgentStreamEvent],
    ) -> AsyncIterable[AgentStreamEvent]:
        async for event in stream:
            if isinstance(event, ToolCallEvent):
                print(f'Tool called: {event.part.tool_name}')
            elif isinstance(event, ToolResultEvent):
                print(f'Tool result: {event.part.content!r}')
            elif isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
                print(f'Text: {event.part.content!r}')
            yield event
```

匹配 [`ToolCallEvent`][pydantic_ai.messages.ToolCallEvent] 和 [`ToolResultEvent`][pydantic_ai.messages.ToolResultEvent] 可同时处理 function tool calls（[`FunctionToolCallEvent`][pydantic_ai.messages.FunctionToolCallEvent] / [`FunctionToolResultEvent`][pydantic_ai.messages.FunctionToolResultEvent]）和 output tool calls（[`OutputToolCallEvent`][pydantic_ai.messages.OutputToolCallEvent] / [`OutputToolResultEvent`][pydantic_ai.messages.OutputToolResultEvent]）。需要区别处理它们时，请匹配具体 subclass。

!!! note "从 `FunctionToolCallEvent` / `FunctionToolResultEvent` 迁移"
    对于 output tool calls，请匹配 `OutputToolCallEvent` / `OutputToolResultEvent`（或共享基类 `ToolCallEvent` / `ToolResultEvent`）。`FunctionToolCallEvent` / `FunctionToolResultEvent` 会在 v2 中停止为 output tool calls 触发。

如果要构建把 streamed events 转换为 protocol-specific formats（如 SSE）的 web UIs，请参阅 [UI event streams](ui/overview.md) 文档和 [`UIEventStream`][pydantic_ai.ui.UIEventStream] base class。

#### Error hooks（错误钩子） {#error-hooks}

每个 lifecycle point 都有一个 `on_*_error` hook；它是 `after_*` 的 error counterpart。`after_*` hooks 在成功时触发，而 `on_*_error` hooks 在失败时触发（在 `wrap_*` 有机会 recover 之后）：

```
before_X → wrap_X(handler)
  ├─ success ─────────→ after_X (modify result)
  └─ failure → on_X_error
        ├─ re-raise ──→ (error propagates, after_X not called)
        └─ recover ───→ after_X (modify recovered result)
```

Error hooks 使用 **raise-to-propagate, return-to-recover** semantics：

- **Raise original error**：原样传播 error（*默认*）
- **Raise different exception**：转换 error
- **Return result**：抑制 error，并使用返回值

| Hook | 触发时机 | Recovery type |
|---|---|---|
| [`on_run_error`][pydantic_ai.capabilities.AbstractCapability.on_run_error] | Agent run 失败 | 返回 [`AgentRunResult`][pydantic_ai.run.AgentRunResult] |
| [`on_node_run_error`][pydantic_ai.capabilities.AbstractCapability.on_node_run_error] | Graph node 失败 | 返回下一个 node 或 [`End`][pydantic_graph.basenode.End] |
| [`on_model_request_error`][pydantic_ai.capabilities.AbstractCapability.on_model_request_error] | Model request 失败 | 返回 [`ModelResponse`][pydantic_ai.messages.ModelResponse] |
| [`on_tool_validate_error`][pydantic_ai.capabilities.AbstractCapability.on_tool_validate_error] | Tool validation 失败 | 返回 validated args `dict` |
| [`on_tool_execute_error`][pydantic_ai.capabilities.AbstractCapability.on_tool_execute_error] | Tool execution 失败 | 返回任意 tool result |
| [`on_output_validate_error`][pydantic_ai.capabilities.AbstractCapability.on_output_validate_error] | Output validation 失败 | 返回 validated output |
| [`on_output_process_error`][pydantic_ai.capabilities.AbstractCapability.on_output_process_error] | Output execution 失败 | 返回任意 output result |

```python {title="error_hooks_example.py" test="skip" lint="skip"}
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import ModelRequestContext, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ModelResponse, TextPart


@dataclass
class ErrorLogger(AbstractCapability[Any]):
    """Logs all errors that occur during agent runs."""

    errors: list[str] = field(default_factory=list)

    async def on_model_request_error(
        self, ctx: RunContext[Any], *, request_context: ModelRequestContext, error: Exception
    ) -> ModelResponse:
        self.errors.append(f'Model error: {error}')
        # Return a fallback response to recover
        return ModelResponse(parts=[TextPart(content='Service temporarily unavailable.')])

    async def on_tool_execute_error(
        self, ctx: RunContext[Any], *, call: Any, tool_def: Any, args: dict[str, Any], error: Exception
    ) -> Any:
        self.errors.append(f'Tool {call.tool_name} failed: {error}')
        raise error  # Re-raise to let the normal retry flow handle it
```

#### Deferred tool calls（延迟工具调用） {#deferred-tool-calls}

Capabilities 可以直接在 agent run 中解析 [deferred tool calls](deferred-tools.md)，即需要 approval 或在外部执行的 calls，而无需结束 run 并等待 follow-up：

| Hook | Signature | 目的 |
|---|---|---|
| [`handle_deferred_tool_calls`][pydantic_ai.capabilities.AbstractCapability.handle_deferred_tool_calls] | `(ctx: RunContext, *, requests: DeferredToolRequests) -> DeferredToolResults \| None` | Inline 解析部分或全部 pending approval/external calls |

多个 capabilities 可以各自处理一个 subset：dispatch 会跨 chain 累积 results，并且只把仍未解析的 requests 传给下一个 capability。返回 `None`（或没有 entries 的 [`DeferredToolResults`][pydantic_ai.tools.DeferredToolResults]）表示拒绝处理。任何仍未解析的内容都会作为 [`DeferredToolRequests`][pydantic_ai.output.DeferredToolRequests] output 冒泡给 caller 处理。

如果 application code 只是需要接入 handler，请使用专门的 [`HandleDeferredToolCalls`][pydantic_ai.capabilities.HandleDeferredToolCalls] capability；参见 [Resolving deferred calls with a handler](deferred-tools.md#resolving-deferred-calls-with-a-handler)。

### 包装 Capabilities {#wrapping-capabilities}

[`WrapperCapability`][pydantic_ai.capabilities.WrapperCapability] 会包装另一个 capability，并把所有 methods 委托给它；这类似于 toolsets 的 [`WrapperToolset`][pydantic_ai.toolsets.WrapperToolset]。Subclass 它可以在委托其余 methods 的同时 override 特定 methods：

```python {title="wrapper_capability_example.py" test="skip" lint="skip"}
from dataclasses import dataclass
from typing import Any

from pydantic_ai import ModelRequestContext, RunContext
from pydantic_ai.capabilities import WrapperCapability


@dataclass
class AuditedCapability(WrapperCapability[Any]):
    """Wraps any capability and logs its model requests."""

    async def before_model_request(
        self, ctx: RunContext[Any], request_context: ModelRequestContext
    ) -> ModelRequestContext:
        print(f'Request from {type(self.wrapped).__name__}')
        return await super().before_model_request(ctx, request_context)
```

内置 [`PrefixTools`][pydantic_ai.capabilities.PrefixTools] 就是 `WrapperCapability` 的示例；它包装另一个 capability，并为其 tool names 添加前缀。

### Per-run state isolation（按运行隔离状态） {#per-run-state-isolation}

默认情况下，capability instance 会在 agent 的所有 runs 之间共享。如果你的 capability 会累积不应在 runs 之间泄漏的 mutable state，请 override [`for_run`][pydantic_ai.capabilities.AbstractCapability.for_run] 返回 fresh instance：

```python {title="per_run_state.py"}
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, ModelRequestContext, RunContext
from pydantic_ai.capabilities import AbstractCapability


@dataclass
class RequestCounter(AbstractCapability[Any]):
    """Counts model requests per run."""

    count: int = 0

    async def for_run(self, ctx: RunContext[Any]) -> 'RequestCounter':
        return RequestCounter()  # fresh instance for each run

    async def before_model_request(
        self, ctx: RunContext[Any], request_context: ModelRequestContext
    ) -> ModelRequestContext:
        self.count += 1
        return request_context


counter = RequestCounter()
agent = Agent('openai:gpt-5.2', capabilities=[counter])

# The shared counter stays at 0 because for_run returns a fresh instance
agent.run_sync('first run')
agent.run_sync('second run')
print(counter.count)
#> 0
```

### 动态构建 Capability {#dynamically-building-a-capability}

Capabilities 可以在每次 agent run 前用函数动态构建；该函数接收 agent [`RunContext`][pydantic_ai.tools.RunContext]，并返回 capability 或 `None`。当 capability（其 instructions、model settings、hooks 或贡献的 toolset）依赖特定于 run 的信息（例如其 [dependencies](./dependencies.md)）时，这很有用。

要注册 dynamic capability，请把接收 [`RunContext`][pydantic_ai.tools.RunContext] 的函数传给 [`Agent`][pydantic_ai.Agent] constructor 或 [`agent.run()`][pydantic_ai.Agent.run] 的 `capabilities` argument。Sync 和 async functions 都受支持。该函数每次 run 调用一次，返回的 capability 会在该 run 剩余期间替代它，因此其 instructions、model settings、toolsets、native tools 和 hooks 都会正常流动。

```python {title="dynamic_capability.py"}
from dataclasses import dataclass
from typing import Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.models.test import TestModel


@dataclass
class Skill(AbstractCapability[str]):
    """Per-user skill loaded from a database at run time."""

    name: str
    role: Literal['admin', 'guest']

    def get_instructions(self) -> str:
        return f'You can use the {self.name} skill (role: {self.role}).'


# Pretend this comes from a database keyed by user.
SKILLS = {
    'alice': Skill(name='refunds', role='admin'),
    'bob': Skill(name='lookup', role='guest'),
}


def user_skill(ctx: RunContext[str]) -> AbstractCapability[str] | None:
    return SKILLS.get(ctx.deps)


agent = Agent(TestModel(), deps_type=str, capabilities=[user_skill])

result = agent.run_sync('hi', deps='alice')
print(result.all_messages()[0].instructions)
#> You can use the refunds skill (role: admin).
```

_（这个示例是完整的，可以"原样"运行）_

要从单个 factory 返回多个 capabilities，请用 [`CombinedCapability`][pydantic_ai.capabilities.CombinedCapability] 包装它们。

!!! note "Durable execution（持久执行：Temporal、DBOS、Prefect）"

    如果 dynamic capability 解析出的 capability 只贡献 instructions、model settings、native tools、hooks，或 `prepare_tools`/`get_wrapper_toolset`（即没有自己的 `get_toolset()`），它可以与 durable execution 无缝协作；factory 会在 workflow 中与 agent loop 的其他部分一起运行。这覆盖了常见的"从数据库加载此用户的 skill 并添加其 instructions"模式。

    不过，通过 `get_toolset()` 贡献自有 toolset 的 dynamic capabilities 尚不支持 durable execution。该 toolset 只有在 run time 才知道，因此会绕过 durable wrapper 的 construction-time toolset registration，并试图直接在 workflow 内执行 I/O。作为 workaround，请通过 `Agent(toolsets=[...])` 静态注册 toolsets（这样它们会被正确包装），并让 dynamic capability 间接引用它们，例如通过 [`prepare_tools`][pydantic_ai.capabilities.AbstractCapability.prepare_tools] 限定每次 run 可见的 tools，而不是在 factory 内构造 toolset。完整支持在 [#5253](https://github.com/pydantic/pydantic-ai/issues/5253) 跟踪。

### Composition 和 middleware semantics {#composition-and-middleware-semantics}

当多个 capabilities 传给 agent 时，它们会组合成单个 [`CombinedCapability`][pydantic_ai.capabilities.CombinedCapability]，并遵循 **middleware semantics**；这与 Django 和 Starlette 等 web frameworks 使用的模式相同：

* **Configuration** 会合并：instructions 连接起来，model settings 以加法方式合并（后面的 capabilities 覆盖前面的），toolsets 组合起来，native tools 收集起来。
* **`before_*`** hooks 按 capability 顺序触发（从 outermost 到 innermost）：`cap1 → cap2 → cap3`。
* **`after_*`** hooks 按反向顺序触发（从 innermost 到 outermost）：`cap3 → cap2 → cap1`。
* **`wrap_*`** hooks 作为 middleware 嵌套：`cap1` 包装 `cap2`，`cap2` 包装 `cap3`，`cap3` 包装实际操作。第一个 capability 是 **outermost** layer。
* **`get_wrapper_toolset`** 遵循相同嵌套：第一个 capability 的 wrapper 位于 outermost。

这意味着 list 中的第一个 capability 对操作有最先和最后的发言权：它会在任何其他 capability 之前看到原始 input，也会在所有 inner capabilities 处理后看到最终 output。

### Ordering（排序） {#ordering}

默认情况下，capabilities 会按你列出的顺序组合。当某个 capability 需要固定在特定位置，而不受用户列出位置影响时，请 override [`get_ordering`][pydantic_ai.capabilities.AbstractCapability.get_ordering]，返回 [`CapabilityOrdering`][pydantic_ai.capabilities.CapabilityOrdering]：

```python {title="capability_ordering_example.py"}
from dataclasses import dataclass
from typing import Any

from pydantic_ai.capabilities import (
    AbstractCapability,
    CapabilityOrdering,
    CombinedCapability,
)


@dataclass
class InstrumentationCapability(AbstractCapability[Any]):
    """Must wrap all other capabilities to trace everything."""

    def get_ordering(self) -> CapabilityOrdering:
        return CapabilityOrdering(position='outermost')


@dataclass
class PlainCapability(AbstractCapability[Any]):
    pass


# InstrumentationCapability ends up first regardless of list order
combined = CombinedCapability([PlainCapability(), InstrumentationCapability()])
assert type(combined.capabilities[0]) is InstrumentationCapability
```

可用 constraints 包括：

* **`position`**：`'outermost'` 或 `'innermost'`。把 capability 放入一个 tier，位于所有没有该 position 的 capabilities 之前（或之后）。多个 capabilities 可以共享一个 tier；原始 list order 用于打破同 tier 内的平局。
* **`wraps`**：此 capability 要包装的 capabilities list（也就是位于它们外侧）。每个 entry 可以是 capability **type**（通过 `issubclass` 匹配所有 instances），也可以是特定 **instance**（按 identity 匹配）。当你的 capability 需要看到另一个 capability 的 output 时使用：`CapabilityOrdering(wraps=[OtherCapability])`。
* **`wrapped_by`**：包装此 capability 的 capabilities list（也就是位于它外侧）。和 `wraps` 一样，接受 types 或 instances。它是 `wraps` 的反向。
* **`requires`**：必须存在的 capability types list。如果缺少任何一个，会 raise [`UserError`][pydantic_ai.exceptions.UserError]。这并不隐含 ordering。

声明 constraints 后，[`CombinedCapability`][pydantic_ai.capabilities.CombinedCapability] 会在 construction time 对其 children 进行拓扑排序，并保留用户提供的顺序作为 tie-breaker。

[`Hooks`][pydantic_ai.capabilities.Hooks] 通过 `ordering` parameter 支持 ordering，因此你可以不 subclass 也声明 ordering constraints：

```python {title="hooks_ordering_example.py"}
from pydantic_ai.capabilities import CapabilityOrdering, CombinedCapability, Hooks

logging_hooks = Hooks(ordering=CapabilityOrdering(position='outermost'))
rate_limit_hooks = Hooks(ordering=CapabilityOrdering(wrapped_by=[logging_hooks]))

# logging_hooks ends up outermost; rate_limit_hooks is wrapped by it
combined = CombinedCapability([rate_limit_hooks, logging_hooks])
assert combined.capabilities[0] is logging_hooks
assert combined.capabilities[1] is rate_limit_hooks
```

## 示例 {#examples}

### Guardrail（PII 脱敏） {#guardrail-pii-redaction}

Guardrail 是拦截 model requests 或 responses 以强制执行 safety rules 的 capability。下面这个 guardrail 会扫描 model responses 中潜在的 PII 并进行 redaction：

```python {title="guardrail_example.py"}
import re
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, ModelRequestContext, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ModelResponse, TextPart


@dataclass
class PIIRedactionGuardrail(AbstractCapability[Any]):
    """Redacts email addresses and phone numbers from model responses."""

    async def after_model_request(
        self,
        ctx: RunContext[Any],
        *,
        request_context: ModelRequestContext,
        response: ModelResponse,
    ) -> ModelResponse:
        for part in response.parts:
            if isinstance(part, TextPart):
                # Redact email addresses
                part.content = re.sub(
                    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                    '[EMAIL REDACTED]',
                    part.content,
                )
                # Redact phone numbers (simple US pattern)
                part.content = re.sub(
                    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                    '[PHONE REDACTED]',
                    part.content,
                )
        return response


agent = Agent('openai:gpt-5.2', capabilities=[PIIRedactionGuardrail()])
result = agent.run_sync("What's Jane's contact info?")
print(result.output)
#> You can reach Jane at [EMAIL REDACTED] or [PHONE REDACTED].
```

### Logging middleware（日志中间件） {#logging-middleware}

当你需要观察或计时某个操作的 input 和 output 时，`wrap_*` pattern 很有用。下面是一个记录每个 model request 和 tool call 的 capability：

```python {title="logging_middleware_example.py"}
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, ModelRequestContext, RunContext, ToolDefinition
from pydantic_ai.capabilities import (
    AbstractCapability,
    WrapModelRequestHandler,
    WrapToolExecuteHandler,
)
from pydantic_ai.messages import ModelResponse, ToolCallPart


@dataclass
class VerboseLogging(AbstractCapability[Any]):
    """Logs model requests and tool executions."""

    async def wrap_model_request(
        self,
        ctx: RunContext[Any],
        *,
        request_context: ModelRequestContext,
        handler: WrapModelRequestHandler,
    ) -> ModelResponse:
        print(f'  Model request (step {ctx.run_step}, {len(request_context.messages)} messages)')
        #>   Model request (step 1, 1 messages)
        response = await handler(request_context)
        print(f'  Model response: {len(response.parts)} parts')
        #>   Model response: 1 parts
        return response

    async def wrap_tool_execute(
        self,
        ctx: RunContext[Any],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
        handler: WrapToolExecuteHandler,
    ) -> Any:
        print(f'  Tool call: {call.tool_name}({args})')
        result = await handler(args)
        print(f'  Tool result: {result!r}')
        return result


agent = Agent('openai:gpt-5.2', capabilities=[VerboseLogging()])
result = agent.run_sync('hello')
print(f'Output: {result.output}')
#> Output: Hello! How can I help you today?
```

## Pydantic AI Harness（能力库） {#pydantic-ai-harness}

[**Pydantic AI Harness**](harness/overview.md) 是 Pydantic AI 的官方 capability library；memory、guardrails、context management 和 [code mode](https://github.com/pydantic/pydantic-ai-harness/tree/main/pydantic_ai_harness/code_mode) 等 standalone capabilities 位于其中，而不在 core 中。完整拆分请参阅 [What goes where?](harness/overview.md#what-goes-where)，也可以直接查看 [capability matrix](https://github.com/pydantic/pydantic-ai-harness#capability-matrix)。

## 第三方 Capabilities {#third-party-capabilities}

Capabilities 是第三方 packages 扩展 Pydantic AI 的推荐方式，因为它们可以把 tools 与 hooks、instructions 和 model settings 打包在一起。完整生态请参阅 [Extensibility](extensibility.md)，其中也包括可包装为 capabilities 的 [third-party toolsets](toolsets.md#third-party-toolsets)。

### Task Management（任务管理） {#task-management}

用于 task planning 和 progress tracking 的 capabilities 可帮助 agents 组织复杂工作：

* [`pydantic-ai-todo`](https://github.com/vstorm-co/pydantic-ai-todo) - 带有 `add_todo`、`read_todos`、`write_todos`、`update_todo_status` 和 `remove_todo` tools 的 `TodoCapability`。支持 subtasks、dependencies 和 PostgreSQL persistence。也提供较低层级的 `TodoToolset`。

### Context Management（上下文管理） {#context-management}

用于管理长 conversations 的 capabilities 可帮助 agents 保持在 context limits 内：

* [`summarization-pydantic-ai`](https://github.com/vstorm-co/summarization-pydantic-ai) - 用于管理长 conversations 的四个 capabilities：`ContextManagerCapability`（real-time token tracking、在可配置阈值自动 compression，以及大型 tool-output truncation）；`SummarizationCapability`（LLM-powered history compression）；`SlidingWindowCapability`（零成本 message trimming）；`LimitWarnerCapability`（在 hard context limits 前注入 finish-soon hint）。也提供 standalone `history_processors`：`SummarizationProcessor`、`SlidingWindowProcessor` 和 `LimitWarnerProcessor`。

### Multi-Agent Orchestration（多智能体编排） {#multi-agent-orchestration}

用于 spawning 和 delegating 到专门 subagents 的 capabilities 可帮助 agents 处理复杂且可并行的工作：

* [`subagents-pydantic-ai`](https://github.com/vstorm-co/subagents-pydantic-ai) - `SubAgentCapability` 添加用于 multi-agent delegation 的 tools：`task`（spawn subagent）、`check_task`、`wait_tasks`、`list_active_tasks`、`soft_cancel_task`、`hard_cancel_task` 和 `answer_subagent`。支持 sync、async 和 auto execution modes、nested subagents 以及 runtime agent creation。也通过 `create_subagent_toolset` 提供较低层级的 toolset。

### Guardrails & Safety（护栏与安全） {#guardrails-safety}

用于 cost control、input/output filtering 和 tool permissions 的 capabilities 可帮助 agents 保持安全并处于预算内：

* [`pydantic-ai-shields`](https://github.com/vstorm-co/pydantic-ai-shields) - 开箱即用的 guardrail capabilities：`CostTracking`（按 run 跟踪 token usage 和 USD cost，预算超支时 raise `BudgetExceededError`）；`ToolGuard`（阻止特定 tools 或要求 approval）；`InputGuard` 和 `OutputGuard`（custom sync 或 async validation functions）；以及 `PromptInjection`、`PiiDetector`、`SecretRedaction`、`BlockedKeywords` 和 `NoRefusals` content shields。

### File Operations & Sandboxing（文件操作与沙箱） {#file-operations-sandboxing}

用于 filesystem access 和 sandboxed code execution 的 capabilities 可帮助 agents 安全地处理文件和运行代码：

* [`pydantic-ai-backend`](https://github.com/vstorm-co/pydantic-ai-backend) - `ConsoleCapability` 使用 fine-grained permission system 注册 `ls`、`read_file`、`write_file`、`edit_file`、`glob`、`grep` 和 `execute` tools。Backends 包括 `StateBackend`（in-memory，用于 testing）、`LocalBackend`（real filesystem）、`DockerSandbox`（isolated container execution）和 `CompositeBackend`（跨 backends routing）。也提供较低层级的 `ConsoleToolset`。

### Agent Skills（Agent 技能） {#agent-skills}

实现 [Agent Skills](https://agentskills.io) 支持的 capabilities 可帮助 agents 高效发现并执行特定任务：

* [`pydantic-ai-skills`](https://github.com/DougTrajano/pydantic-ai-skills) - `SkillsCapability` 通过 progressive disclosure 实现 Agent Skills 支持（按需加载 skills 以减少 tokens）。支持 filesystem 和 programmatic skills；兼容 [agentskills.io](https://agentskills.io)。

如需把你的 package 添加到此页面，请打开 pull request。

## 发布 Capabilities {#publishing-capabilities}

要让 custom capability 可用于 [agent specs](agent-spec.md)，它需要 [`get_serialization_name`][pydantic_ai.capabilities.AbstractCapability.get_serialization_name]（默认是 class name），并且 constructor 必须接受 serializable arguments。默认 [`from_spec`][pydantic_ai.capabilities.AbstractCapability.from_spec] implementation 会调用 `cls(*args, **kwargs)`，因此简单 dataclasses 不需要 override：

```python {title="custom_spec_capability.py"}
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, AgentSpec
from pydantic_ai.capabilities import AbstractCapability


@dataclass
class RateLimit(AbstractCapability[Any]):
    """Limits requests per minute."""

    rpm: int = 60


# In YAML: `- RateLimit: {rpm: 30}`
# In Python:
agent = Agent.from_spec(
    AgentSpec(model='test', capabilities=[{'RateLimit': {'rpm': 30}}]),
    custom_capability_types=[RateLimit],
)
```

用户通过 [`Agent.from_spec`][pydantic_ai.Agent.from_spec] 或 [`Agent.from_file`][pydantic_ai.Agent.from_file] 上的 `custom_capability_types` parameter 注册 custom capability types。

当 constructor 接收无法用 YAML/JSON 表示的类型时，请 override [`from_spec`][pydantic_ai.capabilities.AbstractCapability.from_spec]。Spec fields 应镜像 dataclass fields，但使用 serializable types：

```python {title="from_spec_override_example.py" test="skip" lint="skip"}
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import RunContext, ToolDefinition
from pydantic_ai.capabilities import AbstractCapability


@dataclass
class ConditionalTools(AbstractCapability[Any]):
    """Hides tools unless a condition is met."""

    condition: Callable[[RunContext[Any]], bool]  # not serializable
    hidden_tools: list[str] = field(default_factory=list)

    @classmethod
    def from_spec(cls, hidden_tools: list[str]) -> 'ConditionalTools[Any]':
        # In the spec, there's no condition callable — always hide
        return cls(condition=lambda ctx: True, hidden_tools=hidden_tools)

    async def prepare_tools(
        self, ctx: RunContext[Any], tool_defs: list[ToolDefinition]
    ) -> list[ToolDefinition]:
        if self.condition(ctx):
            return [td for td in tool_defs if td.name not in self.hidden_tools]
        return tool_defs
```

在 YAML 中，这会写作 `- ConditionalTools: {hidden_tools: [dangerous_tool]}`。在 Python code 中，可以使用完整 constructor：`ConditionalTools(condition=my_check, hidden_tools=['dangerous_tool'])`。

Packaging conventions 和更广泛的 extension ecosystem 请参阅 [Extensibility](extensibility.md)。
