# 重试策略 {#retry-strategies}

使用自动重试逻辑处理 tasks 和 evaluators 中的瞬时失败。

## 概览 {#overview}

基于 LLM 的系统可能遇到瞬时失败：

- 速率限制
- 网络超时
- 临时 API 中断
- 上下文长度错误

Pydantic Evals 支持为以下两者配置 retry：

- **Task execution 任务执行** - 被评估的函数
- **Evaluator execution 评估器执行** - evaluators 本身

## 基本 Retry 配置 {#basic-retry-configuration}

使用 [Tenacity](https://tenacity.readthedocs.io/) 参数向 `evaluate()` 或 `evaluate_sync()` 传入 retry 配置：

```python
from tenacity import stop_after_attempt

from pydantic_evals import Case, Dataset


def my_function(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='basic_retry', cases=[Case(inputs='test')], evaluators=[])

report = dataset.evaluate_sync(
    task=my_function,
    retry_task={'stop': stop_after_attempt(3)},
    retry_evaluators={'stop': stop_after_attempt(2)},
)
```

## Retry 配置选项 {#retry-configuration-options}

Retry 配置使用 [Tenacity](https://tenacity.readthedocs.io/)，并支持与 Pydantic AI 的 [`RetryConfig`][pydantic_ai.retries.RetryConfig] 相同的选项：

```python
from tenacity import stop_after_attempt, wait_exponential

from pydantic_evals import Case, Dataset


def my_function(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='retry_config', cases=[Case(inputs='test')], evaluators=[])

retry_config = {
    'stop': stop_after_attempt(3),  # 3 次尝试后停止
    'wait': wait_exponential(multiplier=1, min=1, max=10),  # 指数退避：1s、2s、4s、8s（上限 10s）
    'reraise': True,  # 重试耗尽后重新抛出原始异常
}

dataset.evaluate_sync(
    task=my_function,
    retry_task=retry_config,
)
```

### 常用参数 {#common-parameters}

retry 配置接受 tenacity `retry` 装饰器的任何参数。常见参数包括：

| 参数 | 类型 | 描述 |
|-----------|------|-------------|
| `stop` | `StopBaseT` | stop strategy（例如 `stop_after_attempt(3)`、`stop_after_delay(60)`） |
| `wait` | `WaitBaseT` | wait strategy（例如 `wait_exponential()`、`wait_fixed(2)`） |
| `retry` | `RetryBaseT` | retry condition（例如 `retry_if_exception_type(TimeoutError)`） |
| `reraise` | `bool` | 是否重新抛出原始异常（默认：`False`） |
| `before_sleep` | `Callable` | 重试间 sleep 前的 callback |

所有可用选项请参见 [Tenacity documentation](https://tenacity.readthedocs.io/)。

## Task Retries 任务重试 {#task-retries}

当 task function 失败时进行重试：

```python
from tenacity import stop_after_attempt, wait_exponential

from pydantic_evals import Case, Dataset


async def call_llm(inputs: str) -> str:
    return f'LLM response to: {inputs}'


async def flaky_llm_task(inputs: str) -> str:
    """这可能触发速率限制或超时。"""
    response = await call_llm(inputs)
    return response


dataset = Dataset(name='task_retry', cases=[Case(inputs='test')])

report = dataset.evaluate_sync(
    task=flaky_llm_task,
    retry_task={
        'stop': stop_after_attempt(5),  # 最多尝试 5 次
        'wait': wait_exponential(multiplier=1, min=1, max=30),  # 指数退避，上限 30s
        'reraise': True,
    },
)
```

### Task Retries 何时触发 {#when-task-retries-trigger}

当 task 抛出异常时，会触发 retries：

```python
class RateLimitError(Exception):
    pass


class ValidationError(Exception):
    pass


async def call_api(inputs: str) -> str:
    return f'API response: {inputs}'


async def my_task(inputs: str) -> str:
    try:
        return await call_api(inputs)
    except RateLimitError:
        # 会触发 retry
        raise
    except ValidationError:
        # 也会触发 retry
        raise
```

### 指数退避 {#exponential-backoff}

使用 `wait_exponential()` 时，延迟会指数增长：

```
尝试 1：立即
尝试 2：约 1s 延迟（multiplier * 2^0）
尝试 3：约 2s 延迟（multiplier * 2^1）
尝试 4：约 4s 延迟（multiplier * 2^2）
尝试 5：约 8s 延迟（multiplier * 2^3，受 max 限制）
```

实际延迟取决于传给 `wait_exponential()` 的 `multiplier`、`min` 和 `max` 参数。

## Evaluator Retries 评估器重试 {#evaluator-retries}

当 evaluators 失败时重试：

```python
from tenacity import stop_after_attempt, wait_exponential

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge


def my_task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(
    name='evaluator_retry',
    cases=[Case(inputs='test')],
    evaluators=[
        # LLMJudge 可能触发速率限制
        LLMJudge(rubric='Response is accurate'),
    ],
)

report = dataset.evaluate_sync(
    task=my_task,
    retry_evaluators={
        'stop': stop_after_attempt(3),
        'wait': wait_exponential(multiplier=1, min=0.5, max=10),
        'reraise': True,
    },
)
```

### Evaluator Retries 何时触发 {#when-evaluator-retries-trigger}

当 evaluator 抛出异常时，会触发 retries：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


async def external_api_call(output: str) -> bool:
    return len(output) > 0


@dataclass
class APIEvaluator(Evaluator):
    async def evaluate(self, ctx: EvaluatorContext) -> bool:
        # 如果这里抛出异常，retry 逻辑会触发
        result = await external_api_call(ctx.output)
        return result
```

### Evaluator Failures 评估器失败 {#evaluator-failures}

如果 evaluator 在所有 retries 后仍失败，会记录为 [`EvaluatorFailure`][pydantic_evals.evaluators.EvaluatorFailure]：

```python
from tenacity import stop_after_attempt

from pydantic_evals import Case, Dataset


def task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='evaluator_failures', cases=[Case(inputs='test')], evaluators=[])

report = dataset.evaluate_sync(task, retry_evaluators={'stop': stop_after_attempt(3)})

# 检查 evaluator failures
for case in report.cases:
    if case.evaluator_failures:
        for failure in case.evaluator_failures:
            print(f'Evaluator {failure.name} failed: {failure.error_message}')
    #> (No output - no evaluator failures in this case)
```

在 reports 中查看 evaluator failures：

```python
from pydantic_evals import Case, Dataset


def task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='failure_report', cases=[Case(inputs='test')], evaluators=[])
report = dataset.evaluate_sync(task)

report.print(include_evaluator_failures=True)
"""
  Evaluation Summary:
         task
┏━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID  ┃ Duration ┃
┡━━━━━━━━━━╇━━━━━━━━━━┩
│ Case 1   │     10ms │
├──────────┼──────────┤
│ Averages │     10ms │
└──────────┴──────────┘
"""
#>
#> ✅ case_0                       ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% (0/0)
```

## 组合 Task 和 Evaluator Retries {#combining-task-and-evaluator-retries}

你可以分别配置二者：

```python
from tenacity import stop_after_attempt, wait_exponential

from pydantic_evals import Case, Dataset


def flaky_task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='combined_retry', cases=[Case(inputs='test')], evaluators=[])

