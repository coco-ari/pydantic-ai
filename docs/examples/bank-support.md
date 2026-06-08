一个小而完整的示例，展示如何使用 Pydantic AI 为银行构建支持智能体。

演示内容：

- [动态系统提示](../agent.md#system-prompts)
- [结构化 `output_type`](../output.md#structured-output)
- [工具](../tools.md)

## 运行示例

在[安装依赖并设置环境变量](./setup.md#usage)后运行：

```bash
python/uv-run -m pydantic_ai_examples.bank_support
```

（或使用 `PYDANTIC_AI_MODEL=gemini-3-flash-preview ...`）

## 示例代码

```snippet {path="/examples/pydantic_ai_examples/bank_support.py"}```
