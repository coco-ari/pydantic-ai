# 报告评估器 {#report-evaluators}

报告评估器分析整个实验结果，而不是单个 cases。可以用它们计算实验级统计信息，例如混淆矩阵、precision-recall 曲线、准确率分数，或自定义汇总表。

## 报告评估器如何工作 {#how-report-evaluators-work}

常规 [evaluators](overview.md) 会为每个 case 运行一次，并评估单个输出。
报告评估器会在所有 cases 完成评估_之后_，每个实验运行一次，并接收完整的 [`EvaluationReport`][pydantic_evals.reporting.EvaluationReport] 作为输入。

```
执行 Cases → 运行 Case 评估器 → 运行报告评估器 → 生成最终报告
```

报告评估器的结果会作为 **analyses** 存储在 report 上；如果配置了 Logfire，还会作为结构化 attributes 附加到 experiment span，用于可视化。

## 使用报告评估器 {#using-report-evaluators}

通过 `report_evaluators` 参数把报告评估器传给 `Dataset`：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import ConfusionMatrixEvaluator


def my_classifier(text: str) -> str:
    text = text.lower()
    if 'cat' in text or 'meow' in text:
        return 'cat'
    elif 'dog' in text or 'bark' in text:
        return 'dog'
    return 'unknown'


dataset = Dataset(
    name='animal_classifier',
    cases=[
        Case(name='cat', inputs='The cat goes meow', expected_output='cat'),
        Case(name='dog', inputs='The dog barks', expected_output='dog'),
    ],
    report_evaluators=[
        ConfusionMatrixEvaluator(
            predicted_from='output',
            expected_from='expected_output',
            title='Animal Classification',
        ),
    ],
)

report = dataset.evaluate_sync(my_classifier)
# report.analyses 包含 ConfusionMatrix 结果
```

## 原生报告评估器 {#native-report-evaluators}

### ConfusionMatrixEvaluator 混淆矩阵评估器 {#confusionmatrixevaluator}

在所有 cases 上构建混淆矩阵，对比预测标签和预期标签。

```python
from pydantic_evals.evaluators import ConfusionMatrixEvaluator

ConfusionMatrixEvaluator(
    predicted_from='output',
    expected_from='expected_output',
    title='My Confusion Matrix',
)
```

**参数：**

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `predicted_from` | `'expected_output' \| 'output' \| 'metadata' \| 'labels'` | `'output'` | 预测值来源 |
| `predicted_key` | `str \| None` | `None` | 使用 `metadata` 或 `labels` 时提取的 key |
| `expected_from` | `'expected_output' \| 'output' \| 'metadata' \| 'labels'` | `'expected_output'` | 预期/真实值来源 |
| `expected_key` | `str \| None` | `None` | 使用 `metadata` 或 `labels` 时提取的 key |
| `title` | `str` | `'Confusion Matrix'` | 报告中显示的标题 |

**返回：** [`ConfusionMatrix`][pydantic_evals.reporting.analyses.ConfusionMatrix]

**数据来源：**

- `'output'` - 任务的实际输出（转换为字符串）
- `'expected_output'` - case 的 expected output（转换为字符串）
- `'metadata'` - 来自 case metadata dict 的值（需要 `key`）
- `'labels'` - 来自 case-level evaluator 的 label result（需要 `key`）

**示例 - 使用 expected outputs 做分类：**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import ConfusionMatrixEvaluator

dataset = Dataset(
    name='animal_sounds',
    cases=[
        Case(inputs='meow', expected_output='cat'),
        Case(inputs='woof', expected_output='dog'),
        Case(inputs='chirp', expected_output='bird'),
    ],
    report_evaluators=[
        ConfusionMatrixEvaluator(
            predicted_from='output',
            expected_from='expected_output',
        ),
    ],
)
```

**示例 - 使用 evaluator labels：**

如果 case-level evaluator 生成了类似 `predicted_class` 的 label，你可以引用它：