report = dataset.evaluate_sync(
    task=flaky_task,
    retry_task={
        'stop': stop_after_attempt(5),  # task 最多重试 5 次
        'wait': wait_exponential(multiplier=1, min=1, max=30),
        'reraise': True,
    },
    retry_evaluators={
        'stop': stop_after_attempt(3),  # evaluators 最多重试 3 次
        'wait': wait_exponential(multiplier=1, min=0.5, max=10),
        'reraise': True,
    },
)
```

## 实用示例 {#practical-examples}

### 处理速率限制 {#rate-limit-handling}

```python
from tenacity import stop_after_attempt, wait_exponential

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge


async def expensive_llm_call(inputs: str) -> str:
    return f'LLM response: {inputs}'


async def llm_task(inputs: str) -> str:
    """可能触发速率限制的 task。"""
    return await expensive_llm_call(inputs)


dataset = Dataset(
    name='rate_limit_retry',
    cases=[Case(inputs='test')],
    evaluators=[
        LLMJudge(rubric='Quality check'),  # 也可能触发速率限制
    ],
)

# 为速率限制配置更宽松的 retries
report = dataset.evaluate_sync(
    task=llm_task,
    retry_task={
        'stop': stop_after_attempt(10),  # 速率限制可能需要多次重试
        'wait': wait_exponential(multiplier=2, min=2, max=60),  # 从 2s 开始，指数增长到最高 60s
        'reraise': True,
    },
    retry_evaluators={
        'stop': stop_after_attempt(5),
        'wait': wait_exponential(multiplier=2, min=2, max=30),
        'reraise': True,
    },
)
```

### 处理网络超时 {#network-timeout-handling}

```python
import httpx
from tenacity import stop_after_attempt, wait_exponential

from pydantic_evals import Case, Dataset


