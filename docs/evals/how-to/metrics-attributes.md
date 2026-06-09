# Metrics 与 Attributes

在任务执行期间跟踪自定义 metrics 和 attributes，以获得更丰富的评估洞察。

## 概览 {#overview}

执行评估任务时，你可以记录：

- **Metrics** - 用于定量测量的数值（int/float）
- **Attributes** - 用于定性信息的任意数据

这些内容会出现在评估报告中，也可供 evaluators 用于评估。

## 记录 Metrics {#recording-metrics}

使用 [`increment_eval_metric`][pydantic_evals.increment_eval_metric] 跟踪数值：

```python
from dataclasses import dataclass

from pydantic_evals.dataset import increment_eval_metric


@dataclass
class APIResult:
    output: str
    usage: 'Usage'


@dataclass
class Usage:
    total_tokens: int


def call_api(inputs: str) -> APIResult:
    return APIResult(output=f'Result: {inputs}', usage=Usage(total_tokens=100))


def my_task(inputs: str) -> str:
    # Track API calls
    increment_eval_metric('api_calls', 1)

    result = call_api(inputs)

    # Track tokens used
    increment_eval_metric('tokens_used', result.usage.total_tokens)

    return result.output
```

## 记录 Attributes {#recording-attributes}

使用 [`set_eval_attribute`][pydantic_evals.set_eval_attribute] 存储任意数据：

```python
from pydantic_evals import set_eval_attribute


def process(inputs: str) -> str:
    return f'Processed: {inputs}'


def my_task(inputs: str) -> str:
    # Record which model was used
    set_eval_attribute('model', 'gpt-5.2')

    # Record feature flags
    set_eval_attribute('used_cache', True)
    set_eval_attribute('retry_count', 2)

    # Record structured data
    set_eval_attribute('config', {
        'temperature': 0.7,
        'max_tokens': 100,
    })

    return process(inputs)
```

## 在 Evaluators 中访问 {#accessing-in-evaluators}

Metrics 和 attributes 可通过 [`EvaluatorContext`][pydantic_evals.evaluators.EvaluatorContext] 获取：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class EfficiencyChecker(Evaluator):
    max_api_calls: int = 5

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool]:
        # Access metrics
        api_calls = ctx.metrics.get('api_calls', 0)
        tokens_used = ctx.metrics.get('tokens_used', 0)

        # Access attributes
        used_cache = ctx.attributes.get('used_cache', False)

        return {
            'efficient_api_usage': api_calls <= self.max_api_calls,
            'used_caching': used_cache,
            'token_efficient': tokens_used < 1000,
        }
```

## 在报告中查看 {#viewing-in-reports}

Metrics 和 attributes 会出现在报告数据中：

```python
from pydantic_evals import Case, Dataset


def task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='report_viewing', cases=[Case(inputs='test')], evaluators=[])
report = dataset.evaluate_sync(task)

for case in report.cases:
    print(f'{case.name}:')
    #> Case 1:
    print(f'  Metrics: {case.metrics}')
    #>   Metrics: {}
    print(f'  Attributes: {case.attributes}')
    #>   Attributes: {}
```

你也可以在打印的报告中显示它们：

```python
from pydantic_evals import Case, Dataset


def task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(name='report_printing', cases=[Case(inputs='test')], evaluators=[])
report = dataset.evaluate_sync(task)

# Metrics and attributes are available but not shown by default
# Access them programmatically or via Logfire

for case in report.cases:
    print(f'\nCase: {case.name}')
    """
    Case: Case 1
    """
    print(f'Metrics: {case.metrics}')
    #> Metrics: {}
    print(f'Attributes: {case.attributes}')
    #> Attributes: {}
```

## 自动 Metrics {#automatic-metrics}

使用 Pydantic AI 和 Logfire 时，会自动跟踪一些 metrics：

```python
import logfire

from pydantic_ai import Agent

logfire.configure(send_to_logfire='if-token-present')

agent = Agent('openai:gpt-5.2')


async def ai_task(inputs: str) -> str:
    result = await agent.run(inputs)
    return result.output


