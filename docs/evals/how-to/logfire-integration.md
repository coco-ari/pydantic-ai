# Logfire 集成 {#logfire-integration}

使用 Pydantic Logfire 可视化和分析 evaluation 结果。

## 概览 {#overview}

Pydantic Evals 使用 OpenTelemetry 记录 evaluation 过程的 traces。这些 traces 包含 evaluation 报告中的所有信息，以及任务函数执行过程中的完整 tracing。

你可以将这些 traces 发送到任何兼容 OpenTelemetry 的后端，包括 [Pydantic Logfire](https://logfire.pydantic.dev/docs/guides/web-ui/evals/)。

## 安装 {#installation}

安装可选的 logfire 依赖：

```bash
pip install 'pydantic-evals[logfire]'
```

## 基本设置 {#basic-setup}

在运行 evaluations 前配置 Logfire：

```python {title="basic_logfire_setup.py"}
import logfire

from pydantic_evals import Case, Dataset

# 配置 Logfire
logfire.configure(
    send_to_logfire='if-token-present',  # (1)!
)


# 你的 evaluation 代码
def my_task(inputs: str) -> str:
    return f'result for {inputs}'


dataset = Dataset(name='logfire_demo', cases=[Case(name='test', inputs='example')])
report = dataset.evaluate_sync(my_task)
```

1. 只有在设置了 `LOGFIRE_TOKEN` 环境变量时，才向 Logfire 发送数据

就这样。只要你设置了 `LOGFIRE_TOKEN` 环境变量，evaluation traces 现在就会出现在 Logfire web UI 中。

## 会发送哪些内容到 Logfire {#what-gets-sent-to-logfire}

运行 evaluation 时，Logfire 会收到：

1. **Evaluation metadata 评估元数据**
    1. 数据集名称
    1. cases 数量
    1. evaluator 名称
2. **每个 case 的数据**
    1. inputs 和 outputs
    1. expected outputs 预期输出
    1. metadata 元数据
    1. 执行时长
3. **Evaluation 结果**
    1. 分数、断言和 labels
    1. reasons（如果包含）
    1. evaluator failures 评估器失败
4. **任务执行 traces**
    1. 来自任务函数的所有 OpenTelemetry spans
    1. 工具调用（对于 Pydantic AI agents）
    1. API 调用、数据库查询等

## 在 Logfire 中查看结果 {#viewing-results-in-logfire}

### Evaluation 概览 {#evaluation-overview}

Logfire 会在 root evaluation span 上为 evaluation 结果提供一个特殊表格视图：

![Logfire Evals 概览](../../img/logfire-evals-overview.png)

该视图会显示：

- Case 名称
- 通过/失败状态
- 分数和断言
- 执行时长
- 快速过滤和排序

### 单个 Case 详情 {#individual-case-details}

点击任何 case 即可查看详细 inputs 和 outputs：

![Logfire Evals 用例](../../img/logfire-evals-case.png)

### 完整 Trace 视图 {#full-trace-view}

查看完整执行 trace，包括 evaluation 期间生成的所有 spans：

![Logfire Evals 用例追踪](../../img/logfire-evals-case-trace.png)

这对以下场景尤其有用：

- 调试失败 cases
- 理解性能瓶颈
- 分析工具使用模式
- 编写基于 span 的 evaluators

## 分析 Traces {#analyzing-traces}

### 对比运行 {#comparing-runs}

多次运行同一个 evaluation，并在 Logfire 中对比：

```python
from pydantic_evals import Case, Dataset


def original_task(inputs: str) -> str:
    return f'original result for {inputs}'


def improved_task(inputs: str) -> str:
    return f'improved result for {inputs}'


dataset = Dataset(name='comparison', cases=[Case(name='test', inputs='example')])

# 运行 1：原始实现
report1 = dataset.evaluate_sync(original_task)

# 运行 2：改进实现
report2 = dataset.evaluate_sync(improved_task)

# 在 Logfire 中按时间戳或 attributes 过滤进行对比
```

### 调试失败 Cases {#debugging-failed-cases}

快速查找失败 cases：

1. 搜索 `service_name = 'my_service_evals' AND is_exception`（替换成你实际使用的 service name）
2. 查看完整 span tree，确认失败发生的位置
3. 检查 attributes 和 logs 中的错误消息

## 基于 Span 的 Evaluation {#span-based-evaluation}

Logfire 集成支持强大的 span-based evaluators。详情请参见 [Span-Based Evaluation](../evaluators/span-based.md)。

示例：验证调用了特定工具：

```python
import logfire

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import HasMatchingSpan

logfire.configure(send_to_logfire='if-token-present')


def my_agent(inputs: str) -> str:
    return f'result for {inputs}'


dataset = Dataset(
    name='logfire_demo',
    cases=[Case(name='test', inputs='example')],
    evaluators=[
        HasMatchingSpan(
            query={'name_contains': 'search_tool'},
            evaluation_name='used_search',
        ),
    ],
)

report = dataset.evaluate_sync(my_agent)
```

span tree 可在以下两处使用：

- 你的 evaluator 代码中（通过 `ctx.span_tree`）
- Logfire UI 中（可视化 trace 视图）

## 故障排查 {#troubleshooting}

### Logfire 中没有数据 {#no-data-appearing-in-logfire}

请检查：

1. **Token 已设置**：`echo $LOGFIRE_TOKEN`
2. **配置正确**：
   ```python
   import logfire

   logfire.configure(send_to_logfire='always')  # 强制发送
   ```
3. **网络连接**：检查防火墙设置
4. **项目存在**：在 Logfire UI 中验证项目名称

### Traces 缺少 Spans {#traces-missing-spans}

如果缺少某些 spans：

1. **确保在 imports 前配置 logfire**：
   ```python
   import logfire

   logfire.configure()  # 必须最先执行
   ```

2. **检查 instrumentation**：确保代码启用了你需要的所有 instrumentations：
   ```python
   import logfire

   logfire.instrument_pydantic_ai()
   logfire.instrument_httpx(capture_all=True)
   ```

## 最佳实践 {#best-practices}

### 1. 尽早配置 {#1-configure-early}

始终在运行 evaluations 前配置 Logfire：

```python
import logfire

from pydantic_evals import Case, Dataset

logfire.configure(send_to_logfire='if-token-present')


# 现在导入并运行 evaluations
def task(inputs: str) -> str:
    return f'result for {inputs}'


dataset = Dataset(name='logfire_demo', cases=[Case(name='test', inputs='example')])
dataset.evaluate_sync(task)
```

### 2. 使用描述性 Service Names 和 Environments {#2-use-descriptive-service-names-and-environments}

```python
import logfire

logfire.configure(
    service_name='rag-pipeline-evals',
    environment='development',
)
```

### 3. 定期查看 {#3-review-periodically}

- 定期检查 Logfire 以识别模式
- 查找持续失败的 cases
- 分析性能趋势
- 基于洞察调整 evaluators

## 后续步骤 {#next-steps}

- **[Span-Based Evaluation](../evaluators/span-based.md)** - 在 evaluators 中使用 OpenTelemetry spans
- **[Logfire Documentation](https://logfire.pydantic.dev/docs/guides/web-ui/evals/)** - 完整 Logfire 指南
- **[Metrics & Attributes](metrics-attributes.md)** - 向 traces 添加自定义数据
