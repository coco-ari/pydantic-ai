# native_tools/ 指南

## 添加新的原生工具

- 每个原生工具都必须有一个对应的 capability，并且该 capability 应扩展 `capabilities/` 中的 `NativeOrLocalTool`。Capabilities 是用户在 agents 上启用工具功能的主要面向用户 API；没有 capability 的原生工具对使用 capabilities 列表的用户来说不可发现
  - 本地 fallback（例如 `WebSearch`、`WebFetch`）：在没有原生支持的提供商上，capability 会 fallback 到 function tool
  - Subagent fallback（例如 `ImageGeneration`、`XSearch`）：capability 会通过 `fallback_model` 委托给运行另一个提供商模型的 subagent
- 当提供商 API 有控制是否包含原始工具输出的 request-level 参数时（例如 xAI `include`、OpenAI `include`），请把工具特定的参数作为工具类字段暴露，而不是只放在 model settings 中。配置 `XSearchTool(...)` 的用户应该在那里发现所有相关选项；model settings 仍可作为向后兼容的替代方式
- Provider support 必须记录在三个位置：工具类 docstring 的 `Supported by` 列表、`docs/native-tools.md` provider 表，以及 provider-specific 语义的字段级 docstring
- 当工具字段直接映射到提供商 API 字段名时，优先使用该名称。用户可能会同时打开提供商文档和 pydantic-ai 文档
- 在 `__post_init__` 中校验互斥性和限制，并用清晰消息快速失败（例如 `'Cannot specify both allowed_x_handles and excluded_x_handles'`）
- pydantic-ai 中的原生工具名称必须能通过提供商 API 往返。如果 API 使用不同的函数名（例如 xAI 发送 `x_keyword_search` 而不是 `x_search`），在重放历史时要保留原始名称
