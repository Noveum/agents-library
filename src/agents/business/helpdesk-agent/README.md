# Customer Support Helpdesk Agent Template

A specialized AI agent for customer support that handles inquiries, classifies tickets, suggests knowledge base articles, and manages escalation workflows. Perfect for businesses looking to automate their customer support operations while maintaining high-quality service.

## Features

- 🎧 **Professional Support**: Trained specifically for customer service interactions
- 🎫 **Ticket Management**: Automatic ticket creation, classification, and prioritization
- 📚 **Knowledge Base Integration**: Suggests relevant articles and solutions
- ⚡ **Smart Escalation**: Automatically detects when human intervention is needed
- 📊 **Customer History**: Maintains conversation history and customer context
- 🔍 **Sentiment Analysis**: Monitors customer sentiment and adjusts responses
- 🚀 **Multi-Channel**: Supports chat, email, and API integrations
- 📈 **Analytics Ready**: Built-in tracking for support metrics and KPIs

## Quick Start

### 1. Clone and Setup

```bash
# Copy this template to your project
cp -r business-agents/customer-support/helpdesk-agent my-support-agent
cd my-support-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your Company

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your company details and API keys
nano .env
```

**Required Configuration:**
- `COMPANY_NAME`: Your company name
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: LLM provider API key
- `NOVEUM_API_KEY`: For tracing (optional)

### 3. Run the Support Agent

```bash
# Interactive support mode
python main.py

# Single ticket processing
python main.py --ticket "I can't log into my account"

# API server mode
python main.py --api
```

## Configuration Options

### Company Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPANY_NAME` | `TechCorp` | Your company name |
| `AGENT_NAME` | `Support Agent` | Agent display name |
| `DEFAULT_PRIORITY` | `medium` | Default ticket priority |

### Support Features

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_CATEGORIZE` | `true` | Automatic ticket categorization |
| `AUTO_SUGGEST_ARTICLES` | `true` | Suggest knowledge base articles |
| `INCLUDE_TICKET_ID` | `true` | Include ticket IDs in responses |
| `ESCALATION_KEYWORDS` | See config | Keywords that trigger escalation |

### Memory & Context

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_MAX_MESSAGES` | `50` | Max conversation history |
| `MEMORY_MAX_TOKENS` | `8000` | Max context tokens |
| `MEMORY_PERSIST` | `true` | Save conversations to file |

## Usage Examples

### Interactive Support Mode

```bash
python main.py
```

```
🎧 TechCorp Customer Support
Connected to: Support Agent
Type 'quit', 'exit', or 'bye' to end the session
Type '/history' to see customer history
Type '/stats' to see agent statistics
--------------------------------------------------
Enter customer ID (or press Enter for 'demo_customer'): CUST001
🆔 Customer ID: CUST001
How can I help you today?

Customer: I forgot my password and can't log in

Support Agent: I'm sorry to hear you're having trouble logging in! I'd be happy to help you reset your password.

To reset your password:
1. Go to our login page
2. Click 'Forgot Password' 
3. Enter your email address
4. Check your email for reset instructions
5. Follow the link and create a new password

If you don't receive the email within 5 minutes, please check your spam folder. Is there anything else I can help you with regarding your account access?

📋 Ticket: TKT-20240115-1234 | Priority: medium | Category: technical
```

### API Server Mode

```bash
python main.py --api
```

The agent starts a FastAPI server with these endpoints:

- `POST /support` - Submit a support request
- `GET /customer/{customer_id}/history` - Get customer history
- `GET /stats` - Get agent statistics

**Example API Usage:**

```bash
# Submit support request
curl -X POST "http://localhost:8000/support" \
     -H "Content-Type: application/json" \
     -d '{
       "content": "My account is locked",
       "customer_id": "CUST001",
       "channel": "email"
     }'

# Response
{
  "ticket_id": "TKT-20240115-5678",
  "response": "I understand your account is locked. Let me help you...",
  "priority": "high",
  "category": "account",
  "sentiment": "neutral",
  "escalated": false,
  "timestamp": "2024-01-15T10:30:00"
}
```

## Ticket Management

### Automatic Classification

The agent automatically classifies tickets by:

**Priority Levels:**
- `urgent`: Emergency, critical, down, broken
- `high`: Important, ASAP, quickly
- `medium`: Default priority
- `low`: When possible, no rush

**Categories:**
- `technical`: Login, password, errors, bugs
- `billing`: Bills, charges, payments, refunds
- `account`: Profile, settings, account management
- `product`: Features, tutorials, how-to questions
- `general`: Everything else

**Sentiment Analysis:**
- `positive`: Happy, great, excellent, love
- `neutral`: Default sentiment
- `negative`: Angry, frustrated, terrible, hate

### Escalation Triggers

The agent automatically escalates tickets when customers mention:
- Manager, supervisor, escalate
- Complaint, legal, lawsuit
- Cancel, refund (beyond agent authority)
- Angry, frustrated, unacceptable

## Knowledge Base Integration

### Built-in Articles

The template includes sample knowledge base articles for:
- Password reset procedures
- Billing inquiries
- Account lockout resolution
- Product features overview

### Custom Knowledge Base

