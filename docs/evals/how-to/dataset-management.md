# 数据集管理 {#dataset-management}

创建、保存、加载和生成评估数据集。

## 创建数据集 {#creating-datasets}

### 从代码创建 {#from-code}

直接在 Python 中定义 datasets：

```python
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected, IsInstance

dataset = Dataset[str, str, Any](
    name='my_eval_suite',
    cases=[
        Case(
            name='test_1',
            inputs='input 1',
            expected_output='output 1',
        ),
        Case(
            name='test_2',
            inputs='input 2',
            expected_output='output 2',
        ),
    ],
    evaluators=[
        IsInstance(type_name='str'),
        EqualsExpected(),
    ],
)
```

### 动态添加 Cases {#adding-cases-dynamically}

```python
from typing import Any

from pydantic_evals import Dataset
from pydantic_evals.evaluators import IsInstance

dataset = Dataset[str, str, Any](name='dynamic_dataset', cases=[], evaluators=[])

# Add cases one at a time
dataset.add_case(
    name='dynamic_case',
    inputs='test input',
    expected_output='test output',
)

# Add evaluators
dataset.add_evaluator(IsInstance(type_name='str'))
```

## 保存数据集 {#saving-datasets}

!!! info "详细序列化指南"
    关于序列化格式、JSON schema 生成和自定义 evaluators 的完整细节，请参阅[数据集序列化](dataset-serialization.md)。

### 保存为 YAML {#save-to-yaml}

```python
from typing import Any

from pydantic_evals import Case, Dataset

dataset = Dataset[str, str, Any](name='my_eval_suite', cases=[Case(name='test', inputs='example')])
dataset.to_file('my_dataset.yaml')

# Also saves schema file: my_dataset_schema.json
```

输出（`my_dataset.yaml`）：

```yaml
# yaml-language-server: $schema=my_dataset_schema.json
name: my_eval_suite
cases:
- name: test_1
  inputs: input 1
  expected_output: output 1
  evaluators:
  - EqualsExpected
- name: test_2
  inputs: input 2
  expected_output: output 2
  evaluators:
  - EqualsExpected
evaluators:
- IsInstance: str
```

### 保存为 JSON {#save-to-json}

```python
from typing import Any

from pydantic_evals import Case, Dataset

dataset = Dataset[str, str, Any](name='my_eval_suite', cases=[Case(name='test', inputs='example')])
dataset.to_file('my_dataset.json')

# Also saves schema file: my_dataset_schema.json
```

### 自定义 Schema 路径 {#custom-schema-path}

```python
from pathlib import Path
from typing import Any

from pydantic_evals import Case, Dataset

dataset = Dataset[str, str, Any](name='my_eval_suite', cases=[Case(name='test', inputs='example')])

# Custom schema location
Path('data').mkdir(exist_ok=True)
Path('data/schemas').mkdir(parents=True, exist_ok=True)
dataset.to_file(
    'data/my_dataset.yaml',
    schema_path='schemas/my_schema.json',
)

# No schema file
dataset.to_file('my_dataset.yaml', schema_path=None)
```

## 加载数据集 {#loading-datasets}

### 从 YAML/JSON 加载 {#from-yamljson}

```python {test="skip"}
from typing import Any

from pydantic_evals import Dataset

# Infers format from extension
dataset = Dataset[str, str, Any].from_file('my_dataset.yaml')
dataset = Dataset[str, str, Any].from_file('my_dataset.json')

# Explicit format for non-standard extensions
dataset = Dataset[str, str, Any].from_file('data.txt', fmt='yaml')
```

### 从字符串加载 {#from-string}

```python
from typing import Any

from pydantic_evals import Dataset

yaml_content = """
name: my_tests
cases:
- name: test
  inputs: hello
  expected_output: HELLO
evaluators:
- EqualsExpected
"""

dataset = Dataset[str, str, Any].from_text(yaml_content, fmt='yaml')
```

