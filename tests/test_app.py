import pytest
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    initial_activities = {
        "Basketball": {
            "description": "Team sport focusing on basketball skills and competitive play",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Develop tennis techniques and participate in friendly matches",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["james@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and other visual art forms",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["isabella@mergington.edu", "grace@mergington.edu"]
        },
        "Music Band": {
            "description": "Join the school band and perform in concerts",
            "schedule": "Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu"]
        },
        "Debate Club": {
            "description": "Develop argumentation and public speaking skills",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["sarah@mergington.edu", "aaron@mergington.edu"]
        },
        "Science Lab": {
            "description": "Conduct experiments and explore scientific concepts",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["noah@mergington.edu"]
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Clear and reset activities
    activities.clear()
    activities.update(initial_activities)
    yield
    # Reset after test
    activities.clear()
    activities.update(initial_activities)


class TestGetActivities:
    """Test cases for getting activities"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        data = response.json()
        assert len(data) == 9
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Art Studio" in data
    
    def test_get_activities_has_correct_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        basketball = data["Basketball"]
        
        assert "description" in basketball
        assert "schedule" in basketball
        assert "max_participants" in basketball
        assert "participants" in basketball
        assert isinstance(basketball["participants"], list)


class TestSignup:
    """Test cases for signing up for activities"""
    
    def test_signup_valid_activity(self, client):
        """Test signing up for a valid activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify student was added
        updated = client.get("/activities").json()
        assert "newstudent@mergington.edu" in updated["Basketball"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for non-existent activity"""
        response = client.post(
            "/activities/NonExistent/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_already_registered(self, client):
        """Test signing up when already registered"""
        response = client.post(
            "/activities/Basketball/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_activity_full(self, client):
        """Test signing up when activity is full"""
        # Get Tennis Club and fill it up
        tennis_activity = activities["Tennis Club"]
        # Tennis Club has max 10 participants, currently has 1
        for i in range(9):
            tennis_activity["participants"].append(f"student{i}@mergington.edu")
        
        # Try to sign up when full
        response = client.post(
            "/activities/Tennis Club/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"]


class TestUnregister:
    """Test cases for unregistering from activities"""
    
    def test_unregister_valid(self, client):
        """Test unregistering from an activity"""
        response = client.post(
            "/activities/Basketball/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify student was removed
        updated = client.get("/activities").json()
        assert "alex@mergington.edu" not in updated["Basketball"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from non-existent activity"""
        response = client.post(
            "/activities/NonExistent/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered(self, client):
        """Test unregistering when not registered"""
        response = client.post(
            "/activities/Basketball/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_increases_availability(self, client):
        """Test that unregistering increases available spots"""
        # Get initial availability
        initial = client.get("/activities").json()
        initial_count = len(initial["Basketball"]["participants"])
        
        # Unregister a student
        client.post("/activities/Basketball/unregister?email=alex@mergington.edu")
        
        # Check new count
        updated = client.get("/activities").json()
        updated_count = len(updated["Basketball"]["participants"])
        
        assert updated_count == initial_count - 1


class TestSignupAndUnregister:
    """Integration tests for signup and unregister"""
    
    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering"""
        email = "integration@mergington.edu"
        activity = "Basketball"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify signed up
        activities_data = client.get("/activities").json()
        assert email in activities_data[activity]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify unregistered
        activities_data = client.get("/activities").json()
        assert email not in activities_data[activity]["participants"]
    
    def test_signup_unregister_signup_again(self, client):
        """Test signing up, unregistering, and signing up again"""
        email = "repeat@mergington.edu"
        activity = "Basketball"
        
        # First signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Sign up again
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify registered
        activities_data = client.get("/activities").json()
        assert email in activities_data[activity]["participants"]
