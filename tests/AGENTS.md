# 测试指南

## 测试文件结构

```python
from __future__ import annotations

import pytest
from inline_snapshot import snapshot

from pydantic_ai import Agent
from pydantic_ai.models import Model
# ... other imports

pytestmark = [pytest.mark.anyio, pytest.mark.vcr]


# fixtures/helpers immediately before their test
@pytest.fixture
def my_helper():
    ...


@pytest.mark.parametrize('model', ['openai', 'anthropic', 'google'], indirect=True)
@pytest.mark.parametrize('stream', [False, True])
async def test_feature(model: Model, stream: bool):
    ...
```

## 带预期值的参数化

对于笛卡尔积测试，使用 dict 将参数组合映射到预期结果：

```python
from vcr.cassette import Cassette

from pydantic_ai.models import Model

# expectation can be a dataclass, for more complex cases
EXPECTATIONS: dict[tuple[str, bool], str] = {
    ('openai', False): 'expected output for openai non-streaming',
    ('openai', True): 'expected output for openai streaming',
    ('anthropic', False): 'expected output for anthropic non-streaming',
    ('anthropic', True): 'expected output for anthropic streaming',
}


@pytest.mark.parametrize('model', ['openai', 'anthropic'], indirect=True)
@pytest.mark.parametrize('stream', [False, True])
async def test_feature(model: Model, stream: bool, request: pytest.FixtureRequest, vcr: Cassette):
    """What the test is asserting.

    Use the `request` fixture to access test parameter values.

    Use the `vcr` to make assertions about the HTTP requests if needed.
    Another creative way of, for instance, asserting headers, is to use a patched httpx client fixture.
    This spares us the overhead of parsing cassette fields, so it is to be preferred whenever optimal.
    """
    model_name = request.node.callspec.params['model']
    expected = EXPECTATIONS[(model_name, stream)]

    agent = Agent(model)
    if stream:
        async with agent.run_stream('hello') as result:
            output = await result.get_output()
    else:
        result = await agent.run('hello')
        output = result.output

    assert output == expected
```

## VCR 工作流

使用 `--record-mode=rewrite` 录制 cassettes，不带该标志验证回放，并审查 diff。详细工作流见 `.claude/skills/testing-skill/SKILL.md`。

## 关键 Fixtures

### 来自 `conftest.py`

#### 模型请求

- `allow_model_requests`：绕过默认的 `ALLOW_MODEL_REQUESTS = False`

#### `model` fixture（配合 `indirect=True` 使用）

`model` fixture 接受一个字符串参数（例如 `'openai'`、`'anthropic'`、`'google'`），并返回一个已配置的 `Model` 实例。它使用 session-scoped API key fixtures，这些 fixtures 默认值为 `'mock-api-key'`（录制时从环境加载真实 key）。支持的参数值完整列表见 `tests/conftest.py`。

```python
@pytest.mark.parametrize('model', ['openai', 'anthropic'], indirect=True)
async def test_something(model: Model):
    ...
```

#### 环境管理

- `env`：用于临时 env var 变更的 `TestEnv` 实例
  ```python
  def test_missing_key(env: TestEnv):
      env.remove('OPENAI_API_KEY')
      with pytest.raises(UserError):
          ...
  ```

#### 二进制内容（session-scoped）

- `assets_path`：指向 `tests/assets/` 的 `Path`
- `image_content`：`BinaryImage`（kiwi.jpg）
- `audio_content`：`BinaryContent`（marcelo.mp3）
- `video_content`：`BinaryContent`（small_video.mp4）
- `document_content`：`BinaryContent`（dummy.pdf）
- `text_document_content`：`BinaryContent`（dummy.txt）

#### URL 下载的 SSRF 保护

- `disable_ssrf_protection_for_vcr`：下载 URL 内容的 VCR 测试必需（带 `force_download=True` 的 `ImageUrl`、`AudioUrl`、`DocumentUrl`、`VideoUrl`）
- 如果 VCR 测试在没有这个 fixture 的情况下触发 SSRF validation，autouse guard 会抛出 `RuntimeError`

## 断言 Helpers

### 来自 `conftest.py`

- `IsNow(tz=timezone.utc)`：距离当前时间 10 秒内的 datetime
- `IsStr()`：任意字符串，支持 `regex=r'...'`
- `IsDatetime()`：任意 datetime
- `IsBytes()`：任意 bytes
- `IsInt()`：任意 int
- `IsFloat()`：任意 float
- `IsList()`：任意 list
- `IsInstance(SomeClass)`：某个 class 的实例

### 额外 helpers

- `IsSameStr()`：在同一个断言的多次使用中断言相同字符串值
  ```python
  assert events == [
      {'id': (msg_id := IsSameStr())},
      {'id': msg_id},  # must match first
  ]
  ```

## 最佳实践

- 通过公共 API 测试，而不是 private methods（以 `_` 开头）或 helpers。这样可以验证真实的面向用户行为，并防止测试脆弱地绑定到实现细节。
- 相比追加到巨大的 `test_<provider>.py` 文件，更偏好以功能为中心的参数化测试文件（例如 `test_multimodal_tool_returns.py`）。旧的 per-provider 文件很大，智能体很难导航；新功能应拥有自己的测试文件，使用 `Case` 类和参数化 providers。
- 对复杂结构化输出（对象、message sequences、API responses、嵌套 dicts）使用 `snapshot()`。相比逐字段断言，它能更可靠地捕获意外变化；对变量值使用 `IsStr` 和类似 matchers。
- 断言正在引入变更的核心方面。使用任何必要手段：patch clients 检查 request payloads、接入 pydantic-ai internals、snapshot comparisons。Snapshots 对捕获对象和 message arrays 的结构漂移很有价值，但只有当结构展示了你关心且需要保持一致的行为时，才使用 `result.all_messages()` 或输出断言。
- 对 optional capabilities（model features、server features、streaming）同时测试正向和负向情况。这样可以确保功能在支持时有效，并在缺失时优雅失败。
- 确保测试断言匹配测试名称和 docstrings。没有合适断言或验证相反行为的测试会制造假阳性。
- 针对 MCP 使用真实的 `tests.mcp_server` 实例测试，而不是 mocks。扩展测试服务器，添加 helper tools 以暴露 runtime context（instructions、client info、session state）。
- 当行为变化时，移除陈旧的测试 docstrings、comments 和历史 provider bug notes。
- 当测试不特别需要 system-prompt 代码路径时，优先使用 `instructions=` 而不是 `system_prompt=`。`instructions=` 是非 system-prompt-specific 行为的规范入口（cacheable prefix、persona priming、format guidance）；将 `system_prompt=` 保留给测试 system-prompt 机制的场景，可以让意图更清晰。
- 永远不要在测试 docstrings 或 comments 中引用行号（`lines 872-873`、`L42`、`line 100`）。它们会在下一次编辑被引用文件时过时。请描述条件或行为。

## 目录结构

```
tests/
├── conftest.py              # shared fixtures
├── json_body_serializer.py  # custom VCR serializer
├── assets/                  # binary test files
├── cassettes/               # VCR recordings for root tests
├── models/
│   ├── conftest.py          # model-specific fixtures (if needed)
│   ├── cassettes/           # VCR recordings per test file
│   │   ├── test_openai/
│   │   ├── test_anthropic/
│   │   └── ...
│   └── test_*.py
├── providers/
│   └── test_*.py            # provider initialization tests (unit)
└── test_*.py                # feature tests (prefer VCR + parametrize)
```
