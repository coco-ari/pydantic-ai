# profiles/ 指南

Profiles 描述模型族能力事实以及 schema/request 方面的特殊行为。

- 将模型族自身固有的事实放在这里：结构化输出支持/默认值、原生工具支持、thinking 支持、JSON schema 转换、return-schema 支持、prompted-output 模板，以及模型族特殊行为。
- 不要把 provider 客户端/认证行为放在这里；那属于 providers 或模型适配器。
- 优先使用显式能力字段，而不是分散的 `isinstance` 或 provider-name 检查。
- 当某个功能只适用于部分模型时，清晰地建模该支持事实，并在拥有面向用户行为的层中失败或降级。
- 记住 profile 合并和用户覆盖的存在；当允许稀疏 profile 数据时，避免假设一定存在完整的具体 profile 对象。
