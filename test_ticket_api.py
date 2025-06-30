import requests
import json

# Use the public endpoint from frontend/.env
BASE_URL = "https://3b3839d0-9706-41e4-a6c5-2e43246a5fd6.preview.emergentagent.com/api"

def test_create_ticket():
    # Login first to get a token
    login_data = {
        "email": "finaltest@test.com",
        "password": "password123"
    }
    
    print(f"Logging in with {login_data['email']}...")
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"Login failed with status code {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    token = login_response.json()["token"]
    print(f"Login successful, got token: {token[:10]}...")
    
    # Create a ticket
    ticket_data = {
        "title": "API Test Ticket",
        "description": "This is a test ticket created via direct API call",
        "priority": "medium",
        "category": "general"
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Creating ticket with data: {json.dumps(ticket_data, indent=2)}")
    print(f"Using headers: {json.dumps(headers, indent=2)}")
    
    ticket_response = requests.post(f"{BASE_URL}/tickets", json=ticket_data, headers=headers)
    
    print(f"Response status code: {ticket_response.status_code}")
    print(f"Response headers: {json.dumps(dict(ticket_response.headers), indent=2)}")
    
    if ticket_response.status_code == 200:
        ticket = ticket_response.json()
        print(f"Ticket created successfully with ID: {ticket['id']}")
        print(f"Ticket details: {json.dumps(ticket, indent=2)}")
    else:
        print(f"Failed to create ticket: {ticket_response.text}")

if __name__ == "__main__":
    test_create_ticket()