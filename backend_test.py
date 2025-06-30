import requests
import unittest
import uuid
import time
from datetime import datetime

# Use the public endpoint from frontend/.env
BASE_URL = "https://3b3839d0-9706-41e4-a6c5-2e43246a5fd6.preview.emergentagent.com/api"

class TicketingSystemAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate unique identifiers for test users
        timestamp = int(time.time())
        cls.end_user_email = f"end_user_{timestamp}@test.com"
        cls.agent_email = f"agent_{timestamp}@test.com"
        cls.team_lead_email = f"team_lead_{timestamp}@test.com"
        cls.admin_email = f"admin_{timestamp}@test.com"
        
        cls.password = "Test@123456"
        cls.user_tokens = {}
        cls.user_ids = {}
        
        # Register test users with different roles
        print("\n🔹 Setting up test users...")
        cls._register_user(cls, "End User", cls.end_user_email, cls.password, "end_user")
        cls._register_user(cls, "Support Agent", cls.agent_email, cls.password, "support_agent")
        cls._register_user(cls, "Team Lead", cls.team_lead_email, cls.password, "team_lead")
        cls._register_user(cls, "Admin", cls.admin_email, cls.password, "admin")
        
        # Create a test ticket as end user
        cls.ticket_id = cls._create_test_ticket(cls)
    
    def _register_user(self, name, email, password, role):
        """Helper method to register a user"""
        data = {
            "name": name,
            "email": email,
            "password": password,
            "role": role
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=data)
        
        if response.status_code == 200:
            result = response.json()
            self.user_tokens[role] = result["token"]
            self.user_ids[role] = result["user"]["id"]
            print(f"✅ Registered {role} user: {email}")
        else:
            print(f"❌ Failed to register {role} user: {response.text}")
    
    def _create_test_ticket(self):
        """Helper method to create a test ticket"""
        headers = {"Authorization": f"Bearer {self.user_tokens['end_user']}"}
        data = {
            "title": "Test Ticket",
            "description": "This is a test ticket created by automated tests",
            "priority": "high",
            "category": "technical"
        }
        
        response = requests.post(f"{BASE_URL}/tickets", headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            ticket_id = result["id"]
            print(f"✅ Created test ticket with ID: {ticket_id}")
            return ticket_id
        else:
            print(f"❌ Failed to create test ticket: {response.text}")
            return None
    
    def test_01_connectivity(self):
        """Test basic connectivity to the API"""
        print("\n🔹 Testing API connectivity...")
        try:
            response = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {self.user_tokens['end_user']}"})
            self.assertEqual(response.status_code, 200)
            print("✅ API is accessible")
        except Exception as e:
            self.fail(f"❌ API is not accessible: {str(e)}")
    
    def test_02_login(self):
        """Test login functionality"""
        print("\n🔹 Testing login functionality...")
        
        # Test valid login
        data = {
            "email": self.end_user_email,
            "password": self.password
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=data)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("token", result)
        self.assertIn("user", result)
        print("✅ Login successful")
        
        # Test invalid login
        data = {
            "email": self.end_user_email,
            "password": "wrong_password"
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=data)
        self.assertEqual(response.status_code, 401)
        print("✅ Invalid login rejected")
    
    def test_03_get_current_user(self):
        """Test getting current user info"""
        print("\n🔹 Testing get current user info...")
        
        for role, token in self.user_tokens.items():
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            
            self.assertEqual(response.status_code, 200)
            user_data = response.json()
            self.assertEqual(user_data["role"], role)
            print(f"✅ Retrieved {role} user info")
    
    def test_04_create_ticket(self):
        """Test ticket creation"""
        print("\n🔹 Testing ticket creation...")
        
        headers = {"Authorization": f"Bearer {self.user_tokens['end_user']}"}
        data = {
            "title": f"Test Ticket {uuid.uuid4()}",
            "description": "This is a test ticket description",
            "priority": "medium",
            "category": "general"
        }
        
        response = requests.post(f"{BASE_URL}/tickets", headers=headers, json=data)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("id", result)
        self.assertEqual(result["title"], data["title"])
        self.assertEqual(result["priority"], data["priority"])
        self.assertEqual(result["category"], data["category"])
        self.assertEqual(result["status"], "open")
        print("✅ Ticket created successfully")
    
    def test_05_get_tickets(self):
        """Test getting tickets list"""
        print("\n🔹 Testing get tickets list...")
        
        # Test as end user (should only see their tickets)
        headers = {"Authorization": f"Bearer {self.user_tokens['end_user']}"}
        response = requests.get(f"{BASE_URL}/tickets", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        tickets = response.json()
        self.assertIsInstance(tickets, list)
        
        if tickets:
            for ticket in tickets:
                self.assertEqual(ticket["created_by"], self.user_ids["end_user"])
            print("✅ End user can only see their tickets")
        else:
            print("⚠️ No tickets found for end user")
        
        # Test as support agent (should see all tickets)
        headers = {"Authorization": f"Bearer {self.user_tokens['support_agent']}"}
        response = requests.get(f"{BASE_URL}/tickets", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        tickets = response.json()
        self.assertIsInstance(tickets, list)
        print(f"✅ Support agent can see {len(tickets)} tickets")
    
    def test_06_get_ticket_by_id(self):
        """Test getting a specific ticket"""
        print("\n🔹 Testing get ticket by ID...")
        
        if not self.ticket_id:
            self.skipTest("No test ticket available")
        
        # Test as ticket creator (end user)
        headers = {"Authorization": f"Bearer {self.user_tokens['end_user']}"}
        response = requests.get(f"{BASE_URL}/tickets/{self.ticket_id}", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        ticket = response.json()
        self.assertEqual(ticket["id"], self.ticket_id)
        print("✅ End user can access their ticket")
        
        # Test as support agent
        headers = {"Authorization": f"Bearer {self.user_tokens['support_agent']}"}
        response = requests.get(f"{BASE_URL}/tickets/{self.ticket_id}", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        print("✅ Support agent can access the ticket")
    
    def test_07_update_ticket(self):
        """Test updating a ticket"""
        print("\n🔹 Testing update ticket...")
        
        if not self.ticket_id:
            self.skipTest("No test ticket available")
        
        # Test as support agent
        headers = {"Authorization": f"Bearer {self.user_tokens['support_agent']}"}
        data = {
            "status": "in_progress",
            "assigned_to": self.user_ids["support_agent"]
        }
        
        response = requests.put(f"{BASE_URL}/tickets/{self.ticket_id}", headers=headers, json=data)
        
        self.assertEqual(response.status_code, 200)
        updated_ticket = response.json()
        self.assertEqual(updated_ticket["status"], "in_progress")
        self.assertEqual(updated_ticket["assigned_to"], self.user_ids["support_agent"])
        print("✅ Support agent can update ticket status and assignment")
        
        # Test as end user (should fail)
        headers = {"Authorization": f"Bearer {self.user_tokens['end_user']}"}
        data = {
            "status": "resolved"
        }
        
        response = requests.put(f"{BASE_URL}/tickets/{self.ticket_id}", headers=headers, json=data)
        
        self.assertEqual(response.status_code, 403)
        print("✅ End user cannot update ticket status (permission denied)")
    
    def test_08_add_comments(self):
        """Test adding comments to a ticket"""
        print("\n🔹 Testing add comments...")
        
        if not self.ticket_id:
            self.skipTest("No test ticket available")
        
        # Add regular comment as end user
        headers = {"Authorization": f"Bearer {self.user_tokens['end_user']}"}
        data = {
            "content": "This is a test comment from end user",
            "is_internal": False
        }
        
        response = requests.post(f"{BASE_URL}/tickets/{self.ticket_id}/comments", headers=headers, json=data)
        
        self.assertEqual(response.status_code, 200)
        comment = response.json()
        self.assertEqual(comment["content"], data["content"])
        self.assertEqual(comment["is_internal"], False)
        print("✅ End user can add regular comment")
        
        # Try to add internal comment as end user (should fail)
        data = {
            "content": "This is an internal note that should fail",
            "is_internal": True
        }
        
        response = requests.post(f"{BASE_URL}/tickets/{self.ticket_id}/comments", headers=headers, json=data)
        
        self.assertEqual(response.status_code, 403)
        print("✅ End user cannot add internal comment (permission denied)")
        
        # Add internal comment as support agent
        headers = {"Authorization": f"Bearer {self.user_tokens['support_agent']}"}
        data = {
            "content": "This is an internal note from support agent",
            "is_internal": True
        }
        
        response = requests.post(f"{BASE_URL}/tickets/{self.ticket_id}/comments", headers=headers, json=data)
        
        self.assertEqual(response.status_code, 200)
        comment = response.json()
        self.assertEqual(comment["content"], data["content"])
        self.assertEqual(comment["is_internal"], True)
        print("✅ Support agent can add internal comment")
    
    def test_09_get_comments(self):
        """Test getting comments for a ticket"""
        print("\n🔹 Testing get comments...")
        
        if not self.ticket_id:
            self.skipTest("No test ticket available")
        
        # Get comments as end user (should not see internal comments)
        headers = {"Authorization": f"Bearer {self.user_tokens['end_user']}"}
        response = requests.get(f"{BASE_URL}/tickets/{self.ticket_id}/comments", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        comments = response.json()
        
        for comment in comments:
            self.assertFalse(comment["is_internal"])
        print("✅ End user cannot see internal comments")
        
        # Get comments as support agent (should see all comments)
        headers = {"Authorization": f"Bearer {self.user_tokens['support_agent']}"}
        response = requests.get(f"{BASE_URL}/tickets/{self.ticket_id}/comments", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        comments = response.json()
        print(f"✅ Support agent can see all {len(comments)} comments")
    
    def test_10_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n🔹 Testing dashboard statistics...")
        
        # Test as end user (should fail)
        headers = {"Authorization": f"Bearer {self.user_tokens['end_user']}"}
        response = requests.get(f"{BASE_URL}/dashboard/stats", headers=headers)
        
        self.assertEqual(response.status_code, 403)
        print("✅ End user cannot access dashboard stats (permission denied)")
        
        # Test as support agent
        headers = {"Authorization": f"Bearer {self.user_tokens['support_agent']}"}
        response = requests.get(f"{BASE_URL}/dashboard/stats", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        
        self.assertIn("total_tickets", stats)
        self.assertIn("open_tickets", stats)
        self.assertIn("critical_tickets", stats)
        self.assertIn("tickets_by_category", stats)
        self.assertIn("avg_resolution_time_hours", stats)
        print("✅ Support agent can access dashboard stats")
    
    def test_11_get_users(self):
        """Test getting users list"""
        print("\n🔹 Testing get users list...")
        
        # Test as end user (should fail)
        headers = {"Authorization": f"Bearer {self.user_tokens['end_user']}"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        
        self.assertEqual(response.status_code, 403)
        print("✅ End user cannot access users list (permission denied)")
        
        # Test as team lead
        headers = {"Authorization": f"Bearer {self.user_tokens['team_lead']}"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        
        self.assertEqual(response.status_code, 200)
        users = response.json()
        self.assertIsInstance(users, list)
        print(f"✅ Team lead can access users list ({len(users)} users)")

if __name__ == "__main__":
    unittest.main(verbosity=2)