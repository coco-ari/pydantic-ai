---
title: Pydantic AI Gateway
status: new
---

# Pydantic AI Gateway

**[Pydantic AI Gateway](https://logfire.pydantic.dev/)** 是一个统一接口，可用单个 key 访问多个 AI providers，并通过 [Pydantic Logfire](https://logfire.pydantic.dev/) 管理。功能包括内置 OpenTelemetry 可观测性、实时成本监控、failover 管理，以及与 [Pydantic stack](https://pydantic.dev/) 中其他工具的原生集成。

!!! warning "已迁移到 Pydantic Logfire"
    AI Gateway 已从 `gateway.pydantic.dev` 迁移到 [Pydantic Logfire](https://logfire.pydantic.dev/)。如果你之前使用独立 gateway，请参阅 [Pydantic AI Gateway is Moving to Pydantic Logfire](https://logfire.pydantic.dev/docs/gateway-migration/)。

在 [logfire.pydantic.dev](https://logfire.pydantic.dev/) 注册。

!!! question "有问题？"
    如有问题和反馈，请在 [Slack](https://logfire.pydantic.dev/docs/join-slack/) 联系我们。

## 文档集成 {#documentation-integration}

为了帮助你开始使用 Pydantic AI Gateway，Pydantic AI 文档中的一些代码示例包含 "Via Pydantic AI Gateway" 选项卡，并列提供 "Direct to Provider API" 选项卡，后者使用标准 Pydantic AI 模型字符串。两者的主要区别是：使用 Gateway 时，模型字符串使用 `gateway/` 前缀。

## 主要功能 {#key-features}

- **API key 管理**：使用单个 Gateway key 访问多个 LLM providers。
- **成本限制**：在项目、用户和 API key 层级设置支出限制，并支持每日、每周和每月上限。
- **BYOK 和托管 providers**：带上你自己的 LLM provider API keys（BYOK），或直接通过平台为推理付费。
- **多 provider 支持**：访问 OpenAI、Anthropic、Google Vertex、Groq 和 AWS Bedrock 的模型。_更多 providers 即将推出_。
- **路由组**：配置[路由组](#routing-groups)，在服务同一模型的 providers 之间 fail over，或按权重进行流量负载均衡。
- **后端可观测性**：通过 [Pydantic Logfire](https://pydantic.dev/logfire) 或任何 OpenTelemetry 后端记录每个请求（_即将推出_）。
- **零转换**：不同于把所有内容都转换为一个通用 schema 的传统 AI gateways，**Pydantic AI Gateway** 允许请求直接以每个 provider 的原生格式流转。这让你能在新模型功能发布后立即使用。
- **企业就绪**：继承 Logfire 的企业功能，包括 SSO、自定义角色和权限。

```python {title="hello_world.py"}
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5.2')

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

## 快速开始 {#quick-start}

本节包含如何设置账号并使用 Pydantic AI Gateway 凭据运行应用的说明。

### 创建账号 {#create-an-account}

1. 在 [logfire.pydantic.dev](https://logfire.pydantic.dev/) 注册
2. 选择区域并创建账号。
3. 在你的 organization settings 中激活 gateway。

### 创建 Gateway API keys {#create-gateway-api-keys}

进入 Logfire 中 organization 的 Gateway settings 并创建 API key。

## 使用方式 {#usage}

按照上面的说明设置账号后，你就可以通过 Pydantic AI Gateway 发起 AI 模型请求。
下面的代码片段展示了如何在不同框架和 SDK 中使用 Pydantic AI Gateway。

要使用不同模型，请把模型字符串 `gateway/<api_format>:<model_name>` 改为受支持 providers 提供的其他模型。

可用 providers 和模型示例：

| **Provider** | **API Format**  | **示例模型**                        |
| --- |-----------------|------------------------------------------|
| OpenAI | `openai`        | `gateway/openai:gpt-5.2`                 |
| Anthropic | `anthropic`     | `gateway/anthropic:claude-sonnet-4-6`    |
| Google Cloud（之前称为 Vertex AI） | `google-cloud` | `gateway/google-cloud:gemini-3-flash-preview` |
| Groq | `groq`          | `gateway/groq:openai/gpt-oss-120b`       |
| AWS Bedrock | `bedrock`       | `gateway/bedrock:amazon.nova-micro-v1:0` |

### Pydantic AI

开始前，请确保你使用的是 `pydantic-ai` 1.16 或更高版本。要更新到最新版本，请运行：

=== "uv"

    ```bash
    uv sync -P pydantic-ai
    ```

=== "pip"

    ```bash
    pip install -U pydantic-ai
    ```

把 `PYDANTIC_AI_GATEWAY_API_KEY` 环境变量设置为你的 Gateway API key：

```bash
export PYDANTIC_AI_GATEWAY_API_KEY="pylf_v..."
```

你可以用同一个 API key 访问多个模型，如下面的代码片段所示。

```python {title="hello_world.py"}
from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5.2')

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

#### 直接传入 API Key {#passing-api-key-directly}

使用 [`gateway_provider`][pydantic_ai.providers.gateway.gateway_provider] 直接传入 API key：

```python {title="passing_api_key.py"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.gateway import gateway_provider

provider = gateway_provider('openai', api_key='pylf_v...')
model = OpenAIChatModel('gpt-5.2', provider=provider)
agent = Agent(model)

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

#### 使用不同上游 provider {#using-a-different-upstream-provider}

要使用替代 provider 或路由组，可以在 route 参数中指定：

```python {title="routing_via_provider.py"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.gateway import gateway_provider

provider = gateway_provider(
    'openai',
    api_key='pylf_v...',
    route='builtin-openai'
)
model = OpenAIChatModel('gpt-5.2', provider=provider)
agent = Agent(model)

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

### Claude Code

开始前，请用 `/logout` 退出 Claude Code。

使用与你的 Logfire 区域匹配的 base URL，把 gateway 凭据设置为环境变量：

=== "US"

    ```bash
    export ANTHROPIC_BASE_URL="https://gateway-us.pydantic.dev/proxy/anthropic"
    export ANTHROPIC_AUTH_TOKEN="YOUR_GATEWAY_API_KEY"
    ```

=== "EU"

    ```bash
    export ANTHROPIC_BASE_URL="https://gateway-eu.pydantic.dev/proxy/anthropic"
    export ANTHROPIC_AUTH_TOKEN="YOUR_GATEWAY_API_KEY"
    ```

将 `YOUR_GATEWAY_API_KEY` 替换为你在 Logfire organization 的 Gateway settings 中获取的 API key。

输入 `claude` 启动 Claude Code。之后所有请求都会通过 Pydantic AI Gateway 路由。

### Codex

Codex 使用 OpenAI Responses API，因此应使用 Gateway 的 `openai-responses` route。

把 gateway API key 设置为环境变量：

```bash
export PYDANTIC_AI_GATEWAY_API_KEY="YOUR_GATEWAY_API_KEY"
```

然后使用与你的 Logfire 区域匹配的 base URL，把下面的配置添加到 `~/.codex/config.toml`：

=== "US"

    ```toml
    model = "gpt-5.4"
    model_provider = "pydantic_gateway"

    [model_providers.pydantic_gateway]
    name = "Pydantic AI Gateway"
    base_url = "https://gateway-us.pydantic.dev/proxy/openai-responses"
    env_key = "PYDANTIC_AI_GATEWAY_API_KEY"
    env_key_instructions = "Create a Gateway API key in your Logfire organization's Gateway settings."
    wire_api = "responses"
    ```

=== "EU"

    ```toml
    model = "gpt-5.4"
    model_provider = "pydantic_gateway"

    [model_providers.pydantic_gateway]
    name = "Pydantic AI Gateway"
    base_url = "https://gateway-eu.pydantic.dev/proxy/openai-responses"
    env_key = "PYDANTIC_AI_GATEWAY_API_KEY"
    env_key_instructions = "Create a Gateway API key in your Logfire organization's Gateway settings."
    wire_api = "responses"
    ```

关于在 Codex 中配置自定义 providers 的更多细节，请参阅 [Codex custom model providers docs](https://developers.openai.com/codex/config-advanced#custom-model-providers) 和 [Codex configuration reference](https://developers.openai.com/codex/config-reference/)。

如果你已经有 `~/.codex/config.toml`，请添加 `[model_providers.pydantic_gateway]` block 并更新 `model_provider`，而不是替换整个文件。把 `gpt-5.4` 替换为你希望 Codex 使用的任意 OpenAI Responses 模型。

输入 `codex` 启动 Codex。之后所有请求都会通过 Pydantic AI Gateway 路由。

### SDKs

#### OpenAI SDK

使用与你的 Logfire 区域匹配的 base URL（`gateway-us` 或 `gateway-eu`）。

=== "US"

    ```python {title="openai_sdk.py" test="skip"}
    import openai

    client = openai.Client(
        base_url='https://gateway-us.pydantic.dev/proxy/chat/',
        api_key='pylf_v...',
    )

    response = client.chat.completions.create(
        model='gpt-5.2',
        messages=[{'role': 'user', 'content': 'Hello world'}],
    )
    print(response.choices[0].message.content)
    #> Hello user
    ```

=== "EU"

    ```python {title="openai_sdk.py" test="skip"}
    import openai

    client = openai.Client(
        base_url='https://gateway-eu.pydantic.dev/proxy/chat/',
        api_key='pylf_v...',
    )

    response = client.chat.completions.create(
        model='gpt-5.2',
        messages=[{'role': 'user', 'content': 'Hello world'}],
    )
    print(response.choices[0].message.content)
    #> Hello user
    ```

#### Anthropic SDK

使用与你的 Logfire 区域匹配的 base URL（`gateway-us` 或 `gateway-eu`）。

=== "US"

    ```python {title="anthropic_sdk.py" test="skip"}
    import anthropic

    client = anthropic.Anthropic(
        base_url='https://gateway-us.pydantic.dev/proxy/anthropic/',
        auth_token='pylf_v...',
    )

    response = client.messages.create(
        max_tokens=1000,
        model='claude-sonnet-4-5',
        messages=[{'role': 'user', 'content': 'Hello world'}],
    )
    print(response.content[0].text)
    #> Hello user
    ```

=== "EU"

    ```python {title="anthropic_sdk.py" test="skip"}
    import anthropic

    client = anthropic.Anthropic(
        base_url='https://gateway-eu.pydantic.dev/proxy/anthropic/',
        auth_token='pylf_v...',
    )

    response = client.messages.create(
        max_tokens=1000,
        model='claude-sonnet-4-5',
        messages=[{'role': 'user', 'content': 'Hello world'}],
    )
    print(response.content[0].text)
    #> Hello user
    ```

#### Vercel AI SDK

[Vercel AI SDK](https://ai-sdk.dev/) 可以通过把每个 provider 的 `baseURL` 指向匹配的 proxy path（例如 `/proxy/openai` 或 `/proxy/anthropic`）来经由 Gateway 路由。请使用与你的 Logfire 区域匹配的 base URL（`gateway-us` 或 `gateway-eu`）。

=== "US"

    ```typescript
    import { createOpenAI } from "@ai-sdk/openai";
    import { generateText } from "ai";

    const apiKey = process.env.PYDANTIC_AI_GATEWAY_API_KEY;
    if (!apiKey) throw new Error("set PYDANTIC_AI_GATEWAY_API_KEY");

    const openai = createOpenAI({
      apiKey,
      baseURL: "https://gateway-us.pydantic.dev/proxy/openai",
    });

    async function main() {
      const openaiResult = await generateText({
        model: openai("gpt-5.2"),
        prompt: "what color is the sky? reply concisely",
      });
      console.log("openai:", openaiResult.text);
    }

    main().catch((err) => {
      console.error(err);
      process.exit(1);
    });
    ```

=== "EU"

    ```typescript
    import { createOpenAI } from "@ai-sdk/openai";
    import { generateText } from "ai";

    const apiKey = process.env.PYDANTIC_AI_GATEWAY_API_KEY;
    if (!apiKey) throw new Error("set PYDANTIC_AI_GATEWAY_API_KEY");

    const openai = createOpenAI({
      apiKey,
      baseURL: "https://gateway-eu.pydantic.dev/proxy/openai",
    });

    async function main() {
      const openaiResult = await generateText({
        model: openai("gpt-5.2"),
        prompt: "what color is the sky? reply concisely",
      });
      console.log("openai:", openaiResult.text);
    }

    main().catch((err) => {
      console.error(err);
      process.exit(1);
    });
    ```

## 路由组 {#routing-groups}

**路由组**是一组具名 providers，它们都服务同一个模型。每个成员都有一个**优先级**、一个**权重**和一个 **active** 标志，这三个值组合起来，让单个组可以表达两种不同的路由策略：

- **Failover / fallback**：为成员分配不同优先级。Gateway 总是先尝试优先级最高的 active 成员，只有当更高优先级成员不可用时（例如宕机、被限流或返回错误），才会落到低优先级成员。
- **负载均衡**：为两个或更多成员分配相同优先级，并给每个成员一个权重。Gateway 会按照权重比例把流量分配给这些成员。

两种策略可以组合：例如，你可以有一个最高优先级层，其中两个 providers 以 70/30 负载均衡；再有一个第二优先级层，只有当顶层两个 providers 都失败时才接收流量。

### 创建路由组 {#creating-a-routing-group}

路由组从 Logfire 中 organization 的 Gateway settings 管理：

1. 打开 **Gateway -> Routing Groups**，点击 **Add Routing Group**。
2. 为该组指定一个 slug（例如 `anthropic-routing`）和可选描述。
3. 打开该组的 **Members** 页面，并添加一个或多个 providers。为每个成员设置：
    - **Priority**：值越高越优先尝试。为成员设置不同优先级可实现 failover。
    - **Weight**：同优先级成员之间使用的负载均衡权重。
    - **Active**：inactive 成员会在路由时跳过。

### 使用路由组 {#using-a-routing-group}

通过 `route` 参数（路由组 slug）把 Gateway provider 指向该组：

```python {title="routing_group.py"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.gateway import gateway_provider

provider = gateway_provider(
    'anthropic',
    api_key='pylf_v...',
    route='anthropic-routing',  # (1)!
)
model = AnthropicModel('claude-sonnet-4-6', provider=provider)
agent = Agent(model)

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
"""
The first known use of "hello, world" was in a 1974 textbook about the C programming language.
"""
```

1. 你在 Logfire 中创建的路由组 slug。

## 故障排查 {#troubleshooting}

### 无法计算支出 {#unable-to-calculate-spend}

Gateway 需要知道请求成本，才能提供支出洞察并强制执行支出限制。

每个 provider 的设置中都有一个 **Require pricing data** 开关。启用时（默认），gateway 会在把请求转发到上游之前，拒绝它没有价格数据的模型请求。禁用时，这些请求会被允许通过，但其成本不会被跟踪，也不会计入支出限制。

拒绝响应取决于 provider 类型：

- **内置 providers**（Pydantic 管理）：`404`，并带有一条消息，请你在 Slack 上告知我们，以便添加该模型。
- **自定义 providers**（你自己的 API keys）：`400`，表示需要价格数据，并提示如果你仍然想让请求通过，可以禁用该开关。

我们正在积极支持更多 providers 和模型。如果你希望看到某个特定 provider 或模型受到支持，请在 [Slack](https://logfire.pydantic.dev/docs/join-slack/) 告诉我们，或在 [`genai-prices` 上提交 issue](https://github.com/pydantic/genai-prices/issues/new)。
