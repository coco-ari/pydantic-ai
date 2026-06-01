## 版本政策

我们不会在 V1 的 minor releases 中有意引入破坏性变更。V2 最早会在 2026 年 4 月发布，也就是 2025 年 9 月发布 V1 之后至少 6 个月。

一旦发布 V2，我们会继续为 V1 提供至少 6 个月的安全修复，让你有时间升级应用。

标记为 deprecated 的功能在 V2 之前不会被移除。

当然，一些看似安全的变更和 bug 修复不可避免地会破坏某些用户的代码 &mdash; 这里按惯例附上 [xkcd](https://xkcd.com/1172/)。

以下变更**不会**被视为破坏性变更，并且可能出现在 minor releases 中：

* Bug 修复可能导致现有代码中断，前提是这些代码依赖了未文档化的功能/结构/假设。
* 在现有 message（part）和 event 类型上添加新的 [message parts][pydantic_ai.messages]、[stream events][pydantic_ai.messages.AgentStreamEvent] 或可选字段（包括带默认值的字段）。消费 message parts 或 event streams 时应始终防御式编码，并使用 [`ModelMessagesTypeAdapter`][pydantic_ai.messages.ModelMessagesTypeAdapter] 对 message histories 进行序列化/反序列化。
* 更改 OpenTelemetry span attributes。由于不同的[可观测性平台](logfire.md#using-opentelemetry)支持不同版本的 [OpenTelemetry Semantic Conventions for Generative AI systems](https://opentelemetry.io/docs/specs/semconv/gen-ai/)，Pydantic AI 允许你配置[插桩版本](logfire.md#configuring-data-format)，但默认版本可能会在 minor release 中变化。随着我们在 [Pydantic Logfire](https://logfire.pydantic.dev/docs/guides/web-ui/evals/) 中迭代 Evals 支持，[Pydantic Evals](evals.md) 的 span attributes 也可能变化。
* 更改 `__repr__` 的行为，即使是公共类也一样。

在所有情况下，我们都会尽量减少 churn，并且只在提升 Pydantic AI 用户质量体验有充分理由时才这样做。

## Beta 功能

在 Pydantic，我们喜欢快速推进和创新！为此，minor releases 可能会引入 beta 功能（通过 `beta` 模块标识），这些功能仍在积极开发中。在 beta 阶段，功能的 API 和行为可能不稳定，而且对该功能做出的变更很可能不向后兼容。我们目标是在初始发布后的几个月内，在用户有机会提供反馈并在生产环境测试之后，将 beta 功能移出 beta。

## Python 版本支持

当满足以下条件时，Pydantic 会停止支持某个 Python 版本：

* 该 Python 版本已经到达[预期生命周期结束时间](https://devguide.python.org/versions/)。
* 最近 minor release 的下载中，使用该版本的比例低于 5%。
