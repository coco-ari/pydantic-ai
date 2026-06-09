# 嵌入 {#embeddings}

Embeddings 是文本的向量表示，用来捕捉语义含义。它们对于构建以下功能很关键：

- **语义搜索**：根据含义查找文档，而不只是匹配关键词
- **RAG (Retrieval-Augmented Generation)**：为你的 AI agents 检索相关上下文
- **相似度检测**：查找相似文档、检测重复内容或聚类内容
- **分类**：将 embeddings 作为下游 ML models 的特征

Pydantic AI 提供统一接口，用于跨多个 providers 生成 embeddings。

## 快速开始 {#quick-start}

[`Embedder`][pydantic_ai.embeddings.Embedder] 类是生成 embeddings 的高层接口：

```python {title="embeddings_quickstart.py"}
from pydantic_ai import Embedder

embedder = Embedder('openai:text-embedding-3-small')


async def main():
    # Embed a search query
    result = await embedder.embed_query('What is machine learning?')
    print(f'Embedding dimensions: {len(result.embeddings[0])}')
    #> Embedding dimensions: 1536

    # Embed multiple documents at once
    docs = [
        'Machine learning is a subset of AI.',
        'Deep learning uses neural networks.',
        'Python is a programming language.',
    ]
    result = await embedder.embed_documents(docs)
    print(f'Embedded {len(result.embeddings)} documents')
    #> Embedded 3 documents
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

!!! tip "查询 vs 文档"
    某些 embedding models 会分别针对查询和文档做不同优化。对搜索查询使用
    [`embed_query()`][pydantic_ai.embeddings.Embedder.embed_query]，对要建立索引的内容使用
    [`embed_documents()`][pydantic_ai.embeddings.Embedder.embed_documents]。

## 嵌入结果 {#embedding-result}

所有 embed 方法都会返回 [`EmbeddingResult`][pydantic_ai.embeddings.EmbeddingResult]，其中包含 embeddings 和有用的 metadata。

为了方便，你可以按索引（`result[0]`）或按原始输入文本（`result['Hello world']`）访问 embeddings。

```python {title="embedding_result.py"}
from pydantic_ai import Embedder

embedder = Embedder('openai:text-embedding-3-small')


async def main():
    result = await embedder.embed_query('Hello world')

    # Access embeddings - each is a sequence of floats
    embedding = result.embeddings[0]  # By index via .embeddings
    embedding = result[0]  # Or directly via __getitem__
    embedding = result['Hello world']  # Or by original input text
    print(f'Dimensions: {len(embedding)}')
    #> Dimensions: 1536

    # Check usage
    print(f'Tokens used: {result.usage.input_tokens}')
    #> Tokens used: 2

    # Calculate cost (requires `genai-prices` to have pricing data for the model)
    cost = result.cost()
    print(f'Cost: ${cost.total_price:.6f}')
    #> Cost: $0.000000
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

## 选择模型 {#choosing-a-model}

最佳 embedding model 取决于你的约束。下面是一份起点速查表；在为大型索引确定模型前，请查阅各 provider 文档和 [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard)。

