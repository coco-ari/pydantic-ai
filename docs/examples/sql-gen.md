# SQL 生成

此示例展示如何使用 Pydantic AI 根据用户输入生成 SQL 查询。

演示内容：

- [动态系统提示](../agent.md#system-prompts)
- [结构化 `output_type`](../output.md#structured-output)
- [输出校验](../output.md#output-validator-functions)
- [智能体依赖](../dependencies.md)

## 运行示例

生成的 SQL 会通过在 PostgreSQL 上以 `EXPLAIN` 查询运行来校验。要运行此示例，你需要先启动 PostgreSQL，例如通过 Docker：

```bash
docker run --rm -e POSTGRES_PASSWORD=postgres -p 54320:5432 postgres
```

_（这里在 `54320` 端口运行 postgres，以避免与你可能正在运行的其他 postgres 实例冲突）_

在[安装依赖并设置环境变量](./setup.md#usage)后运行：

```bash
python/uv-run -m pydantic_ai_examples.sql_gen
```

或者使用自定义提示：

```bash
python/uv-run -m pydantic_ai_examples.sql_gen "find me errors"
```

此模型默认使用 `gemini-3-flash-preview`，因为 Gemini 擅长处理这类一次性查询。

## 示例代码

```snippet {path="/examples/pydantic_ai_examples/sql_gen.py"}```
