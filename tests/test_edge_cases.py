import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_special_characters_in_activity_name(self, client):
        """Test activity names with special characters."""
        # Test URL encoding with special characters
        special_activity = "Art & Design Club"
        activities[special_activity] = {
            "description": "Creative arts and design",
            "schedule": "Fridays, 3:00 PM",
            "max_participants": 10,
            "participants": []
        }
        
        # Test signup with special characters in activity name
        response = client.post(f"/activities/{special_activity}/signup?email=test@mergington.edu")
        assert response.status_code == 200
    
    def test_special_characters_in_email(self, client):
        """Test emails with special characters."""
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        activity_name = list(activities_data.keys())[0]
        
        # Test email with special characters
        special_emails = [
            "test+tag@mergington.edu",
            "test.user@mergington.edu",
            "test_user@mergington.edu"
        ]
        
        for email in special_emails:
            # Clean up first
            if email in activities[activity_name]["participants"]:
                activities[activity_name]["participants"].remove(email)
            
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200, f"Failed for email: {email}"
    
    def test_empty_email_parameter(self, client):
        """Test signup with empty email parameter."""
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        activity_name = list(activities_data.keys())[0]
        
        response = client.post(f"/activities/{activity_name}/signup?email=")
        # Should handle empty email gracefully
        assert response.status_code in [400, 422]  # Bad request or validation error
    
    def test_missing_email_parameter(self, client):
        """Test signup without email parameter."""
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        activity_name = list(activities_data.keys())[0]
        
        response = client.post(f"/activities/{activity_name}/signup")
        # Should require email parameter
        assert response.status_code in [400, 422]  # Bad request or validation error


class TestActivityCapacity:
    """Test activity capacity management."""
    
    def test_activity_at_exact_capacity(self, client):
        """Test behavior when activity reaches exact capacity."""
        test_activity = "Capacity Test"
        max_capacity = 3
        
        activities[test_activity] = {
            "description": "Test capacity management",
            "schedule": "Test schedule",
            "max_participants": max_capacity,
            "participants": []
        }
        
        # Fill to capacity
        emails = [f"user{i}@mergington.edu" for i in range(max_capacity)]
        
        for email in emails:
            response = client.post(f"/activities/{test_activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify at capacity
        assert len(activities[test_activity]["participants"]) == max_capacity
        
        # Try to add one more (should fail)
        response = client.post(f"/activities/{test_activity}/signup?email=overflow@mergington.edu")
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]
        
        # Verify still at capacity (no overflow)
        assert len(activities[test_activity]["participants"]) == max_capacity
    
    def test_unregister_and_re_signup(self, client):
        """Test unregistering and then signing up again."""
        test_activity = "Re-signup Test"
        test_email = "resign@mergington.edu"
        
        activities[test_activity] = {
            "description": "Test re-signup functionality",
            "schedule": "Test schedule",
            "max_participants": 5,
            "participants": [test_email]
        }
        
        # First unregister
        response = client.delete(f"/activities/{test_activity}/unregister?email={test_email}")
        assert response.status_code == 200
        assert test_email not in activities[test_activity]["participants"]
        
        # Then sign up again
        response = client.post(f"/activities/{test_activity}/signup?email={test_email}")
        assert response.status_code == 200
        assert test_email in activities[test_activity]["participants"]


class TestResponseFormats:
    """Test API response formats and consistency."""
    
    def test_activities_response_format(self, client):
        """Test that activities endpoint returns consistent format."""
        response = client.get("/activities")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Check that each activity has consistent structure
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert len(activity_name) > 0
            
            required_keys = ["description", "schedule", "max_participants", "participants"]
            for key in required_keys:
                assert key in activity_data
            
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str) 
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
    
    def test_signup_response_format(self, client):
        """Test signup response format."""
        # Find activity with space
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        activity_name = None
        for name, details in activities_data.items():
            if len(details["participants"]) < details["max_participants"]:
                activity_name = name
                break
        
        test_email = "format.test@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={test_email}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0
    
    def test_unregister_response_format(self, client):
        """Test unregister response format."""
        test_activity = "Format Test"
        test_email = "format.unregister@mergington.edu"
        
        activities[test_activity] = {
            "description": "Test response format",
            "schedule": "Test schedule",
            "max_participants": 5,
            "participants": [test_email]
        }
        
        response = client.delete(f"/activities/{test_activity}/unregister?email={test_email}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0
    
    def test_error_response_format(self, client):
        """Test error response format consistency."""
        # Test 404 error format
        response = client.post("/activities/NonExistent/signup?email=test@mergington.edu")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
        
        # Test 400 error format
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        activity_name = list(activities_data.keys())[0]
        
        response = client.delete(f"/activities/{activity_name}/unregister?email=notfound@mergington.edu")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)