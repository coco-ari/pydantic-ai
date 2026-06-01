# Pydantic Evals

[![CI](https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml/badge.svg?event=push)](https://github.com/pydantic/pydantic-ai/actions/workflows/ci.yml?query=branch%3Amain)
[![Coverage](https://coverage-badge.samuelcolvin.workers.dev/pydantic/pydantic-ai.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/pydantic/pydantic-ai)
[![PyPI](https://img.shields.io/pypi/v/pydantic-evals.svg)](https://pypi.python.org/pypi/pydantic-evals)
[![python versions](https://img.shields.io/pypi/pyversions/pydantic-evals.svg)](https://github.com/pydantic/pydantic-ai)
[![license](https://img.shields.io/github/license/pydantic/pydantic-ai.svg)](https://github.com/pydantic/pydantic-ai/blob/main/LICENSE)

这是一个用于评估 Python 中非确定性（或“随机”）函数的库。它提供了一个简单、Pythonic 的接口，用于定义和运行随机函数，并分析这些函数的运行结果。

虽然这个库作为 [Pydantic AI](https://ai.pydantic.dev) 的一部分开发，但它在内部只把 Pydantic AI 用于一小部分生成式功能，并且设计上可以配合任意“随机函数”实现使用。尤其是，它可以与其他（非 Pydantic AI）AI 库、智能体框架等一起使用。

和 Pydantic AI 一样，这个库优先考虑类型安全和常见 Python 语法的使用，而不是晦涩、领域特定的 Python 语法用法。

完整文档见 [ai.pydantic.dev/evals](https://ai.pydantic.dev/evals)。

## 示例

通常你会把 Pydantic Evals 用于更复杂的函数（例如 Pydantic AI 智能体或图），但下面是一个快速示例：使用自定义评估器和内置评估器，根据一个测试用例评估一个简单函数。

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext, IsInstance

# 定义一个包含输入和预期输出的测试用例
case = Case(
    name='capital_question',
    inputs='What is the capital of France?',
    expected_output='Paris',
)

# 定义一个自定义评估器
class MatchAnswer(Evaluator[str, str]):
    def evaluate(self, ctx: EvaluatorContext[str, str]) -> float:
        if ctx.output == ctx.expected_output:
            return 1.0
        elif isinstance(ctx.output, str) and ctx.expected_output.lower() in ctx.output.lower():
            return 0.8
        return 0.0

# 用测试用例和评估器创建数据集
dataset = Dataset(
    name='capital_eval',
    cases=[case],
    evaluators=[IsInstance(type_name='str'), MatchAnswer()],
)

# 定义要评估的函数
async def answer_question(question: str) -> str:
    return 'Paris'

# 运行评估
report = dataset.evaluate_sync(answer_question)
report.print(include_input=True, include_output=True)
"""
                                    Evaluation Summary: answer_question
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID          ┃ Inputs                         ┃ Outputs ┃ Scores            ┃ Assertions ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ capital_question │ What is the capital of France? │ Paris   │ MatchAnswer: 1.00 │ ✔          │     10ms │
├──────────────────┼────────────────────────────────┼─────────┼───────────────────┼────────────┼──────────┤
│ Averages         │                                │         │ MatchAnswer: 1.00 │ 100.0% ✔   │     10ms │
└──────────────────┴────────────────────────────────┴─────────┴───────────────────┴────────────┴──────────┘
"""
```

将这个库用于更复杂的函数（例如 Pydantic AI 智能体）时也类似：你只需要定义一个任务函数来包装要评估的函数，并让它的签名匹配测试用例的输入和输出。

## Logfire 集成

Pydantic Evals 使用 OpenTelemetry 为评估中的每个 case 记录 trace。

你可以把这些 trace 发送到任何兼容 OpenTelemetry 的后端。为了获得最佳体验，我们推荐 [Pydantic Logfire](https://logfire.pydantic.dev/docs)，它包含针对 evals 的自定义视图：

<div style="display: flex; gap: 1rem; flex-wrap: wrap;">
  <img src="https://ai.pydantic.dev/img/logfire-evals-overview.png" alt="Logfire Evals Overview" width="48%">
  <img src="https://ai.pydantic.dev/img/logfire-evals-case.png" alt="Logfire Evals Case View" width="48%">
</div>

你将看到输入、输出、token 使用量、执行耗时等完整细节。你还可以访问每个 case 的完整 trace，这非常适合调试、编写路径感知评估器，或针对生产 trace 运行类似评估。

基础设置：

```python {test="skip" lint="skip" format="skip"}
import logfire

logfire.configure(
    send_to_logfire='if-token-present',
    environment='development',
    service_name='evals',
)

...

my_dataset.evaluate_sync(my_task)
```

[在这里阅读更多关于 Logfire 集成的内容。](https://ai.pydantic.dev/evals/#logfire-integration)
