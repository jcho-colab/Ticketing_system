from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime
from enum import Enum
import shutil

# Import email utilities
from email_utils import send_email
ROOT_DIR = Path(__file__).parent
from dotenv import load_dotenv
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Ticketing System API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")

# Enums
class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TicketCategory(str, Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    GENERAL = "general"

# Models
class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., max_length=120)
    description: str
    priority: TicketPriority
    category: TicketCategory
    status: TicketStatus = TicketStatus.OPEN
    created_by_email: EmailStr
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    attachments: Optional[List[str]] = None

class TicketCreate(BaseModel):
    title: str = Field(..., max_length=120)
    description: str
    priority: TicketPriority
    category: TicketCategory
    attachments: Optional[List[str]] = None
    email: EmailStr

class TicketUpdate(BaseModel):
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None
    status: Optional[TicketStatus] = None

class TicketResponse(BaseModel):
    id: str
    title: str
    description: str
    priority: TicketPriority
    category: TicketCategory
    status: TicketStatus
    created_by_email: EmailStr
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    attachments: Optional[List[str]] = None

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    user_name: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CommentCreate(BaseModel):
    content: str
    email: EmailStr

# Ticket Routes
@api_router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    title: str = Form(...),
    description: str = Form(...),
    priority: TicketPriority = Form(...),
    category: TicketCategory = Form(...),
    email: EmailStr = Form(...),
    attachments: List[UploadFile] = File([])
):
    logger.info(f"Received ticket creation request: title={title}, email={email}")
    try:
        # Handle file uploads
        attachment_paths = []
        if attachments:
            for file in attachments:
                if file.filename:
                    # Create a unique filename to avoid conflicts
                    file_extension = Path(file.filename).suffix
                    unique_filename = f"{uuid.uuid4()}{file_extension}"
                    file_path = UPLOADS_DIR / unique_filename
                    
                    # Save the file
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    
                    # Store the relative path
                    attachment_paths.append(f"uploads/{unique_filename}")
        
        ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            category=category,
            created_by_email=email,
            attachments=attachment_paths if attachment_paths else None
        )
        result = await db.tickets.insert_one(ticket.dict())
        logger.info(f"Ticket created with ID: {result.inserted_id}")
        
        # Send email confirmation
        try:
            # Format attachment list for email
            attachment_list = ""
            if attachment_paths:
                attachment_list = "<ul>"
                for path in attachment_paths:
                    filename = Path(path).name
                    attachment_list += f"<li>{filename}</li>"
                attachment_list += "</ul>"
            else:
                attachment_list = "<p>None</p>"
            
            email_body = f"""
            <h2>Ticket Created Successfully</h2>
            <p>Thank you for submitting your ticket. Here are the details:</p>
            <ul>
                <li><strong>Ticket ID:</strong> {ticket.id}</li>
                <li><strong>Title:</strong> {ticket.title}</li>
                <li><strong>Description:</strong> {ticket.description}</li>
                <li><strong>Priority:</strong> {ticket.priority.value}</li>
                <li><strong>Category:</strong> {ticket.category.value}</li>
                <li><strong>Created At:</strong> {ticket.created_at}</li>
                <li><strong>Attachments:</strong> {attachment_list}</li>
            </ul>
            <p>We will review your ticket and respond as soon as possible.</p>
            """
            
            await send_email(
                subject=f"Ticket Created: {ticket.title}",
                recipients=[email],
                template_body=email_body
            )
            logger.info(f"Email confirmation sent to {email}")
        except Exception as email_error:
            logger.error(f"Failed to send email confirmation: {email_error}", exc_info=True)
        
        return TicketResponse(**ticket.dict())
    except Exception as e:
        logger.error(f"Error creating ticket: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/tickets", response_model=List[TicketResponse])
async def get_tickets(email: EmailStr):
    tickets = await db.tickets.find({"created_by_email": email}).sort("created_at", -1).to_list(1000)
    return [TicketResponse(**ticket) for ticket in tickets]

@api_router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str):
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketResponse(**ticket)

@api_router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(ticket_id: str, ticket_update: TicketUpdate):
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    update_data = {k: v for k, v in ticket_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    if "status" in update_data:
        if update_data["status"] == TicketStatus.RESOLVED.value:
            update_data["resolved_at"] = datetime.utcnow()
        elif update_data["status"] == TicketStatus.CLOSED.value:
            update_data["closed_at"] = datetime.utcnow()
            
    await db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
    
    updated_ticket = await db.tickets.find_one({"id": ticket_id})
    return TicketResponse(**updated_ticket)

# Comment Routes
@api_router.post("/tickets/{ticket_id}/comments", response_model=Comment)
async def add_comment(ticket_id: str, comment_data: CommentCreate):
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    comment = Comment(
        ticket_id=ticket_id,
        user_name=comment_data.email,
        content=comment_data.content,
    )
    
    await db.comments.insert_one(comment.dict())
    return comment

@api_router.get("/tickets/{ticket_id}/comments", response_model=List[Comment])
async def get_comments(ticket_id: str):
    comments = await db.comments.find({"ticket_id": ticket_id}).sort("created_at", 1).to_list(1000)
    return [Comment(**comment) for comment in comments]

# Include the router in the main app
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()