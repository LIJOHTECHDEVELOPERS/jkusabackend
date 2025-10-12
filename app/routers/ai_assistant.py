## Updated AI Script with Integration for All Endpoints

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
from app.models.news import News  # Assuming News model exists based on provided snippets

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
    Gather relevant data from database based on user query keywords. Increased limits and added more keywords for better coverage.
    Added fetching for gallery, announcements, and news to integrate with all endpoints.
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
    
    # Gather Events
    if any(keyword in query_lower for keyword in ["event", "events", "happening", "program", "schedule", "when", "upcoming", "date", "meeting"]):
        events = db.query(Event).filter(Event.is_published == True).limit(20).all()
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
    if any(keyword in query_lower for keyword in ["activity", "activities", "do", "participate", "join", "sport", "club activity"]):
        activities = db.query(Activity).filter(Activity.is_published == True).limit(20).all()
        context["activities"] = [
            {
                "title": a.title,
                "description": a.description,
                "category": a.category,
                "start_datetime": str(a.start_datetime),
                "end_datetime": str(a.end_datetime) if a.end_datetime else None,
                "location": a.location
            } for a in activities
        ]
    
    # Gather Clubs
    if any(keyword in query_lower for keyword in ["club", "clubs", "organization", "society", "join", "group", "association"]):
        clubs = db.query(Club).filter(Club.is_active == True).limit(20).all()
        context["clubs"] = [
            {
                "name": c.name,
                "description": c.description,
                "category": c.category,
                "contact": c.contact_email
            } for c in clubs
        ]
    
    # Gather Leadership
    if any(keyword in query_lower for keyword in ["leader", "leadership", "official", "president", "who is", "executive", "board"]):
        leaders = db.query(Leadership).limit(20).all()
        context["leadership"] = [
            {
                "name": l.name,
                "position": l.position,
                "campus": l.campus.value if l.campus else None,
                "category": l.category.value if l.category else None,
                "year_of_service": l.year_of_service
            } for l in leaders
        ]
    
    # Gather Resources
    if any(keyword in query_lower for keyword in ["resource", "document", "download", "file", "material", "guide", "form"]):
        resources = db.query(Resource).filter(Resource.is_published == True).limit(20).all()
        context["resources"] = [
            {
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "file_url": r.file_url
            } for r in resources
        ]
    
    # Gather Gallery
    if any(keyword in query_lower for keyword in ["gallery", "photo", "picture", "image", "album", "visual"]):
        galleries = db.query(Gallery).limit(20).all()
        context["gallery"] = [
            {
                "title": g.title,
                "description": g.description,
                "category": g.category.value if g.category else None,
                "year": g.year
            } for g in galleries
        ]
    
    # Gather Announcements
    if any(keyword in query_lower for keyword in ["announcement", "announce", "notice", "update", "bulletin"]):
        announcements = db.query(Announcement).limit(20).all()
        context["announcements"] = [
            {
                "title": a.title,
                "content": a.content,
                "date": str(a.announced_at)
            } for a in announcements
        ]
    
    # Gather News
    if any(keyword in query_lower for keyword in ["news", "article", "story", "report", "blog", "press"]):
        news_items = db.query(News).limit(20).all()
        context["news"] = [
            {
                "title": n.title,
                "content": n.content,
                "date": str(n.published_at)
            } for n in news_items
        ]
    
    return context

def build_system_prompt(context_data: dict) -> str:
    """
    Build a comprehensive system prompt with context data. Added sections for gallery, announcements, and news.
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
            prompt += f"- {activity['title']}: {activity['description']} starting {activity['start_datetime']}\n"
    
    if context_data.get("clubs"):
        prompt += "\n\nSTUDENT CLUBS & ORGANIZATIONS:\n"
        for club in context_data["clubs"]:
            prompt += f"- {club['name']}: {club['description']} (Contact: {club['contact']})\n"
    
    if context_data.get("leadership"):
        prompt += "\n\nJKUSA LEADERSHIP:\n"
        for leader in context_data["leadership"]:
            campus_info = f" - {leader['campus']}" if leader['campus'] else ""
            prompt += f"- {leader['name']}: {leader['position']}{campus_info} ({leader['year_of_service']})\n"
    
    if context_data.get("resources"):
        prompt += "\n\nAVAILABLE RESOURCES:\n"
        for resource in context_data["resources"]:
            prompt += f"- {resource['title']}: {resource['description']}\n"
    
    if context_data.get("gallery"):
        prompt += "\n\nGALLERY ITEMS:\n"
        for gallery in context_data["gallery"]:
            prompt += f"- {gallery['title']}: {gallery['description']} ({gallery['year']})\n"
    
    if context_data.get("announcements"):
        prompt += "\n\nANNOUNCEMENTS:\n"
        for ann in context_data["announcements"]:
            prompt += f"- {ann['title']}: {ann['content']} on {ann['date']}\n"
    
    if context_data.get("news"):
        prompt += "\n\nNEWS ARTICLES:\n"
        for news in context_data["news"]:
            prompt += f"- {news['title']}: {news['content']} on {news['date']}\n"
    
    return prompt

def get_sources_from_context(context_data: dict) -> List[str]:
    """
    Extract source references from context data. Added for gallery, announcements, and news.
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
    if context_data.get("gallery"):
        sources.append("JKUSA Gallery Database")
    if context_data.get("announcements"):
        sources.append("JKUSA Announcements Database")
    if context_data.get("news"):
        sources.append("JKUSA News Database")
    
    return sources if sources else ["JKUSA General Information"]

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_message: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    Chat endpoint that uses Google AI to answer questions about JKUAT/JKUSA.
    Enhanced error handling to prevent generic 500 errors.
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
        
        # Initialize Gemini model (corrected model name if needed; assuming 'gemini-1.5-flash' is intended)
        model = genai.GenerativeModel('gemini-1.5-flash')  # Updated to valid model name to prevent errors
        
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
        
        # Add conversation history if provided (limit to last 5 to prevent token overflow)
        for msg in chat_message.conversation_history[-5:]:
            conversation_parts.append({
                "role": msg.get("role", "user"),
                "parts": [msg.get("content", "")]
            })
        
        # Add current message
        conversation_parts.append({
            "role": "user",
            "parts": [chat_message.message]
        })
        
        # Generate response with error handling
        try:
            chat = model.start_chat(history=conversation_parts[:-1])
            response = chat.send_message(chat_message.message)
        except genai.types.generation_types.GenerationError as gen_err:
            logger.error(f"Google AI generation error: {str(gen_err)}")
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable. Please try again later.")
        except Exception as ai_err:
            logger.error(f"Unexpected AI error: {str(ai_err)}")
            raise HTTPException(status_code=500, detail=f"Error generating AI response: {str(ai_err)}")
        
        # Get sources
        sources = get_sources_from_context(context_data)
        
        return ChatResponse(
            response=response.text,
            sources=sources,
            timestamp=datetime.now()
        )
        
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in AI chat: {str(e)}")
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
        "service": "Google AI (Gemini 1.5 Flash)",
        "model": "gemini-1.5-flash",
        "message": "AI Assistant is ready" if GOOGLE_AI_API_KEY else "Please configure GOOGLE_AI_API_KEY"
    }