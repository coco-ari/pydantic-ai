# Python 能力表

状态说明：

- `not_started`：还没系统学过。
- `learning`：已经接触，但需要例子和练习巩固。
- `known`：可以在读源码时直接使用。

## 基础语法

| 知识点 | 状态 | 证据/备注 | 最近更新 |
| --- | --- | --- | --- |
| 变量与赋值 | learning | 用户说明 Python 基础较弱，暂按需要补课 | 2026-06-09 |
| 基础类型：`str`、`int`、`bool`、`None` | learning | 读 `Agent(..., instructions='...')` 会用到 | 2026-06-09 |
| 容器：`list`、`dict`、`tuple`、`set` | not_started | 读 messages、settings、tool schema 会用到 | 2026-06-09 |
| 条件判断：`if` / `elif` / `else` | not_started | 读运行分支会用到 | 2026-06-09 |
| 循环：`for` / `while` | learning | 用户能解释 `while not isinstance(node, End)` 会循环执行节点直到结束 | 2026-06-09 |
| 函数定义与参数 | learning | 读 tool、instructions 装饰器会用到 | 2026-06-09 |
| 关键字参数与默认参数 | learning | `Agent(..., output_type=...)`、`run_sync(..., deps=...)` 会用到 | 2026-06-09 |
| `*args` / `**kwargs` | not_started | 读包装器、公共 API 兼容层会用到 | 2026-06-09 |

## 面向对象

| 知识点 | 状态 | 证据/备注 | 最近更新 |
| --- | --- | --- | --- |
| 类与实例 | known | 用户能说明 `OpenAIProvider` 和 `OpenAIChatModel` 是类，用来创建 provider 和 model 对象 | 2026-06-09 |
| 方法与属性 | learning | 用户能解释 `self._model` 是 agent 内部保存模型的属性，继续通过 `run_sync()` 巩固 | 2026-06-09 |
| 对象组合 | learning | 已接触 `Agent` 持有 model、model 持有 provider 的关系；理解不需要一次到位 | 2026-06-09 |
| 执行图与节点 | learning | 用户能把 graph 和任务节点联系起来；已校正 graph 是节点与流转规则，node 是单个任务节点 | 2026-06-09 |
| 继承 | not_started | 读 `AbstractAgent`、model/provider 基类会用到 | 2026-06-09 |
| 抽象基类 / 协议 | not_started | 读 `abstract.py` 和 provider 接口会用到 | 2026-06-09 |
| `dataclass` | not_started | docs 示例和内部状态对象会用到 | 2026-06-09 |

## 类型系统

| 知识点 | 状态 | 证据/备注 | 最近更新 |
| --- | --- | --- | --- |
| 类型注解基础 | learning | `Agent[DepsT, OutputT]`、函数参数会用到 | 2026-06-09 |
| 泛型：`TypeVar`、`Generic` | not_started | 理解 `Agent[DepsT, OutputT]` 必需 | 2026-06-09 |
| 联合类型：`A | B` | not_started | 读 messages、output 类型分支会用到 | 2026-06-09 |
| `Literal` | not_started | 读配置选项和策略会用到 | 2026-06-09 |
| `Protocol` | not_started | 读模型接口和工具接口时可能用到 | 2026-06-09 |
| `TypedDict` | not_started | 读 provider payload 和 settings 会用到 | 2026-06-09 |

## 异步与上下文管理

| 知识点 | 状态 | 证据/备注 | 最近更新 |
| --- | --- | --- | --- |
| `async def` / `await` | learning | 已理解 `self.run(...)` 是异步 Agent 运行任务，`run_sync()` 用事件循环执行它；暂不要求理解事件循环底层 | 2026-06-09 |
| async iterator：`async for` | not_started | 读 streaming events 必需 | 2026-06-09 |
| context manager：`with` | not_started | 读 `agent.iter()`、stream API 会用到 | 2026-06-09 |
| async context manager：`async with` | learning | 已理解 `async with self.iter(...) as agent_run` 是创建并进入一次 AgentRun 上下文 | 2026-06-09 |

## Pydantic 与项目常用机制

| 知识点 | 状态 | 证据/备注 | 最近更新 |
| --- | --- | --- | --- |
| Pydantic `BaseModel` | not_started | 理解结构化输出和消息模型必需 | 2026-06-09 |
| 字段校验：`Field` | not_started | docs 的 `SupportOutput` 示例会用到 | 2026-06-09 |
| 装饰器 | not_started | `@agent.tool`、`@agent.instructions` 必需 | 2026-06-09 |
| 异常处理：`try` / `except` | not_started | 读 retry、模型错误处理会用到 | 2026-06-09 |
| 包和模块：`import` | learning | 从 `from pydantic_ai import Agent` 开始 | 2026-06-09 |
| 标准库 `os.getenv()` | learning | 最小 API 示例用它读取环境变量，避免把密钥写进源码 | 2026-06-09 |

## 工程工具

| 知识点 | 状态 | 证据/备注 | 最近更新 |
| --- | --- | --- | --- |
| 虚拟环境与依赖管理 | not_started | 本项目使用 `uv` workspace | 2026-06-09 |
| 环境变量与密钥管理 | learning | 使用 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`PYDANTIC_AI_MODEL` 配置示例 | 2026-06-09 |
| pytest 基础 | not_started | 后续读测试理解行为 | 2026-06-09 |
| pyright / 类型检查 | not_started | 本项目重视类型安全 | 2026-06-09 |
| Git 基础 | not_started | 只学习可先不要求 | 2026-06-09 |
