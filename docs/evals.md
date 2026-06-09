---
title: Pydantic Evals
---

# Pydantic Evals

**Pydantic Evals** 是一个强大的评估框架，用于系统化测试和评估 AI 系统，范围从简单的 LLM 调用到复杂的多 agent 应用。

## 设计理念 {#design-philosophy}

!!! note "代码优先的方法"
    Pydantic Evals 遵循代码优先的理念，所有评估组件都在 Python 中定义。这不同于基于 Web 配置的平台。你在代码中编写并运行 evals，并可以把结果写入磁盘，或在终端中、在 [Pydantic Logfire](https://logfire.pydantic.dev/docs/guides/web-ui/evals/) 中查看。

!!! danger "Evals 仍是新兴实践"
    与单元测试不同，evals 仍是一门新兴的技艺/科学。任何声称确切知道你的 evals 应该如何定义的人，都可以放心忽略。我们把 Pydantic Evals 设计得灵活且实用，同时避免过度武断。


## 快速导航 {#quick-navigation}

**入门：**

- [安装](#installation)
- [快速开始](evals/quick-start.md)
- [核心概念](evals/core-concepts.md)

**评估器：**

- [评估器概览](evals/evaluators/overview.md) - 比较评估器类型，并了解何时使用每种方法
- [内置评估器](evals/evaluators/built-in.md) - 精确匹配、实例检查和其他开箱即用评估器的完整参考
- [LLM 作为裁判](evals/evaluators/llm-judge.md) - 使用 LLM 评估主观质量、复杂标准和自然语言输出
- [自定义评估器](evals/evaluators/custom.md) - 实现 domain-specific 的评分逻辑和自定义评估指标
- [基于 Span 的评估](evals/evaluators/span-based.md) - 使用 OpenTelemetry traces 评估内部 agent 行为（工具调用、执行流）。对于答案正确性取决于 _如何_ 得出，而不只是最终输出的复杂 agent，这非常重要。它还能确保 eval 断言与生产 telemetry 对齐。

**How-To 指南：**

- [Logfire 集成](evals/how-to/logfire-integration.md) - 可视化结果
- [数据集管理](evals/how-to/dataset-management.md) - 保存、加载、生成
- [并发与性能](evals/how-to/concurrency.md) - 控制并行执行
- [重试策略](evals/how-to/retry-strategies.md) - 处理瞬时失败
- [指标与属性](evals/how-to/metrics-attributes.md) - 跟踪自定义数据
- [用例生命周期 hooks](evals/how-to/lifecycle.md) - 按用例设置、清理和上下文增强

**示例：**

- [简单验证](evals/examples/simple-validation.md) - 基础示例

**参考：**

- [API 文档](api/pydantic_evals/dataset.md)

## 代码优先评估 {#code-first-evaluation}

Pydantic Evals 采用**代码优先方法**：你可以在 Python 代码中定义所有评估组件（数据集、实验、任务、用例和评估器），也可以把它们定义为由 Python 代码加载的序列化数据。这不同于完全基于 Web 配置的平台。

运行一个 _Experiment_ 时，你会看到进度指示器，并可以在运行 Python 代码的任何地方（IDE、终端等）打印结果。你还会拿到一个 report 对象，可以将它序列化并存储，或发送到 notebook 或其他应用做进一步可视化和分析。

如果你使用 [Pydantic Logfire](https://logfire.pydantic.dev/docs/guides/web-ui/evals/)，实验结果会自动出现在 Logfire Web 界面中，用于可视化、比较和协作分析。Logfire 作为 observability 层存在：你在代码中编写并运行 evals，然后在 Web UI 中查看和分析结果。

## 安装 {#installation}

要安装 Pydantic Evals 包，请运行：

```bash
pip/uv-add pydantic-evals
```

`pydantic-evals` 不依赖 `pydantic-ai`，但如果你想在 evals 中使用 OpenTelemetry traces，或把评估结果发送到 [logfire](https://pydantic.dev/logfire)，可以安装可选的 `logfire` 依赖。

```bash
pip/uv-add 'pydantic-evals[logfire]'
```

## Pydantic Evals 数据模型 {#pydantic-evals-data-model}

Pydantic Evals 围绕一个简单数据模型构建：

### 数据模型图 {#data-model-diagram}

```
Dataset (1) ──────────── (Many) Case
│                        │
│                        │
└─── (Many) Experiment ──┴─── (Many) Case results
     │
     └─── (1) Task
     │
     └─── (Many) Evaluator
```

### 关键关系 {#key-relationships}

1. **Dataset → Cases**：一个 Dataset 包含多个 Cases
2. **Dataset → Experiments**：一个 Dataset 可以随着时间用于多个 Experiments
3. **Experiment → Case results**：一个 Experiment 通过执行每个 Case 生成结果
4. **Experiment → Task**：一个 Experiment 评估一个已定义的 Task
5. **Experiment → Evaluators**：一个 Experiment 使用多个 Evaluators。Dataset-wide Evaluators 会针对所有 Cases 运行，而 case-specific Evaluators 只针对各自的 Cases 运行

### 数据流 {#data-flow}

1. **创建 Dataset**：在 YAML/JSON 中定义 cases 和 evaluators，或直接在 Python 中定义
2. **执行 Experiment**：运行 `dataset.evaluate_sync(task_function)`
3. **运行 Cases**：每个 Case 都会针对 Task 执行
4. **Evaluation**：Evaluators 为每个 Case 的 Task 输出打分
5. **Results**：所有 Case results 会被收集到一份摘要报告中

!!! note "一个类比"

    一个有用（但并不完美）的类比，是把 evals 看作一个**单元测试**框架：

    - **Cases + Evaluators** 是你的单个单元测试：每个测试定义一个你想验证的具体场景，其中包含输入和预期结果。就像单元测试一样，一个 case 会问：_"给定这个输入，我的系统是否产生了正确输出？"_

    - **Datasets** 类似测试套件：它们是把单元测试组织在一起的脚手架。它们把相关 cases 分组，并定义应当应用于套件中所有测试的共享评估标准。

    - **Experiments** 类似运行整个测试套件并获得报告。当你执行 `dataset.evaluate_sync(my_ai_function)` 时，就是把所有 cases 跑到你的 AI 系统上，并收集结果，就像运行 `pytest` 并获得通过、失败和性能指标摘要一样。

    与传统单元测试的关键区别在于，AI 系统是概率性的。如果你在做类型检查，仍然会得到简单的通过/失败；但文本输出的分数更可能是定性和/或分类的，也更开放于解释。

要更深入理解，请参阅[核心概念](evals/core-concepts.md)。

## Datasets 和 Cases {#datasets-and-cases}

在 Pydantic Evals 中，一切都从 [`Dataset`][pydantic_evals.dataset.Dataset] 和 [`Case`][pydantic_evals.dataset.Case] 开始：

- **[`Dataset`][pydantic_evals.dataset.Dataset]**：为评估特定任务或函数而设计的一组测试 Cases
- **[`Case`][pydantic_evals.dataset.Case]**：对应 Task 输入的单个测试场景，可带可选预期输出、metadata 和 case-specific evaluators

```python {title="simple_eval_dataset.py"}
from pydantic_evals import Case, Dataset

case1 = Case(
    name='simple_case',
    inputs='What is the capital of France?',
    expected_output='Paris',
    metadata={'difficulty': 'easy'},
)

dataset = Dataset(name='capital_quiz', cases=[case1])
```

_（这个示例是完整的，可以直接运行）_

参阅[数据集管理](evals/how-to/dataset-management.md)，了解如何保存、加载和生成 datasets。

## Evaluators 评估器 {#evaluators}

[`Evaluator`][pydantic_evals.evaluators.Evaluator] 会在你的 Task 针对 Case 测试时分析并评分结果。

它们可以是确定性的、基于代码的检查（例如用正则测试模型输出格式，或检查是否出现 PII 或敏感数据），也可以评估非确定性的模型输出质量，例如准确性、precision/recall、幻觉或指令遵循情况。

在 LLM 系统中，两类测试都有用，但经典的基于代码的测试，比需要人类或机器审查模型输出的测试更便宜、更简单。

Pydantic Evals 包含几个[内置评估器](evals/evaluators/built-in.md)，也允许你定义[自定义评估器](evals/evaluators/custom.md)：

```python {title="simple_eval_evaluator.py" requires="simple_eval_dataset.py"}
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.evaluators.common import IsInstance

from simple_eval_dataset import dataset

dataset.add_evaluator(IsInstance(type_name='str'))  # (1)!


@dataclass
class MyEvaluator(Evaluator):
    async def evaluate(self, ctx: EvaluatorContext[str, str]) -> float:  # (2)!
        if ctx.output == ctx.expected_output:
            return 1.0
        elif (
            isinstance(ctx.output, str)
            and ctx.expected_output.lower() in ctx.output.lower()
        ):
            return 0.8
        else:
            return 0.0


dataset.add_evaluator(MyEvaluator())
```

1. 你可以用 [`add_evaluator`][pydantic_evals.dataset.Dataset.add_evaluator] 方法向 dataset 添加内置评估器。
2. 这个自定义评估器会根据输出是否匹配预期输出返回一个简单分数。

_（这个示例是完整的，可以直接运行）_

了解更多：

- [评估器概览](evals/evaluators/overview.md) - 何时使用不同类型
- [内置评估器](evals/evaluators/built-in.md) - 完整参考
- [LLM Judge](evals/evaluators/llm-judge.md) - 使用 LLM 作为评估器
- [自定义评估器](evals/evaluators/custom.md) - 编写你自己的逻辑
- [基于 Span 的评估](evals/evaluators/span-based.md) - 分析执行 traces

## 运行 Experiments {#running-experiments}

执行评估意味着针对数据集中的所有 cases 运行一个 task，也称为运行一次 "experiment"。

把上面两个示例合在一起，并使用更声明式的 [`Dataset`][pydantic_evals.dataset.Dataset] `evaluators` kwarg：

```python {title="simple_eval_complete.py"}
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext, IsInstance

case1 = Case(  # (1)!
    name='simple_case',
    inputs='What is the capital of France?',
    expected_output='Paris',
    metadata={'difficulty': 'easy'},
)


class MyEvaluator(Evaluator[str, str]):
    def evaluate(self, ctx: EvaluatorContext[str, str]) -> float:
        if ctx.output == ctx.expected_output:
            return 1.0
        elif (
            isinstance(ctx.output, str)
            and ctx.expected_output.lower() in ctx.output.lower()
        ):
            return 0.8
        else:
            return 0.0


dataset = Dataset(
    name='capital_quiz',
    cases=[case1],
    evaluators=[IsInstance(type_name='str'), MyEvaluator()],  # (2)!
)


async def guess_city(question: str) -> str:  # (3)!
    return 'Paris'


report = dataset.evaluate_sync(guess_city)  # (4)!
report.print(include_input=True, include_output=True, include_durations=False)  # (5)!
"""
                              Evaluation Summary: guess_city
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Case ID     ┃ Inputs                         ┃ Outputs ┃ Scores            ┃ Assertions ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ simple_case │ What is the capital of France? │ Paris   │ MyEvaluator: 1.00 │ ✔          │
├─────────────┼────────────────────────────────┼─────────┼───────────────────┼────────────┤
│ Averages    │                                │         │ MyEvaluator: 1.00 │ 100.0% ✔   │
└─────────────┴────────────────────────────────┴─────────┴───────────────────┴────────────┘
"""
```

1. 像上面一样创建一个[测试用例][pydantic_evals.dataset.Case]
2. 创建一个包含测试 cases 和 [`evaluators`][pydantic_evals.dataset.Dataset.evaluators] 的 [`Dataset`][pydantic_evals.dataset.Dataset]
3. 这是我们要评估的函数。
4. 用 [`evaluate_sync`][pydantic_evals.dataset.Dataset.evaluate_sync] 运行评估。它会针对数据集中的所有测试 cases 运行该函数，并返回一个 [`EvaluationReport`][pydantic_evals.reporting.EvaluationReport] 对象。
5. 用 [`print`][pydantic_evals.reporting.EvaluationReport.print] 打印报告，展示评估结果。这里省略 duration，只是为了避免打印输出每次运行都发生变化。

_（这个示例是完整的，可以直接运行）_

更多示例见[快速开始](evals/quick-start.md)，控制并行执行请参阅[并发与性能](evals/how-to/concurrency.md)。

## API 参考 {#api-reference}

关于所有类、方法和配置选项的完整说明，请参阅详细的 [API 参考文档](https://ai.pydantic.dev/api/pydantic_evals/dataset/)。

## 下一步 {#next-steps}

<!-- TODO - 这里非常适合放一个完整教程或案例研究 -->
1. **从简单评估开始**：[快速开始](evals/quick-start.md)
2. **理解数据模型**：[核心概念](evals/core-concepts.md)
3. **探索内置评估器**：[内置评估器](evals/evaluators/built-in.md)
4. **集成 Logfire** 进行可视化：[Logfire 集成](evals/how-to/logfire-integration.md)
5. **构建全面测试套件**：[数据集管理](evals/how-to/dataset-management.md)
6. **为 domain-specific 指标实现自定义评估器**：[自定义评估器](evals/evaluators/custom.md)
