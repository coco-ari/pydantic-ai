# LLM Judge 深入说明 {#llm-judge-deep-dive}

[`LLMJudge`][pydantic_evals.evaluators.LLMJudge] 评估器使用 LLM 根据评分规则评估输出的主观质量。

## 何时使用 LLM-as-a-Judge {#when-to-use-llm-as-a-judge}

LLM judges 非常适合评估需要理解和判断的质量：

**适合的使用场景：**

- 事实准确性
- 有帮助程度和相关性
- 语气和风格合规
- 响应完整性
- 遵循复杂指令
- RAG groundedness（答案是否使用了提供的上下文？）
- 引用准确性

**不适合的使用场景：**

- 格式验证（改用 [`IsInstance`][pydantic_evals.evaluators.IsInstance]）
- 精确匹配（使用 [`EqualsExpected`][pydantic_evals.evaluators.EqualsExpected]）
- 性能检查（使用 [`MaxDuration`][pydantic_evals.evaluators.MaxDuration]）
- 确定性逻辑（编写自定义 evaluator）

## 基础用法 {#basic-usage}

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    name='factual_accuracy',
    cases=[Case(inputs='test')],
    evaluators=[
        LLMJudge(rubric='Response is factually accurate'),
    ],
)
```

## 配置选项 {#configuration-options}

### Rubric

`rubric` 是你的评估标准。应具体且清晰：

**不好的 rubrics（模糊）：**
```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(rubric='Good response')  # Too vague
LLMJudge(rubric='Check quality')  # What aspect of quality?
```

**好的 rubrics（具体）：**
```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(rubric='Response directly answers the user question without hallucination')
LLMJudge(rubric='Response uses formal, professional language appropriate for business communication')
LLMJudge(rubric='All factual claims in the response are supported by the provided context')
```

### 包含上下文 {#including-context}

控制 judge 能看到哪些信息：

```python
from pydantic_evals.evaluators import LLMJudge

# Output only (default)
LLMJudge(rubric='Response is polite')

# Output + Input
LLMJudge(
    rubric='Response accurately answers the input question',
    include_input=True,
)

# Output + Input + Expected Output
LLMJudge(
    rubric='Response is semantically equivalent to the expected output',
    include_input=True,
    include_expected_output=True,
)
```

**示例：**
```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    name='math_check',
    cases=[
        Case(
            inputs='What is 2+2?',
            expected_output='4',
        ),
    ],
    evaluators=[
        # This judge sees: output + inputs + expected_output
        LLMJudge(
            rubric='Response provides the same answer as expected, possibly with explanation',
            include_input=True,
            include_expected_output=True,
        ),
    ],
)
```

### 模型选择 {#model-selection}

根据成本/质量权衡选择 judge model：

```python
from pydantic_evals.evaluators import LLMJudge

# Default: GPT-4o (good balance)
LLMJudge(rubric='...')

# Anthropic Claude (alternative default)
LLMJudge(
    rubric='...',
    model='anthropic:claude-sonnet-4-6',
)

# Cheaper option for simple checks
LLMJudge(
    rubric='Response contains profanity',
    model='openai:gpt-5-mini',
)

# Premium option for nuanced evaluation
LLMJudge(
    rubric='Response demonstrates deep understanding of quantum mechanics',
    model='anthropic:claude-opus-4-5',
)
```

### 模型设置 {#model-settings}

自定义模型行为：

```python
from pydantic_ai import ModelSettings
from pydantic_evals.evaluators import LLMJudge

