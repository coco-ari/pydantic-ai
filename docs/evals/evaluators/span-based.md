# 基于 Span 的评估 {#span-based-evaluation}

通过分析执行期间捕获的 OpenTelemetry spans 来评估 AI 系统行为。

!!! note "需要 Logfire"
    基于 span 的评估需要安装并配置 `logfire`：
    ```bash
    pip install 'pydantic-evals[logfire]'
    ```

## 概览 {#overview}

基于 span 的评估让你不仅能评估 AI 系统产生了**什么**，还能评估它是**如何**执行的。对于复杂 agents，这非常关键，因为确保期望行为往往取决于所采取的执行路径，而不只是最终输出。

### 为什么需要基于 Span 的评估？ {#why-span-based-evaluation}

传统评估器评估任务输入和输出。对于简单任务，这可能足够：如果输出正确，任务就成功了。但对于复杂的多步骤 agents，_过程_ 和结果同样重要：

- **以错误方式得到正确答案**：agent 可能偶然产生正确输出（例如猜测、在本应搜索时使用缓存数据、调用了错误工具但碰巧成功）
- **验证必需行为**：你需要确保调用了特定工具、执行了特定代码路径，或遵循了特定模式
- **性能和效率**：agent 应该高效得到答案，不应出现不必要的工具调用、无限循环或过多重试
- **安全和合规**：必须验证未尝试危险操作、未不当访问敏感数据，或未绕过 guardrails

### 真实场景 {#real-world-scenarios}

基于 span 的评估尤其适用于：

- **RAG 系统**：验证生成前确实检索并 rerank 了文档，而不只是答案包含引用
- **多 agent 协调**：确保 orchestrator 按正确顺序委派给正确的 specialist agents
- **工具调用 agents**：确认使用（或避免）了特定工具，并且顺序符合预期
- **调试和回归测试**：捕获输出仍然正确但内部逻辑退化的行为回归
- **生产对齐**：确保你的评估断言基于生产中捕获的同一份 telemetry 数据运行，这样 eval 洞察能直接转化为生产监控

### 工作方式 {#how-it-works}

当你配置 logfire（`logfire.configure()`）后，Pydantic Evals 会捕获任务执行期间生成的所有 OpenTelemetry spans。随后你可以编写评估器，对以下内容断言条件：

- **调用了哪些工具**：`HasMatchingSpan(query={'name_contains': 'search_tool'})`
- **执行了哪些代码路径**：验证特定函数已运行或走到了特定分支
- **时序特征**：检查操作是否在 SLA 边界内完成
- **错误条件**：检测重试、fallback 或特定失败模式
- **执行结构**：验证父子关系、委派模式或执行顺序

这创造了一种根本不同的评估范式：你测试的是行为契约，而不仅是输入输出关系。

## 基础用法 {#basic-usage}

```python
import logfire

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import HasMatchingSpan

# Configure logfire to capture spans
logfire.configure(send_to_logfire='if-token-present')

dataset = Dataset(
    name='span_basic',
    cases=[Case(inputs='test')],
    evaluators=[
        # Check that database was queried
        HasMatchingSpan(
            query={'name_contains': 'database_query'},
            evaluation_name='used_database',
        ),
    ],
)
```

## HasMatchingSpan 评估器 {#hasmatchingspan-evaluator}

[`HasMatchingSpan`][pydantic_evals.evaluators.HasMatchingSpan] 评估器会检查是否有任意 span 匹配查询：

```python
from pydantic_evals.evaluators import HasMatchingSpan

HasMatchingSpan(
    query={'name_contains': 'test'},
    evaluation_name='span_check',
)
```

**返回：** `bool` - 如果任意 span 匹配查询，则为 `True`

## SpanQuery 参考 {#spanquery-reference}

[`SpanQuery`][pydantic_evals.otel.SpanQuery] 是一个包含查询条件的字典：

### 名称条件 {#name-conditions}

按名称匹配 spans：

