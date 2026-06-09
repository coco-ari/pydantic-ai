# 自定义 Evaluators

为特定领域逻辑、外部集成或专用 metrics 编写自定义 evaluators。

## 基础自定义 Evaluator {#basic-custom-evaluator}

所有 evaluators 都继承自 [`Evaluator`][pydantic_evals.evaluators.Evaluator]，并且必须实现 `evaluate`：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ExactMatch(Evaluator):
    """Check if output exactly matches expected output."""

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output == ctx.expected_output
```

**关键点：**

- 使用 `@dataclass` 装饰器（必需）
- 继承自 `Evaluator`
- 实现 `evaluate(self, ctx: EvaluatorContext) -> EvaluatorOutput`
- 返回 `bool`、`int`、`float`、`str`、[`EvaluationReason`][pydantic_evals.evaluators.EvaluationReason]，或由这些类型组成的 `dict`

## EvaluatorContext 上下文 {#evaluatorcontext}

上下文提供 case 执行的所有信息：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class MyEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        # Access case data
        ctx.name              # Case name
        ctx.inputs            # Task inputs
        ctx.metadata          # Case metadata
        ctx.expected_output   # Expected output (may be None)
        ctx.output            # Actual output

        # Performance data
        ctx.duration          # Task execution time (seconds)

        # Custom metrics/attributes (see metrics guide)
        ctx.metrics           # dict[str, int | float]
        ctx.attributes        # dict[str, Any]

        # OpenTelemetry spans (if logfire configured)
        ctx.span_tree         # SpanTree for behavioral checks

        return True
```

## Evaluator 参数 {#evaluator-parameters}

把可配置参数作为 dataclass 字段添加：

```python
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ContainsKeyword(Evaluator):
    keyword: str
    case_sensitive: bool = True

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        output = ctx.output
        keyword = self.keyword

        if not self.case_sensitive:
            output = output.lower()
            keyword = keyword.lower()

        return keyword in output


# Usage
dataset = Dataset(
    name='keyword_check',
    cases=[Case(name='test', inputs='This is important')],
    evaluators=[
        ContainsKeyword(keyword='important', case_sensitive=False),
    ],
)
```

## 返回类型 {#return-types}

### 布尔断言 {#boolean-assertions}

