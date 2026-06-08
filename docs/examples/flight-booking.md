一个多智能体流程示例：一个智能体将工作委托给另一个智能体，然后把控制权移交给第三个智能体。

演示内容：

* [智能体委托](../multi-agent-applications.md#agent-delegation)
* [程序化智能体移交](../multi-agent-applications.md#programmatic-agent-hand-off)
* [用量限制](../agent.md#usage-limits)

在这个场景中，一组智能体协作，为用户找到最佳航班。

此示例的控制流可概括如下：

```mermaid
graph TD
  START --> search_agent("search agent")
  search_agent --> extraction_agent("extraction agent")
  extraction_agent --> search_agent
  search_agent --> human_confirm("human confirm")
  human_confirm --> search_agent
  search_agent --> FAILED
  human_confirm --> find_seat_function("find seat function")
  find_seat_function --> human_seat_choice("human seat choice")
  human_seat_choice --> find_seat_agent("find seat agent")
  find_seat_agent --> find_seat_function
  find_seat_function --> buy_flights("buy flights")
  buy_flights --> SUCCESS
```

## 运行示例

在[安装依赖并设置环境变量](./setup.md#usage)后运行：

```bash
python/uv-run -m pydantic_ai_examples.flight_booking
```

## 示例代码

```snippet {path="/examples/pydantic_ai_examples/flight_booking.py"}```
