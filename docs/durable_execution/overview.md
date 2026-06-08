# 持久化执行

Pydantic AI 允许你构建持久化智能体，在短暂 API 故障、应用错误或重启后保留进度，并以生产级可靠性处理长时间运行、异步以及人在回路中的工作流。持久化智能体完整支持[流式传输](../agent.md#streaming-all-events)和 [MCP](../mcp/client.md)，并额外提供容错能力。

Pydantic AI 官方支持四种持久化执行方案：

- [Temporal](./temporal.md)
- [DBOS](./dbos.md)
- [Prefect](./prefect.md)
- [Restate](./restate.md)

这些集成由 Pydantic 团队和供应商团队共同维护，并且只使用 Pydantic AI 的公共接口，因此也可以作为集成其他持久化系统的参考。
