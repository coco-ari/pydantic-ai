# 评估器概览 {#evaluators-overview}

Evaluators 是 Pydantic Evals 的核心。它们分析任务输出，并提供分数、标签或通过/失败断言。

## 何时使用不同评估器 {#when-to-use-different-evaluators}

### 确定性检查（快速且可靠） {#deterministic-checks-fast-reliable}

当你可以定义精确规则时，使用确定性评估器：

| 评估器 | 使用场景 | 示例 |
|-----------|----------|---------|
| [`EqualsExpected`][pydantic_evals.evaluators.EqualsExpected] | 精确输出匹配 | 结构化数据、分类 |
| [`Equals`][pydantic_evals.evaluators.Equals] | 等于指定值 | 检查哨兵值 |
| [`Contains`][pydantic_evals.evaluators.Contains] | 子字符串/元素检查 | 必需关键词、PII 检测 |
| [`IsInstance`][pydantic_evals.evaluators.IsInstance] | 类型验证 | 格式验证 |
| [`MaxDuration`][pydantic_evals.evaluators.MaxDuration] | 性能阈值 | SLA 合规 |
| [`HasMatchingSpan`][pydantic_evals.evaluators.HasMatchingSpan] | 行为验证 | 工具调用、代码路径 |

**优点：**

- 执行快（微秒到毫秒）
- 结果确定
- 无成本
- 易调试

**何时使用：**

- 格式验证（JSON 结构、类型检查）
- 必需内容检查（必须包含 X，必须不包含 Y）
- 性能要求（延迟、token 数）
- 行为检查（调用了哪些工具，执行了哪些代码路径）

### LLM 作为裁判（灵活且细致） {#llm-as-a-judge-flexible-nuanced}

当评估需要理解或判断时，使用 [`LLMJudge`][pydantic_evals.evaluators.LLMJudge]：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    name='llm_judge_example',
    cases=[Case(inputs='What is 2+2?', expected_output='4')],
    evaluators=[
        LLMJudge(
            rubric='Response is factually accurate based on the input',
            include_input=True,
        )
    ],
)
```

**优点：**

- 可以评估主观质量（有帮助程度、语气、创造力）
- 理解自然语言
- 可以遵循复杂评分规则
- 可跨领域灵活使用

**缺点：**

- 更慢（每次评估数秒）
- 需要花费模型调用成本
- 非确定性
- 可能存在偏见

**何时使用：**

- 事实准确性
- 相关性和有帮助程度
- 语气和风格
- 完整性
- 指令遵循
- RAG 质量（groundedness、引用准确性）

### 自定义评估器 {#custom-evaluators}

如果你想使用框架未提供的评估逻辑，自定义评估器会很有用。
它们经常用于 domain-specific 逻辑：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ValidSQL(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        try:
            import sqlparse
            sqlparse.parse(ctx.output)
            return True
        except Exception:
            return False
```

**何时使用：**

- Domain-specific 验证（SQL 语法、正则模式、业务规则）
- 外部 API 调用（运行生成的代码、检查数据库）
- 复杂计算（precision/recall、BLEU 分数）
- 集成检查（API 调用是否成功？）

## 评估类型 {#evaluation-types}

