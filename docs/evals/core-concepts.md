# 核心概念 {#core-concepts}

本页解释 Pydantic Evals 中的关键概念，以及它们如何协同工作。

## 概览 {#overview}

Pydantic Evals 围绕以下核心概念构建：

- **[`Dataset`][pydantic_evals.dataset.Dataset]** - 包含测试 cases 和 evaluators 的静态定义
- **[`Case`][pydantic_evals.dataset.Case]** - 一个带输入和可选预期输出的单个测试场景
- **[`Evaluator`][pydantic_evals.evaluators.Evaluator]** - 为单个输出评分或验证的逻辑
- **[`ReportEvaluator`][pydantic_evals.evaluators.ReportEvaluator]** - 分析完整实验结果的逻辑（例如混淆矩阵、准确率）
- **Experiment** - 针对 dataset 中的所有 cases 运行 task function 的动作。（这对应一次 `Dataset.evaluate` 调用。）
- **[`EvaluationReport`][pydantic_evals.reporting.EvaluationReport]** - 运行 experiment 得到的结果

关键区别在于：

- **定义**（带 `Case`s、`Evaluator`s 和 `ReportEvaluator`s 的 `Dataset`）- 你想测试什么
- **执行**（Experiment）- 针对这些测试运行你的 task
- **结果**（带 case results 和 experiment-wide analyses 的 `EvaluationReport`）- experiment 中发生了什么

## 单元测试类比 {#unit-testing-analogy}

理解 Pydantic Evals 的一个有用方式：

| 单元测试 | Pydantic Evals |
|--------------|----------------|
| Test function | [`Case`][pydantic_evals.dataset.Case] + [`Evaluator`][pydantic_evals.evaluators.Evaluator] |
| Test suite | [`Dataset`][pydantic_evals.dataset.Dataset] |
| 运行 tests（`pytest`） | **Experiment**（`dataset.evaluate(task)`） |
| Test report | [`EvaluationReport`][pydantic_evals.reporting.EvaluationReport] |
| `assert` | 返回 `bool` 的 Evaluator |

**关键区别**：AI 系统是概率性的，因此 evaluation 不只是简单的通过/失败，还可以包含：

- 定量分数（0.0 到 1.0）
- 定性标签（"good"、"acceptable"、"poor"）
- 带解释原因的通过/失败断言

就像你可以在同一个 test suite 上多次运行 `pytest` 一样，你也可以在同一个 dataset 上运行多个 experiments，以比较不同实现或跟踪随时间变化的表现。

## Dataset

[`Dataset`][pydantic_evals.dataset.Dataset] 是一组 test cases 和 evaluators，用于定义一个评估套件。

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance

dataset = Dataset(
    name='my_eval_suite',
    cases=[
        Case(inputs='test input', expected_output='test output'),
    ],
    evaluators=[
        IsInstance(type_name='str'),
    ],
)
```

### 关键特性 {#key-features}

- **类型安全**：对 `InputsT`、`OutputT` 和 `MetadataT` 类型泛型化
- **可序列化**：可保存到 YAML 或 JSON 文件，也可从中加载
- **可评估**：可针对任何输入/输出类型匹配的函数运行

### `Dataset` 级和 `Case` 级 Evaluators {#dataset-level-vs-case-level-evaluators}

Evaluators 可以定义在两个层级：

- **`Dataset` 级**：应用于 dataset 中的所有 cases
- **`Case` 级**：只应用于特定 cases

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected, IsInstance

dataset = Dataset(
    name='case_level_evaluators',
    cases=[
        Case(
            name='special_case',
            inputs='test',
            expected_output='TEST',
            evaluators=[
                # This evaluator only runs for this case
                EqualsExpected(),
            ],
        ),
    ],
    evaluators=[
        # This evaluator runs for ALL cases
        IsInstance(type_name='str'),
    ],
)
```

## Experiments

**Experiment** 是你针对 dataset 中所有 cases 执行 task function 时发生的事情。它连接了静态测试定义（Dataset）和结果（EvaluationReport）。

### 运行 Experiment {#running-an-experiment}

通过在 dataset 上调用 [`evaluate()`][pydantic_evals.dataset.Dataset.evaluate] 或 [`evaluate_sync()`][pydantic_evals.dataset.Dataset.evaluate_sync] 来运行 experiment：

