# Pydantic AI Harness 能力库 {#pydantic-ai-harness}

[**Pydantic AI Harness**](https://github.com/pydantic/pydantic-ai-harness) 是 Pydantic AI 的官方[能力](../capabilities.md)库，也就是智能体的"电池包"。

```bash
uv add pydantic-ai-harness
```

## 哪些内容放在哪里？ {#what-goes-where}

Pydantic AI core 提供智能体循环、模型提供商、capabilities/hooks 抽象，以及两类能力：

- **需要模型或框架支持的能力**，即由提供商原生工具（如[图像生成](../capabilities.md#provider-adaptive-tools)）、提供商特定 API（如通过 OpenAI 或 Anthropic API 做 compaction），或深度智能体图集成支撑的能力。这些能力与模型类代码紧密相关，需要一起发布。
- **构成智能体体验基础的能力**，即几乎每个智能体都会受益的能力，例如[网页搜索](../capabilities.md#provider-adaptive-tools)、[工具搜索](../tools-advanced.md#tool-search)和[思考](../capabilities.md#thinking)。它们更像智能体自身的特质，而不是附加配件。

**Pydantic AI Harness** 则承载其他内容：让特定类别智能体更强大的独立能力，或仍在寻找最终形态的能力。上下文管理、记忆、护栏、文件系统访问、代码执行、多智能体编排，这些都是可按智能体需求选择的构建块。

Harness 也是新能力的*起点*。它作为独立包发布，因此能力可以更快迭代，而无需承担 core 的严格向后兼容要求。当某个能力稳定下来并证明自己具有广泛必要性时，它可以毕业进入 core，[code mode](https://github.com/pydantic/pydantic-ai-harness/tree/main/pydantic_ai_harness/code_mode) 就是一个早期候选。

许多能力都受益于"向上回退"模式：它们通常从适用于所有模型的本地实现开始，然后在可用时获得使用提供商内置 API 的原生支持，并在两者之间自动切换。core 中的[网页搜索](../capabilities.md#provider-adaptive-tools)、[网页获取](../capabilities.md#provider-adaptive-tools)和[图像生成](../capabilities.md#provider-adaptive-tools)已经采用这种方式；skills、code mode 和上下文压缩也会采用同样思路。

## 其中包含什么？

完整的可用能力、计划能力和社区替代方案列表，请参见 harness README 中的 [capability matrix](https://github.com/pydantic/pydantic-ai-harness#capability-matrix)。

## 贡献能力

能力贡献应提交到 [harness 仓库](https://github.com/pydantic/pydantic-ai-harness)，而不是 pydantic-ai。capabilities 抽象为贡献提供了清晰边界，让评审更容易。详情请参见 [Contributing](https://github.com/pydantic/pydantic-ai-harness#contributing)。

## 构建自己的能力

你也可以将能力作为独立包发布。API 请参见[构建自定义能力](../capabilities.md#building-custom-capabilities)，打包指南请参见[发布能力包](../extensibility.md#publishing-capability-packages)。

## 链接

- [GitHub](https://github.com/pydantic/pydantic-ai-harness)
- [PyPI](https://pypi.org/project/pydantic-ai-harness/)
- [能力矩阵](https://github.com/pydantic/pydantic-ai-harness#capability-matrix)
- [版本政策](https://github.com/pydantic/pydantic-ai-harness#version-policy)
- [贡献指南](https://github.com/pydantic/pydantic-ai-harness#contributing)