!!! info "详细返回类型指南"
    关于自定义 Evaluators 可以返回什么内容的完整细节，请参阅[自定义评估器返回类型](custom.md#return-types)。

Evaluators 基本返回三类结果：

### 1. 断言（bool） {#1-assertions-bool}

通过/失败检查，在报告中显示为 ✔ 或 ✗：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class HasKeyword(Evaluator):
    keyword: str

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return self.keyword in ctx.output
```

**用于：** 二元检查、质量门禁、合规要求

### 2. 分数（int 或 float） {#2-scores-int-or-float}

数值指标：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ConfidenceScore(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> float:
        # Analyze and return score
        return 0.87  # 87% confidence
```

**用于：** 质量指标、排序、A/B 测试、回归跟踪

### 3. 标签（str） {#3-labels-str}

分类结果：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class SentimentClassifier(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> str:
        if 'error' in ctx.output.lower():
            return 'error'
        elif 'success' in ctx.output.lower():
            return 'success'
        return 'neutral'
```

**用于：** 分类、错误归类、质量分桶

### 多个结果 {#multiple-results}

你可以从单个评估器返回多个评估结果：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ComprehensiveCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | float | str]:
        return {
            'valid_format': self._check_format(ctx.output),  # bool
            'quality_score': self._score_quality(ctx.output),  # float
            'category': self._classify(ctx.output),  # str
        }

    def _check_format(self, output: str) -> bool:
        return True

    def _score_quality(self, output: str) -> float:
        return 0.85

    def _classify(self, output: str) -> str:
        return 'good'
```

## 组合评估器 {#combining-evaluators}

混合搭配评估器来创建全面的评估套件：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import (
    Contains,
    IsInstance,
    LLMJudge,
    MaxDuration,
)

dataset = Dataset(
    name='layered_evaluation',
    cases=[Case(inputs='test', expected_output='result')],
    evaluators=[
        # Fast deterministic checks first
        IsInstance(type_name='str'),
        Contains(value='required_field'),
        MaxDuration(seconds=2.0),
        # Slower LLM checks after
        LLMJudge(
            rubric='Response is accurate and helpful',
            include_input=True,
        ),
    ],
)
```

## Case-specific evaluators {#case-specific-evaluators}

Case-specific evaluators 是构建全面评估套件时最强大的功能之一。你可以把评估器附加到单个 [`Case`][pydantic_evals.dataset.Case] 对象上，并且它们只会针对这些特定 cases 运行：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance, LLMJudge

dataset = Dataset(
    name='case_specific_evaluators',
    cases=[
        Case(
            name='greeting_response',
            inputs='Say hello',
            evaluators=[
                # This evaluator only runs for this case
                LLMJudge(
                    rubric='Response is warm and friendly, uses casual tone',
                    include_input=True,
                ),
            ],
        ),
        Case(
            name='formal_response',
            inputs='Write a business email',
            evaluators=[
                # Different requirements for this case
                LLMJudge(
                    rubric='Response is professional and formal, uses business language',
                    include_input=True,
                ),
            ],
        ),
    ],
    evaluators=[
        # This runs for ALL cases
        IsInstance(type_name='str'),
    ],
)
```

### 为什么 Case-Specific Evaluators 很重要 {#why-case-specific-evaluators-matter}

Case-specific evaluators 解决了 "一刀切" 评估的根本问题：**如果你能写出一个单一评估器评分规则，完美覆盖所有 cases 的需求，那你应该直接把这个规则合并进 agent 的 instructions**。（注意：当你希望生产中使用更便宜的模型，并用更贵的模型评估它时，这一点没那么适用；但在很多情况下，在生产中使用你能用到的最佳模型是合理的。）

Case-specific evaluation 的力量来自细微差别：

- **不同 cases 有不同需求**：客服回复需要共情；技术 API 回复需要精确
- **避免 "inmates running the asylum"**：如果你的 LLMJudge 评分规则足够通用，能到处适用，那你的 agent 本来就应该遵守它
- **捕获细致的 golden 行为**：每个 case 都可以准确指定该场景下的 "好" 是什么样

### 使用 Case-Specific LLMJudge 构建 Golden Datasets {#building-golden-datasets-with-case-specific-llmjudge}

一个特别强大的模式，是用 case-specific [`LLMJudge`][pydantic_evals.evaluators.LLMJudge] evaluators 快速构建全面、可维护的评估套件。你不需要精确的 `expected_output` 值，而是可以描述你关心什么：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    name='golden_dataset',
    cases=[
        Case(
            name='handle_refund_request',
            inputs={'query': 'I want my money back', 'order_id': '12345'},
            evaluators=[
                LLMJudge(
                    rubric="""
                    Response should:
                    1. Acknowledge the refund request empathetically
                    2. Ask for the reason for the refund
                    3. Mention our 30-day refund policy
                    4. NOT process the refund immediately (needs manager approval)
                    """,
                    include_input=True,
                ),
            ],
        ),
        Case(
            name='handle_shipping_question',
            inputs={'query': 'Where is my order?', 'order_id': '12345'},
            evaluators=[
                LLMJudge(
                    rubric="""
                    Response should:
                    1. Confirm the order number
                    2. Provide tracking information
                    3. Give estimated delivery date
                    4. Be brief and factual (not overly apologetic)
                    """,
                    include_input=True,
                ),
            ],
        ),
        Case(
            name='handle_angry_customer',
            inputs={'query': 'This is completely unacceptable!', 'order_id': '12345'},
            evaluators=[
                LLMJudge(
                    rubric="""
                    Response should:
                    1. Prioritize de-escalation with empathy
                    2. Avoid being defensive
                    3. Offer concrete next steps
                    4. Use phrases like "I understand" and "Let me help"
                    """,
                    include_input=True,
                ),
            ],
        ),
    ],
)
```

这种方法让你可以：

- **快速构建全面测试套件**：只需描述每个 case 想要什么
- **易维护**：需求变化时更新 rubrics，而不需要重新生成输出
- **自然覆盖边界情况**：发现新问题后添加带具体需求的新 cases
- **捕获领域知识**：每个 rubric 都记录该场景下 "好" 的含义

LLM evaluator 擅长理解细微需求并评估合规性，因此这是一种实用方式，能创建彻底的评估覆盖，同时避免脆弱性。

## Async vs Sync {#async-vs-sync}

Evaluators 可以是同步或异步的：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class SyncEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


async def some_async_operation() -> bool:
    return True


@dataclass
class AsyncEvaluator(Evaluator):
    async def evaluate(self, ctx: EvaluatorContext) -> bool:
        result = await some_async_operation()
        return result
```

Pydantic Evals 会自动处理两者。以下情况使用 async：
- 发起 API 调用
- 运行数据库查询
- 执行 I/O 操作
- 调用 LLM（例如 [`LLMJudge`][pydantic_evals.evaluators.LLMJudge]）

## 评估上下文 {#evaluation-context}

所有 evaluators 都会收到一个 [`EvaluatorContext`][pydantic_evals.evaluators.EvaluatorContext]：

- `ctx.inputs` - Task 输入
- `ctx.output` - Task 输出（要评估的内容）
- `ctx.expected_output` - 预期输出（如果提供）
- `ctx.metadata` - Case metadata（如果提供）
- `ctx.duration` - Task 执行时间（秒）
- `ctx.span_tree` - OpenTelemetry spans（如果配置了 logfire）
- `ctx.metrics` - 自定义 metrics 字典
- `ctx.attributes` - 自定义 attributes 字典

这为 evaluators 提供了完整上下文，以便做出有依据的评估。

## 错误处理 {#error-handling}

如果 evaluator 抛出异常，该异常会被捕获为 [`EvaluatorFailure`][pydantic_evals.evaluators.EvaluatorFailure]：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


def risky_operation(output: str) -> bool:
    # This might raise an exception
    if 'error' in output:
        raise ValueError('Found error in output')
    return True


@dataclass
class RiskyEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        # If this raises an exception, it will be captured
        result = risky_operation(ctx.output)
        return result
```

失败会出现在 `report.cases[i].evaluator_failures` 中，并包含：

- Evaluator 名称
- 错误消息
- 完整 stacktrace

使用重试配置来处理瞬时失败（见[重试策略](../how-to/retry-strategies.md)）。

## 报告评估器（实验范围） {#report-evaluators-experiment-wide}

上面的所有评估器都会对每个 case 运行一次。**报告评估器**不同：它们会在所有 cases 都完成评估后，对每个 experiment 运行一次，并一起分析完整结果集。

使用报告评估器计算实验范围统计，例如：

- **混淆矩阵**：可视化各分类的分类准确率
- **Precision-recall 曲线**：用 AUC 分数评估排序质量
- **标量指标**：整体准确率、F1、BLEU 或任何单个数值
- **摘要表**：按类别拆分、错误类别摘要

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import ConfusionMatrixEvaluator

dataset = Dataset(
    name='report_evaluator_example',
    cases=[
        Case(inputs='meow', expected_output='cat'),
        Case(inputs='woof', expected_output='dog'),
    ],
    report_evaluators=[
        ConfusionMatrixEvaluator(
            predicted_from='output',
            expected_from='expected_output',
        ),
    ],
)
```

**另见：** [报告评估器](report-evaluators.md) 获取完整指南，包括内置报告评估器以及如何编写自定义报告评估器。

## 下一步 {#next-steps}

- **[原生评估器](built-in.md)** - 所有已提供评估器的完整参考
- **[LLM Judge](llm-judge.md)** - 深入了解 LLM 作为裁判的评估
- **[第三方集成](framework-integrations.md)** - 包装 Ragas、DeepEval 和其他指标库
- **[自定义评估器](custom.md)** - 编写你自己的评估逻辑
- **[报告评估器](report-evaluators.md)** - 实验范围分析
- **[基于 Span 的评估](span-based.md)** - 使用 OpenTelemetry spans 进行评估
