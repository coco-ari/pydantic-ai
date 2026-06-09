# Case Lifecycle Hooks 用例生命周期钩子 {#case-lifecycle-hooks}

使用 [`CaseLifecycle`][pydantic_evals.lifecycle.CaseLifecycle] 控制 evaluation 期间每个 case 的 setup、context preparation 和 teardown。

## 概览 {#overview}

[`CaseLifecycle`][pydantic_evals.lifecycle.CaseLifecycle] 在 case evaluation 的每个阶段提供 hooks。你将 lifecycle **类**（不是实例）传给 [`Dataset.evaluate`][pydantic_evals.dataset.Dataset.evaluate]，系统会为每个 case 创建一个新实例，因此实例属性天然可以保存 case-specific state。

## Evaluation 流程 {#evaluation-flow}

每个 case 遵循以下流程：

1. **`setup()`**：在任务执行前调用
2. **任务运行**
3. **`prepare_context()`**：在任务之后、evaluators 之前调用
4. **Evaluators 运行**
5. **`teardown()`**：在 evaluators 完成后调用；如果 case 被中断，则在 cleanup 期间调用

## 每个 Case 的 Setup 和 Teardown {#per-case-setup-and-teardown}

当每个 case 都需要自己的环境时，请使用 `setup()` 和 `teardown()`，例如创建数据库、启动服务，或准备由 case metadata 驱动的 fixtures。由于每个 case 都会创建新的 lifecycle 实例，实例属性天然是 case-scoped：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators.context import EvaluatorContext
from pydantic_evals.lifecycle import CaseLifecycle
from pydantic_evals.reporting import ReportCase, ReportCaseFailure


class SetupFromMetadata(CaseLifecycle[str, str, dict]):
    async def setup(self) -> None:
        prefix = (self.case.metadata or {}).get('prefix', '')
        self.prefix = prefix

    async def prepare_context(
        self, ctx: EvaluatorContext[str, str, dict]
    ) -> EvaluatorContext[str, str, dict]:
        ctx.metrics['prefix_length'] = len(self.prefix)
        return ctx

    async def teardown(
        self,
        result: ReportCase[str, str, dict] | ReportCaseFailure[str, str, dict] | None,
    ) -> None:
        pass  # 在这里清理资源


dataset = Dataset(
    name='setup_teardown',
    cases=[
        Case(name='no_prefix', inputs='hello', metadata={'prefix': ''}),
        Case(name='with_prefix', inputs='hello', metadata={'prefix': 'PREFIX:'}),
    ]
)

report = dataset.evaluate_sync(lambda inputs: inputs.upper(), lifecycle=SetupFromMetadata)

metrics = {c.name: c.metrics for c in report.cases}
print(metrics['no_prefix']['prefix_length'])
#> 0
print(metrics['with_prefix']['prefix_length'])
#> 7
```

case metadata 可以驱动每个 case 的行为，而不需要自定义 [`Case`][pydantic_evals.dataset.Case] 子类或序列化。

### 条件式 Teardown {#conditional-teardown}

`teardown()` hook 会接收完整结果，因此你可以根据成功或失败调整 cleanup 逻辑，例如在 case 失败时保留测试环境以便人工检查。如果 evaluation 在 case 产生报告结果前被中断，`result` 可能是 `None`；当 cleanup 依赖 case 结果时，请处理这个分支：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.lifecycle import CaseLifecycle
from pydantic_evals.reporting import ReportCase, ReportCaseFailure

cleaned_up: list[str] = []


class ConditionalCleanup(CaseLifecycle[str, str, dict]):
    async def setup(self) -> None:
        self.resource_id = self.case.name

    async def teardown(
        self,
        result: ReportCase[str, str, dict] | ReportCaseFailure[str, str, dict] | None,
    ) -> None:
        keep_on_failure = (self.case.metadata or {}).get('keep_on_failure', False)
        if result is None:
            # 异常退出
            cleaned_up.append(self.resource_id)
        elif isinstance(result, ReportCaseFailure) and keep_on_failure:
            # case 失败
            pass  # 保留资源以供检查
        else:
            # case 成功
            cleaned_up.append(self.resource_id)


dataset = Dataset(
    name='conditional_cleanup',
    cases=[
        Case(name='success_case', inputs='hello', metadata={'keep_on_failure': True}),
        Case(name='failure_case', inputs='fail', metadata={'keep_on_failure': True}),
    ]
)


def task(inputs: str) -> str:
    if inputs == 'fail':
        raise ValueError('intentional failure')
    return inputs.upper()


report = dataset.evaluate_sync(task, max_concurrency=1, lifecycle=ConditionalCleanup)

print(cleaned_up)
#> ['success_case']
```

## 准备 Evaluator Context {#preparing-evaluator-context}

`prepare_context()` hook 会在任务完成后、evaluators 看到 context 前运行。它可用于基于任务 output、span tree 或任何其他状态添加 metrics 或 attributes。例如，可以从 instrumented spans 派生 metrics（如 tool call 计数或 API latency），也可以根据 `setup()` 期间设置的外部资源计算值：

```python
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.lifecycle import CaseLifecycle


class EnrichMetrics(CaseLifecycle):
    async def prepare_context(self, ctx: EvaluatorContext) -> EvaluatorContext:
        ctx.metrics['output_length'] = len(str(ctx.output))
        return ctx


@dataclass
class CheckLength(Evaluator):
    max_length: int = 50

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.metrics.get('output_length', 0) <= self.max_length


dataset = Dataset(
    name='context_enrichment',
    cases=[Case(name='short', inputs='hi'), Case(name='long', inputs='hello world')],
    evaluators=[CheckLength()],
)

report = dataset.evaluate_sync(lambda inputs: inputs.upper(), lifecycle=EnrichMetrics)

for case in report.cases:
    print(f'{case.name}: output_length={case.metrics["output_length"]}')
    #> short: output_length=2
    #> long: output_length=11
```

## 类型参数 {#type-parameters}

[`CaseLifecycle`][pydantic_evals.lifecycle.CaseLifecycle] 与 [`Case`][pydantic_evals.dataset.Case] 一样，对三个类型参数泛型化：`InputsT`、`OutputT` 和 `MetadataT`。三者都默认为 `Any`，因此当 hooks 不需要类型特定访问时，可以省略它们：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators.context import EvaluatorContext
from pydantic_evals.lifecycle import CaseLifecycle


# 适用于任何数据集，无需类型参数
class GenericMetricEnricher(CaseLifecycle):
    async def prepare_context(self, ctx: EvaluatorContext) -> EvaluatorContext:
        ctx.metrics['custom'] = 42
        return ctx


dataset = Dataset(name='generic_lifecycle', cases=[Case(inputs='test')])
report = dataset.evaluate_sync(lambda inputs: inputs, lifecycle=GenericMetricEnricher)

print(report.cases[0].metrics['custom'])
#> 42
```

## 后续步骤 {#next-steps}

- **[Metrics & Attributes](metrics-attributes.md)**：在任务中记录 metrics
- **[Custom Evaluators](../evaluators/custom.md)**：在 evaluators 中使用 enriched metrics
- **[Span-Based Evaluation](../evaluators/span-based.md)**：分析执行 traces
