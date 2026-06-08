# 数据集序列化 {#dataset-serialization}

了解如何以不同格式保存和加载 datasets，并支持自定义 evaluators 和 IDE 集成。

## 概览 {#overview}

Pydantic Evals 支持将 datasets 序列化为两种格式的文件：

- **YAML**（`.yaml`、`.yml`）- 人类可读，非常适合版本控制
- **JSON**（`.json`）- 结构化、机器可读

两种格式都支持：

- 自动生成 JSON schema，用于 IDE 自动补全和验证
- 自定义 evaluator 序列化/反序列化
- 使用泛型参数进行类型安全加载

## YAML 格式 {#yaml-format}

由于可读性和紧凑语法，YAML 是大多数用例的推荐格式。

### 基本示例 {#basic-example}

```python
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected, IsInstance

# 创建带类型参数的数据集
dataset = Dataset[str, str, Any](
    name='my_tests',
    cases=[
        Case(
            name='test_1',
            inputs='hello',
            expected_output='HELLO',
        ),
    ],
    evaluators=[
        IsInstance(type_name='str'),
        EqualsExpected(),
    ],
)

# 保存为 YAML
dataset.to_file('my_tests.yaml')
```

这会创建两个文件：

1. **`my_tests.yaml`** - dataset
2. **`my_tests_schema.json`** - 用于 IDE 支持的 JSON schema

### YAML 输出 {#yaml-output}

```yaml
# yaml-language-server: $schema=my_tests_schema.json
name: my_tests
cases:
- name: test_1
  inputs: hello
  expected_output: HELLO
evaluators:
- IsInstance: str
- EqualsExpected
```

### 用于 IDE 的 JSON Schema {#json-schema-for-ides}

第一行引用 schema 文件：

```yaml
# yaml-language-server: $schema=my_tests_schema.json
```

这会启用：

- **Autocomplete**：在 VS Code、PyCharm 和其他编辑器中自动补全
- **Inline validation**：编辑时内联验证
- **Documentation tooltips**：字段文档提示
- **Error highlighting**：对无效数据高亮错误

