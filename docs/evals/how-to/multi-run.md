# 多次运行评估

多次运行每个 case，以衡量波动性并获得更可靠的聚合结果。

## 概览

AI 系统天然具有随机性，同一输入在多次运行中可能产生不同输出。`repeat` 参数允许你多次运行每个 case，并自动聚合结果，从而更清楚地了解系统的典型行为。

## 基本用法

将 `repeat` 传给 [`evaluate()`][pydantic_evals.dataset.Dataset.evaluate] 或 [`evaluate_sync()`][pydantic_evals.dataset.Dataset.evaluate_sync]：

```python
from pydantic_evals import Case, Dataset

dataset = Dataset(
    name='multi_run_basic',
    cases=[
        Case(name='greeting', inputs='Say hello'),
        Case(name='farewell', inputs='Say goodbye'),
    ]
)


def task(inputs: str) -> str:
    return inputs.upper()


# Run each case 5 times
report = dataset.evaluate_sync(task, repeat=5)

# 2 cases × 5 repeats = 10 total runs
print(len(report.cases))
#> 10
```

当 `repeat > 1` 时，每次运行都会获得类似 `greeting [1/5]`、`greeting [2/5]` 的带索引名称，同时原始 case 名称会保存在 [`source_case_name`][pydantic_evals.reporting.ReportCase.source_case_name] 中用于分组。

## 访问分组结果

使用 [`case_groups()`][pydantic_evals.reporting.EvaluationReport.case_groups] 访问按原始 case 组织的运行结果，以及每组的聚合统计：

```python
from pydantic_evals import Case, Dataset

dataset = Dataset(
    name='grouped_results',
    cases=[
        Case(name='greeting', inputs='Say hello'),
        Case(name='farewell', inputs='Say goodbye'),
    ]
)


def task(inputs: str) -> str:
    return inputs.upper()


report = dataset.evaluate_sync(task, repeat=3)

groups = report.case_groups()
assert groups is not None  # None for single-run (repeat=1)

print(len(groups))
#> 2

group_names = [g.name for g in groups]
print(group_names)
#> ['greeting', 'farewell']

# Each group has 3 runs and aggregated statistics
for group in groups:
    assert len(group.runs) == 3
    assert len(group.failures) == 0
    assert group.summary.task_duration > 0
```

每个 [`ReportCaseGroup`][pydantic_evals.reporting.ReportCaseGroup] 包含：

- `name`，原始 case 名称
- `runs`，单个 [`ReportCase`][pydantic_evals.reporting.ReportCase] 结果
- `failures`，所有抛出异常的运行
- `summary`，包含平均分数、指标、标签、断言和耗时的 [`ReportCaseAggregate`][pydantic_evals.reporting.ReportCaseAggregate]

## 聚合

当 `repeat > 1` 时，报告的 [`averages()`][pydantic_evals.reporting.EvaluationReport.averages] 会使用两级聚合策略：

1. **组内平均**：将每个 case 的运行结果平均为组摘要
2. **跨组平均**：将各组摘要平均为最终结果

这可确保每个原始 case 对整体平均值的贡献相同，而不受成功或失败运行次数影响。

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected

dataset = Dataset(
    name='aggregation',
    cases=[
        Case(name='easy', inputs='hello', expected_output='HELLO'),
        Case(name='hard', inputs='world', expected_output='WORLD'),
    ],
    evaluators=[EqualsExpected()],
)


def task(inputs: str) -> str:
    return inputs.upper()


report = dataset.evaluate_sync(task, repeat=3)

averages = report.averages()
assert averages is not None
print(f'Overall assertion rate: {averages.assertions}')
#> Overall assertion rate: 1.0
```

## 默认行为

当 `repeat=1`（默认值）时，行为与标准评估完全相同：没有运行索引，没有 `source_case_name`，且 `case_groups()` 返回 `None`：

```python
from pydantic_evals import Case, Dataset

dataset = Dataset(name='default_behavior', cases=[Case(name='test', inputs='hello')])


def task(inputs: str) -> str:
    return inputs.upper()


report = dataset.evaluate_sync(task)  # repeat=1 by default

assert report.case_groups() is None
assert all(c.source_case_name is None for c in report.cases)
```

## 下一步

- **[并发与性能](concurrency.md)**，使用 `max_concurrency` 控制并行执行
- **[指标与属性](metrics-attributes.md)**，跨运行跟踪自定义指标
- **[Logfire 集成](logfire-integration.md)**，可视化多次运行结果
