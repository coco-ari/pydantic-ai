## UI 适配器中的向后兼容性（尤其是 AG-UI）

自 [3971](https://github.com/pydantic/pydantic-ai/pull/3971#discussion_r3011028336) 起，我们决定引入坚持较低（现有）版本要求的策略。简而言之，这意味着：

- 不允许提升版本要求
- 新功能应通过版本检查（包括 import）进行门控
- 较旧版本遇到新功能时不应报错，而是跳过它
