# Simple Chat Agent Template

A basic conversational AI agent that can chat with users using various LLM providers. This template includes memory management, Noveum tracing integration, and multiple deployment options.

## Features

- 🤖 **Multi-Provider Support**: Works with OpenAI, Anthropic, and other LLM providers
- 💾 **Memory Management**: Maintains conversation history with configurable limits
- 📊 **Noveum Integration**: Built-in tracing and observability
- 🔧 **Highly Configurable**: Environment variables and YAML configuration
- 🚀 **Multiple Modes**: Interactive chat, single message, or API server
- 🧪 **Production Ready**: Error handling, logging, and graceful degradation

## Quick Start

### 1. Clone and Setup

```bash
# Copy this template to your project
cp -r basic-agents/simple-chat-agent my-chat-agent
cd my-chat-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required Environment Variables:**
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (depending on provider)
- `NOVEUM_API_KEY` (optional, for tracing)

### 3. Run the Agent

```bash
# Interactive chat mode
python main.py

# Single message mode
python main.py --message "Hello, how are you?"

# API server mode
python main.py --api
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider (openai, anthropic, mock) |
| `LLM_MODEL` | `gpt-3.5-turbo` | Model name |
| `LLM_TEMPERATURE` | `0.7` | Response creativity (0.0-2.0) |
| `AGENT_NAME` | `ChatBot` | Agent display name |
| `MEMORY_TYPE` | `buffer` | Memory system type |
| `MEMORY_MAX_MESSAGES` | `20` | Max messages to remember |
| `NOVEUM_ENABLED` | `true` | Enable Noveum tracing |

### YAML Configuration

You can also use a YAML configuration file:

```bash
python main.py --config my-config.yaml
```

See `config.yaml` for a complete example.

## Usage Examples

### Interactive Chat

```bash
python main.py
```

```
💬 Starting interactive chat with ChatBot
Type 'quit', 'exit', or 'bye' to end the conversation
Type '/reset' to clear conversation history
Type '/stats' to see agent statistics
--------------------------------------------------

You: Hello! What's your name?

ChatBot: Hello! I'm ChatBot, your friendly AI assistant. How can I help you today?

You: /stats

📊 Agent Statistics:
   agent_name: ChatBot
   llm_provider: openai
   llm_model: gpt-3.5-turbo
   memory_type: buffer
   tracing_enabled: True
   total_conversations: 1
   uptime: 2024-01-15T10:30:45.123456
```

### API Server Mode

```bash
python main.py --api
```

The agent will start a FastAPI server on `http://localhost:8000` with:

- `POST /chat` - Send a message to the agent
- `GET /stats` - Get agent statistics  
- `POST /reset/{user_id}` - Reset conversation for a user
- `GET /docs` - API documentation

**Example API Usage:**

```bash
# Send a message
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello!", "user_id": "user123"}'

# Get statistics
curl "http://localhost:8000/stats"

# Reset conversation
curl -X POST "http://localhost:8000/reset/user123"
```

### Single Message Mode

```bash
python main.py --message "Explain quantum computing in simple terms"
```

## Customization

### 1. Modify the System Prompt

Edit the system prompt in `config.yaml` or set the `SYSTEM_PROMPT` environment variable:

```yaml
system_prompt: |
  You are a specialized customer support agent for TechCorp.
  - Always be helpful and professional
  - Escalate complex technical issues to human agents
  - Provide clear step-by-step instructions
```

### 2. Add Custom Logic

Extend the `SimpleChatAgent` class in `main.py`:

```python
class CustomChatAgent(SimpleChatAgent):
    async def _process_message(self, message: str, user_id: str) -> str:
        # Add custom preprocessing
        if "urgent" in message.lower():
            message = f"[URGENT] {message}"
        
        # Call parent method
        response = await super()._process_message(message, user_id)
        
        # Add custom postprocessing
        if len(response) > 500:
            response += "\n\n(This is a long response - would you like me to summarize?)"
        
        return response
```

### 3. Integrate with External Services

Add custom tools and integrations:

```python
async def _process_message(self, message: str, user_id: str) -> str:
    # Check if user wants weather information
    if "weather" in message.lower():
        weather_data = await self.get_weather_data()
        message = f"{message}\n\nCurrent weather: {weather_data}"
    
    return await super()._process_message(message, user_id)

async def get_weather_data(self):
    # Implement weather API integration
    return "Sunny, 72°F"
```

## Memory Systems

### Buffer Memory (Default)

Keeps recent messages in memory with configurable limits:

```yaml
memory:
  type: buffer
  max_messages: 20      # Keep last 20 messages
  max_tokens: 4000      # Trim if over 4000 tokens
  persist_to_file: true # Save to file
  file_path: ./conversations.json
```

### Summary Memory (Placeholder)

Maintains conversation summaries (implementation needed):

```yaml
memory:
  type: summary
  summary_frequency: 10  # Summarize every 10 messages
```

## Noveum Tracing

The agent automatically traces:

- **Agent Interactions**: User messages and responses
- **LLM Calls**: Provider, model, tokens, duration
- **Memory Operations**: Add, retrieve, clear operations
- **Errors**: Failures and exceptions

Configure tracing in `.env`:

```bash
NOVEUM_ENABLED=true
NOVEUM_API_KEY=your_api_key
NOVEUM_PROJECT=my-chat-agent
NOVEUM_ENVIRONMENT=production
```

## Testing

Run the included tests:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

## Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "main.py", "--api"]
```

### Environment Variables for Production

```bash
# Production environment variables
LLM_PROVIDER=openai
OPENAI_API_KEY=your_production_key
NOVEUM_ENABLED=true
NOVEUM_API_KEY=your_noveum_key
NOVEUM_ENVIRONMENT=production
MEMORY_PERSIST=true
MEMORY_FILE_PATH=/data/conversations.json
```

## Troubleshooting

### Common Issues

1. **Missing API Key**
   ```
   Error: OpenAI API key is required
   ```
   Solution: Set `OPENAI_API_KEY` in your `.env` file

2. **Import Error for Noveum**
   ```
   Warning: Noveum trace package not found
   ```
   Solution: Install with `pip install noveum-trace` or disable tracing

3. **Memory Persistence Issues**
   ```
   Warning: Failed to save memory to file
   ```
   Solution: Check file permissions and directory exists

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

This template is part of the [AI Agents Library](../../README.md). To contribute improvements:

1. Fork the repository
2. Make your changes
3. Add tests for new features
4. Submit a pull request

## License

This template is licensed under the Apache 2.0 License. See the main repository [LICENSE](../../LICENSE) for details.

