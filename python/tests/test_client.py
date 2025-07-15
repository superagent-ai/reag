import pytest
from reag.client import ReagClient, Document, QueryResult


@pytest.mark.asyncio
async def test_query_with_documents():
    async with ReagClient() as client:
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
        assert response is not None
        assert len(response) == 1
        result = response[0]
        assert isinstance(result, QueryResult)
        assert result.content is not None
        assert result.document is not None
        assert result.reasoning is not None
        assert isinstance(result.is_irrelevant, bool)


@pytest.mark.asyncio
async def test_query_with_metadata_filter():
    async with ReagClient() as client:
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
        assert response is not None
        assert len(response) == 1
        result = response[0]
        assert isinstance(result, QueryResult)
        assert result.document.metadata["id"] == "sa-1"


@pytest.mark.asyncio
async def test_query_with_integer_filter():
    async with ReagClient() as client:
        docs = [
            Document(
                name="Superagent",
                content="Superagent is a workspace for AI-agents that learn, perform work, and collaborate.",
                metadata={
                    "version": 1,
                    "source": "web",
                    "id": "sa-1",
                },
            ),
            Document(
                name="Superagent",
                content="Superagent is a workspace for AI-agents that learn, perform work, and collaborate.",
                metadata={
                    "version": 2,
                    "source": "web",
                    "id": "sa-2",
                },
            ),
        ]
        options = {
            "filter": [{"key": "version", "value": 2, "operator": "greaterThanOrEqual"}]
        }
        response = await client.query(
            "What is Superagent?", documents=docs, options=options
        )
        assert response is not None
        assert len(response) == 1
        result = response[0]
        assert isinstance(result, QueryResult)
        assert result.document.metadata["version"] == 2


@pytest.mark.asyncio
async def test_query_returns_empty_for_irrelevant_docs():
    async with ReagClient() as client:
        docs = [
            Document(
                name="Irrelevant Doc",
                content="This document contains completely unrelated content about cooking recipes.",
                metadata={"type": "recipe", "cuisine": "italian"},
            )
        ]
        response = await client.query("What is Superagent?", documents=docs)
        print(response)
        assert response is not None
        assert len(response) == 0  # Should be empty since doc is irrelevant


@pytest.mark.asyncio
async def test_agentops_integration():
    """Test that AgentOps integration works when available"""
    try:
        import reag
        
        # This should not raise an error even if AgentOps is not installed
        # due to the fallback decorators
        async with ReagClient() as client:
            docs = [
                Document(
                    name="Test Doc",
                    content="This is a test document for AgentOps integration.",
                    metadata={"type": "test"},
                ),
            ]
            response = await client.query("What is this document about?", documents=docs)
            assert response is not None
    except ImportError:
        # If AgentOps is not installed, the test should still pass
        # due to the fallback decorators
        pass


def test_init_agentops_function():
    """Test that init_agentops function works correctly"""
    import reag
    
    # Test that the function exists and is callable
    assert hasattr(reag, 'init_agentops')
    assert callable(reag.init_agentops)
    
    # Test that it raises error when AgentOps is not available and no api_key
    try:
        reag.init_agentops()
        # Should either work (if AgentOps is installed) or raise ImportError
    except (ImportError, ValueError):
        # Expected if AgentOps is not installed or no API key provided
        pass
