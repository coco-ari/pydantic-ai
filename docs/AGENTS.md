<!-- braindump: rules extracted from PR review patterns -->

# docs/ 指南

## 文档

<!-- rule:232 -->
- 使用 anchor fragments（`#section-name`）把所有概念、功能和 API 元素链接到它们的文档/参考页面中的具体章节。这样可以提高可发现性，并通过直接导航到相关文档上下文来减少用户阻力。
<!-- rule:66 -->
- 对 API 元素使用 reference-style links：`[ElementName][module.path.ElementName]`。这可以在 mkdocs 中启用 hover docs 和导航。相比普通反引号，它能提供 tooltip 和 jump-to-definition 等交互式文档功能。
<!-- rule:714 -->
- 从面向用户的文档中省略已弃用功能，只记录当前做法。这样可以防止用户学习过时模式，并减少对推荐路径的困惑。
<!-- rule:82 -->
- 在文档中将项目名写作 `Pydantic AI`（两个词），不要写成 `Pydantic-AI`、`PydanticAI` 或 `pAI`。这样可以保持一致的品牌身份，并避免文档中的混淆。
<!-- rule:359 -->
- 代码示例结构应为：上下文/简介 -> 代码块 -> 注意事项/细节（不要在上下文之前放代码）。这样可以确保读者在看到代码前理解目的和用法，让文档更易学习并减少困惑。
<!-- rule:93 -->
- 除非实现细节会影响用户决策，否则不要在用户文档中展示实现细节；聚焦用户能控制的内容，而不是内部如何工作。这样可以通过分离面向用户的 API 和可能变化的实现，保持文档干净且易维护。
<!-- rule:52 -->
- 使用渐进披露组织文档：概念 -> 能力 -> 示例（先独立示例）-> 配置 -> 边界情况。这样可以帮助读者逐步建立心智模型，降低认知负担，并让功能更易采用。
<!-- rule:152 -->
- 在文档中先展示**推荐做法**，再用明确的关系语言（例如 "In addition to..."、"As an alternative to..."）和具体功能名引入替代方案。这样可以确保用户首先接触最佳实践，避免采用旧模式或次优模式。
<!-- rule:109 -->
- 移除描述功能“按预期工作”的文档内容，只关注集成特定问题、限制或偏差。这样可以通过消除噪音降低认知负担和维护成本，并防止琐碎说明过时。
<!-- rule:67 -->
- 将 provider-specific config/features 保持在 `docs/models/{provider}.md` 和 `docs/api/models/{provider}.md` 中；通用文档保持 provider-agnostic，只包含一个最小示例和链接。这样可以避免重复，保持通用功能文档简洁易维护，并确保用户在一个规范位置找到 provider-specific 细节，而不是散落在多个页面。
<!-- rule:941 -->
- 除非不可避免（外部服务、凭据、非确定性行为），否则避免在代码示例中使用 `test="skip"`；应改用 mocks 或 fixtures。可测试的文档示例能证明代码有效，并防止文档与实际行为漂移。
<!-- rule:727 -->
- 链接到规范来源，而不是复制在其他地方维护的列表或摘要。这样可以防止来源事实变化时文档过时。
<!-- rule:808 -->
- 文档应聚焦用户任务和公共 API，把实现细节留给 docstrings。任务导向的指南能帮助用户更快完成目标，而把高级/内部细节放在 API 参考中，可以避免在存在合理默认值时用复杂性压倒用户。
<!-- rule:301 -->
- 在文档中，将展示参数变体的示例合并到一个代码块并配备注释；只有互斥参数或不同用例才拆分。这样可以减少简单参数替代方案的重复样板，让文档更易扫描。
<!-- rule:58 -->
- 在文档示例中展示真实用例，说明该功能为什么重要。这样可以防止使用玩具场景或调试代码误导用户，避免遮蔽实际价值。精心编写的示例能帮助用户理解何时应用功能，并避免为可用更简单方法解决的问题实现不必要模式。
<!-- rule:54 -->
- 在文档示例中使用 fence-level `{test="skip" lint="skip"}`，不要使用 inline suppressions。这样可以保持代码干净并聚焦读者。文档代码应示范最佳实践；fence-level skip directives 将工具约束与示例本身分离，而 inline `# noqa` 或 `# type: ignore` 会用实现细节污染教学代码。
<!-- rule:151 -->
- 记录重叠功能时，要交叉引用替代方案并解释权衡。这样可以防止用户错过更合适的选项，或在存在多种方法时实现重复功能（例如 `UsageLimits` vs rate-limiting、provider-specific implementations）。
<!-- rule:1112 -->
- 记录所有可配置功能的默认行为和用例，帮助用户判断何时覆盖默认值。如果不知道默认会发生什么以及何时适合替代方案，用户就无法做出知情配置选择。
<!-- rule:135 -->
- 在文档示例中使用实际、当前可用的模型名称。这样可以防止用户因不存在或假想模型而困惑或复制粘贴失败，确保用户无需修改即可运行文档示例。
<!-- rule:508 -->
- 提交前使用 `make docs-serve` 验证所有文档链接。这样可以及早发现损坏的内部/外部链接，防止文档漂移和 broken links 影响用户，尤其是在代码重构之后。
<!-- rule:283 -->
- 使用 MkDocs admonitions（`!!! note`、`!!! warning`）作为 callouts，不要使用 blockquotes（`>`）或 GitHub alerts（`> [!NOTE]`）。这样可以确保在 MkDocs 中一致渲染，并防止 callouts 污染目录。
<!-- rule:618 -->
- 将子主题、示例和配置细节嵌套在父级章节中。这样可以提高可发现性并减少重复上下文。分层组织让文档更易导航和理解，因为相关内容被组合在一起，而不是散落在顶层章节或独立文件中。
<!-- rule:298 -->
- 在 provider feature support tables 中，使用 `Notes` 或 `Provider Support Notes` 列记录差异、限制和特殊值。这样可以保持表结构清晰且约束可发现，把 provider-specific exceptions 集中在一个可扫描位置，而不是散落在配置示例或 inline parentheticals 中。
<!-- rule:634 -->
- 在 provider feature tables 中，使用标准标签（`Full feature support`、`Limited parameter support`），并将不支持的变体移到 `Unsupported` 列，而不是作为 inline exceptions。这样可以确保一致、可扫描的文档结构，让用户快速识别跨 providers 的确切支持边界。
<!-- rule:168 -->
- 记录替代方案时，解释权衡（限制、要求、收益、用例），并在组合使用可能冲突时给出警告。这样可以帮助用户做出知情决策，并避免配置冲突造成的隐蔽 bug。

<!-- /braindump -->