| 如果你想要... | 例如 |
| --- | --- |
| 托管 API | `openai:text-embedding-3-small`（便宜的默认选择）、`openai:text-embedding-3-large`、`voyageai:voyage-3.5` 或 `cohere:embed-v4.0` |
| 无 API key、私有、免费 | `sentence-transformers:google/embeddinggemma-300m`、`sentence-transformers:lightonai/DenseOn`、`sentence-transformers:Qwen/Qwen3-Embedding-0.6B`，或任何其他 [Hugging Face model](https://huggingface.co/models?library=sentence-transformers) |
| 多语言 | `cohere:embed-multilingual-v3.0`、`sentence-transformers:jinaai/jina-embeddings-v5-text-small-retrieval` 或 `sentence-transformers:Snowflake/snowflake-arctic-embed-l-v2.0` |
| 专门领域 | `voyageai:voyage-code-3`、`voyageai:voyage-law-2`、`voyageai:voyage-finance-2`、`sentence-transformers:nomic-ai/CodeRankEmbed` 或 `sentence-transformers:TechWolf/JobBERT-v3` |
| 运行在已有 AWS 基础设施上 | `bedrock:amazon.titan-embed-text-v2:0` 或 `bedrock:cohere.embed-v4:0` |
| 减小索引大小 | 任何支持维度控制的模型（见[设置](#settings)） |

!!! tip "之后切换模型"
    更换模型会改变输出维度和相似度分布，因此你需要重新 embed（并重新建立索引）你的文档。请选择一个愿意长期使用的模型，或选择支持[维度控制](#settings)的模型，这样无需更换模型也能调整索引大小。

## 提供商 {#providers}

### OpenAI

[`OpenAIEmbeddingModel`][pydantic_ai.embeddings.openai.OpenAIEmbeddingModel] 适用于 OpenAI 的 embeddings API，以及任何 [OpenAI-compatible provider](models/openai.md#openai-compatible-models)。

#### 安装 {#openai-install}

要使用 OpenAI embedding models，你需要安装 `pydantic-ai`，或安装带 `openai` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[openai]"
```

#### 配置 {#openai-configuration}

要通过 OpenAI API 使用 `OpenAIEmbeddingModel`，请前往 [platform.openai.com](https://platform.openai.com/) 并找到生成 API key 的位置。拿到 API key 后，可以将其设置为环境变量：

```bash
export OPENAI_API_KEY='your-api-key'
```

然后即可使用模型：

```python {title="openai_embeddings.py"}
from pydantic_ai import Embedder

embedder = Embedder('openai:text-embedding-3-small')


async def main():
    result = await embedder.embed_query('Hello world')
    print(len(result.embeddings[0]))
    #> 1536
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

可用模型请参阅 [OpenAI's embedding models](https://platform.openai.com/docs/guides/embeddings)。

#### 维度控制 {#openai-dimension-control}

OpenAI 的 `text-embedding-3-*` models 支持通过 `dimensions` 设置降低维度：

```python {title="openai_dimensions.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings import EmbeddingSettings

embedder = Embedder(
    'openai:text-embedding-3-small',
    settings=EmbeddingSettings(dimensions=256),
)


async def main():
    result = await embedder.embed_query('Hello world')
    print(len(result.embeddings[0]))
    #> 256
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

#### OpenAI 兼容提供商 {#openai-compatible}

由于 [`OpenAIEmbeddingModel`][pydantic_ai.embeddings.openai.OpenAIEmbeddingModel] 使用与 [`OpenAIChatModel`][pydantic_ai.models.openai.OpenAIChatModel] 相同的 provider system，你可以将它与任何 [OpenAI 兼容 provider](models/openai.md#openai-compatible-models) 搭配使用：

```python {title="openai_compatible_embeddings.py"}
# Using Azure OpenAI
from openai import AsyncAzureOpenAI

from pydantic_ai import Embedder
from pydantic_ai.embeddings.openai import OpenAIEmbeddingModel
from pydantic_ai.providers.openai import OpenAIProvider

azure_client = AsyncAzureOpenAI(
    azure_endpoint='https://your-resource.openai.azure.com',
    api_version='2024-02-01',
    api_key='your-azure-key',
)
model = OpenAIEmbeddingModel(
    'text-embedding-3-small',
    provider=OpenAIProvider(openai_client=azure_client),
)
embedder = Embedder(model)


# Using any OpenAI-compatible API
model = OpenAIEmbeddingModel(
    'your-model-name',
    provider=OpenAIProvider(
        base_url='https://your-provider.com/v1',
        api_key='your-api-key',
    ),
)
embedder = Embedder(model)
```

对于拥有专用 provider classes 的 providers（例如 [`OllamaProvider`][pydantic_ai.providers.ollama.OllamaProvider] 或 [`AzureProvider`][pydantic_ai.providers.azure.AzureProvider]），你可以使用简写语法：

```python
from pydantic_ai import Embedder

embedder = Embedder('azure:text-embedding-3-small')
embedder = Embedder('ollama:nomic-embed-text')
```

完整支持 provider 列表请参阅 [OpenAI 兼容模型](models/openai.md#openai-compatible-models)。

### Google

[`GoogleEmbeddingModel`][pydantic_ai.embeddings.google.GoogleEmbeddingModel] 通过 Gemini API (Google AI Studio) 或 Google Cloud（曾称为 Vertex AI）使用 Google 的 embedding models。

#### 安装 {#google-install}

要使用 Google embedding models，你需要安装 `pydantic-ai`，或安装带 `google` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[google]"
```

#### 配置 {#google-configuration}

要通过 Gemini API 使用 `GoogleEmbeddingModel`，请前往 [aistudio.google.com](https://aistudio.google.com/) 生成 API key。拿到 API key 后，可以将其设置为环境变量：

```bash
export GOOGLE_API_KEY='your-api-key'
```

然后即可使用模型：

```python {title="google_embeddings.py"}
from pydantic_ai import Embedder

embedder = Embedder('google:gemini-embedding-001')


async def main():
    result = await embedder.embed_query('Hello world')
    print(len(result.embeddings[0]))
    #> 3072
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

可用模型请参阅 [Google Embeddings documentation](https://ai.google.dev/gemini-api/docs/embeddings)。

##### Google Cloud

要通过 Google Cloud（曾称为 Vertex AI）而不是 Gemini API 使用 Google 的 embedding models，请使用 `google-cloud:` provider prefix：

```python {title="google_cloud_embeddings.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.google import GoogleEmbeddingModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

# Using provider prefix
embedder = Embedder('google-cloud:gemini-embedding-001')

# Or with explicit provider configuration
model = GoogleEmbeddingModel(
    'gemini-embedding-001',
    provider=GoogleCloudProvider(project='my-project', location='us-central1'),
)
embedder = Embedder(model)
```

有关 Google Cloud authentication options（包括 application default credentials、service accounts 和 API keys）的更多细节，请参阅 [Google provider documentation](models/google.md#google-cloud-enterprise)。

#### 维度控制 {#google-dimension-control}

Google 的 embedding models 支持通过 `dimensions` 设置降低维度：

```python {title="google_dimensions.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings import EmbeddingSettings

embedder = Embedder(
    'google:gemini-embedding-001',
    settings=EmbeddingSettings(dimensions=768),
)


async def main():
    result = await embedder.embed_query('Hello world')
    print(len(result.embeddings[0]))
    #> 768
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

#### Google 专用设置 {#google-specific-settings}

Google models 通过 [`GoogleEmbeddingSettings`][pydantic_ai.embeddings.google.GoogleEmbeddingSettings] 支持额外设置：

```python {title="google_settings.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.google import GoogleEmbeddingSettings

embedder = Embedder(
    'google:gemini-embedding-001',
    settings=GoogleEmbeddingSettings(
        dimensions=768,
        google_task_type='SEMANTIC_SIMILARITY',  # Optimize for similarity comparison
    ),
)
```

可用 task types 请参阅 [Google 的 task type 文档](https://ai.google.dev/gemini-api/docs/embeddings#task-types)。默认情况下，`embed_query()` 使用 `RETRIEVAL_QUERY`，`embed_documents()` 使用 `RETRIEVAL_DOCUMENT`。

### Cohere

[`CohereEmbeddingModel`][pydantic_ai.embeddings.cohere.CohereEmbeddingModel] 提供对 Cohere embedding models 的访问，它们提供 multilingual support 和多种 model sizes。

#### 安装 {#cohere-install}

要使用 Cohere embedding models，你需要安装 `pydantic-ai`，或安装带 `cohere` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[cohere]"
```

#### 配置 {#cohere-configuration}

要使用 `CohereEmbeddingModel`，请前往 [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys) 并找到生成 API key 的位置。拿到 API key 后，可以将其设置为环境变量：

```bash
export CO_API_KEY='your-api-key'
```

然后即可使用模型：

```python {title="cohere_embeddings.py"}
from pydantic_ai import Embedder

embedder = Embedder('cohere:embed-v4.0')


async def main():
    result = await embedder.embed_query('Hello world')
    print(len(result.embeddings[0]))
    #> 1024
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

可用模型请参阅 [Cohere Embed 文档](https://docs.cohere.com/docs/cohere-embed)。

#### Cohere 专用设置 {#cohere-specific-settings}

Cohere models 通过 [`CohereEmbeddingSettings`][pydantic_ai.embeddings.cohere.CohereEmbeddingSettings] 支持额外设置：

```python {title="cohere_settings.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.cohere import CohereEmbeddingSettings

embedder = Embedder(
    'cohere:embed-v4.0',
    settings=CohereEmbeddingSettings(
        dimensions=512,
        cohere_truncate='END',  # Truncate long inputs instead of erroring
        cohere_max_tokens=256,  # Limit tokens per input
    ),
)
```

### VoyageAI

[`VoyageAIEmbeddingModel`][pydantic_ai.embeddings.voyageai.VoyageAIEmbeddingModel] 提供对 VoyageAI embedding models 的访问，这些模型针对 retrieval 优化，并有面向 code、finance 和 legal domains 的专门模型。

#### 安装 {#voyageai-install}

要使用 VoyageAI embedding models，你需要安装带 `voyageai` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[voyageai]"
```

#### 配置 {#voyageai-configuration}

要使用 `VoyageAIEmbeddingModel`，请前往 [dash.voyageai.com](https://dash.voyageai.com/) 生成 API key。拿到 API key 后，可以将其设置为环境变量：

```bash
export VOYAGE_API_KEY='your-api-key'
```

然后即可使用模型：

```python {title="voyageai_embeddings.py" max_py="3.13"}
from pydantic_ai import Embedder

embedder = Embedder('voyageai:voyage-3.5')


async def main():
    result = await embedder.embed_query('Hello world')
    print(len(result.embeddings[0]))
    #> 1024
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

可用模型请参阅 [VoyageAI Embeddings 文档](https://docs.voyageai.com/docs/embeddings)。

#### VoyageAI 专用设置 {#voyageai-specific-settings}

VoyageAI models 通过 [`VoyageAIEmbeddingSettings`][pydantic_ai.embeddings.voyageai.VoyageAIEmbeddingSettings] 支持额外设置：

```python {title="voyageai_settings.py" max_py="3.13"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.voyageai import VoyageAIEmbeddingSettings

embedder = Embedder(
    'voyageai:voyage-3.5',
    settings=VoyageAIEmbeddingSettings(
        dimensions=512,  # Reduce output dimensions
        voyageai_input_type='document',  # Override input type for all requests
    ),
)
```

### Bedrock

[`BedrockEmbeddingModel`][pydantic_ai.embeddings.bedrock.BedrockEmbeddingModel] 通过 AWS Bedrock 提供对 embedding models 的访问，包括 Amazon Titan、Cohere 和 Amazon Nova models。

#### 安装 {#bedrock-install}

要使用 Bedrock embedding models，你需要安装 `pydantic-ai`，或安装带 `bedrock` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[bedrock]"
```

#### 配置 {#bedrock-configuration}

AWS Bedrock authentication 使用标准 AWS credentials。有关通过 environment variables、AWS credentials file 或 IAM roles 配置 credentials 的细节，请参阅 [Bedrock provider documentation](models/bedrock.md#environment-variables)。

请确保你的 AWS account 可以访问你想使用的 Bedrock embedding models。详情请参阅 [AWS Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)。

#### 基本用法 {#basic-usage}

```python {title="bedrock_embeddings.py" test="skip"}
from pydantic_ai import Embedder

# Using Amazon Titan
embedder = Embedder('bedrock:amazon.titan-embed-text-v2:0')


async def main():
    result = await embedder.embed_query('Hello world')
    print(len(result.embeddings[0]))
    #> 1024
```

_（这个示例需要已配置 AWS credentials）_

#### 支持的模型 {#supported-models}

Bedrock 支持三类 embedding models。完整可用模型列表请参阅 [AWS Bedrock documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)。

**Amazon Titan：**

- `amazon.titan-embed-text-v1`：1536 dimensions（固定），8K tokens
- `amazon.titan-embed-text-v2:0`：256/384/1024 dimensions（可配置，默认 1024），8K tokens

**Cohere Embed：**

- `cohere.embed-english-v3`：仅英文，1024 dimensions（固定），512 tokens
- `cohere.embed-multilingual-v3`：Multilingual，1024 dimensions（固定），512 tokens
- `cohere.embed-v4:0`：256/512/1024/1536 dimensions（可配置，默认 1536），128K tokens

**Amazon Nova：**

- `amazon.nova-2-multimodal-embeddings-v1:0`：256/384/1024/3072 dimensions（可配置，默认 3072），8K tokens

#### Titan 专用设置 {#titan-specific-settings}

Titan v2 支持通过 `bedrock_titan_normalize`（默认：`True`）进行 vector normalization，以便直接计算相似度。Titan v1 不支持此设置。

```python {title="bedrock_titan.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.bedrock import BedrockEmbeddingSettings

embedder = Embedder(
    'bedrock:amazon.titan-embed-text-v2:0',
    settings=BedrockEmbeddingSettings(
        dimensions=512,
        bedrock_titan_normalize=True,
    ),
)
```

!!! note
    Titan models 不支持 `truncate` 设置。`dimensions` 设置仅受 Titan v2 支持。

#### Cohere 专用设置 {#bedrock-cohere-specific-settings}

Bedrock 上的 Cohere models 通过 [`BedrockEmbeddingSettings`][pydantic_ai.embeddings.bedrock.BedrockEmbeddingSettings] 支持额外设置：

- `bedrock_cohere_input_type`：默认情况下，`embed_query()` 使用 `'search_query'`，`embed_documents()` 使用 `'search_document'`。也接受 `'classification'` 或 `'clustering'`。
- `bedrock_cohere_truncate`：细粒度 truncation control：`'NONE'`（默认，overflow 时报错）、`'START'` 或 `'END'`。覆盖基础 `truncate` 设置。
- `bedrock_cohere_max_tokens`：限制每个 input 的 tokens（默认：128000）。仅受 Cohere v4 支持。

```python {title="bedrock_cohere.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.bedrock import BedrockEmbeddingSettings

embedder = Embedder(
    'bedrock:cohere.embed-v4:0',
    settings=BedrockEmbeddingSettings(
        dimensions=512,
        bedrock_cohere_max_tokens=1000,
        bedrock_cohere_truncate='END',
    ),
)
```

!!! note
    `dimensions` 和 `bedrock_cohere_max_tokens` 设置仅受 Cohere v4 支持。Cohere v3 models 维度固定为 1024。

#### Nova 专用设置 {#nova-specific-settings}

Bedrock 上的 Nova models 通过 [`BedrockEmbeddingSettings`][pydantic_ai.embeddings.bedrock.BedrockEmbeddingSettings] 支持额外设置：

- `bedrock_nova_truncate`：细粒度 truncation control：`'NONE'`（默认，overflow 时报错）、`'START'` 或 `'END'`。覆盖基础 `truncate` 设置。
- `bedrock_nova_embedding_purpose`：默认情况下，`embed_query()` 使用 `'GENERIC_RETRIEVAL'`，`embed_documents()` 使用 `'GENERIC_INDEX'`。也接受 `'TEXT_RETRIEVAL'`、`'CLASSIFICATION'` 或 `'CLUSTERING'`。

```python {title="bedrock_nova.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.bedrock import BedrockEmbeddingSettings

embedder = Embedder(
    'bedrock:amazon.nova-2-multimodal-embeddings-v1:0',
    settings=BedrockEmbeddingSettings(
        dimensions=1024,
        bedrock_nova_embedding_purpose='TEXT_RETRIEVAL',
        truncate=True,
    ),
)
```

#### 并发设置 {#concurrency-settings}

不支持 batch embedding 的模型（Titan 和 Nova）会为每段 input text 单独发起 API request。默认情况下，这些请求并发运行，最多 5 个 parallel requests。

你可以通过 `bedrock_max_concurrency` 设置进行调整：

```python {title="bedrock_concurrency.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.bedrock import BedrockEmbeddingSettings

# Increase concurrency for faster throughput
embedder = Embedder(
    'bedrock:amazon.titan-embed-text-v2:0',
    settings=BedrockEmbeddingSettings(bedrock_max_concurrency=10),
)

# Or reduce concurrency to avoid rate limits
embedder = Embedder(
    'bedrock:amazon.nova-2-multimodal-embeddings-v1:0',
    settings=BedrockEmbeddingSettings(bedrock_max_concurrency=2),
)
```

#### 区域前缀（跨区域推理） {#regional-prefixes-cross-region-inference}

Bedrock 支持使用 `us.`、`eu.` 或 `apac.` 等地理前缀进行跨区域推理：

```python {title="bedrock_regional.py"}
from pydantic_ai import Embedder

embedder = Embedder('bedrock:us.amazon.titan-embed-text-v2:0')
```

#### 使用 AWS Application Inference Profiles {#using-aws-application-inference-profiles}

设置 [`bedrock_inference_profile`][pydantic_ai.embeddings.bedrock.BedrockEmbeddingSettings.bedrock_inference_profile]，可以在保留 base model name 以检测 model capabilities 的同时，将 requests 路由通过 inference profile：

```python {title="bedrock_inference_profile.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.bedrock import BedrockEmbeddingModel
from pydantic_ai.providers.bedrock import BedrockProvider

provider = BedrockProvider(region_name='us-east-1')

model = BedrockEmbeddingModel(
    'amazon.titan-embed-text-v2:0',
    provider=provider,
    settings={
        'bedrock_inference_profile': 'arn:aws:bedrock:us-east-1:123456789012:application-inference-profile/my-embed-profile',
    },
)
embedder = Embedder(model)
```

#### 使用自定义 Provider {#using-a-custom-provider}

对于 explicit credentials 或自定义 boto3 client 等高级配置，你可以直接创建 [`BedrockProvider`][pydantic_ai.providers.bedrock.BedrockProvider]。更多细节请参阅 [Bedrock provider documentation](models/bedrock.md#provider-argument)。

```python {title="bedrock_provider.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.bedrock import BedrockEmbeddingModel
from pydantic_ai.providers.bedrock import BedrockProvider

provider = BedrockProvider(
    region_name='us-west-2',
    aws_access_key_id='your-access-key',
    aws_secret_access_key='your-secret-key',
)

model = BedrockEmbeddingModel('amazon.titan-embed-text-v2:0', provider=provider)
embedder = Embedder(model)
```

!!! note "Token 计数"
    Bedrock embedding models 不支持 `count_tokens()` 方法，因为 AWS Bedrock 的 token counting API 仅适用于 text generation models（Claude、Llama 等），不适用于 embedding models。调用 `count_tokens()` 会引发 `NotImplementedError`。

### Sentence Transformers（本地） {#sentence-transformers-local}

[`SentenceTransformerEmbeddingModel`][pydantic_ai.embeddings.sentence_transformers.SentenceTransformerEmbeddingModel] 使用 [sentence-transformers](https://www.sbert.net/) library 在本地运行 embeddings，让你无需任何 API calls 就能访问数千个 [Hugging Face 上的 embedding models](https://huggingface.co/models?library=sentence-transformers)。这非常适合：

- **隐私**：Data 永远不会离开你的 infrastructure
- **成本**：高容量 workloads 无 API charges
- **离线使用**：模型下载后不需要 internet connection
- **专门领域或语言**：从 [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard) 选择针对 code、multilingual、biomedical、legal 等训练的模型

#### 安装 {#sentence-transformers-install}

要使用 Sentence Transformers embedding models，你需要安装带 `sentence-transformers` 可选组的 `pydantic-ai-slim`：

```bash
pip/uv-add "pydantic-ai-slim[sentence-transformers]"
```

#### 用法 {#sentence-transformers-usage}

```python {title="sentence_transformers_embeddings.py" max_py="3.13"}
from pydantic_ai import Embedder

# Model is downloaded from Hugging Face on first use
embedder = Embedder('sentence-transformers:lightonai/DenseOn')


async def main():
    result = await embedder.embed_query('Hello world')
    print(len(result.embeddings[0]))
    #> 768
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

[`lightonai/DenseOn`](https://huggingface.co/lightonai/DenseOn) 是一个近期较强的 149M 参数 general-purpose model，它会非对称编码 queries 和 documents：[`embed_query()`][pydantic_ai.embeddings.Embedder.embed_query] 和 [`embed_documents()`][pydantic_ai.embeddings.Embedder.embed_documents] 会自动应用模型的 `query:` / `document:` prompts。更多选项请参阅 [Sentence Transformers pretrained models](https://www.sbert.net/docs/sentence_transformer/pretrained_models.html) 文档和 [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard)；另请参阅上面的[选择模型](#choosing-a-model)。

#### 设备选择 {#device-selection}

控制用于 inference 的 device：

```python {title="sentence_transformers_device.py" max_py="3.13"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings.sentence_transformers import (
    SentenceTransformersEmbeddingSettings,
)

embedder = Embedder(
    'sentence-transformers:sentence-transformers/all-MiniLM-L6-v2',
    settings=SentenceTransformersEmbeddingSettings(
        sentence_transformers_device='cuda',  # Use GPU
        sentence_transformers_normalize_embeddings=True,  # L2 normalize
    ),
)
```

#### 使用已有 Model Instance {#using-an-existing-model-instance}

如果你需要更细粒度控制 model initialization：

```python {title="sentence_transformers_instance.py" max_py="3.13"}
from sentence_transformers import SentenceTransformer

from pydantic_ai import Embedder
from pydantic_ai.embeddings.sentence_transformers import (
    SentenceTransformerEmbeddingModel,
)

# Create and configure the model yourself
st_model = SentenceTransformer('microsoft/harrier-oss-v1-270m', device='cpu')

# Wrap it for use with Pydantic AI
model = SentenceTransformerEmbeddingModel(st_model)
embedder = Embedder(model)
```

## 设置 {#settings}

[`EmbeddingSettings`][pydantic_ai.embeddings.EmbeddingSettings] 提供适用于跨 providers 的通用配置选项：

- `dimensions`：降低输出 embedding dimensions（OpenAI、Google、Cohere、Bedrock、VoyageAI 支持）
- `truncate`：当为 `True` 时，截断超出模型 context length 的 input text，而不是引发错误（Cohere、Bedrock、VoyageAI 支持）

设置可以在 embedder level 指定（应用于所有 calls），也可以按 call 指定：

```python {title="embedding_settings.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings import EmbeddingSettings

# Default settings for all calls
embedder = Embedder(
    'openai:text-embedding-3-small',
    settings=EmbeddingSettings(dimensions=512),
)


async def main():
    # Override for a specific call
    result = await embedder.embed_query(
        'Hello world',
        settings=EmbeddingSettings(dimensions=256),
    )
    print(len(result.embeddings[0]))
    #> 256
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

## Token 计数 {#token-counting}

你可以在 embedding 前检查 token counts，以避免超出 model limits：

```python {title="token_counting.py"}
from pydantic_ai import Embedder

embedder = Embedder('openai:text-embedding-3-small')


async def main():
    text = 'Hello world, this is a test.'

    # Count tokens in text
    token_count = await embedder.count_tokens(text)
    print(f'Tokens: {token_count}')
    #> Tokens: 7

    # Check model's maximum input tokens (returns None if unknown)
    max_tokens = await embedder.max_input_tokens()
    print(f'Max tokens: {max_tokens}')
    #> Max tokens: 1024
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

## 测试 {#testing}

使用 [`TestEmbeddingModel`][pydantic_ai.embeddings.TestEmbeddingModel] 进行测试，无需发起 API calls：

```python {title="testing_embeddings.py"}
from pydantic_ai import Embedder
from pydantic_ai.embeddings import TestEmbeddingModel


async def test_my_rag_system():
    embedder = Embedder('openai:text-embedding-3-small')
    test_model = TestEmbeddingModel()

    with embedder.override(model=test_model):
        result = await embedder.embed_query('test query')

        # TestEmbeddingModel returns deterministic embeddings
        assert result.embeddings[0] == [1.0] * 8

        # Check what settings were used
        assert test_model.last_settings is not None
```

## 插桩 {#instrumentation}

启用 OpenTelemetry instrumentation 以便调试和监控：

```python {title="instrumented_embeddings.py"}
import logfire

from pydantic_ai import Embedder

logfire.configure()

# Instrument a specific embedder
embedder = Embedder('openai:text-embedding-3-small', instrument=True)

# Or instrument all embedders globally
Embedder.instrument_all()
```

有关在 Pydantic AI 中使用 Logfire 的更多细节，请参阅[调试和监控指南](logfire.md)。

## 使用 rerankers 进行两阶段 retrieval {#two-stage-retrieval-with-rerankers}

对于高质量 retrieval，一种常见模式是**两阶段**：先使用 embedding model 低成本拉取较宽的候选 shortlist，然后使用 **cross-encoder reranker** 更精确地对每个 candidate 与 query 进行评分。Cross-encoder 会一起读取 query 和 document，因此比 embedding lookup 更慢，但准确得多，非常适合把 top-100 recall list 缩小为实际交给 LLM 的 top-5 results。

Pydantic AI 不内置 reranker provider class，因此你需要自带。最常见的本地选项是来自 `sentence-transformers` 的 `CrossEncoder`：

```python {title="rerank.py" max_py="3.13"}
import asyncio
from functools import cache

from sentence_transformers import CrossEncoder


@cache
def get_reranker() -> CrossEncoder:
    # Loaded lazily on first call, then reused.
    return CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')


async def rerank(query: str, candidates: list[str], top_k: int = 3) -> list[str]:
    """Rerank retrieval candidates by relevance to `query`."""
    reranker = get_reranker()
    # CrossEncoder.rank is blocking, so run it off the event loop.
    ranked = await asyncio.to_thread(
        reranker.rank, query, candidates, top_k=top_k, return_documents=True
    )
    return [item['text'] for item in ranked]
```

在把结果交给 LLM 前，对 vector search 返回的 candidates 调用 `rerank()`（例如在 [RAG example](examples/rag.md) 的 `retrieve` tool 中）。

!!! tip "托管 reranker 替代方案"
    如果你不想本地运行 reranker，多个 providers 提供 hosted rerankers，包括 [Cohere Rerank](https://docs.cohere.com/docs/rerank-overview)、[VoyageAI Rerank](https://docs.voyageai.com/docs/reranker) 和 [Jina Rerank](https://jina.ai/reranker)。请从与上面 `rerank()` 形状相同的 helper function 中调用它们的 HTTP clients 或 SDKs。

## 构建自定义 Embedding Models {#building-custom-embedding-models}

要集成自定义 embedding provider，请继承 [`EmbeddingModel`][pydantic_ai.embeddings.EmbeddingModel]：

```python {title="custom_embedding_model.py"}
from collections.abc import Sequence

from pydantic_ai.embeddings import EmbeddingModel, EmbeddingResult, EmbeddingSettings
from pydantic_ai.embeddings.result import EmbedInputType


class MyCustomEmbeddingModel(EmbeddingModel):
    @property
    def model_name(self) -> str:
        return 'my-custom-model'

    @property
    def system(self) -> str:
        return 'my-provider'

    async def embed(
        self,
        inputs: str | Sequence[str],
        *,
        input_type: EmbedInputType,
        settings: EmbeddingSettings | None = None,
    ) -> EmbeddingResult:
        inputs, settings = self.prepare_embed(inputs, settings)

        # Call your embedding API here
        embeddings = [[0.1, 0.2, 0.3] for _ in inputs]  # Placeholder

        return EmbeddingResult(
            embeddings=embeddings,
            inputs=inputs,
            input_type=input_type,
            model_name=self.model_name,
            provider_name=self.system,
        )
```

如果你想包装现有 model 以添加 caching 或 logging 等自定义行为，请使用 [`WrapperEmbeddingModel`][pydantic_ai.embeddings.WrapperEmbeddingModel]。
