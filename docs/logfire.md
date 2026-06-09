# Pydantic Logfire 调试和监控

使用 LLM 的应用会遇到一些广为人知、也容易理解的挑战：LLM **慢**、**不可靠**且**昂贵**。

这些应用也会遇到一些大多数开发者更少碰到的问题：LLM **易变**且**非确定性**。提示中的细微变化就可能完全改变模型表现，而且也没有可以运行的 `EXPLAIN` 查询来理解原因。

!!! danger "警告"
    从软件工程师的角度看，你可以把 LLM 想象成你听过的最糟糕数据库，而且还要更糟。

    如果 LLM 没有这么有用，我们根本不会碰它们。

要构建成功的 LLM 应用，我们需要新工具来理解模型性能，以及依赖这些模型的应用行为。

只能让你理解模型表现的 LLM 可观测性工具并不够用：调用 LLM API 很简单，难的是把它构建进应用。

## Pydantic Logfire

[Pydantic Logfire](https://pydantic.dev/logfire) 是由创建并维护 Pydantic Validation 和 Pydantic AI 的团队开发的可观测性平台。Logfire 旨在让你理解整个应用：Gen AI、经典预测式 AI、HTTP 流量、数据库查询，以及现代应用需要的其他一切，全部基于 OpenTelemetry。

!!! tip "Pydantic Logfire 是商业产品"
    Logfire 是一个有商业支持的托管平台，提供非常慷慨且永久的[免费层级](https://pydantic.dev/pricing/)。
    你可以在几分钟内注册并开始使用 Logfire。企业层级也可以自托管 Logfire。

Pydantic AI 对 Logfire 提供内置（但可选）支持。这意味着如果已安装并配置 `logfire` 包，且启用了智能体插桩，那么智能体运行的详细信息会发送到 Logfire。否则几乎没有额外开销，也不会发送任何内容。

下面示例展示了在 Logfire 中运行 [Weather Agent](examples/weather-agent.md) 的细节：

![Weather Agent Logfire](img/logfire-weather-agent.png)

一次智能体运行会生成一条 trace，并为每次模型请求和工具调用发出 spans。

## 使用 Logfire {#using-logfire}

要使用 Logfire，你需要一个 Logfire [账号](https://logfire.pydantic.dev)。`pydantic-ai` 已包含 Logfire Python SDK：

```bash
pip/uv-add pydantic-ai
```

如果你使用 slim 包，也可以安装带 `logfire` 可选组的版本：

```bash
pip/uv-add "pydantic-ai-slim[logfire]"
```

然后用 Logfire 认证本地环境：

```bash
py-cli logfire auth
```

并配置一个接收数据的项目：

```bash
py-cli logfire projects new
```

（或用 `logfire projects use` 使用已有项目）

这会在当前工作目录写入一个 `.logfire` 目录，Logfire SDK 会在运行时使用它进行配置。

完成后，就可以开始使用 Logfire 为 Pydantic AI 代码插桩：

```python {title="instrument_pydantic_ai.py" hl_lines="1 5 6"}
import logfire

from pydantic_ai import Agent

logfire.configure()  # (1)!
logfire.instrument_pydantic_ai()  # (2)!

agent = Agent('openai:gpt-5.2', instructions='Be concise, reply with one sentence.')
result = agent.run_sync('Where does "hello world" come from?')  # (3)!
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

1. [`logfire.configure()`][logfire.configure] 会配置 SDK；默认情况下它会从 `.logfire` 目录查找写入 token，但你也可以直接传入 token。
2. [`logfire.instrument_pydantic_ai()`][logfire.Logfire.instrument_pydantic_ai] 会启用 Pydantic AI 插桩。
3. 由于已启用插桩，每次运行都会生成一条 trace，并为模型调用和工具函数执行发出 spans。

_（这个示例是完整的，可以"按原样"运行）_

它会在 Logfire 中显示如下：

![Logfire Simple Agent Run](img/logfire-simple-agent.png)

[Logfire 文档](https://logfire.pydantic.dev/docs/)包含更多使用 Logfire 的细节，
包括如何为 [HTTPX](https://logfire.pydantic.dev/docs/integrations/http-clients/httpx/) 和 [FastAPI](https://logfire.pydantic.dev/docs/integrations/web-frameworks/fastapi/) 等其他库插桩。

因为 Logfire 构建于 [OpenTelemetry](https://opentelemetry.io/) 之上，所以你可以使用 Logfire Python SDK 将数据发送到任何 OpenTelemetry collector，参见[下文](#using-opentelemetry)。

### 调试

为了演示 Logfire 如何帮助你可视化一次 Pydantic AI 运行的流程，下面是在运行 [chat app 示例](examples/chat-app.md)时从 Logfire 看到的视图：

{{ video('a764aff5840534dc77eba7d028707bfa', 25) }}

### 监控性能

我们也可以在 Logfire 中用 SQL 查询数据，从而监控应用性能。下面是一个真实示例：在 Logfire 自身内部使用 Logfire 监控 Pydantic AI 运行：

![Logfire monitoring Pydantic AI](img/logfire-monitoring-pydanticai.png)

### 监控 HTTP 请求 {#monitoring-http-requests}

正如 Hamel Husain 有影响力的 2024 年博客文章 ["Fuck You, Show Me The Prompt."](https://hamel.dev/blog/posts/prompt/) 所说，
（请忽略标题大小写和措辞，观点是有效的）能够查看发给模型提供商的原始 HTTP 请求和响应通常很有用。

要观察发给模型提供商的原始 HTTP 请求，可以使用 Logfire 的 [HTTPX 插桩](https://logfire.pydantic.dev/docs/integrations/http-clients/httpx/)，因为所有 provider SDK（除 [Bedrock](models/bedrock.md) 之外）内部都使用 [HTTPX](https://www.python-httpx.org/) 库：


```py {title="with_logfire_instrument_httpx.py" hl_lines="7"}
import logfire

from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)  # (1)!

agent = Agent('openai:gpt-5.2')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

1. 更多细节请参阅 [`logfire.instrument_httpx` 文档][logfire.Logfire.instrument_httpx]；`capture_all=True` 表示同时捕获请求和响应的 headers 与 body。

![Logfire with HTTPX instrumentation](img/logfire-with-httpx.png)

## 使用 OpenTelemetry {#using-opentelemetry}

Pydantic AI 的插桩使用 [OpenTelemetry](https://opentelemetry.io/)（OTel），Logfire 也基于它构建。

这意味着你可以用任何 OpenTelemetry 后端调试和监控 Pydantic AI。

Pydantic AI 遵循 [OpenTelemetry Semantic Conventions for Generative AI systems](https://opentelemetry.io/docs/specs/semconv/gen-ai/)，所以虽然我们认为你会在使用 Logfire 平台时获得最佳体验 :wink:，但你应该也能使用任何支持 GenAI 的 OTel 服务。

### 将 Logfire 与替代 OTel 后端一起使用

你可以完全免费地使用 Logfire SDK，并把数据发送到任何 OpenTelemetry 后端。

下面示例展示如何配置 Logfire 库，把数据发送到优秀的 [otel-tui](https://github.com/ymtdzzz/otel-tui)，这是一个开源的、基于终端的 OTel 后端和查看器（与 Pydantic Validation 无关联）。

用 docker 运行 `otel-tui`（更多说明见 [otel-tui readme](https://github.com/ymtdzzz/otel-tui)）：

```txt title="Terminal"
docker run --rm -it -p 4318:4318 --name otel-tui ymtdzzz/otel-tui:latest
```

然后运行：

```python {title="otel_tui.py" hl_lines="7 8" test="skip"}
import os

import logfire

from pydantic_ai import Agent

os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'  # (1)!
logfire.configure(send_to_logfire=False)  # (2)!
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

agent = Agent('openai:gpt-5.2')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris
```

1. 将 `OTEL_EXPORTER_OTLP_ENDPOINT` 环境变量设置为你的 OpenTelemetry 后端 URL。如果你使用的后端需要身份验证，可能还需要设置[其他环境变量](https://opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/)。当然，这些变量也可以在进程外设置，例如使用 `export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`。
2. 我们[配置][logfire.configure] Logfire，禁用向 Logfire 自身的 OTel 后端发送数据。如果移除 `send_to_logfire=False`，数据会同时发送到 Logfire 和你的 OpenTelemetry 后端。

运行上面的代码会把 tracing 数据发送到 `otel-tui`，并显示如下：

![otel tui simple](img/otel-tui-simple.png)

把 [weather agent](examples/weather-agent.md) 示例连接到 `otel-tui` 时，可以看到它如何用于可视化更复杂的 trace：

![otel tui weather agent](img/otel-tui-weather.png)

关于使用 Logfire SDK 向替代后端发送数据的更多信息，请参阅
[Logfire 文档](https://logfire.pydantic.dev/docs/how-to-guides/alternative-backends/)。

### 不使用 Logfire 的 OTel

你也可以完全不使用 Logfire，直接从 Pydantic AI 发出 OpenTelemetry 数据。

为此，需要安装并配置所需的 OpenTelemetry 包。要运行下面的示例，请使用：

```txt title="Terminal"
uv run \
  --with 'pydantic-ai-slim[openai]' \
  --with opentelemetry-sdk \
  --with opentelemetry-exporter-otlp \
  raw_otel.py
```

```python {title="raw_otel.py" test="skip"}
import os

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider

from pydantic_ai import Agent

os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4318'
exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(exporter)
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(span_processor)

set_tracer_provider(tracer_provider)

Agent.instrument_all()
agent = Agent('openai:gpt-5.2')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> Paris
```

### 替代可观测性后端 {#alternative-observability-backends}

由于 Pydantic AI 使用 OpenTelemetry 做可观测性，你可以轻松把它配置为向任何 OpenTelemetry 兼容后端发送数据，而不仅限于我们的可观测性平台 [Pydantic Logfire](#pydantic-logfire)。

以下 providers 有专门的 Pydantic AI 文档：

<!-- 如需在此添加其他平台，必须追加到列表底部，并且只能写平台名称和链接。 -->
- [Langfuse](https://langfuse.com/docs/integrations/pydantic-ai)
- [W&B Weave](https://weave-docs.wandb.ai/guides/integrations/pydantic_ai/)
- [Arize](https://arize.com/docs/ax/observe/tracing-integrations-auto/pydantic-ai)
- [Openlayer](https://www.openlayer.com/docs/integrations/pydantic-ai)
- [LangWatch](https://docs.langwatch.ai/integration/python/integrations/pydantic-ai)
- [Patronus AI](https://docs.patronus.ai/docs/percival/integrations/pydantic)
- [Opik](https://www.comet.com/docs/opik/tracing/integrations/pydantic-ai)
- [mlflow](https://mlflow.org/docs/latest/genai/tracing/integrations/listing/pydantic_ai)
- [Agenta](https://docs.agenta.ai/observability/integrations/pydanticai)
- [Braintrust](https://www.braintrust.dev/docs/integrations/sdk-integrations/pydantic-ai)
- [SigNoz](https://signoz.io/docs/pydantic-ai-observability/)
- [Laminar](https://docs.laminar.sh/tracing/integrations/pydantic-ai)
- [Respan](https://respan.ai/docs/integrations/pydantic-ai)

## 高级用法

### 聚合 usage 属性名称

默认情况下，model/request spans 和 agent run spans 都使用标准的 `gen_ai.usage.input_tokens` 和 `gen_ai.usage.output_tokens` 属性。一些可观测性后端（例如 Datadog、New Relic、LangSmith、Opik）会跨所有 spans 聚合这些属性，因为 agent run spans 会报告其 child spans 的 usage 总和，所以可能导致重复计数。

为避免这种情况，可以启用 `use_aggregated_usage_attribute_names`，让 agent run spans 使用不同的属性名称（例如 `gen_ai.aggregated_usage.input_tokens`、`gen_ai.aggregated_usage.output_tokens` 和 `gen_ai.aggregated_usage.details.*`）：

!!! note "自定义命名空间"
    `gen_ai.aggregated_usage.*` 命名空间是自定义扩展，不属于 [OpenTelemetry Semantic Conventions for GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)。它是为了解决可观测性后端中的重复计数问题而引入的。如果 OpenTelemetry 未来为聚合 usage 引入官方约定，这个命名空间可能会更新或弃用。

```python
from pydantic_ai import Agent
from pydantic_ai.models.instrumented import InstrumentationSettings

Agent.instrument_all(InstrumentationSettings(use_aggregated_usage_attribute_names=True))
```

### 配置数据格式 {#configuring-data-format}

Pydantic AI 遵循 [OpenTelemetry Semantic Conventions for Generative AI systems](https://opentelemetry.io/docs/specs/semconv/gen-ai/)，具体来说是这些 conventions 的 1.37.0 版本。可以通过 [`InstrumentationSettings`][pydantic_ai.models.instrumented.InstrumentationSettings] 的 `version` 参数配置插桩格式。

**默认值是 `version=2`**，它在规范合规性和兼容性之间提供了良好平衡。

#### Version 1（旧版，已弃用）

基于 [OpenTelemetry semantic conventions version 1.36.0](https://github.com/open-telemetry/semantic-conventions/blob/v1.36.0/docs/gen-ai/README.md) 或更早版本。消息会作为 request span 的子事件（logs）逐条捕获。使用 `event_mode='logs'` 可将事件作为基于 OpenTelemetry log 的事件发出：

```python {title="instrumentation_settings_event_mode.py"}
import logfire

from pydantic_ai import Agent

logfire.configure()
logfire.instrument_pydantic_ai(version=1, event_mode='logs')
agent = Agent('openai:gpt-5.2')
result = agent.run_sync('What is the capital of France?')
print(result.output)
#> The capital of France is Paris.
```

这个版本在 Logfire UI 中显示效果不会那么好，并将在 Pydantic AI 的未来版本中移除，但可能对向后兼容有用。

#### Version 2（默认）

使用较新的 OpenTelemetry GenAI spec，并将消息存储在以下属性中：

- `gen_ai.system_instructions`，用于传给智能体的 instructions
- `gen_ai.input.messages` 和 `gen_ai.output.messages`，位于模型请求 spans 上
- `pydantic_ai.all_messages`，位于 agent run spans 上

出于兼容性原因，一些 span 和属性名称并不完全符合 spec。使用 version 3 或 4 可以获得更好的合规性。

#### 第 3 版 {#version-3}

在 version 2 基础上提供以下改进：

- **符合 spec 的 span 名称：**
    - `agent run` 变为 `invoke_agent {gen_ai.agent.name}`（填入 agent name）
    - `running tool` 变为 `execute_tool {gen_ai.tool.name}`（填入 tool name）
- **符合 spec 的属性名称：**
    - `tool_arguments` 变为 `gen_ai.tool.call.arguments`
    - `tool_response` 变为 `gen_ai.tool.call.result`
- **Thinking tokens 支持：** 在可用时捕获 thinking/reasoning tokens

#### 第 4 版 {#version-4}

在 version 3 基础上改进了多模态内容处理，以更好地对齐 [GenAI semantic conventions for multimodal inputs](https://opentelemetry.io/docs/specs/semconv/gen-ai/non-normative/examples-llm-calls/#multimodal-inputs-example)：

**基于 URL 的媒体（ImageUrl、AudioUrl、VideoUrl）：**

- 旧版（v1-3）：`{"type": "image-url", "url": "..."}`
- 新版（v4）：`{"type": "uri", "modality": "image", "uri": "...", "mime_type": "..."}`

**内联二进制内容（BinaryContent、FilePart）：**

- 旧版（v1-3）：`{"type": "binary", "media_type": "...", "content": "..."}`
- 新版（v4）：`{"type": "blob", "modality": "image", "mime_type": "...", "content": "..."}`

注意：根据 OTel spec，`modality` 字段只会包含在图像、音频和视频内容类型中。DocumentUrl 和不支持的媒体类型会省略 `modality` 字段。

#### 第 5 版 {#version-5}

在 version 4 基础上改进了延迟工具调用处理：

- [`CallDeferred`][pydantic_ai.exceptions.CallDeferred] 和 [`ApprovalRequired`][pydantic_ai.exceptions.ApprovalRequired] 异常不再记录 exception event，也不会把 span status 设置为 ERROR，因为 deferrals 是控制流，不是错误。span 会保持 UNSET。

---

请注意，OpenTelemetry Semantic Conventions 仍处于实验阶段，未来很可能发生变化。

### 设置 OpenTelemetry SDK providers

默认情况下会使用全局 `TracerProvider` 和 `LoggerProvider`。这些会由 `logfire.configure()` 自动设置。它们也可以通过 OpenTelemetry Python SDK 中的 `set_tracer_provider` 和 `set_logger_provider` 函数设置。你可以使用 [`InstrumentationSettings`][pydantic_ai.models.instrumented.InstrumentationSettings] 设置自定义 providers。

```python {title="instrumentation_settings_providers.py"}
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk.trace import TracerProvider

from pydantic_ai import Agent, InstrumentationSettings
from pydantic_ai.capabilities import Instrumentation

instrumentation_settings = InstrumentationSettings(
    tracer_provider=TracerProvider(),
    logger_provider=LoggerProvider(),
)

agent = Agent('openai:gpt-5.2', capabilities=[Instrumentation(settings=instrumentation_settings)])
# or to instrument all agents:
Agent.instrument_all(instrumentation_settings)
```

### 排除二进制内容

```python {title="excluding_binary_content.py"}
from pydantic_ai import Agent, InstrumentationSettings
from pydantic_ai.capabilities import Instrumentation

instrumentation_settings = InstrumentationSettings(include_binary_content=False)

agent = Agent('openai:gpt-5.2', capabilities=[Instrumentation(settings=instrumentation_settings)])
# or to instrument all agents:
Agent.instrument_all(instrumentation_settings)
```

### 排除 prompts 和 completions

出于隐私和安全原因，你可能希望在不向可观测性平台暴露敏感用户数据或专有 prompts 的情况下，监控智能体行为和性能。Pydantic AI 允许你从 telemetry 中排除实际内容，同时保留调试和监控所需的结构信息。

设置 `include_content=False` 时，Pydantic AI 会从 telemetry 中排除敏感内容，包括用户 prompts、模型 completions、工具调用参数和响应，以及任何其他消息内容。

```python {title="excluding_sensitive_content.py"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import Instrumentation
from pydantic_ai.models.instrumented import InstrumentationSettings

instrumentation_settings = InstrumentationSettings(include_content=False)

agent = Agent('openai:gpt-5.2', capabilities=[Instrumentation(settings=instrumentation_settings)])
# or to instrument all agents:
Agent.instrument_all(instrumentation_settings)
```

这个设置在生产环境中特别有用，因为合规要求或数据敏感性问题可能要求限制发送到可观测性平台的内容。

### 添加自定义 Metadata

使用智能体的 `metadata` 参数可以把额外数据附加到智能体 span。
启用插桩后，计算出的 metadata 会记录到 agent span 的 `metadata` 属性中。
详情和用法请参阅[智能体指南中的 usage 和 metadata 示例](agent.md#run-metadata)。