async def api_task(inputs: str) -> str:
    """调用可能超时的外部 API 的 task。"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post('https://api.example.com', json={'input': inputs})
        return response.text


dataset = Dataset(name='timeout_retry', cases=[Case(inputs='test')], evaluators=[])

# 为网络问题配置快速 retries
report = dataset.evaluate_sync(
    task=api_task,
    retry_task={
        'stop': stop_after_attempt(4),  # 几次快速重试
        'wait': wait_exponential(multiplier=0.5, min=0.5, max=5),  # 快速重试，上限 5s
        'reraise': True,
    },
)
```

### 处理 Context Length {#context-length-handling}

```python
from tenacity import stop_after_attempt

from pydantic_evals import Case, Dataset


class ContextLengthError(Exception):
    pass


async def llm_call(inputs: str, max_tokens: int = 8000) -> str:
    return f'LLM response: {inputs[:100]}'


async def smart_llm_task(inputs: str) -> str:
    """可能超过 context length 的 task。"""
    try:
        return await llm_call(inputs, max_tokens=8000)
    except ContextLengthError:
        # 使用更短 context 重试
        truncated_inputs = inputs[:4000]
        return await llm_call(truncated_inputs, max_tokens=4000)


dataset = Dataset(name='context_length', cases=[Case(inputs='test')], evaluators=[])

# 不重试 context length errors（在 task 中处理）
report = dataset.evaluate_sync(
    task=smart_llm_task,
    retry_task={'stop': stop_after_attempt(1)},  # 不重试，由我们处理
)
```

## Retry 与 Error Handling {#retry-vs-error-handling}

**Retries 适用于：**

- 瞬时失败（速率限制、超时）
- 网络问题
- 临时服务中断
- 可恢复错误

**Error handling 适用于：**

- 校验错误
- 逻辑错误
- 永久失败
- 预期错误条件

```python
class RateLimitError(Exception):
    pass


async def llm_call(inputs: str) -> str:
    return f'LLM response: {inputs}'


def is_valid(result: str) -> bool:
    return len(result) > 0


async def smart_task(inputs: str) -> str:
    """处理预期错误，让 retries 处理瞬时失败。"""
    try:
        result = await llm_call(inputs)

        # 验证 output（不要重试 validation errors）
        if not is_valid(result):
            return 'ERROR: Invalid output format'

        return result

    except RateLimitError:
        # 让 retry 逻辑处理它
        raise

    except ValueError as e:
        # 不重试，这是永久错误
        return f'ERROR: {e}'
```

## 故障排查 {#troubleshooting}

### "重试后仍失败" {#still-failing-after-retries}

增加 retry attempts，或检查错误是否可重试：

```python
import logging

from tenacity import stop_after_attempt

from pydantic_evals import Case, Dataset


def task(inputs: str) -> str:
    return f'Result: {inputs}'


# 添加 logging 以查看失败原因
logging.basicConfig(level=logging.DEBUG)

dataset = Dataset(name='troubleshooting', cases=[Case(inputs='test')], evaluators=[])

# Tenacity 会记录 retry attempts
report = dataset.evaluate_sync(task, retry_task={'stop': stop_after_attempt(5)})
```

### "Evaluations 耗时太长" {#evaluations-taking-too-long}

减少 retry attempts 或等待时间：

```python
from tenacity import stop_after_attempt, wait_exponential

# 更快的 retries
retry_config = {
    'stop': stop_after_attempt(3),  # 更少 attempts
    'wait': wait_exponential(multiplier=0.1, min=0.1, max=2),  # 快速 retries，上限 2s
    'reraise': True,
}
```

### "尽管重试仍触发速率限制" {#hitting-rate-limits-despite-retries}

增加延迟，或使用 `max_concurrency`：

```python
from tenacity import stop_after_attempt, wait_exponential

from pydantic_evals import Case, Dataset


def task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='rate_limit_config', cases=[Case(inputs='test')], evaluators=[])

# 更长延迟
retry_config = {
    'stop': stop_after_attempt(5),
    'wait': wait_exponential(multiplier=5, min=5, max=60),  # 从 5s 开始，指数增长到最高 60s
    'reraise': True,
}

# 同时降低并发
report = dataset.evaluate_sync(
    task=task,
    retry_task=retry_config,
    max_concurrency=2,  # 仅 2 个并发 tasks
)
```

## 后续步骤 {#next-steps}

- **[Concurrency & Performance](concurrency.md)** - 优化 evaluation 性能
- **[Logfire Integration](logfire-integration.md)** - 在 Logfire 中查看 retries
