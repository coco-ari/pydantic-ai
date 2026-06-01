# providers/ 指南

Providers 负责 API 客户端、认证、base URL、HTTP 生命周期，以及提供商级别的模型/profile 推断。

- 将提供商 API 行为放在 providers 或具体模型适配器中，不要放在 graph/tool/output 代码中。
- 将 provider/model profiles 作为随提供商或模型族变化的能力事实的事实来源。
- 保持提供商特定设置有类型且带提供商前缀，让用户能发现每个字段属于哪个 API。
- 在添加兼容性分支前，根据上游文档或 SDK 类型验证提供商事实。
- 在保留结构化 metadata/provider-details 字段中的提供商特定元数据时，保持归一化的核心行为。
