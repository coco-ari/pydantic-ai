# 编码智能体 Skills

如果你正在用编码智能体构建 Pydantic AI 应用，可以从 [`pydantic/skills`](https://github.com/pydantic/skills) 仓库安装 Pydantic AI skill，为智能体提供最新的框架知识。

[Agent skills](https://agentskills.io) 是指令和参考材料包，编码智能体会按需加载它们。安装此 skill 后，编码智能体可以访问 Pydantic AI 模式、架构指南，以及涵盖[工具](tools.md)、[能力](capabilities.md)、[结构化输出](output.md)、[流式传输](agent.md#streaming-events-and-final-output)、[测试](testing.md)、[多智能体委托](multi-agent-applications.md)、[钩子](hooks.md)和 [agent specs](agent-spec.md) 的常见任务参考。

!!! note
    如果你想为自己的 Pydantic AI 智能体构建 agent skills，请参见 Capabilities 页面中第三方能力部分的 [Agent Skills](capabilities.md#agent-skills) 条目。

## 安装

### Claude Code

从 Anthropic marketplace 安装[官方 Pydantic AI plugin](https://claude.com/plugins/pydantic-ai)，它默认可用：

```bash
claude plugin install pydantic-ai@claude-plugins-official
```

作为替代方案，你也可以从 [`pydantic/skills`](https://github.com/pydantic/skills) marketplace 安装；该 marketplace 将 Pydantic AI skill 与其他由 Pydantic 维护的 skills 打包在一起：

```bash
claude plugin marketplace add pydantic/skills
claude plugin install ai@pydantic-skills
```

### 跨智能体（agentskills.io）

使用 [skills CLI](https://github.com/vercel-labs/skills) 安装 Pydantic AI skill：

```bash
npx skills add pydantic/skills
```

这可通过 [agentskills.io](https://agentskills.io) 标准用于 30 多种智能体，包括 Claude Code、Codex、Cursor 和 Gemini CLI。

### Library Skills 库技能 {#library-skills}

Pydantic AI 也会将其 skill 随包一起发布，因此你可以通过 [library-skills.io](https://library-skills.io) 直接从项目依赖中安装：

```bash
uvx library-skills --all
```

必须使用 `--all` 标志，因为该 skill 打包在 `pydantic-ai-slim` 中，而 `pydantic-ai` 元包只是传递依赖它。没有此标志时，`library-skills` 只扫描直接依赖，无法发现该 skill。

添加 `--claude` 可在默认 `.agents/skills/` 目录之外，同时安装到 `.claude/skills/`，因为 Claude Code 不会读取 `.agents/`。

## 另请参见

- [`pydantic/skills`](https://github.com/pydantic/skills)：源码仓库
- [agentskills.io](https://agentskills.io)：agent skills 的开放标准
- [library-skills.io](https://library-skills.io)：安装随项目依赖打包的 agent skills
