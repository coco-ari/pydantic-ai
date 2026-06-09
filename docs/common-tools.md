# 常用工具 {#common-tools}

Pydantic AI 提供了一些原生工具，可用于增强 agent 的能力。

## DuckDuckGo 搜索工具 {#duckduckgo-search-tool}

DuckDuckGo 搜索工具允许你在 web 上搜索信息。它构建在 [DuckDuckGo API](https://github.com/deedy5/ddgs) 之上。

### 安装 {#installation}

要使用 [`duckduckgo_search_tool`][pydantic_ai.common_tools.duckduckgo.duckduckgo_search_tool]，你需要安装带有 `duckduckgo` 可选组的 [`pydantic-ai-slim`](install.md#slim-install)：

```bash
pip/uv-add "pydantic-ai-slim[duckduckgo]"
```

### 用法 {#usage}

下面展示如何在 agent 中使用 DuckDuckGo search tool：

```py {title="duckduckgo_search.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

agent = Agent(
    'openai:gpt-5.2',
    tools=[duckduckgo_search_tool()],
    instructions='Search DuckDuckGo for the given query and return the results.',
)

result = agent.run_sync(
    'Can you list the top five highest-grossing animated films of 2025?'
)
print(result.output)
"""
I looked into several sources on animated box‐office performance in 2025, and while detailed
rankings can shift as more money is tallied, multiple independent reports have already
highlighted a couple of record‐breaking shows. For example:

• Ne Zha 2 – News outlets (Variety, Wikipedia's "List of animated feature films of 2025", and others)
    have reported that this Chinese title not only became the highest‑grossing animated film of 2025
    but also broke records as the highest‑grossing non‑English animated film ever. One article noted
    its run exceeded US$1.7 billion.
• Inside Out 2 – According to data shared on Statista and in industry news, this Pixar sequel has been
    on pace to set new records (with some sources even noting it as the highest‑grossing animated film
    ever, as of January 2025).

Beyond those two, some entertainment trade sites (for example, a Just Jared article titled
"Top 10 Highest-Earning Animated Films at the Box Office Revealed") have begun listing a broader
top‑10. Although full consolidated figures can sometimes differ by source and are updated daily during
a box‑office run, many of the industry trackers have begun to single out five films as the biggest
earners so far in 2025.

Unfortunately, although multiple articles discuss the "top animated films" of 2025, there isn't yet a
single, universally accepted list with final numbers that names the complete top five. (Box‑office
rankings, especially mid‑year, can be fluid as films continue to add to their totals.)

Based on what several sources note so far, the two undisputed leaders are:
1. Ne Zha 2
2. Inside Out 2

The remaining top spots (3–5) are reported by some outlets in their "Top‑10 Animated Films"
lists for 2025 but the titles and order can vary depending on the source and the exact cut‑off
date of the data. For the most up‑to‑date and detailed ranking (including the 3rd, 4th, and 5th
highest‑grossing films), I recommend checking resources like:
• Wikipedia's "List of animated feature films of 2025" page
• Box‑office tracking sites (such as Box Office Mojo or The Numbers)
• Trade articles like the one on Just Jared

To summarize with what is clear from the current reporting:
1. Ne Zha 2
2. Inside Out 2
3–5. Other animated films (yet to be definitively finalized across all reporting outlets)

If you're looking for a final, consensus list of the top five, it may be best to wait until
the 2025 year‑end box‑office tallies are in or to consult a regularly updated entertainment industry source.

Would you like help finding a current source or additional details on where to look for the complete updated list?
"""
```

## Web 抓取工具 {#web-fetch-tool}

Web 抓取工具允许你的 agent 获取网页内容并将其转换为 markdown。它使用 [SSRF protection](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery) 来防止服务器端请求伪造攻击。

### 安装 {#installation}

要使用 [`web_fetch_tool`][pydantic_ai.common_tools.web_fetch.web_fetch_tool]，你需要安装带有 `web-fetch` 可选组的 [`pydantic-ai-slim`](install.md#slim-install)：

```bash
pip/uv-add "pydantic-ai-slim[web-fetch]"
```

### 用法 {#usage}

下面展示如何在 agent 中使用 web fetch tool：

```py {title="web_fetch.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.common_tools.web_fetch import web_fetch_tool

agent = Agent(
    'openai:gpt-5.2',
    tools=[web_fetch_tool()],
    instructions='Fetch web pages and summarize their content.',
)

result = agent.run_sync('What is on https://ai.pydantic.dev?')
print(result.output)
```

!!! tip "通过 WebFetch capability 自动 fallback"
    你不需要直接使用 [`web_fetch_tool`][pydantic_ai.common_tools.web_fetch.web_fetch_tool]；当模型不支持 native URL fetching 时，[`WebFetch`][pydantic_ai.capabilities.WebFetch] capability 会自动将它用作本地 fallback。

## Tavily 搜索工具 {#tavily-search-tool}

!!! info
    Tavily 是付费服务，但他们提供免费额度用于试用产品。

    你需要[注册账号](https://app.tavily.com/home)并获取 API key，才能使用 Tavily 搜索工具。

Tavily 搜索工具允许你在 web 上搜索信息。它构建在 [Tavily API](https://tavily.com/) 之上。

### 安装 {#installation}

要使用 [`tavily_search_tool`][pydantic_ai.common_tools.tavily.tavily_search_tool]，你需要安装带有 `tavily` 可选组的 [`pydantic-ai-slim`](install.md#slim-install)：

```bash
pip/uv-add "pydantic-ai-slim[tavily]"
```

### 用法 {#usage}

下面展示如何在 agent 中使用 Tavily search tool：

```py {title="tavily_search.py" test="skip"}
import os

from pydantic_ai import Agent
from pydantic_ai.common_tools.tavily import tavily_search_tool

api_key = os.getenv('TAVILY_API_KEY')
assert api_key is not None

agent = Agent(
    'openai:gpt-5.2',
    tools=[tavily_search_tool(api_key)],
    instructions='Search Tavily for the given query and return the results.',
)

result = agent.run_sync('Tell me the top news in the GenAI world, give me links.')
print(result.output)
"""
Here are some of the top recent news articles related to GenAI:

1. How CLEAR users can improve risk analysis with GenAI – Thomson Reuters
   Read more: https://legal.thomsonreuters.com/blog/how-clear-users-can-improve-risk-analysis-with-genai/
   (This article discusses how CLEAR's new GenAI-powered tool streamlines risk analysis by quickly summarizing key information from various public data sources.)

2. TELUS Digital Survey Reveals Enterprise Employees Are Entering Sensitive Data Into AI Assistants More Than You Think – FT.com
   Read more: https://markets.ft.com/data/announce/detail?dockey=600-202502260645BIZWIRE_USPRX____20250226_BW490609-1
   (This news piece highlights findings from a TELUS Digital survey showing that many enterprise employees use public GenAI tools and sometimes even enter sensitive data.)

3. The Essential Guide to Generative AI – Virtualization Review
   Read more: https://virtualizationreview.com/Whitepapers/2025/02/SNOWFLAKE-The-Essential-Guide-to-Generative-AI.aspx
   (This guide provides insights into how GenAI is revolutionizing enterprise strategies and productivity, with input from industry leaders.)

Feel free to click on the links to dive deeper into each story!
"""
```

### 配置参数 {#configuring-parameters}

`tavily_search_tool` factory 接受用于控制搜索行为的可选参数。`max_results` 始终由开发者控制，永远不会出现在 LLM tool schema 中。其他参数在提供时会固定用于所有搜索，并从 LLM 的 tool schema 中隐藏。未设置的参数仍可由 LLM 在每次调用时设置。

例如，你可以在创建工具时锁定 `max_results` 和 `include_domains`，同时仍允许 LLM 控制 `exclude_domains`：

```py {title="tavily_domain_filtering.py"}
import os

from pydantic_ai import Agent
from pydantic_ai.common_tools.tavily import tavily_search_tool

api_key = os.getenv('TAVILY_API_KEY')
assert api_key is not None

agent = Agent(
    'openai:gpt-5.2',
    tools=[tavily_search_tool(api_key, max_results=5, include_domains=['arxiv.org'])],
    instructions='Search for information and return the results.',
)

result = agent.run_sync(
    'Find recent papers about transformer architectures'
)
print(result.output)
"""
Here are some recent papers about transformer architectures from arxiv.org:

1. "Attention Is All You Need" - The foundational paper on the Transformer model.
2. "FlashAttention: Fast and Memory-Efficient Exact Attention" - Proposes an IO-aware attention algorithm.
"""
```

## Exa 搜索工具 {#exa-search-tool}

!!! info
    Exa 是带免费试用额度的付费服务。

    你需要[注册账号](https://dashboard.exa.ai)并获取 API key，才能使用 Exa 工具。

Exa 是一个 neural search engine，可在数十亿网页中查找高质量、相关的结果。它提供多个工具，包括 web search、查找相似页面、内容检索和 AI-powered answers。

### 安装 {#installation}

要使用 Exa tools，你需要安装带有 `exa` 可选组的 [`pydantic-ai-slim`](install.md#slim-install)：

```bash
pip/uv-add "pydantic-ai-slim[exa]"
```

### 用法 {#usage}

你可以单独使用 Exa tools，也可以将其作为 toolset 使用。可用工具如下：

- [`exa_search_tool`][pydantic_ai.common_tools.exa.exa_search_tool]：使用多种搜索类型（auto、keyword、neural、fast、deep）搜索 web
- [`exa_find_similar_tool`][pydantic_ai.common_tools.exa.exa_find_similar_tool]：查找与给定 URL 相似的页面
- [`exa_get_contents_tool`][pydantic_ai.common_tools.exa.exa_get_contents_tool]：从 URLs 获取全文内容
- [`exa_answer_tool`][pydantic_ai.common_tools.exa.exa_answer_tool]：获取带 citations 的 AI-powered answers

#### 使用单个工具 {#using-individual-tools}

```py {title="exa_search.py" test="skip"}
import os

from pydantic_ai import Agent
from pydantic_ai.common_tools.exa import exa_search_tool

api_key = os.getenv('EXA_API_KEY')
assert api_key is not None

agent = Agent(
    'openai:gpt-5.2',
    tools=[exa_search_tool(api_key, num_results=5, max_characters=1000)],
    system_prompt='Search the web for information using Exa.',
)

result = agent.run_sync('What are the latest developments in quantum computing?')
print(result.output)
```

#### 使用 ExaToolset {#using-exatoolset}

使用多个 Exa tools 时，为了提高效率，请使用 [`ExaToolset`][pydantic_ai.common_tools.exa.ExaToolset]，它会在所有工具之间共享单个 API client。你可以配置要包含哪些工具：

```py {title="exa_toolset.py" test="skip"}
import os

from pydantic_ai import Agent
from pydantic_ai.common_tools.exa import ExaToolset

api_key = os.getenv('EXA_API_KEY')
assert api_key is not None

toolset = ExaToolset(
    api_key,
    num_results=5,
    max_characters=1000,  # 限制文本内容以控制 token 使用量
    include_search=True,  # 包含 search tool（默认：True）
    include_find_similar=True,  # 包含 find_similar tool（默认：True）
    include_get_contents=False,  # 排除 get_contents tool
    include_answer=True,  # 包含 answer tool（默认：True）
)

agent = Agent(
    'openai:gpt-5.2',
    toolsets=[toolset],
    system_prompt='You have access to Exa search tools to find information on the web.',
)

result = agent.run_sync('Find recent AI research papers and summarize the key findings.')
print(result.output)
```
