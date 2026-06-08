# 原生评估器 {#native-evaluators}

Pydantic Evals 为常见评估任务提供了几个内置评估器。

## 比较评估器 {#comparison-evaluators}

### EqualsExpected

检查输出是否与用例中的预期输出完全相等。

```python
from pydantic_evals.evaluators import EqualsExpected

EqualsExpected()
```

**参数：** 无

**返回：** `bool` - 如果 `ctx.output == ctx.expected_output` 则为 `True`

**示例：**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected

dataset = Dataset(
    name='equals_expected_demo',
    cases=[
        Case(
            name='addition',
            inputs='2 + 2',
            expected_output='4',
        ),
    ],
    evaluators=[EqualsExpected()],
)
```

**说明：**

- 如果 `expected_output` 为 `None`，会跳过评估（返回空字典 `{}`）
- 使用 Python 的 `==` 运算符，因此适用于任何可比较类型
- 对于结构化数据，会比较嵌套结构是否相等

---

### Equals

检查输出是否等于指定值。

```python
from pydantic_evals.evaluators import Equals

Equals(value='expected_result')
```

**参数：**

- `value` (Any)：要与输出比较的值
- `evaluation_name` (str | None)：报告中此评估的自定义名称

**返回：** `bool` - 如果 `ctx.output == value` 则为 `True`

**示例：**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Equals

# Check output is always "success"
dataset = Dataset(
    name='equals_demo',
    cases=[Case(inputs='test')],
    evaluators=[
        Equals(value='success', evaluation_name='is_success'),
    ],
)
```

**使用场景：**

- 检查哨兵值
- 验证输出是否保持一致
- 测试是否分类到特定类别

---

### Contains

检查输出是否包含指定值或子字符串。

```python
from pydantic_evals.evaluators import Contains

Contains(
    value='substring',
    case_sensitive=True,
    as_strings=False,
)
```

**参数：**

- `value` (Any)：要搜索的值
- `case_sensitive` (bool)：字符串比较是否区分大小写（默认：`True`）
- `as_strings` (bool)：检查前是否将两个值都转换为字符串（默认：`False`）
- `evaluation_name` (str | None)：报告中此评估的自定义名称

**返回：** [`EvaluationReason`][pydantic_evals.evaluators.EvaluationReason] - 带解释的通过/失败结果

**行为：**

对于**字符串**：检查是否包含子字符串

- `Contains(value='hello', case_sensitive=False)`
  - 匹配："Hello World"、"say hello"、"HELLO"
  - 不匹配："hi there"

对于**列表/元组**：检查成员关系

- `Contains(value='apple')`
  - 匹配：`['apple', 'banana']`、`('apple',)`
  - 不匹配：`['apples', 'orange']`

对于**字典**：检查键值对

- `Contains(value={'name': 'Alice'})`
  - 匹配：`{'name': 'Alice', 'age': 30}`
  - 不匹配：`{'name': 'Bob'}`

**示例：**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains

dataset = Dataset(
    name='contains_demo',
    cases=[Case(inputs='test')],
    evaluators=[
        # Check for required keywords
        Contains(value='terms and conditions', case_sensitive=False),
        # Check for PII (fail if found)
        # Note: Use a custom evaluator that returns False when PII found
    ],
)
```

**使用场景：**

- 必需内容校验
- 关键词检测
- PII/敏感数据检测
- 多值验证

---

## 类型验证 {#type-validation}

### IsInstance

检查输出是否为给定名称对应类型的实例。

```python
from pydantic_evals.evaluators import IsInstance

IsInstance(type_name='str')
```

**参数：**

- `type_name` (str)：要检查的类型名称（使用 `__name__` 或 `__qualname__`）
- `evaluation_name` (str | None)：报告中此评估的自定义名称

**返回：** [`EvaluationReason`][pydantic_evals.evaluators.EvaluationReason] - 带类型信息的通过/失败结果

**示例：**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance

dataset = Dataset(
    name='isinstance_demo',
    cases=[Case(inputs='test')],
    evaluators=[
        # Check output is always a string
        IsInstance(type_name='str'),
        # Check for Pydantic model
        IsInstance(type_name='MyModel'),
        # Check for dict
        IsInstance(type_name='dict'),
    ],
)
```

**说明：**

- 同时匹配类型的 `__name__` 和 `__qualname__`
- 适用于内置类型（`str`、`int`、`dict`、`list` 等）
- 适用于自定义类和 Pydantic 模型
- 会检查完整的 MRO（Method Resolution Order）以支持继承

**使用场景：**

