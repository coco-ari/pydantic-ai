# Agent 规格说明 {#agent-specs}

Agent 规格说明允许你用 YAML 或 JSON 声明式定义 agents，包括 [model](models/overview.md)、[instructions](agent.md#instructions)、[capabilities](capabilities.md) 等。只需一行即可加载，无需编写 Python agent 构造代码。

这适用于：

- 将 agent 配置与应用代码分离
- 让非开发者（prompt engineers、领域专家）配置 agents
- 将 agent 定义与其他配置文件放在一起
- 在团队或项目之间共享 agent 配置

## 定义 spec {#defining-a-spec}

spec 文件用 YAML 或 JSON 定义 agent 配置：

```yaml {title="agent.yaml" test="skip"}
model: anthropic:claude-opus-4-6
instructions: You are a helpful research assistant.
model_settings:
  max_tokens: 8192
capabilities:
  - WebSearch:
      local: duckduckgo
  - Thinking:
      effort: high
```

## 加载 specs {#loading-specs}

[`Agent.from_file`][pydantic_ai.Agent.from_file] 会从 YAML 或 JSON 文件加载 spec 并构建 agent：

```python {title="from_file_example.py" test="skip"}
from pydantic_ai import Agent

agent = Agent.from_file('agent.yaml')
```

[`Agent.from_spec`][pydantic_ai.Agent.from_spec] 接受 dict 或 [`AgentSpec`][pydantic_ai.agent.spec.AgentSpec] 实例，并支持额外关键字参数来补充或覆盖 spec：

```python {title="from_spec_example.py"}
from dataclasses import dataclass

from pydantic_ai import Agent


@dataclass
class UserContext:
    user_name: str


agent = Agent.from_spec(
    {
        'model': 'anthropic:claude-opus-4-6',
        'instructions': 'You are helping {{user_name}}.',
        'capabilities': [{'WebSearch': {'local': 'duckduckgo'}}],
    },
    deps_type=UserContext,
)
```

关键字参数与 spec 字段的交互方式如下：

* **标量字段**（`model`、`name`、`end_strategy` 等）：提供关键字参数时，会覆盖 spec 值。对于 retry budgets，`retries` 关键字参数会覆盖 spec 的 `retries` 值。
* **`instructions`**：合并；spec instructions 在前，关键字参数 instructions 在后。
* **`capabilities`**：合并；spec capabilities 在前，关键字参数 capabilities 在后。
* **`model_settings`**：增量合并；关键字参数 settings 会覆盖匹配的 spec settings。
* **`output_type`**：优先级高于 spec 中的 `output_schema`。

传入 `deps_type` 时，spec 的 `instructions`、`description` 和 capability 参数中的 [template strings](#template-strings) 会在构造时编译，并根据 deps type 验证。

若需要更精细地控制 spec 加载，请使用 [`AgentSpec.from_file`][pydantic_ai.agent.spec.AgentSpec.from_file] 单独加载 spec，然后再传给 `Agent.from_spec`。

## 模板字符串 {#template-strings}

[`TemplateStr`][pydantic_ai.TemplateStr] 提供 Handlebars 风格模板（`{{variable}}`），会在运行时根据 agent 的[依赖](dependencies.md)渲染。在 spec 文件中，包含 `{{` 的字符串会自动转换为 template strings：

```yaml {test="skip"}
instructions: "You are assisting {{name}}, who is a {{role}}."
```

模板变量会从 `deps` 对象字段解析。提供 `deps_type`（或 [`deps_schema`](#deps_schema)）时，模板变量名称会在构造时验证。

在 Python 代码中，可以显式使用 [`TemplateStr`][pydantic_ai.TemplateStr]；不过通常更推荐使用带 [`RunContext`][pydantic_ai.tools.RunContext] 的 callable，以获得 IDE 自动补全和类型检查：

```python {title="template_instructions.py"}
from dataclasses import dataclass

from pydantic_ai import Agent, TemplateStr


@dataclass
class UserProfile:
    name: str
    role: str


agent = Agent(
    'openai:gpt-5.2',
    deps_type=UserProfile,
    instructions=TemplateStr('You are assisting {{name}}, who is a {{role}}.'),
)
result = agent.run_sync('hello', deps=UserProfile(name='Alice', role='engineer'))
print(result.output)
#> Hello! How can I help you today?
```

## Capability spec 语法 {#capability-spec-syntax}

spec 中的 capabilities 支持三种形式：

* `'MyCapability'`：无参数，调用 `MyCapability.from_spec()`
* `{'MyCapability': value}`：单个位置参数，调用 `MyCapability.from_spec(value)`
* `{'MyCapability': {key: value, ...}}`：关键字参数，调用 `MyCapability.from_spec(**kwargs)`

## Specs 中的自定义 capabilities {#custom-capabilities-in-specs}

如何让自定义 capabilities 与 agent specs 配合使用，请参见[发布 capabilities](capabilities.md#publishing-capabilities)。

## `AgentSpec` 参考 {#agentspec-reference}

[`AgentSpec`][pydantic_ai.agent.spec.AgentSpec] model 表示完整 spec 结构：

| 字段 | 类型 | 描述 |
|---|---|---|
| `model` | `str` | [Model](models/overview.md) 名称（必需） |
| `name` | `str \| None` | Agent 名称 |
| `description` | `str \| None` | Agent 描述（支持 [templates](#template-strings)） |
| `instructions` | `str \| list[str] \| None` | [Instructions](agent.md#instructions)（支持 [templates](#template-strings)） |
| `model_settings` | `dict \| None` | [模型设置](agent.md#model-run-settings) |
| `capabilities` | `list` | [Capabilities](capabilities.md)（见 [spec syntax](#capability-spec-syntax)） |
| `deps_schema` | `dict \| None` | 用于 [template string](#template-strings) 验证的 JSON Schema（见下文） |
| `output_schema` | `dict \| None` | 用于[结构化输出](output.md)的 JSON Schema（见下文） |
| `retries` | `int \| AgentRetries \| None` | [tools](tools-advanced.md#tool-retries) 和 [output validation](output.md#output-validator-functions) 的 retry budgets。传入整数可让两者使用同一预算，或传入 [`AgentRetries`][pydantic_ai.agent.AgentRetries] 分别配置。 |
| `end_strategy` | `EndStrategy` | 何时停止（`'early'` 或 `'exhaustive'`） |
| `tool_timeout` | `float \| None` | 默认 [tool](tools.md) timeout，单位秒 |
| `instrument` | `bool \| None` | 启用 [Logfire](logfire.md) instrumentation |
| `metadata` | `dict \| None` | Agent [元数据](agent.md#run-metadata) |

### `deps_schema`

在没有 Python `deps_type` 的情况下加载 spec 文件时，`deps_schema` 会提供 JSON Schema，用于在构造时验证 [template string](#template-strings) variable 名称。它**不会**在运行时验证实际 deps 对象，只会确保 `{{user_name}}` 这样的 template variables 对应 schema 中定义的 properties。

### `output_schema`

提供 `output_schema` 时（并且没有向 `from_spec` 传入 `output_type` 关键字参数），它定义模型最终 output 应产生的结构。在底层，它会创建 [`StructuredDict`][pydantic_ai.output.StructuredDict] output type：JSON Schema 会发送给 model API，让模型知道要产生什么结构，而响应会以 `dict[str, Any]` 返回。

!!! note
    模型响应不会根据 schema 的 `properties` 或 `required` 字段验证，而是作为普通 dict 接受。schema 是给模型的 instruction，不是运行时验证约束。

```yaml {title="agent_with_schema.yaml" test="skip"}
model: anthropic:claude-opus-4-6
deps_schema:
  type: object
  properties:
    user_name:
      type: string
  required: [user_name]
output_schema:
  type: object
  properties:
    answer:
      type: string
    confidence:
      type: number
  required: [answer, confidence]
instructions: "You are helping {{user_name}}. Always include a confidence score."
capabilities:
  - WebSearch:
      local: duckduckgo
```

## 保存 specs {#saving-specs}

[`AgentSpec.to_file`][pydantic_ai.agent.spec.AgentSpec.to_file] 会将 spec 保存为 YAML 或 JSON，并可选生成一个配套 JSON Schema 文件，用于编辑器自动补全：

```python {title="save_spec_example.py"}
from pydantic_ai import AgentSpec

spec = AgentSpec(
    model='anthropic:claude-opus-4-6',
    instructions='You are a helpful assistant.',
    capabilities=[{'WebSearch': {'local': 'duckduckgo'}}],
)
spec.to_file('agent.yaml')
# 也会生成 ./agent_schema.json 用于编辑器自动补全
```

生成的 JSON Schema 文件可在支持 [YAML Language Server](https://github.com/redhat-developer/yaml-language-server) protocol 的编辑器中启用自动补全和验证。传入 `schema_path=None` 可跳过 schema 生成。
