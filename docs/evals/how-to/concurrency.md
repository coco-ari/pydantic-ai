# 并发与性能 {#concurrency-performance}

控制 evaluation cases 如何并行执行。

## 概览 {#overview}

默认情况下，Pydantic Evals 会并发运行所有 cases，以最大化吞吐量。你可以用 `max_concurrency` 参数控制此行为。

## 基本用法 {#basic-usage}

```python
from pydantic_evals import Case, Dataset


def my_task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='concurrency_demo', cases=[Case(inputs='test1'), Case(inputs='test2')])

# 并发运行所有 cases（默认）
report = dataset.evaluate_sync(my_task)

# 限制为 5 个并发 cases
report = dataset.evaluate_sync(my_task, max_concurrency=5)

# 顺序运行（一次一个）
report = dataset.evaluate_sync(my_task, max_concurrency=1)
```

## 何时限制并发 {#when-to-limit-concurrency}

### 速率限制 {#rate-limiting}

许多 API 都有速率限制，会约束并发请求：

```python
from pydantic_evals import Case, Dataset


async def my_llm_task(inputs: str) -> str:
    return f'LLM Result: {inputs}'


dataset = Dataset(name='rate_limit_demo', cases=[Case(inputs='test1')])

# 如果你的 API 允许每秒 10 个请求
report = dataset.evaluate_sync(
    my_llm_task,
    max_concurrency=10,
)
```

### 资源约束 {#resource-constraints}

限制并发可以避免压垮系统资源：

```python
from pydantic_evals import Case, Dataset


def heavy_computation(inputs: str) -> str:
    return f'Heavy: {inputs}'


def db_query_task(inputs: str) -> str:
    return f'DB: {inputs}'


dataset = Dataset(name='resource_constraints', cases=[Case(inputs='test1')])

# 内存密集型操作
report = dataset.evaluate_sync(
    heavy_computation,
    max_concurrency=2,  # 每次只运行 2 个
)

# 数据库连接池限制
report = dataset.evaluate_sync(
    db_query_task,
    max_concurrency=5,  # 匹配连接池大小
)
```

### 调试 {#debugging}

顺序运行可以看到更清晰的错误 trace：

```python
from pydantic_evals import Case, Dataset


def my_task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='debug_demo', cases=[Case(inputs='test1')])

# 更容易调试
report = dataset.evaluate_sync(
    my_task,
    max_concurrency=1,
)
```

## 性能对比 {#performance-comparison}

下面的示例展示性能差异：

```python {title="concurrency_example.py"}
import asyncio

from pydantic_evals import Case, Dataset

# 创建包含多个测试 cases 的数据集
dataset = Dataset(
    name='performance_comparison',
    cases=[
        Case(
            name=f'case_{i}',
            inputs=i,
            expected_output=i * 2,
        )
        for i in range(10)
    ]
)


async def slow_task(input_value: int) -> int:
    """模拟慢操作（例如 API 调用）。"""
    await asyncio.sleep(0.1)  # 每个 case 100ms
    return input_value * 2


# 无限制并发：总计约 0.1s（所有 cases 并行运行）
report = dataset.evaluate_sync(slow_task)

# 限制并发：总计约 0.5s（每次 2 个，5 批）
report = dataset.evaluate_sync(slow_task, max_concurrency=2)

# 顺序执行：总计约 1.0s（每次 1 个，10 个 cases）
report = dataset.evaluate_sync(slow_task, max_concurrency=1)
```

## Evaluators 的并发 {#concurrency-with-evaluators}

默认情况下，任务执行和 evaluator 执行都会并发发生：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge


def my_task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(
    name='evaluator_concurrency',
    cases=[Case(inputs=f'test{i}') for i in range(100)],  # 100 个 cases
    evaluators=[
        LLMJudge(rubric='Quality check'),  # 会发起 API 调用
    ],
)

# 任务和 evaluator 都按受控并发运行
report = dataset.evaluate_sync(
    my_task,
    max_concurrency=10,
)
```

如果你的 evaluators 成本较高（例如 [`LLMJudge`][pydantic_evals.evaluators.LLMJudge]），限制并发有助于管理：

- API 速率限制
- 成本（减少并发 API 调用）
- 内存使用

## Async 与 Sync {#async-vs-sync}

同步和异步 evaluation 都支持并发控制：

### Sync API

```python
from pydantic_evals import Case, Dataset


def my_task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='sync_demo', cases=[Case(inputs='test1')])

# 在内部以受控并发运行异步操作
report = dataset.evaluate_sync(my_task, max_concurrency=10)
```

### Async API

```python
from pydantic_evals import Case, Dataset


async def my_task(inputs: str) -> str:
    return f'Result: {inputs}'


async def run_evaluation():
    dataset = Dataset(name='async_demo', cases=[Case(inputs='test1')])
    # 行为相同，但位于 async context 中
    report = await dataset.evaluate(my_task, max_concurrency=10)
    return report
```

## 监控并发 {#monitoring-concurrency}

跟踪执行情况以优化设置：

```python {test="skip"}
import time

from pydantic_evals import Case, Dataset


def task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='monitoring', cases=[Case(inputs=f'test{i}') for i in range(10)])

t0 = time.time()
report = dataset.evaluate_sync(task, max_concurrency=10)
duration = time.time() - t0

num_cases = len(report.cases) + len(report.failures)
avg_duration = duration / num_cases

print(f'Total: {duration:.2f}s')
#> Total: 0.01s
print(f'Cases: {num_cases}')
#> Cases: 10
print(f'Avg per case: {avg_duration:.2f}s')
#> Avg per case: 0.00s
print(f'Effective concurrency: ~{num_cases * avg_duration / duration:.1f}')
#> Effective concurrency: ~1.0
```

## 处理速率限制 {#handling-rate-limits}

如果触发速率限制，evaluation 会失败。请使用 retry strategies：

```python
from pydantic_evals import Case, Dataset


def task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='rate_limit_handling', cases=[Case(inputs='test1')])

# 降低并发以避免速率限制
report = dataset.evaluate_sync(
    task,
    max_concurrency=5,  # 保持在速率限制以下
)
```

处理瞬时失败请参见 [Retry Strategies](retry-strategies.md)。

## 后续步骤 {#next-steps}

- **[Retry Strategies](retry-strategies.md)** - 处理瞬时失败
- **[Dataset Management](dataset-management.md)** - 处理大型数据集
- **[Logfire Integration](logfire-integration.md)** - 监控性能