```python
# Exact name match
{'name_equals': 'search_database'}

# Contains substring
{'name_contains': 'tool_call'}

# Regex pattern
{'name_matches_regex': r'llm_call_\d+'}
```

### 属性条件 {#attribute-conditions}

匹配带有特定 attributes 的 spans：

```python
# Has specific attribute values
{'has_attributes': {'operation': 'search', 'status': 'success'}}

# Has attribute keys (any value)
{'has_attribute_keys': ['user_id', 'request_id']}
```

### 耗时条件 {#duration-conditions}

按执行时间匹配：

```python
from datetime import timedelta

# Minimum duration
{'min_duration': 1.0}  # seconds
{'min_duration': timedelta(seconds=1)}

# Maximum duration
{'max_duration': 5.0}  # seconds
{'max_duration': timedelta(seconds=5)}

# Range
{'min_duration': 0.5, 'max_duration': 2.0}
```

### 逻辑运算符 {#logical-operators}

组合条件：

```python
# NOT
{'not_': {'name_contains': 'error'}}

# AND (all must match)
{'and_': [
    {'name_contains': 'tool'},
    {'max_duration': 1.0},
]}

# OR (any must match)
{'or_': [
    {'name_equals': 'search'},
    {'name_equals': 'query'},
]}
```

### 子级/后代条件 {#childdescendant-conditions}

查询 spans 之间的关系：

```python
# Count direct children
{'min_child_count': 1}
{'max_child_count': 5}

# Some child matches query
{'some_child_has': {'name_contains': 'retry'}}

# All children match query
{'all_children_have': {'max_duration': 0.5}}

# No children match query
{'no_child_has': {'has_attributes': {'error': True}}}

# Descendant queries (recursive)
{'min_descendant_count': 5}
{'some_descendant_has': {'name_contains': 'api_call'}}
```

### 祖先/深度条件 {#ancestordepth-conditions}

查询 span 层级结构：

```python
# Depth (root spans have depth 0)
{'min_depth': 1}  # Not a root span
{'max_depth': 2}  # At most 2 levels deep

# Ancestor queries
{'some_ancestor_has': {'name_equals': 'agent_run'}}
{'all_ancestors_have': {'max_duration': 10.0}}
{'no_ancestor_has': {'has_attributes': {'error': True}}}
```

### 停止递归 {#stop-recursing}

控制递归查询：

```python
{
    'some_descendant_has': {'name_contains': 'expensive'},
    'stop_recursing_when': {'name_equals': 'boundary'},
}
# Only search descendants until hitting a span named 'boundary'
```

## 实用示例 {#practical-examples}

### 验证工具使用 {#verify-tool-usage}

检查是否调用了特定工具：

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import HasMatchingSpan

dataset = Dataset(
    name='tool_verification',
    cases=[Case(inputs='test')],
    evaluators=[
        # Must call search tool
        HasMatchingSpan(
            query={'name_contains': 'search_tool'},
            evaluation_name='used_search',
        ),

        # Must NOT call dangerous tool
        HasMatchingSpan(
            query={'not_': {'name_contains': 'delete_database'}},
            evaluation_name='safe_execution',
        ),
    ],
)
```

### 检查多个工具 {#check-multiple-tools}

验证一系列操作：

```python
from pydantic_evals.evaluators import HasMatchingSpan

evaluators = [
    HasMatchingSpan(
        query={'name_contains': 'retrieve_context'},
        evaluation_name='retrieved_context',
    ),
    HasMatchingSpan(
        query={'name_contains': 'generate_response'},
        evaluation_name='generated_response',
    ),
    HasMatchingSpan(
        query={'and_': [
            {'name_contains': 'cite'},
            {'has_attribute_keys': ['source_id']},
        ]},
        evaluation_name='added_citations',
    ),
]
```

### 性能断言 {#performance-assertions}

确保操作满足延迟要求：

```python
from pydantic_evals.evaluators import HasMatchingSpan