简单的 pass/fail 检查：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class IsValidJSON(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        try:
            import json
            json.loads(ctx.output)
            return True
        except Exception:
            return False
```

### 数值评分 {#numeric-scores}

质量 metrics：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class LengthScore(Evaluator):
    """Score based on output length (0.0 = too short, 1.0 = ideal)."""

    ideal_length: int = 100
    tolerance: int = 20

    def evaluate(self, ctx: EvaluatorContext) -> float:
        length = len(ctx.output)
        diff = abs(length - self.ideal_length)

        if diff <= self.tolerance:
            return 1.0
        else:
            # Decay score as we move away from ideal
            score = max(0.0, 1.0 - (diff - self.tolerance) / self.ideal_length)
            return score
```

### 字符串标签 {#string-labels}

分类：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class SentimentClassifier(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> str:
        output_lower = ctx.output.lower()

        if any(word in output_lower for word in ['error', 'failed', 'wrong']):
            return 'negative'
        elif any(word in output_lower for word in ['success', 'correct', 'great']):
            return 'positive'
        else:
            return 'neutral'
```

### 带原因的结果 {#with-reasons}

为任意结果添加解释：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext


@dataclass
class SmartCheck(Evaluator):
    threshold: float = 0.8

    def evaluate(self, ctx: EvaluatorContext) -> EvaluationReason:
        score = self._calculate_score(ctx.output)

        if score >= self.threshold:
            return EvaluationReason(
                value=True,
                reason=f'Score {score:.2f} exceeds threshold {self.threshold}',
            )
        else:
            return EvaluationReason(
                value=False,
                reason=f'Score {score:.2f} below threshold {self.threshold}',
            )

    def _calculate_score(self, output: str) -> float:
        # Your scoring logic
        return 0.75
```

### 多个结果 {#multiple-results}

通过返回键值对字典，你可以从一个 evaluator 返回多个 evaluations。

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import (
    EvaluationReason,
    Evaluator,
    EvaluatorContext,
    EvaluatorOutput,
)


@dataclass
class ComprehensiveCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> EvaluatorOutput:
        format_valid = self._check_format(ctx.output)

        return {
            'valid_format': EvaluationReason(
                value=format_valid,
                reason='Valid JSON format' if format_valid else 'Invalid JSON format',
            ),
            'quality_score': self._score_quality(ctx.output),  # float
            'category': self._classify(ctx.output),  # str
        }

    def _check_format(self, output: str) -> bool:
        return output.startswith('{') and output.endswith('}')

    def _score_quality(self, output: str) -> float:
        return len(output) / 100.0

    def _classify(self, output: str) -> str:
        return 'short' if len(output) < 50 else 'long'
```

返回字典中的每个 key 都会成为报告中的一条独立结果。值可以是：

- 基本类型（`bool`、`int`、`float`、`str`）
- [`EvaluationReason`][pydantic_evals.evaluators.EvaluationReason]（带解释的 value）
- 这些类型组成的嵌套 dict

[`EvaluatorOutput`][pydantic_evals.evaluators.evaluator.EvaluatorOutput] 类型表示 evaluator 可以返回的所有合法值，
并可作为自定义 `evaluate` 方法的返回类型注解。

### 条件结果 {#conditional-results}

Evaluators 可以针对给定 case 动态决定是否产出结果；不适用时返回空 dict：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import (
    EvaluationReason,
    Evaluator,
    EvaluatorContext,
    EvaluatorOutput,
)


@dataclass
class SQLValidator(Evaluator):
    """Only evaluates SQL queries, skips other outputs."""

    def evaluate(self, ctx: EvaluatorContext) -> EvaluatorOutput:
        # Check if this case is relevant for SQL validation
        if not isinstance(ctx.output, str) or not ctx.output.strip().upper().startswith(
            ('SELECT', 'INSERT', 'UPDATE', 'DELETE')
        ):
            # Return empty dict - this evaluator doesn't apply to this case
            return {}

        # This is a SQL query, perform validation
        try:
            # In real implementation, use sqlparse or similar
            is_valid = self._validate_sql(ctx.output)
            return {
                'sql_valid': is_valid,
                'sql_complexity': self._measure_complexity(ctx.output),
            }
        except Exception as e:
            return {'sql_valid': EvaluationReason(False, reason=f'Exception: {e}')}

    def _validate_sql(self, query: str) -> bool:
        # Simplified validation
        return 'FROM' in query.upper() or 'INTO' in query.upper()

    def _measure_complexity(self, query: str) -> str:
        joins = query.upper().count('JOIN')
        if joins == 0:
            return 'simple'
        elif joins <= 2:
            return 'moderate'
        else:
            return 'complex'
```

这个模式适用于：

- 某个 evaluator 只适用于特定类型的输出（例如代码验证只适用于代码输出）
- 验证依赖 metadata tags（例如只评估标记为 `language='python'` 的 cases）
- 你希望根据其他 evaluator 结果，有条件地运行昂贵检查

**关键点：**

- 返回 `{}` 表示"这个 evaluator 不适用于这里"，该 case 不会显示来自这个 evaluator 的结果
- 返回 `{'key': value}` 表示"这个 evaluator 适用，这些是结果"
- 当它适用于大量 cases，或条件基于输出本身时，这比使用 case-level evaluators 更实用
- evaluator 仍会为每个 case 运行，但在不相关时可以短路

## 异步 Evaluators {#async-evaluators}

对 I/O-bound 操作使用 `async def`：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class APIValidator(Evaluator):
    api_url: str

    async def evaluate(self, ctx: EvaluatorContext) -> bool:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                json={'output': ctx.output},
            )
            return response.json()['valid']
```

Pydantic Evals 会自动处理同步和异步 evaluators。

## 使用 Metadata {#using-metadata}

访问 case metadata，以执行 context-aware evaluation：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class DifficultyAwareScore(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> float:
        # Base score
        base_score = self._score_output(ctx.output)

        # Adjust based on difficulty from metadata
        if ctx.metadata and 'difficulty' in ctx.metadata:
            difficulty = ctx.metadata['difficulty']

            if difficulty == 'easy':
                # Penalize mistakes more on easy questions
                return base_score
            elif difficulty == 'hard':
                # Be more lenient on hard questions
                return min(1.0, base_score * 1.2)

        return base_score

    def _score_output(self, output: str) -> float:
        # Your scoring logic
        return 0.8
```

## 使用 Metrics {#using-metrics}

访问任务执行期间设置的自定义 metrics：

```python
from dataclasses import dataclass

from pydantic_evals import increment_eval_metric, set_eval_attribute
from pydantic_evals.evaluators import Evaluator, EvaluatorContext


# In your task
def my_task(inputs: str) -> str:
    result = f'processed: {inputs}'

    # Record metrics
    increment_eval_metric('api_calls', 3)
    set_eval_attribute('used_cache', True)

    return result


# In your evaluator
@dataclass
class EfficiencyCheck(Evaluator):
    max_api_calls: int = 5

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        api_calls = ctx.metrics.get('api_calls', 0)
        return api_calls <= self.max_api_calls
```

更多信息请参阅 [Metrics & Attributes 指南](../how-to/metrics-attributes.md)。

## 泛型类型参数 {#generic-type-parameters}

使用泛型让 evaluators 类型安全：

```python
from dataclasses import dataclass
from typing import TypeVar

from pydantic_evals.evaluators import Evaluator, EvaluatorContext

InputsT = TypeVar('InputsT')
OutputT = TypeVar('OutputT')


@dataclass
class TypedEvaluator(Evaluator[InputsT, OutputT, dict]):
    def evaluate(self, ctx: EvaluatorContext[InputsT, OutputT, dict]) -> bool:
        # ctx.inputs and ctx.output are now properly typed
        return True
```

## 自定义 Evaluation 名称 {#custom-evaluation-names}

控制 evaluations 在报告中的显示方式：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class CustomNameEvaluator(Evaluator):
    check_type: str

    def get_default_evaluation_name(self) -> str:
        # Use check_type as the name instead of class name
        return f'{self.check_type}_check'

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


# In reports, appears as "format_check" instead of "CustomNameEvaluator"
evaluator = CustomNameEvaluator(check_type='format')
```

或者使用 `evaluation_name` 字段（如果使用内置模式）：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class MyEvaluator(Evaluator):
    evaluation_name: str | None = None

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return True


# Usage
MyEvaluator(evaluation_name='my_custom_name')
```

## 真实世界示例 {#real-world-examples}

### SQL 验证 {#sql-validation}

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext


@dataclass
class ValidSQL(Evaluator):
    dialect: str = 'postgresql'

    def evaluate(self, ctx: EvaluatorContext) -> EvaluationReason:
        try:
            import sqlparse
            parsed = sqlparse.parse(ctx.output)

            if not parsed:
                return EvaluationReason(
                    value=False,
                    reason='Could not parse SQL',
                )

            # Check for dangerous operations
            sql_upper = ctx.output.upper()
            if 'DROP' in sql_upper or 'DELETE' in sql_upper:
                return EvaluationReason(
                    value=False,
                    reason='Contains dangerous operations (DROP/DELETE)',
                )

            return EvaluationReason(
                value=True,
                reason='Valid SQL syntax',
            )
        except Exception as e:
            return EvaluationReason(
                value=False,
                reason=f'SQL parsing error: {e}',
            )
```

### 代码执行 {#code-execution}

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext


@dataclass
class ExecutablePython(Evaluator):
    timeout_seconds: float = 5.0

    async def evaluate(self, ctx: EvaluatorContext) -> EvaluationReason:
        import asyncio
        import os
        import tempfile

        # Write code to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(ctx.output)
            temp_path = f.name

        try:
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                'python', temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds,
                )
            except asyncio.TimeoutError:
                process.kill()
                return EvaluationReason(
                    value=False,
                    reason=f'Execution timeout after {self.timeout_seconds}s',
                )

            if process.returncode == 0:
                return EvaluationReason(
                    value=True,
                    reason='Code executed successfully',
                )
            else:
                return EvaluationReason(
                    value=False,
                    reason=f'Execution failed: {stderr.decode()}',
                )
        finally:
            os.unlink(temp_path)
```

### 外部 API 验证 {#external-api-validation}

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class APIResponseValid(Evaluator):
    api_endpoint: str
    api_key: str

    async def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | float]:
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_endpoint,
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    json={'data': ctx.output},
                    timeout=10.0,
                )

                result = response.json()

                return {
                    'api_reachable': True,
                    'validation_passed': result.get('valid', False),
                    'confidence_score': result.get('confidence', 0.0),
                }
        except Exception:
            return {
                'api_reachable': False,
                'validation_passed': False,
                'confidence_score': 0.0,
            }
