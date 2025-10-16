import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


class TestBasicEndpoints:
    """Test basic API endpoints."""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static index.html."""
        response = client.get("/")
        assert response.status_code == 200
        # Should redirect to static files
    
    def test_get_activities(self, client):
        """Test getting all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should contain the default activities
        assert len(data) > 0
        
        # Check structure of first activity
        first_activity = list(data.values())[0]
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity


class TestActivitySignup:
    """Test activity signup functionality."""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        # Get an activity with available spots
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        # Find an activity with available spots
        activity_name = None
        for name, details in activities_data.items():
            if len(details["participants"]) < details["max_participants"]:
                activity_name = name
                break
        
        assert activity_name is not None, "No activities with available spots found"
        
        test_email = "newstudent@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert test_email in data["message"]
        assert activity_name in data["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        updated_activities = activities_response.json()
        assert test_email in updated_activities[activity_name]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity."""
        response = client.post("/activities/NonExistent/signup?email=test@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_participant(self, client):
        """Test signup when participant is already registered."""
        # First, get an existing participant
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        # Find an activity with existing participants
        activity_name = None
        existing_email = None
        for name, details in activities_data.items():
            if details["participants"]:
                activity_name = name
                existing_email = details["participants"][0]
                break
        
        assert activity_name is not None, "No activities with participants found"
        
        response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_full_activity(self, client):
        """Test signup when activity is at capacity."""
        # First, create a temporary full activity
        test_activity = "Full Test Activity"
        activities[test_activity] = {
            "description": "Test activity at capacity",
            "schedule": "Test schedule",
            "max_participants": 1,
            "participants": ["existing@mergington.edu"]
        }
        
        response = client.post(f"/activities/{test_activity}/signup?email=new@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "Activity is full" in data["detail"]


class TestActivityUnregister:
    """Test activity unregister functionality."""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity."""
        # First, add a test participant
        test_activity = "Test Unregister Activity"
        test_email = "unregister@mergington.edu"
        
        activities[test_activity] = {
            "description": "Test activity for unregistration",
            "schedule": "Test schedule",
            "max_participants": 10,
            "participants": [test_email, "other@mergington.edu"]
        }
        
        response = client.delete(f"/activities/{test_activity}/unregister?email={test_email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert test_email in data["message"]
        assert test_activity in data["message"]
        
        # Verify the participant was removed
        assert test_email not in activities[test_activity]["participants"]
        assert "other@mergington.edu" in activities[test_activity]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from non-existent activity."""
        response = client.delete("/activities/NonExistent/unregister?email=test@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered(self, client):
        """Test unregister when participant is not registered."""
        # Get an existing activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        activity_name = list(activities_data.keys())[0]
        
        response = client.delete(f"/activities/{activity_name}/unregister?email=notregistered@mergington.edu")
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]


class TestDataIntegrity:
    """Test data integrity and edge cases."""
    
    def test_activity_data_structure(self, client):
        """Test that all activities have the required structure."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities_data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            
            for field in required_fields:
                assert field in activity_data, f"Missing {field} in {activity_name}"
            
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0
            assert len(activity_data["participants"]) <= activity_data["max_participants"]
    
    def test_email_validation_format(self, client):
        """Test various email formats in signup."""
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        # Find an activity with available spots
        activity_name = None
        for name, details in activities_data.items():
            if len(details["participants"]) < details["max_participants"]:
                activity_name = name
                break
        
        assert activity_name is not None
        
        # Test valid email formats
        valid_emails = [
            "student@mergington.edu",
            "first.last@mergington.edu",
            "student123@mergington.edu"
        ]
        
        for email in valid_emails:
            # Clean up first
            if email in activities[activity_name]["participants"]:
                activities[activity_name]["participants"].remove(email)
            
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200, f"Failed for email: {email}"
    
    def test_concurrent_operations(self, client):
        """Test that operations maintain data consistency."""
        # Create a test activity
        test_activity = "Concurrent Test"
        activities[test_activity] = {
            "description": "Test concurrent operations",
            "schedule": "Test schedule",
            "max_participants": 3,
            "participants": []
        }
        
        # Add multiple participants
        emails = ["user1@test.edu", "user2@test.edu", "user3@test.edu"]
        
        for email in emails:
            response = client.post(f"/activities/{test_activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all were added
        assert len(activities[test_activity]["participants"]) == 3
        
        # Remove one participant
        response = client.delete(f"/activities/{test_activity}/unregister?email={emails[1]}")
        assert response.status_code == 200
        
        # Verify correct removal
        assert len(activities[test_activity]["participants"]) == 2
        assert emails[1] not in activities[test_activity]["participants"]
        assert emails[0] in activities[test_activity]["participants"]
        assert emails[2] in activities[test_activity]["participants"]