```python
from pydantic_evals import Case, Dataset

# Define your dataset (static definition)
dataset = Dataset(
    name='uppercase_experiment',
    cases=[
        Case(inputs='hello', expected_output='HELLO'),
        Case(inputs='world', expected_output='WORLD'),
    ],
)

# Define your task
def uppercase_task(text: str) -> str:
    return text.upper()

# Run the experiment (execution)
report = dataset.evaluate_sync(uppercase_task)
```

### Experiment 期间会发生什么 {#what-happens-during-an-experiment}

运行 experiment 时：

1. **Setup**：dataset 加载所有 cases、evaluators 和 report evaluators
2. **Execution**：对每个 case：
    1. 使用 `case.inputs` 调用 task function
    2. 计量执行时间并捕获 OpenTelemetry spans（如果配置了 `logfire`）
    3. 记录每个 case 的 task function 输出
3. **Case Evaluation**：对每个 case output：
    1. 运行所有 dataset-level evaluators
    2. 运行 case-specific evaluators（如果有）
    3. 收集结果（scores、assertions、labels）
4. **Report Evaluation**：如果配置了 report evaluators，它们会在完整结果集上运行，生成 experiment-wide analyses（混淆矩阵、precision-recall 曲线、scalar metrics、tables 等）
5. **Reporting**：所有结果会聚合到一个 [`EvaluationReport`][pydantic_evals.reporting.EvaluationReport] 中，其中包含 per-case results 和 experiment-wide analyses

### 从一个 Dataset 运行多个 Experiments {#multiple-experiments-from-one-dataset}

Pydantic Evals 的一个关键特性是，你可以用同一个 dataset 评估不同 task 实现：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected

dataset = Dataset(
    name='comparison_test',
    cases=[
        Case(inputs='hello', expected_output='HELLO'),
    ],
    evaluators=[EqualsExpected()],
)


# Original implementation
def task_v1(text: str) -> str:
    return text.upper()


# Improved implementation (with exclamation)
def task_v2(text: str) -> str:
    return text.upper() + '!'


# Compare results
report_v1 = dataset.evaluate_sync(task_v1)
report_v2 = dataset.evaluate_sync(task_v2)

avg_v1 = report_v1.averages()
avg_v2 = report_v2.averages()
print(f'V1 pass rate: {avg_v1.assertions if avg_v1 and avg_v1.assertions else 0}')
#> V1 pass rate: 1.0
print(f'V2 pass rate: {avg_v2.assertions if avg_v2 and avg_v2.assertions else 0}')
#> V2 pass rate: 0
```

这让你可以：

- **比较实现**的不同版本
- **跟踪性能**随时间变化
- **A/B test** 不同方法
- 在部署前**验证变更**

## Case

[`Case`][pydantic_evals.dataset.Case] 表示一个带具体输入和可选预期输出的单个测试场景。

```python
from pydantic_evals import Case
from pydantic_evals.evaluators import EqualsExpected

case = Case(
    name='test_uppercase',  # Optional, but recommended for reporting
    inputs='hello world',  # Required: inputs to your task
    expected_output='HELLO WORLD',  # Optional: expected output
    metadata={'category': 'basic'},  # Optional: arbitrary metadata
    evaluators=[EqualsExpected()],  # Optional: case-specific evaluators
)
```

### Case 组成部分 {#case-components}

#### 输入 {#inputs}
传给被评估 task 的输入。可以是任意类型：

```python
from pydantic import BaseModel

from pydantic_evals import Case


class MyInputModel(BaseModel):
    field1: str


# Simple types
Case(inputs='hello')
Case(inputs=42)

# Complex types
Case(inputs={'query': 'What is AI?', 'max_tokens': 100})
Case(inputs=MyInputModel(field1='value'))
```

#### 预期输出 {#expected-output}
预期结果，供 [`EqualsExpected`][pydantic_evals.evaluators.EqualsExpected] 等 evaluators 使用：

```python
from pydantic_evals import Case

