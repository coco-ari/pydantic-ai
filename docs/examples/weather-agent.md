此示例展示 Pydantic AI 使用多个工具，LLM 需要依次调用这些工具来回答问题。

演示内容：

- [工具](../tools.md)
- [智能体依赖](../dependencies.md)
- [流式文本响应](../output.md#streaming-text)
- 为智能体构建 [Gradio](https://www.gradio.app/) UI

在这个例子中，我们构建的是一个"天气"智能体。用户可以询问多个地点的天气，
智能体会使用 `get_lat_lng` 工具获取这些地点的经纬度，然后使用
`get_weather` 工具获取这些地点的天气。

## 运行示例

要正确运行此示例，你可能需要添加两个额外的 API key。**注意：如果缺少任一 key，代码会回退到虚拟数据，因此它们不是必需的**：

- 来自 [tomorrow.io](https://www.tomorrow.io/weather-api/) 的天气 API key，通过 `WEATHER_API_KEY` 设置
- 来自 [geocode.maps.co](https://geocode.maps.co/) 的地理编码 API key，通过 `GEO_API_KEY` 设置

在[安装依赖并设置环境变量](./setup.md#usage)后运行：

```bash
python/uv-run -m pydantic_ai_examples.weather_agent
```

## 示例代码
```snippet {path="/examples/pydantic_ai_examples/weather_agent.py"}```

## 运行 UI

你可以使用 [Gradio](https://www.gradio.app/) 为智能体构建多轮聊天应用。Gradio 是一个完全用 Python 构建 AI Web 应用的框架。它内置聊天组件和智能体支持，因此整个 UI 可以在单个 Python 文件中实现。

天气智能体的 UI 如下所示：

{{ video('c549d8d8827ded15f326f998e428e6c3', 6) }}


```bash
pip install gradio>=6.7.0
python/uv-run -m pydantic_ai_examples.weather_agent_gradio
```

## UI 代码
```snippet {path="/examples/pydantic_ai_examples/weather_agent_gradio.py"}```
