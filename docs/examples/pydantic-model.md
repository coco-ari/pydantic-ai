# Pydantic 模型

一个简单示例，展示如何使用 Pydantic AI 根据文本输入构造 Pydantic 模型。

演示内容：

- [结构化 `output_type`](../output.md#structured-output)

## 运行示例

在[安装依赖并设置环境变量](./setup.md#usage)后运行：

```bash
python/uv-run -m pydantic_ai_examples.pydantic_model
```

此示例默认使用 `openai:gpt-5`，但也能很好地配合其他模型使用。例如，你可以用 Gemini 运行：

```bash
PYDANTIC_AI_MODEL=gemini-3-pro-preview python/uv-run -m pydantic_ai_examples.pydantic_model
```

（或使用 `PYDANTIC_AI_MODEL=gemini-3-flash-preview ...`）

## 示例代码

```snippet {path="/examples/pydantic_ai_examples/pydantic_model.py"}```
