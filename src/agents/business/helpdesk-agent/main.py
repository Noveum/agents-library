#!/usr/bin/env python3
"""
Customer Support Helpdesk Agent Template

A specialized AI agent for customer support that can handle common inquiries,
escalate complex issues, and maintain customer interaction history.

Features:
- Ticket classification and routing
- Knowledge base integration
- Escalation workflows
- Customer sentiment analysis
- Multi-channel support (chat, email, API)

Usage:
    python main.py                    # Interactive support mode
    python main.py --ticket "Issue"   # Process single ticket
    python main.py --api             # Run as support API
"""

import asyncio
import argparse
import os
import sys
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

def _load_local_config():
    import importlib.util
    import sys
    from pathlib import Path

    config_path = Path(__file__).resolve().with_name("config.py")
    spec = importlib.util.spec_from_file_location("helpdesk_local_config", config_path)
    if not spec or not spec.loader:
        raise ImportError(f"Unable to load Helpdesk config from {config_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_local_config = _load_local_config()
SupportAgentConfig = _local_config.SupportAgentConfig

from src.shared.llm_client import LLMClient
from src.shared.memory import ConversationMemory
from src.shared.noveum_tracer import NoveumTracer


class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    PRODUCT = "product"
    GENERAL = "general"


class SupportTicket:
    """Represents a customer support ticket."""
    
    def __init__(self, content: str, customer_id: str, channel: str = "chat"):
        self.ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d')}-{hash(content) % 10000:04d}"
        self.content = content
        self.customer_id = customer_id
        self.channel = channel
        self.created_at = datetime.now()
        self.priority = TicketPriority.MEDIUM
        self.category = TicketCategory.GENERAL
        self.status = "open"
        self.assigned_to = None
        self.resolution = None
        self.sentiment = "neutral"
        self.escalated = False


class CustomerSupportAgent:
    """
    Specialized customer support agent with advanced support capabilities.
    
    Features:
    - Automatic ticket classification and prioritization
    - Knowledge base integration for common issues
    - Escalation workflows for complex problems
    - Customer sentiment monitoring
    - Multi-channel support (chat, email, API)
    """
    
    def __init__(self, config: SupportAgentConfig):
        """Initialize the customer support agent."""
        self.config = config
        self.llm_client = LLMClient(config.llm_config)
        self.memory = ConversationMemory(config.memory_config)
        self.tracer = NoveumTracer(config.noveum_config) if config.noveum_config.enabled else None
        
        # Support-specific configuration
        self.agent_name = config.agent_name or "Support Agent"
        self.company_name = config.company_name or "TechCorp"
        self.escalation_keywords = config.escalation_keywords or [
            "manager", "supervisor", "escalate", "complaint", "legal", "lawsuit",
            "cancel", "refund", "angry", "frustrated", "unacceptable"
        ]
        
        # Load knowledge base
        self.knowledge_base = self._load_knowledge_base()
        
        print(f"🎧 {self.agent_name} initialized for {self.company_name}")
        print(f"📚 Knowledge base loaded with {len(self.knowledge_base)} articles")
        if self.tracer:
            print(f"📊 Noveum tracing enabled for project: {config.noveum_config.project}")
    
    def _load_knowledge_base(self) -> Dict[str, str]:
        """Load knowledge base articles."""
        # In a real implementation, this would load from a database or files
        return {
            "password_reset": """
            To reset your password:
            1. Go to the login page
            2. Click 'Forgot Password'
            3. Enter your email address
            4. Check your email for reset instructions
            5. Follow the link and create a new password
            
            If you don't receive the email within 5 minutes, check your spam folder.
            """,
            
            "billing_inquiry": """
            For billing questions:
            - View your current bill in Account Settings > Billing
            - Download invoices from the Billing History section
            - Update payment methods in Payment Settings
            - Contact billing@company.com for payment disputes
            
            Billing cycles run from the 1st to the last day of each month.
            """,
            
            "account_locked": """
            If your account is locked:
            1. Wait 15 minutes for automatic unlock
            2. Try logging in again
            3. If still locked, use the 'Unlock Account' option
            4. Contact support if the issue persists
            
            Accounts are locked after 5 failed login attempts for security.
            """,
            
            "product_features": """
            Our product includes:
            - Real-time collaboration tools
            - Advanced analytics dashboard
            - API access for integrations
            - 24/7 customer support
            - 99.9% uptime guarantee
            
            For detailed feature documentation, visit our Help Center.
            """
        }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the support agent."""
        return f"""You are a professional customer support agent for {self.company_name}. 

Your role and responsibilities:
- Provide helpful, accurate, and timely support to customers
- Maintain a friendly, professional, and empathetic tone
- Resolve issues efficiently using available resources
- Escalate complex issues when appropriate
- Follow company policies and procedures

Guidelines:
- Always greet customers warmly and thank them for contacting support
- Listen carefully to understand the customer's issue
- Ask clarifying questions when needed
- Provide step-by-step solutions when possible
- Offer alternatives if the primary solution doesn't work
- Follow up to ensure the issue is resolved
- Apologize for any inconvenience caused

Escalation triggers:
- Customer requests to speak with a manager/supervisor
- Legal threats or mentions of lawsuits
- Requests for refunds beyond your authority
- Technical issues you cannot resolve
- Angry or abusive customers

Company information:
- Company: {self.company_name}
- Support hours: 24/7
- Response time goal: Under 2 minutes for chat, 4 hours for email
- Customer satisfaction target: 95%

Remember: You represent {self.company_name} and should always maintain professionalism while being genuinely helpful."""
    
    async def handle_support_request(self, content: str, customer_id: str, channel: str = "chat") -> Dict[str, Any]:
        """
        Handle a customer support request and return structured response.
        
        Args:
            content: Customer's message/issue
            customer_id: Unique customer identifier
            channel: Communication channel (chat, email, phone)
            
        Returns:
            Structured support response with ticket info
        """
        if self.tracer:
            return await self.tracer.trace_agent_interaction(
                agent_name=self.agent_name,
                user_message=content,
                handler=self._process_support_request,
                user_id=customer_id,
                metadata={"channel": channel, "company": self.company_name}
            )
        else:
            return await self._process_support_request(content, customer_id, channel)

    async def chat(self, message: str, user_id: str = "default") -> str:
        """
        Chat endpoint-compatible wrapper.

        The underlying implementation returns structured ticket data; the API expects a string,
        so we return only the user-facing response text.
        """
        result = await self.handle_support_request(message, user_id, channel="chat")
        if isinstance(result, dict) and "response" in result:
            return str(result["response"])
        return str(result)

    async def process(self, message: str, user_id: str = "default") -> str:
        """Process endpoint-compatible alias."""
        return await self.chat(message, user_id)
    
    async def _process_support_request(self, content: str, customer_id: str, channel: str = "chat") -> Dict[str, Any]:
        """Internal support request processing."""
        try:
            # Create support ticket
            ticket = SupportTicket(content, customer_id, channel)
            
            # Analyze and classify the ticket
            await self._analyze_ticket(ticket)
            
            # Check for knowledge base matches
            kb_match = self._search_knowledge_base(content)
            
            # Add customer message to memory
            await self.memory.add_message(customer_id, "user", content, {
                "ticket_id": ticket.ticket_id,
                "channel": channel,
                "priority": ticket.priority.value,
                "category": ticket.category.value
            })
            
            # Prepare context for LLM
            conversation_history = await self.memory.get_conversation(customer_id)
            
            # Build enhanced prompt with context
            enhanced_prompt = self._build_support_prompt(ticket, kb_match, conversation_history)
            
            # Generate response
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": enhanced_prompt}
            ]
            
            response = await self.llm_client.generate(
                messages=messages,
                max_tokens=self.config.max_response_tokens,
                temperature=self.config.temperature
            )
            
            # Add agent response to memory
            await self.memory.add_message(customer_id, "assistant", response, {
                "ticket_id": ticket.ticket_id,
                "kb_used": kb_match is not None,
                "escalated": ticket.escalated
            })
            
            # Return structured response
            return {
                "ticket_id": ticket.ticket_id,
                "response": response,
                "priority": ticket.priority.value,
                "category": ticket.category.value,
                "sentiment": ticket.sentiment,
                "escalated": ticket.escalated,
                "knowledge_base_used": kb_match is not None,
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_response = f"I apologize, but I'm experiencing technical difficulties. Please try again in a moment, or contact our support team directly at support@{self.company_name.lower()}.com"
            
            return {
                "ticket_id": f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "response": error_response,
                "priority": "high",
                "category": "technical",
                "sentiment": "neutral",
                "escalated": True,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_ticket(self, ticket: SupportTicket):
        """Analyze ticket for priority, category, and sentiment."""
        content_lower = ticket.content.lower()
        
        # Determine priority
        if any(word in content_lower for word in ["urgent", "emergency", "critical", "down", "broken"]):
            ticket.priority = TicketPriority.URGENT
        elif any(word in content_lower for word in ["important", "asap", "quickly", "soon"]):
            ticket.priority = TicketPriority.HIGH
        elif any(word in content_lower for word in ["when possible", "no rush", "whenever"]):
            ticket.priority = TicketPriority.LOW
        
        # Determine category
        if any(word in content_lower for word in ["login", "password", "access", "error", "bug", "crash"]):
            ticket.category = TicketCategory.TECHNICAL
        elif any(word in content_lower for word in ["bill", "charge", "payment", "invoice", "refund"]):
            ticket.category = TicketCategory.BILLING
        elif any(word in content_lower for word in ["account", "profile", "settings", "delete"]):
            ticket.category = TicketCategory.ACCOUNT
        elif any(word in content_lower for word in ["feature", "how to", "tutorial", "guide"]):
            ticket.category = TicketCategory.PRODUCT
        
        # Determine sentiment
        if any(word in content_lower for word in ["angry", "frustrated", "terrible", "awful", "hate"]):
            ticket.sentiment = "negative"
        elif any(word in content_lower for word in ["happy", "great", "excellent", "love", "amazing"]):
            ticket.sentiment = "positive"
        
        # Check for escalation triggers
        if any(keyword in content_lower for keyword in self.escalation_keywords):
            ticket.escalated = True
            ticket.priority = TicketPriority.HIGH
    
    def _search_knowledge_base(self, content: str) -> Optional[str]:
        """Search knowledge base for relevant articles."""
        content_lower = content.lower()
        
        # Simple keyword matching (in production, use vector search)
        if any(word in content_lower for word in ["password", "reset", "login"]):
            return self.knowledge_base.get("password_reset")
        elif any(word in content_lower for word in ["bill", "billing", "charge", "payment"]):
            return self.knowledge_base.get("billing_inquiry")
        elif any(word in content_lower for word in ["locked", "account", "access"]):
            return self.knowledge_base.get("account_locked")
        elif any(word in content_lower for word in ["feature", "product", "what can"]):
            return self.knowledge_base.get("product_features")
        
        return None
    
    def _build_support_prompt(self, ticket: SupportTicket, kb_match: Optional[str], conversation_history: List[Dict]) -> str:
        """Build enhanced prompt with context."""
        prompt_parts = [
            f"Customer Issue: {ticket.content}",
            f"Ticket ID: {ticket.ticket_id}",
            f"Priority: {ticket.priority.value}",
            f"Category: {ticket.category.value}",
            f"Channel: {ticket.channel}",
            f"Customer Sentiment: {ticket.sentiment}"
        ]
        
        if kb_match:
            prompt_parts.append(f"\nRelevant Knowledge Base Article:\n{kb_match}")
        
        if ticket.escalated:
            prompt_parts.append("\n⚠️ ESCALATION REQUIRED: This issue should be escalated to a human agent.")
        
        if len(conversation_history) > 2:  # More than just the current exchange
            prompt_parts.append(f"\nPrevious conversation context available ({len(conversation_history)} messages)")
        
        return "\n".join(prompt_parts)
    
    async def get_customer_history(self, customer_id: str) -> Dict[str, Any]:
        """Get customer interaction history."""
        conversation = await self.memory.get_conversation(customer_id)
        
        # Extract ticket information from metadata
        tickets = []
        for msg in conversation:
            if msg.get("role") == "user" and "metadata" in msg:
                metadata = msg.get("metadata", {})
                if "ticket_id" in metadata:
                    tickets.append({
                        "ticket_id": metadata["ticket_id"],
                        "content": msg["content"],
                        "timestamp": msg.get("timestamp"),
                        "priority": metadata.get("priority"),
                        "category": metadata.get("category")
                    })
        
        return {
            "customer_id": customer_id,
            "total_interactions": len(conversation),
            "tickets": tickets,
            "last_contact": conversation[-1].get("timestamp") if conversation else None
        }
    
    def get_support_stats(self) -> Dict[str, Any]:
        """Get support agent statistics."""
        return {
            "agent_name": self.agent_name,
            "company": self.company_name,
            "llm_provider": self.config.llm_config.provider,
            "llm_model": self.config.llm_config.model,
            "knowledge_base_articles": len(self.knowledge_base),
            "escalation_keywords": len(self.escalation_keywords),
            "tracing_enabled": self.tracer is not None,
            "total_customers": self.memory.get_conversation_count(),
            "uptime": datetime.now().isoformat()
        }


async def interactive_support_mode(agent: CustomerSupportAgent):
    """Run the agent in interactive support mode."""
    print(f"\n🎧 {agent.company_name} Customer Support")
    print(f"Connected to: {agent.agent_name}")
    print("Type 'quit', 'exit', or 'bye' to end the session")
    print("Type '/history' to see customer history")
    print("Type '/stats' to see agent statistics")
    print("-" * 50)
    
    customer_id = input("Enter customer ID (or press Enter for 'demo_customer'): ").strip()
    if not customer_id:
        customer_id = "demo_customer"
    
    print(f"🆔 Customer ID: {customer_id}")
    print("How can I help you today?\n")
    
    while True:
        try:
            # Get customer input
            user_input = input("Customer: ").strip()
            
            if not user_input:
                continue
                
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print(f"\n👋 Thank you for contacting {agent.company_name} support!")
                break
            elif user_input == '/history':
                history = await agent.get_customer_history(customer_id)
                print(f"\n📋 Customer History:")
                print(f"   Total interactions: {history['total_interactions']}")
                print(f"   Tickets: {len(history['tickets'])}")
                if history['last_contact']:
                    print(f"   Last contact: {history['last_contact']}")
                continue
            elif user_input == '/stats':
                stats = agent.get_support_stats()
                print(f"\n📊 Support Agent Statistics:")
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                continue
            
            # Process support request
            print(f"\n{agent.agent_name}: ", end="", flush=True)
            
            result = await agent.handle_support_request(user_input, customer_id, "chat")
            
            print(result["response"])
            
            # Show ticket information
            print(f"\n📋 Ticket: {result['ticket_id']} | Priority: {result['priority']} | Category: {result['category']}")
            if result['escalated']:
                print("⚠️  This issue has been flagged for escalation to a human agent.")
            
        except KeyboardInterrupt:
            print(f"\n\n👋 Thank you for contacting {agent.company_name} support!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


async def single_ticket_mode(agent: CustomerSupportAgent, ticket_content: str):
    """Process a single support ticket."""
    customer_id = "single_ticket_customer"
    
    result = await agent.handle_support_request(ticket_content, customer_id, "api")
    
    print(f"Ticket ID: {result['ticket_id']}")
    print(f"Priority: {result['priority']}")
    print(f"Category: {result['category']}")
    print(f"Response: {result['response']}")
    
    if result['escalated']:
        print("⚠️  ESCALATION REQUIRED")


async def api_server_mode(agent: CustomerSupportAgent):
    """Run the agent as a support API server."""
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI(title=f"{agent.company_name} Support API", version="1.0.0")
        
        class SupportRequest(BaseModel):
            content: str
            customer_id: str
            channel: str = "api"
        
        class SupportResponse(BaseModel):
            ticket_id: str
            response: str
            priority: str
            category: str
            sentiment: str
            escalated: bool
            timestamp: str
        
        @app.post("/support", response_model=SupportResponse)
        async def handle_support(request: SupportRequest):
            try:
                result = await agent.handle_support_request(
                    request.content, 
                    request.customer_id, 
                    request.channel
                )
                return SupportResponse(**result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/customer/{customer_id}/history")
        async def get_customer_history(customer_id: str):
            return await agent.get_customer_history(customer_id)
        
        @app.get("/stats")
        async def get_stats():
            return agent.get_support_stats()
        
        print(f"🚀 Starting {agent.company_name} Support API")
        print("📖 API Documentation: http://localhost:8000/docs")
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except ImportError:
        print("❌ FastAPI not installed. Install with: pip install fastapi uvicorn")
        sys.exit(1)


def main():
    """Main entry point for the support agent."""
    parser = argparse.ArgumentParser(description="Customer Support Agent")
    parser.add_argument("--ticket", "-t", help="Single ticket to process")
    parser.add_argument("--api", action="store_true", help="Run as API server")
    parser.add_argument("--config", "-c", help="Path to config file", default="config.yaml")
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = SupportAgentConfig.from_file(args.config)
    except FileNotFoundError:
        print(f"⚠️  Config file not found: {args.config}")
        print("Using default configuration...")
        config = SupportAgentConfig.from_env()
    
    # Create and run agent
    async def run():
        agent = CustomerSupportAgent(config)
        
        if args.api:
            await api_server_mode(agent)
        elif args.ticket:
            await single_ticket_mode(agent, args.ticket)
        else:
            await interactive_support_mode(agent)
    
    # Run the agent
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n👋 Support agent stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

