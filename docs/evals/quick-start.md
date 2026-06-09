# Pydantic Evals 评估 {#pydantic-evals}

**Pydantic Evals** 是一个强大的评估框架，用于系统化测试和评估 AI 系统，范围从简单 LLM 调用到复杂多智能体应用。

## Pydantic Evals 是什么？ {#what-is-pydantic-evals}

Pydantic Evals 帮你：

- **创建测试数据集**，包含类型安全的结构化 inputs 和 expected outputs
- **运行 evaluations**，用自动并发评估你的 AI 系统
- **为结果评分**，使用确定性检查、LLM judges 或自定义 evaluators
- **生成报告**，包含详细 metrics、assertions 和性能数据
- **跟踪变更**，通过比较不同时期的 evaluation runs
- **集成 Logfire**，用于可视化和协作分析

## 安装 {#installation}

```bash
pip install pydantic-evals
```

对于 OpenTelemetry tracing 和 Logfire 集成：

```bash
pip install 'pydantic-evals[logfire]'
```

## 快速开始 {#quick-start}

虽然 evaluations 通常用于测试 AI 系统，但 Pydantic Evals 框架可以用于任何函数调用。为了演示核心功能，我们先从一个简单、确定性的示例开始。

下面是评估简单文本转换函数的完整示例：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains, EqualsExpected

# 创建包含测试 cases 的数据集
dataset = Dataset(
    name='uppercase_tests',
    cases=[
        Case(
            name='uppercase_basic',
            inputs='hello world',
            expected_output='HELLO WORLD',
        ),
        Case(
            name='uppercase_with_numbers',
            inputs='hello 123',
            expected_output='HELLO 123',
        ),
    ],
    evaluators=[
        EqualsExpected(),  # 检查是否与 expected_output 完全匹配
        Contains(value='HELLO', case_sensitive=True),  # 检查是否包含 "HELLO"
    ],
)


# 定义要评估的函数
def uppercase_text(text: str) -> str:
    return text.upper()


# 运行 evaluation
report = dataset.evaluate_sync(uppercase_text)

# 打印结果
report.print()
"""
        Evaluation Summary: uppercase_text
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID                ┃ Assertions ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ uppercase_basic        │ ✔✔         │     10ms │
├────────────────────────┼────────────┼──────────┤
│ uppercase_with_numbers │ ✔✔         │     10ms │
├────────────────────────┼────────────┼──────────┤
│ Averages               │ 100.0% ✔   │     10ms │
└────────────────────────┴────────────┴──────────┘
"""
```

输出：

```
                  Evaluation Summary: uppercase_text
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID                 ┃ Assertions ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ uppercase_basic         │ ✔✔         │     10ms │
├─────────────────────────┼────────────┼──────────┤
│ uppercase_with_numbers  │ ✔✔         │     10ms │
├─────────────────────────┼────────────┼──────────┤
│ Averages                │ 100.0% ✔   │     10ms │
└─────────────────────────┴────────────┴──────────┘
```

## 核心概念 {#key-concepts}

理解几个核心概念，有助于你更充分地使用 Pydantic Evals：

- **[`Dataset`][pydantic_evals.dataset.Dataset]** - 测试 cases 和（可选）evaluators 的集合
- **[`Case`][pydantic_evals.dataset.Case]** - 单个测试场景，包含 inputs、可选 expected outputs 以及 case-specific evaluators
- **[`Evaluator`][pydantic_evals.evaluators.Evaluator]** - 对任务 outputs 评分或验证的函数
- **[`EvaluationReport`][pydantic_evals.reporting.EvaluationReport]** - 运行 evaluation 得到的结果

深入了解请参见 [Core Concepts](core-concepts.md)。

## 常见用例 {#common-use-cases}

### 确定性验证 {#deterministic-validation}

测试你的 AI 系统是否产生结构正确的 outputs：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains, IsInstance

dataset = Dataset(
    name='dict_validation',
    cases=[
        Case(inputs={'data': 'required_key present'}, expected_output={'result': 'success'}),
    ],
    evaluators=[
        IsInstance(type_name='dict'),
        Contains(value='required_key'),
    ],
)
```

### LLM-as-a-Judge Evaluation 评估 {#llm-as-a-judge-evaluation}

使用 LLM 评估准确性或有用性等主观质量：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    name='llm_judge_test',
    cases=[
        Case(inputs='What is the capital of France?', expected_output='Paris'),
    ],
    evaluators=[
        LLMJudge(
            rubric='Response is accurate and helpful',
            include_input=True,
            model='anthropic:claude-sonnet-4-6',
        )
    ],
)
```

### 性能测试 {#performance-testing}

确保你的系统满足性能要求：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import MaxDuration

dataset = Dataset(
    name='performance_test',
    cases=[
        Case(inputs='test input', expected_output='test output'),
    ],
    evaluators=[
        MaxDuration(seconds=2.0),
    ],
)
```

## 后续步骤 {#next-steps}

继续阅读文档了解更多内容：

- **[Core Concepts](core-concepts.md)** - 理解数据模型和 evaluation 流程
- **[Native Evaluators](evaluators/built-in.md)** - 了解所有可用 evaluators
- **[Custom Evaluators](evaluators/custom.md)** - 编写自己的 evaluation 逻辑
- **[Dataset Management](how-to/dataset-management.md)** - 保存、加载和生成数据集
- **[Examples](examples/simple-validation.md)** - 常见场景的实用示例