```python
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import (
    ConfusionMatrixEvaluator,
    Evaluator,
    EvaluatorContext,
)


@dataclass
class ClassifyOutput(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> dict[str, str]:
        # Classify the output into a category
        return {'predicted_class': categorize(ctx.output)}


def categorize(output: str) -> str:
    return 'positive' if 'good' in output.lower() else 'negative'


dataset = Dataset(
    name='labels_example',
    cases=[Case(inputs='test', expected_output='positive')],
    evaluators=[ClassifyOutput()],
    report_evaluators=[
        ConfusionMatrixEvaluator(
            predicted_from='labels',
            predicted_key='predicted_class',
            expected_from='expected_output',
        ),
    ],
)
```

---

### PrecisionRecallEvaluator 精确率-召回率评估器 {#precisionrecallevaluator}

根据数值分数和二元真实标签计算带 AUC（曲线下面积）的 precision-recall 曲线。

```python
from pydantic_evals.evaluators import PrecisionRecallEvaluator

PrecisionRecallEvaluator(
    score_from='scores',
    score_key='confidence',
    positive_from='assertions',
    positive_key='is_correct',
)
```

**参数：**

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `score_key` | `str` | _（必需）_ | scores 或 metrics 字典中的 key |
| `positive_from` | `'expected_output' \| 'assertions' \| 'labels'` | _（必需）_ | 二元真实标签的来源 |
| `positive_key` | `str \| None` | `None` | assertions 或 labels dict 中的 key |
| `score_from` | `'scores' \| 'metrics'` | `'scores'` | 数值分数的来源 |
| `title` | `str` | `'Precision-Recall Curve'` | 报告中显示的标题 |
| `n_thresholds` | `int` | `100` | 曲线上的阈值点数量 |

**返回：** [`PrecisionRecall`][pydantic_evals.reporting.analyses.PrecisionRecall] + [`ScalarResult`][pydantic_evals.reporting.analyses.ScalarResult]（AUC）

为了准确性，AUC 会以完整分辨率计算（使用每个唯一分数作为阈值），
然后将曲线点下采样到 `n_thresholds` 用于显示。AUC 会同时返回到曲线（用于图表渲染）和单独的 `ScalarResult`（用于查询和排序）。

**Score 来源：**

- `'scores'` - 来自 case-level evaluator 的数值分数（通过 `score_key` 查找）
- `'metrics'` - 任务执行期间设置的自定义指标（通过 `score_key` 查找）

**Positive 来源：**

- `'assertions'` - 来自 case-level evaluator 的布尔断言（通过 `positive_key` 查找）
- `'labels'` - 转换为布尔值的 label result（通过 `positive_key` 查找）
- `'expected_output'` - 转换为布尔值的 case expected output

**示例：**

```python
from dataclasses import dataclass
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import (
    Evaluator,
    EvaluatorContext,
    PrecisionRecallEvaluator,
)


@dataclass
class ConfidenceEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> dict[str, Any]:
        confidence = calculate_confidence(ctx.output)
        return {
            'confidence': confidence,      # numeric score
            'is_correct': ctx.output == ctx.expected_output,  # boolean assertion
        }


def calculate_confidence(output: str) -> float:
    return 0.85  # placeholder


dataset = Dataset(
    name='precision_recall_example',
    cases=[
        Case(inputs='test 1', expected_output='cat'),
        Case(inputs='test 2', expected_output='dog'),
    ],
    evaluators=[ConfidenceEvaluator()],
    report_evaluators=[
        PrecisionRecallEvaluator(
            score_from='scores',
            score_key='confidence',
            positive_from='assertions',
            positive_key='is_correct',
        ),
    ],
)
```

---

### ROCAUCEvaluator ROC AUC 评估器 {#rocaucevaluator}

根据数值分数和二元真实标签计算 ROC（Receiver Operating Characteristic）曲线和 AUC。ROC 曲线会在不同阈值下绘制真正率与假正率，并带有一条虚线随机基线对角线供参考。

```python
from pydantic_evals.evaluators import ROCAUCEvaluator

ROCAUCEvaluator(
    score_key='confidence',
    positive_from='assertions',
    positive_key='is_correct',
)
```

