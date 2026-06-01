# 依赖

Pydantic AI 使用依赖注入系统，向智能体的 [system prompts](agent.md#system-prompts)、[工具](tools.md)和[输出校验器](output.md#output-validator-functions)提供数据和服务。

与 Pydantic AI 的设计理念一致，我们的依赖系统尽量使用 Python 开发中的既有最佳实践，而不是发明晦涩的“魔法”。这应该能让依赖具备类型安全、易理解、更易测试，并最终更易部署到生产环境。

## 定义依赖

依赖可以是任何 Python 类型。在简单情况下，你也许可以传入单个对象作为依赖（例如 HTTP 连接），但当依赖包含多个对象时，[dataclasses][] 通常是一个方便的容器。

下面是定义一个需要依赖的智能体示例。

（**注意：** 这个示例实际上没有使用依赖，请参见下面的[访问依赖](#访问依赖)。）

```python {title="unused_dependencies.py"}
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent


@dataclass
class MyDeps:  # (1)!
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'openai:gpt-5.2',
    deps_type=MyDeps,  # (2)!
)


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run(
            'Tell me a joke.',
            deps=deps,  # (3)!
        )
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
```

1. 定义一个 dataclass 来保存依赖。
2. 将 dataclass 类型传给 [`Agent` 构造函数][pydantic_ai.agent.Agent.__init__]的 `deps_type` 参数。**注意**：这里传入的是类型，不是实例；这个参数在运行时实际上不会被使用，它存在的目的是让我们能对智能体进行完整类型检查。
3. 运行智能体时，将 dataclass 的实例传给 `deps` 参数。

_（这个示例是完整的，可以“原样”运行；你需要添加 `asyncio.run(main())` 来运行 `main`。）_

## 访问依赖

依赖通过 [`RunContext`][pydantic_ai.tools.RunContext] 类型访问；它应该是 system prompt 函数等的第一个参数。

```python {title="system_prompt_dependencies.py" hl_lines="20-27"}
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'openai:gpt-5.2',
    deps_type=MyDeps,
)


@agent.system_prompt  # (1)!
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  # (2)!
    response = await ctx.deps.http_client.get(  # (3)!
        'https://example.com',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},  # (4)!
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
```

1. [`RunContext`][pydantic_ai.tools.RunContext] 可以作为唯一参数可选地传给 [`system_prompt`][pydantic_ai.agent.Agent.system_prompt] 函数。
2. [`RunContext`][pydantic_ai.tools.RunContext] 会用依赖类型参数化；如果该类型不正确，静态类型检查器会报错。
3. 通过 [`.deps`][pydantic_ai.tools.RunContext.deps] 属性访问依赖。
4. 通过 [`.deps`][pydantic_ai.tools.RunContext.deps] 属性访问依赖。

_（这个示例是完整的，可以“原样”运行；你需要添加 `asyncio.run(main())` 来运行 `main`。）_

除了 [`.deps`][pydantic_ai.tools.RunContext.deps] 之外，[`RunContext`][pydantic_ai.tools.RunContext] 还可以通过 [`.agent`][pydantic_ai.tools.RunContext.agent] 访问正在运行的智能体。当[工具](tools.md)、[hooks](hooks.md) 或 [capabilities](capabilities.md) 需要读取智能体属性（如 [`name`][pydantic_ai.agent.Agent.name] 或 [`output_type`][pydantic_ai.agent.Agent.output_type]）时，这很有用。

依赖字段也可以通过 [template strings](agent-spec.md#template-strings) 在 instructions 和 descriptions 中引用。例如，`TemplateStr('Hello {{name}}')` 会在运行时从 deps 对象渲染 `name`。这在无法使用 callables 的 [agent specs](agent-spec.md) 中尤其有用。

### 异步依赖 vs. 同步依赖

[System prompt 函数](agent.md#system-prompts)、[function tools](tools.md) 和[输出校验器](output.md#output-validator-functions)都会在智能体运行的 async context 中执行。

如果这些函数不是协程（例如 `async def`），它们会通过线程池中的 [`run_in_executor`][asyncio.loop.run_in_executor] 调用。因此，当依赖执行 IO 时，使用 `async` 方法会略好一些，不过同步依赖也应能正常工作。

!!! note "`run` vs. `run_sync` 以及异步依赖 vs. 同步依赖"
    你使用同步依赖还是异步依赖，与使用 `run` 还是 `run_sync` 完全无关。`run_sync` 只是 `run` 的包装器，智能体始终在 async context 中运行。

下面是与上面相同的示例，但使用同步依赖：

```python {title="sync_dependencies.py"}
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.Client  # (1)!


agent = Agent(
    'openai:gpt-5.2',
    deps_type=MyDeps,
)


@agent.system_prompt
def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  # (2)!
    response = ctx.deps.http_client.get(
        'https://example.com', headers={'Authorization': f'Bearer {ctx.deps.api_key}'}
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    deps = MyDeps('foobar', httpx.Client())
    result = await agent.run(
        'Tell me a joke.',
        deps=deps,
    )
    print(result.output)
    #> Did you hear about the toothpaste scandal? They called it Colgate.
```

1. 这里我们使用同步的 `httpx.Client`，而不是异步的 `httpx.AsyncClient`。
2. 为了匹配同步依赖，system prompt 函数现在是普通函数，而不是协程。

_（这个示例是完整的，可以“原样”运行；你需要添加 `asyncio.run(main())` 来运行 `main`。）_

## 完整示例

除了 system prompts，依赖还可以在[工具](tools.md)和[输出校验器](output.md#output-validator-functions)中使用。

```python {title="full_example.py" hl_lines="27-35 38-48"}
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, ModelRetry, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'openai:gpt-5.2',
    deps_type=MyDeps,
)


@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    response = await ctx.deps.http_client.get('https://example.com')
    response.raise_for_status()
    return f'Prompt: {response.text}'


@agent.tool  # (1)!
async def get_joke_material(ctx: RunContext[MyDeps], subject: str) -> str:
    response = await ctx.deps.http_client.get(
        'https://example.com#jokes',
        params={'subject': subject},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    response.raise_for_status()
    return response.text


@agent.output_validator  # (2)!
async def validate_output(ctx: RunContext[MyDeps], output: str) -> str:
    response = await ctx.deps.http_client.post(
        'https://example.com#validate',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
        params={'query': output},
    )
    if response.status_code == 400:
        raise ModelRetry(f'invalid response: {response.text}')
    response.raise_for_status()
    return output


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.
```

1. 要将 `RunContext` 传给工具，请使用 [`tool`][pydantic_ai.agent.Agent.tool] 装饰器。
2. `RunContext` 可以作为第一个参数可选地传给 [`output_validator`][pydantic_ai.agent.Agent.output_validator] 函数。

_（这个示例是完整的，可以“原样”运行；你需要添加 `asyncio.run(main())` 来运行 `main`。）_

## 覆盖依赖

测试智能体时，能够自定义依赖很有用。

虽然有时可以在单元测试中直接调用智能体来实现这一点，但我们也可以在调用应用代码时覆盖依赖，而应用代码内部再调用智能体。

这是通过智能体上的 [`override`][pydantic_ai.agent.Agent.override] 方法完成的。

```python {title="joke_app.py"}
from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient

    async def system_prompt_factory(self) -> str:  # (1)!
        response = await self.http_client.get('https://example.com')
        response.raise_for_status()
        return f'Prompt: {response.text}'


joke_agent = Agent('openai:gpt-5.2', deps_type=MyDeps)


@joke_agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    return await ctx.deps.system_prompt_factory()  # (2)!


async def application_code(prompt: str) -> str:  # (3)!
    ...
    ...
    # now deep within application code we call our agent
    async with httpx.AsyncClient() as client:
        app_deps = MyDeps('foobar', client)
        result = await joke_agent.run(prompt, deps=app_deps)  # (4)!
    return result.output
```

1. 在依赖上定义一个方法，让 system prompt 更容易自定义。
2. 从 system prompt 函数中调用 system prompt factory。
3. 调用智能体的应用代码；在真实应用中，这可能是一个 API endpoint。
4. 从应用代码内部调用智能体；在真实应用中，这个调用可能位于很深的调用栈中。注意，当 deps 被覆盖时，这里的 `app_deps` 不会被使用。

_（这个示例是完整的，可以“原样”运行。）_

```python {title="test_joke_app.py" hl_lines="10-12" call_name="test_application_code" requires="joke_app.py"}
from joke_app import MyDeps, application_code, joke_agent


class TestMyDeps(MyDeps):  # (1)!
    async def system_prompt_factory(self) -> str:
        return 'test prompt'


async def test_application_code():
    test_deps = TestMyDeps('test_key', None)  # (2)!
    with joke_agent.override(deps=test_deps):  # (3)!
        joke = await application_code('Tell me a joke.')  # (4)!
    assert joke.startswith('Did you hear about the toothpaste scandal?')
```

1. 在测试中定义 `MyDeps` 的子类，以自定义 system prompt factory。
2. 创建测试依赖实例；这里不需要传入 `http_client`，因为它不会被使用。
3. 在 `with` 块持续期间覆盖智能体依赖；智能体运行时会使用 `test_deps`。
4. 现在可以安全调用应用代码，智能体会使用被覆盖的依赖。

## 示例

以下示例展示如何在 Pydantic AI 中使用依赖：

- [Weather Agent](examples/weather-agent.md)
- [SQL Generation](examples/sql-gen.md)
- [RAG](examples/rag.md)
