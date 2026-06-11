from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel


@dataclass
class WeatherDeps:
    unit: str
    source: str


agent = Agent(TestModel(), deps_type=WeatherDeps)


@agent.tool
def get_weather(ctx: RunContext[WeatherDeps], city: str) -> str:
    return f"{city}: unit={ctx.deps.unit}, source={ctx.deps.source}"


first = agent.run_sync("weather please", deps=WeatherDeps(unit="C", source="local"))
second = agent.run_sync("weather please", deps=WeatherDeps(unit="F", source="remote"))

print(first.output)
print(second.output)