### 从字典加载 {#from-dict}

```python
from typing import Any

from pydantic_evals import Dataset

data = {
    'name': 'my_tests',
    'cases': [
        {
            'name': 'test',
            'inputs': 'hello',
            'expected_output': 'HELLO',
        },
    ],
    'evaluators': [{'EqualsExpected': {}}],
}

dataset = Dataset[str, str, Any].from_dict(data)
```

### 使用自定义 Evaluators {#with-custom-evaluators}

加载使用自定义 evaluators 的数据集时，必须把它们传给 `from_file()`：

```python {test="skip"}
from dataclasses import dataclass
from typing import Any

from pydantic_evals import Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class MyCustomEvaluator(Evaluator):
    threshold: float = 0.5

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


# Load with custom evaluator registry
dataset = Dataset[str, str, Any].from_file(
    'my_dataset.yaml',
    custom_evaluator_types=[MyCustomEvaluator],
)
```

关于使用自定义 evaluators 进行序列化的完整细节，请参阅[数据集序列化](dataset-serialization.md)。

## 生成数据集 {#generating-datasets}

Pydantic Evals 允许你使用 LLM 和 [`generate_dataset`][pydantic_evals.generation.generate_dataset] 生成测试数据集。

Datasets 可以生成 JSON 或 YAML 格式；两种情况下都会在数据集旁边生成 JSON schema 文件，并在数据集中引用它，因此你应该能在编辑器中获得类型检查和自动补全。

```python {title="generate_dataset_example.py"}
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from pydantic_evals import Dataset
from pydantic_evals.generation import generate_dataset


class QuestionInputs(BaseModel, use_attribute_docstrings=True):  # (1)!
    """Model for question inputs."""

    question: str
    """A question to answer"""
    context: str | None = None
    """Optional context for the question"""


class AnswerOutput(BaseModel, use_attribute_docstrings=True):  # (2)!
    """Model for expected answer outputs."""

    answer: str
    """The answer to the question"""
    confidence: float = Field(ge=0, le=1)
    """Confidence level (0-1)"""


class MetadataType(BaseModel, use_attribute_docstrings=True):  # (3)!
    """Metadata model for test cases."""

    difficulty: str
    """Difficulty level (easy, medium, hard)"""
    category: str
    """Question category"""


async def main():
    dataset = await generate_dataset(  # (4)!
        dataset_type=Dataset[QuestionInputs, AnswerOutput, MetadataType],
        n_examples=2,
        extra_instructions="""
        Generate question-answer pairs about world capitals and landmarks.
        Make sure to include both easy and challenging questions.
        """,
    )
    output_file = Path('questions_cases.yaml')
    dataset.to_file(output_file)  # (5)!
    print(output_file.read_text(encoding='utf-8'))
    """
    # yaml-language-server: $schema=questions_cases_schema.json
    name: generated
    cases:
    - name: Easy Capital Question
      inputs:
        question: What is the capital of France?
        context: null
      metadata:
        difficulty: easy
        category: Geography
      expected_output:
        answer: Paris
        confidence: 0.95
      evaluators:
      - EqualsExpected
    - name: Challenging Landmark Question
      inputs:
        question: Which world-famous landmark is located on the banks of the Seine River?
        context: null
      metadata:
        difficulty: hard
        category: Landmarks
      expected_output:
        answer: Eiffel Tower
        confidence: 0.9
      evaluators:
      - EqualsExpected
    evaluators: []
    report_evaluators: []
    """
```

