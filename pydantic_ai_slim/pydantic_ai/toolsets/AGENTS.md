# toolsets/ 指南

Toolsets 是可复用的工具集合，包含生命周期、instructions 和执行边界。

- 对过滤、前缀、审批、延迟、metadata 或 schema 变更等跨切面行为，优先使用 wrapper toolsets；避免为了可组合的行为修改每一个具体 toolset。
- 保持 `get_tools`、`get_instructions`、lifecycle 和 `call_tool` 语义一致。如果 wrapper 转发其中之一，请检查它是否也应该转发其他语义。
- 在 wrappers、MCP、deferred execution、message history 和 durable engines 中保持工具身份和稳定命名。
- 当 toolset 或 capability 可以拥有某个功能状态时，不要把该功能特定状态放到 `Agent` 上。
- 尽可能通过公共 agent/toolset 行为进行测试；当行为影响协议形状时，对 message/tool-call history 做快照。