LLMJudge(
    rubric='...',
    model_settings=ModelSettings(
        temperature=0.0,  # Deterministic evaluation
        max_tokens=100,  # Shorter responses
    ),
)
```

## 输出模式 {#output-modes}

### 仅断言（默认） {#assertion-only-default}

返回带原因的通过/失败：

```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(rubric='Response is accurate')
# Returns: {'LLMJudge_pass': EvaluationReason(value=True, reason='...')}
```

在报告中：
```
┃ Assertions ┃
┃ ✔          ┃
```

### 仅分数 {#score-only}

返回数值分数（0.0 到 1.0）：

```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(
    rubric='Response quality',
    score={'include_reason': True},
    assertion=False,
)
# Returns: {'LLMJudge_score': EvaluationReason(value=0.85, reason='...')}
```

在报告中：
```
┃ Scores             ┃
┃ LLMJudge_score: 0.85 ┃
```

### 同时返回分数和断言 {#both-score-and-assertion}

```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(
    rubric='Response quality',
    score={'include_reason': True},
    assertion={'include_reason': True},
)
# Returns: {
#     'LLMJudge_score': EvaluationReason(value=0.85, reason='...'),
#     'LLMJudge_pass': EvaluationReason(value=True, reason='...'),
# }
```

### 自定义名称 {#custom-names}

```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(
    rubric='Response is factually accurate',
    assertion={
        'evaluation_name': 'accuracy',
        'include_reason': True,
    },
)
# Returns: {'accuracy': EvaluationReason(value=True, reason='...')}
```

在报告中：
```
┃ Assertions ┃
┃ accuracy: ✔ ┃
```

## 实用示例 {#practical-examples}

### RAG 评估 {#rag-evaluation}

评估 RAG 系统是否使用了提供的上下文：

```python
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge


@dataclass
class RAGInput:
    question: str
    context: str


dataset = Dataset(
    name='rag_evaluation',
    cases=[
        Case(
            inputs=RAGInput(
                question='What is the capital of France?',
                context='France is a country in Europe. Its capital is Paris.',
            ),
        ),
    ],
    evaluators=[
        LLMJudge(
            rubric='Response answers the question using only information from the provided context',
            include_input=True,
            assertion={'evaluation_name': 'grounded', 'include_reason': True},
        ),
        LLMJudge(
            rubric='Response cites specific quotes or facts from the context',
            include_input=True,
            assertion={'evaluation_name': 'uses_citations', 'include_reason': True},
        ),
    ],
)
```

### 使用 Case-Specific Rubrics 生成食谱 {#recipe-generation-with-case-specific-rubrics}

这个示例展示如何同时使用 dataset-level 和 case-specific evaluators：

```python {title="recipe_evaluation.py" test="skip"}
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from pydantic_ai import Agent, format_as_xml
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance, LLMJudge


class CustomerOrder(BaseModel):
    dish_name: str
    dietary_restriction: str | None = None


class Recipe(BaseModel):
    ingredients: list[str]
    steps: list[str]


recipe_agent = Agent(
    'openai:gpt-5-mini',
    output_type=Recipe,
    instructions=(
        'Generate a recipe to cook the dish that meets the dietary restrictions.'
    ),
)


async def transform_recipe(customer_order: CustomerOrder) -> Recipe:
    r = await recipe_agent.run(format_as_xml(customer_order))
    return r.output


recipe_dataset = Dataset[CustomerOrder, Recipe, Any](
    name='recipe_evaluation',
    cases=[
        Case(
            name='vegetarian_recipe',
            inputs=CustomerOrder(
                dish_name='Spaghetti Bolognese', dietary_restriction='vegetarian'
            ),
            expected_output=None,
            metadata={'focus': 'vegetarian'},
            evaluators=(  # (1)!
                LLMJudge(
                    rubric='Recipe should not contain meat or animal products',
                ),
            ),
        ),
        Case(
            name='gluten_free_recipe',
            inputs=CustomerOrder(
                dish_name='Chocolate Cake', dietary_restriction='gluten-free'
            ),
            expected_output=None,
            metadata={'focus': 'gluten-free'},
            evaluators=(  # (2)!
                LLMJudge(
                    rubric='Recipe should not contain gluten or wheat products',
                ),
            ),
        ),
    ],
    evaluators=[  # (3)!
        IsInstance(type_name='Recipe'),
        LLMJudge(
            rubric='Recipe should have clear steps and relevant ingredients',
            include_input=True,
            model='anthropic:claude-sonnet-4-6',
        ),
    ],
)


