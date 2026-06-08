# 使用 FastAPI 的聊天应用

一个使用 FastAPI 构建的简单聊天应用示例。

演示内容：

* [复用聊天历史](../message-history.md)
* [序列化消息](../message-history.md#accessing-messages-from-results)
* [流式响应](../output.md#streamed-results)

此示例展示如何在请求之间存储聊天历史，并用它为模型的新响应提供上下文。

这里的大部分复杂逻辑位于 `chat_app.py` 和 `chat_app.ts` 之间：前者将响应流式传输到浏览器，
后者在浏览器中渲染消息。

## 运行示例

在[安装依赖并设置环境变量](./setup.md#usage)后运行：

```bash
python/uv-run -m pydantic_ai_examples.chat_app
```

然后在 [localhost:8000](http://localhost:8000) 打开应用。

![示例对话](../img/chat-app-example.png)

## 示例代码

运行聊天应用的 Python 代码：

```snippet {path="/examples/pydantic_ai_examples/chat_app.py"}```

用于渲染应用的简单 HTML 页面：

```snippet {path="/examples/pydantic_ai_examples/chat_app.html"}```

用于处理消息渲染的 TypeScript。为保持示例简单（也冒着冒犯前端开发者的风险），TypeScript 代码会作为纯文本传给浏览器，并在浏览器中转译。

```snippet {path="/examples/pydantic_ai_examples/chat_app.ts"}```
