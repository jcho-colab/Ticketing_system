from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
import hashlib
from enum import Enum
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

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="Ticketing System API", version="1.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    END_USER = "end_user"
    SUPPORT_AGENT = "support_agent"
    TEAM_LEAD = "team_lead"
    ADMIN = "admin"

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
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: UserRole
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: UserRole = UserRole.END_USER

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    created_at: datetime
    is_active: bool

class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., max_length=120)
    description: str
    priority: TicketPriority
    category: TicketCategory
    status: TicketStatus = TicketStatus.OPEN
    created_by: str  # user_id
    assigned_to: Optional[str] = None  # user_id
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

class TicketCreate(BaseModel):
    title: str = Field(..., max_length=120)
    description: str
    priority: TicketPriority
    category: TicketCategory

class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = None
    priority: Optional[TicketPriority] = None
    category: Optional[TicketCategory] = None
    status: Optional[TicketStatus] = None
    assigned_to: Optional[str] = None

class TicketResponse(BaseModel):
    id: str
    title: str
    description: str
    priority: TicketPriority
    category: TicketCategory
    status: TicketStatus
    created_by: str
    created_by_name: str
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    user_id: str
    user_name: str
    content: str
    is_internal: bool = False  # Internal notes vs customer-visible comments
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CommentCreate(BaseModel):
    content: str
    is_internal: bool = False

class DashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    critical_tickets: int
    high_priority_tickets: int
    tickets_by_category: dict
    avg_resolution_time_hours: float

# Utility Functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password

def create_jwt_token(user_id: str, user_role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": user_role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user_role = payload.get("role")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {"id": user_id, "role": user_role, "user_data": user}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_roles: List[UserRole]):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in [role.value for role in required_roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Authentication Routes
@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role
    )
    
    # Store user with hashed password
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create JWT token
    token = create_jwt_token(user.id, user.role.value)
    
    return {
        "token": token,
        "user": UserResponse(**user.dict())
    }