evaluators = [
    # Database queries should be fast
    HasMatchingSpan(
        query={'and_': [
            {'name_contains': 'database'},
            {'max_duration': 0.1},  # 100ms max
        ]},
        evaluation_name='fast_db_queries',
    ),

    # Overall should complete quickly
    HasMatchingSpan(
        query={'and_': [
            {'name_equals': 'task_execution'},
            {'max_duration': 2.0},
        ]},
        evaluation_name='within_sla',
    ),
]
```

### 错误检测 {#error-detection}

检查错误条件：

```python
from pydantic_evals.evaluators import HasMatchingSpan

evaluators = [
    # No errors occurred
    HasMatchingSpan(
        query={'not_': {'has_attributes': {'error': True}}},
        evaluation_name='no_errors',
    ),

    # Retries happened
    HasMatchingSpan(
        query={'name_contains': 'retry'},
        evaluation_name='had_retries',
    ),

    # Fallback was used
    HasMatchingSpan(
        query={'name_contains': 'fallback_model'},
        evaluation_name='used_fallback',
    ),
]
```

### 复杂行为检查 {#complex-behavioral-checks}

验证复杂行为模式：

```python
from pydantic_evals.evaluators import HasMatchingSpan

evaluators = [
    # Agent delegated to sub-agent
    HasMatchingSpan(
        query={'and_': [
            {'name_contains': 'agent'},
            {'some_child_has': {'name_contains': 'delegate'}},
        ]},
        evaluation_name='used_delegation',
    ),

    # Made multiple LLM calls with retries
    HasMatchingSpan(
        query={'and_': [
            {'name_contains': 'llm_call'},
            {'some_descendant_has': {'name_contains': 'retry'}}
            {'min_descendant_count': 3},
        ]},
        evaluation_name='retry_pattern',
    ),
]
```

## 使用 SpanTree 的自定义评估器 {#custom-evaluators-with-spantree}

如需更复杂的 span 分析，可以编写自定义评估器：

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class CustomSpanCheck(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool | int]:
        span_tree = ctx.span_tree

        # Find specific spans
        llm_spans = span_tree.find(lambda node: 'llm' in node.name)
        tool_spans = span_tree.find(lambda node: 'tool' in node.name)

        # Calculate metrics
        total_llm_time = sum(
            span.duration.total_seconds() for span in llm_spans
        )

        return {
            'used_llm': len(llm_spans) > 0,
            'used_tools': len(tool_spans) > 0,
            'tool_count': len(tool_spans),
            'llm_fast': total_llm_time < 2.0,
        }
```

### SpanTree API 接口 {#spantree-api}

[`SpanTree`][pydantic_evals.otel.SpanTree] 提供 span 分析方法：

```python
from pydantic_evals.otel import SpanTree


# Example API (requires span_tree from context)
def example_api(span_tree: SpanTree) -> None:
    span_tree.find(lambda n: True)  # Find all matching nodes
    span_tree.any({'name_contains': 'test'})  # Check if any span matches
    span_tree.all({'name_contains': 'test'})  # Check if all spans match
    span_tree.count({'name_contains': 'test'})  # Count matching spans

    # Iteration
    for node in span_tree:
        print(node.name, node.duration, node.attributes)
```

### SpanNode 属性 {#spannode-properties}

每个 [`SpanNode`][pydantic_evals.otel.SpanNode] 都有：

```python
from pydantic_evals.otel import SpanNode


# Example properties (requires node from context)
def example_properties(node: SpanNode) -> None:
    _ = node.name  # Span name
    _ = node.duration  # timedelta
    _ = node.attributes  # dict[str, AttributeValue]
    _ = node.start_timestamp  # datetime
    _ = node.end_timestamp  # datetime
    _ = node.children  # list[SpanNode]
    _ = node.descendants  # list[SpanNode] (recursive)
    _ = node.ancestors  # list[SpanNode]
    _ = node.parent  # SpanNode | None
```

