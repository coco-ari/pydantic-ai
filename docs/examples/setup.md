# 示例

这里包含一些示例，展示如何使用 Pydantic AI 以及它能做什么。

## 使用 {#usage}

这些示例随 `pydantic-ai` 一起发布，因此你可以通过克隆 [pydantic-ai 仓库](https://github.com/pydantic/pydantic-ai)来运行它们，也可以直接用 `pip` 或 `uv` 从 PyPI 安装 `pydantic-ai`。

### 安装所需依赖

无论采用哪种方式，运行某些示例都需要安装额外依赖。你只需安装 `examples` 可选依赖组。

如果你通过 pip/uv 安装了 `pydantic-ai`，可以用下面的命令安装额外依赖：

```bash
pip/uv-add "pydantic-ai[examples]"
```

如果你克隆了仓库，则应改用 `uv sync --extra examples` 安装额外依赖。

### 设置模型环境变量

这些示例需要你为一个或多个 LLM 设置认证。具体方法请参见[模型配置](../models/overview.md)文档。

简而言之，大多数情况下你需要设置以下环境变量之一：

=== "OpenAI"

    ```bash
    export OPENAI_API_KEY=your-api-key
    ```

=== "Google Gemini"

    ```bash
    export GEMINI_API_KEY=your-api-key
    ```

### 运行示例

要运行示例（无论你是安装了 `pydantic_ai`，还是克隆了仓库，都可以这样做），请运行：

```bash
python/uv-run -m pydantic_ai_examples.<example_module_name>
```

例如，运行非常简单的 [`pydantic_model`](./pydantic-model.md) 示例：

```bash
python/uv-run -m pydantic_ai_examples.pydantic_model
```

如果你喜欢单行命令并且正在使用 uv，可以零配置运行一个 pydantic-ai 示例：

```bash
OPENAI_API_KEY='your-api-key' \
  uv run --with "pydantic-ai[examples]" \
  -m pydantic_ai_examples.pydantic_model
```

---

除了直接运行示例，你可能还想编辑它们。可以用下面的命令将示例复制到新目录：

```bash
python/uv-run -m pydantic_ai_examples --copy-to examples/
```