@api_router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="Account deactivated")
    
    token = create_jwt_token(user["id"], user["role"])
    
    return {
        "token": token,
        "user": UserResponse(**{k: v for k, v in user.items() if k != "password"})
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    user_data = current_user["user_data"]
    return UserResponse(**{k: v for k, v in user_data.items() if k != "password"})

# Ticket Routes
@api_router.post("/tickets", response_model=TicketResponse)
async def create_ticket(ticket_data: TicketCreate, current_user: dict = Depends(get_current_user)):
    ticket = Ticket(
        **ticket_data.dict(),
        created_by=current_user["id"]
    )
    
    await db.tickets.insert_one(ticket.dict())
    
    # Get creator info for response
    creator = await db.users.find_one({"id": current_user["id"]})
    
    response_data = ticket.dict()
    response_data["created_by_name"] = creator["name"]
    response_data["assigned_to_name"] = None

    # Send email notification
    try:
        await send_email(
            subject=f"Ticket Created: {ticket.title}",
            recipients=[creator["email"]],
            template_body=f"""
            <p>Hi {creator['name']},</p>
            <p>Your ticket with the title "<strong>{ticket.title}</strong>" has been successfully created.</p>
            <p>You will be notified of any updates.</p>
            <p>Thank you!</p>
            """
        )
    except Exception as e:
        logger.error(f"Error sending email: {e}")

    return TicketResponse(**response_data)

@api_router.get("/tickets", response_model=List[TicketResponse])
async def get_tickets(
    status: Optional[TicketStatus] = None,
    category: Optional[TicketCategory] = None,
    priority: Optional[TicketPriority] = None,
    assigned_to_me: bool = False,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    
    # Role-based filtering
    if current_user["role"] == UserRole.END_USER.value:
        query["created_by"] = current_user["id"]
    
    # Apply filters
    if status:
        query["status"] = status.value
    if category:
        query["category"] = category.value
    if priority:
        query["priority"] = priority.value
    if assigned_to_me:
        query["assigned_to"] = current_user["id"]
    
    tickets = await db.tickets.find(query).sort("created_at", -1).to_list(1000)
    
    # Enrich with user names
    user_ids = set()
    for ticket in tickets:
        user_ids.add(ticket["created_by"])
        if ticket.get("assigned_to"):
            user_ids.add(ticket["assigned_to"])
    
    users = {user["id"]: user for user in await db.users.find({"id": {"$in": list(user_ids)}}).to_list(1000)}
    
    response_tickets = []
    for ticket in tickets:
        ticket_response = ticket.copy()
        ticket_response["created_by_name"] = users.get(ticket["created_by"], {}).get("name", "Unknown")
        ticket_response["assigned_to_name"] = users.get(ticket.get("assigned_to"), {}).get("name") if ticket.get("assigned_to") else None
        response_tickets.append(TicketResponse(**ticket_response))
    
    return response_tickets

@api_router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check permissions
    if (current_user["role"] == UserRole.END_USER.value and 
        ticket["created_by"] != current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get user names
    creator = await db.users.find_one({"id": ticket["created_by"]})
    assignee = None
    if ticket.get("assigned_to"):
        assignee = await db.users.find_one({"id": ticket["assigned_to"]})
    
    ticket["created_by_name"] = creator["name"] if creator else "Unknown"
    ticket["assigned_to_name"] = assignee["name"] if assignee else None
    
    return TicketResponse(**ticket)

@api_router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str, 
    ticket_update: TicketUpdate,
    current_user: dict = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.TEAM_LEAD, UserRole.ADMIN]))
):
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    update_data = {k: v for k, v in ticket_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Handle status changes
    if "status" in update_data:
        if update_data["status"] == TicketStatus.RESOLVED.value:
            update_data["resolved_at"] = datetime.utcnow()
        elif update_data["status"] == TicketStatus.CLOSED.value:
            update_data["closed_at"] = datetime.utcnow()
    
    await db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
    
    # Get updated ticket with user names
    updated_ticket = await db.tickets.find_one({"id": ticket_id})
    creator = await db.users.find_one({"id": updated_ticket["created_by"]})
    assignee = None
    if updated_ticket.get("assigned_to"):
        assignee = await db.users.find_one({"id": updated_ticket["assigned_to"]})
    
    updated_ticket["created_by_name"] = creator["name"] if creator else "Unknown"
    updated_ticket["assigned_to_name"] = assignee["name"] if assignee else None

    # Send email notification if status changed
    if "status" in update_data and creator:
        try:
            await send_email(
                subject=f"Ticket Status Updated: {updated_ticket['title']}",
                recipients=[creator["email"]],
                template_body=f"""
                <p>Hi {creator['name']},</p>
                <p>The status of your ticket "<strong>{updated_ticket['title']}</strong>" has been updated to <strong>{updated_ticket['status']}</strong>.</p>
                <p>Thank you!</p>
                """
            )
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    return TicketResponse(**updated_ticket)

# Comment Routes
@api_router.post("/tickets/{ticket_id}/comments", response_model=Comment)
async def add_comment(
    ticket_id: str,
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check permissions for internal comments
    if comment_data.is_internal and current_user["role"] == UserRole.END_USER.value:
        raise HTTPException(status_code=403, detail="Cannot create internal comments")
    
    comment = Comment(
        ticket_id=ticket_id,
        user_id=current_user["id"],
        user_name=current_user["user_data"]["name"],
        content=comment_data.content,
        is_internal=comment_data.is_internal
    )
    
    await db.comments.insert_one(comment.dict())

    # Send email notification
    try:
        creator = await db.users.find_one({"id": ticket["created_by"]})
        recipients = []
        if creator:
            recipients.append(creator["email"])

        if ticket.get("assigned_to"):
            assignee = await db.users.find_one({"id": ticket["assigned_to"]})
            if assignee and assignee["email"] not in recipients:
                recipients.append(assignee["email"])
        
        if recipients:
            await send_email(
                subject=f"New Comment on Ticket: {ticket['title']}",
                recipients=recipients,
                template_body=f"""
                <p>A new comment has been added to the ticket "<strong>{ticket['title']}</strong>".</p>
                <p><strong>Comment:</strong></p>
                <p>{comment.content}</p>
                <p>Thank you!</p>
                """
            )
    except Exception as e:
        logger.error(f"Error sending email: {e}")

    return comment

@api_router.get("/tickets/{ticket_id}/comments", response_model=List[Comment])
async def get_comments(ticket_id: str, current_user: dict = Depends(get_current_user)):
    ticket = await db.tickets.find_one({"id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Filter internal comments for end users
    query = {"ticket_id": ticket_id}
    if current_user["role"] == UserRole.END_USER.value:
        query["is_internal"] = False
    
    comments = await db.comments.find(query).sort("created_at", 1).to_list(1000)
    return [Comment(**comment) for comment in comments]

# User Management Routes (Admin only)
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(require_role([UserRole.ADMIN, UserRole.TEAM_LEAD]))):
    users = await db.users.find().to_list(1000)
    return [UserResponse(**{k: v for k, v in user.items() if k != "password"}) for user in users]

# Dashboard Routes
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(require_role([UserRole.SUPPORT_AGENT, UserRole.TEAM_LEAD, UserRole.ADMIN]))):
    # Get ticket counts by status
    total_tickets = await db.tickets.count_documents({})
    open_tickets = await db.tickets.count_documents({"status": TicketStatus.OPEN.value})
    in_progress_tickets = await db.tickets.count_documents({"status": TicketStatus.IN_PROGRESS.value})
    resolved_tickets = await db.tickets.count_documents({"status": TicketStatus.RESOLVED.value})
    closed_tickets = await db.tickets.count_documents({"status": TicketStatus.CLOSED.value})
    
    # Get priority counts
    critical_tickets = await db.tickets.count_documents({"priority": TicketPriority.CRITICAL.value})
    high_priority_tickets = await db.tickets.count_documents({"priority": TicketPriority.HIGH.value})
    
    # Get tickets by category
    technical_tickets = await db.tickets.count_documents({"category": TicketCategory.TECHNICAL.value})
    billing_tickets = await db.tickets.count_documents({"category": TicketCategory.BILLING.value})
    general_tickets = await db.tickets.count_documents({"category": TicketCategory.GENERAL.value})
    
    tickets_by_category = {
        "technical": technical_tickets,
        "billing": billing_tickets,
        "general": general_tickets
    }
    
    # Calculate average resolution time
    resolved_tickets_with_times = await db.tickets.find({
        "status": {"$in": [TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]},
        "resolved_at": {"$exists": True}
    }).to_list(1000)
    
    avg_resolution_time_hours = 0
    if resolved_tickets_with_times:
        total_hours = 0
        for ticket in resolved_tickets_with_times:
            created_at = ticket["created_at"]
            resolved_at = ticket["resolved_at"]
            diff = resolved_at - created_at
            total_hours += diff.total_seconds() / 3600
        avg_resolution_time_hours = total_hours / len(resolved_tickets_with_times)
    
    return DashboardStats(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
        closed_tickets=closed_tickets,
        critical_tickets=critical_tickets,
        high_priority_tickets=high_priority_tickets,
        tickets_by_category=tickets_by_category,
        avg_resolution_time_hours=round(avg_resolution_time_hours, 2)
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()