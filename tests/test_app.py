import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        # Arrange
        expected_activities = ["Chess Club", "Programming Class"]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        assert set(response.json().keys()) == set(expected_activities)
    
    def test_get_activities_returns_correct_structure(self, client, reset_activities):
        # Arrange
        required_keys = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert set(activity_data.keys()) == required_keys


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self, client, reset_activities):
        # Arrange
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Programming Class"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in reset_activities[activity_name]["participants"]
    
    def test_signup_duplicate_email_rejected(self, client, reset_activities):
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_activity_full_rejected(self, client, reset_activities):
        # Arrange
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        email3 = "student3@mergington.edu"
        activity_name = "Chess Club"  # Max 2 participants, 1 already signed up
        
        # Sign up first student (fills to capacity)
        client.post(f"/activities/{activity_name}/signup?email={email1}")
        
        # Act - Try to sign up second student (should fail, activity full)
        response = client.post(
            f"/activities/{activity_name}/signup?email={email2}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()
    
    def test_signup_nonexistent_activity_not_found(self, client, reset_activities):
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        # Arrange
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email not in reset_activities[activity_name]["participants"]
    
    def test_unregister_user_not_signed_up(self, client, reset_activities):
        # Arrange
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_nonexistent_activity_not_found(self, client, reset_activities):
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestBugFix:
    """Tests verifying the duplicate registration bug is fixed"""
    
    def test_cannot_register_twice_for_same_activity(self, client, reset_activities):
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Programming Class"
        
        # Act - First signup (should succeed)
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        # Second signup attempt (should fail)
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert - First succeeds, second fails
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()
        # Verify only one entry in participants
        assert reset_activities[activity_name]["participants"].count(email) == 1
    
    def test_capacity_enforced_prevents_duplicate_signup(self, client, reset_activities):
        # Arrange
        email1 = "email1@mergington.edu"
        email2 = "email2@mergington.edu"
        activity_name = "Programming Class"  # Max 2, currently 0
        
        # Act - Fill activity to capacity
        response1 = client.post(f"/activities/{activity_name}/signup?email={email1}")
        response2 = client.post(f"/activities/{activity_name}/signup?email={email2}")
        # Try to add third person (should fail)
        response3 = client.post(
            f"/activities/{activity_name}/signup?email=email3@mergington.edu"
        )
        
        # Assert - First two succeed, third fails due to capacity
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 400
        assert len(reset_activities[activity_name]["participants"]) == 2
