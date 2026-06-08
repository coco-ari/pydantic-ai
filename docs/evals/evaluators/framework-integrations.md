# 第三方集成 {#third-party-integrations}

Pydantic Evals 不会强依赖任何特定 metrics 框架。当团队已经在使用 [Ragas](https://github.com/explodinggradients/ragas)、[DeepEval](https://github.com/confident-ai/deepeval) 或其他评分库时，[`Evaluator`][pydantic_evals.evaluators.Evaluator] 基类可以很直接地包装上游 metric，并在任何 Pydantic Evals 数据集中运行它。本页展示常见集成的完整示例。

!!! tip "能用原生 evaluator 时优先使用"
    如果基于 rubric 的 [`LLMJudge`][pydantic_evals.evaluators.LLMJudge] 或[自定义 evaluator](custom.md) 能覆盖你的用例，通常会更简单：没有额外依赖，分数也能干净地进入报告。只有当你明确需要*完全一致*的上游实现时，才使用下面的集成，例如为了复现已发布 benchmark、与现有评估套件保持一致，或使用我们没有原生暴露的功能。你可以在同一个数据集中混用外部 evaluator 和原生 evaluator。

## 模式 {#pattern}

每个框架集成都遵循同一种模式：

1. 继承 [`Evaluator`][pydantic_evals.evaluators.Evaluator]。
2. 将 `ctx.inputs`、`ctx.output`、`ctx.expected_output` 和 metadata 适配为上游 metric 期望的形式。
3. 返回 `float` 分数、`bool` 断言、[`EvaluationReason`][pydantic_evals.evaluators.EvaluationReason]，或包含这些值的 `dict`。

本页其余部分展示具体 adapter。这些示例刻意保持简洁，你可以按团队需要扩展配置，例如模型选择、阈值、按 case 开关等。

## Ragas

使用 `pip install ragas` 安装（不包含在 `pydantic-evals` 中）。

这个 adapter 会为单轮样本包装 [`ragas.metrics.Faithfulness`](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/)。每个 case 都需要在 inputs 或 metadata 中提供检索到的上下文。

```python {test="skip" lint="skip"}
from dataclasses import dataclass

from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import Faithfulness

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext


@dataclass
class RagasFaithfulness(Evaluator):
    """Wrap `ragas.metrics.Faithfulness` as a Pydantic Evals evaluator."""

    context_field: str = 'context'

    async def evaluate(self, ctx: EvaluatorContext) -> EvaluationReason:
        metadata = ctx.metadata or {}
        retrieved_contexts = metadata.get(self.context_field, [])
        if isinstance(retrieved_contexts, str):
            retrieved_contexts = [retrieved_contexts]

        sample = SingleTurnSample(
            user_input=str(ctx.inputs),
            response=str(ctx.output),
            retrieved_contexts=retrieved_contexts,
        )
        metric = Faithfulness()
        score = await metric.single_turn_ascore(sample)
        return EvaluationReason(value=float(score), reason=f'ragas.Faithfulness = {score:.3f}')
```

用法与任何内置 evaluator 相同：

```python {test="skip" lint="skip"}
from pydantic_evals import Case, Dataset

dataset = Dataset(
    name='rag_eval',
    cases=[
        Case(
            inputs='What is the capital of France?',
            metadata={'context': ['Paris is the capital of France.']},
        ),
    ],
    evaluators=[RagasFaithfulness()],
)
```

同样的模式也适用于 `ragas.metrics.answer_relevancy`、`context_precision` 和其他评分 metrics：替换 metric 类，并在需要时替换样本字段。

## DeepEval

使用 `pip install deepeval` 安装（不包含在 `pydantic-evals` 中）。

这个 adapter 会包装 [DeepEval 的 `GEval` metric](https://docs.confident-ai.com/docs/metrics-llm-evals)，针对 `LLMTestCase` 对某个 criterion 打分。DeepEval 的 `measure` 是同步的，因此这个 evaluator 也是同步的。

```python {test="skip" lint="skip"}
from dataclasses import dataclass

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext


@dataclass
class DeepEvalGEval(Evaluator):
    """Wrap `deepeval.metrics.GEval` as a Pydantic Evals evaluator."""

    metric_name: str
    criteria: str
    threshold: float = 0.5

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, float | bool | EvaluationReason]:
        test_case = LLMTestCase(
            input=str(ctx.inputs),
            actual_output=str(ctx.output),
            expected_output=None if ctx.expected_output is None else str(ctx.expected_output),
        )
        metric = GEval(
            name=self.metric_name,
            criteria=self.criteria,
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            threshold=self.threshold,
        )
        metric.measure(test_case)
        return {
            f'{self.metric_name}_score': EvaluationReason(value=float(metric.score), reason=metric.reason or ''),
            f'{self.metric_name}_pass': bool(metric.success),
        }
```

同样的包装形态也适用于 DeepEval 的 `FaithfulnessMetric`、`AnswerRelevancyMetric`、`HallucinationMetric` 等：替换 metric 类，并填充相关的 `LLMTestCase` 字段（例如 faithfulness 需要 `retrieval_context`）。

## 依赖说明 {#notes-on-dependencies}

- `ragas` 和 `deepeval` 是可选依赖，不会随 `pydantic-evals` 安装，也不属于任何依赖组。只在使用这些集成的项目中安装它们。
- 这两个库都会自行发起 LLM 调用，因此在运行包含这些 evaluators 的数据集时，要预期额外的 API 用量。