**参数：**

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `score_key` | `str` | _（必需）_ | scores 或 metrics 字典中的 key |
| `positive_from` | `'expected_output' \| 'assertions' \| 'labels'` | _（必需）_ | 二元真实标签的来源 |
| `positive_key` | `str \| None` | `None` | assertions 或 labels dict 中的 key |
| `score_from` | `'scores' \| 'metrics'` | `'scores'` | 数值分数的来源 |
| `title` | `str` | `'ROC Curve'` | 报告中显示的标题 |
| `n_thresholds` | `int` | `100` | 曲线上的阈值点数量 |

**返回：** [`LinePlot`][pydantic_evals.reporting.analyses.LinePlot] + [`ScalarResult`][pydantic_evals.reporting.analyses.ScalarResult]（AUC）

AUC 会以完整分辨率计算。图表包含一条从 (0, 0) 到 (1, 1) 的虚线 "Random" 基线，便于视觉对比。

**Score 和 Positive 来源：** 与 [`PrecisionRecallEvaluator`](#precisionrecallevaluator) 相同。

---

### KolmogorovSmirnovEvaluator Kolmogorov-Smirnov 评估器 {#kolmogorovsmirnovevaluator}

根据数值分数和二元真实标签计算 Kolmogorov-Smirnov 图和 KS 统计量。KS 图展示正例和反例分数分布的经验 CDFs（累积分布函数）。KS 统计量是两条 CDFs 之间的最大垂直距离；值越高，表示类别分离越好。

```python
from pydantic_evals.evaluators import KolmogorovSmirnovEvaluator

KolmogorovSmirnovEvaluator(
    score_key='confidence',
    positive_from='assertions',
    positive_key='is_correct',
)
```

**参数：**

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `score_key` | `str` | _（必需）_ | scores 或 metrics 字典中的 key |
| `positive_from` | `'expected_output' \| 'assertions' \| 'labels'` | _（必需）_ | 二元真实标签的来源 |
| `positive_key` | `str \| None` | `None` | assertions 或 labels dict 中的 key |
| `score_from` | `'scores' \| 'metrics'` | `'scores'` | 数值分数的来源 |
| `title` | `str` | `'KS Plot'` | 报告中显示的标题 |
| `n_thresholds` | `int` | `100` | 曲线上的阈值点数量 |

**返回：** [`LinePlot`][pydantic_evals.reporting.analyses.LinePlot] + [`ScalarResult`][pydantic_evals.reporting.analyses.ScalarResult]（KS Statistic）

**Score 和 Positive 来源：** 与 [`PrecisionRecallEvaluator`](#precisionrecallevaluator) 相同。

---

## 自定义报告评估器 {#custom-report-evaluators}

通过继承 [`ReportEvaluator`][pydantic_evals.evaluators.ReportEvaluator] 并实现 `evaluate` 方法来编写自定义报告评估器：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import ReportEvaluator, ReportEvaluatorContext
from pydantic_evals.reporting.analyses import ScalarResult


@dataclass
class AccuracyEvaluator(ReportEvaluator):
    """Computes overall accuracy as a scalar metric."""

    def evaluate(self, ctx: ReportEvaluatorContext) -> ScalarResult:
        cases = ctx.report.cases
        if not cases:
            return ScalarResult(title='Accuracy', value=0.0, unit='%')

        correct = sum(
            1 for case in cases
            if case.output == case.expected_output
        )
        accuracy = correct / len(cases) * 100
        return ScalarResult(title='Accuracy', value=accuracy, unit='%')
```

### ReportEvaluatorContext 上下文 {#reportevaluatorcontext}

传给 `evaluate()` 的上下文包含：

- `ctx.name` - 实验名称
- `ctx.report` - 包含所有 case results 的完整 [`EvaluationReport`][pydantic_evals.reporting.EvaluationReport]
- `ctx.experiment_metadata` - 可选的实验级 metadata 字典

通过 `ctx.report.cases`，你可以访问每个 case 的 inputs、outputs、expected outputs、scores、labels、assertions、metrics 和 attributes。

### 返回类型 {#return-types}

报告评估器必须返回 `ReportAnalysis` 或 `list[ReportAnalysis]`。可用的分析类型包括：

#### ScalarResult 标量结果 {#scalarresult}

单个数值统计量：

```python
from pydantic_evals.reporting.analyses import ScalarResult

ScalarResult(
    title='Accuracy',
    value=93.3,
    unit='%',
    description='Percentage of correctly classified cases.',
)
```

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `title` | `str` | 显示名称 |
| `value` | `float \| int` | 数值 |
| `unit` | `str \| None` | 可选单位标签（例如 `'%'`、`'ms'`） |
| `description` | `str \| None` | 可选的较长描述 |

---

#### TableResult 表格结果 {#tableresult}

通用数据表：

```python
from pydantic_evals.reporting.analyses import TableResult

TableResult(
    title='Per-Class Metrics',
    columns=['Class', 'Precision', 'Recall', 'F1'],
    rows=[
        ['cat', 0.95, 0.90, 0.924],
        ['dog', 0.88, 0.92, 0.899],
    ],
    description='Precision, recall, and F1 per class.',
)
```

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `title` | `str` | 显示名称 |
| `columns` | `list[str]` | 列表头 |
| `rows` | `list[list[str \| int \| float \| bool \| None]]` | 行数据 |
| `description` | `str \| None` | 可选的较长描述 |

---

#### ConfusionMatrix 混淆矩阵 {#confusionmatrix}

混淆矩阵（通常由 `ConfusionMatrixEvaluator` 生成，但也可以直接构造）：

```python
from pydantic_evals.reporting.analyses import ConfusionMatrix

ConfusionMatrix(
    title='Sentiment',
    class_labels=['positive', 'negative', 'neutral'],
    matrix=[
        [45, 3, 2],   # expected=positive
        [5, 40, 5],   # expected=negative
        [1, 2, 47],   # expected=neutral
    ],
)
```

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `title` | `str` | 显示名称 |
| `class_labels` | `list[str]` | 两个轴上的有序 labels |
| `matrix` | `list[list[int]]` | `matrix[expected][predicted]` = 计数 |
| `description` | `str \| None` | 可选的较长描述 |

---

#### PrecisionRecall 精确率-召回率 {#precisionrecall}

Precision-recall 曲线数据（通常由 `PrecisionRecallEvaluator` 生成）：

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `title` | `str` | 显示名称 |
| `curves` | `list[PrecisionRecallCurve]` | 一条或多条曲线 |
| `description` | `str \| None` | 可选的较长描述 |

每个 `PrecisionRecallCurve` 包含一个 `name`、一个 `PrecisionRecallPoint`s 列表（带 `threshold`、`precision`、`recall`），以及一个可选 `auc` 值。

---

#### LinePlot 折线图 {#lineplot}

带标注坐标轴的通用 XY 折线图，支持多条曲线。可用于 ROC 曲线、KS 图、校准曲线，或任何自定义折线图：

```python
from pydantic_evals.reporting.analyses import LinePlot, LinePlotCurve, LinePlotPoint

LinePlot(
    title='ROC Curve',
    x_label='False Positive Rate',
    y_label='True Positive Rate',
    x_range=(0, 1),
    y_range=(0, 1),
    curves=[
        LinePlotCurve(
            name='Model (AUC: 0.95)',
            points=[LinePlotPoint(x=0.0, y=0.0), LinePlotPoint(x=0.1, y=0.8), LinePlotPoint(x=1.0, y=1.0)],
        ),
        LinePlotCurve(
            name='Random',
            points=[LinePlotPoint(x=0, y=0), LinePlotPoint(x=1, y=1)],
            style='dashed',
        ),
    ],
)
```

| 字段 | 类型 | 描述 |
|-------|------|-------------|
| `title` | `str` | 显示名称 |
| `x_label` | `str` | x 轴标签 |
| `y_label` | `str` | y 轴标签 |
| `x_range` | `tuple[float, float] \| None` | 可选的 x 轴固定范围 |
| `y_range` | `tuple[float, float] \| None` | 可选的 y 轴固定范围 |
| `curves` | `list[LinePlotCurve]` | 要绘制的一条或多条曲线 |
| `description` | `str \| None` | 可选的较长描述 |

每个 `LinePlotCurve` 包含一个 `name`、一个 `LinePlotPoint`s 列表（带 `x`、`y`）、一个可选 `style`（`'solid'` 或 `'dashed'`），以及用于经验 CDFs 这类阶梯函数的可选 `step` 插值模式（`'start'`、`'middle'` 或 `'end'`）。

`LinePlot` 是自定义曲线类评估器的推荐返回类型；任何返回 `LinePlot` 的 evaluator 都会在 Logfire UI 中渲染为折线图，无需任何前端变更。

### 返回多个分析结果 {#returning-multiple-analyses}

单个报告评估器可以通过返回列表来返回多个分析结果：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import ReportEvaluator, ReportEvaluatorContext
from pydantic_evals.reporting.analyses import ReportAnalysis, ScalarResult, TableResult


@dataclass
class ClassificationSummary(ReportEvaluator):
    """Produces both a scalar accuracy and a per-class metrics table."""

    def evaluate(self, ctx: ReportEvaluatorContext) -> list[ReportAnalysis]:
        cases = ctx.report.cases
        if not cases:
            return []

        labels = sorted({str(c.expected_output) for c in cases if c.expected_output})

        # Scalar: overall accuracy
        correct = sum(1 for c in cases if c.output == c.expected_output)
        accuracy = ScalarResult(
            title='Accuracy', value=correct / len(cases) * 100, unit='%'
        )

        # Table: per-class breakdown
        rows = []
        for label in labels:
            tp = sum(1 for c in cases if str(c.output) == label and str(c.expected_output) == label)
            fp = sum(1 for c in cases if str(c.output) == label and str(c.expected_output) != label)
            fn = sum(1 for c in cases if str(c.output) != label and str(c.expected_output) == label)
            p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
            rows.append([label, round(p, 3), round(r, 3), round(f1, 3)])

        table = TableResult(
            title='Per-Class Metrics',
            columns=['Class', 'Precision', 'Recall', 'F1'],
            rows=rows,
        )

        return [accuracy, table]
```

### 异步报告评估器 {#async-report-evaluators}

报告评估器支持 async `evaluate` 方法，并会通过 `evaluate_async` 自动处理：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import ReportEvaluator, ReportEvaluatorContext
from pydantic_evals.reporting.analyses import ScalarResult


@dataclass
class AsyncAccuracy(ReportEvaluator):
    async def evaluate(self, ctx: ReportEvaluatorContext) -> ScalarResult:
        # Can use async I/O here (e.g., call an external API)
        cases = ctx.report.cases
        correct = sum(1 for c in cases if c.output == c.expected_output)
        return ScalarResult(
            title='Accuracy',
            value=correct / len(cases) * 100 if cases else 0.0,
            unit='%',
        )
```

## 序列化 {#serialization}

报告评估器会使用与 case-level evaluators 相同的格式序列化到 YAML/JSON dataset files，也会从这些文件反序列化。这意味着带报告评估器的 datasets 可以完整地通过文件序列化往返。

**带报告评估器的 YAML dataset 示例：**

```yaml
# yaml-language-server: $schema=./test_cases_schema.json
name: classifier_eval
cases:
  - name: cat_test
    inputs: The cat meows
    expected_output: cat
  - name: dog_test
    inputs: The dog barks
    expected_output: dog
report_evaluators:
  - ConfusionMatrixEvaluator
  - PrecisionRecallEvaluator:
      score_key: confidence
      positive_from: assertions
      positive_key: is_correct
```

原生报告评估器（`ConfusionMatrixEvaluator`、`PrecisionRecallEvaluator`、`ROCAUCEvaluator`、`KolmogorovSmirnovEvaluator`）会被自动识别。对于自定义报告评估器，请通过 `custom_report_evaluator_types` 传入：

```python {test="skip" lint="skip"}
from pydantic_evals import Dataset

dataset = Dataset[str, str, None].from_file(
    'test_cases.yaml',
    custom_report_evaluator_types=[MyCustomReportEvaluator],
)
```

类似地，保存带自定义报告评估器的 dataset 时，也需要把它们传给 `to_file`，这样 JSON schema 才会包含它们：

```python {test="skip" lint="skip"}
dataset.to_file(
    'test_cases.yaml',
    custom_report_evaluator_types=[MyCustomReportEvaluator],
)
```

## 在 Logfire 中查看分析结果 {#viewing-analyses-in-logfire}

配置 [Logfire](../how-to/logfire-integration.md) 后，分析结果会自动作为 `logfire.experiment.analyses` attribute 附加到 experiment span。Logfire UI 会把它们渲染为交互式可视化：

- **混淆矩阵** 显示为热力图
- **Precision-recall 曲线** 渲染为折线图，并在图例中显示 AUC
- **Line plots**（ROC 曲线、KS 图等）渲染为带可配置坐标轴的折线图
- **Scalar results** 显示为带标签的值
- **Tables** 渲染为格式化数据表

在 Logfire Evals 视图中比较多个 experiments 时，同类型分析结果会并排显示，便于比较。

## 完整示例 {#complete-example}

一个结合 case-level evaluators 和报告评估器的完整示例：

```python
from dataclasses import dataclass
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import (
    ConfusionMatrixEvaluator,
    Evaluator,
    EvaluatorContext,
    KolmogorovSmirnovEvaluator,
    PrecisionRecallEvaluator,
    ReportEvaluator,
    ReportEvaluatorContext,
    ROCAUCEvaluator,
)
from pydantic_evals.reporting.analyses import ScalarResult


def my_classifier(text: str) -> str:
    text = text.lower()
    if 'cat' in text or 'meow' in text:
        return 'cat'
    elif 'dog' in text or 'bark' in text:
        return 'dog'
    elif 'bird' in text or 'chirp' in text:
        return 'bird'
    return 'unknown'


# Case-level evaluator: runs per case
@dataclass
class ConfidenceEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> dict[str, Any]:
        confidence = compute_confidence(ctx.output, ctx.inputs)
        is_correct = ctx.output == ctx.expected_output
        return {
            'confidence': confidence,
            'is_correct': is_correct,
        }


def compute_confidence(output: str, inputs: str) -> float:
    return 0.85  # placeholder


# Report-level evaluator: runs once over the full report
@dataclass
class AccuracyEvaluator(ReportEvaluator):
    def evaluate(self, ctx: ReportEvaluatorContext) -> ScalarResult:
        cases = ctx.report.cases
        correct = sum(1 for c in cases if c.output == c.expected_output)
        return ScalarResult(
            title='Accuracy',
            value=correct / len(cases) * 100 if cases else 0.0,
            unit='%',
        )


dataset = Dataset(
    name='full_example',
    cases=[
        Case(inputs='The cat meows', expected_output='cat'),
        Case(inputs='The dog barks', expected_output='dog'),
        Case(inputs='A bird chirps', expected_output='bird'),
    ],
    evaluators=[ConfidenceEvaluator()],
    report_evaluators=[
        ConfusionMatrixEvaluator(
            predicted_from='output',
            expected_from='expected_output',
            title='Animal Classification',
        ),
        PrecisionRecallEvaluator(
            score_from='scores',
            score_key='confidence',
            positive_from='assertions',
            positive_key='is_correct',
        ),
        ROCAUCEvaluator(
            score_from='scores',
            score_key='confidence',
            positive_from='assertions',
            positive_key='is_correct',
        ),
        KolmogorovSmirnovEvaluator(
            score_from='scores',
            score_key='confidence',
            positive_from='assertions',
            positive_key='is_correct',
        ),
        AccuracyEvaluator(),
    ],
)

report = dataset.evaluate_sync(my_classifier)

# Access analyses programmatically
for analysis in report.analyses:
    print(f'{analysis.type}: {analysis.title}')
    #> confusion_matrix: Animal Classification
    #> precision_recall: Precision-Recall Curve
    #> scalar: Precision-Recall Curve AUC
    #> line_plot: ROC Curve
    #> scalar: ROC Curve AUC
    #> line_plot: KS Plot
    #> scalar: KS Statistic
    #> scalar: Accuracy
```

## 下一步 {#next-steps}

- **[原生 Evaluators](built-in.md)** - Case-level evaluator reference
- **[自定义 Evaluators](custom.md)** - 编写 case-level evaluators
- **[Logfire 集成](../how-to/logfire-integration.md)** - 在 Logfire UI 中查看 analyses
