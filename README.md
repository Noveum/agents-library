# AI Agents Library

A production-ready collection of AI agent templates with unified API access and Kubernetes deployment support. Built with ❤️ by the [Noveum](https://noveum.ai) team.

## Overview

This repository provides a comprehensive library of AI agents that can be deployed as microservices or used as templates for custom implementations. Each agent includes complete configuration, testing, and deployment manifests with built-in [Noveum](https://noveum.ai) observability.

## Features

- **Agent Templates**: Ready-to-use AI agents organized by category
- **Unified API**: REST API for invoking any agent via HTTP endpoints
- **Kubernetes Native**: Production-ready deployment with auto-scaling
- **Multi-Provider Support**: OpenAI, Anthropic, Azure, AWS, and GCP
- **Observability**: Built-in tracing with [Noveum](https://noveum.ai) integration
- **Testing**: Comprehensive test suite with CI/CD support

## Repository Structure

```
agents-library/
├── src/                     # Source code
│   ├── agents/             # Agent implementations
│   │   ├── basic/          # Simple foundational agents
│   │   ├── business/       # Business domain agents
│   │   ├── technical/      # Technical and development agents
│   │   ├── creative/       # Creative and content agents
│   │   └── specialized/    # Domain-specific agents
│   ├── api/               # FastAPI application
│   │   ├── main.py        # API server
│   │   ├── agent_registry.py # Agent discovery
│   │   └── client.py      # Python clients
│   ├── shared/            # Shared components
│   │   ├── llm_client.py  # Multi-provider LLM client
│   │   ├── memory.py      # Memory management
│   │   └── noveum_tracer.py # Tracing integration
│   └── tests/             # Test suite
├── k8s/                   # Kubernetes manifests
├── docs/                  # Documentation
├── examples/              # Usage examples
└── scripts/               # Utility scripts
```

## 🤖 Available Agents

### Basic Agents (`src/agents/basic/`)

#### [Simple Chat Agent](src/agents/basic/simple-chat-agent/)
- **Description**: A foundational conversational AI agent with memory management
- **Use Cases**: Customer service, general Q&A, interactive chatbots
- **Features**: Multi-provider LLM support, conversation memory, configurable personality
- **Endpoints**: `chat`, `process`
- **Documentation**: [README](src/agents/basic/simple-chat-agent/README.md)
- **Configuration**: [agent_info.yaml](src/agents/basic/simple-chat-agent/agent_info.yaml)

### Business Agents (`src/agents/business/`)

#### [Customer Support Helpdesk Agent](src/agents/business/helpdesk-agent/)
- **Description**: Specialized customer support agent with ticket management and escalation workflows
- **Use Cases**: Automated customer service, support ticket handling, FAQ responses
- **Features**: Ticket classification, escalation detection, knowledge base integration
- **Endpoints**: `chat`, `support`, `process`
- **Documentation**: [README](src/agents/business/helpdesk-agent/README.md)
- **Configuration**: [agent_info.yaml](src/agents/business/helpdesk-agent/agent_info.yaml)

### Technical Agents (`src/agents/technical/`)
*Ready for expansion - contribute your technical agents here!*

- **Code Assistant**: Code generation, debugging, and review
- **DevOps Helper**: Infrastructure automation and monitoring
- **Data Analyst**: Data processing and visualization
- **API Documentation**: Automatic API documentation generation

### Creative Agents (`src/agents/creative/`)
*Ready for expansion - contribute your creative agents here!*

- **Content Writer**: Blog posts, articles, and marketing copy
- **Social Media Manager**: Post generation and engagement strategies
- **Design Assistant**: Creative briefs and design recommendations
- **Copywriter**: Marketing copy and advertising content

### Specialized Agents (`src/agents/specialized/`)
*Ready for expansion - contribute your domain-specific agents here!*

- **Finance Advisor**: Financial analysis and investment advice
- **Healthcare Assistant**: Medical information and health guidance
- **Legal Advisor**: Legal research and compliance assistance
- **Education Tutor**: Personalized learning and tutoring

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/Noveum/agents-library.git
cd agents-library

# Install dependencies
pip install -r src/api/requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (see Configuration section below)

# Start API server
python -m src.api.main
```

Access the API at `http://localhost:8000` and documentation at `http://localhost:8000/docs`.

### Docker Deployment

```bash
# Development
docker-compose --profile dev up

# Production
docker-compose up --build
```

### Kubernetes Deployment

```bash
# Quick deployment
./k8s/deploy.sh

# Manual deployment
kubectl apply -f k8s/
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default | Get API Key |
|----------|-------------|----------|---------|-------------|
| `OPENAI_API_KEY` | OpenAI API key | Yes* | - | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes* | - | [Anthropic Console](https://console.anthropic.com/) |
| `NOVEUM_API_KEY` | Noveum tracing key | No | - | [Noveum Dashboard](https://noveum.ai/dashboard) |
| `LLM_PROVIDER` | LLM provider | No | `openai` | - |
| `LLM_MODEL` | Model name | No | `gpt-3.5-turbo` | - |
| `NOVEUM_ENABLED` | Enable tracing | No | `true` | - |

*At least one LLM provider API key is required.

### 🔍 Noveum Observability Integration

This library comes with built-in [Noveum](https://noveum.ai) integration for comprehensive observability:

- **Automatic Tracing**: All agent interactions are automatically traced
- **Performance Monitoring**: Track response times, token usage, and costs
- **Error Tracking**: Detailed error logging and debugging information
- **Analytics Dashboard**: Visualize agent usage patterns and performance

#### Getting Started with Noveum

1. **Sign up**: Create a free account at [noveum.ai](https://noveum.ai)
2. **Get API Key**: Generate your API key in the [Noveum Dashboard](https://noveum.ai/dashboard)
3. **Configure**: Add `NOVEUM_API_KEY=your-key-here` to your `.env` file
4. **Monitor**: View real-time analytics in your [Noveum Dashboard](https://noveum.ai/dashboard)

#### Noveum Features

- 📊 **Real-time Analytics**: Monitor agent performance and usage
- 🔍 **Detailed Tracing**: Track every LLM call and agent interaction
- 💰 **Cost Tracking**: Monitor API costs across all providers
- 🚨 **Error Monitoring**: Get alerts for failures and performance issues
- 📈 **Usage Insights**: Understand user behavior and agent effectiveness

Learn more at [noveum.ai](https://noveum.ai) or check the [documentation](https://docs.noveum.ai).

### Agent Configuration

Each agent includes an `agent_info.yaml` file with metadata:

```yaml
agent_id: category.agent_name
name: Human Readable Name
category: basic|business|technical|creative|specialized
description: Agent description
endpoints: [chat, process, support]
configuration:
  required_env_vars: [OPENAI_API_KEY]
  optional_env_vars: [LLM_MODEL, TEMPERATURE]
```

## API Usage

### List Available Agents

```bash
curl http://localhost:8000/agents
```

### Chat with an Agent

```bash
curl -X POST http://localhost:8000/agents/basic.simple_chat_agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how can you help me?",
    "user_id": "user123"
  }'
```

### Customer Support Request

```bash
curl -X POST http://localhost:8000/agents/business.helpdesk_agent/support \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need help with my account login",
    "user_id": "customer456"
  }'
```

### Python Client

```python
from src.api.client import AgentsAPIClient

with AgentsAPIClient("http://localhost:8000") as client:
    # List agents
    agents = client.list_agents()
    print(f"Available agents: {[agent.name for agent in agents.agents]}")
    
    # Chat with basic agent
    response = client.chat(
        "basic.simple_chat_agent",
        "What can you do?",
        user_id="user123"
    )
    print(f"Agent: {response.response}")
    
    # Submit support request
    support_response = client.support_request(
        "business.helpdesk_agent",
        "I need help with billing",
        user_id="customer789"
    )
    print(f"Support: {support_response.response}")
```

## Development

### Adding New Agents

1. **Choose Category**: Select appropriate category in `src/agents/`
2. **Create Directory**: Follow the established structure
   ```
   src/agents/category/agent-name/
   ├── main.py              # Agent implementation
   ├── config.py            # Configuration classes
   ├── requirements.txt     # Dependencies
   ├── agent_info.yaml      # Metadata
   ├── README.md           # Documentation
   └── tests/              # Test files
   ```

3. **Implement Agent**: Follow the pattern from existing agents
   ```python
   class MyAgent:
       async def chat(self, message: str, user_id: str) -> str:
           # Implementation
           pass
   ```

4. **Add Documentation**: Create comprehensive README and examples
5. **Test**: Add unit tests and integration tests
6. **Submit**: Agent will be automatically discovered and available via API

### Agent Template Structure

Each agent follows this consistent structure:

- **[main.py](src/agents/basic/simple-chat-agent/main.py)**: Core agent implementation
- **[config.py](src/agents/basic/simple-chat-agent/config.py)**: Configuration classes and validation
- **[agent_info.yaml](src/agents/basic/simple-chat-agent/agent_info.yaml)**: Agent metadata and capabilities
- **[README.md](src/agents/basic/simple-chat-agent/README.md)**: Usage documentation and examples
- **[requirements.txt](src/agents/basic/simple-chat-agent/requirements.txt)**: Python dependencies
- **[.env.example](src/agents/basic/simple-chat-agent/.env.example)**: Environment configuration template
- **[tests/](src/agents/basic/simple-chat-agent/tests/)**: Unit tests and test utilities

### Testing

```bash
# Run all tests
pytest

# Run specific categories
pytest -m unit
pytest -m integration
pytest -m api

# With coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## Production Deployment

### Kubernetes

The repository includes production-ready Kubernetes manifests in [`k8s/`](k8s/):

- **[Namespace](k8s/namespace.yaml)**: Isolated environment
- **[ConfigMap](k8s/configmap.yaml)**: Application configuration
- **[Secret](k8s/secret.yaml)**: API keys and sensitive data
- **[Deployment](k8s/deployment.yaml)**: Application pods with health checks
- **[Service](k8s/service.yaml)**: Internal load balancing
- **[Ingress](k8s/ingress.yaml)**: External access with SSL/TLS
- **[HPA](k8s/hpa.yaml)**: Horizontal pod autoscaling

### Security

- API keys stored as Kubernetes secrets
- Non-root container execution
- Network policies for pod isolation
- RBAC for service account permissions
- Input validation and rate limiting

### Monitoring

- Health check endpoints for all agents
- Prometheus metrics collection
- Structured JSON logging
- Distributed tracing with [Noveum](https://noveum.ai)
- Grafana dashboards for visualization

## API Reference

### Endpoints

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `GET` | `/` | API information | [Try it](http://localhost:8000/) |
| `GET` | `/agents` | List all agents | [Try it](http://localhost:8000/agents) |
| `GET` | `/agents/{id}` | Get agent details | [Try it](http://localhost:8000/agents/basic.simple_chat_agent) |
| `POST` | `/agents/{id}/chat` | Chat with agent | See examples above |
| `POST` | `/agents/{id}/process` | Process message | See examples above |
| `POST` | `/agents/{id}/support` | Support request | See examples above |
| `GET` | `/health` | System health | [Try it](http://localhost:8000/health) |
| `GET` | `/health/{id}` | Agent health | [Try it](http://localhost:8000/health/basic.simple_chat_agent) |
| `GET` | `/stats` | Registry statistics | [Try it](http://localhost:8000/stats) |

### Interactive Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Spec**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Response Format

```json
{
  "agent_id": "basic.simple_chat_agent",
  "response": "Hello! How can I help you?",
  "metadata": {
    "user_id": "user123",
    "processing_time": 0.234
  },
  "processing_time": 0.234,
  "timestamp": "2024-01-01T12:00:00Z",
  "success": true,
  "error": null
}
```

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-new-agent`
3. **Add your agent**: Follow the established patterns and structure
4. **Include tests**: Add comprehensive tests for your agent
5. **Update documentation**: Add your agent to this README
6. **Submit a pull request**: We'll review and merge your contribution

### Contribution Guidelines

- Follow the established directory structure
- Include comprehensive documentation
- Add unit tests and integration tests
- Use type hints throughout your code
- Follow Python best practices (PEP 8)
- Include example usage in your agent's README

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Examples and Tutorials

### Basic Usage Examples

- **[Simple Chat](examples/basic_chat.py)**: Basic conversation with an agent
- **[Customer Support](examples/customer_support.py)**: Handling support requests
- **[Batch Processing](examples/batch_processing.py)**: Processing multiple requests
- **[Custom Configuration](examples/custom_config.py)**: Advanced configuration options

### Integration Examples

- **[Flask Integration](examples/flask_integration.py)**: Using agents in Flask applications
- **[FastAPI Integration](examples/fastapi_integration.py)**: Building on top of the API
- **[Webhook Handler](examples/webhook_handler.py)**: Processing webhooks with agents
- **[Scheduled Tasks](examples/scheduled_tasks.py)**: Running agents on schedules

## Troubleshooting

### Common Issues

1. **Agent Not Found**: Check agent directory structure and `agent_info.yaml`
2. **Import Errors**: Verify Python path and dependencies
3. **API Key Issues**: Ensure environment variables are set correctly
4. **Health Check Failures**: Check agent dependencies and LLM connectivity

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=debug python -m src.api.main

# Enable auto-reload for development
python -m src.api.main --reload
```

### Getting Help

- **Documentation**: Complete guides in this repository
- **Issues**: [GitHub Issues](https://github.com/Noveum/agents-library/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Noveum/agents-library/discussions)
- **Noveum Support**: [help@noveum.ai](mailto:help@noveum.ai)
- **Enterprise Support**: Contact the Noveum team

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the API framework
- Powered by [OpenAI](https://openai.com/) and [Anthropic](https://anthropic.com/) LLMs
- Observability by [Noveum](https://noveum.ai)
- Deployed on [Kubernetes](https://kubernetes.io/)

---

**Ready to build amazing AI agents? Start with our templates and deploy to production in minutes!**

**Built with ❤️ by the [Noveum](https://noveum.ai) team**

