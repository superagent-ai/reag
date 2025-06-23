# 🎓 ReAG Python SDK

## Installation
1. Ensure Python 3.9+ is installed.
2. Install using pip or poetry:
   ```bash
   pip install reag
   # or
   poetry add reag
   ```

## Quick Start
```python
from reag.client import ReagClient, Document

async with ReagClient(
      model="ollama/deepseek-r1:7b",
      model_kwargs={"api_base": "http://localhost:11434"}
   ) as client:
        docs = [
            Document(
                name="Superagent",
                content="Superagent is a workspace for AI-agents that learn, perform work, and collaborate.",
                metadata={
                    "url": "https://superagent.sh",
                    "source": "web",
                },
            ),
        ]
        response = await client.query("What is Superagent?", documents=docs)

```

## API Reference

### Initialization
Initialize the client by providing required configuration options:

```typescript
client = new ReagClient(
  model: "gpt-4.1-nano", // LiteLLM model name
  filtration_model: "minimax", // Filtration model name
  system: Optional[str] // Optional system prompt
  batchSize: Optional[Number] // Optional batch size
  schema: Optional[BaseModel] // Optional Pydantic schema
);
```

### Document Structure
Documents should follow this structure:
```python
document = Document(
    name="Superagent",
    content="Superagent is a workspace for AI-agents that learn, perform work, and collaborate.",
    metadata={
        "url": "https://superagent.sh",
        "source": "web",
    },
)
```

### Querying
Query documents with optional filters:

```python
docs = [
    Document(
        name="Superagent",
        content="Superagent is a workspace for AI-agents that learn, perform work, and collaborate.",
        metadata={
            "url": "https://superagent.sh",
            "source": "web",
            "id": "sa-1",
        },
    ),
    Document(
        name="Superagent",
        content="Superagent is a workspace for AI-agents that learn, perform work, and collaborate.",
        metadata={
            "url": "https://superagent.sh",
            "source": "web",
            "id": "sa-2",
        },
    ),
]
options = {"filter": [{"key": "id", "value": "sa-1", "operator": "equals"}]}
response = await client.query(
    "What is Superagent?", documents=docs, options=options
)
```

Response structure:
```python
content: str
reasoning: str
is_irrelevant: bool
document: Document
```

Example filters:
- Filter by metadata field:
  ```python
  options = {"filter": [{"key": "id", "value": "sa-1", "operator": "equals"}]}
  ```
- Filter by numeric values:
  ```python
  options = {
    "filter": [{"key": "version", "value": 2, "operator": "greaterThanOrEqual"}]
  }
  ```

## Contributing

We welcome contributions from the community. Please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on reporting issues, suggesting improvements, and submitting pull requests.

## License

This project is licensed under the [MIT License](LICENSE).

## Additional Resources
- [ReAG Blog Post](https://www.superagent.sh/blog/reag-reasoning-augmented-generation) - A deep dive into ReAG.

## Contact

For support or inquiries, please contact:
- [Create Issue](https://github.com/superagent-ai/reag/issues)
- X: [@superagent_ai](https://x.com/superagent_ai)
