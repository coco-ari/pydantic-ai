
# 可扩展性 {#extensibility}

Pydantic AI 的设计目标之一就是易于扩展。[Capabilities](capabilities.md) 是主要扩展点：它们会把工具、生命周期 hooks、instructions 和模型设置打包成可复用单元，可在多个智能体之间共享、作为库发布，并从 [spec 文件](agent-spec.md)加载。

除了 capabilities，Pydantic AI 还为专门需求提供了其他几种扩展机制。

## Capabilities

Capabilities 是扩展 Pydantic AI 的推荐方式，适用于：

- **团队**构建可复用的内部智能体组件（guardrails、审计日志、认证）
- **包作者**发布可跨模型和智能体工作的扩展
- **社区贡献者**分享常见问题的解决方案

使用和构建 capabilities 请参见 [Capabilities](capabilities.md)；轻量级、基于装饰器的做法请参见 [Hooks](hooks.md)。

!!! tip
    如果你想贡献 capability，请在 [**Pydantic AI Harness**](https://github.com/pydantic/pydantic-ai-harness) 上开 issue，而不是在 pydantic-ai 上。大多数 capabilities 都属于 harness，区别请参见[哪些内容放在哪里？](harness/overview.md#what-goes-where)。

## 发布 capability 包 {#publishing-capability-packages}

要让 capability 可安装，并可在 [agent specs](agent-spec.md) 中使用：

1. **实现 [`get_serialization_name()`][pydantic_ai.capabilities.AbstractCapability.get_serialization_name]**：默认使用类名。返回 `None` 可选择不支持 spec。

2. **实现 [`from_spec()`][pydantic_ai.capabilities.AbstractCapability.from_spec]**：默认行为是 `cls(*args, **kwargs)`。如果构造函数接受不可序列化类型，请覆盖它。

3. **包命名**：使用 `pydantic-ai-` 前缀（例如 `pydantic-ai-guardrails`），便于用户找到你的包。

4. **注册**：用户通过 [`Agent.from_spec`][pydantic_ai.Agent.from_spec] 或 [`Agent.from_file`][pydantic_ai.Agent.from_file] 的 `custom_capability_types` 传入自定义 capability 类型。

```python {test="skip" lint="skip"}
from pydantic_ai import Agent

from my_package import MyCapability

agent = Agent.from_file('agent.yaml', custom_capability_types=[MyCapability])
```

实现细节请参见 [spec 中的自定义 capabilities](agent-spec.md#custom-capabilities-in-specs)。

## Pydantic AI Harness

[**Pydantic AI Harness**](harness/overview.md) 是 Pydantic AI 的官方 capability 库：memory、guardrails 和 context management 等独立 capabilities 位于这里，而不是 core 中。完整拆分请参见[哪些内容放在哪里？](harness/overview.md#what-goes-where)，也可以直接查看 [capability matrix](https://github.com/pydantic/pydantic-ai-harness#capability-matrix)。

## 第三方生态 {#third-party-ecosystem}

### Capabilities

[Capabilities](capabilities.md) 是需要把工具与 hooks、instructions 或模型设置打包在一起的包的推荐扩展机制。社区包请参见[第三方 capabilities](capabilities.md#third-party-capabilities)。

### Toolsets

许多第三方扩展以 [toolsets](toolsets.md) 形式提供；它们也可以包装成 [capabilities](capabilities.md)，以使用 hooks、instructions 和模型设置。完整列表请参见[第三方 toolsets](toolsets.md#third-party-toolsets)。

## 其他扩展点 {#other-extension-points}

### 自定义 toolsets {#custom-toolsets}

对于专门的工具执行需求（自定义传输、工具过滤、执行包装），请实现 [`AbstractToolset`][pydantic_ai.toolsets.AbstractToolset]，或继承 [`WrapperToolset`][pydantic_ai.toolsets.WrapperToolset]：

- [`AbstractToolset`][pydantic_ai.toolsets.AbstractToolset]：完全控制工具定义和执行
- [`WrapperToolset`][pydantic_ai.toolsets.WrapperToolset]：委托给被包装的 toolset，并覆盖特定方法

详情请参见[构建自定义 Toolset](toolsets.md#building-a-custom-toolset)。

!!! tip
    如果你的 toolset 还需要提供 instructions、模型设置或 hooks，请考虑改为构建[自定义 capability](capabilities.md#building-custom-capabilities)。

### 自定义模型 {#custom-models}

要连接 Pydantic AI 尚未支持的模型提供商，请实现 [`Model`][pydantic_ai.models.Model]：

- [`Model`][pydantic_ai.models.Model]：模型实现的基础接口
- [`WrapperModel`][pydantic_ai.models.wrapper.WrapperModel]：委托给被包装的模型，适合添加 instrumentation 或转换

详情请参见[自定义模型](models/overview.md#custom-models)。

### 自定义智能体 {#custom-agents}

对于自定义智能体行为，请继承 [`AbstractAgent`][pydantic_ai.agent.AbstractAgent] 或 [`WrapperAgent`][pydantic_ai.agent.WrapperAgent]：

- [`AbstractAgent`][pydantic_ai.agent.AbstractAgent]：智能体实现的基础接口，提供 `run`、`run_sync` 和 `run_stream`
- [`WrapperAgent`][pydantic_ai.agent.WrapperAgent]：委托给被包装的智能体，适合添加前/后处理或上下文管理
