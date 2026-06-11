from dataclasses import dataclass

from pydantic_ai import RunContext
from pydantic_ai.usage import RunUsage
from pydantic_ai.models.test import TestModel


@dataclass
class WeatherDeps:
    unit: str


def format_weather(ctx: RunContext[WeatherDeps], city: str) -> str:
    return city + f": sunny, unit={ctx.deps.unit}"


deps = WeatherDeps(unit="C")
ctx = RunContext[WeatherDeps](
    deps=deps,
    model=TestModel(),
    usage=RunUsage(),
)

print(format_weather(ctx, "London"))