# Automatically tracked metrics:
# - requests: Number of LLM calls
# - input_tokens: Total input tokens
# - output_tokens: Total output tokens
# - prompt_tokens: Prompt tokens (if available)
# - completion_tokens: Completion tokens (if available)
# - cost: Estimated cost (if using genai-prices)
```

在 evaluators 中访问这些指标：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class CostChecker(Evaluator):
    max_cost: float = 0.01  # $0.01

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        cost = ctx.metrics.get('cost', 0.0)
        return cost <= self.max_cost
```

## 实用示例 {#practical-examples}

### API 使用跟踪 {#api-usage-tracking}

```python
from dataclasses import dataclass

from pydantic_evals import increment_eval_metric, set_eval_attribute
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


def check_cache(inputs: str) -> str | None:
    return None  # No cache hit for demo


@dataclass
class APIResult:
    text: str
    usage: 'Usage'


@dataclass
class Usage:
    total_tokens: int


async def call_api(inputs: str) -> APIResult:
    return APIResult(text=f'Result: {inputs}', usage=Usage(total_tokens=100))


def save_to_cache(inputs: str, result: str) -> None:
    pass  # Save to cache


async def smart_task(inputs: str) -> str:
    # Try cache first
    if cached := check_cache(inputs):
        set_eval_attribute('cache_hit', True)
        return cached

    set_eval_attribute('cache_hit', False)

    # Call API
    increment_eval_metric('api_calls', 1)
    result = await call_api(inputs)

    increment_eval_metric('tokens', result.usage.total_tokens)

    # Cache result
    save_to_cache(inputs, result.text)

    return result.text


# Evaluate efficiency
@dataclass
class EfficiencyEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | float]:
        api_calls = ctx.metrics.get('api_calls', 0)
        cache_hit = ctx.attributes.get('cache_hit', False)

        return {
            'used_cache': cache_hit,
            'made_api_call': api_calls > 0,
            'efficiency_score': 1.0 if cache_hit else 0.5,
        }
```

### 工具使用跟踪 {#tool-usage-tracking}

```python
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_evals import increment_eval_metric, set_eval_attribute
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

agent = Agent('openai:gpt-5.2')


def search(query: str) -> str:
    return f'Search results for: {query}'


def call(endpoint: str) -> str:
    return f'API response from: {endpoint}'


@agent.tool
def search_database(ctx: RunContext, query: str) -> str:
    increment_eval_metric('db_searches', 1)
    set_eval_attribute('last_query', query)
    return search(query)


@agent.tool
def call_api(ctx: RunContext, endpoint: str) -> str:
    increment_eval_metric('api_calls', 1)
    set_eval_attribute('last_endpoint', endpoint)
    return call(endpoint)


# Evaluate tool usage
@dataclass
class ToolUsageEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | int]:
        db_searches = ctx.metrics.get('db_searches', 0)
        api_calls = ctx.metrics.get('api_calls', 0)

        return {
            'used_database': db_searches > 0,
            'used_api': api_calls > 0,
            'tool_call_count': db_searches + api_calls,
            'reasonable_tool_usage': (db_searches + api_calls) <= 5,
        }
```

### 性能跟踪 {#performance-tracking}

```python
import time
from dataclasses import dataclass

from pydantic_evals import increment_eval_metric, set_eval_attribute
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


async def retrieve_context(inputs: str) -> list[str]:
    return ['context1', 'context2']


async def generate_response(context: list[str], inputs: str) -> str:
    return f'Generated response for {inputs}'


async def monitored_task(inputs: str) -> str:
    # Track sub-operation timing
    t0 = time.perf_counter()
    context = await retrieve_context(inputs)
    retrieve_time = time.perf_counter() - t0

    increment_eval_metric('retrieve_time', retrieve_time)

    t0 = time.perf_counter()
    result = await generate_response(context, inputs)
    generate_time = time.perf_counter() - t0

    increment_eval_metric('generate_time', generate_time)

    # Record which operations were needed
    set_eval_attribute('needed_retrieval', len(context) > 0)
    set_eval_attribute('context_chunks', len(context))

    return result


# Evaluate performance
@dataclass
class PerformanceEvaluator(Evaluator):
    max_retrieve_time: float = 0.5
    max_generate_time: float = 2.0

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool]:
        retrieve_time = ctx.metrics.get('retrieve_time', 0.0)
        generate_time = ctx.metrics.get('generate_time', 0.0)

        return {
            'fast_retrieval': retrieve_time <= self.max_retrieve_time,
            'fast_generation': generate_time <= self.max_generate_time,
        }
```

