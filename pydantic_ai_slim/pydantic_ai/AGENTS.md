<!-- braindump: rules extracted from PR review patterns -->

# pydantic_ai_slim/pydantic_ai/ 指南

对这个包进行非平凡变更时，还要阅读 [Pydantic AI Slim 架构](../../agent_docs/pydantic-ai-slim.md)。

## API 设计

<!-- rule:587 -->
- 将 capability flags 添加到 model profile 类中，而不是使用内联 `isinstance()` 检查。这样可以避免分散的功能检测逻辑。将功能支持集中为 profile 类中的布尔标志（例如 `bedrock_supports_prompt_caching`），能让 capability detection 更易维护，并避免在各个使用点重复 provider/model 类型检查。
<!-- rule:716 -->
- 在 `Provider.model_profile()` 中配置 provider-specific API 功能，而不是在 model profile 函数中配置。Model profiles 应只包含模型固有特征。这样可以将 provider-agnostic 模型特征与 provider-specific API 行为分离，让模型能在不同 providers 上保持一致工作。
<!-- rule:264 -->
- 将 provider-specific metadata 存储在结构化的 `provider_details` 或 `provider_metadata` 字段中，不要放在 `id`、`content` 或 `args` 中。这样可以避免语义字段重载，并在保持主字段跨 providers 归一化的同时，实现一致的 provider 行为解释。
<!-- rule:17 -->
- 在 `_otel_*.py` 模块中，只实现规范定义的功能，不要加入来自内部概念或其他标准的自定义扩展。这样可以防止规范漂移，并确保与期望标准兼容遥测数据的外部工具兼容。
<!-- rule:266 -->
- 将 provider metadata（`provider_details`、`provider_name`、`id`、`signature`）存储在专用的 `provider_metadata` 字段中，不要编码进字符串字段。这样可以防止在存储、UI exchange 和 provider round-trip 的 JSON 序列化/反序列化周期中丢失数据；结构化 metadata 能保留类型信息，而编码字符串会丢失。
<!-- rule:987 -->
- 对跨切面的 toolset 行为扩展 `WrapperToolset`，不要修改基类或单个 toolset 实现。可组合 wrappers（例如 `ApprovalRequiredToolset`、`DeferredLoadingToolset`）可以将功能应用到任何 toolset，而不会产生耦合或重复。

## 类型系统

<!-- rule:185 -->
- 对 typed unions 的穷尽式 `if`/`elif` 链，使用 `else: assert_never(value)` 结尾。当 union 扩展时，这能在类型检查阶段捕获未处理的 union 变体，避免缺失分支导致运行时错误。
<!-- rule:60 -->
- 避免 `Any` 类型注解。使用 `Union`、`Protocol`、`TypeVar` 或 schema-derived 类型来提高精度。精确类型能在类型检查阶段发现 bug，并改善 IDE 自动补全；当外部约束导致无法避免 `Any` 时，请在 docstring 中记录预期结构。
<!-- rule:238 -->
- 当结构已知时，使用 `TypedDict` 或 dataclass，而不是 `dict[str, Any]`。这样可以启用静态类型检查、消除 `cast()` 调用、提供运行时校验，并自文档化预期结构。

## 代码风格

<!-- rule:552 -->
- 使用 helpers、delegation 或 type overloads 合并具有重复逻辑的方法。这样可以降低维护负担，并防止同一控制流的不同实现产生分歧导致 bug。
<!-- rule:41 -->
- 在 dataclasses 中将必需字段放在可选字段之前。Python 要求非默认参数在默认参数之前，这可以避免语法错误，因为 Python 的 dataclass 实现会强制无默认值字段必须位于有默认值字段之前。

## 通用

<!-- rule:40 -->
- 对 optional/config 参数使用 keyword-only params（在前 1-2 个位置参数后放置 `*`）。这样可以在添加参数时避免破坏性变更，并消除多个可选参数函数中的位置参数混淆。
<!-- rule:71 -->
- 在 `ModelSettings` 子类和 profiles 中，用 `{provider}_` 前缀标记 provider-specific 字段。这样可以避免混淆哪些 provider 支持哪些参数。清晰的 provider 命名空间可以防止用户误以为某个字段跨 providers 生效，从而减少 API 误用。
<!-- rule:894 -->
- 将捕获同一异常的 `try`/`except` 块合并为一个块，以减少重复并简化控制流。当多个操作抛出同一异常类型并具有类似处理逻辑时，合并 try blocks 可以避免代码重复，并让错误处理更易维护和一致更新。


<!-- /braindump -->
