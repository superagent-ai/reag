# 🎓 ReAG TypeScript SDK

## Installation
1. Ensure Node.js (14+) is installed.
2. Install using npm:
   ```bash
   npm install @superagent-ai/reag
   npm install @ai-sdk/openai
   ```
3. Or using Yarn:
   ```bash
   yarn add @superagent-ai/reag
   yarn add @ai-sdk/openai
   ```

## Quick Start
```typescript
import { ReagClient, ClientOptions } from '@superagent-ai/reag';
import { openai } from "@ai-sdk/openai";

// Initialize the SDK with required options
const client = new ReagClient({
  model: openai("o3-mini", { structuredOutputs: true }),
  filtrationModel: openai("minimax", { structuredOutputs: true }),
  // system: optional system prompt here or use the default
});

// Example document with metadata
const document = {
  name: "Getting Started",
  content: "ReAG SDK is a framework for Reasoning Augmented Generation...",
  metadata: {
    url: "https://docs.example.com/getting-started",
    source: "documentation",
    id: "doc-1"
  }
};

// Query with document context and filters
const response = await client.query(
  "Describe the main features of the SDK",
  [document],
  {
    filter: [
      {
        key: "source",
        value: "documentation",
        operator: "equals"
      }
    ]
  }
);

// Response includes: content, reasoning, isIrrelevant, and document reference
console.log('Query Response:', response);
```

## API Reference

### Initialization
Initialize the client by providing required configuration options:

```typescript
const client = new ReagClient({
  model: openai("o3-mini", { structuredOutputs: true }),
  filtrationModel: openai("minimax", { structuredOutputs: true }),
  system?: string // Optional system prompt
  batchSize?: number // Optional batch size
  schema?: z.ZodSchema // Optional schema
});
```

### Document Structure
Documents should follow this structure:
```typescript
interface Document {
  name: string;
  content: string;
  metadata: {
    [key: string]: any;  // Custom metadata fields
  }
}
```

### Querying
Query documents with optional filters:

```typescript
const response = await client.query(
  query: string,
  documents: Document[],
  options?: {
    filter?: Array<{
      key: string;
      value: string | number;
      operator: "equals" | "greaterThanOrEqual" // and other operators
    }>
  }
);
```

Response structure:
```typescript
interface QueryResponse {
  content: string;      // Generated response
  reasoning: string;    // Reasoning behind the response
  isIrrelevant: boolean; // Relevance indicator
  document: Document;   // Reference to source document
}
```

Example filters:
- Filter by metadata field:
  ```typescript
  {
    filter: [
      {
        key: "source",
        value: "documentation",
        operator: "equals"
      }
    ]
  }
  ```
- Filter by numeric values:
  ```typescript
  {
    filter: [
      {
        key: "version",
        value: 2,
        operator: "greaterThanOrEqual"
      }
    ]
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
