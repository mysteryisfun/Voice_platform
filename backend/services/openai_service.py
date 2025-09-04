"""
OpenAI service for dynamic question generation
"""
import os
from typing import List, Dict, Any
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def generate_first_question(self, initial_context: str = None) -> str:
        """Generate the first onboarding question"""
        
        # Start with a simple, direct first question - no AI needed
        return "What is your company name and what is your main business or service?"
    
    def generate_next_question(self, qa_history: List[Dict], current_count: int) -> Dict[str, Any]:
        """Generate next question based on conversation history"""
        
        # Force completion after 5 questions - we just need basics for voice agent
        if current_count >= 5:
            return {
                "question": None,
                "is_complete": True,
                "reasoning": "Sufficient information collected for voice agent creation"
            }
        
        system_prompt = """You are conducting a focused business onboarding for voice agent creation.

        Ask ONLY essential questions to create a functional voice agent:
        1. Company name and main business
        2. Primary service/product offered
        3. Target customers (who calls)
        4. Voice agent's main purpose (support, sales, booking, info)
        5. Key business hours or availability

        Rules:
        - Ask ONE specific, essential question
        - Keep questions short and direct
        - COMPLETE after 5 questions maximum
        - Focus on voice agent functionality, not business investigation
        - Do NOT ask about tone/voice style (already configured)
        - If you have enough info to create an agent, indicate completion

        Return JSON: {"question": "...", "is_complete": false, "reasoning": "why this question"}
        OR {"question": null, "is_complete": true, "reasoning": "sufficient information gathered"}
        """
        
        # Format conversation history
        conversation = "\n".join([
            f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['answer']}" 
            for i, qa in enumerate(qa_history)
        ])
        
        user_prompt = f"""Conversation so far:
{conversation}

Current question count: {current_count} of 5 maximum

Generate the next question or indicate completion. Return valid JSON only."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.3  # Lower temperature for more focused responses
            )
            
            import json
            result = json.loads(response.choices[0].message.content.strip())
            return result
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            
            # Fallback logic based on question count
            if current_count >= 8:
                return {
                    "question": None, 
                    "is_complete": True, 
                    "reasoning": "Reached minimum question threshold"
                }
            else:
                fallback_questions = [
                    "What are your main products or services?",
                    "Who is your target audience or typical customer?", 
                    "What would you want your voice agent to help customers with?",
                    "What tone should your voice agent have - professional, friendly, or casual?",
                    "What are your business hours when the agent should be available?",
                    "Are there any specific topics the agent should avoid or emphasize?"
                ]
                
                if current_count < len(fallback_questions):
                    return {
                        "question": fallback_questions[current_count],
                        "is_complete": False,
                        "reasoning": "Using fallback question due to API issue"
                    }
                else:
                    return {
                        "question": None,
                        "is_complete": True, 
                        "reasoning": "Fallback completion"
                    }
    
    def generate_enhanced_system_prompt(self, qa_history: List[Dict], agent_name: str, company_name: str, 
                                      identity_config, voice_config, tools_config) -> str:
        """Generate enhanced system prompt with full configuration"""
        
        system_prompt = f"""Generate a comprehensive system prompt for a voice agent with the following configuration:

        Agent Identity:
        - Name: {agent_name}
        - Role: {identity_config.agent_role}
        - Company: {company_name}
        - Greeting: {identity_config.greeting_message or 'Default greeting'}

        Voice & Personality:
        - Voice: {voice_config.voice_id}
        - Personality: {voice_config.personality}
        - Tone: {voice_config.tone}
        - Speaking Speed: {voice_config.speaking_speed}
        - Response Style: {voice_config.response_style}

        Available Tools:
        - {', '.join(tools_config.enabled_tools)}

        Special Instructions:
        {tools_config.special_instructions or 'None'}

        Escalation Triggers:
        {', '.join(tools_config.escalation_triggers) if tools_config.escalation_triggers else 'Standard escalation when unable to help'}

        Generate a detailed system prompt that incorporates all this information."""
        
        # Format Q&A for context
        qa_context = "\n".join([
            f"Q: {qa['question']}\nA: {qa['answer']}" 
            for qa in qa_history
        ])
        
        user_prompt = f"""Business Information from Onboarding:
{qa_context}

{system_prompt}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are creating a system prompt for a voice agent. Make it comprehensive, professional, and actionable."},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            
            # Fallback enhanced system prompt
            tools_list = ', '.join(tools_config.enabled_tools)
            greeting = identity_config.greeting_message or f"Hello! I'm {agent_name}, how can I help you today?"
            special_instructions_text = f"Special instructions: {tools_config.special_instructions}" if tools_config.special_instructions else ""
            
            return f"""You are {agent_name}, a {voice_config.personality} voice assistant for {company_name} working as a {identity_config.agent_role}.

Your role is to:
- Greet customers with: "{greeting}"
- Use a {voice_config.tone} tone with {voice_config.response_style} responses
- Provide excellent customer service

Available tools: {tools_list}

Voice characteristics:
- Speak at {voice_config.speaking_speed} speed
- Maintain {voice_config.personality} personality throughout conversations

{special_instructions_text}

Always be helpful, accurate, and professional. If you cannot help with something, {', '.join(tools_config.escalation_triggers) if tools_config.escalation_triggers else 'offer to connect them with a human representative'}."""

    def generate_system_prompt(self, qa_history: List[Dict], company_name: str) -> str:
        """Generate system prompt for the voice agent based on onboarding Q&A"""
        
        system_prompt = """Generate a comprehensive system prompt for a voice agent based on the business onboarding information.

        The prompt should:
        1. Define the agent's role and purpose
        2. Include company-specific information
        3. Set personality and tone guidelines
        4. List available tools (RAG knowledge, lead capture, appointment booking)
        5. Include conversation guidelines and boundaries
        
        Make it detailed but concise. The agent will use this as its core instructions."""
        
        # Format Q&A for context
        qa_context = "\n".join([
            f"Q: {qa['question']}\nA: {qa['answer']}" 
            for qa in qa_history
        ])
        
        user_prompt = f"""Business Information:
Company: {company_name}

Onboarding Q&A:
{qa_context}

Generate a complete system prompt for this company's voice agent."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            
            # Fallback system prompt
            return f"""You are a helpful voice assistant for {company_name}.

Your role is to:
- Answer questions about {company_name} using your knowledge base
- Capture lead information when customers are interested
- Help schedule appointments when requested
- Provide excellent customer service

Personality: Professional and helpful
Tone: Friendly but business-appropriate

Available tools:
- Knowledge retrieval from company documents
- Lead capture (name, email, phone, requirements)
- Appointment booking

Always be polite, accurate, and helpful. If you don't know something, say so and offer to connect them with a human representative."""