Add your own articles by modifying the `_load_knowledge_base()` method:

```python
def _load_knowledge_base(self) -> Dict[str, str]:
    return {
        "custom_article": """
        Your custom support article content here.
        Include step-by-step instructions and helpful tips.
        """,
        # Add more articles...
    }
```

### External Knowledge Base

For production use, integrate with external systems:

```python
async def _search_external_kb(self, query: str):
    # Integrate with your knowledge base API
    # Examples: Zendesk, Freshdesk, custom database
    pass
```

## Customization Examples

### 1. Company-Specific Responses

Customize the system prompt in `config.yaml`:

```yaml
company_name: "Acme Corp"
agent_name: "Acme Support"

# Add company-specific information
support:
  business_hours: "Monday-Friday 9AM-6PM EST"
  escalation_email: "escalations@acme.com"
  knowledge_base_url: "https://help.acme.com"
```

### 2. Custom Escalation Logic

Override the escalation detection:

```python
async def _analyze_ticket(self, ticket: SupportTicket):
    await super()._analyze_ticket(ticket)
    
    # Custom escalation rules
    if "enterprise" in ticket.customer_id.lower():
        ticket.priority = TicketPriority.HIGH
    
    if "vip" in ticket.customer_id.lower():
        ticket.escalated = True
```

### 3. Integration with CRM Systems

Add CRM integration:

```python
async def _get_customer_info(self, customer_id: str):
    # Integrate with Salesforce, HubSpot, etc.
    customer_data = await self.crm_client.get_customer(customer_id)
    return {
        "tier": customer_data.get("tier"),
        "subscription": customer_data.get("subscription"),
        "previous_issues": customer_data.get("tickets", [])
    }
```

### 4. Advanced Analytics

Add custom metrics tracking:

```python
async def _track_metrics(self, ticket: SupportTicket, response_time: float):
    metrics = {
        "ticket_id": ticket.ticket_id,
        "category": ticket.category.value,
        "priority": ticket.priority.value,
        "response_time": response_time,
        "escalated": ticket.escalated,
        "customer_sentiment": ticket.sentiment
    }
    
    # Send to analytics system
    await self.analytics_client.track_event("support_interaction", metrics)
```

## Advanced Features

### Multi-Language Support

Add language detection and responses:

```python
async def _detect_language(self, content: str) -> str:
    # Use language detection library
    return "en"  # Default to English

async def _get_localized_response(self, response: str, language: str) -> str:
    if language != "en":
        # Translate response
        return await self.translator.translate(response, target_lang=language)
    return response
```

### Sentiment-Based Routing

Route based on customer sentiment:

```python
async def _route_by_sentiment(self, ticket: SupportTicket):
    if ticket.sentiment == "negative":
        # Route to senior agents
        ticket.assigned_to = "senior_agent_pool"
        ticket.priority = TicketPriority.HIGH
```

### Integration with Ticketing Systems

Connect to existing ticketing systems:

```python
async def _create_external_ticket(self, ticket: SupportTicket):
    # Create ticket in Zendesk, Jira, etc.
    external_ticket = await self.ticketing_system.create_ticket({
        "subject": f"Support Request - {ticket.category.value}",
        "description": ticket.content,
        "priority": ticket.priority.value,
        "customer_id": ticket.customer_id
    })
    
    ticket.external_id = external_ticket.id
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
# Production configuration
COMPANY_NAME=YourCompany
LLM_PROVIDER=openai
OPENAI_API_KEY=your_production_key
NOVEUM_ENABLED=true
NOVEUM_API_KEY=your_noveum_key
NOVEUM_ENVIRONMENT=production
MEMORY_PERSIST=true
MEMORY_FILE_PATH=/data/support_conversations.json
```

### Load Balancing

For high-volume support, deploy multiple instances:

```yaml
# docker-compose.yml
version: '3.8'
services:
  support-agent:
    build: .
    replicas: 3
    environment:
      - COMPANY_NAME=YourCompany
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8000-8002:8000"
```

## Monitoring & Analytics

### Key Metrics to Track

- **Response Time**: Time to first response
- **Resolution Rate**: Percentage of issues resolved without escalation
- **Customer Satisfaction**: Based on sentiment analysis
- **Ticket Volume**: Number of tickets by category/priority
- **Escalation Rate**: Percentage of tickets escalated

### Noveum Dashboard

The agent automatically tracks:
- Customer interactions and response times
- Ticket classification accuracy
- Knowledge base article usage
- Escalation patterns
- Agent performance metrics

## Troubleshooting

### Common Issues

1. **High Escalation Rate**
   - Review escalation keywords
   - Improve knowledge base coverage
   - Adjust sentiment detection thresholds

2. **Poor Ticket Classification**
   - Add more category keywords
   - Implement machine learning classification
   - Review and update classification rules

3. **Slow Response Times**
   - Optimize LLM parameters
   - Implement response caching
   - Use faster models for simple queries

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

This template is part of the [AI Agents Library](../../../README.md). To contribute improvements:

1. Fork the repository
2. Make your changes
3. Add tests for new features
4. Submit a pull request

## License

This template is licensed under the Apache 2.0 License. See the main repository [LICENSE](../../../LICENSE) for details.