### 质量跟踪 {#quality-tracking}

```python
from dataclasses import dataclass

from pydantic_evals import set_eval_attribute
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


async def llm_call(inputs: str) -> dict:
    return {'text': f'Response: {inputs}', 'confidence': 0.85, 'sources': ['doc1', 'doc2']}


async def quality_task(inputs: str) -> str:
    result = await llm_call(inputs)

    # Extract quality indicators
    confidence = result.get('confidence', 0.0)
    sources_used = result.get('sources', [])

    set_eval_attribute('confidence', confidence)
    set_eval_attribute('source_count', len(sources_used))
    set_eval_attribute('sources', sources_used)

    return result['text']


# Evaluate based on quality signals
@dataclass
class QualityEvaluator(Evaluator):
    min_confidence: float = 0.7

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | float]:
        confidence = ctx.attributes.get('confidence', 0.0)
        source_count = ctx.attributes.get('source_count', 0)

        return {
            'high_confidence': confidence >= self.min_confidence,
            'used_sources': source_count > 0,
            'quality_score': confidence * (1.0 + 0.1 * source_count),
        }
```


## 实验级 Metadata {#experiment-level-metadata}

除了 case-level metadata 之外，调用 [`evaluate()`][pydantic_evals.dataset.Dataset.evaluate] 时也可以传入 experiment-level metadata：

```python
from pydantic_evals import Case, Dataset

dataset = Dataset(
    name='experiment_metadata',
    cases=[
        Case(
            inputs='test',
            metadata={'difficulty': 'easy'},  # Case-level metadata
        )
    ]
)


async def task(inputs: str) -> str:
    return f'Result: {inputs}'


# Pass experiment-level metadata
async def main():
    report = await dataset.evaluate(
        task,
        metadata={
            'model': 'gpt-5.2',
            'prompt_version': 'v2.1',
            'temperature': 0.7,
        },
    )

    # Access experiment metadata in the report
    print(report.experiment_metadata)
    #> {'model': 'gpt-5.2', 'prompt_version': 'v2.1', 'temperature': 0.7}
```

### 何时使用实验 Metadata {#when-to-use-experiment-metadata}

Experiment metadata 适合跟踪适用于整次评估运行的配置：

- **模型配置**：模型名称、版本、参数
- **Prompt 版本管理**：使用了哪个 prompt 模板
- **基础设施**：部署环境、region
- **实验上下文**：开发者名称、功能分支、commit hash

当你需要以下能力时，这些 metadata 尤其有价值：

- 随时间比较多次评估运行
- 跟踪哪份配置产生了哪些结果
- 从历史数据复现评估结果

### 在报告中查看 {#viewing-in-reports}

Experiment metadata 会显示在打印报告顶部：

```python
from pydantic_evals import Case, Dataset

dataset = Dataset(name='metadata_report', cases=[Case(inputs='hello', expected_output='HELLO')])


async def task(text: str) -> str:
    return text.upper()

async def main():
    report = await dataset.evaluate(
        task,
        metadata={'model': 'gpt-5.2', 'version': 'v1.0'},
    )

    print(report.render())
    """
    ╭─ Evaluation Summary: task ─╮
    │ model: gpt-5.2             │
    │ version: v1.0              │
    ╰────────────────────────────╯
    ┏━━━━━━━━━━┳━━━━━━━━━━┓
    ┃ Case ID  ┃ Duration ┃
    ┡━━━━━━━━━━╇━━━━━━━━━━┩
    │ Case 1   │     10ms │
    ├──────────┼──────────┤
    │ Averages │     10ms │
    └──────────┴──────────┘
    """
```

