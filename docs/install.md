# 安装

Pydantic AI 在 PyPI 上以 [`pydantic-ai`](https://pypi.org/project/pydantic-ai/) 发布，因此安装非常简单：

```bash
pip/uv-add pydantic-ai
```

（需要 Python 3.10+）

这会安装 `pydantic_ai` 包、核心依赖，以及使用 Pydantic AI 中所有内置模型所需的库。
如果你只想安装使用特定模型所需的依赖，可以安装 Pydantic AI 的 ["slim"](#slim-install) 版本。

## 与 Pydantic Logfire 一起使用

Pydantic AI 与 [Pydantic Logfire](https://pydantic.dev/logfire) 有优秀（但完全可选）的集成，可帮助你查看和理解智能体运行。

Logfire 包含在 `pydantic-ai` 中（但不包含在 ["slim" 版本](#slim-install)中），因此通常可以按照 [Logfire 设置文档](logfire.md#using-logfire)立即开始使用。

## 运行示例

我们将 [`pydantic_ai_examples`](https://github.com/pydantic/pydantic-ai/tree/main/examples/pydantic_ai_examples) 目录作为独立 PyPI 包（[`pydantic-ai-examples`](https://pypi.org/project/pydantic-ai-examples/)）分发，让示例极易自定义和运行。

要安装示例，请使用 `examples` 可选组：

```bash
pip/uv-add "pydantic-ai[examples]"
```

要运行示例，请按照[示例文档](examples/setup.md)中的说明操作。

## Slim 安装

如果你知道自己要使用哪个模型，并希望避免安装多余包，可以使用 [`pydantic-ai-slim`](https://pypi.org/project/pydantic-ai-slim/) 包。
例如，如果你只使用 [`OpenAIChatModel`][pydantic_ai.models.openai.OpenAIChatModel]，可以运行：

```bash
pip/uv-add "pydantic-ai-slim[openai]"
```

`pydantic-ai-slim` 有以下可选组：

* `logfire` — 安装 [Pydantic Logfire](logfire.md) 依赖 `logfire` [PyPI ↗](https://pypi.org/project/logfire){:target="_blank"}
* `evals` — 安装 [Pydantic Evals](evals.md) 依赖 `pydantic-evals` [PyPI ↗](https://pypi.org/project/pydantic-evals){:target="_blank"}
* `openai` — 安装 [OpenAI Model](models/openai.md) 依赖 `openai` [PyPI ↗](https://pypi.org/project/openai){:target="_blank"}
* `vertexai` — 安装 `GoogleVertexProvider` 依赖 `google-auth` [PyPI ↗](https://pypi.org/project/google-auth){:target="_blank"} 和 `requests` [PyPI ↗](https://pypi.org/project/requests){:target="_blank"}
* `google` — 安装 [Google Model](models/google.md) 依赖 `google-genai` [PyPI ↗](https://pypi.org/project/google-genai){:target="_blank"}
* `anthropic` — 安装 [Anthropic Model](models/anthropic.md) 依赖 `anthropic` [PyPI ↗](https://pypi.org/project/anthropic){:target="_blank"}
* `groq` — 安装 [Groq Model](models/groq.md) 依赖 `groq` [PyPI ↗](https://pypi.org/project/groq){:target="_blank"}
* `mistral` — 安装 [Mistral Model](models/mistral.md) 依赖 `mistralai` [PyPI ↗](https://pypi.org/project/mistralai){:target="_blank"}
* `cohere` - 安装 [Cohere Model](models/cohere.md) 依赖 `cohere` [PyPI ↗](https://pypi.org/project/cohere){:target="_blank"}
* `bedrock` - 安装 [Bedrock Model](models/bedrock.md) 依赖 `boto3` [PyPI ↗](https://pypi.org/project/boto3){:target="_blank"}
* `huggingface` - 安装 [Hugging Face Model](models/huggingface.md) 依赖 `huggingface-hub` [PyPI ↗](https://pypi.org/project/huggingface-hub){:target="_blank"}
* `sentence-transformers` - 安装 [Sentence Transformers Embedding Model](embeddings.md#sentence-transformers-local) 依赖 `sentence-transformers` [PyPI ↗](https://pypi.org/project/sentence-transformers){:target="_blank"}
* `voyageai` - 安装 [VoyageAI Embedding Model](embeddings.md#voyageai) 依赖 `voyageai` [PyPI ↗](https://pypi.org/project/voyageai){:target="_blank"}
* `outlines-transformers` -（已弃用，将在 v2 移除）安装 [Outlines Model](models/outlines.md) 依赖 `outlines[transformers]` [PyPI ↗](https://pypi.org/project/outlines){:target="_blank"}
* `outlines-llamacpp` -（已弃用，将在 v2 移除）安装 [Outlines Model](models/outlines.md) 依赖 `outlines[llamacpp]` [PyPI ↗](https://pypi.org/project/outlines){:target="_blank"}
* `outlines-mlxlm` -（已弃用，将在 v2 移除）安装 [Outlines Model](models/outlines.md) 依赖 `outlines[mlxlm]` [PyPI ↗](https://pypi.org/project/outlines){:target="_blank"}
* `outlines-sglang` -（已弃用，将在 v2 移除）安装 [Outlines Model](models/outlines.md) 依赖 `outlines[sglang]` [PyPI ↗](https://pypi.org/project/outlines){:target="_blank"}
* `outlines-vllm-offline` -（已弃用，将在 v2 移除）安装 [Outlines Model](models/outlines.md) 依赖 `outlines` [PyPI ↗](https://pypi.org/project/outlines){:target="_blank"} 和 `vllm` [PyPI ↗](https://pypi.org/project/vllm){:target="_blank"}
* `duckduckgo` - 安装 [DuckDuckGo Search Tool](common-tools.md#duckduckgo-search-tool) 依赖 `ddgs` [PyPI ↗](https://pypi.org/project/ddgs){:target="_blank"}
* `tavily` - 安装 [Tavily Search Tool](common-tools.md#tavily-search-tool) 依赖 `tavily-python` [PyPI ↗](https://pypi.org/project/tavily-python){:target="_blank"}
* `exa` - 安装 [Exa Search Tool](common-tools.md#exa-search-tool) 依赖 `exa-py` [PyPI ↗](https://pypi.org/project/exa-py){:target="_blank"}
* `web-fetch` - 安装 [Web Fetch Tool](common-tools.md#web-fetch-tool) 依赖 `markdownify` [PyPI ↗](https://pypi.org/project/markdownify){:target="_blank"}
* `cli` - 安装 [CLI](cli.md) 依赖 `rich` [PyPI ↗](https://pypi.org/project/rich){:target="_blank"}、`prompt-toolkit` [PyPI ↗](https://pypi.org/project/prompt-toolkit){:target="_blank"} 和 `argcomplete` [PyPI ↗](https://pypi.org/project/argcomplete){:target="_blank"}
* `mcp` - 安装 [MCP](mcp/client.md) 依赖 `mcp` [PyPI ↗](https://pypi.org/project/mcp){:target="_blank"}
* `fastmcp` - 安装 [FastMCP](mcp/fastmcp-client.md) 依赖 `fastmcp` [PyPI ↗](https://pypi.org/project/fastmcp){:target="_blank"}
* `a2a` -（已弃用，将在 v2 移除）安装 [A2A](a2a.md) 依赖 `fasta2a` [PyPI ↗](https://pypi.org/project/fasta2a){:target="_blank"}。建议直接安装 `fasta2a[pydantic-ai]>=0.6.1` 并使用 `from fasta2a.pydantic_ai import agent_to_a2a`。
* `ui` - 安装 [UI Event Streams](ui/overview.md) 依赖 `starlette` [PyPI ↗](https://pypi.org/project/starlette){:target="_blank"}
* `ag-ui` - 安装 [AG-UI Event Stream Protocol](ui/ag-ui.md) 依赖 `ag-ui-protocol` [PyPI ↗](https://pypi.org/project/ag-ui-protocol){:target="_blank"} 和 `starlette` [PyPI ↗](https://pypi.org/project/starlette){:target="_blank"}
* `dbos` - 安装 [DBOS Durable Execution](durable_execution/dbos.md) 依赖 `dbos` [PyPI ↗](https://pypi.org/project/dbos){:target="_blank"}
* `prefect` - 安装 [Prefect Durable Execution](durable_execution/prefect.md) 依赖 `prefect` [PyPI ↗](https://pypi.org/project/prefect){:target="_blank"}

你也可以安装多个模型和用例的依赖，例如：

```bash
pip/uv-add "pydantic-ai-slim[openai,google,logfire]"
```