report = recipe_dataset.evaluate_sync(transform_recipe)
print(report)
"""
     Evaluation Summary: transform_recipe
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID            ┃ Assertions ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ vegetarian_recipe  │ ✔✔✔        │    38.1s │
├────────────────────┼────────────┼──────────┤
│ gluten_free_recipe │ ✔✔✔        │    22.4s │
├────────────────────┼────────────┼──────────┤
│ Averages           │ 100.0% ✔   │    30.3s │
└────────────────────┴────────────┴──────────┘
"""
```

1. Case-specific evaluator：只针对 vegetarian recipe case 运行
2. Case-specific evaluator：只针对 gluten-free recipe case 运行
3. Dataset-level evaluators：针对所有 cases 运行

### 多维度评估 {#multi-aspect-evaluation}

使用多个 judges 评估不同质量维度：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    name='multi_aspect',
    cases=[Case(inputs='test')],
    evaluators=[
        # Accuracy
        LLMJudge(
            rubric='Response is factually accurate',
            include_input=True,
            assertion={'evaluation_name': 'accurate'},
        ),

        # Helpfulness
        LLMJudge(
            rubric='Response is helpful and actionable',
            include_input=True,
            score={'evaluation_name': 'helpfulness'},
            assertion=False,
        ),

        # Tone
        LLMJudge(
            rubric='Response uses professional, respectful language',
            assertion={'evaluation_name': 'professional_tone'},
        ),

        # Safety
        LLMJudge(
            rubric='Response contains no harmful, biased, or inappropriate content',
            assertion={'evaluation_name': 'safe'},
        ),
    ],
)
```

### 比较式评估 {#comparative-evaluation}

将输出与预期输出比较：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

dataset = Dataset(
    name='comparative_eval',
    cases=[
        Case(
            name='translation',
            inputs='Hello world',
            expected_output='Bonjour le monde',
        ),
    ],
    evaluators=[
        LLMJudge(
            rubric='Response is semantically equivalent to the expected output',
            include_input=True,
            include_expected_output=True,
            score={'evaluation_name': 'semantic_similarity'},
            assertion={'evaluation_name': 'correct_meaning'},
        ),
    ],
)
```

## 最佳实践 {#best-practices}

### 1. Rubrics 要具体 {#1-be-specific-in-rubrics}

**不好：**
```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(rubric='Good answer')
```

**更好：**
```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(rubric='Response accurately answers the question without hallucinating facts')
```

**最好：**
```python
from pydantic_evals.evaluators import LLMJudge

LLMJudge(
    rubric='''
    Response must:
    1. Directly answer the question asked
    2. Use only information from the provided context
    3. Cite specific passages from the context
    4. Acknowledge if information is insufficient
    ''',
    include_input=True,
)
```

### 2. 使用多个 Judges {#2-use-multiple-judges}

不要总是试图用一个 rubric 评估所有内容：

```python
from pydantic_evals.evaluators import LLMJudge

# Instead of this:
LLMJudge(rubric='Response is good, accurate, helpful, and safe')

# Do this:
evaluators = [
    LLMJudge(rubric='Response is factually accurate'),
    LLMJudge(rubric='Response is helpful and actionable'),
    LLMJudge(rubric='Response is safe and appropriate'),
]
```

### 3. 与确定性检查组合 {#3-combine-with-deterministic-checks}

不要把 LLM evaluation 用在可以确定性完成的检查上：

```python
from pydantic_evals.evaluators import Contains, IsInstance, LLMJudge

evaluators = [
    IsInstance(type_name='str'),
    Contains(value='required_section'),
    LLMJudge(rubric='Response quality is high'),
]
```

### 4. 使用 Temperature 0 保持一致性 {#4-use-temperature-0-for-consistency}

```python
from pydantic_ai import ModelSettings
from pydantic_evals.evaluators import LLMJudge

