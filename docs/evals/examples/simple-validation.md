# 示例：简单验证 {#example-simple-validation}

这是一个概念验证示例，用确定性检查评估一个简单的文本转换函数。

## 场景 {#scenario}

我们要测试一个把文本转换为标题大小写的函数。我们希望验证：

- 输出始终是字符串
- 输出匹配预期格式
- 函数能正确处理边界情况
- 性能满足要求

## 完整示例 {#complete-example}

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import (
    Contains,
    EqualsExpected,
    IsInstance,
    MaxDuration,
)


# The function we're testing
def to_title_case(text: str) -> str:
    """Convert text to title case."""
    return text.title()


# Create evaluation dataset
dataset = Dataset(
    name='title_case_validation',
    cases=[
        # Basic functionality
        Case(
            name='basic_lowercase',
            inputs='hello world',
            expected_output='Hello World',
        ),
        Case(
            name='basic_uppercase',
            inputs='HELLO WORLD',
            expected_output='Hello World',
        ),
        Case(
            name='mixed_case',
            inputs='HeLLo WoRLd',
            expected_output='Hello World',
        ),

        # Edge cases
        Case(
            name='empty_string',
            inputs='',
            expected_output='',
        ),
        Case(
            name='single_word',
            inputs='hello',
            expected_output='Hello',
        ),
        Case(
            name='with_punctuation',
            inputs='hello, world!',
            expected_output='Hello, World!',
        ),
        Case(
            name='with_numbers',
            inputs='hello 123 world',
            expected_output='Hello 123 World',
        ),
        Case(
            name='apostrophes',
            inputs="don't stop believin'",
            expected_output="Don'T Stop Believin'",
        ),
    ],
    evaluators=[
        # Always returns a string
        IsInstance(type_name='str'),

        # Matches expected output
        EqualsExpected(),

        # Output should contain capital letters
        Contains(value='H', evaluation_name='has_capitals'),

        # Should be fast (under 1ms)
        MaxDuration(seconds=0.001),
    ],
)


# Run evaluation
if __name__ == '__main__':
    report = dataset.evaluate_sync(to_title_case)

    # Print results
    report.print(include_input=True, include_output=True)
"""
                            Evaluation Summary: to_title_case
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID          ┃ Inputs               ┃ Outputs              ┃ Assertions ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ basic_lowercase  │ hello world          │ Hello World          │ ✔✔✔✗       │     10ms │
├──────────────────┼──────────────────────┼──────────────────────┼────────────┼──────────┤
│ basic_uppercase  │ HELLO WORLD          │ Hello World          │ ✔✔✔✗       │     10ms │
├──────────────────┼──────────────────────┼──────────────────────┼────────────┼──────────┤
│ mixed_case       │ HeLLo WoRLd          │ Hello World          │ ✔✔✔✗       │     10ms │
├──────────────────┼──────────────────────┼──────────────────────┼────────────┼──────────┤
│ empty_string     │ -                    │ -                    │ ✔✔✗✗       │     10ms │
├──────────────────┼──────────────────────┼──────────────────────┼────────────┼──────────┤
│ single_word      │ hello                │ Hello                │ ✔✔✔✗       │     10ms │
├──────────────────┼──────────────────────┼──────────────────────┼────────────┼──────────┤
│ with_punctuation │ hello, world!        │ Hello, World!        │ ✔✔✔✗       │     10ms │
├──────────────────┼──────────────────────┼──────────────────────┼────────────┼──────────┤
│ with_numbers     │ hello 123 world      │ Hello 123 World      │ ✔✔✔✗       │     10ms │
├──────────────────┼──────────────────────┼──────────────────────┼────────────┼──────────┤
│ apostrophes      │ don't stop believin' │ Don'T Stop Believin' │ ✔✔✗✗       │     10ms │
├──────────────────┼──────────────────────┼──────────────────────┼────────────┼──────────┤
│ Averages         │                      │                      │ 68.8% ✔    │     10ms │
└──────────────────┴──────────────────────┴──────────────────────┴────────────┴──────────┘
"""
# Check if all passed
avg = report.averages()
if avg and avg.assertions == 1.0:
    print('\n✅ All tests passed!')
else:
    print(f'\n❌ Some tests failed (pass rate: {avg.assertions:.1%})')
    """
    ❌ Some tests failed (pass rate: 68.8%)
    """