## 任务与实验 Metadata 之间的同步 {#synchronization-between-tasks-and-experiment-metadata}

Experiment metadata 用于*记录*配置，而不是*配置*任务。
metadata dict 不会自动配置任务行为；你必须确保 metadata dict 中的值与任务实际使用的值一致。
例如，metadata 可能不小心声明 `temperature: 0.7`，而任务实际使用的是 `temperature: 1.0`，这会导致实验跟踪不准确且结果不可复现。

为了避免这个问题，我们建议建立一个配置的单一事实来源，让任务和 metadata 都引用它。
下面是一些实现这种同步的建议模式。

### 模式 1：共享模块常量 {#pattern-1-shared-module-constants}

对于较简单的场景，可以使用模块级常量：

```python
from pydantic_ai import Agent
from pydantic_evals import Case, Dataset

# Module constants as single source of truth
MODEL_NAME = 'openai:gpt-5-mini'
TEMPERATURE = 0.7
INSTRUCTIONS = 'You are a helpful assistant.'

agent = Agent(MODEL_NAME, model_settings={'temperature': TEMPERATURE}, instructions=INSTRUCTIONS)


async def task(inputs: str) -> str:
    result = await agent.run(inputs)
    return result.output


async def main():
    dataset = Dataset(name='shared_constants', cases=[Case(inputs='What is the capital of France?')])

    # Metadata references same constants
    await dataset.evaluate(
        task,
        metadata={
            'model': MODEL_NAME,
            'temperature': TEMPERATURE,
            'instructions': INSTRUCTIONS,
        },
    )
```

### 模式 2：配置对象（推荐） {#pattern-2-configuration-object-recommended}

只定义一次配置，并在所有地方使用：

```python
from dataclasses import asdict, dataclass

from pydantic_ai import Agent
from pydantic_evals import Case, Dataset


@dataclass
class TaskConfig:
    """Single source of truth for task configuration.

    Includes all variables you'd like to see in experiment metadata.
    """

    model: str
    temperature: float
    max_tokens: int
    prompt_version: str


# Define configuration once
config = TaskConfig(
    model='openai:gpt-5-mini',
    temperature=0.7,
    max_tokens=500,
    prompt_version='v2.1',
)

# Use config in task
agent = Agent(
    config.model,
    model_settings={'temperature': config.temperature, 'max_tokens': config.max_tokens},
)


async def task(inputs: str) -> str:
    """Task uses the same config that's recorded in metadata."""
    result = await agent.run(inputs)
    return result.output


# Evaluate with metadata derived from the same config
async def main():
    dataset = Dataset(name='config_evaluation', cases=[Case(inputs='What is the capital of France?')])

    report = await dataset.evaluate(
        task,
        metadata=asdict(config),  # Guaranteed to match task behavior
    )

    print(report.experiment_metadata)
    """
    {
        'model': 'openai:gpt-5-mini',
        'temperature': 0.7,
        'max_tokens': 500,
        'prompt_version': 'v2.1',
    }
    """
```

如果全局任务配置不合适，也可以在任务调用位置创建 `TaskConfig` 对象，并通过 `deps` 或类似机制传给 agent；但这种情况下你仍需保证该值始终与传给 `Dataset.evaluate` 的 `metadata` 中的值相同。

### 反模式：重复配置 {#anti-pattern-duplicate-configuration}

**避免这个常见错误**：

```python
from pydantic_ai import Agent
from pydantic_evals import Case, Dataset

# ❌ BAD: Configuration defined in multiple places
agent = Agent('openai:gpt-5-mini', model_settings={'temperature': 0.7})


async def task(inputs: str) -> str:
    result = await agent.run(inputs)
    return result.output


async def main():
    dataset = Dataset(name='anti_pattern', cases=[Case(inputs='test')])

    # ❌ BAD: Metadata manually typed - easy to get out of sync
    await dataset.evaluate(
        task,
        metadata={
            'model': 'openai:gpt-5-mini',  # Duplicated! Could diverge from agent definition
            'temperature': 0.8,  # ⚠️ WRONG! Task actually uses 0.7
        },
    )
```

