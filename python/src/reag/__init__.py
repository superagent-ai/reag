import os
from typing import Optional

try:
    import agentops
    AGENTOPS_AVAILABLE = True
except ImportError:
    AGENTOPS_AVAILABLE = False

from .client import ReagClient, Document, QueryResult, MetadataFilter
from .schema import ResponseSchema, ResponseSchemaMessage

__version__ = "0.0.6"
__all__ = ["ReagClient", "Document", "QueryResult", "MetadataFilter", "ResponseSchema", "ResponseSchemaMessage", "init_agentops"]

def init_agentops(
    api_key: Optional[str] = None,
    tags: Optional[list] = None,
    trace_name: Optional[str] = None,
    auto_start_session: bool = True
):
    """
    Initialize AgentOps for monitoring and tracing.
    
    Args:
        api_key: AgentOps API key. If not provided, will look for AGENTOPS_API_KEY environment variable.
        tags: List of tags to apply to traces.
        trace_name: Name for the trace.
        auto_start_session: Whether to automatically start a session.
    """
    if not AGENTOPS_AVAILABLE:
        raise ImportError("AgentOps is not installed. Install it with: pip install agentops")
    
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv("AGENTOPS_API_KEY")
    
    if api_key is None:
        raise ValueError("AgentOps API key is required. Pass it as a parameter or set AGENTOPS_API_KEY environment variable.")
    
    # Initialize AgentOps
    agentops.init(
        api_key=api_key,
        tags=tags or ["reag"],
        trace_name=trace_name or "ReAG Workflow",
        auto_start_session=auto_start_session
    )