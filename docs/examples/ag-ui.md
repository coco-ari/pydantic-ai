# Agent User Interaction (AG-UI) 智能体用户交互 {#agent-user-interaction-ag-ui}

这个示例展示如何将 Pydantic AI 智能体与 [AG-UI Dojo](https://github.com/ag-ui-protocol/ag-ui/tree/main/apps/dojo) 示例应用一起使用。

关于 AG-UI 集成的更多信息，请参见 [AG-UI 文档](../ui/ag-ui.md)。

演示内容：

- [AG-UI](../ui/ag-ui.md)
- [工具](../tools.md)

## 前置条件 {#prerequisites}

- 一个 [OpenAI API key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key)

## 运行示例 {#running-the-example}

在[安装依赖并设置环境变量](./setup.md#usage)后，你需要两个命令行窗口。

### Pydantic AI AG-UI 后端 {#pydantic-ai-ag-ui-backend}

设置你的 OpenAI API Key：

```bash
export OPENAI_API_KEY=<your api key>
```

启动 Pydantic AI AG-UI 示例后端。

```bash
python/uv-run -m pydantic_ai_examples.ag_ui
```

### AG-UI Dojo 示例前端 {#ag-ui-dojo-example-frontend}

接下来运行 AG-UI Dojo 示例前端。

1. 克隆 [AG-UI 仓库](https://github.com/ag-ui-protocol/ag-ui)

    ```shell
    git clone https://github.com/ag-ui-protocol/ag-ui.git
    ```

2. 进入 `ag-ui/typescript-sdk` 目录

    ```shell
    cd ag-ui/sdks/typescript
    ```

3. 按照[官方说明](https://github.com/ag-ui-protocol/ag-ui/tree/main/apps/dojo#development-setup)运行 Dojo app
4. 访问 <http://localhost:3000/pydantic-ai>
5. 在侧边栏中选择 View `Pydantic AI`

## 功能示例 {#feature-examples}

### Agentic Chat 智能体聊天 {#agentic-chat}

这里演示一个基本智能体交互，包括 Pydantic AI server 端工具和 AG-UI client 端工具。

如果你已经[运行示例](#running-the-example)，可以在 <http://localhost:3000/pydantic-ai/feature/agentic_chat> 查看。

#### 智能体工具 {#agent-tools}

- `time` - 用于检查某个时区当前时间的 Pydantic AI 工具
- `background` - 用于设置 client 窗口背景色的 AG-UI 工具

#### 智能体 prompts {#agent-prompts}

```text
What is the time in New York?
```

```text
Change the background to blue
```

下面是一个同时混合 AG-UI 和 Pydantic AI 工具的复杂示例：

```text
Perform the following steps, waiting for the response of each step before continuing:
1. Get the time
2. Set the background to red
3. Get the time
4. Report how long the background set took by diffing the two times
```

#### Agentic Chat 代码 {#agentic-chat-code}

```snippet {path="/examples/pydantic_ai_examples/ag_ui/api/agentic_chat.py"}```

### Agentic Generative UI 智能体生成式 UI {#agentic-generative-ui}

这里演示一个长时间运行的任务，其中智能体会向前端发送更新，让用户知道正在发生什么。

如果你已经[运行示例](#running-the-example)，可以在 <http://localhost:3000/pydantic-ai/feature/agentic_generative_ui> 查看。

#### 计划 prompts {#plan-prompts}

```text
Create a plan for breakfast and execute it
```

#### Agentic Generative UI 代码 {#agentic-generative-ui-code}

```snippet {path="/examples/pydantic_ai_examples/ag_ui/api/agentic_generative_ui.py"}```

### Human in the Loop 人在回路中 {#human-in-the-loop}

这里演示一个简单的 human-in-the-loop 工作流：智能体提出计划，用户可以用复选框批准。

#### 任务规划工具 {#task-planning-tools}

- `generate_task_steps` - 用于生成并确认步骤的 AG-UI 工具

#### 任务规划 prompt {#task-planning-prompt}

```text
Generate a list of steps for cleaning a car for me to review
```

#### Human in the Loop 代码 {#human-in-the-loop-code}

```snippet {path="/examples/pydantic_ai_examples/ag_ui/api/human_in_the_loop.py"}```

### Predictive State Updates 预测式状态更新 {#predictive-state-updates}

这里演示如何使用 predictive state updates 功能，根据智能体响应更新 UI 状态，包括通过用户确认进行交互。

如果你已经[运行示例](#running-the-example)，可以在 <http://localhost:3000/pydantic-ai/feature/predictive_state_updates> 查看。

#### 故事工具 {#story-tools}

- `write_document` - 用于将文档写入窗口的 AG-UI 工具
- `document_predict_state` - 为 `write_document` 工具启用文档状态预测的 Pydantic AI 工具

这里也展示如何基于共享状态信息使用自定义 instructions。

#### 故事示例 {#story-example}

起始文档文本：

```markdown
Bruce was a good dog,
```

智能体 prompt：

```text
Help me complete my story about bruce the dog, is should be no longer than a sentence.
```

#### Predictive State Updates 代码 {#predictive-state-updates-code}

```snippet {path="/examples/pydantic_ai_examples/ag_ui/api/predictive_state_updates.py"}```

### Shared State 共享状态 {#shared-state}

这里演示如何使用 UI 和智能体之间的共享状态。

发送给智能体的状态会由基于函数的 instruction 检测。随后会用自定义 pydantic 模型验证数据，再用它创建智能体要遵循的 instructions，并通过 AG-UI 工具发送给 client。

如果你已经[运行示例](#running-the-example)，可以在 <http://localhost:3000/pydantic-ai/feature/shared_state> 查看。

#### 食谱工具 {#recipe-tools}

- `display_recipe` - 用于以图形格式显示食谱的 AG-UI 工具

#### 食谱示例 {#recipe-example}

1. 自定义食谱的基本设置
2. 点击 `Improve with AI`

#### Shared State 代码 {#shared-state-code}

```snippet {path="/examples/pydantic_ai_examples/ag_ui/api/shared_state.py"}```

### Tool Based Generative UI 基于工具的生成式 UI {#tool-based-generative-ui}

这里演示如何为带用户确认的工具输出使用自定义渲染。

如果你已经[运行示例](#running-the-example)，可以在 <http://localhost:3000/pydantic-ai/feature/tool_based_generative_ui> 查看。

#### Haiku 工具 {#haiku-tools}

- `generate_haiku` - 用于展示英文和日文 haiku 的 AG-UI 工具

#### Haiku prompt {#haiku-prompt}

```text
Generate a haiku about formula 1
```

#### Tool Based Generative UI 代码 {#tool-based-generative-ui-code}

```snippet {path="/examples/pydantic_ai_examples/ag_ui/api/tool_based_generative_ui.py"}```
