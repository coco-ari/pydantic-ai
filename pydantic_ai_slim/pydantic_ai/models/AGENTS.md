<!-- braindump: rules extracted from PR review patterns -->

# pydantic_ai_slim/pydantic_ai/models/ 指南

## API 设计

<!-- rule:912 -->
- 在 docstrings 中记录不支持的 model settings，并在运行时静默忽略。这样可以在模型能力不同时避免破坏客户端代码。不同模型提供商支持不同功能；当某个 setting 不受支持时大声失败会破坏跨模型代码可移植性，而有清晰文档的静默降级能让用户做出知情选择。
<!-- rule:81 -->
- 对 `request()` 和 `request_stream()` 应用相同的响应处理。如果 `request()` 调用 `_process_response()`，`request_stream()` 必须对每个 chunk 应用它。这样可以确保 streaming 和 non-streaming 代码路径以一致行为支持相同 message types（`ToolCallPart`、`NativeToolCallPart`、`TextPart` 等），避免功能在一种模式可用、另一种模式失败。
<!-- rule:598 -->
- 通过 `ModelResponse.provider_details` 或 `TextPart.provider_details` 暴露 provider-specific data。这样可以避免 API 膨胀并保持一致的 provider 集成模式。在让 providers 暴露 logprobs、safety filters、content filtering 和 usage metrics 的同时，保持核心响应接口简洁且不破坏各集成之间的一致性。
<!-- rule:26 -->
- 在 `pydantic_ai/models/` 中实现 workaround 前，要通过测试验证 provider limitations。将校验交给运行时 API 响应，而不是预先做客户端侧检查。这样可以避免基于过时假设添加不必要 workaround 而降低功能性，并让底层 API 返回关于实际不兼容性的清晰错误消息。
<!-- rule:478 -->
- Token counting 必须镜像实际 request 参数（`tools`、`system_prompt`、configs）并使用相同的 message formatting。这样可以确保 token count 估算匹配实际 API 使用情况，避免计费意外和 quota 错误。

## 错误处理

<!-- rule:562 -->
- 对不支持的模型功能/content/parameters 抛出显式错误，绝不要静默跳过或降级。这样可以防止静默失败，并让用户在运行时发现能力限制，而不是得到意外行为。
<!-- rule:65 -->
- 在 model adapters 中，对 message part/content types 使用穷尽式模式匹配；对于不支持的类型，抛出显式错误，而不是过滤或断言。这样可以防止 message mapping 期间静默数据丢失，并在模型 API 不支持某些内容类型（例如 `FileContent`）时提供清晰反馈，让集成失败可调试而不是难以理解。
<!-- rule:433 -->
- 对可恢复的 API 失败（content filters、empty content），返回 `parts=[]` 为空但 metadata（`finish_reason`、`timestamp`、`provider_response_id`）已填充的 `ModelResponse`。这样可以优雅降级而不是触发级联错误。系统可以通过保留 response metadata 进行可观测性，同时表示没有可用内容，从而优雅处理 provider-level failures，避免 model adapters 中不必要的异常传播。

## 类型系统

<!-- rule:73 -->
- 使用 typed settings classes（例如 `OpenAISettings`、`AnthropicSettings`）以及带 provider 前缀的字段，而不是 `extra_body` 或 dict literals。这样可以为 provider-specific config 启用类型检查和自动补全，防止拼写错误或无效值导致运行时错误。
<!-- rule:972 -->
- 定义 Pydantic models 来校验 API responses。这样可以避免 `.get()` 的脆弱性，并及早捕获 schema 变化，防止字段缺失/格式错误导致运行时错误，同时在解析外部 API 数据时提供类型安全。

## 通用

<!-- rule:9 -->
- 将 provider-specific code 放在 `models/{provider}.py` 中，而不是 shared modules 中。即使某些 providers 的函数很简单，也要在所有 providers 中一致添加函数。这样可以保持清晰的架构边界，避免共享兼容层累积 provider-specific logic 而难以维护。

<!-- /braindump -->