Case(
    inputs='2 + 2',
    expected_output='4',
)
```

如果没有提供 `expected_output`，依赖它的 evaluators（如 `EqualsExpected`）会跳过该 case。

#### Metadata
Evaluators 可以通过 [`EvaluatorContext`][pydantic_evals.evaluators.EvaluatorContext] 访问的任意数据：

```python
from pydantic_evals import Case

Case(
    inputs='question',
    metadata={
        'difficulty': 'hard',
        'category': 'math',
        'source': 'exam_2024',
    },
)
```

Metadata 可用于：

- 分析时过滤 cases
- 为 evaluators 提供上下文
- 组织 test suites

#### Evaluators

Cases 可以拥有自己的 evaluators，并且这些 evaluators 只会针对该特定 case 运行。这对于构建全面评估套件尤其强大，因为不同 cases 可以有不同需求。如果你能写出一个适用于所有 cases 的 evaluator rubric，那你应该直接把它合并进 agent instructions。Case-specific [`LLMJudge`][pydantic_evals.evaluators.LLMJudge] evaluators 特别适合快速构建可维护的 golden datasets：为每个场景描述 "好" 是什么样。更详细的解释和示例见 [Case-specific evaluators](evaluators/overview.md#case-specific-evaluators)。

## Evaluator

[`Evaluator`][pydantic_evals.evaluators.Evaluator] 评估 task 输出，并返回一个或多个 scores、labels 或 assertions。每个 score、label 或 assertion 也可以关联一个可选的字符串原因。

### Evaluator 类型 {#evaluator-types}

Evaluators 返回不同类型的结果：

| 返回类型 | 用途 | 示例 |
|-------------|---------|---------|
| `bool` | **Assertion** - 通过/失败检查 | `True` → ✔，`False` → ✗ |
| `int` 或 `float` | **Score** - 数值质量指标 | `0.95`、`87` |
| `str` | **Label** - 分类结果 | `"correct"`、`"hallucination"` |

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ExactMatch(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output == ctx.expected_output  # Assertion


@dataclass
class Confidence(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> float:
        # Analyze output and return confidence score
        return 0.95  # Score


@dataclass
class Classifier(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> str:
        if 'error' in ctx.output.lower():
            return 'error'  # Label
        return 'success'
```

Evaluators 还可以返回 [`EvaluationReason`][pydantic_evals.evaluators.EvaluationReason] 实例，以及从 labels 到输出值的字典。
更多细节见[自定义 evaluator 返回类型](evaluators/custom.md#return-types)文档。

### EvaluatorContext

所有 evaluators 都会收到一个 [`EvaluatorContext`][pydantic_evals.evaluators.EvaluatorContext]，其中包含：

- `name`：Case 名称（可选）
- `inputs`：Task 输入
- `metadata`：Case metadata（可选）
- `expected_output`：预期输出（可选）
- `output`：task 实际输出
- `duration`：task 执行时间（秒）
- `span_tree`：OpenTelemetry spans（如果配置了 `logfire`）
- `attributes`：自定义 attributes 字典
- `metrics`：自定义 metrics 字典

### 多个 Evaluations {#multiple-evaluations}

Evaluators 可以通过返回字典来返回多个结果：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class MultiCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | float | str]:
        return {
            'is_valid': isinstance(ctx.output, str),  # Assertion
            'length': len(ctx.output),  # Metric
            'category': 'long' if len(ctx.output) > 100 else 'short',  # Label
        }
```

### Evaluation Reasons

使用 [`EvaluationReason`][pydantic_evals.evaluators.EvaluationReason] 为 evaluations 添加解释：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext


@dataclass
class SmartCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> EvaluationReason:
        if ctx.output == ctx.expected_output:
            return EvaluationReason(
                value=True,
                reason='Exact match with expected output',
            )
        return EvaluationReason(
            value=False,
            reason=f'Expected {ctx.expected_output!r}, got {ctx.output!r}',
        )
```

使用 `include_reasons=True` 时，原因会出现在报告中。

## Evaluation Report

[`EvaluationReport`][pydantic_evals.reporting.EvaluationReport] 是运行 experiment 的结果。它包含针对 dataset cases 执行 task 并运行所有 evaluators 后得到的全部数据。

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected

