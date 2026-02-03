# NovaBot Simulator

Automated testing agent that simulates user conversations to test NovaBot with realistic questions and adversarial attacks.

## Overview

NovaBot Simulator runs automated test sessions against NovaBot to:
- Test normal user interactions (greetings, product questions, follow-ups)
- Test adversarial scenarios (security probing, system prompt extraction, confusion attacks)
- Measure performance metrics (latency, RAG usage, error rates)
- Validate response quality and security

## Features

- **Realistic Question Generation**: Questions are curated from actual Noveum documentation topics
- **80/20 Split**: 80% normal questions, 20% adversarial questions
- **Parallel Execution**: Runs multiple sessions concurrently for faster testing
- **Comprehensive Metrics**: Tracks latency, RAG usage, errors, and more
- **JSON Output**: Saves complete conversation logs and metrics to JSON file
- **Session-Based**: Each session maintains conversation context

## Quick Start

### Basic Usage

```bash
# Run with default settings (10 sessions, 10 messages each)
python -m src.agents.business.nova_bot_simulator.main

# Or from the simulator directory
cd src/agents/business/nova_bot_simulator
python main.py
```

### Configuration via Environment Variables

```bash
# Number of sessions to simulate
export SIMULATOR_NUM_SESSIONS=10

# Messages per session
export SIMULATOR_MESSAGES_PER_SESSION=10

# Ratio of adversarial questions (0.0-1.0)
export SIMULATOR_ADVERSARIAL_RATIO=0.2

# Output file path
export SIMULATOR_OUTPUT_FILE=./results.json

# Enable/disable parallel execution
export SIMULATOR_PARALLEL=true

# Paths to documentation data
export SIMULATOR_METADATA_JSON_PATH=./NoveumDocsData/index/metadata.json
export SIMULATOR_DOCS_JSON_PATH=./NoveumDocsData/processed/docs.json
```

### NovaBot Configuration

The simulator uses the same environment variables as NovaBot:

```bash
# LLM Provider (required)
export OPENAI_API_KEY=your_key
# OR
export GEMINI_API_KEY=your_key

# Embeddings (required for RAG)
export OPENAI_API_KEY=your_key

# Noveum Tracing (optional)
export NOVEUM_API_KEY=your_key
export NOVEUM_PROJECT=novabot
export NOVEUM_ENVIRONMENT=development
```

## Question Types

### Normal Questions (80%)

Generated from actual Noveum documentation topics:

- **Greetings**: "Hi", "Hello", "Good morning"
- **Product Overview**: "What is Noveum?", "What does Noveum do?"
- **Core Concepts**: Traces, Spans, Attributes, Events
- **SDK Integration**: Python SDK setup and examples
- **Dashboard**: Features and usage
- **Evaluation**: NovaEval and scoring
- **Getting Started**: Quick setup guides
- **Integration Examples**: LangChain, LangGraph
- **Follow-ups**: Natural conversation flow

### Adversarial Questions (20%)

Designed to test security and robustness:

- **System Prompt Extraction**: Attempts to reveal instructions
- **Security Probing**: API key extraction, config access
- **Confusion Attacks**: Instruction manipulation attempts
- **Rude/Aggressive**: Hostile user behavior
- **Implementation Probing**: Code and architecture questions
- **Edge Cases**: Empty strings, very long inputs, special characters

## Output

### Console Output

Real-time progress and summary statistics:

```
🤖 NovaBotSimulator initialized
   Normal questions: 150
   Adversarial questions: 50
   Sessions: 10, Messages per session: 10

🚀 Starting simulation...
   Sessions: 10
   Messages per session: 10
   Adversarial ratio: 20.0%
   Parallel execution: True

⏳ Running sessions in parallel...

============================================================
📊 SIMULATION SUMMARY
============================================================
Total Sessions: 10
Total Interactions: 100
Average Latency: 1250.50 ms
RAG Usage Rate: 65.0%
Adversarial Questions: 20.0%
Error Rate: 0.0%
============================================================
```

### JSON Output

Complete results saved to `nova_bot_simulator_results.json`:

```json
{
  "config": {
    "num_sessions": 10,
    "messages_per_session": 10,
    "adversarial_ratio": 0.2,
    "parallel": true
  },
  "sessions": [
    {
      "session_id": "sim_session_001",
      "interactions": [...],
      "total_messages": 10,
      "avg_latency_ms": 1200.5,
      "rag_usage_count": 7,
      "adversarial_count": 0,
      "error_count": 0
    }
  ],
  "total_interactions": 100,
  "avg_latency_ms": 1250.5,
  "rag_usage_rate": 0.65,
  "adversarial_rate": 0.2,
  "error_rate": 0.0,
  "timestamp": "2024-01-15 10:30:00"
}
```

## Metrics

The simulator tracks:

- **Latency**: Response time per interaction and averages
- **RAG Usage**: Whether retrieval was triggered and chunks retrieved
- **Error Rate**: Exceptions and failures
- **Question Distribution**: Normal vs adversarial breakdown
- **Session-Level Stats**: Per-session metrics

## Integration with Noveum Tracing

Each `agent.chat()` call automatically creates a Noveum trace (if configured). The simulator doesn't need to manage tracing directly - it's handled by NovaBot's internal tracing.

## Requirements

- Python 3.8+
- Same dependencies as NovaBot (LangChain, OpenAI/Gemini SDKs)
- Access to Noveum documentation data (`NoveumDocsData/`)

## Example Usage

```python
from src.agents.business.nova_bot_simulator.main import NovaBotSimulatorAgent
from src.agents.business.nova_bot_simulator.config import SimulatorConfig
import asyncio

async def run_test():
    config = SimulatorConfig.from_env()
    simulator = NovaBotSimulatorAgent(config)
    results = await simulator.run_simulation()
    simulator.print_summary(results)
    simulator.save_results(results, config.output_file)

asyncio.run(run_test())
```

## Troubleshooting

**No questions generated**: Ensure `NoveumDocsData/index/metadata.json` exists and is readable.

**Import errors**: Make sure you're running from the repository root or have the correct Python path.

**Agent initialization fails**: Check that NovaBot's required environment variables are set (API keys, etc.).

**Slow execution**: Reduce `SIMULATOR_NUM_SESSIONS` or disable parallel execution for debugging.

