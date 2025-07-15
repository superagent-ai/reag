import httpx
import asyncio
import json
import re
from typing import List, Optional, TypeVar, Dict, Union
from pydantic import BaseModel
try:
    import agentops
    _AGENTOPS_AVAILABLE = True
except ImportError:
    _AGENTOPS_AVAILABLE = False
from litellm import acompletion

from reag.prompt import REAG_SYSTEM_PROMPT
from reag.schema import ResponseSchemaMessage


class Document(BaseModel):
    name: str
    content: str
    metadata: Optional[Dict[str, Union[str, int]]] = None


class MetadataFilter(BaseModel):
    key: str
    value: Union[str, int]
    operator: Optional[str] = None


T = TypeVar("T")


class QueryResult(BaseModel):
    content: str
    reasoning: str
    is_irrelevant: bool
    document: Document


DEFAULT_BATCH_SIZE = 20


class ReagClient:
    """
    ReAG (Reasoning Augmented Generation) client for querying documents.
    
    AgentOps Integration:
    To enable AgentOps monitoring, provide your AgentOps API key:
    
    client = ReagClient(
        agentops_api_key="your-api-key-here",
        agentops_tags=["reag", "production"],
        agentops_auto_start_session=True
    )
    """
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        system: str = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        schema: Optional[BaseModel] = None,
        model_kwargs: Optional[Dict] = None,
        agentops_api_key: Optional[str] = None,
        agentops_tags: Optional[List[str]] = None,
        agentops_auto_start_session: bool = True,
    ):
        self.model = model
        self.system = system or REAG_SYSTEM_PROMPT
        self.batch_size = batch_size
        self.schema = schema or ResponseSchemaMessage
        self.model_kwargs = model_kwargs or {}
        self._http_client = None
        
        if _AGENTOPS_AVAILABLE and agentops_api_key:
            agentops.init(
                api_key=agentops_api_key,
                tags=agentops_tags or ["reag"],
                auto_start_session=agentops_auto_start_session,
            )

    async def __aenter__(self):
        self._http_client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http_client:
            await self._http_client.aclose()

    def _filter_documents_by_metadata(
        self, documents: List[Document], filters: Optional[List[MetadataFilter]] = None
    ) -> List[Document]:
        if not filters:
            return documents

        filtered_docs = []
        for doc in documents:
            matches_all_filters = True

            for filter_item in filters:
                metadata_value = (
                    doc.metadata.get(filter_item.key) if doc.metadata else None
                )
                if metadata_value is None:
                    matches_all_filters = False
                    break

                if isinstance(metadata_value, str) and isinstance(
                    filter_item.value, str
                ):
                    if filter_item.operator == "contains":
                        if not filter_item.value in metadata_value:
                            matches_all_filters = False
                            break
                    elif filter_item.operator == "startsWith":
                        if not metadata_value.startswith(filter_item.value):
                            matches_all_filters = False
                            break
                    elif filter_item.operator == "endsWith":
                        if not metadata_value.endswith(filter_item.value):
                            matches_all_filters = False
                            break
                    elif filter_item.operator == "regex":
                        import re

                        if not re.match(filter_item.value, metadata_value):
                            matches_all_filters = False
                            break

                if filter_item.operator == "equals":
                    if metadata_value != filter_item.value:
                        matches_all_filters = False
                        break
                elif filter_item.operator == "notEquals":
                    if metadata_value == filter_item.value:
                        matches_all_filters = False
                        break
                elif filter_item.operator == "greaterThan":
                    if not metadata_value > filter_item.value:
                        matches_all_filters = False
                        break
                elif filter_item.operator == "lessThan":
                    if not metadata_value < filter_item.value:
                        matches_all_filters = False
                        break
                elif filter_item.operator == "greaterThanOrEqual":
                    if not metadata_value >= filter_item.value:
                        matches_all_filters = False
                        break
                elif filter_item.operator == "lessThanOrEqual":
                    if not metadata_value <= filter_item.value:
                        matches_all_filters = False
                        break

            if matches_all_filters:
                filtered_docs.append(doc)

        return filtered_docs

    def _extract_think_content(self, text: str) -> tuple[str, str, bool]:
        """Extract content from think tags and parse the bulleted response format."""
        # Extract think content
        think_match = re.search(r'<think>(.*?)</think>', text, flags=re.DOTALL)
        reasoning = think_match.group(1).strip() if think_match else ""
        
        # Remove think tags and get remaining text
        remaining_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        
        # Initialize default values
        content = ""
        is_irrelevant = True
        
        # Extract is_irrelevant value
        irrelevant_match = re.search(r'\*\*isIrrelevant:\*\*\s*(true|false)', remaining_text, re.IGNORECASE)
        if irrelevant_match:
            is_irrelevant = irrelevant_match.group(1).lower() == 'true'
        
        # Extract content value
        content_match = re.search(r'\*\*Answer:\*\*\s*(.*?)(?:\n|$)', remaining_text, re.DOTALL)
        if content_match:
            content = content_match.group(1).strip()
        
        return content, reasoning, is_irrelevant

    async def query(
        self, prompt: str, documents: List[Document], options: Optional[Dict] = None
    ) -> List[QueryResult]:
        try:
            # Convert dictionary filters to MetadataFilter objects
            filters = None
            if options and "filter" in options:
                raw_filters = options["filter"]
                if isinstance(raw_filters, list):
                    filters = [
                        MetadataFilter(**f) if isinstance(f, dict) else f
                        for f in raw_filters
                    ]
                elif isinstance(raw_filters, dict):
                    filters = [MetadataFilter(**raw_filters)]

            filtered_documents = self._filter_documents_by_metadata(documents, filters)

            def format_doc(doc: Document) -> str:
                return f"Name: {doc.name}\nMetadata: {doc.metadata}\nContent: {doc.content}"

            batch_size = self.batch_size
            batches = [
                filtered_documents[i : i + batch_size]
                for i in range(0, len(filtered_documents), batch_size)
            ]

            results = []
            for batch in batches:
                tasks = []
                # Create tasks for parallel processing within the batch
                for document in batch:
                    system = f"{self.system}\n\n# Available source\n\n{format_doc(document)}"
                    tasks.append(
                        acompletion(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system},
                                {"role": "user", "content": prompt},
                            ],
                            response_format=self.schema,
                            **self.model_kwargs,
                        )
                    )

                # Process all documents in the batch concurrently
                batch_responses = await asyncio.gather(*tasks)

                # Process the responses
                for document, response in zip(batch, batch_responses):
                    message_content = response.choices[0].message.content

                    try:
                        if self.model.startswith("ollama/"):
                            content, reasoning, is_irrelevant = self._extract_think_content(message_content)
                            results.append(
                                QueryResult(
                                    content=content,
                                    reasoning=reasoning,
                                    is_irrelevant=is_irrelevant,
                                    document=document,
                                )
                            )
                        else:
                            # Ensure it's parsed as a dict
                            data = (
                                json.loads(message_content)
                                if isinstance(message_content, str)
                                else message_content
                            )

                            if data["source"].get("is_irrelevant", True):
                                continue

                            results.append(
                                QueryResult(
                                    content=data["source"].get("content", ""),
                                    reasoning=data["source"].get("reasoning", ""),
                                    is_irrelevant=data["source"].get("is_irrelevant", False),
                                    document=document,
                                )
                            )
                    except json.JSONDecodeError:
                        print("Error: Could not parse response:", message_content)
                        continue

            return results

        except Exception as e:
            raise Exception(f"Query failed: {str(e)}")
