# 使用 Modal 构建 Slack Lead Qualifier {#slack-lead-qualifier-with-modal}

在这个示例中，我们将构建一个 agentic 应用，它会：

- 自动研究每个加入公司公开 Slack 社区的新成员，判断他们与公司商业产品的匹配程度；
- 将分析发送到一个（私有）Slack channel；并且
- 每天将过去 24 小时内排名前 5 的 leads 摘要发送到另一个 Slack channel。

我们会把应用部署到 [Modal](https://modal.com)，因为它允许你用 Python 定义带 Web endpoints、scheduled functions 和 background functions 的应用，并通过 CLI 部署，而无需搭建或管理任何基础设施。这是一种很好的方式，可以降低组织内成员开始构建和部署 AI agents 来简化工作的门槛。

我们还会添加 [Pydantic Logfire](https://pydantic.dev/logfire)，以便在应用和 agent 响应 webhooks 与 schedule 运行时获得可观测性。

## 截图 {#screenshots}

发送到 Slack 的分析看起来会像这样：

![Slack 消息](../img/slack-lead-qualifier-slack.png)

对应的 [Logfire](https://pydantic.dev/logfire) trace 看起来会像这样：

![Logfire trace 追踪](../img/slack-lead-qualifier-logfire.png)

这些条目都可以点击，以查看该步骤发生了什么的更多细节，包括与 LLM 的完整对话，以及 HTTP requests 和 responses。

## 前置条件 {#prerequisites}

如果你只想看代码，而不想实际完成运行所需的各项设置，可以直接[跳到代码](#the-code)。

### Slack app 应用 {#slack-app}

你需要有一个 Slack workspace，并具备创建 apps 所需的权限。

2. 按 <https://docs.slack.dev/quickstart> 的说明创建一个新的 Slack app。
    1. 在第 2 步 "Requesting scopes" 中，请求以下 scopes：
        - [`users.read`](https://docs.slack.dev/reference/scopes/users.read)
        - [`users.read.email`](https://docs.slack.dev/reference/scopes/users.read.email)
        - [`users.profile.read`](https://docs.slack.dev/reference/scopes/users.profile.read)
    2. 在第 3 步 "Installing and authorizing the app" 中，记下 Access Token，因为我们稍后需要把它存为 Modal 中的 Secret。
    3. 可以跳过第 4 步和第 5 步。我们需要订阅 `team_join` 事件，但此时你还没有 webhook URL。
1. 创建应用要发布消息的 channels，并把 Slack app 添加进去：
    - `#new-slack-leads`
    - `#daily-slack-leads-summary`

    这些名称在示例中是硬编码的。如果你想使用不同 channels，可以 clone 仓库并在 `examples/pydantic_ai_examples/slack_lead_qualifier/functions.py` 中修改它们。

### Logfire Write Token 写入令牌 {#logfire-write-token}

1. 如果你还没有 Logfire 账号，请在 <https://logfire-us.pydantic.dev/> 创建一个。
2. 创建一个新项目，例如命名为 `slack-lead-qualifier`。
3. 生成一个新的 Write Token 并记下它，因为我们稍后需要把它存为 Modal 中的 Secret。

### OpenAI API Key 密钥 {#openai-api-key}

1. 如果你还没有 OpenAI 账号，请在 <https://platform.openai.com/> 创建一个。
2. 在 Settings 中创建一个新的 API Key 并记下它，因为我们稍后需要把它存为 Modal 中的 Secret。

### Modal 账号 {#modal-account}

1. 如果你还没有 Modal 账号，请在 <https://modal.com/signup> 创建一个。
2. 在 <https://modal.com/secrets> 创建 3 个 "Custom" 类型的 Secrets：
    - Name: `slack`，key: `SLACK_API_KEY`，value: 你之前生成的 Slack Access Token
    - Name: `logfire`，key: `LOGFIRE_TOKEN`，value: 你之前生成的 Logfire Write Token
    - Name: `openai`，key: `OPENAI_API_KEY`，value: 你之前生成的 OpenAI API Key

## 使用方式 {#usage}

1. 确保你已经[安装依赖](./setup.md#usage)。

2. 使用 Modal 认证：

    ```bash
    python/uv-run -m modal setup
    ```

3. 将示例作为 [ephemeral Modal app](https://modal.com/docs/guide/apps#ephemeral-apps) 运行，这意味着它只会运行到你用 Ctrl+C 退出为止：

    ```bash
    python/uv-run -m modal serve -m pydantic_ai_examples.slack_lead_qualifier.modal
    ```

4. 记下 `Created web function web_app =>` 之后的 URL，这就是你的 webhook endpoint URL。

5. 回到 <https://docs.slack.dev/quickstart>，按照第 4 步 "Configuring the app for event listening"，用你记下的 webhook endpoint URL 作为 Request URL 订阅 `team_join` 事件。

现在，当有新成员（也可以是你用临时邮箱创建的用户）加入 Slack workspace 时，你会在运行 `modal serve` 的终端和 Logfire Live view 中看到 webhook event 被处理。等待几秒后，你应该能在 `#new-slack-leads` Slack channel 看到结果。

!!! note "模拟 Slack 注册"
    你也可以像下面这样伪造一个 Slack signup event，用任意姓名或邮箱试用这个 agent：

    ```bash
    curl -X POST <webhook endpoint URL> \
    -H "Content-Type: application/json" \
    -d '{
        "type": "event_callback",
        "event": {
            "type": "team_join",
            "user": {
                "profile": {
                    "email": "samuel@pydantic.dev",
                    "first_name": "Samuel",
                    "last_name": "Colvin",
                    "display_name": "Samuel Colvin"
                }
            }
        }
    }'
    ```

!!! note "部署到生产环境"
    如果你想把这个应用以持久方式部署到自己的 Modal workspace，可以使用这个命令：

    ```bash
    python/uv-run -m modal deploy -m pydantic_ai_examples.slack_lead_qualifier.modal
    ```

    你可能会想先[下载代码](https://github.com/pydantic/pydantic-ai/tree/main/examples/pydantic_ai_examples/slack_lead_qualifier)，放到一个新 repo 中，然后用 GitHub Actions 做[持续部署](https://modal.com/docs/guide/continuous-deployment#github-actions)。

    不要忘记把 Slack event request URL 更新为新的持久 URL。你还需要根据自己的情况修改 [agent 的 instructions](#agent)。

## 代码 {#the-code}

我们将从基础部分开始，然后逐步构建成完整应用。

### Models 模型 {#models}

#### `Profile`

首先，我们定义一个表示 Slack user profile 的 [Pydantic](https://docs.pydantic.dev) 模型。这些字段来自 [`team_join`](https://docs.slack.dev/reference/events/team_join) 事件，该事件会发送到稍后要定义的 webhook endpoint。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/models.py" fragment="profile"}```

我们还定义了一个 `Profile.as_prompt()` helper 方法，它使用 [`format_as_xml`][pydantic_ai.format_prompt.format_as_xml] 将 profile 转换为可发送给模型的字符串。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/models.py" fragment="import-format_as_xml profile-intro profile-as_prompt"}```

#### `Analysis`

我们需要的第二个模型表示 agent 将执行的分析结果。我们包含 docstrings，为模型提供这些字段应包含内容的额外上下文。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/models.py" fragment="analysis"}```

我们还定义了一个 `Analysis.as_slack_blocks()` helper 方法，将分析转换为一些 [Slack blocks](https://api.slack.com/reference/block-kit/blocks)，以便发送给 Slack API 来发布新消息。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/models.py" fragment="analysis-intro analysis-as_slack_blocks"}```

### Agent 智能体 {#agent}

现在进入 Pydantic AI，定义负责实际分析的 agent。

我们指定要使用的模型（`openai:gpt-5`）、提供 [instructions](../agent.md#instructions)、让 agent 访问 [DuckDuckGo search tool](../common-tools.md#duckduckgo-search-tool)，并告诉它使用 [Native Output](../output.md#native-output) 结构化输出模式输出 `Analysis` 或 `None`。

这个应用真正重要的部分在 instructions 中，它告诉 agent 如何评估每个新的 Slack 成员。如果你计划自己使用这个应用，当然需要根据自己的情况修改它们。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/agent.py" fragment="imports agent"}```

#### `analyze_profile`

我们还定义了一个 `analyze_profile` helper 函数，它接收 `Profile`、运行 agent，并返回 `Analysis`（或 `None`），同时用 [Logfire](../logfire.md) 做 instrumentation。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/agent.py" fragment="analyze_profile"}```

### 分析存储 {#analysis-store}

下一个需要的构建块，是一个用来存储所有已完成分析的位置，这样在发送每日摘要时可以查询它们。

幸运的是，Modal 为我们提供了一种方便的方式，可以存储一些数据，并在后续 Modal run（webhook 或 scheduled）中读回：[`modal.Dict`](https://modal.com/docs/reference/modal.Dict)。

我们定义了一些便捷方法，用于轻松添加、列出和清空分析。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/store.py" fragment="import-modal analysis_store"}```

!!! note
    注意最后一行的 `# type: ignore`。遗憾的是，`modal` 没有完整定义它的类型，因此我们需要它来阻止静态类型检查器 `pyright` 报错；我们会对所有 Pydantic AI 代码（包括示例）运行 pyright。

### 发送 Slack 消息 {#send-slack-message}

接下来，我们需要一种真正发送 Slack 消息的方式，因此定义一个简单函数来使用 Slack 的 [`chat.postMessage`](https://api.slack.com/methods/chat.postMessage) API。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/slack.py" fragment="send_slack_message"}```

### 功能 {#features}

现在可以开始把这些构建块组合起来，实现我们想要的实际功能。

#### `process_slack_member`

这个函数接收 [`Profile`](#profile)，用 agent [分析](#analyze_profile)它，将其添加到 [`AnalysisStore`](#analysis-store)，并把分析[发送](#send-slack-message)到 `#new-slack-leads` channel。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/functions.py" fragment="imports constant-new_lead_channel process_slack_member"}```

#### `send_daily_summary`

这个函数列出 [`AnalysisStore`](#analysis-store) 中的所有分析，按相关性取前 5 个，[发送](#send-slack-message)到 `#daily-slack-leads-summary` channel，并清空 `AnalysisStore`，这样下一次每日运行不会再次处理这些分析。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/functions.py" fragment="imports-daily_summary constant-daily_summary_channel send_daily_summary"}```

### Web app 应用 {#web-app}

目前，这两个函数实际上还没有从任何地方被调用。

我们来实现一个 [FastAPI](https://fastapi.tiangolo.com/) endpoint，用于处理 `team_join` Slack webhook（也称为 [Slack Events API](https://docs.slack.dev/apis/events-api)），并调用刚刚定义的 [`process_slack_member`](#process_slack_member) 函数。顺手也用 Logfire 对 FastAPI 做 instrumentation。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/app.py" fragment="app"}```

#### 使用 Modal 的 `process_slack_member` {#process_slack_member-with-modal}

这里稍微做了一点绕行：我们并没有直接调用 `functions.py` 中定义的 [`process_slack_member`](#process_slack_member) 函数，因为 Slack 要求 webhooks 在 3 秒内响应，而我们需要更多时间来与 LLM 通信、做一些 Web searches，并发送 Slack 消息。

相反，我们调用了下面这个与 app 一起定义的函数，它使用 Modal 的 [`modal.Function.spawn`](https://modal.com/docs/reference/modal.Function#spawn) 功能在后台运行函数。（如果你好奇这个函数在 Modal 侧是什么样，可以[跳到后面的部分](#backgrounded-process_slack_member)。）

因为 `modal.py`（下一节会看到）会 import `app.py`，所以我们在函数定义内部从 `modal.py` import；如果在顶层 import，会导致 circular import error。

我们还会传递当前 Logfire context 来获得 [Distributed Tracing](https://logfire.pydantic.dev/docs/how-to-guides/distributed-tracing/)，这意味着后台函数执行会作为 webhook request trace 的子节点显示，从而把与该请求相关的一切都放在一个地方。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/app.py" fragment="process_slack_member"}```

### Modal app 应用 {#modal-app}

现在看看 Modal 如何让部署这一切变得容易。

#### 设置 Modal {#set-up-modal}

我们做的第一件事是定义 Modal app，指定要使用的 base image（带 Python 3.13 的 Debian）、它需要的所有 Python packages，以及运行时需要可用的 Modal 界面中定义的所有 secrets。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py" fragment="setup_modal"}```

#### 设置 Logfire {#set-up-logfire}

接下来，我们定义一个函数，为 Pydantic AI 和 HTTPX 设置 Logfire instrumentation。

不能在文件顶层做这件事，因为所请求的 packages（如 `logfire`）只会在 Modal 上运行的函数中可用（例如后面要定义的函数）。这个文件 `modal.py` 会在你的本地机器上运行，并且本地只访问 `modal` package。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py" fragment="setup_logfire"}```

#### Web app

要在 Modal 上部署 [web endpoint](https://modal.com/docs/guide/webhooks)，只需定义一个返回 ASGI app（例如 FastAPI）的函数，并用 `@app.function()` 和 `@modal.asgi_app()` 装饰它。

这个 `web_app` 函数会在 Modal 上运行，因此在函数内部可以调用需要 `logfire` package 的 `setup_logfire` 函数，并 import 使用其他 requested packages 的 `app.py`。

默认情况下，Modal 会按需启动一个容器来处理一次函数调用（例如 Web request），这意味着每个请求都会有一点启动时间。不过 Slack 要求 webhooks 在 3 秒内响应，因此我们指定 `min_containers=1`，让 web endpoint 始终保持运行并随时准备响应请求。这有点麻烦且有些浪费，但好在 [Modal 的定价](https://modal.com/pricing) 相当合理，每月有 $30 免费计算额度，并为 startup 和 academic researchers 提供最高 $50k 的免费 credits。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py" fragment="web_app"}```

!!! note
    注意 `@modal.asgi_app()` 行上的 `# type: ignore`。遗憾的是，`modal` 没有完整定义它的类型，因此我们需要它来阻止静态类型检查器 `pyright` 报错；我们会对所有 Pydantic AI 代码（包括示例）运行 pyright。

#### Scheduled `send_daily_summary` {#scheduled-send_daily_summary}

要定义 [scheduled function](https://modal.com/docs/guide/cron)，可以使用带 `schedule` 参数的 `@app.function()` 装饰器。这个 Modal function 会每天 UTC 上午 8 点调用我们导入的 [`send_daily_summary`](#send_daily_summary) 函数。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py" fragment="send_daily_summary"}```

#### 后台运行的 `process_slack_member` {#backgrounded-process_slack_member}

最后，我们定义一个 Modal function，包装 [`process_slack_member`](#process_slack_member) 函数，使它可以在后台运行。

你应该还记得，我们从 [web app spawn 这个函数](#process_slack_member-with-modal)时传递了 Logfire context 以获得 [Distributed Tracing](https://logfire.pydantic.dev/docs/how-to-guides/distributed-tracing/)，因此这里需要附加它。

```snippet {path="/examples/pydantic_ai_examples/slack_lead_qualifier/modal.py" fragment="process_slack_member"}```

## 结论 {#conclusion}

就是这样。现在，假设你已经满足[前置条件](#prerequisites)，就可以使用[使用方式](#usage)下的命令运行或部署这个应用。