## 调试 Span 查询 {#debugging-span-queries}

### 在 Logfire 中查看 Spans {#view-spans-in-logfire}

如果你正向 Logfire 发送数据，可以在 Web UI 中查看所有 spans，以理解 trace 结构。

### 打印 Span Tree {#print-span-tree}

```python
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext


@dataclass
class DebugSpans(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        for node in ctx.span_tree:
            print(f"{'  ' * len(node.ancestors)}{node.name} ({node.duration})")
        return True
```

### 查询测试 {#query-testing}

逐步测试查询：

```python
from pydantic_evals.evaluators import HasMatchingSpan

# Start simple
query = {'name_contains': 'tool'}

# Add conditions gradually
query = {'and_': [
    {'name_contains': 'tool'},
    {'max_duration': 1.0},
]}

# Test in evaluator
HasMatchingSpan(query=query, evaluation_name='test')
```

## 使用场景 {#use-cases}

### RAG 系统验证 {#rag-system-verification}

验证检索增强生成工作流：

```python
from pydantic_evals.evaluators import HasMatchingSpan

evaluators = [
    # Retrieved documents
    HasMatchingSpan(
        query={'name_contains': 'vector_search'},
        evaluation_name='retrieved_docs',
    ),

    # Reranked results
    HasMatchingSpan(
        query={'name_contains': 'rerank'},
        evaluation_name='reranked_results',
    ),

    # Generated with context
    HasMatchingSpan(
        query={'and_': [
            {'name_contains': 'generate'},
            {'has_attribute_keys': ['context_ids']},
        ]},
        evaluation_name='used_context',
    ),
]
```

### 多 Agent 系统 {#multi-agent-systems}

验证 agent 协调：

```python
from pydantic_evals.evaluators import HasMatchingSpan

evaluators = [
    # Master agent ran
    HasMatchingSpan(
        query={'name_equals': 'master_agent'},
        evaluation_name='master_ran',
    ),

    # Delegated to specialist
    HasMatchingSpan(
        query={'and_': [
            {'name_contains': 'specialist_agent'},
            {'some_ancestor_has': {'name_equals': 'master_agent'}},
        ]},
        evaluation_name='delegated_correctly',
    ),

    # No circular delegation
    HasMatchingSpan(
        query={'not_': {'and_': [
            {'name_contains': 'agent'},
            {'some_descendant_has': {'name_contains': 'agent'}}
            {'some_ancestor_has': {'name_contains': 'agent'}},
        ]}},
        evaluation_name='no_circular_delegation',
    ),
]
```

### 工具使用模式 {#tool-usage-patterns}

验证智能工具选择：

```python
from pydantic_evals.evaluators import HasMatchingSpan

evaluators = [
    # Used search before answering
    HasMatchingSpan(
        query={'and_': [
            {'name_contains': 'search'},
            {'some_ancestor_has': {'name_contains': 'answer'}},
        ]},
        evaluation_name='searched_before_answering',
    ),

    # Limited tool calls (no loops)
    HasMatchingSpan(
        query={'and_': [
            {'name_contains': 'tool'},
            {'max_child_count': 5},
        ]},
        evaluation_name='reasonable_tool_usage',
    ),
]
```

## 最佳实践 {#best-practices}

1. **从简单开始**：先使用基础名称查询，再按需增加复杂度
2. **使用描述性名称**：在应用代码中为 spans 取好名称
3. **测试查询**：在运行完整评估前验证查询有效
4. **与其他评估器组合使用**：把 span 检查与输出验证结合
5. **记录预期**：用注释说明为什么特定 spans 应该存在或不应该存在

## 下一步 {#next-steps}

- **[Logfire 集成](../how-to/logfire-integration.md)** - 设置 Logfire 来捕获 spans
- **[自定义评估器](custom.md)** - 编写高级 span 分析
- **[原生评估器](built-in.md)** - 其他评估器类型
