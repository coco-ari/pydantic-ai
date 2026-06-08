关于鲸鱼的信息，展示流式结构化响应校验的示例。

演示内容：

* [流式结构化输出](../output.md#streaming-structured-output)

此脚本会流式传输关于鲸鱼的结构化响应，校验数据，
并在接收数据时使用 [`rich`](https://github.com/Textualize/rich) 将其显示为动态表格。

## 运行示例

在[安装依赖并设置环境变量](./setup.md#usage)后运行：

```bash
python/uv-run -m pydantic_ai_examples.stream_whales
```

应输出类似下面的内容：

{{ video('53dd5e7664c20ae90ed90ae42f606bf3', 25) }}

## 示例代码

```snippet {path="/examples/pydantic_ai_examples/stream_whales.py"}```