```

## 预期输出 {#expected-output}

```
                        Evaluation Summary: to_title_case
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID           ┃ Inputs               ┃ Outputs               ┃ Assertions ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ basic_lowercase   │ hello world          │ Hello World           │ ✔✔✔✔       │      <1ms│
├───────────────────┼──────────────────────┼───────────────────────┼────────────┼──────────┤
│ basic_uppercase   │ HELLO WORLD          │ Hello World           │ ✔✔✔✔       │      <1ms│
├───────────────────┼──────────────────────┼───────────────────────┼────────────┼──────────┤
│ mixed_case        │ HeLLo WoRLd          │ Hello World           │ ✔✔✔✔       │      <1ms│
├───────────────────┼──────────────────────┼───────────────────────┼────────────┼──────────┤
│ empty_string      │                      │                       │ ✔✔✗✔       │      <1ms│
├───────────────────┼──────────────────────┼───────────────────────┼────────────┼──────────┤
│ single_word       │ hello                │ Hello                 │ ✔✔✔✔       │      <1ms│
├───────────────────┼──────────────────────┼───────────────────────┼────────────┼──────────┤
│ with_punctuation  │ hello, world!        │ Hello, World!         │ ✔✔✔✔       │      <1ms│
├───────────────────┼──────────────────────┼───────────────────────┼────────────┼──────────┤
│ with_numbers      │ hello 123 world      │ Hello 123 World       │ ✔✔✔✔       │      <1ms│
├───────────────────┼──────────────────────┼───────────────────────┼────────────┼──────────┤
│ apostrophes       │ don't stop believin' │ Don'T Stop Believin'  │ ✔✔✔✔       │      <1ms│
├───────────────────┼──────────────────────┼───────────────────────┼────────────┼──────────┤
│ Averages          │                      │                       │ 96.9% ✔    │      <1ms│
└───────────────────┴──────────────────────┴───────────────────────┴────────────┴──────────┘

✅ All tests passed!
```

注意：`empty_string` 用例有一个失败断言（`has_capitals`），因为空字符串不包含大写字母。

## 保存与加载 {#saving-and-loading}

保存数据集以便将来使用：

```python {test="skip"}
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected


# The function we're testing
def to_title_case(text: str) -> str:
    """Convert text to title case."""
    return text.title()


# Create dataset
dataset: Dataset[str, str, Any] = Dataset(
    name='title_case_tests',
    cases=[Case(inputs='test', expected_output='Test')],
    evaluators=[EqualsExpected()],
)

# Save to YAML
dataset.to_file('title_case_tests.yaml')

# Load later
dataset = Dataset.from_file('title_case_tests.yaml')
report = dataset.evaluate_sync(to_title_case)
```

## 添加更多用例 {#adding-more-cases}

当你发现 bug 或边界情况时，把它们加入数据集：

```python {test="skip"}
from pydantic_evals import Dataset

# Load existing dataset
dataset = Dataset.from_file('title_case_tests.yaml')

# Found a bug with unicode
dataset.add_case(
    name='unicode_chars',
    inputs='café résumé',
    expected_output='Café Résumé',
)

# Found a bug with all caps words
dataset.add_case(
    name='acronyms',
    inputs='the USA and FBI',
    expected_output='The Usa And Fbi',  # Python's title() behavior
)

# Test with very long input
dataset.add_case(
    name='long_input',
    inputs=' '.join(['word'] * 1000),
    expected_output=' '.join(['Word'] * 1000),
)

# Save updated dataset
dataset.to_file('title_case_tests.yaml')
```

## 与 pytest 一起使用 {#using-with-pytest}

与 pytest 集成，用于 CI/CD：

```python
import pytest

from pydantic_evals import Dataset


# The function we're testing
def to_title_case(text: str) -> str:
    """Convert text to title case."""
    return text.title()


@pytest.fixture
def title_case_dataset():
    return Dataset.from_file('title_case_tests.yaml')


def test_title_case_evaluation(title_case_dataset):
    """Run evaluation tests."""
    report = title_case_dataset.evaluate_sync(to_title_case)

    # All cases should pass
    avg = report.averages()
    assert avg is not None
    assert avg.assertions == 1.0, f'Some tests failed (pass rate: {avg.assertions:.1%})'


def test_title_case_performance(title_case_dataset):
    """Verify performance."""
    report = title_case_dataset.evaluate_sync(to_title_case)

    # All cases should complete quickly
    for case in report.cases:
        assert case.task_duration < 0.001, f'{case.name} took {case.task_duration}s'
```

## 下一步 {#next-steps}

- **[原生评估器](../evaluators/built-in.md)** - 浏览所有可用评估器
- **[自定义评估器](../evaluators/custom.md)** - 编写你自己的评估逻辑
- **[数据集管理](../how-to/dataset-management.md)** - 保存、加载和管理数据集
- **[并发与性能](../how-to/concurrency.md)** - 优化评估性能