1. 定义 task 输入的 schema。
2. 定义 task 预期输出的 schema。
3. 定义测试 cases metadata 的 schema。
4. 调用 [`generate_dataset`][pydantic_evals.generation.generate_dataset]，创建一个符合 schema 且包含 2 个 cases 的 [`Dataset`][pydantic_evals.dataset.Dataset]。
5. 把 dataset 保存到 YAML 文件。这也会写入 `questions_cases_schema.json`，其中包含 `questions_cases.yaml` 的 JSON schema，方便编辑。这个神奇的 `yaml-language-server` 注释至少受 vscode、jetbrains/pycharm 支持（更多细节见[这里](https://github.com/redhat-developer/yaml-language-server#using-inlined-schema)）。

_（这个示例是完整的，可以直接运行；你需要添加 `asyncio.run(main(answer))` 来运行 `main`）_

你也可以把 datasets 写成 JSON 文件：

```python {title="generate_dataset_example_json.py" requires="generate_dataset_example.py"}
from pathlib import Path

from pydantic_evals import Dataset
from pydantic_evals.generation import generate_dataset

from generate_dataset_example import AnswerOutput, MetadataType, QuestionInputs


async def main():
    dataset = await generate_dataset(  # (1)!
        dataset_type=Dataset[QuestionInputs, AnswerOutput, MetadataType],
        n_examples=2,
        extra_instructions="""
        Generate question-answer pairs about world capitals and landmarks.
        Make sure to include both easy and challenging questions.
        """,
    )
    output_file = Path('questions_cases.json')
    dataset.to_file(output_file)  # (2)!
    print(output_file.read_text(encoding='utf-8'))
    """
    {
      "$schema": "questions_cases_schema.json",
      "name": "generated",
      "cases": [
        {
          "name": "Easy Capital Question",
          "inputs": {
            "question": "What is the capital of France?",
            "context": null
          },
          "metadata": {
            "difficulty": "easy",
            "category": "Geography"
          },
          "expected_output": {
            "answer": "Paris",
            "confidence": 0.95
          },
          "evaluators": [
            "EqualsExpected"
          ]
        },
        {
          "name": "Challenging Landmark Question",
          "inputs": {
            "question": "Which world-famous landmark is located on the banks of the Seine River?",
            "context": null
          },
          "metadata": {
            "difficulty": "hard",
            "category": "Landmarks"
          },
          "expected_output": {
            "answer": "Eiffel Tower",
            "confidence": 0.9
          },
          "evaluators": [
            "EqualsExpected"
          ]
        }
      ],
      "evaluators": [],
      "report_evaluators": []
    }
    """
```

1. 与上面完全相同地生成 [`Dataset`][pydantic_evals.dataset.Dataset]。
2. 把 dataset 保存到 JSON 文件。这也会写入 `questions_cases_schema.json`，其中包含 `questions_cases.json` 的 JSON schema。这次 JSON 文件中包含 `$schema` key，用于定义 IDE 在你编辑该文件时使用的 schema；这没有正式规范，但在 vscode 和 pycharm 中可用，并在 [json-schema-org/json-schema-spec#828](https://github.com/json-schema-org/json-schema-spec/issues/828) 中有深入讨论。

_（这个示例是完整的，可以直接运行；你需要添加 `asyncio.run(main(answer))` 来运行 `main`）_

## 类型安全的数据集 {#type-safe-datasets}

使用泛型类型参数获得类型安全：

```python
from typing_extensions import TypedDict

from pydantic_evals import Case, Dataset


class MyInput(TypedDict):
    query: str
    max_results: int


class MyOutput(TypedDict):
    results: list[str]


class MyMetadata(TypedDict):
    category: str


# Type-safe dataset
dataset: Dataset[MyInput, MyOutput, MyMetadata] = Dataset(
    name='typed_dataset',
    cases=[
        Case(
            name='test',
            inputs={'query': 'test', 'max_results': 10},
            expected_output={'results': ['a', 'b']},
            metadata={'category': 'search'},
        ),
    ],
)
```

## Schema 生成 {#schema-generation}

生成 JSON Schema 以支持 IDE：

```python
from typing import Any

from pydantic_evals import Case, Dataset

dataset = Dataset[str, str, Any](name='my_eval_suite', cases=[Case(name='test', inputs='example')])

# Save with schema
dataset.to_file('my_dataset.yaml')  # Creates my_dataset_schema.json

# Schema enables:
# - Autocomplete in VS Code/PyCharm
# - Validation while editing
# - Inline documentation
```

手动生成 schema：

```python
import json
from dataclasses import dataclass
from typing import Any

from pydantic_evals import Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class MyCustomEvaluator(Evaluator):
    threshold: float = 0.5

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


schema = Dataset[str, str, Any].model_json_schema_with_evaluators(
    custom_evaluator_types=[MyCustomEvaluator],
)
print(json.dumps(schema, indent=2)[:66] + '...')
"""
{
  "$defs": {
    "Case": {
      "additionalProperties": false,
...
"""
```

## 最佳实践 {#best-practices}

### 1. 使用清晰名称 {#1-use-clear-names}

```python
from pydantic_evals import Case

# Good
Case(name='uppercase_basic_ascii', inputs='hello')
Case(name='uppercase_unicode_emoji', inputs='hello 😀')
Case(name='uppercase_empty_string', inputs='')

# Bad
Case(name='test1', inputs='hello')
Case(name='test2', inputs='world')
Case(name='test3', inputs='foo')
```

### 2. 按难度组织 {#2-organize-by-difficulty}

```python
from pydantic_evals import Case, Dataset

dataset = Dataset(
    name='organized_by_difficulty',
    cases=[
        Case(name='easy_1', inputs='test', metadata={'difficulty': 'easy'}),
        Case(name='easy_2', inputs='test2', metadata={'difficulty': 'easy'}),
        Case(name='medium_1', inputs='test3', metadata={'difficulty': 'medium'}),
        Case(name='hard_1', inputs='test4', metadata={'difficulty': 'hard'}),
    ],
)
```

### 3. 从小开始，逐步增长 {#3-start-small-grow-gradually}

```python
from pydantic_evals import Case, Dataset

# Start with representative cases
dataset = Dataset(
    name='starting_small',
    cases=[
        Case(name='happy_path', inputs='test'),
        Case(name='edge_case', inputs=''),
        Case(name='error_case', inputs='invalid'),
    ],
)

# Add more as you find issues
dataset.add_case(name='newly_discovered_edge_case', inputs='edge')
```

### 4. 适当使用 Case-specific Evaluators {#4-use-case-specific-evaluators-where-appropriate}

Case-specific evaluators 允许不同 cases 拥有不同评估标准，这对于全面的 "test coverage" 很重要。你不必尝试编写一刀切的 evaluators，而是可以为每个场景明确指定 "好" 是什么样。对于 [`LLMJudge`][pydantic_evals.evaluators.LLMJudge] evaluators，这一点尤其强大，因为你可以按 case 描述细致需求，从而轻松构建并维护 golden datasets。详细指导见 [Case-specific evaluators](../evaluators/overview.md#case-specific-evaluators)。

### 5. 按用途分离 Datasets {#5-separate-datasets-by-purpose}

```python
from typing import Any

from pydantic_evals import Case, Dataset

# First create some test datasets
for name in ['smoke_tests', 'comprehensive_tests', 'regression_tests']:
    test_dataset = Dataset[str, Any, Any](name=name, cases=[Case(name='test', inputs='example')])
    test_dataset.to_file(f'{name}.yaml')

# Smoke tests (fast, critical paths)
smoke_tests = Dataset[str, Any, Any].from_file('smoke_tests.yaml')

# Comprehensive tests (slow, thorough)
comprehensive = Dataset[str, Any, Any].from_file('comprehensive_tests.yaml')

# Regression tests (specific bugs)
regression = Dataset[str, Any, Any].from_file('regression_tests.yaml')
```

## 下一步 {#next-steps}

- **[数据集序列化](dataset-serialization.md)** - 保存和加载 datasets 的深入指南
- **[生成数据集](#generating-datasets)** - 使用 LLMs 生成测试 cases
- **[示例：简单验证](../examples/simple-validation.md)** - 实用示例
