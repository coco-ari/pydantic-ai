# 数据分析师 {#data-analyst}

在某些智能体工作流中，智能体不需要知道工具输出的精确内容，但仍需要以某种方式处理工具输出。这在数据分析中尤其常见：智能体需要知道查询工具的结果是一个带有特定命名列的 `DataFrame`，但不一定需要知道每一行的内容。

借助 Pydantic AI，你可以使用[依赖对象](../dependencies.md)存储某个工具的结果，并在另一个工具中使用它。

在这个示例中，我们将构建一个智能体，用于分析 [Cornell 的 Rotten Tomatoes 电影评论数据集](https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes)。


演示内容：

- [智能体依赖](../dependencies.md)


## 运行示例 {#running-the-example}

在[安装依赖并设置环境变量](./setup.md#usage)后，运行：

```bash
python/uv-run -m pydantic_ai_examples.data_analyst
```


输出（debug）：


> 根据我对 Cornell Movie Review 数据集（rotten_tomatoes）的分析，训练拆分中有 **4,265 条负面评论**。这些评论的标签是 'neg'（在数据集中用 0 表示）。



## 示例代码 {#example-code}

```snippet {path="/examples/pydantic_ai_examples/data_analyst.py"}```


## 附录 {#appendix}

### 选择模型 {#choosing-a-model}

此示例需要使用理解 DuckDB SQL 的模型。你可以用 `clai` 检查：

```sh
> clai -m bedrock:us.anthropic.claude-sonnet-4-5-20250929-v1:0
clai - Pydantic AI CLI v0.0.1.dev920+41dd069 with bedrock:us.anthropic.claude-sonnet-4-5-20250929-v1:0
clai ➤ do you understand duckdb sql?
# DuckDB SQL

是的，我理解 DuckDB SQL。DuckDB 是一种进程内分析型 SQL 数据库，
语法类似 PostgreSQL。它专注于分析查询，
并为结构化数据的高性能分析而设计。

DuckDB SQL 的一些关键特性包括：

 • 针对 OLAP（在线分析处理）优化
 • 列式向量化查询执行
 • 支持标准 SQL，并兼容 PostgreSQL
 • 支持复杂分析查询
 • 高效处理 CSV/Parquet/JSON 文件

我可以帮助你处理 DuckDB SQL 查询、schema 设计、优化或其他
DuckDB 相关问题。
```