- 格式验证
- 结构化输出校验
- 类型一致性检查

---

## 性能评估 {#performance-evaluation}

### MaxDuration

检查任务执行时间是否低于最大阈值。

```python
from datetime import timedelta

from pydantic_evals.evaluators import MaxDuration

MaxDuration(seconds=2.0)
# or
MaxDuration(seconds=timedelta(seconds=2))
```

**参数：**

- `seconds` (float | timedelta)：允许的最大耗时

**返回：** `bool` - 如果 `ctx.duration <= seconds` 则为 `True`

**示例：**

```python
from datetime import timedelta

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import MaxDuration

dataset = Dataset(
    name='max_duration_demo',
    cases=[Case(inputs='test')],
    evaluators=[
        # SLA: must respond in under 2 seconds
        MaxDuration(seconds=2.0),
        # Or using timedelta
        MaxDuration(seconds=timedelta(milliseconds=500)),
    ],
)
```

**使用场景：**

- SLA 合规性
- 性能回归测试
- 延迟要求
- 超时验证

**另见：** [并发与性能](../how-to/concurrency.md)

---

## LLM 作为裁判 {#llm-as-a-judge}

### LLMJudge

使用 LLM 按照评分规则评估主观质量。

```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(
    rubric='Response is accurate and helpful',
    model='openai:gpt-5.2',
    include_input=False,
    include_expected_output=False,
    model_settings=None,
    score=False,
    assertion={'include_reason': True},
)
```

**参数：**

- `rubric` (str)：评估标准（必填）
- `model` (Model | KnownModelName | None)：要使用的模型（默认：`'openai:gpt-5.2'`）
- `include_input` (bool)：是否在提示中包含任务输入（默认：`False`）
- `include_expected_output` (bool)：是否在提示中包含预期输出（默认：`False`）
- `model_settings` (ModelSettings | None)：自定义模型设置
- `score` (OutputConfig | False)：配置分数输出（默认：`False`）
- `assertion` (OutputConfig | False)：配置断言输出（默认：包含原因）

**返回：** 取决于 `score` 和 `assertion` 参数（见下文）

**输出模式：**

默认返回带原因的**布尔断言**：

- `LLMJudge(rubric='Response is polite')`
  - 返回：`{'LLMJudge_pass': EvaluationReason(value=True, reason='...')}`

改为返回**分数**（0.0 到 1.0）：

- `LLMJudge(rubric='Response quality', score={'include_reason': True}, assertion=False)`
  - 返回：`{'LLMJudge_score': EvaluationReason(value=0.85, reason='...')}`

同时返回**分数**和**断言**：

- `LLMJudge(rubric='Response quality', score={'include_reason': True}, assertion={'include_reason': True})`
  - 返回：`{'LLMJudge_score': EvaluationReason(value=0.85, reason='...'), 'LLMJudge_pass': EvaluationReason(value=True, reason='...')}`

**自定义评估名称：**

- `LLMJudge(rubric='Response is factually accurate', assertion={'evaluation_name': 'accuracy', 'include_reason': True})`
  - 返回：`{'accuracy': EvaluationReason(value=True, reason='...')}`

**示例：**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    name='llm_judge_demo',
    cases=[Case(inputs='test', expected_output='result')],
    evaluators=[
        # Basic accuracy check
        LLMJudge(
            rubric='Response is factually accurate',
            include_input=True,
        ),
        # Quality score with different model
        LLMJudge(
            rubric='Overall response quality',
            model='anthropic:claude-sonnet-4-6',
            score={'evaluation_name': 'quality', 'include_reason': False},
            assertion=False,
        ),
        # Check against expected output
        LLMJudge(
            rubric='Response matches the expected answer semantically',
            include_input=True,
            include_expected_output=True,
        ),
    ],
)
```

**另见：** [LLM Judge 深入说明](llm-judge.md)

---

## 基于 Span 的评估 {#span-based-evaluation}

### HasMatchingSpan

检查 OpenTelemetry span 是否匹配查询（需要配置 Logfire）。

```python
from pydantic_evals.evaluators import HasMatchingSpan

