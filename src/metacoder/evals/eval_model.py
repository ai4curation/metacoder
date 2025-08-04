from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field
from metacoder.configuration import AIModelConfig, MCPConfig
from deepeval.metrics import base_metric
from deepeval.test_case import LLMTestCase

class EvalCase(BaseModel):
    """
    A single evaluation test case.

    Defines an individual test scenario with input, expected output, and evaluation criteria.
    Each case is run through all specified metrics to produce scored results.
    
    Example:
        ```yaml
        name: "title_extraction"
        metrics: [CorrectnessMetric]
        input: "What is the title of PMID:12345?"
        expected_output: "Example Paper Title"
        threshold: 0.9
        ```
    """
    name: str = Field(..., description="Unique identifier for the test case")
    metrics: List[str] = Field(..., description="List of metric names to apply (e.g., CorrectnessMetric, FaithfulnessMetric)")
    input: str = Field(..., description="The prompt or question to send to the AI coder")
    expected_output: Optional[str] = Field(default=None, description="Expected response for comparison-based metrics")
    retrieval_context: Optional[str | List[str]] = Field(default=None, description="Context documents for RAG-based metrics")
    threshold: float = Field(default=0.7, description="Score threshold for passing (0.0-1.0)")
    context: Optional[List[str]] = Field(default=None, description="Additional context for the evaluation")
    additional_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Extra metadata for custom metrics")
    comments: Optional[str] = Field(default=None, description="Human-readable notes about the test case")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorization and filtering")

class EvalDataset(BaseModel):
    """
    Complete evaluation dataset configuration.
    
    Defines the full evaluation suite including models, coders, test cases, and optional MCP servers.
    The evaluation runner will execute all combinations of model × coder × case × metric.
    
    Example:
        ```yaml
        name: "pubmed_evaluation"
        description: "Test PubMed MCP integration"
        models:
          gpt-4o:
            provider: openai
            name: gpt-4
        coders:
          claude: {}
        servers:
          pubmed:
            name: pubmed
            command: uvx
            args: [mcp-simple-pubmed]
        cases:
          - name: "test1"
            metrics: [CorrectnessMetric]
            input: "What is 1+1?"
            expected_output: "2"
        ```
    """
    name: str = Field(..., description="Name of the evaluation dataset")
    description: str | None = Field(None, description="Description of what this evaluation tests")
    coders: dict[str, dict[str, Any]] | None = Field(None, description="Coders to test with optional configuration (defaults to all available)")
    models: Dict[str, AIModelConfig] = Field(..., description="AI models to use for evaluation")
    servers: Dict[str, MCPConfig] = Field({}, description="MCP servers available for test cases")
    server_combinations: List[List[str]] | None = Field(None, description="Server combinations to evaluate (None = test each individually)")
    cases: List[EvalCase] = Field(..., description="List of test cases to run")

