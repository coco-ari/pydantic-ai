from __future__ import annotations

import os
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider


def load_local_env() -> None:
    """读取同目录 `.env`；只填充当前进程环境变量，不把密钥写入 Git。"""
    env_path = Path(__file__).with_name('.env')
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue

        name, value = line.split('=', 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        # 本地学习示例以同目录 `.env` 为准，避免 shell 里残留的旧变量误导请求。
        if name:
            os.environ[name] = value


def require_env(name: str) -> str:
    """读取必需环境变量；密钥缺失时尽早报错，避免把 API key 写进源码。"""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f'请先在 `.env` 或环境变量中设置 `{name}`。')
    return value


load_local_env()

REQUEST_TIMEOUT_SECONDS = 30

api_key = require_env('OPENAI_API_KEY')
base_url = os.getenv('OPENAI_BASE_URL')
model_name = os.getenv('PYDANTIC_AI_MODEL', 'gpt-5.5')

# OpenAI-compatible API 通常复用 OpenAI SDK 协议：
# - 官方 OpenAI 可以不设置 base_url；
# - 第三方兼容服务需要设置 OPENAI_BASE_URL，例如 https://example.com/v1。
provider = OpenAIProvider(api_key=api_key, base_url=base_url)
model = OpenAIChatModel(model_name, provider=provider)

print(
    f'正在请求：base_url={provider.base_url}, '
    f'model={model_name}, api_key=已设置, timeout={REQUEST_TIMEOUT_SECONDS}s'
)

agent = Agent(
    model,
    instructions='你是一个耐心的 Python 老师，用中文简洁回答。',
    model_settings={'timeout': REQUEST_TIMEOUT_SECONDS},
)

result = agent.run_sync('Python 的基础变量有哪些？')
print(result.output)
