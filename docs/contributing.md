我们欢迎你为 Pydantic AI 做贡献！

## 我们如何工作：简短版 {#how-we-work--the-short-version}

Pydantic AI 由一个小团队维护。我们会根据什么最能惠及最多用户来设定优先级，并按这个顺序处理 issues 和 PRs，而不是按提交时间顺序处理。

- **发现 bug？** 请开 issue，提供清晰描述和最小可复现示例。附上 [Logfire](https://logfire.pydantic.dev/) trace 链接能显著加快我们的调试速度。
- **想要功能或 API 变更？** 请开 issue 描述你要解决的问题。不要从代码开始。
- **想帮助构建某个功能？** 请在 issue 下评论，说明你为什么需要它以及你能带来什么上下文。我们称之为成为 "champion"，下文会详细说明。
- **有修复或代码想分享？** 请先确保 maintainer 已在 issue 上同意方案并分配给你，然后再开 PR。

本页其余部分会解释我们为什么这样工作，以及你可以期待什么。

## 写代码之前 {#before-you-write-code}

对于任何非平凡变更，请在写代码前先与 maintainer 对齐方案。提前对齐的 PR 会比我们第一次看到的 PR 更快合入。

### 小修复 {#trivial-fixes}

错别字、坏链接、小型文档改进、明显的一行修复：直接开 PR 即可，不需要 issue。

### Bug 修复 {#bug-fixes}

如果修复方式可能不止一种，或你不确定它是否真的是 bug，请先开 issue。请包含最小可复现示例，并最好提供展示问题的 [Logfire trace link](https://logfire.pydantic.dev/)。对于范围明确的 bugs，我们可能会在内部生成修复。你能做的最有价值的事，是提交清晰报告，然后验证修复是否适用于你的用例。

### 功能、集成或 API 变更 {#features-integrations-or-api-changes}

写代码前，请先判断这个变更是否真的需要放在 core 中。大多数新的 agent behaviors 应该放在官方 capability 库 [**Pydantic AI Harness**](https://github.com/pydantic/pydantic-ai-harness) 中，而不是这个仓库。Pydantic AI core 用于 agent loop、model providers，以及需要模型特定支持或对 agent 体验很基础的 capabilities。独立 capabilities，例如 guardrails、memory、context management、file system access 等，应该放在 harness 中，以便更快迭代。完整区别请参见[哪些内容放在哪里？](harness/overview.md#what-goes-where)。

**如果你的想法是 capability**，请改在 [pydantic-ai-harness](https://github.com/pydantic/pydantic-ai-harness/issues) 上开 issue。你也可以按 `pydantic-ai-<name>` 约定将 capabilities 作为自己的包发布，见[发布 capability 包](extensibility.md#publishing-capability-packages)。一旦 capability 有真实用户且形态稳定，我们可以讨论 upstream 到 harness 或 core。

如果它确实属于 core：

1. **先搜索。** 如果已有 issue 覆盖你的需求，请在那里评论。如果最接近的 issue 只是相关，请开一个新 issue 并链接它。
2. **描述问题，不只是方案。** 告诉我们你在构建什么、什么阻塞了你、你尝试过什么。这些上下文比代码更重要。
3. **构建前先提出计划。** 在 issue 上发布解决方案形态，或只带一个 `PLAN.md` 开 draft PR。对于较大功能，我们会与贡献者进行简短视频通话来迭代设计；20 分钟通话通常能省下数周异步 review 周期。
4. **等待分配。** maintainer 需要先同意方案并把 issue 分配给你，然后你再开 PR。未分配 PR 可能会被自动关闭。

!!! warning
    未事先对齐就编写大型 feature PR，是贡献停滞或被关闭的最常见原因。

## Champions（倡导者） {#champions}

"champion" 是指需要某个功能、对问题有上下文，并愿意投入时间帮助我们把它做对的人。如果你想 champion 某个功能：

- 在 issue 下评论说明：你在构建什么、为什么需要它，以及你能贡献什么（领域知识、测试、验证）。
- 我们会优先处理有一个或多个带生产用例的 champions 站出来的功能。没有 champion 的功能会留在 backlog 中，直到我们自己将其排上优先级，或有真实上下文的人出现。
- 成为 champion 不等于要写代码。它意味着塑造计划并验证结果。对于重要功能，我们会安排通话一起迭代设计。

功能发布时，champions 会作为 co-authors 得到署名。

## Review 期间可以期待什么 {#what-to-expect-during-review}

### 我们按优先级顺序 review PRs，而不是按提交顺序 {#we-review-prs-in-our-priority-order-not-submission-order}

我们不会自动 triage 每个新 PR。未事先对齐的 issue 对应 PR 不在我们的 review queue 中，无论它写得多好。如果没有 maintainer 在 issue 上同意变更并分配给你，请假设我们还没有看到你的 PR。

即使是我们之前参与讨论过代码的 PR，我们也会把所有贡献代码视为起点，而不是最终产品。我们根据功能对项目的重要性 review 和排序 PR，而不是根据代码投入了多少努力。这不同于传统开源工作方式，我们宁愿坦诚说明，也不愿让 PR 长期没有任何信号。

**如果你想知道 PR 当前状态**，最好的做法是在 [Pydantic Slack](https://logfire.pydantic.dev/docs/join-slack/) 的 `#pydantic-ai` 频道 ping 我们。

### 我们可能重写或取代你的代码 {#we-may-rewrite-or-supersede-your-code}

我们将贡献代码视为说明性材料：它是展示变更形态并证明方案可行的起点，而不是我们最终合并的形式。对于非平凡变更，你能给我们的最有用内容是计划加可运行示例，而不是打磨好的、可直接合并的实现。

对于任何 PR，我们都可能向你的分支推送 commits，打开一个取代它的后续 PR，或从头重写。出于安全原因，我们倾向于重写贡献代码，而不是原样合并。你仍会作为原作者获得署名。

请不要在未事先对齐的 PR 上花精力追求绿色 CI、处理每条自动 review 评论或为 merge conflicts 反复 rebase。如果我们推进该变更，这些打磨会在重写时被丢弃。让方案跑通，然后停下来在 Slack 上 ping 我们。

### 自动 review 是建议，不是门禁 {#automated-review-is-advisory-not-a-gate}

PRs 会由 Devin 和我们自己的工具自动 review。这些 review 是建议性的：

- bot approval 不表示你的 PR 可以合并。只有人类 maintainer 的 review 才算数。
- bot finding 不表示你必须按它行动。如果你不同意，请说明。
- 如果自动 review 在你的 PR 上产生噪声，请告诉我们。我们会用这些反馈重新调校工具。

### 优先级 {#priority}

我们收到的贡献远多于能 review 的数量，因此会专注于影响最大的地方。我们无法承诺处理每个 PR，即使是好的 PR；相比让你的工作无限期没有信号地挂着，我们宁愿提前说明。

我们如何权衡优先级：

- **用户需求**：更多用户需要的功能优先。有生产用例 champion 支持的功能，优先级高于 speculative additions。
- **Provider 重要性**：影响 frontier providers（Anthropic、OpenAI、Google）或我们知道被大量使用的 providers 的工作优先。小众 provider 的 model integration 会等待；Anthropic 的修复不会。
- **Roadmap 对齐**：与当前重点方向一致的功能优先。目前包括 capabilities/hooks API、provider-adaptive tools，以及 [Pydantic AI Harness](https://github.com/pydantic/pydantic-ai-harness) capability library。
- **Capabilities 优先于 core**：可以作为 [capability](capabilities.md) 存在的功能应该进入 [Pydantic AI Harness](https://github.com/pydantic/pydantic-ai-harness) 或作为你自己的包发布，这通常是最快路径。一旦它有 traction，再回来讨论 upstream。

## 如果你的 PR 或 issue 没有动静 {#if-your-pr-or-issue-has-gone-quiet}

1. 带上链接，在 [Pydantic Slack](https://logfire.pydantic.dev/docs/join-slack/) 的 `#pydantic-ai` 频道 ping 我们。
2. 说明你需要什么："Can you take a look?"、"I'm blocked - is this on your radar?" 或 "Should I close this?" 都可以。
3. 如果你已经等了几周仍没有任何人类回应，请明确指出。这是我们流程上的失败，我们想知道。

## 安装和设置 {#installation-and-setup}

克隆你的 fork 并进入仓库目录：

```bash
git clone git@github.com:<your username>/pydantic-ai.git
cd pydantic-ai
```

安装 `uv`（0.4.30 或更高版本）和 `pre-commit`：

- [`uv` install docs](https://docs.astral.sh/uv/getting-started/installation/)
- [`pre-commit` install docs](https://pre-commit.com/#install)

要安装 `pre-commit`，可以运行以下命令：

```bash
uv tool install pre-commit
```

安装 `pydantic-ai`、所有依赖和 pre-commit hooks：

```bash
make install
```

## 运行测试等命令 {#running-tests-etc}

我们使用 `make` 管理大多数你需要运行的命令。

要查看可用命令详情，请运行：

```bash
make help
```

要运行代码格式化、linting、静态类型检查，以及带 coverage report 生成的测试，请运行：

```bash
make
```

## 文档变更 {#documentation-changes}

要在本地运行文档页面，请运行：

```bash
uv run mkdocs serve
```

## 向 Pydantic AI 添加新模型的规则 {#new-model-rules}

为了避免给 Pydantic AI 维护者带来过多工作量，我们无法接受所有模型贡献，因此制定了以下规则，说明何时会接受新模型、何时不会。希望这能减少失望和无效工作的可能性。

- 要添加带额外依赖的新模型，该依赖需要在 PyPI 上连续 3 个月或更久保持每月下载量超过 50 万。
- 要添加内部使用另一个模型逻辑且没有额外依赖的新模型，该模型所属 GitHub org 总星数需要超过 2 万。
- 对于任何只是自定义 URL 和 API key 的其他模型，我们乐意添加一段描述，包含链接和要使用的 URL 说明。
- 对于任何需要更多逻辑的其他模型，我们推荐你发布自己的 Python 包 `pydantic-ai-xxx`，它依赖 [`pydantic-ai-slim`](install.md#slim-install)，并实现一个继承自我们 [`Model`][pydantic_ai.models.Model] ABC 的模型。

如果你不确定是否该添加某个模型，请[创建 issue](https://github.com/pydantic/pydantic-ai/issues)。
