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
| 容器：`list`、`dict`、`tuple`、`set` | learning | 已用 `ModelRequest.parts` 理解 list；用户能把 dict 类比成 Java Map，并理解 `{"get_weather":"a: sunny"}` 是工具名到工具返回值的映射 | 2026-06-10 |
| 条件判断：`if` / `elif` / `else` | not_started | 读运行分支会用到 | 2026-06-09 |
| 循环：`for` / `while` | learning | 用户能解释 `while not isinstance(node, End)` 会循环执行节点直到结束 | 2026-06-09 |
| 函数定义与参数 | known | 用户能解释 `def get_weather(city)` 中 `def`、函数名、参数和 `return` 的含义，并能类比 Java 方法 | 2026-06-10 |
| 关键字参数与默认参数 | learning | 用户能判断 `unit="C"` 是把 `"C"` 传给名叫 `unit` 的参数；后续通过 `deps=...` 继续巩固 | 2026-06-11 |
| `*args` / `**kwargs` | not_started | 读包装器、公共 API 兼容层会用到 | 2026-06-09 |

## 面向对象

| 知识点 | 状态 | 证据/备注 | 最近更新 |
| --- | --- | --- | --- |
| 类与实例 | known | 用户能说明 `OpenAIProvider` 和 `OpenAIChatModel` 是类，用来创建 provider 和 model 对象 | 2026-06-09 |
| 方法与属性 | known | 用户能正确判断 `book.title` 读到 `"Python Basics"`，能判断连续属性 `ctx.deps.unit` 读到 `"C"`，也能追踪 `ctx.deps` 重新赋值后读到新对象里的 `unit` | 2026-06-11 |
| 对象组合 | known | 用户已理解 `Agent` 持有 model、model 持有 provider，能区分 `ModelRequest`/`ModelResponse`，并能说明 `TestModel` 不是 graph node 而是被 `ModelRequestNode` 调用 | 2026-06-10 |
| 执行图与节点 | known | 用户能说明 `CallToolsNode` 根据模型响应决定执行工具后返回 `ModelRequestNode`，或在无需工具时返回 `End` | 2026-06-10 |
| 继承 | not_started | 读 `AbstractAgent`、model/provider 基类会用到 | 2026-06-09 |
| 抽象基类 / 协议 | not_started | 读 `abstract.py` 和 provider 接口会用到 | 2026-06-09 |
| `dataclass` | learning | 用户能把 `@dataclass` 类比为 Java Lombok `@Data`，并判断 `book.price` 会打印 `99`；已理解其用于快速创建保存数据的类 | 2026-06-11 |

## 类型系统

| 知识点 | 状态 | 证据/备注 | 最近更新 |
| --- | --- | --- | --- |
| 类型注解基础 | learning | 用户能准确表述 `unit: str` 是建议/声明参数类型；能说明 `-> int` 表示函数返回值建议是 `int`，不是运行时默认强制；后续在工具函数签名中继续巩固 | 2026-06-11 |
| 泛型：`TypeVar`、`Generic` | learning | 用户能按外观解释 `RunContext[WeatherDeps]`：`ctx` 的类型是 `RunContext`，里面关联/装着 `WeatherDeps` 类型的数据；尚未学习 `TypeVar`/`Generic` 机制 | 2026-06-11 |
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
| 装饰器 | learning | 用户能说明 `@agent.tool_plain` 是注册工具，不是执行工具；仍需继续练习装饰器通用机制 | 2026-06-10 |
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
