#!/usr/bin/env python3
"""
Customer Support Example

Demonstrates how to use the helpdesk agent for customer support scenarios.
"""

import asyncio
from src.api.client import AgentsAPIClient, AsyncAgentsAPIClient


def basic_support_requests():
    """Example of handling various support requests."""
    print("🎧 Customer Support Examples")
    print("=" * 40)
    
    with AgentsAPIClient("http://localhost:8000") as client:
        # Different types of support requests
        support_scenarios = [
            {
                "user_id": "customer_001",
                "message": "I can't log into my account. I keep getting an error message.",
                "type": "Login Issue"
            },
            {
                "user_id": "customer_002", 
                "message": "I was charged twice for my subscription this month. Can you help?",
                "type": "Billing Issue"
            },
            {
                "user_id": "customer_003",
                "message": "How do I cancel my subscription?",
                "type": "Account Management"
            },
            {
                "user_id": "customer_004",
                "message": "The app keeps crashing when I try to upload files.",
                "type": "Technical Issue"
            },
            {
                "user_id": "customer_005",
                "message": "I need to update my payment method but can't find the option.",
                "type": "Account Settings"
            }
        ]
        
        print("📞 Processing Support Requests:")
        print("-" * 40)
        
        for scenario in support_scenarios:
            print(f"\n🎫 {scenario['type']} (User: {scenario['user_id']})")
            print(f"Customer: {scenario['message']}")
            
            # Submit support request
            response = client.support_request(
                "business.helpdesk_agent",
                scenario['message'],
                user_id=scenario['user_id']
            )
            
            print(f"Support Agent: {response.response}")
            print(f"⏱️  Processing time: {response.processing_time:.2f}s")


async def concurrent_support_handling():
    """Example of handling multiple support requests concurrently."""
    print("\n🚀 Concurrent Support Handling")
    print("=" * 40)
    
    async with AsyncAgentsAPIClient("http://localhost:8000") as client:
        # Simulate multiple customers contacting support simultaneously
        concurrent_requests = [
            ("customer_101", "I forgot my password and the reset email isn't coming"),
            ("customer_102", "My premium features aren't working after upgrading"),
            ("customer_103", "I need to change my email address on the account"),
            ("customer_104", "The mobile app won't sync with the web version"),
            ("customer_105", "I want to downgrade my plan but keep my data")
        ]
        
        print(f"📞 Handling {len(concurrent_requests)} simultaneous requests...")
        
        # Process all requests concurrently
        tasks = [
            client.support_request(
                "business.helpdesk_agent",
                message,
                user_id=user_id
            )
            for user_id, message in concurrent_requests
        ]
        
        responses = await asyncio.gather(*tasks)
        
        print("\n📋 Support Responses:")
        print("-" * 40)
        
        for i, (request, response) in enumerate(zip(concurrent_requests, responses)):
            user_id, message = request
            print(f"\n🎫 Ticket #{i+1} ({user_id})")
            print(f"Issue: {message}")
            print(f"Response: {response.response}")
            print(f"Status: {'✅ Resolved' if response.success else '❌ Failed'}")


def escalation_scenarios():
    """Example of support requests that might require escalation."""
    print("\n🚨 Escalation Scenarios")
    print("=" * 40)
    
    with AgentsAPIClient("http://localhost:8000") as client:
        escalation_cases = [
            {
                "user_id": "vip_customer_001",
                "message": "This is completely unacceptable! I've been a premium customer for 3 years and my data is completely gone. I demand to speak to a manager immediately!",
                "priority": "High"
            },
            {
                "user_id": "enterprise_client",
                "message": "Our entire team of 500 users cannot access the system. This is costing us thousands of dollars per hour. We need immediate assistance.",
                "priority": "Critical"
            },
            {
                "user_id": "security_concern",
                "message": "I think my account has been hacked. I see login attempts from countries I've never been to and my settings have been changed.",
                "priority": "Security"
            }
        ]
        
        for case in escalation_cases:
            print(f"\n🚨 {case['priority']} Priority Case")
            print(f"Customer: {case['user_id']}")
            print(f"Issue: {case['message']}")
            
            response = client.support_request(
                "business.helpdesk_agent",
                case['message'],
                user_id=case['user_id']
            )
            
            print(f"Agent Response: {response.response}")
            
            # Check if escalation is recommended
            if any(keyword in response.response.lower() for keyword in ['escalate', 'manager', 'supervisor', 'urgent']):
                print("🔺 ESCALATION RECOMMENDED")
            else:
                print("✅ Handled at first level")


def support_analytics():
    """Example of gathering support analytics."""
    print("\n📊 Support Analytics")
    print("=" * 40)
    
    with AgentsAPIClient("http://localhost:8000") as client:
        # Get agent health and performance
        health = client.get_agent_health("business.helpdesk_agent")
        print(f"Agent Status: {health.get('status', 'Unknown')}")
        
        # Get overall system stats
        try:
            stats = client.get_stats()
            print(f"Total Agents: {stats.get('total_agents', 0)}")
            print(f"Active Instances: {stats.get('active_instances', 0)}")
        except Exception as e:
            print(f"Stats unavailable: {e}")


def main():
    """Run all customer support examples."""
    print("🎧 AI Agents Library - Customer Support Examples")
    print("=" * 55)
    
    # Check if API server is running
    try:
        with AgentsAPIClient("http://localhost:8000") as client:
            health = client.get_health()
            print(f"✅ API Server Status: {health['status']}")
            
            # Check if helpdesk agent is available
            agents = client.list_agents()
            helpdesk_available = any(
                agent.agent_id == "business.helpdesk_agent" 
                for agent in agents.agents
            )
            
            if not helpdesk_available:
                print("❌ Helpdesk agent not available")
                return
            else:
                print("✅ Helpdesk agent available")
                
    except Exception as e:
        print(f"❌ API Server not available: {e}")
        print("💡 Start the server with: python -m src.api.main")
        return
    
    # Run examples
    basic_support_requests()
    
    # Run async example
    asyncio.run(concurrent_support_handling())
    
    escalation_scenarios()
    support_analytics()
    
    print("\n✅ Customer support examples completed!")


if __name__ == "__main__":
    main()

