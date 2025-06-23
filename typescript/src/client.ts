import {
  generateText,
  LanguageModel,
  GenerateObjectResult,
  generateObject,
} from "ai";
import { z } from "zod";

import { REAG_SYSTEM_PROMPT } from "./prompt";
import { RESPONSE_SCHEMA } from "./schema";

export interface ClientOptions {
  /**
   * The language model instance to use for queries.
   * This should be an instance of a model that implements the Vercel AI SDK's LanguageModel interface.
   * See: https://sdk.vercel.ai/docs/foundations/providers-and-models
   */
  model: LanguageModel;
  /**
   * The filtration model instance to use for document filtration.
   * This should be an instance of a model that implements the Vercel AI SDK's LanguageModel interface.
   */
  filtrationModel: LanguageModel;
  /**
   * The system prompt that provides context and instructions to the model.
   * This string sets the behavior and capabilities of the model for all queries.
   */
  system: string;
  /**
   * The size of the batch to process documents in.
   * This is used to limit the number of documents processed at once.
   */
  batchSize?: number;
  /**
   * The schema to use for the response.
   */
  schema?: z.ZodSchema;
}

export interface Document {
  name: string;
  content: string;
  metadata?: Record<string, string | number>;
}

export interface QueryResult<T> {
  results: {
    relevant: T[];
    irrelevant?: boolean;
  };
  document: Document;
}

export interface MetadataFilter {
  key: string;
  value: string | number;
  operator?:
    | "equals"
    | "contains"
    | "startsWith"
    | "endsWith"
    | "notEquals"
    | "greaterThan"
    | "lessThan"
    | "greaterThanOrEqual"
    | "lessThanOrEqual"
    | "regex";
}

const DEFAULT_BATCH_SIZE = 20;

/**
 * The Client class that wraps a language model and exposes query methods.
 */
export class ReagClient {
  private readonly model: LanguageModel;
  private readonly filtrationModel: LanguageModel;
  private readonly system: string;
  private readonly batchSize: number;
  private readonly schema: z.ZodSchema;

  /**
   * Constructs a new Client instance.
   * @param options Configuration options for the Client.
   */
  constructor(options: ClientOptions) {
    this.model = options.model;
    this.filtrationModel = options.filtrationModel;
    this.system = options.system || REAG_SYSTEM_PROMPT;
    this.batchSize = options.batchSize || DEFAULT_BATCH_SIZE;
    this.schema = options.schema || RESPONSE_SCHEMA;
  }

  /**
   * Filters documents based on metadata criteria
   */
  private filterDocumentsByMetadata(
    documents: Document[],
    filter?: MetadataFilter[]
  ): Document[] {
    if (!filter?.length) return documents;

    return documents.filter((doc) => {
      return filter.every((filter) => {
        const metadataValue = doc.metadata?.[filter.key];
        if (!metadataValue) return false;

        // Handle string operations only if both values are strings
        if (
          typeof metadataValue === "string" &&
          typeof filter.value === "string"
        ) {
          switch (filter.operator) {
            case "contains":
              return metadataValue.includes(filter.value);
            case "startsWith":
              return metadataValue.startsWith(filter.value);
            case "endsWith":
              return metadataValue.endsWith(filter.value);
            case "regex":
              return new RegExp(filter.value).test(metadataValue);
          }
        }

        // Handle numeric comparisons and equality checks
        switch (filter.operator) {
          case "equals":
            return metadataValue === filter.value;
          case "notEquals":
            return metadataValue !== filter.value;
          case "greaterThan":
            return metadataValue > filter.value;
          case "lessThan":
            return metadataValue < filter.value;
          case "greaterThanOrEqual":
            return metadataValue >= filter.value;
          case "lessThanOrEqual":
            return metadataValue <= filter.value;
          default:
            return metadataValue === filter.value;
        }
      });
    });
  }

  /**
   * Executes a query on the assigned language model with document batching
   */
  async query<T extends z.ZodType>(
    prompt: string,
    documents: Document[],
    options?: {
      filter?: MetadataFilter[];
    }
  ): Promise<QueryResult<z.infer<T>>[]> {
    try {
      const filteredDocuments = this.filterDocumentsByMetadata(
        documents,
        options?.filter
      );

      const formatDoc = (doc: Document) =>
        `Name: ${doc.name}\nMetadata: ${JSON.stringify(
          doc.metadata
        )}\nContent: ${doc.content}`;

      const batches = Array.from(
        { length: Math.ceil(filteredDocuments.length / this.batchSize) },
        (_, i) =>
          filteredDocuments.slice(i * this.batchSize, (i + 1) * this.batchSize)
      );

      const batchResults = await Promise.all(
        batches.map(async (batch) => {
          // Process each document in the batch individually
          const batchResponses = await Promise.all(
            batch.map(async (document) => {
              const system = `${
                this.system
              }\n\n# Available source\n\n${formatDoc(document)}`;

              // Use the filtration model for document filtration
              const filtrationResponse = await generateObject({
                model: this.filtrationModel,
                system,
                prompt,
                schema: this.schema,
              });

              const filtrationData = filtrationResponse.object;

              if (filtrationData.isIrrelevant) {
                return null;
              }

              // Use the reasoning model for generating the final answer
              const reasoningResponse = await generateObject({
                model: this.model,
                system,
                prompt,
                schema: this.schema,
              });

              return {
                response: reasoningResponse,
                document,
              };
            })
          );

          return batchResponses.filter((response) => response !== null);
        })
      );

      const results = batchResults.flat().map(({ response, document }) => ({
        ...response.object,
        document,
      }));

      return results;
    } catch (error) {
      throw new Error(`Query failed: ${error}`);
    }
  }
}
