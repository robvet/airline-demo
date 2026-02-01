Yes - several approaches depending on what you're evaluating:

Yes - several approaches depending on what you're evaluating:

LLM Output Quality

Promptfoo - Open source, test prompts against expected outputs, regression testing
Ragas - RAG-specific evaluation (faithfulness, relevance, context recall)
DeepEval - Unit testing for LLMs with metrics like hallucination, toxicity
Azure AI Evaluation SDK - Integrated with Azure AI Studio

Agent/Orchestration Evaluation

LangSmith - Trace agent runs, compare outputs, human feedback loops
Braintrust - Experiment tracking, A/B test prompts
Weights & Biases (W&B) - ML experiment tracking extended to LLMs

Key Metrics for Agentic Systems

Task completion rate
Tool call accuracy (right tool, right args)
Handoff precision (routed to correct agent)
Guardrail effectiveness (blocked bad inputs)
Latency per turn
Token efficiency

For your workshop, the most relevant would be:

Promptfoo - Test prompt changes don't regress behavior
Azure AI Evaluation - Since you're on Azure OpenAI already
Custom assertions - Validate tool calls match expected patterns
