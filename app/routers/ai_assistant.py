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
from app.models.announcement import Announcement

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
    Gather relevant data from database based on user query keywords.
    Added try-except blocks to prevent crashes from missing models or fields.
    """
    context = {
        "events": [],
        "activities": [],
        "clubs": [],
        "leadership": [],
        "resources": [],
        "gallery": [],
        "announcements": [],
        "news": []
    }
    
    query_lower = user_query.lower()
    
    try:
        # Gather Events
        if any(keyword in query_lower for keyword in ["event", "events", "happening", "program", "schedule", "when", "upcoming", "date", "meeting"]):
            events = db.query(Event).filter(Event.is_published == True).limit(10).all()
            context["events"] = [
                {
                    "title": getattr(e, 'title', 'N/A'),
                    "description": getattr(e, 'description', ''),
                    "date": str(getattr(e, 'event_date', '')),
                    "location": getattr(e, 'location', ''),
                    "category": getattr(e, 'category', '')
                } for e in events
            ]
    except Exception as e:
        logger.warning(f"Error fetching events: {str(e)}")
    
    try:
        # Gather Activities
        if any(keyword in query_lower for keyword in ["activity", "activities", "do", "participate", "join", "sport", "club activity"]):
            activities = db.query(Activity).filter(getattr(Activity, 'is_published', True) == True).limit(10).all()
            context["activities"] = [
                {
                    "title": getattr(a, 'title', 'N/A'),
                    "description": getattr(a, 'description', ''),
                    "category": getattr(a, 'category', ''),
                    "start_datetime": str(getattr(a, 'start_datetime', '')),
                    "location": getattr(a, 'location', '')
                } for a in activities
            ]
    except Exception as e:
        logger.warning(f"Error fetching activities: {str(e)}")
    
    try:
        # Gather Clubs
        if any(keyword in query_lower for keyword in ["club", "clubs", "organization", "society", "join", "group", "association"]):
            clubs = db.query(Club).filter(getattr(Club, 'is_active', True) == True).limit(10).all()
            context["clubs"] = [
                {
                    "name": getattr(c, 'name', 'N/A'),
                    "description": getattr(c, 'description', ''),
                    "category": getattr(c, 'category', ''),
                    "contact": getattr(c, 'contact_email', '')
                } for c in clubs
            ]
    except Exception as e:
        logger.warning(f"Error fetching clubs: {str(e)}")
    
    try:
        # Gather Leadership
        if any(keyword in query_lower for keyword in ["leader", "leadership", "official", "president", "who is", "executive", "board"]):
            leaders = db.query(Leadership).limit(10).all()
            context["leadership"] = [
                {
                    "name": getattr(l, 'name', 'N/A'),
                    "position": getattr(l, 'position', ''),
                    "campus": getattr(l, 'campus', None) and str(l.campus.value) or None,
                    "category": getattr(l, 'category', None) and str(l.category.value) or None,
                    "year_of_service": getattr(l, 'year_of_service', '')
                } for l in leaders
            ]
    except Exception as e:
        logger.warning(f"Error fetching leadership: {str(e)}")
    
    try:
        # Gather Resources
        if any(keyword in query_lower for keyword in ["resource", "document", "download", "file", "material", "guide", "form"]):
            resources = db.query(Resource).filter(getattr(Resource, 'is_published', True) == True).limit(10).all()
            context["resources"] = [
                {
                    "title": getattr(r, 'title', 'N/A'),
                    "description": getattr(r, 'description', ''),
                    "category": getattr(r, 'category', ''),
                    "file_url": getattr(r, 'file_url', '') or getattr(r, 'pdf_url', '')
                } for r in resources
            ]
    except Exception as e:
        logger.warning(f"Error fetching resources: {str(e)}")
    
    try:
        # Gather Gallery
        if any(keyword in query_lower for keyword in ["gallery", "photo", "picture", "image", "album", "visual"]):
            galleries = db.query(Gallery).limit(10).all()
            context["gallery"] = [
                {
                    "title": getattr(g, 'title', 'N/A'),
                    "description": getattr(g, 'description', ''),
                    "category": getattr(g, 'category', None) and str(g.category.value) or None,
                    "year": getattr(g, 'year', '')
                } for g in galleries
            ]
    except Exception as e:
        logger.warning(f"Error fetching gallery: {str(e)}")
    
    try:
        # Gather Announcements
        if any(keyword in query_lower for keyword in ["announcement", "announce", "notice", "update", "bulletin"]):
            announcements = db.query(Announcement).limit(10).all()
            context["announcements"] = [
                {
                    "title": getattr(a, 'title', 'N/A'),
                    "content": getattr(a, 'content', ''),
                    "date": str(getattr(a, 'announced_at', ''))
                } for a in announcements
            ]
    except Exception as e:
        logger.warning(f"Error fetching announcements: {str(e)}")
    
    return context

def build_system_prompt(context_data: dict) -> str:
    """Build a comprehensive system prompt with context data."""
    prompt = """You are JKUSA AI Assistant, an official virtual assistant for JKUAT Students' Association (JKUSA) 
