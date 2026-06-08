# 升级指南 {#upgrade-guide}

2025 年 9 月，Pydantic AI 达到 V1，这意味着我们承诺 API 稳定性：在 V2 之前不会引入破坏你代码的变更。更多信息请查看我们的[版本政策](version-policy.md)。

## 破坏性变更 {#breaking-changes}

下面按版本列出经过筛选的破坏性变更，帮助你升级 Pydantic AI。

### v1.0.1 (2025-09-05)

以下破坏性变更意外遗漏在 v1.0.0 之外：

- 见 [#2808](https://github.com/pydantic/pydantic-ai/pull/2808) - 出于安全原因，从 `pydantic_evals` 中移除 `Python` evaluator

### v1.0.0 (2025-09-04)

- 见 [#2725](https://github.com/pydantic/pydantic-ai/pull/2725) - 放弃支持 Python 3.9
- 见 [#2738](https://github.com/pydantic/pydantic-ai/pull/2738) - 让许多 dataclasses 要求使用关键字参数
- 见 [#2715](https://github.com/pydantic/pydantic-ai/pull/2715) - 从 `pydantic_evals` spans 中移除 `cases` 和 `averages` 属性
- 见 [#2798](https://github.com/pydantic/pydantic-ai/pull/2798) - 将 `ModelRequest.parts` 和 `ModelResponse.parts` 类型从 `list` 改为 `Sequence`
- 见 [#2726](https://github.com/pydantic/pydantic-ai/pull/2726) - 将 `InstrumentationSettings` 默认版本设为 2
- 见 [#2717](https://github.com/pydantic/pydantic-ai/pull/2717) - 当向 `AsyncTenacityTransport` 或 `TenacityTransport` 传入 `AsyncRetrying` 或 `Retrying` 对象而不是 `RetryConfig` 时，不再报错

### v0.x.x

V1 之前，minor versions 用于引入破坏性变更：

**v0.8.0 (2025-08-26)**

见 [#2689](https://github.com/pydantic/pydantic-ai/pull/2689) - `AgentStreamEvent` 扩展为 `ModelResponseStreamEvent` 和 `HandleResponseEvent` 的 union，简化了 `event_stream_handler` 函数签名。接受 `AgentStreamEvent | HandleResponseEvent` 的现有代码会继续工作。

**v0.7.6 (2025-08-26)**

以下破坏性变更被意外发布在 patch version 中，而不是 minor version 中：

见 [#2670](https://github.com/pydantic/pydantic-ai/pull/2670) - `TenacityTransport` 和 `AsyncTenacityTransport` 现在要求使用 `pydantic_ai.retries.RetryConfig`（它只是一个包含传给 `tenacity.retry` 的 kwargs 的 `TypedDict`），而不是 `tenacity.Retrying` 或 `tenacity.AsyncRetrying`。

**v0.7.0 (2025-08-12)**

见 [#2458](https://github.com/pydantic/pydantic-ai/pull/2458) - `pydantic_ai.models.StreamedResponse` 现在除了现有的 `PartStartEvent` 和 `PartDeltaEvent`，还会 yield `FinalResultEvent`。如果你使用 `pydantic_ai.direct.model_request_stream` 或 `pydantic_ai.direct.model_request_stream_sync`，可能需要更新代码以适配这一点。

见 [#2458](https://github.com/pydantic/pydantic-ai/pull/2458) - `pydantic_ai.models.Model.request_stream` 现在会接收 `run_context` 参数。如果你实现了自定义 `Model` 子类，需要适配这一点。

见 [#2458](https://github.com/pydantic/pydantic-ai/pull/2458) - `pydantic_ai.models.StreamedResponse` 现在要求提供 `model_request_parameters` 字段和构造参数。如果你实现了自定义 `Model` 子类并实现了 `request_stream`，需要适配这一点。

**v0.6.0 (2025-08-06)**

此版本旨在清理一些旧的弃用代码，让我们离 V1 更近一步。

见 [#2440](https://github.com/pydantic/pydantic-ai/pull/2440) - 从 `Graph` 类中移除了 `next` 方法。请改用 `async with graph.iter(...) as run:  run.next()`。

见 [#2441](https://github.com/pydantic/pydantic-ai/pull/2441) - 从 `Agent` 类中移除了 `result_type`、`result_tool_name` 和 `result_tool_description` 参数。请改用 `output_type`。

见 [#2441](https://github.com/pydantic/pydantic-ai/pull/2441) - 同样从 `Agent` 类中移除了 `result_retries` 参数。请改用 `output_retries`。

见 [#2443](https://github.com/pydantic/pydantic-ai/pull/2443) - 从 `FinalResult` 类中移除了 `data` 属性。请改用 `output`。

见 [#2445](https://github.com/pydantic/pydantic-ai/pull/2445) - 从 `StreamedRunResult` 类中移除了 `get_data` 和 `validate_structured_result` 方法。请改用 `get_output` 和 `validate_structured_output`。

见 [#2446](https://github.com/pydantic/pydantic-ai/pull/2446) - `format_as_xml` 函数移动到了 `pydantic_ai.format_as_xml` 模块。请改为通过 `from pydantic_ai import format_as_xml` 导入它。

见 [#2451](https://github.com/pydantic/pydantic-ai/pull/2451) - 移除了弃用的 `Agent.result_validator` 方法、`Agent.last_run_messages` 属性、`AgentRunResult.data` 属性，以及 result classes 中的 `result_tool_return_content` 参数。

**v0.5.0 (2025-08-04)**

见 [#2388](https://github.com/pydantic/pydantic-ai/pull/2388) - `EvaluationResult` 的 `source` 字段现在是 `EvaluatorSpec` 类型，而不是实际 source `Evaluator` 实例，以帮助序列化/反序列化。

见 [#2163](https://github.com/pydantic/pydantic-ai/pull/2163) - `EvaluationReport.print` 和 `EvaluationReport.console_table` 方法现在要求大多数参数按关键字传入。

**v0.4.0 (2025-07-08)**

见 [#1799](https://github.com/pydantic/pydantic-ai/pull/1799) - Pydantic Evals 的 `EvaluationReport` 和 `ReportCase` 现在是 generic dataclasses，而不是 Pydantic models。如果你之前使用 `model_dump()` 序列化它们，现在需要改用 `EvaluationReportAdapter` 和 `ReportCaseAdapter` type adapters。

见 [#1507](https://github.com/pydantic/pydantic-ai/pull/1507) - `ToolDefinition` 的 `description` 参数现在是可选的，位置参数顺序也因此从 `name, description, parameters_json_schema, ...` 改为 `name, parameters_json_schema, description, ...`。

**v0.3.0 (2025-06-18)**

见 [#1142](https://github.com/pydantic/pydantic-ai/pull/1142) - 增加对 thinking parts 的支持。

我们现在会将 provider-specific text parts 中的 thinking blocks（`"<think>..."</think>"`）转换为 Pydantic AI `ThinkingPart`s。作为此版本的一部分，我们也选择不把 `ThinkingPart`s 发回 provider，目的是为用户节省成本。未来我们计划添加一个设置来自定义此行为。

**v0.2.0 (2025-05-12)**

见 [#1647](https://github.com/pydantic/pydantic-ai/pull/1647) - usage 作为 `ModelResponse` 的一部分是合理的，并且在 "messages"（实际上是一串 requests 和 response）中可能非常有用。此 PR 中：

- 向 `ModelResponse` 添加 `usage`（该字段有 `Usage()` 默认工厂，因此加载没有 usage 的数据也能工作）
- 将 `Model.request` 的返回类型从 `tuple[ModelResponse, Usage]` 改为仅 `ModelResponse`

**v0.1.0 (2025-04-15)**

见 [#1248](https://github.com/pydantic/pydantic-ai/pull/1248) - 许多地方的属性/参数名 `result` 重命名为 `output`。希望所有变更都保留了旧名称对应的弃用属性或参数，因此你应该会看到许多 deprecation warnings。

见 [#1484](https://github.com/pydantic/pydantic-ai/pull/1484) - `format_as_xml` 被移动，并可从包根导入，例如 `from pydantic_ai import format_as_xml`。

## 完整 Changelog {#full-changelog}

<div id="display-changelog">
  完整 changelog 请参见 <a href="https://github.com/pydantic/pydantic-ai/releases">GitHub Releases</a>。
</div>

<script>
  fetch('/changelog.html').then(r => {
    if (r.ok) {
      r.text().then(t => {
        document.getElementById('display-changelog').innerHTML = t;
      });
    }
  });
</script>