dataset = Dataset(
    name='report_example',
    cases=[Case(inputs='hello', expected_output='HELLO')],
    evaluators=[EqualsExpected()],
)


def my_task(text: str) -> str:
    return text.upper()


# Run an experiment
report = dataset.evaluate_sync(my_task)

# Print to console
report.print()
"""
    Evaluation Summary: my_task
┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID  ┃ Assertions ┃ Duration ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Case 1   │ ✔          │     10ms │
├──────────┼────────────┼──────────┤
│ Averages │ 100.0% ✔   │     10ms │
└──────────┴────────────┴──────────┘
"""

# Access data programmatically
for case in report.cases:
    print(f'{case.name}: {case.scores}')
    #> Case 1: {}
```

### 报告结构 {#report-structure}

[`EvaluationReport`][pydantic_evals.reporting.EvaluationReport] 包含：

- `name`：Experiment 名称
- `cases`：成功 case evaluations 的列表
- `failures`：失败 executions 的列表
- `analyses`：来自 [report evaluators](evaluators/report-evaluators.md) 的 experiment-wide analyses 列表（混淆矩阵、PR 曲线、scalars、tables）
- `trace_id`：OpenTelemetry trace ID（可选）
- `span_id`：OpenTelemetry span ID（可选）

### ReportCase

每个成功的 case result 都包含：

**Case 数据：**

- `name`：Case 名称
- `inputs`：Task 输入
- `metadata`：Case metadata（可选）
- `expected_output`：预期输出（可选）
- `output`：task 实际输出

**Evaluation 结果：**

- `scores`：来自 evaluators 的数值分数字典
- `labels`：来自 evaluators 的分类标签字典
- `assertions`：来自 evaluators 的通过/失败断言字典

**性能数据：**

- `task_duration`：Task 执行时间
- `total_duration`：包含 evaluators 的总时间

**附加数据：**

- `metrics`：自定义 metrics 字典
- `attributes`：自定义 attributes 字典

**Tracing：**

- `trace_id`：OpenTelemetry trace ID（可选）
- `span_id`：OpenTelemetry span ID（可选）

**错误：**

- `evaluator_failures`：Evaluator 错误列表

## 数据模型关系 {#data-model-relationships}

下面展示核心概念之间的关系：

### 静态定义 {#static-definition}

- 一个 **Dataset** 包含：
  - 多个 **Cases**（带输入和预期输出的测试场景）
  - 多个 **Evaluators**（为单个输出评分的逻辑）
  - 多个 **Report Evaluators**（分析完整实验结果的逻辑）

### 执行（Experiment） {#execution-experiment}

当你调用 `dataset.evaluate(task)` 时，会运行一个 **Experiment**：

- **Task** function 会针对 **Dataset** 中的所有 **Cases** 执行
- 所有 **Evaluators** 会按需针对每个输出运行（包括 dataset-level 和 case-specific）
- 最终输出一个 **EvaluationReport**

### 结果 {#results}

- 一个 **EvaluationReport** 包含：
  - 每个 **Case** 的结果（inputs、outputs、scores、assertions、labels）
  - 来自 report evaluators 的 experiment-wide **Analyses**（混淆矩阵、PR 曲线、scalars、tables）
  - 摘要统计（averages、pass rates）
  - 性能数据（durations）
  - Tracing 信息（OpenTelemetry spans）

### 关键关系 {#key-relationships}

- **一个 Dataset → 多个 Experiments**：你可以用同一个 dataset 评估不同 task 实现，或多次运行来跟踪变化
- **一个 Experiment → 一个 Report**：每次调用 `dataset.evaluate(...)`，都会得到一个 report
- **一个 Experiment → 多个 Case Results**：report 包含 dataset 中每个 case 的结果


## 下一步 {#next-steps}

- **[评估器概览](evaluators/overview.md)** - 何时使用不同 evaluator 类型
- **[原生评估器](evaluators/built-in.md)** - 已提供 evaluators 的完整参考
- **[自定义评估器](evaluators/custom.md)** - 编写你自己的评估逻辑
- **[报告评估器](evaluators/report-evaluators.md)** - Experiment-wide analyses（混淆矩阵、PR 曲线等）
- **[数据集管理](how-to/dataset-management.md)** - 保存、加载和生成 datasets