!!! note "编辑器支持"
    `yaml-language-server` 注释受以下工具支持：

    - VS Code (with YAML extension)
    - JetBrains IDEs (PyCharm, IntelliJ, etc.)
    - Most editors with YAML language server support

    更多细节请参见 [YAML Language Server docs](https://github.com/redhat-developer/yaml-language-server#using-inlined-schema)。

### 从 YAML 加载 {#loading-from-yaml}

```python
from pathlib import Path
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected, IsInstance

# 先创建并保存数据集
Path('my_tests.yaml').parent.mkdir(exist_ok=True)
dataset = Dataset[str, str, Any](
    name='my_tests',
    cases=[Case(name='test_1', inputs='hello', expected_output='HELLO')],
    evaluators=[IsInstance(type_name='str'), EqualsExpected()],
)
dataset.to_file('my_tests.yaml')

# 使用类型参数加载数据集
dataset = Dataset[str, str, Any].from_file('my_tests.yaml')


def my_task(text: str) -> str:
    return text.upper()


# 运行 evaluation
report = dataset.evaluate_sync(my_task)
```

## JSON 格式 {#json-format}

JSON 格式适合程序化生成，或需要严格结构的场景。

### 基本示例 {#basic-example}

```python
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected

dataset = Dataset[str, str, Any](
    name='my_tests',
    cases=[
        Case(name='test_1', inputs='hello', expected_output='HELLO'),
    ],
    evaluators=[EqualsExpected()],
)

# 保存为 JSON
dataset.to_file('my_tests.json')
```

### JSON 输出 {#json-output}

```json
{
  "$schema": "my_tests_schema.json",
  "name": "my_tests",
  "cases": [
    {
      "name": "test_1",
      "inputs": "hello",
      "expected_output": "HELLO"
    }
  ],
  "evaluators": [
    "EqualsExpected"
  ]
}
```

顶部的 `$schema` key 会启用类似 YAML 的 IDE 支持。

### 从 JSON 加载 {#loading-from-json}

```python
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected

# 先创建并保存数据集
dataset = Dataset[str, str, Any](
    name='my_tests',
    cases=[Case(name='test_1', inputs='hello', expected_output='HELLO')],
    evaluators=[EqualsExpected()],
)
dataset.to_file('my_tests.json')

# 从 JSON 加载
dataset = Dataset[str, str, Any].from_file('my_tests.json')
```

## Schema 生成 {#schema-generation}

### 自动创建 Schema {#automatic-schema-creation}

默认情况下，`to_file()` 会在 dataset 旁边创建 JSON schema 文件：

```python
from typing import Any

from pydantic_evals import Case, Dataset

dataset = Dataset[str, str, Any](name='my_tests', cases=[Case(inputs='test')])

# 同时创建 my_tests.yaml 和 my_tests_schema.json
dataset.to_file('my_tests.yaml')
```

### 自定义 Schema 位置 {#custom-schema-location}

```python
from pathlib import Path
from typing import Any

from pydantic_evals import Case, Dataset

dataset = Dataset[str, str, Any](name='my_tests', cases=[Case(inputs='test')])

# 创建目录
Path('data').mkdir(exist_ok=True)

# 自定义 schema 文件名（相对于 dataset 文件位置）
dataset.to_file(
    'data/my_tests.yaml',
    schema_path='my_schema.json',
)

# 不生成 schema 文件
dataset.to_file('my_tests.yaml', schema_path=None)
```

### Schema Path 模板 {#schema-path-templates}

使用 `{stem}` 引用 dataset 文件名：

```python
from typing import Any

from pydantic_evals import Case, Dataset

dataset = Dataset[str, str, Any](name='my_tests', cases=[Case(inputs='test')])

# 创建：my_tests.yaml 和 my_tests.schema.json
dataset.to_file(
    'my_tests.yaml',
    schema_path='{stem}.schema.json',
)
```

### 手动生成 Schema {#manual-schema-generation}

无需保存 dataset 即可生成 schema：

```python
import json
from typing import Any

from pydantic_evals import Dataset

# 获取特定 dataset 类型的 dict 形式 schema
schema = Dataset[str, str, Any].model_json_schema_with_evaluators()

# 手动保存
with open('custom_schema.json', 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2)
```

## 自定义 Evaluators {#custom-evaluators}

自定义 evaluators 在序列化和反序列化期间需要特殊处理。

### 要求 {#requirements}

自定义 evaluators 必须：

1. 使用 `@dataclass` 装饰
2. 继承自 `Evaluator`
3. 同时传给 `to_file()` 和 `from_file()`

### 完整示例 {#complete-example}

```python
from dataclasses import dataclass
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class CustomThreshold(Evaluator):
    """检查 output 长度是否超过阈值。"""

    min_length: int
    max_length: int = 100

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        length = len(str(ctx.output))
        return self.min_length <= length <= self.max_length


# 创建带自定义 evaluator 的数据集
dataset = Dataset[str, str, Any](
    name='custom_threshold_tests',
    cases=[
        Case(
            name='test_length',
            inputs='example',
            expected_output='long result',
            evaluators=[
                CustomThreshold(min_length=5, max_length=20),
            ],
        ),
    ],
)

# 使用自定义 evaluator types 保存
dataset.to_file(
    'dataset.yaml',
    custom_evaluator_types=[CustomThreshold],
)
```

### 保存后的 YAML {#saved-yaml}

```yaml
# yaml-language-server: $schema=dataset_schema.json
cases:
- name: test_length
  inputs: example
  expected_output: long result
  evaluators:
  - CustomThreshold:
      min_length: 5
      max_length: 20
```

### 使用自定义 Evaluators 加载 {#loading-with-custom-evaluators}

```python
from dataclasses import dataclass
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class CustomThreshold(Evaluator):
    """检查 output 长度是否超过阈值。"""

    min_length: int
    max_length: int = 100

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        length = len(str(ctx.output))
        return self.min_length <= length <= self.max_length


# 先创建并保存数据集
dataset = Dataset[str, str, Any](
    name='custom_threshold_tests',
    cases=[
        Case(
            name='test_length',
            inputs='example',
            expected_output='long result',
            evaluators=[CustomThreshold(min_length=5, max_length=20)],
        ),
    ],
)
dataset.to_file('dataset.yaml', custom_evaluator_types=[CustomThreshold])

# 使用自定义 evaluator registry 加载
dataset = Dataset[str, str, Any].from_file(
    'dataset.yaml',
    custom_evaluator_types=[CustomThreshold],
)
```

!!! warning "重要"
    你必须同时向 `to_file()` 和 `from_file()` 传入 `custom_evaluator_types`。

    - `to_file()`：在 JSON schema 中包含该 evaluator
    - `from_file()`：注册该 evaluator 用于反序列化

## Evaluator 序列化格式 {#evaluator-serialization-formats}

Evaluators 可以序列化为三种形式：

### 1. 仅名称（无参数） {#1-name-only-no-parameters}

```yaml
evaluators:
- EqualsExpected
- IsInstance: str  # 使用默认参数
```

### 2. 单个参数（短格式） {#2-single-parameter-short-form}

```yaml
evaluators:
- IsInstance: str
- Contains: "required text"
- MaxDuration: 2.0
```

### 3. 多个参数（Dict 格式） {#3-multiple-parameters-dict-form}

```yaml
evaluators:
- CustomThreshold:
    min_length: 5
    max_length: 20
- LLMJudge:
    rubric: "Response is accurate"
    model: "openai:gpt-5"
    include_input: true
```

## 格式对比 {#format-comparison}

| 特性 | YAML | JSON |
|---------|------|------|
| 人类可读 | 优秀 | 良好 |
| 注释 | 支持 | 不支持 |
| 紧凑 | 是 | 较冗长 |
| 机器解析 | 良好 | 优秀 |
| IDE 支持 | 支持 | 支持 |
| 版本控制 | diff 清晰 | diff 噪声较多 |

**建议**：大多数情况下使用 YAML；程序化生成时使用 JSON。

## 高级：Evaluator 序列化名称 {#advanced-evaluator-serialization-name}

自定义 evaluator 在序列化文件中的显示方式：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class VeryLongDescriptiveEvaluatorName(Evaluator):
    @classmethod
    def get_serialization_name(cls) -> str:
        return 'ShortName'

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True
```

在 YAML 中：

```yaml
evaluators:
- ShortName  # 而不是 VeryLongDescriptiveEvaluatorName
```

## 故障排查 {#troubleshooting}

### IDE 中找不到 Schema {#schema-not-found-in-ide}

**问题**：YAML 文件不显示自动补全

**解决方案**：

1. **检查 schema path**，位于 YAML 第一行：
   ```yaml
   # yaml-language-server: $schema=correct_schema_name.json
   ```

2. **验证 schema 文件存在**，并位于同一目录

3. **重启 language server**，在 IDE 中操作

4. **安装 YAML extension**（VS Code：Red Hat 的 "YAML"）

### 找不到自定义 Evaluator {#custom-evaluator-not-found}

**问题**：`ValueError: Unknown evaluator name: 'CustomEvaluator'`

**解决方案**：加载时传入 `custom_evaluator_types`：

```python
from dataclasses import dataclass
from typing import Any

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class CustomEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


# 先创建并使用自定义 evaluator 保存
dataset = Dataset[str, str, Any](
    name='custom_eval_tests',
    cases=[Case(inputs='test', evaluators=[CustomEvaluator()])],
)
dataset.to_file('tests.yaml', custom_evaluator_types=[CustomEvaluator])

# 使用自定义 evaluator types 加载
dataset = Dataset[str, str, Any].from_file(
    'tests.yaml',
    custom_evaluator_types=[CustomEvaluator],  # 必需！
)
```

### 格式推断失败 {#format-inference-failed}

**问题**：`ValueError: Cannot infer format from extension`

**解决方案**：显式指定格式：

```python
from typing import Any

from pydantic_evals import Case, Dataset

dataset = Dataset[str, str, Any](name='my_tests', cases=[Case(inputs='test')])

# 为非常规扩展名显式指定格式
dataset.to_file('data.txt', fmt='yaml')
dataset_loaded = Dataset[str, str, Any].from_file('data.txt', fmt='yaml')
```

### Schema 生成错误 {#schema-generation-error}

**问题**：自定义 evaluator 导致 schema 生成失败

**解决方案**：确保 evaluator 是正确的 dataclass：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


# 正确
@dataclass
class MyEvaluator(Evaluator):
    value: int

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


# 错误：缺少 @dataclass
class BadEvaluator(Evaluator):
    def __init__(self, value: int):
        self.value = value

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True
```

## 后续步骤 {#next-steps}

- **[Dataset Management](dataset-management.md)** - 创建和组织 datasets
- **[Custom Evaluators](../evaluators/custom.md)** - 编写自定义 evaluation 逻辑
- **[Core Concepts](../core-concepts.md)** - 理解数据模型
