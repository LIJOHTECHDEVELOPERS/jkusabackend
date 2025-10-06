from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    user_auth, 
    admin_auth, 
    admin_announcement, 
    admin_leadership, 
    admin_event, 
    admin_news,
    admin_gallery  # NEW IMPORT
)
from app.routers.admin_announcement import public_router as public_announcement_router
from app.routers.admin_news import public_news_router
from app.routers.admin_event import public_event_router
from app.routers.admin_leadership import public_leadership_router
from app.routers.admin_gallery import public_gallery_router  # NEW IMPORT
from app.database import engine, Base
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="CMSystem we are building")

# Enable CORS
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://digikenya.co.ke",
    "http://localhost:8081",
    "https://dashboard.jkusa.org",
    "https://jkusa.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("Origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# Custom exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("Origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(user_auth.router)
app.include_router(admin_auth.router)
app.include_router(admin_announcement.router)
app.include_router(public_announcement_router)
app.include_router(admin_leadership.router)
app.include_router(public_leadership_router)
app.include_router(admin_event.router)
app.include_router(public_event_router)
app.include_router(admin_news.router)
app.include_router(public_news_router)
app.include_router(admin_gallery.router)  # NEW ROUTER
app.include_router(public_gallery_router)  # NEW ROUTER

@app.get("/")
def read_root():
    logger.debug("Root endpoint accessed")
    return {"message": "JKUSA CMS Backend is running."}