# 使用 Restate 的持久化执行

[Restate](https://restate.dev) 是一个轻量级持久化执行运行时，对 AI 智能体提供一等支持。Pydantic AI 集成通过 [Restate Python SDK](https://github.com/restatedev/sdk-python/tree/main/python/restate/ext/pydantic) 提供。

更多信息请访问 [Restate 文档](https://docs.restate.dev/ai/patterns/durable-agents)。

## 持久化执行

Restate 会将智能体执行的每一步记录到 journal 中，从而让智能体具备**持久化**能力。如果进程在执行中崩溃，Restate 会重放 journal，跳过已完成步骤，并从中断位置继续执行。

你的智能体运行在 Restate **service** 内的普通 HTTP handler 中。Restate Server 位于应用前方，负责管理编排、journaling 和重试。服务可以像普通 Docker 容器或 serverless 函数一样运行。

持久化智能体包含三个构建块：

1. **handler**：你的智能体逻辑，在 Restate service 中作为 HTTP endpoint 暴露。
2. **LLM 调用**：会被持久化，因此恢复时不会重新获取响应，从而节省成本和时间。
3. **工具执行**：包装在持久化步骤中，因此副作用不会重复发生。

```text
                  Clients
              (HTTP, Kafka, etc.)
                     |
                     v
            +---------------------+
            |   Restate Server    |      (Journals execution,
            +---------------------+       retries on failure,
                     ^                    manages state)
                     |
        Journal      |   Replay on
        steps,       |   recovery,
        retries      |   schedule calls
                     v
+------------------------------------------------------+
|               Application Process                    |
|   +----------------------------------------------+   |
|   |         Restate Service Handler              |   |
|   |           (Agent Run Loop)                   |   |
|   |    [ Durable Steps (Tool, MCP, Model) ]      |   |
|   +----------------------------------------------+   |
|         |           |                |               |
+------------------------------------------------------+
          |           |                |
          v           v                v
      [External APIs, services, databases, etc.]
```

更多信息请参见 [Restate 文档](https://docs.restate.dev/ai/patterns/durable-agents)。

## 持久化智能体

任何 Pydantic AI 智能体都可以通过 Restate SDK 中的 `RestateAgent` 包装，并在 Restate service handler 中运行，从而变为持久化智能体。

安装 Restate SDK：

```bash
pip/uv-add pydantic-ai "restate_sdk[serde]"
```

下面是一个使用 Restate 构建持久化 Pydantic AI 智能体的完整示例：

```python {title="restate_agent.py" test="skip" lint="skip"}
import restate
from pydantic_ai import Agent, RunContext
from restate.ext.pydantic import RestateAgent, restate_context

weather_agent = Agent(  # (1)!
    'openai:gpt-5.2',
    system_prompt='You are a helpful agent that provides weather updates.',
)


@weather_agent.tool()
async def get_weather(_run_ctx: RunContext[None], city: str) -> dict:
    """Get the current weather for a given city."""

    # Do durable tool steps using the Restate context
    async def call_weather_api(city: str) -> dict:
        return {'temperature': 23, 'description': 'Sunny and warm.'}

    return await restate_context().run_typed(  # (2)!
        f'Get weather {city}', call_weather_api, city=city
    )


restate_agent = RestateAgent(weather_agent)  # (3)!

agent_service = restate.Service('WeatherAgent')


@agent_service.handler()
async def run(_ctx: restate.Context, prompt: str) -> str:  # (4)!
    result = await restate_agent.run(prompt)
    return result.output


app = restate.app(services=[agent_service])  # (5)!

if __name__ == "__main__":  # (6)!
    import hypercorn
    import asyncio
    conf = hypercorn.Config()
    conf.bind = ["0.0.0.0:9080"]
    asyncio.run(hypercorn.asyncio.serve(app, conf))
```

1. 像平常使用 Pydantic AI 一样定义智能体和工具。
2. 在工具内部使用 `restate_context()` action，让工具执行具备持久化能力。结果会被持久化，并重试直到成功。恢复时不会重复执行副作用。
3. `RestateAgent` 包装智能体，使每个 LLM 响应都保存在 Restate Server 中，并在恢复期间重放。
4. Restate service handler 为智能体提供持久化执行上下文，并将其作为 HTTP endpoint 暴露。
5. `restate.app()` 创建可被服务的应用。
6. 使用 Hypercorn 等 ASGI server 运行应用。

了解如何运行智能体，请参见 [Restate agent quickstart](https://docs.restate.dev/ai-quickstart)。
