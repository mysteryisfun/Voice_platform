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
        
        system_prompt = """You are an AI assistant helping to onboard businesses for voice agent creation.
        You need to ask the right questions to understand their business and configure a voice agent.
        
        Start with fundamental business information. Ask ONE clear, specific question.
        Keep questions conversational and easy to answer.
        
        Focus areas: company basics, industry, target audience, voice agent purpose.
        """
        
        user_prompt = f"""Generate the first question to start business onboarding for voice agent creation.
        
        Initial context: {initial_context or 'No additional context provided'}
        
        Return only the question, no explanations."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            # Fallback question
            return "What is your company name and what industry are you in?"
    
    def generate_next_question(self, qa_history: List[Dict], current_count: int) -> Dict[str, Any]:
        """Generate next question based on conversation history"""
        
        system_prompt = """You are an AI assistant conducting a business onboarding interview for voice agent creation.

        Based on the conversation history, generate the NEXT logical question to gather information for:
        1. Business basics (company, industry, services)
        2. Target audience and customers  
        3. Voice agent purpose (support, sales, booking, info)
        4. Agent personality and tone preferences
        5. Business hours and availability
        6. Specific terminology or compliance needs

        Rules:
        - Ask ONE specific question
        - Build on previous answers
        - Avoid repeating covered topics
        - Keep questions conversational
        - Complete after 8-12 meaningful questions
        - If sufficient info gathered, indicate completion

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

Current question count: {current_count}

Generate the next question or indicate completion. Return valid JSON only."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.7
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
