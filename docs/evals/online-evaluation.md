# 在线评估 {#online-evaluation}

在线评估让你可以把 evaluators 附加到生产环境（或预发环境）函数上，使每次调用（或抽样子集）都能在后台自动评估。这里使用的仍然是与 [`Dataset.evaluate()`][pydantic_evals.dataset.Dataset.evaluate] 相同的 [`Evaluator`][pydantic_evals.evaluators.Evaluator] 类；区别只是接入方式不同。

## 何时使用在线评估 {#when-to-use-online-evaluation}

当你希望做到以下事情时，在线评估很有用：

- **监控生产质量：** 按照 rubric 持续为 LLM 输出打分
- **捕获回归：** 检测不同部署之间 agent 行为是否退化
- **收集评估数据：** 从真实流量构建数据集，用于离线分析
- **控制成本：** 只对一部分流量运行昂贵的 LLM judges，同时对全部流量运行廉价检查

如果要在部署前针对精选数据集进行测试，请改用基于 [`Dataset.evaluate()`][pydantic_evals.dataset.Dataset.evaluate] 的[离线评估](quick-start.md)。

## 快速开始 {#quick-start}

[`evaluate()`][pydantic_evals.online.evaluate] decorator 可以把 evaluators 附加到任意函数上。Evaluators 会在后台运行，不阻塞调用方，结果会作为 [OpenTelemetry events](#default-otel-event-emission) 发出：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import evaluate


@dataclass
class OutputNotEmpty(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return bool(ctx.output)


@evaluate(OutputNotEmpty())
async def summarize(text: str) -> str:
    return f'Summary of: {text}'
```

请在应用启动流程的其他位置接入 OTel export（例如 [`logfire.configure()`](../logfire.md#using-logfire)），这样发出的 `gen_ai.evaluation.result` events 才能到达你的后端。

每次被装饰的调用都会为每个 evaluator result 发出一个 `gen_ai.evaluation.result` OTel event，并遵循 [OTel GenAI evaluation semconv](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-events/#event-gen_aievaluationresult)。这与离线评估通过 `logfire.span` 发出 OTel spans 的方式相呼应：如果进程中配置了任何 OTel SDK（通过 [`logfire.configure()`](../logfire.md#using-logfire)、直接使用 OTel SDK，或通过 vendor instrumentation），events 会流向你的后端；否则，发出事件只是一个低成本 no-op。

如果还想在 Python 代码中额外处理结果，用于 alerting、自定义聚合、内存内测试捕获或非 OTel 目标，请注册一个 [sink](#sinks)。Sinks 会在 OTel event emission *之外*运行。

模块级 [`configure()`][pydantic_evals.online.configure] 和 [`evaluate()`][pydantic_evals.online.evaluate] 函数会委托给一个全局 [`OnlineEvalConfig`][pydantic_evals.online.OnlineEvalConfig]。如果需要多套配置或隔离设置，请创建你自己的 config 实例（见下文 [OnlineEvalConfig](#onlineevalconfig)）。

## Target（目标） {#target}

每个被装饰的函数（或 agent）都会发出带有 **target** 标记的结果。target 是一个名称，用于在下游 sinks 和 dashboards 中对结果分组。默认情况下，target 是被装饰函数的 `__name__`，但你可以用 `target=...` 覆盖：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import evaluate


@dataclass
class OutputNotEmpty(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return bool(ctx.output)


# Default: target='summarize' (function name)
@evaluate(OutputNotEmpty())
async def summarize(text: str) -> str: ...


# Override: use a friendly name
@evaluate(OutputNotEmpty(), target='customer_support')
async def run_agent(prompt: str) -> str: ...
```

每次 `submit()` 调用都会把 target name 作为普通 `str` 提供给 sinks；单个 sink 实例可以处理任意数量的被装饰函数或 agents。

对于 agent capabilities，target name 来自 agent 自身的 `name` attribute（见 [Agent 集成](#agent-integration)）；如果要按 agent 属性分类或路由，请在 config 上添加 metadata（例如 `metadata={'kind': 'agent'}`）。

## 核心概念 {#core-concepts}

### OnlineEvaluator 配置

不同 evaluators 需要不同设置。廉价 heuristic 可以在 100% 流量上运行；昂贵的 LLM judge 可能只在 1% 流量上运行。[`OnlineEvaluator`][pydantic_evals.online.OnlineEvaluator] 会用 per-evaluator 配置包装一个 [`Evaluator`][pydantic_evals.evaluators.Evaluator]：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext, LLMJudge
from pydantic_evals.online import OnlineEvaluator


@dataclass
class IsHelpful(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return len(str(ctx.output)) > 10


# Cheap evaluator: run on every request
always_check = OnlineEvaluator(evaluator=IsHelpful(), sample_rate=1.0)

# Expensive evaluator: run on 1% of requests, limit concurrency
rare_check = OnlineEvaluator(
    evaluator=LLMJudge(rubric='Is the response helpful?'),
    sample_rate=0.01,
    max_concurrency=5,
)
```

当你把裸 [`Evaluator`][pydantic_evals.evaluators.Evaluator] 传给 [`evaluate()`][pydantic_evals.online.evaluate] decorator 时，它会自动用 config 的默认 sample rate 包装成 [`OnlineEvaluator`][pydantic_evals.online.OnlineEvaluator]。

### OnlineEvalConfig 配置

[`OnlineEvalConfig`][pydantic_evals.online.OnlineEvalConfig] 保存跨 evaluator 的默认值（sample rate、metadata、可选的额外 sinks、OTel-emission 开关）。它有一个全局默认实例，你也可以为不同配置创建自定义实例：

```python
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic_evals.evaluators import (
    EvaluationResult,
    Evaluator,
    EvaluatorContext,
    EvaluatorFailure,
)
from pydantic_evals.online import OnlineEvalConfig, wait_for_evaluations


@dataclass
class IsNonEmpty(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return bool(ctx.output)


results_log: list[str] = []


async def log_sink(
    results: Sequence[EvaluationResult],
    failures: Sequence[EvaluatorFailure],
    context: EvaluatorContext,
) -> None:
    for r in results:
        results_log.append(f'{r.name}={r.value}')


my_eval = OnlineEvalConfig(
    default_sink=log_sink,
    default_sample_rate=1.0,
    metadata={'service': 'my-app'},
)


@my_eval.evaluate(IsNonEmpty())
async def my_function(query: str) -> str:
    return f'Answer to: {query}'


async def main():
    result = await my_function('What is 2+2?')
    print(result)
    #> Answer to: What is 2+2?
    await wait_for_evaluations()
    print(results_log)
    #> ['IsNonEmpty=True']


asyncio.run(main())
```

### Sinks（结果接收器）

OTel event emission 是在线评估的默认 observability surface（见[默认 OTel event emission](#default-otel-event-emission)）。Sinks 用于在 Python 代码中进行*额外*处理，例如内存内测试捕获、alerting、fan-out 到非 OTel 目标，或自定义聚合。[`EvaluationSink`][pydantic_evals.online.EvaluationSink] 是对应 protocol；单个 config 可以注册多个 sinks。

内置 [`CallbackSink`][pydantic_evals.online.CallbackSink] 会包装任何接受 results、failures 和 context 的 callable（同步或异步都可以）。任何需要 sink 的地方也可以直接传裸 callable，它会被自动包装成 [`CallbackSink`][pydantic_evals.online.CallbackSink]。

如果需要自定义 sinks，请实现 [`EvaluationSink`][pydantic_evals.online.EvaluationSink] protocol。每次 `submit()` 调用都会收到一个 [`SinkPayload`][pydantic_evals.online.SinkPayload]，其中打包了某次函数调用运行的一个或多个 evaluators 所产生的 results、failures、context、span reference 和 target：

```python
from pydantic_evals.online import SinkPayload


class PrintSink:
    """Prints evaluation results to stdout."""

    async def submit(self, payload: SinkPayload) -> None:
        for r in payload.results:
            version = f' ({r.evaluator_version})' if r.evaluator_version else ''
            print(f'  [{payload.target}] {r.name}{version}: {r.value}')
        for f in payload.failures:
            version = f' ({f.evaluator_version})' if f.evaluator_version else ''
            print(f'  [{payload.target}] FAILED {f.name}{version}: {f.error_message}')
```

`payload.results` 和 `payload.failures` 可能覆盖单次函数调用中的一个或多个 evaluators。当多个 evaluators 共享一个 sink 时，它们的结果会被批量合并到一次 `submit()` 调用中。每个结果都携带自己的归因信息（name、[`EvaluationResult`][pydantic_evals.evaluators.EvaluationResult] 和 [`EvaluatorFailure`][pydantic_evals.evaluators.EvaluatorFailure] 上的 `evaluator_version`，以及 source spec），因此 sinks 可以在下游将它们分开；见 [Evaluator Versioning](#evaluator-versioning)。`payload.target` 标识正在被评估的函数或 agent（见 [Target](#target)）。

### 默认 OTel event emission {#default-otel-event-emission}

每个被分派的 evaluator 都会为每个 [`EvaluationResult`][pydantic_evals.evaluators.EvaluationResult] 或 [`EvaluatorFailure`][pydantic_evals.evaluators.EvaluatorFailure] 无条件发出一个 `gen_ai.evaluation.result` OTel log event；不需要注册 sink。Events 会以产生它们的 span 作为 parent，因此在 trace 中会嵌套显示在原始函数调用下面。如果进程中没有配置 OTel SDK，发出事件就是一个低成本 no-op。

每个 event 都有 `event.name = 'gen_ai.evaluation.result'` 和一段简短的人类可读 body（例如 `evaluation: accuracy=0.87`，或 `evaluation: accuracy failed: <error>`）。Emission 遵循 [OpenTelemetry GenAI evaluation semconv](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-events/#event-gen_aievaluationresult)，并包含以下 attributes：

- `gen_ai.evaluation.name`：当 `evaluate()` 返回 scalar 时是 evaluator class name；当它返回 `{'accuracy': ..., 'score': ...}` 时是 mapping key。来源：[`EvaluationResult.name`][pydantic_evals.evaluators.EvaluationResult] / [`EvaluatorFailure.name`][pydantic_evals.evaluators.EvaluatorFailure]。
- `gen_ai.evaluation.score.value`：为 `bool`（`True`->`1.0`，`False`->`0.0`）和 numeric returns 填充。`str` returns 会省略。
- `gen_ai.evaluation.score.label`：为 `bool`（`True`->`'pass'`，`False`->`'fail'`）和 `str` returns 填充（直接用作 label）。numeric returns 会省略。
- `gen_ai.evaluation.explanation`：成功时为 `EvaluationResult.reason`，失败时为 `EvaluatorFailure.error_message`。不存在时省略。可以在自定义 evaluator 中构造 `EvaluationResult` 时通过 `reason=...` 设置。
- `error.type`（仅 failure events）：当 failure 由捕获的 exception 构建时为 exception class name（例如 `'ValueError'`）；对于未提供该值而构造的 `EvaluatorFailure` 实例，会回退为 `'pydantic_evals.EvaluatorFailure'`。成功评估中不存在。来源：`EvaluatorFailure.error_type`。
- `gen_ai.evaluation.target`：`@evaluate(target=...)` 或 agent `name`。见 [Target](#target)。
- `gen_ai.evaluation.evaluator.version`：`Evaluator.evaluator_version` class attribute；类未设置时省略。见 [Evaluator Versioning](#evaluator-versioning)。
- `gen_ai.evaluation.evaluator.source`：JSON-serialized [`EvaluatorSpec`][pydantic_evals.evaluators.evaluator.EvaluatorSpec]，用于标识 evaluator class 及其 constructor arguments，让下游查询无需只依赖 `name` 就能按 evaluator identity 分组（两个不同的 `LLMJudge(rubric=...)` 实例共享同一个 name，但 source 不同）。

[OTel baggage](https://pydantic.dev/docs/logfire/reference/baggage/) entries（如果有）也会作为 attributes 附加到每个 event 上；可通过 config 上的 `include_baggage` 配置。上面的 `gen_ai.*` 和 `error.type` attributes 与 baggage 冲突时总是优先。

例如，上面的 `OutputNotEmpty` evaluator 若用 `@evaluate(OutputNotEmpty(), target='customer_support')` 装饰，并且对某次调用返回 `True`，则会发出一个包含以下内容的 event：

- `gen_ai.evaluation.name = 'OutputNotEmpty'`
- `gen_ai.evaluation.score.value = 1.0`
- `gen_ai.evaluation.score.label = 'pass'`
- `gen_ai.evaluation.target = 'customer_support'`
- `gen_ai.evaluation.evaluator.source = '{"name":"OutputNotEmpty","arguments":null}'`

带 constructor arguments 的 evaluator 会把这些参数渲染到 `source` 中。例如 [`LLMJudge(rubric='Is the response helpful?')`][pydantic_evals.evaluators.LLMJudge] 会发出 `gen_ai.evaluation.evaluator.source = '{"name":"LLMJudge","arguments":["Is the response helpful?"]}'`，因此两个 rubrics 不同的 `LLMJudge` 实例在下游仍然可区分。

`gen_ai.evaluation.evaluator.*` 下的 attributes 是 pydantic-evals 扩展；它们不属于当前 OTel GenAI semconv，名称将来可能会为了与新增 semconv 对齐而变化。

如果要禁用默认 emission（例如某个 test harness 只想断言自定义 sink），请在 config 上设置 `emit_otel_events=False`：

```python
from pydantic_evals.online import OnlineEvalConfig

config = OnlineEvalConfig(emit_otel_events=False)
```

#### Evaluator Versioning（Evaluator 版本管理） {#evaluator-versioning}

在 [`Evaluator`][pydantic_evals.evaluators.Evaluator] subclass 上 override [`get_evaluator_version`][pydantic_evals.evaluators.Evaluator.get_evaluator_version]，即可为它发出的每个结果加上 version string。该版本会在 emitted events 上显示为 `gen_ai.evaluation.evaluator.version`，并在每个 [`EvaluationResult`][pydantic_evals.evaluators.EvaluationResult] 和 [`EvaluatorFailure`][pydantic_evals.evaluators.EvaluatorFailure] 上显示为 `evaluator_version`。这样 trend lines 和 dashboards 就可以过滤掉已退役 evaluator versions 产生的结果，而无需删除历史行；当你修改 LLM judge prompt 或重写 heuristic，导致先前分数失效时，这很有用：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ToneCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> str:
        return 'neutral'

    def get_evaluator_version(self) -> str | None:
        return 'v2'  # bumped after prompt rewrite
```

该 version 适用于 evaluator 产生的所有结果（因此一个 evaluator class 映射到一个 version，即使 evaluator 返回的是 named results mapping）。

## 抽样 {#sampling}

使用 per-evaluator sample rates 控制评估频率，在质量监控和成本之间取得平衡。

!!! note
    Sampling 会在被装饰函数运行**之前**决定。当某次调用没有抽中任何 evaluators 时，函数执行不会产生额外 instrumentation overhead（没有 logfire span，也没有 span tree capture）。

### 静态 Sample Rates {#static-sample-rates}

`0.0` 到 `1.0` 之间的 `sample_rate` 会设置每次调用被评估的概率：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import OnlineEvaluator


@dataclass
class QuickCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return bool(ctx.output)


# Run on every request
always = OnlineEvaluator(evaluator=QuickCheck(), sample_rate=1.0)

# Run on 10% of requests
sometimes = OnlineEvaluator(evaluator=QuickCheck(), sample_rate=0.1)

# Never run (effectively disabled)
never = OnlineEvaluator(evaluator=QuickCheck(), sample_rate=0.0)
```

### 动态 Sample Rates {#dynamic-sample-rates}

传入 callable 可以启用运行时可配置或依赖输入的 sampling。该 callable 会收到一个 [`SamplingContext`][pydantic_evals.online.SamplingContext]，其中包含 evaluator instance、function inputs、config metadata 和 per-call random seed，并返回 `float`（概率）或 `bool`（always/never）：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import OnlineEvaluator, SamplingContext


def get_current_rate(ctx: SamplingContext) -> float:
    return 0.5


@dataclass
class QuickCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return bool(ctx.output)


dynamic = OnlineEvaluator(evaluator=QuickCheck(), sample_rate=get_current_rate)
```

这支持与 feature flags、managed variables 或配置系统集成。例如，你可以把 `get_current_rate` 替换为运行时从远程配置服务（例如 [Logfire managed variables](https://logfire.pydantic.dev/docs/reference/advanced/managed-variables/)）读取的函数，从而无需重新部署应用就能改变概率。

你也可以使用 [`SamplingContext`][pydantic_evals.online.SamplingContext] 根据 function inputs 做出 sampling 决策：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import OnlineEvaluator, SamplingContext


def sample_long_inputs(ctx: SamplingContext) -> bool:
    """Only evaluate calls with long input text."""
    return len(str(ctx.inputs.get('text', ''))) > 100


@dataclass
class QualityCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return len(str(ctx.output)) > 10


expensive = OnlineEvaluator(evaluator=QualityCheck(), sample_rate=sample_long_inputs)
```

### 相关抽样 {#correlated-sampling}

默认情况下，每个 evaluator 独立抽样。如果有三个 evaluators 且各自为 10%，大约 27% 的调用会产生 evaluation overhead（`1 - 0.9^3`）。如果你希望*同一批* 10% 的调用运行*所有* evaluators，请设置 `sampling_mode='correlated'`：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import OnlineEvalConfig, OnlineEvaluator


@dataclass
class CheckA(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


@dataclass
class CheckB(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


config = OnlineEvalConfig(
    default_sink=lambda results, failures, ctx: None,
    sampling_mode='correlated',
)

# Both run on the same ~10% of calls
check_a = OnlineEvaluator(evaluator=CheckA(), sample_rate=0.1)
check_b = OnlineEvaluator(evaluator=CheckB(), sample_rate=0.1)
```

在 correlated mode 下，每次函数调用会生成一个随机 `call_seed`（在 0.0 到 1.0 之间均匀分布），并在所有 evaluators 之间共享。当 `call_seed < sample_rate` 时，某个 evaluator 会运行；因此低 rate evaluators 的调用总是高 rate evaluators 调用的子集，总 overhead probability 等于最大 rate，而不是累加。

对于希望无论 mode 如何都自行实现 correlated logic 的自定义 `sample_rate` callables，`call_seed` 也可以从 [`SamplingContext`][pydantic_evals.online.SamplingContext] 获取。

### 禁用评估 {#disabling-evaluation}

使用 [`disable_evaluation()`][pydantic_evals.online.disable_evaluation] 可以在某个 scope 内抑制所有在线评估。这在测试中可能很有用：

```python
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic_evals.evaluators import (
    EvaluationResult,
    Evaluator,
    EvaluatorContext,
    EvaluatorFailure,
)
from pydantic_evals.online import (
    OnlineEvalConfig,
    disable_evaluation,
    wait_for_evaluations,
)


@dataclass
class OutputCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return bool(ctx.output)


results_log: list[str] = []


async def log_sink(
    results: Sequence[EvaluationResult],
    failures: Sequence[EvaluatorFailure],
    context: EvaluatorContext,
) -> None:
    for r in results:
        results_log.append(f'{r.name}={r.value}')


config = OnlineEvalConfig(default_sink=log_sink)


@config.evaluate(OutputCheck())
async def my_function(x: int) -> int:
    return x * 2


async def main():
    # Evaluators suppressed inside this block
    with disable_evaluation():
        result = await my_function(21)
        print(result)
        #> 42

    await wait_for_evaluations()
    print(f'evaluations run: {len(results_log)}')
    #> evaluations run: 0

    # Evaluators resume outside the block
    await my_function(21)
    await wait_for_evaluations()
    print(f'evaluations run: {len(results_log)}')
    #> evaluations run: 1


asyncio.run(main())
```

## 条件评估 {#conditional-evaluation}

为了控制成本，你可以在单个自定义 evaluator 内有条件地运行昂贵的评估逻辑。返回一个 mapping，并且只包含已经运行的检查对应的 keys；你不想执行的检查可以直接从结果中省略：

```python
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic_evals.evaluators import (
    EvaluationResult,
    Evaluator,
    EvaluatorContext,
    EvaluatorFailure,
)
from pydantic_evals.online import (
    OnlineEvalConfig,
    wait_for_evaluations,
)

results_log: list[str] = []


async def log_sink(
    results: Sequence[EvaluationResult],
    failures: Sequence[EvaluatorFailure],
    context: EvaluatorContext,
) -> None:
    for r in results:
        results_log.append(f'{r.name}={r.value}')


@dataclass
class ConditionalAnalysis(Evaluator):
    """Runs a cheap check on every call, and an expensive check only on long outputs."""

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, float | bool]:
        output = str(ctx.output)
        results: dict[str, float | bool] = {
            'has_content': len(output) > 0,
        }
        # Only run the expensive analysis on long outputs
        if len(output) > 20:
            # pretend the following line is expensive..
            results['detail_score'] = len(output) / 100.0
        return results


config = OnlineEvalConfig(default_sink=log_sink)


@config.evaluate(ConditionalAnalysis())
async def generate(prompt: str) -> str:
    return f'Response to: {prompt}'


async def main():
    await generate('hi')  # short output — only cheap check runs
    await wait_for_evaluations()
    print(results_log)
    #> ['has_content=True']

    results_log.clear()
    await generate('tell me a long story about dragons')  # long output — both checks run
    await wait_for_evaluations()
    print(sorted(results_log))
    #> ['detail_score=0.47', 'has_content=True']


asyncio.run(main())
```

这种模式让你可以在一个 evaluator 中组合廉价检查和昂贵检查，并在条件不满足时避免不必要的工作。

## 同步函数支持 {#sync-function-support}

[`evaluate()`][pydantic_evals.online.evaluate] decorator 同时适用于 async 和 sync functions：

```python
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic_evals.evaluators import (
    EvaluationResult,
    Evaluator,
    EvaluatorContext,
    EvaluatorFailure,
)
from pydantic_evals.online import OnlineEvalConfig, wait_for_evaluations

results_log: list[str] = []


async def log_sink(
    results: Sequence[EvaluationResult],
    failures: Sequence[EvaluatorFailure],
    context: EvaluatorContext,
) -> None:
    for r in results:
        results_log.append(f'{r.name}={r.value}')


@dataclass
class OutputCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return bool(ctx.output)


config = OnlineEvalConfig(default_sink=log_sink)


@config.evaluate(OutputCheck())
def process(text: str) -> str:
    return text.upper()


async def main():
    # Sync decorated functions work from async contexts too
    result = process('hello')
    print(result)
    #> HELLO

    await wait_for_evaluations()
    print(results_log)
    #> ['OutputCheck=True']


asyncio.run(main())
```

被装饰的同步函数可以在 sync 和 async contexts 中工作。当存在运行中的 event loop 时，evaluators 会作为该 loop 上的 background tasks 分派。否则，会生成一个带有独立 event loop 的 background thread。

## Per-Evaluator Sink 覆盖 {#per-evaluator-sink-overrides}

单个 evaluators 可以覆盖 config 的 default sink。如果不同 evaluators 需要把结果发送到不同目标，这会很有用：

```python
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from pydantic_evals.evaluators import (
    EvaluationResult,
    Evaluator,
    EvaluatorContext,
    EvaluatorFailure,
)
from pydantic_evals.online import (
    OnlineEvalConfig,
    OnlineEvaluator,
    wait_for_evaluations,
)

default_log: list[str] = []
special_log: list[str] = []


async def default_sink(
    results: Sequence[EvaluationResult],
    failures: Sequence[EvaluatorFailure],
    context: EvaluatorContext,
) -> None:
    for r in results:
        default_log.append(r.name)


async def special_sink(
    results: Sequence[EvaluationResult],
    failures: Sequence[EvaluatorFailure],
    context: EvaluatorContext,
) -> None:
    for r in results:
        special_log.append(r.name)


@dataclass
class FastCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


@dataclass
class ImportantCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


config = OnlineEvalConfig(default_sink=default_sink)


@config.evaluate(
    FastCheck(),  # uses default sink
    OnlineEvaluator(evaluator=ImportantCheck(), sink=special_sink),  # uses special sink
)
async def my_function(x: int) -> int:
    return x


async def main():
    await my_function(42)
    await wait_for_evaluations()

    print(f'default: {default_log}')
    #> default: ['FastCheck']
    print(f'special: {special_log}')
    #> special: ['ImportantCheck']


asyncio.run(main())
```

## 从已存储数据重新运行 Evaluators {#re-running-evaluators-from-stored-data}

在线评估的一项关键能力，是无需重新执行原始函数即可重新运行 evaluators。当你想用更新后的 rubrics 评估历史数据，或在已有 traces 上运行额外 evaluators 时，这很有用。

### `run_evaluators` 函数

[`run_evaluators()`][pydantic_evals.online.run_evaluators] 会针对一个 [`EvaluatorContext`][pydantic_evals.evaluators.EvaluatorContext] 运行一组 evaluators 并返回结果：

```python
import asyncio
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import run_evaluators
from pydantic_evals.otel.span_tree import SpanTree


@dataclass
class LengthCheck(Evaluator):
    min_length: int = 10

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return len(str(ctx.output)) >= self.min_length


@dataclass
class HasKeyword(Evaluator):
    keyword: str = 'hello'

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return self.keyword in str(ctx.output).lower()


async def main():
    # Build a context manually (in practice, you'd get this from stored data)
    # Normally EvaluatorContext would not be manually constructed —
    # it is built automatically by the @evaluate decorator or OnlineEvaluation capability,
    # or from an EvaluatorContextSource (see below).
    ctx = EvaluatorContext(
        name='example',
        inputs={'query': 'greet the user'},
        output='Hello! How can I help you today?',
        expected_output=None,
        metadata=None,
        duration=0.5,
        _span_tree=SpanTree(),
        attributes={},
        metrics={},
    )

    results, failures = await run_evaluators(
        [LengthCheck(min_length=10), HasKeyword(keyword='hello')],
        ctx,
    )

    for r in results:
        print(f'{r.name}: {r.value}')
        #> LengthCheck: True
        #> HasKeyword: True
    print(f'failures: {len(failures)}')
    #> failures: 0


asyncio.run(main())
```

### EvaluatorContextSource Protocol（协议） {#evaluatorcontextsource-protocol}

如果要从外部存储（例如 Pydantic Logfire）获取 context data，请实现 [`EvaluatorContextSource`][pydantic_evals.online.EvaluatorContextSource] protocol。它定义了 `fetch()` 和 `fetch_many()` methods，用于从已存储数据返回 [`EvaluatorContext`][pydantic_evals.evaluators.EvaluatorContext] objects：

```python
import asyncio
from collections.abc import Sequence

from pydantic_evals.evaluators import EvaluatorContext
from pydantic_evals.online import SpanReference
from pydantic_evals.otel.span_tree import SpanTree


class MyContextSource:
    """Example source that fetches context from a hypothetical store."""

    def __init__(self, store: dict[str, EvaluatorContext]) -> None:
        self._store = store

    async def fetch(self, span: SpanReference) -> EvaluatorContext:
        return self._store[span.span_id]

    async def fetch_many(self, spans: Sequence[SpanReference]) -> list[EvaluatorContext]:
        return [self._store[s.span_id] for s in spans]


def _make_context(
    *,
    inputs: object = None,
    output: object = None,
    metadata: object = None,
    duration: float = 0.0,
) -> EvaluatorContext:
    # Normally EvaluatorContext would not be manually constructed —
    # it is built automatically by the @evaluate decorator or OnlineEvaluation capability.
    return EvaluatorContext(
        name=None,
        inputs=inputs,
        output=output,
        expected_output=None,
        metadata=metadata,
        duration=duration,
        _span_tree=SpanTree(),
        attributes={},
        metrics={},
    )


async def main():
    source = MyContextSource({
        'span_abc': _make_context(
            inputs={'query': 'What is AI?'},
            output='AI is artificial intelligence.',
            metadata={'model': 'gpt-4o'},
            duration=1.2,
        ),
        'span_def': _make_context(
            inputs={'query': 'What is ML?'},
            output='ML is machine learning.',
            metadata={'model': 'gpt-4o'},
            duration=0.8,
        ),
    })

    # Fetch a single context
    ctx = await source.fetch(SpanReference(trace_id='t1', span_id='span_abc'))
    print(f'inputs: {ctx.inputs}')
    #> inputs: {'query': 'What is AI?'}
    print(f'output: {ctx.output}')
    #> output: AI is artificial intelligence.

    # Fetch multiple contexts in a batch
    spans = [
        SpanReference(trace_id='t1', span_id='span_abc'),
        SpanReference(trace_id='t1', span_id='span_def'),
    ]
    contexts = await source.fetch_many(spans)
    print(f'batch size: {len(contexts)}')
    #> batch size: 2


asyncio.run(main())
```

## 并发控制 {#concurrency-control}

每个 [`OnlineEvaluator`][pydantic_evals.online.OnlineEvaluator] 都有一个 `max_concurrency` limit（默认：10）。达到该 limit 时，针对该 evaluator 的新 evaluation requests 会被**丢弃**（不会排队）。这可以防止昂贵 evaluators 消耗无界资源：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import OnlineEvaluator


@dataclass
class ExpensiveCheck(Evaluator):
    async def evaluate(self, ctx: EvaluatorContext) -> bool:
        # Imagine this makes a slow call to an LLM
        return True


# Allow at most 3 concurrent evaluations
limited = OnlineEvaluator(
    evaluator=ExpensiveCheck(),
    sample_rate=0.1,
    max_concurrency=3,
)
```

如果要对被丢弃的 evaluations 做出反应，请在 [`OnlineEvaluator`][pydantic_evals.online.OnlineEvaluator] 上设置 `on_max_concurrency`，或在 [`OnlineEvalConfig`][pydantic_evals.online.OnlineEvalConfig] 上设置默认值。Callback 会收到本应被评估的 [`EvaluatorContext`][pydantic_evals.evaluators.EvaluatorContext]，可以是 sync 或 async：

```python
import warnings
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import OnlineEvalConfig, OnlineEvaluator


@dataclass
class ExpensiveCheck(Evaluator):
    async def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


def warn_on_drop(ctx: EvaluatorContext) -> None:
    warnings.warn('Evaluation dropped due to max concurrency', stacklevel=1)


# Per-evaluator handler
limited = OnlineEvaluator(
    evaluator=ExpensiveCheck(),
    max_concurrency=3,
    on_max_concurrency=warn_on_drop,
)

# Or set a global default for all evaluators in a config
config = OnlineEvalConfig(on_max_concurrency=warn_on_drop)
```

!!! note
    如果既没有设置 per-evaluator 的 `on_max_concurrency`，也没有设置 config-level 的 `on_max_concurrency`，被丢弃的 evaluations 会被静默忽略。

## 错误处理 {#error-handling}

错误处理分为两类：

- **`on_sampling_error`**：当 `sample_rate` callable 抛出异常时同步调用。接收该 exception 和 [`Evaluator`][pydantic_evals.evaluators.Evaluator]。必须是 sync（不能是 async）。如果设置了它，该 evaluator 会被跳过。如果未设置，该 exception 会**传播给调用方**。
- **`on_error`**：当 `sink` 或 `on_max_concurrency` callback 中发生 exception 时调用。接收 exception、[`EvaluatorContext`][pydantic_evals.evaluators.EvaluatorContext]、[`Evaluator`][pydantic_evals.evaluators.Evaluator] 和一个 [`OnErrorLocation`][pydantic_evals.online.OnErrorLocation] string。可以是 sync 或 async。如果未设置，exceptions 会被**静默抑制**。`'sink'` location 的范围较宽，既覆盖 custom sink failures，也覆盖更少见的默认 OTel event emission failures；因此按 location 分支的 handlers 应把 `'sink'` 视为"结果投递出错"。

可在 [`OnlineEvalConfig`][pydantic_evals.online.OnlineEvalConfig] 上设置这些全局默认值，或在 [`OnlineEvaluator`][pydantic_evals.online.OnlineEvaluator] 上按 evaluator 覆盖：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import OnErrorLocation, OnlineEvalConfig, OnlineEvaluator


def log_errors(
    exc: Exception,
    ctx: EvaluatorContext,
    evaluator: Evaluator,
    location: OnErrorLocation,
) -> None:
    print(f'[{location}] {type(exc).__name__}: {exc}')


@dataclass
class MyCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


# Global default — applies to all evaluators in this config
config = OnlineEvalConfig(
    default_sink=lambda results, failures, context: None,
    on_error=log_errors,
)

# Per-evaluator override
custom = OnlineEvaluator(evaluator=MyCheck(), on_error=log_errors)
```

关键行为：

- **Evaluator exceptions** 会通过转换成传给 sinks 的 [`EvaluatorFailure`][pydantic_evals.evaluators.EvaluatorFailure] objects 来处理；它们不会经过 `on_error`。
- **一个 evaluator 的 error 不会影响 siblings**；每个 evaluator 都在自己的 task 中运行，并拥有隔离的 error handling。
- **一个 sink 的 error 不会影响其他 sinks**；每次 sink submission 都会单独包装。
- **如果 `on_error` 本身抛出异常**，该 exception 会被静默抑制，以保护 sibling evaluators。
- **如果没有设置 `on_error`**，exceptions 会被静默抑制；这是安全默认值。

### 评估失败调用 {#evaluating-failed-calls}

默认情况下，当被装饰函数或被包装的 agent run 抛出异常时，**不会分派任何 evaluators**；只有成功结果会到达 evaluators。该 exception 会照常传播给调用方。

如果要为 failure modes 打分（例如分类 exception types、统计 tool errors、对 regressions 发出 alert），请在对应 [`OnlineEvaluator`][pydantic_evals.online.OnlineEvaluator] 上设置 `run_on_errors=True` 来 opt in。调用抛出异常时，这些 evaluators 会以 exception 作为 `EvaluatorContext.output` 被分派；分派后 exception 仍会继续传播：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online import OnlineEvaluator, evaluate


@dataclass
class CategorizeError(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> str:
        # On failed calls, ctx.output is the raised exception.
        if isinstance(ctx.output, Exception):
            return type(ctx.output).__name__
        return 'ok'


@evaluate(OnlineEvaluator(evaluator=CategorizeError(), run_on_errors=True))
async def my_function(x: int) -> int:
    if x < 0:
        raise ValueError('negative input')
    return x * 2
```

对该调用抽中的 evaluators 如果没有设置 `run_on_errors=True`，会在 error path 上被跳过。因此，一个廉价的 success-only check 可以和专用 error categorizer 放在同一个 decorator 中。这个 flag 也会被 [`OnlineEvaluation`][pydantic_evals.online_capability.OnlineEvaluation] agent capability 遵守。

## Agent 集成 {#agent-integration}

[`OnlineEvaluation`][pydantic_evals.online_capability.OnlineEvaluation] capability 为 Pydantic AI agents 带来在线评估。你不需要装饰函数，而是把该 capability 添加到 agent 上。与 `@evaluate` decorator 一样，evaluators 会在后台分派，结果默认作为 OTel events 发出；不需要注册 sink：

```python
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.online_capability import OnlineEvaluation


@dataclass
class OutputNotEmpty(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return bool(ctx.output)


agent = Agent(
    'openai:gpt-5.2',
    name='assistant',
    capabilities=[OnlineEvaluation(evaluators=[OutputNotEmpty()])],
)
```

写入每个 emitted event 的 target name 是 agent 自身的 `name` attribute，因此来自 `agent = Agent(..., name='assistant')` 的 events 会落在 `gen_ai.evaluation.target = 'assistant'` 下。如果 agent 没有 name，target 会回退为字面字符串 `'agent'`。

每次 agent run 完成后，该 capability 会：

1. 根据 evaluators 的 `sample_rate` 配置进行抽样
2. 从 run result（output、prompt、token usage、duration、span tree）构建 [`EvaluatorContext`][pydantic_evals.evaluators.EvaluatorContext]；`context.name` 会填入 agent run 的 `run_id`
3. 在后台异步分派 evaluators
4. 不等待 evaluators 完成就把控制权返回给调用方

如果要附加额外 sinks 或覆盖 sampling defaults，请传入 [`OnlineEvalConfig`][pydantic_evals.online.OnlineEvalConfig]；这与 `@evaluate` decorator 相同：`OnlineEvaluation(evaluators=[...], config=OnlineEvalConfig(default_sample_rate=0.1))`。

该 capability 支持与 [`@evaluate()`][pydantic_evals.online.evaluate] decorator 相同的全部功能：sampling、per-evaluator sinks、concurrency control 和 error handling。`config` 参数是可选的，并默认使用全局 [`DEFAULT_CONFIG`][pydantic_evals.online.DEFAULT_CONFIG]。

!!! note
    [`OnlineEvaluation`][pydantic_evals.online_capability.OnlineEvaluation] 会在 run 到达 final result 时包装 [`agent.run()`][pydantic_ai.Agent.run]、[`agent.run_stream()`][pydantic_ai.Agent.run_stream] 和 [`agent.iter()`][pydantic_ai.Agent.iter]。对于 streaming runs，evaluators 只会在 final result 可用且外围 context manager 退出后分派。驱动 [`agent.iter()`][pydantic_ai.Agent.iter] run 到完成时也会应用相同的 delayed-dispatch 行为；这通常是推荐的 streaming API。

## API 参考 {#api-reference}

`pydantic_evals.online` module 的完整 API 记录在 [API reference](../api/pydantic_evals/online.md) 中。

## 下一步 {#next-steps}

- **[Custom Evaluators](evaluators/custom.md)**：为你的领域编写 evaluators
- **[Native Evaluators](evaluators/built-in.md)**：使用现成 evaluators
- **[Logfire Integration](how-to/logfire-integration.md)**：在 Logfire 中可视化 evaluation results
- **[Quick Start](quick-start.md)**：使用 [`Dataset.evaluate()`][pydantic_evals.dataset.Dataset.evaluate] 进行离线评估
