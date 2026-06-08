使用 **Pydantic AI** 构建的医疗分诊和委托系统，展示编排智能体（`triage_agent`）如何协调多个专科智能体（例如心脏科、神经科和资深临床医生）。

演示内容：
- [智能体委托与协调](../multi-agent-applications.md#agent-delegation)
- [结构化 `output_type`](../output.md#structured-output)
- [工具](../tools.md)

---

## 概览

此示例展示如何使用**多个 Pydantic AI 智能体**模拟医疗分诊工作流。

该系统包括：
- **全科医生、心脏科和神经科智能体**，用于一级咨询。
- **资深医生智能体**，用于升级处理和治疗计划。
- **分诊智能体（协调者）**，用于决定调用哪个工具以及何时升级。

`triage_agent` 使用两个工具：
1. `consult_specialist`，将主诉路由给领域专科医生。
2. `consult_senior_doctor`，在危急或模糊场景中升级病例。

每位专科医生都会生成结构化的 `MedicalReport`，资深医生会生成结构化的 `TreatmentPlan`。
编排器随后将两者汇总为最终的 `TriageFinalOutput`。

---

## 运行示例

在[安装依赖并设置环境变量](./setup.md#usage)后运行：

```bash
python -m pydantic_ai_examples.medical_agent_delegation

请确保设置有效的 **Cohere API key**，或替换模型引用：

```bash
export CO_API_KEY="your-cohere-api-key"
```

如果愿意，也可以切换到 OpenAI 或 Anthropic 模型：

```python
MODEL = 'openai:gpt-5.2'
```
