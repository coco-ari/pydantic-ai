# capabilities/ 指南

Capabilities 是跨切面智能体行为的可组合归属地。

- 当行为会贡献 instructions、settings、tools、native tools、wrappers、lifecycle hooks 或 event/history processing 时，优先使用 capability，而不是新增 `Agent` 构造函数关键字参数。
- 除非 capability 明确在建模提供商原生功能，否则保持 capabilities 与提供商无关；提供商特定事实属于 providers/profiles 或提供商原生工具类。
- 保持组合顺序。如果某个 capability 包装 model/tool/output/event 行为，请检查它如何与 `CombinedCapability` 和相邻 capabilities 交互。
- 对面向用户的 capabilities，更新文档和示例，让用户把该 capability 作为主要 API 发现，而不是把它当作实现细节。
- 在添加不可序列化状态或隐藏的运行时依赖前，检查 durable execution、agent specs 和序列化配置。