在这个反模式中，metadata 声明 `temperature: 0.8`，但任务使用的是 `0.7`。这会导致：

- 实验跟踪不正确
- 无法复现结果
- 比较 runs 时产生困惑
- 浪费时间调试 "为什么结果不同"

## Metrics vs Attributes vs Metadata 指标、属性与元数据 {#metrics-vs-attributes-vs-metadata}

理解它们的差异：

| 功能 | Metrics | Attributes | Case Metadata | Experiment Metadata |
|---------|---------|------------|---------------|---------------------|
| **设置位置** | 任务执行 | 任务执行 | Case 定义 | `evaluate()` 调用 |
| **类型** | int、float | Any | Any | Any |
| **用途** | 定量 | 定性 | 测试数据 | 实验配置 |
| **用于** | 聚合 | 上下文 | 任务输入 | 跟踪 runs |
| **可供谁使用** | Evaluators | Evaluators | 任务和 Evaluators | 仅报告 |
| **作用域** | 每个 case | 每个 case | 每个 case | 每个实验 |

```python
from pydantic_evals import Case, Dataset, increment_eval_metric, set_eval_attribute

# Case Metadata: Defined in case (before execution)
case = Case(
    inputs='question',
    metadata={'difficulty': 'hard', 'category': 'math'},  # Per-case metadata
)

dataset = Dataset(name='metrics_demo', cases=[case])


# Metrics & Attributes: Recorded during execution
async def task(inputs):
    # These are recorded during execution for each case
    increment_eval_metric('tokens', 100)
    set_eval_attribute('model', 'gpt-5.2')
    return f'Result: {inputs}'


async def main():
    # Experiment Metadata: Defined at evaluation time
    await dataset.evaluate(
        task,
        metadata={  # Experiment-level metadata
            'prompt_version': 'v2.1',
            'temperature': 0.7,
        },
    )
```

## 故障排除 {#troubleshooting}

### "Metrics/attributes 没有出现" {#metricsattributes-not-appearing}

确保你在任务内部调用这些函数：

```python
from pydantic_evals import increment_eval_metric


def process(inputs: str) -> str:
    return f'Processed: {inputs}'


# Bad: Called outside task
increment_eval_metric('count', 1)


def bad_task(inputs):
    return process(inputs)


# Good: Called inside task
def good_task(inputs):
    increment_eval_metric('count', 1)
    return process(inputs)
```

### "Metrics 没有递增" {#metrics-not-incrementing}

检查你使用的是 `increment_eval_metric`，而不是 `set_eval_attribute`：

```python
from pydantic_evals import increment_eval_metric, set_eval_attribute

# Bad: This will overwrite, not increment
set_eval_attribute('count', 1)
set_eval_attribute('count', 1)  # Still 1

# Good: This increments
increment_eval_metric('count', 1)
increment_eval_metric('count', 1)  # Now 2
```

### "Attributes 中的数据太多" {#too-much-data-in-attributes}

存储摘要，而不是原始数据：

```python
from pydantic_evals import set_eval_attribute

giant_response_object = {'key' + str(i): 'value' * 100 for i in range(1000)}

# Bad: Huge object
set_eval_attribute('full_response', giant_response_object)

# Good: Summary
set_eval_attribute('response_size_kb', len(str(giant_response_object)) / 1024)
set_eval_attribute('response_keys', list(giant_response_object.keys())[:10])  # First 10 keys
```

## 下一步 {#next-steps}

- **[Case 生命周期 Hooks](lifecycle.md)** - 每个 case 的 setup、teardown 和 context 准备
- **[自定义 Evaluators](../evaluators/custom.md)** - 在 evaluators 中使用 metrics/attributes
- **[Logfire 集成](logfire-integration.md)** - 在 Logfire 中查看 metrics
- **[并发与性能](concurrency.md)** - 优化评估性能