LLMJudge(
    rubric='...',
    model_settings=ModelSettings(temperature=0.0),
)
```


## 限制 {#limitations}

### 非确定性 {#non-determinism}

LLM judges 不是确定性的。同一输出在不同运行中可能获得不同分数。

**缓解：**

- 使用 `temperature=0.0` 获得更高一致性
- 运行多次评估并求平均
- 对不稳定评估使用重试策略

### 成本 {#cost}

LLM judges 会发起 API 调用，这会花费金钱和时间。

**缓解：**

- 对简单检查使用更便宜的模型（`gpt-5-mini`）
- 先运行确定性检查以快速失败
- 尽可能缓存结果
- 只评估发生变化的 cases

### 模型偏见 {#model-biases}

LLM judges 会继承训练数据中的偏见。

**缓解：**

- 使用多个 judge models 并比较
- 审查评估原因，而不只是分数
- 用人工标注测试集验证 judges
- 注意已知偏见（长度偏见、风格偏好）

### 上下文限制 {#context-limits}

Judges 对输入有 token 限制。

**缓解：**

- 智能截断长输入/输出
- 使用不需要完整上下文的聚焦 rubrics
- 对超长内容考虑分块评估

## 调试 LLM Judges {#debugging-llm-judges}

### 查看原因 {#view-reasons}

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge


def my_task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(
    name='debug_reasons',
    cases=[Case(inputs='test')],
    evaluators=[LLMJudge(rubric='Response is clear')],
)
report = dataset.evaluate_sync(my_task)
report.print(include_reasons=True)
"""
     Evaluation Summary: my_task
┏━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID  ┃ Assertions  ┃ Duration ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Case 1   │ LLMJudge: ✔ │     10ms │
│          │   Reason: - │          │
│          │             │          │
│          │             │          │
├──────────┼─────────────┼──────────┤
│ Averages │ 100.0% ✔    │     10ms │
└──────────┴─────────────┴──────────┘
"""
```

输出：
```
┃ Assertions              ┃
┃ accuracy: ✔            ┃
┃   Reason: The response │
┃   correctly states...  │
```

### 以编程方式访问 {#access-programmatically}

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge


def my_task(inputs: str) -> str:
    return f'Result: {inputs}'


dataset = Dataset(
    name='programmatic_access',
    cases=[Case(inputs='test')],
    evaluators=[LLMJudge(rubric='Response is clear')],
)
report = dataset.evaluate_sync(my_task)
for case in report.cases:
    for name, result in case.assertions.items():
        print(f'{name}: {result.value}')
        #> LLMJudge: True
        if result.reason:
            print(f'  Reason: {result.reason}')
            #>   Reason: -
```

### 比较 Judges {#compare-judges}

使用不同 judge models 测试相同 cases：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge


def my_task(inputs: str) -> str:
    return f'Result: {inputs}'


judges = [
    LLMJudge(rubric='Response is clear', model='openai:gpt-5.2'),
    LLMJudge(rubric='Response is clear', model='anthropic:claude-sonnet-4-6'),
    LLMJudge(rubric='Response is clear', model='openai:gpt-5-mini'),
]

for judge in judges:
    dataset = Dataset(name='judge_comparison', cases=[Case(inputs='test')], evaluators=[judge])
    report = dataset.evaluate_sync(my_task)
    # Compare results
```

## 高级：自定义 Judge Models {#advanced-custom-judge-models}

为所有 `LLMJudge` evaluators 设置默认 judge model：

```python
from pydantic_evals.evaluators import LLMJudge
from pydantic_evals.evaluators.llm_as_a_judge import set_default_judge_model

# Set default to Claude
set_default_judge_model('anthropic:claude-sonnet-4-6')

# Now all LLMJudge instances use Claude by default
LLMJudge(rubric='...')  # Uses Claude
```

## 下一步 {#next-steps}

- **[自定义评估器](custom.md)** - 编写自定义评估逻辑
- **[原生评估器](built-in.md)** - 完整评估器参考