HasMatchingSpan(
    query={'name_contains': 'tool_call'},
    evaluation_name='called_tool',
)
```

**参数：**

- `query` ([`SpanQuery`][pydantic_evals.otel.SpanQuery])：用于匹配 span 的查询
- `evaluation_name` (str | None)：报告中此评估的自定义名称

**返回：** `bool` - 如果任意 span 匹配该查询则为 `True`

**示例：**

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import HasMatchingSpan

dataset = Dataset(
    name='span_check_demo',
    cases=[Case(inputs='test')],
    evaluators=[
        # Check that a specific tool was called
        HasMatchingSpan(
            query={'name_contains': 'search_database'},
            evaluation_name='used_database',
        ),
        # Check for errors
        HasMatchingSpan(
            query={'has_attributes': {'error': True}},
            evaluation_name='had_errors',
        ),
        # Check duration constraints
        HasMatchingSpan(
            query={
                'name_equals': 'llm_call',
                'max_duration': 2.0,  # seconds
            },
            evaluation_name='llm_fast_enough',
        ),
    ],
)
```

**另见：** [基于 Span 的评估](span-based.md)

---

## 原生报告评估器 {#native-report-evaluators}

除了上面的用例级评估器，Pydantic Evals 还提供了可分析整个实验结果的报告评估器。
这些评估器通过 `Dataset` 上的 `report_evaluators` 参数传入。

| 报告评估器 | 用途 | 输出 |
|------------------|---------|--------|
| [`ConfusionMatrixEvaluator`][pydantic_evals.evaluators.ConfusionMatrixEvaluator] | 分类混淆矩阵 | `ConfusionMatrix` |
| [`PrecisionRecallEvaluator`][pydantic_evals.evaluators.PrecisionRecallEvaluator] | 带 AUC 的 PR 曲线 | `PrecisionRecall` |

**另见：** [报告评估器](report-evaluators.md)，其中包含完整文档、参数和示例，
也包括如何编写会生成 `ScalarResult` 和 `TableResult` 分析的自定义报告评估器。

---

## 快速参考表 {#quick-reference-table}

### 用例级评估器 {#case-level-evaluators}

| 评估器 | 用途 | 返回类型 | 成本 | 速度 |
|-----------|---------|-------------|------|-------|
| [`EqualsExpected`][pydantic_evals.evaluators.EqualsExpected] | 与预期输出精确匹配 | `bool` | 免费 | 即时 |
| [`Equals`][pydantic_evals.evaluators.Equals] | 等于指定值 | `bool` | 免费 | 即时 |
| [`Contains`][pydantic_evals.evaluators.Contains] | 包含值/子字符串 | `bool` + 原因 | 免费 | 即时 |
| [`IsInstance`][pydantic_evals.evaluators.IsInstance] | 类型验证 | `bool` + 原因 | 免费 | 即时 |
| [`MaxDuration`][pydantic_evals.evaluators.MaxDuration] | 性能阈值 | `bool` | 免费 | 即时 |
| [`LLMJudge`][pydantic_evals.evaluators.LLMJudge] | 主观质量 | `bool` 和/或 `float` | $$ | 慢 |
| [`HasMatchingSpan`][pydantic_evals.evaluators.HasMatchingSpan] | 行为检查 | `bool` | 免费 | 快 |

### 报告级评估器 {#report-level-evaluators}

| 评估器 | 用途 | 输出类型 | 成本 | 速度 |
|-----------|---------|-------------|------|-------|
| [`ConfusionMatrixEvaluator`][pydantic_evals.evaluators.ConfusionMatrixEvaluator] | 分类矩阵 | `ConfusionMatrix` | 免费 | 即时 |
| [`PrecisionRecallEvaluator`][pydantic_evals.evaluators.PrecisionRecallEvaluator] | 带 AUC 的 PR 曲线 | `PrecisionRecall` | 免费 | 即时 |

## 组合评估器 {#combining-evaluators}

最佳实践是组合快速的确定性检查和较慢的 LLM 评估：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import (
    Contains,
    IsInstance,
    LLMJudge,
    MaxDuration,
)

dataset = Dataset(
    name='combined_evaluators',
    cases=[Case(inputs='test')],
    evaluators=[
        # Fast checks first (fail fast)
        IsInstance(type_name='str'),
        Contains(value='required_field'),
        MaxDuration(seconds=2.0),
        # Expensive LLM checks last
        LLMJudge(rubric='Response is helpful and accurate'),
    ],
)
```

这种方式：

1. 立即捕获格式/结构问题
2. 快速验证必需内容
3. 只有在基础检查通过后才运行昂贵的 LLM 评估
4. 提供全面的质量评估

## 下一步 {#next-steps}

- **[LLM Judge](llm-judge.md)** - 深入了解 LLM 作为裁判的评估
- **[自定义评估器](custom.md)** - 编写你自己的评估逻辑
- **[报告评估器](report-evaluators.md)** - 实验范围分析（混淆矩阵、PR 曲线等）
- **[基于 Span 的评估](span-based.md)** - 使用 OpenTelemetry span 进行行为检查