at Jomo Kenyatta University of Agriculture and Technology (JKUAT).

STRICT GUIDELINES:
1. You ONLY provide information about JKUAT and JKUSA
2. You MUST NOT answer questions about other universities or student organizations
3. If asked about non-JKUAT/JKUSA topics, politely redirect: "I can only help with JKUAT and JKUSA information. How can I assist you with our university?"
4. Base your answers ONLY on the provided context data
5. If information is not in the context, say: "I don't have that specific information right now, but I can help with other JKUSA details!"
6. Be helpful, friendly, and professional
7. Keep responses concise but informative
8. Mention sources when providing specific information

ABOUT JKUAT:
- Jomo Kenyatta University of Agriculture and Technology
- Located in Juja, Kiambu County, Kenya
- Leading public university focused on agriculture, engineering, technology, and sciences
- Multiple campuses including Main Campus (Juja), Karen Campus, and others

ABOUT JKUSA:
- JKUAT Students' Association - official student government
- Represents all JKUAT students across campuses
- Organizes events, activities, leadership, and student services

"""
    
    # Add context data safely
    sections_added = []
    
    if context_data.get("events") and len(context_data["events"]) > 0:
        prompt += "\n\n🗓️ UPCOMING EVENTS:\n"
        for event in context_data["events"][:3]:
            prompt += f"- {event['title']}: {event['description']} ({event['date']}, {event['location']})\n"
        sections_added.append("Events")
    
    if context_data.get("activities") and len(context_data["activities"]) > 0:
        prompt += "\n\n🎯 STUDENT ACTIVITIES:\n"
        for activity in context_data["activities"][:3]:
            prompt += f"- {activity['title']}: {activity['description']}\n"
        sections_added.append("Activities")
    
    if context_data.get("clubs") and len(context_data["clubs"]) > 0:
        prompt += "\n\n🏛️ STUDENT CLUBS & ORGANIZATIONS:\n"
        for club in context_data["clubs"][:5]:
            prompt += f"- {club['name']}: {club['description']}\n"
        sections_added.append("Clubs")
    
    if context_data.get("leadership") and len(context_data["leadership"]) > 0:
        prompt += "\n\n👥 CURRENT LEADERSHIP:\n"
        for leader in context_data["leadership"][:5]:
            campus = leader['campus'] or "Main Campus"
            prompt += f"- {leader['name']} ({leader['position']}) - {campus}\n"
        sections_added.append("Leadership")
    
    if context_data.get("resources") and len(context_data["resources"]) > 0:
        prompt += "\n\n📚 AVAILABLE RESOURCES:\n"
        for resource in context_data["resources"][:3]:
            prompt += f"- {resource['title']}: {resource['description']}\n"
        sections_added.append("Resources")
    
    if context_data.get("announcements") and len(context_data["announcements"]) > 0:
        prompt += "\n\n📢 RECENT ANNOUNCEMENTS:\n"
        for ann in context_data["announcements"][:2]:
            prompt += f"- {ann['title']} ({ann['date']})\n"
        sections_added.append("Announcements")
    
    if not sections_added:
        prompt += "\n\nNo specific context data available for this query."
    
    prompt += "\n\nAlways respond based on this context and JKUSA guidelines."
    return prompt

def get_sources_from_context(context_data: dict) -> List[str]:
    """Extract source references from context data."""
    sources = set()
    
    if context_data.get("events"):
        sources.add("JKUSA Events Database")
    if context_data.get("activities"):
        sources.add("JKUSA Activities Database")
    if context_data.get("clubs"):
        sources.add("JKUSA Clubs & Organizations Database")
    if context_data.get("leadership"):
        sources.add("JKUSA Leadership Directory")
    if context_data.get("resources"):
        sources.add("JKUSA Resources Library")
    if context_data.get("announcements"):
        sources.add("JKUSA Announcements")
    
    return list(sources) if sources else ["JKUSA General Information"]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_message: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    Chat endpoint with robust error handling for Google Generative AI.
    """
    if not GOOGLE_AI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Google AI API key not configured."
        )
    
    try:
        # Gather context data from database
        logger.info(f"Processing AI query: {chat_message.message[:100]}...")
        context_data = gather_context_data(db, chat_message.message)
        
        # Build system prompt
        system_prompt = build_system_prompt(context_data)
        
        # Initialize model with safety settings - FIXED VERSION
        try:
            # Correct way to create GenerationConfig
            generation_config = genai.GenerationConfig(
                max_output_tokens=1000,
                temperature=0.7
            )
            
            # Correct way to set safety settings
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            model = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            logger.info("Model initialized successfully with generation config and safety settings")
        except Exception as model_err:
            logger.warning(f"Failed to initialize model with config: {str(model_err)}, using basic model")
            # Fallback to basic model initialization
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Prepare the prompt
        full_prompt = f"{system_prompt}\n\nUSER QUESTION: {chat_message.message}\n\nPlease provide a helpful response based on the JKUSA context above."
        
        # Generate response with comprehensive error handling
        try:
            response = model.generate_content(full_prompt)
            ai_response = response.text
            logger.info("AI response generated successfully")
        except Exception as ai_err:
            error_msg = str(ai_err).lower()
            
            # Handle specific error types
            if "block" in error_msg or "safety" in error_msg:
                logger.warning("AI response blocked due to safety filters")
                ai_response = "I'm sorry, I can't respond to that query due to content guidelines. How else can I help with JKUSA information?"
            elif "quota" in error_msg or "rate" in error_msg:
                logger.error("API quota exceeded")
                ai_response = "I'm currently experiencing high demand. Please try again in a moment."
            elif "invalid" in error_msg and "api" in error_msg:
                logger.error("Invalid API key")
                ai_response = "There's a configuration issue. Please contact JKUSA support."
            else:
                logger.error(f"AI generation failed: {str(ai_err)}")
                ai_response = "I'm experiencing technical difficulties right now. Please try again later or contact JKUSA support for assistance."
        
        # Get sources
        sources = get_sources_from_context(context_data)
        
        logger.info(f"AI response generated successfully. Sources: {sources}")
        
        return ChatResponse(
            response=ai_response,
            sources=sources,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critical error in AI chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing AI request. Please try again."
        )

@router.get("/health")
async def ai_health_check():
    """Health check endpoint."""
    model_available = False
    error_details = None
    
    try:
        # Test model availability
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        # Try a simple generation to verify it works
        test_response = model.generate_content("Hello")
        model_available = True
    except Exception as e:
        error_details = str(e)
        logger.warning(f"Model test failed: {error_details}")
    
    return {
        "status": "healthy" if GOOGLE_AI_API_KEY and model_available else "degraded",
        "service": "Google AI (Gemini 2.0 Flash)",
        "model_available": model_available,
        "api_key_configured": bool(GOOGLE_AI_API_KEY),
        "error": error_details if not model_available else None,
        "message": "AI Assistant ready" if GOOGLE_AI_API_KEY and model_available else "Configuration issues detected"
    }