# durable_exec/ 指南

Durable execution 集成是一等兼容性目标。

- 将 Temporal、DBOS、Prefect、Restate 和类似引擎视为核心智能体语义的兼容性检查，而不是外围适配器。
- 在 durable 边界之间保留 run context、dependencies、message history、retries、model/profile selection 和 toolset lifecycle。
- 避免隐藏的顺序假设、不可序列化状态和仅运行时闭包，除非 durable wrapper 明确拥有它们。
- 相比特定引擎的逃生口，优先使用通用 capabilities/toolsets/models 扩展点。
- 修改 graph/tool/output/streaming/MCP 行为时，检查 durable wrappers 是否需要匹配更新，并在外部运行时行为重要时添加 workflow 级测试。
