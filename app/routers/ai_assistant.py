"""
AI Assistant Router for JKUAT/JKUSA Information
Connects to Google AI API and gathers information from existing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import os
from datetime import datetime
import logging

from app.database import get_db
from app.models.event import Event
from app.models.activity import Activity
from app.models.club import Club
from app.models.leadership import Leadership
from app.models.gallery import Gallery
from app.models.resource import Resource

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

# Configure Google AI
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
if GOOGLE_AI_API_KEY:
    genai.configure(api_key=GOOGLE_AI_API_KEY)

class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    timestamp: datetime

def gather_context_data(db: Session, user_query: str) -> dict:
    """
    Gather relevant data from database based on user query keywords
    """
    context = {
        "events": [],
        "activities": [],
        "clubs": [],
        "leadership": [],
        "resources": [],
        "gallery": []
    }
    
    query_lower = user_query.lower()
    
    # Gather Events
    if any(keyword in query_lower for keyword in ["event", "happening", "program", "schedule", "when"]):
        events = db.query(Event).filter(Event.is_published == True).limit(5).all()
        context["events"] = [
            {
                "title": e.title,
                "description": e.description,
                "date": str(e.event_date),
                "location": e.location,
                "category": e.category
            } for e in events
        ]
    
    # Gather Activities
    if any(keyword in query_lower for keyword in ["activity", "activities", "do", "participate"]):
        activities = db.query(Activity).filter(Activity.is_published == True).limit(5).all()
        context["activities"] = [
            {
                "title": a.title,
                "description": a.description,
                "category": a.category
            } for a in activities
        ]
    
    # Gather Clubs
    if any(keyword in query_lower for keyword in ["club", "clubs", "organization", "society", "join"]):
        clubs = db.query(Club).filter(Club.is_active == True).limit(10).all()
        context["clubs"] = [
            {
                "name": c.name,
                "description": c.description,
                "category": c.category,
                "contact": c.contact_email
            } for c in clubs
        ]
    
    # Gather Leadership
    if any(keyword in query_lower for keyword in ["leader", "leadership", "official", "president", "who is"]):
        leaders = db.query(Leadership).limit(10).all()
        context["leadership"] = [
            {
                "name": l.name,
                "position": l.position,
                "campus": l.campus.value if l.campus else None,
                "category": l.category.value if l.category else None
            } for l in leaders
        ]
    
    # Gather Resources
    if any(keyword in query_lower for keyword in ["resource", "document", "download", "file", "material"]):
        resources = db.query(Resource).filter(Resource.is_published == True).limit(5).all()
        context["resources"] = [
            {
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "file_url": r.file_url
            } for r in resources
        ]
    
    return context

def build_system_prompt(context_data: dict) -> str:
    """
    Build a comprehensive system prompt with context data
    """
    prompt = """You are JKUSA AI Assistant, an official virtual assistant for JKUAT Students' Association (JKUSA) 
at Jomo Kenyatta University of Agriculture and Technology (JKUAT).

STRICT GUIDELINES:
1. You ONLY provide information about JKUAT and JKUSA
2. You MUST NOT answer questions about other universities or student organizations
3. If asked about non-JKUAT/JKUSA topics, politely redirect the conversation
4. Base your answers ONLY on the provided context data
5. If information is not in the context, say you don't have that specific information
6. Be helpful, friendly, and professional
7. Use the data sources provided to give accurate, up-to-date information

ABOUT JKUAT:
- Jomo Kenyatta University of Agriculture and Technology
- Located in Juja, Kiambu County, Kenya
- One of Kenya's leading public universities
- Focus on agriculture, engineering, technology, and sciences

ABOUT JKUSA:
- JKUAT Students' Association
- Official student organization representing JKUAT students
- Organizes events, activities, and provides student services
- Has multiple campuses: Main Campus, City Campus, Karen Campus, and others

"""
    
    # Add context data
    if context_data.get("events"):
        prompt += "\n\nUPCOMING EVENTS:\n"
        for event in context_data["events"]:
            prompt += f"- {event['title']}: {event['description']} on {event['date']} at {event['location']}\n"
    
    if context_data.get("activities"):
        prompt += "\n\nSTUDENT ACTIVITIES:\n"
        for activity in context_data["activities"]:
            prompt += f"- {activity['title']}: {activity['description']}\n"
    
    if context_data.get("clubs"):
        prompt += "\n\nSTUDENT CLUBS & ORGANIZATIONS:\n"
        for club in context_data["clubs"]:
            prompt += f"- {club['name']}: {club['description']} (Contact: {club['contact']})\n"
    
    if context_data.get("leadership"):
        prompt += "\n\nJKUSA LEADERSHIP:\n"
        for leader in context_data["leadership"]:
            campus_info = f" - {leader['campus']}" if leader['campus'] else ""
            prompt += f"- {leader['name']}: {leader['position']}{campus_info}\n"
    
    if context_data.get("resources"):
        prompt += "\n\nAVAILABLE RESOURCES:\n"
        for resource in context_data["resources"]:
            prompt += f"- {resource['title']}: {resource['description']}\n"
    
    return prompt

def get_sources_from_context(context_data: dict) -> List[str]:
    """
    Extract source references from context data
    """
    sources = []
    
    if context_data.get("events"):
        sources.append("JKUSA Events Database")
    if context_data.get("activities"):
        sources.append("JKUSA Activities Database")
    if context_data.get("clubs"):
        sources.append("JKUSA Clubs & Organizations Database")
    if context_data.get("leadership"):
        sources.append("JKUSA Leadership Directory")
    if context_data.get("resources"):
        sources.append("JKUSA Resources Library")
    
    return sources if sources else ["JKUSA General Information"]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_message: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    Chat endpoint that uses Google AI to answer questions about JKUAT/JKUSA
    """
    if not GOOGLE_AI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Google AI API key not configured. Please set GOOGLE_AI_API_KEY environment variable."
        )
    
    try:
        # Gather context data from database
        context_data = gather_context_data(db, chat_message.message)
        
        # Build system prompt with context
        system_prompt = build_system_prompt(context_data)
        
        # Initialize Gemini model (using latest stable model)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Build conversation history
        conversation_parts = []
        
        # Add system context
        conversation_parts.append({
            "role": "user",
            "parts": [system_prompt]
        })
        conversation_parts.append({
            "role": "model",
            "parts": ["I understand. I am JKUSA AI Assistant and will only provide information about JKUAT and JKUSA based on the provided context."]
        })
        
        # Add conversation history if provided
        for msg in chat_message.conversation_history[-5:]:  # Last 5 messages
            conversation_parts.append({
                "role": msg.get("role", "user"),
                "parts": [msg.get("content", "")]
            })
        
        # Add current message
        conversation_parts.append({
            "role": "user",
            "parts": [chat_message.message]
        })
        
        # Generate response
        chat = model.start_chat(history=conversation_parts[:-1])
        response = chat.send_message(chat_message.message)
        
        # Get sources
        sources = get_sources_from_context(context_data)
        
        return ChatResponse(
            response=response.text,
            sources=sources,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing AI request: {str(e)}"
        )

@router.get("/health")
async def ai_health_check():
    """
    Check if AI service is configured and ready
    """
    return {
        "status": "healthy" if GOOGLE_AI_API_KEY else "not_configured",
        "service": "Google AI (Gemini 2.5 Flash)",
        "model": "gemini-2.5-flash",
        "message": "AI Assistant is ready" if GOOGLE_AI_API_KEY else "Please configure GOOGLE_AI_API_KEY"
    }