# RAG

RAG 搜索示例。此演示允许你向 [Logfire](https://pydantic.dev/logfire) 文档提问。

演示内容：

- [工具](../tools.md)
- [智能体依赖](../dependencies.md)
- RAG 搜索

实现方式是创建一个包含 Markdown 文档各个章节的数据库，然后将搜索工具注册到 Pydantic AI 智能体。

从 Markdown 文件中提取章节的逻辑，以及包含这些数据的 JSON 文件，可在
[这个 gist](https://gist.github.com/samuelcolvin/4b5bb9bb163b1122ff17e29e48c10992) 中找到。

搜索数据库使用 [带 pgvector 的 PostgreSQL](https://github.com/pgvector/pgvector)，下载并运行 pgvector 最简单的方式是使用 Docker：

```bash
mkdir postgres-data
docker run --rm \
  -e POSTGRES_PASSWORD=postgres \
  -p 54320:5432 \
  -v `pwd`/postgres-data:/var/lib/postgresql/data \
  pgvector/pgvector:pg17
```

与 [SQL 生成](./sql-gen.md)示例一样，我们在 `54320` 端口运行 postgres，以避免与你可能正在运行的其他 postgres 实例冲突。
我们还会将 PostgreSQL `data` 目录挂载到本地，以便在需要停止并重启容器时持久化数据。

启动数据库并[安装依赖、设置环境变量](./setup.md#usage)后，可以用下面的命令构建搜索数据库（**警告**：这需要 `OPENAI_API_KEY` 环境变量，并会调用 OpenAI embedding API 约 300 次，为文档的每个章节生成 embedding）：

```bash
python/uv-run -m pydantic_ai_examples.rag build
```

（注意：当前构建数据库并不使用 Pydantic AI，而是直接使用 OpenAI SDK。）

然后可以用下面的命令向智能体提问：

```bash
python/uv-run -m pydantic_ai_examples.rag search "How do I configure logfire to work with FastAPI?"
```

## 示例代码

```snippet {path="/examples/pydantic_ai_examples/rag.py"}```
