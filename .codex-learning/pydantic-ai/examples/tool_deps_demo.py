from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel


@dataclass
class WeatherDeps:
    unit: str


agent = Agent(TestModel(), deps_type=WeatherDeps)


@agent.tool
def get_weather(ctx: RunContext[WeatherDeps], city: str) -> str:
    return city + f": sunny, unit={ctx.deps.unit}"


result = agent.run_sync("What is the weather?", deps=WeatherDeps(unit="C"))
print(result.output)