```

## 测试 Evaluators {#testing-evaluators}

像测试其他 Python 代码一样测试 evaluators：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class ExactMatch(Evaluator):
    """Check if output exactly matches expected output."""

    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output == ctx.expected_output


def test_exact_match():
    evaluator = ExactMatch()

    # Test match
    ctx = EvaluatorContext(
        name='test',
        inputs='input',
        metadata=None,
        expected_output='expected',
        output='expected',
        duration=0.1,
        _span_tree=None,
        attributes={},
        metrics={},
    )
    assert evaluator.evaluate(ctx) is True

    # Test mismatch
    ctx.output = 'different'
    assert evaluator.evaluate(ctx) is False
```

## 最佳实践 {#best-practices}

### 1. 保持 Evaluators 聚焦 {#1-keep-evaluators-focused}

每个 evaluator 应该只检查一件事：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


def check_format(output: str) -> bool:
    return output.startswith('{')


def check_content(output: str) -> bool:
    return len(output) > 10


def check_length(output: str) -> bool:
    return len(output) < 1000


def check_spelling(output: str) -> bool:
    return True  # Placeholder


# Bad: Doing too much
@dataclass
class EverythingChecker(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> dict:
        return {
            'format_valid': check_format(ctx.output),
            'content_good': check_content(ctx.output),
            'length_ok': check_length(ctx.output),
            'spelling_correct': check_spelling(ctx.output),
        }


# Good: Separate evaluators
@dataclass
class FormatValidator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return check_format(ctx.output)


@dataclass
class ContentChecker(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return check_content(ctx.output)


@dataclass
class LengthChecker(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return check_length(ctx.output)


@dataclass
class SpellingChecker(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return check_spelling(ctx.output)
```

这有一些例外：

* 当存在大量共享计算或网络请求延迟时，让单个 evaluator 一次性计算所有依赖输出可能更好。
* 如果多个检查彼此紧密耦合或非常接近，把它们的逻辑都放到一个 evaluator 中可能是合理的。

### 2. 优雅处理缺失数据 {#2-handle-missing-data-gracefully}

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext


@dataclass
class SafeEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> EvaluationReason:
        if ctx.expected_output is None:
            return EvaluationReason(
                value=True,
                reason='Skipped: no expected output provided',
            )

        # Your evaluation logic
        ...
```

### 3. 提供有帮助的原因 {#3-provide-helpful-reasons}

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext


@dataclass
class HelpfulEvaluator(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> EvaluationReason:
        # Bad
        return EvaluationReason(value=False, reason='Failed')

        # Good
        return EvaluationReason(
            value=False,
            reason=f'Expected {ctx.expected_output!r}, got {ctx.output!r}',
        )
```

### 4. 对外部调用使用超时 {#4-use-timeouts-for-external-calls}

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class APIEvaluator(Evaluator):
    timeout: float = 10.0

    async def _call_api(self, output: str) -> bool:
        # Placeholder for API call
        return True

    async def evaluate(self, ctx: EvaluatorContext) -> bool:
        import asyncio

        try:
            return await asyncio.wait_for(
                self._call_api(ctx.output),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            return False
```

## 下一步 {#next-steps}

- **[Report Evaluators](report-evaluators.md)** - 实验级分析（confusion matrices、PR curves、自定义表格）
- **[基于 Span 的评估](span-based.md)** - 使用 OpenTelemetry spans
- **[示例](../examples/simple-validation.md)** - 实用示例
