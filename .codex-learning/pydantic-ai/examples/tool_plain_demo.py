from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel


agent = Agent(TestModel())


@agent.tool_plain(
    name="weather_lookup",
    description="Get weather for a city",
)
def get_weather(city: str) -> str:
    return city + ": sunny"


result = agent.run_sync("What is the weather?")
print(result.output)
