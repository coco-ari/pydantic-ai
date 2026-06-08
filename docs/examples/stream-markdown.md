此示例展示如何从智能体流式传输 Markdown，并使用 [`rich`](https://github.com/Textualize/rich) 库在终端中高亮输出。

如果设置了所需的环境变量，它会分别使用 OpenAI 和 Google Gemini 模型运行此示例。

演示内容：

* [流式文本响应](../output.md#streaming-text)

## 运行示例

在[安装依赖并设置环境变量](./setup.md#usage)后运行：

```bash
python/uv-run -m pydantic_ai_examples.stream_markdown
```

## 示例代码

```snippet {path="/examples/pydantic_ai_examples/stream_markdown.py"}```
