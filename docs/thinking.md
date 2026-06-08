# 思考

思考（或推理）是模型在给出最终答案之前，逐步处理问题的过程。

在支持的提供商之间启用思考的最简单方式，是使用 [`Thinking`][pydantic_ai.capabilities.Thinking] capability。
当你需要直接访问某个提供商的原生思考控制项时，也可以使用提供商专用设置完成高级配置。

## 统一思考设置 {#unified-thinking-settings}

使用 [`Thinking` capability](capabilities.md#thinking) 启用思考：

```python {title="thinking_capability.py"}
from pydantic_ai import Agent
from pydantic_ai.capabilities import Thinking

agent = Agent('anthropic:claude-opus-4-7', capabilities=[Thinking(effort='high')])
```

你也可以直接设置 [`ModelSettings`][pydantic_ai.settings.ModelSettings] 底层的 `thinking` 字段：

```python {title="unified_thinking.py"}
from pydantic_ai import Agent

agent = Agent('anthropic:claude-opus-4-7', model_settings={'thinking': 'high'})
```

[`Thinking.effort`][pydantic_ai.capabilities.Thinking.effort] 的值接受：

- `True` - 使用提供商的默认 effort 级别启用思考
- `False` - 禁用思考（对于始终启用思考的模型会被静默忽略）
- `'minimal'` / `'low'` / `'medium'` / `'high'` / `'xhigh'` - 以指定 effort 级别启用思考（不支持的级别会映射到最接近的可用值）

这些值也正是底层 `thinking` 模型设置接受的值。
省略该设置时，模型会使用默认行为。当统一设置和提供商专用设置（下方各节有说明）同时存在时，提供商专用设置优先。

### 提供商转换

`Thinking` capability 会把每个 effort 值映射为所选提供商的原生格式：

| 提供商 | `Thinking()` / `Thinking(effort=True)` | `Thinking(effort='high')` | 说明 |
|---|---|---|---|
| Anthropic（Opus 4.6+） | `anthropic_thinking={'type': 'adaptive'}` | `{type: 'adaptive'}` + `effort='high'` | Claude Opus 4.7 和 4.8 也支持 `effort='xhigh'` |
| Anthropic（较旧模型） | `anthropic_thinking={'type': 'enabled', 'budget_tokens': 10000}` | `budget_tokens=16384` | 基于预算；`'low'` -> 2048 tokens |
| OpenAI | `reasoning_effort='medium'` | `reasoning_effort='high'` | |
| Google（Gemini 3+） | `include_thoughts=True` | `thinking_level='HIGH'` | |
| Google（Gemini 2.5） | `include_thoughts=True` | `thinking_budget=24576` | |
| Groq | `reasoning_format='parsed'` | `reasoning_format='parsed'` | `thinking=False` -> `'hidden'`（并不是真正禁用） |
| OpenRouter | `reasoning={'effort': 'medium', 'enabled': True}` | `reasoning={'effort': 'high', 'enabled': True}` | `thinking=False` -> `effort='none'`；始终启用的路由会静默忽略；通过 `extra_body` 发送 |
| Cerebras | `disable_reasoning=False` | `disable_reasoning=False` | `thinking=False` -> `disable_reasoning=True` |
| xAI | `reasoning_effort='high'` | `reasoning_effort='high'` | 只有 `'low'` 和 `'high'`，且仅适用于 `grok-3-mini`；`thinking=False` 会被静默忽略 |
| Bedrock（Claude 4.6+） | `thinking.type='adaptive'` | `{type: 'adaptive'}` + `output_config.effort='high'` | 根据 AWS 文档，effort 位于同级 `output_config` 字段；`xhigh` 映射为 `max` |
| Bedrock（Claude 较旧模型） | `thinking.type='enabled'` | `budget_tokens=16384` | 基于预算 |
| Bedrock（OpenAI） | `reasoning_effort='medium'` | `reasoning_effort='high'` | Converse 拒绝 `'none'`；`thinking=False` 会被静默忽略 |
| Bedrock（Qwen） | `reasoning_config='high'` | `reasoning_config='high'` | 只有 `'low'` 和 `'high'`；`thinking=False` 会被静默忽略 |

## OpenAI

使用 [`OpenAIChatModel`][pydantic_ai.models.openai.OpenAIChatModel] 时，`<think>` 标签内的文本输出会转换为 [`ThinkingPart`][pydantic_ai.messages.ThinkingPart] 对象。
你可以通过[模型配置文件](models/openai.md#model-profile)上的 [`thinking_tags`][pydantic_ai.profiles.ModelProfile.thinking_tags] 字段自定义这些标签。

一些 [OpenAI 兼容模型提供商](models/openai.md#openai-compatible-models)也可能支持不由标签分隔的原生 thinking parts。它们会作为 API 中独立的自定义字段发送和接收。通常，如果你通过 `<provider>:<model>` 简写调用模型，Pydantic AI 会替你处理。不过，你仍然可以使用 [`openai_chat_thinking_field`][pydantic_ai.profiles.openai.OpenAIModelProfile.openai_chat_thinking_field] 配置这些字段。

如果你的提供商建议原样回传这些自定义字段，以获得缓存或交错思考收益，也可以通过 [`openai_chat_send_back_thinking_parts`][pydantic_ai.profiles.openai.OpenAIModelProfile.openai_chat_send_back_thinking_parts] 实现。

### OpenAI Responses

[`OpenAIResponsesModel`][pydantic_ai.models.openai.OpenAIResponsesModel] 可以生成原生 thinking parts。
要启用此功能，需要设置
[`OpenAIResponsesModelSettings.openai_reasoning_effort`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_reasoning_effort] 和 [`OpenAIResponsesModelSettings.openai_reasoning_summary`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_reasoning_summary] [模型设置](agent.md#model-run-settings)。

默认情况下，消息历史中 reasoning、text 和 function call parts 的唯一 ID 会发送给模型。如果你发送的消息历史与上一轮 Responses API 收到的内容不完全匹配，就可能出现类似 `"Item 'rs_123' of type 'reasoning' was provided without its required following item."` 的错误；
例如你使用了[历史处理器](message-history.md#processing-message-history)时就可能发生。
要禁用这一行为，可以关闭 [`OpenAIResponsesModelSettings.openai_send_reasoning_ids`][pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_send_reasoning_ids] [模型设置](agent.md#model-run-settings)。

```python {title="openai_thinking_part.py"}
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings

model = OpenAIResponsesModel('gpt-5.2')
settings = OpenAIResponsesModelSettings(
    openai_reasoning_effort='low',
    openai_reasoning_summary='detailed',
)
agent = Agent(model, model_settings=settings)
...
```

!!! note "没有摘要的原始推理"
    一些 OpenAI 兼容 API（例如 LM Studio、vLLM，或使用 gpt-oss 模型的 OpenRouter）可能返回没有 reasoning summary 的原始推理内容。这种情况下，[`ThinkingPart.content`][pydantic_ai.messages.ThinkingPart.content] 会为空，但原始推理可在 `provider_details['raw_content']` 中取得。根据 [OpenAI 指南](https://cookbook.openai.com/examples/responses_api/reasoning_items)，原始推理不应直接展示给用户，因此我们把它存到 `provider_details`，而不是主要的 `content` 字段。

## Anthropic

要启用思考，请使用 [`AnthropicModelSettings.anthropic_thinking`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_thinking] [模型设置](agent.md#model-run-settings)。

!!! note
    扩展思考（`type: 'enabled'` 搭配 `budget_tokens`）在 `claude-opus-4-6` 上已弃用，并在 `claude-opus-4-7` 和 `claude-opus-4-8` 上移除。对于这些模型，请改用[自适应思考](#adaptive-thinking--effort)。

```python {title="anthropic_thinking_part.py"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings

model = AnthropicModel('claude-sonnet-4-5')
settings = AnthropicModelSettings(
    anthropic_thinking={'type': 'enabled', 'budget_tokens': 1024},
)
agent = Agent(model, model_settings=settings)
...
```

### 交错思考

要启用[交错思考](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#interleaved-thinking)，需要在模型设置中包含 beta header：

```python {title="anthropic_interleaved_thinking.py"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings

model = AnthropicModel('claude-sonnet-4-5')
settings = AnthropicModelSettings(
    anthropic_thinking={'type': 'enabled', 'budget_tokens': 10000},
    extra_headers={'anthropic-beta': 'interleaved-thinking-2025-05-14'},
)
agent = Agent(model, model_settings=settings)
...
```

### 自适应思考与 Effort {#adaptive-thinking--effort}

从 `claude-opus-4-6` 开始，Anthropic 支持[自适应思考](https://docs.anthropic.com/en/docs/build-with-claude/adaptive-thinking)，模型会根据每个请求的复杂度动态决定何时思考以及思考多少。这取代了扩展思考（`type: 'enabled'` 搭配 `budget_tokens`），后者在 Opus 4.6 上已弃用，并在 Opus 4.7 和 4.8 上移除。Claude Opus 4.7 和 4.8 还新增了 `xhigh` effort 级别。自适应思考也会自动启用交错思考。

```python {title="anthropic_adaptive_thinking.py"}
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings

model = AnthropicModel('claude-opus-4-8')
settings = AnthropicModelSettings(
    anthropic_thinking={'type': 'adaptive'},
    anthropic_effort='high',
)
agent = Agent(model, model_settings=settings)
...
```

[`anthropic_effort`][pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_effort] 设置控制模型在回答中投入多少 effort（独立于 thinking）。详情请参阅 [Anthropic effort 文档](https://docs.anthropic.com/en/docs/build-with-claude/effort)。

!!! note
    较旧模型（`claude-sonnet-4-5`、`claude-opus-4-5` 等）不支持自适应思考，需要使用上方展示的 `{'type': 'enabled', 'budget_tokens': N}`。

Thinking tokens 会计入 Anthropic 的循环级[任务预算](models/anthropic.md#task-budgets-beta)，因此随着预算消耗，自适应思考会自然缩减。

## Google

高级用法可使用 [`GoogleModelSettings.google_thinking_config`][pydantic_ai.models.google.GoogleModelSettings.google_thinking_config] [模型设置](agent.md#model-run-settings)。

```python {title="google_thinking_part.py"}
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

model = GoogleModel('gemini-3.5-flash')
settings = GoogleModelSettings(google_thinking_config={'include_thoughts': True, 'thinking_level': 'MEDIUM'})
agent = Agent(model, model_settings=settings)
...
```

更多细节请参阅 [Google 模型文档](models/google.md#configure-thinking)。

## xAI

xAI 推理模型（Grok）支持原生思考。要在多轮对话中保留思考内容，请启用 [`XaiModelSettings.xai_include_encrypted_content`][pydantic_ai.models.xai.XaiModelSettings.xai_include_encrypted_content]。

```python {title="xai_thinking_part.py"}
from pydantic_ai import Agent
from pydantic_ai.models.xai import XaiModel, XaiModelSettings

model = XaiModel('grok-4-fast-reasoning')
settings = XaiModelSettings(xai_include_encrypted_content=True)
agent = Agent(model, model_settings=settings)
...
```

## Bedrock

对于 Claude Sonnet 4.6+ 和 Opus 4.6+，Pydantic AI 的统一 `thinking` 设置会自动转换为 AWS 要求的[自适应思考](https://docs.aws.amazon.com/bedrock/latest/userguide/claude-messages-adaptive-thinking.html)结构 - 设置 [`ModelSettings.thinking`][pydantic_ai.settings.ModelSettings.thinking] 即可。

对于较旧 Claude 模型，或需要固定特定 `budget_tokens` 时，你仍可以使用 [`BedrockModelSettings.bedrock_additional_model_requests_fields`][pydantic_ai.models.bedrock.BedrockModelSettings.bedrock_additional_model_requests_fields] [模型设置](agent.md#model-run-settings)直接传入提供商专用配置：

=== "Claude"

    ```python {title="bedrock_claude_thinking_part.py"}
    from pydantic_ai import Agent
    from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings

    model = BedrockConverseModel('us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    model_settings = BedrockModelSettings(
        bedrock_additional_model_requests_fields={
            'thinking': {'type': 'enabled', 'budget_tokens': 1024}
        }
    )
    agent = Agent(model=model, model_settings=model_settings)

    ```
=== "OpenAI"


    ```python {title="bedrock_openai_thinking_part.py"}
    from pydantic_ai import Agent
    from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings

    model = BedrockConverseModel('openai.gpt-oss-120b-1:0')
    model_settings = BedrockModelSettings(
        bedrock_additional_model_requests_fields={'reasoning_effort': 'low'}
    )
    agent = Agent(model=model, model_settings=model_settings)

    ```
=== "Qwen"


    ```python {title="bedrock_qwen_thinking_part.py"}
    from pydantic_ai import Agent
    from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings

    model = BedrockConverseModel('qwen.qwen3-32b-v1:0')
    model_settings = BedrockModelSettings(
        bedrock_additional_model_requests_fields={'reasoning_config': 'high'}
    )
    agent = Agent(model=model, model_settings=model_settings)

    ```

=== "Deepseek"
    Deepseek 模型的推理[始终启用](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-reasoning.html)。

    ```python {title="bedrock_deepseek_thinking_part.py"}
    from pydantic_ai import Agent
    from pydantic_ai.models.bedrock import BedrockConverseModel

    model = BedrockConverseModel('us.deepseek.r1-v1:0')
    agent = Agent(model=model)

    ```

## Groq

Groq 支持用不同格式接收 thinking parts：

- `"raw"`: thinking part 包含在 `<think>` 标签内的文本内容中，并会自动转换为 [`ThinkingPart`][pydantic_ai.messages.ThinkingPart] 对象。
- `"hidden"`: thinking part 不包含在文本内容中。
- `"parsed"`: thinking part 在响应中有自己的结构化 part，并会转换为 [`ThinkingPart`][pydantic_ai.messages.ThinkingPart] 对象。

要启用思考，请使用 [`GroqModelSettings.groq_reasoning_format`][pydantic_ai.models.groq.GroqModelSettings.groq_reasoning_format] [模型设置](agent.md#model-run-settings)：

```python {title="groq_thinking_part.py"}
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel, GroqModelSettings

model = GroqModel('qwen/qwen3-32b')
settings = GroqModelSettings(groq_reasoning_format='parsed')
agent = Agent(model, model_settings=settings)
...
```

!!! note
    Groq 不支持真正禁用思考。通过统一设置指定 `thinking=False` 时，Pydantic AI 会发送 `reasoning_format='hidden'`，这会抑制推理输出，但模型仍可能在内部推理。

## OpenRouter

要启用思考，请使用 [`OpenRouterModelSettings.openrouter_reasoning`][pydantic_ai.models.openrouter.OpenRouterModelSettings.openrouter_reasoning] [模型设置](agent.md#model-run-settings)。

```python {title="openrouter_thinking_part.py"}
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings

model = OpenRouterModel('openai/gpt-5.2')
settings = OpenRouterModelSettings(openrouter_reasoning={'effort': 'high'})
agent = Agent(model, model_settings=settings)
...
```

!!! note "Wire format 细节"
    [`thinking`][pydantic_ai.settings.ModelSettings.thinking] 的 truthy 值会在线路格式中同时发送 `effort` 和 `enabled: True`。显式的 `enabled: True` 对默认启用推理的模型没有影响，但对可选启用推理的路由（例如 `google/gemma-*` 家族的一部分）是必要的；否则即便设置了 `effort`，推理仍会保持禁用。

    [`thinking=False`][pydantic_ai.settings.ModelSettings.thinking] 会在上游能够遵守禁用信号的路由（例如 `anthropic/claude-sonnet-4.5`、`z-ai/glm-4.6`）上发送 `reasoning={'effort': 'none'}`，这是[文档化的 OpenRouter 禁用信号](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)。在上游始终启用的路由（例如 `openai/o3`、`openai/gpt-5`、`mistralai/magistral-medium-*`、`deepseek/deepseek-r1`、`x-ai/grok-3-mini`）上，`thinking=False` 会在模型配置文件层被静默忽略，与同一模型的直接路由行为一致。如果你需要显式的逐路由控制，请直接设置 [`OpenRouterModelSettings.openrouter_reasoning`][pydantic_ai.models.openrouter.OpenRouterModelSettings.openrouter_reasoning]。

## Mistral

`magistral` 模型家族支持思考，不需要专门启用。

## Cohere

`command-a-reasoning-08-2025` 模型支持思考，不需要专门启用。

## Hugging Face

`<think>` 标签内的文本输出会自动转换为 [`ThinkingPart`][pydantic_ai.messages.ThinkingPart] 对象。
你可以通过[模型配置文件](models/openai.md#model-profile)上的 [`thinking_tags`][pydantic_ai.profiles.ModelProfile.thinking_tags] 字段自定义这些标签。

## Outlines

一些通过 Outlines 运行的本地模型，会在文本输出中包含由标签分隔的 thinking part。这种情况下，Pydantic AI 会处理它，把 thinking part 从最终答案中分离出来，无需专门启用。默认使用的 thinking tags 是 `"<think>"` 和 `"</think>"`。如果你的模型使用不同标签，可以在[模型配置文件](models/openai.md#model-profile)中使用 [`thinking_tags`][pydantic_ai.profiles.ModelProfile.thinking_tags] 字段指定。

Outlines 目前不支持将 thinking 与结构化输出一起使用。如果你提供 `output_type`，模型文本输出将不会包含带相关标签的 thinking part，性能可能下降。
