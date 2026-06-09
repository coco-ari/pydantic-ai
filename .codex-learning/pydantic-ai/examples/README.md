# 学习示例：使用自己的 API 运行 Pydantic AI

这个目录只放你的学习代码，不放正式项目源码。

## 本节要学什么

- 如何用 `OpenAIProvider` 接入 OpenAI 或 OpenAI-compatible API。
- 为什么 API key 不应该写进 `.py` 文件。
- `os.getenv()` 如何从环境变量读取配置。
- `Agent(model, instructions=...)` 如何创建一个最小 agent。

## 方式一：写入本地 `.env`

复制模板：

```powershell
Copy-Item .codex-learning/pydantic-ai/examples/.env.example .codex-learning/pydantic-ai/examples/.env
```

然后编辑 `.codex-learning/pydantic-ai/examples/.env`：

```text
OPENAI_API_KEY=你的-api-key
OPENAI_BASE_URL=https://icoe.pp.ua/v1
PYDANTIC_AI_MODEL=gpt-5.5
```

`.env` 已经被本目录的 `.gitignore` 忽略，不应该提交到 Git。

## 方式二：PowerShell 设置环境变量

如果你使用 OpenAI 官方 API：

```powershell
$env:OPENAI_API_KEY="你的-api-key"
$env:PYDANTIC_AI_MODEL="gpt-5.2"
```

如果你使用 OpenAI-compatible API，还需要设置 `base_url`：

```powershell
$env:OPENAI_API_KEY="你的-api-key"
$env:OPENAI_BASE_URL="https://你的服务地址/v1"
$env:PYDANTIC_AI_MODEL="你的模型名"
```

只在当前 PowerShell 窗口生效。关闭窗口后需要重新设置。

## 运行示例

在仓库根目录运行：

```powershell
uv run python .codex-learning/pydantic-ai/examples/hello_custom_api.py
```

如果你还没安装依赖，先运行：

```powershell
uv sync --frozen --all-extras --no-extra outlines-vllm-offline --no-extra outlines-llamacpp --all-packages
```

## 不要提交密钥

不要把真实 API key 写进代码、Markdown 或 Git 提交里。这个目录的 `.gitignore` 已经忽略 `.env`，但当前示例不自动读取 `.env`，先用 PowerShell 环境变量最简单。
