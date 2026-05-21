from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Building, EmergencyAlert, UserAlertConfirmation, UserProfile


class MobileApiTests(APITestCase):
    def test_mobile_register_returns_user_and_jwt_tokens(self):
        building = Building.objects.create(name="Gedung A", address="Jakarta")
        response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Budi Santoso",
                "phone": "08123456789",
                "password": "secret123",
                "building_id": building.id,
                "floor": 7,
                "disability_type": "none",
                "fcm_token": "fcm-register",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["phone"], "08123456789")
        self.assertEqual(response.data["data"]["admin_status"], "pending")
        self.assertIn("access", response.data["tokens"])
        self.assertTrue(
            UserProfile.objects.filter(
                phone_number="08123456789",
                status="pending",
                building=building,
            ).exists()
        )

    def test_mobile_register_requires_valid_building(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Budi Santoso",
                "phone": "08123456789",
                "password": "secret123",
                "building_id": 999,
                "floor": 7,
                "disability_type": "none",
                "fcm_token": "fcm-register",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(UserProfile.objects.count(), 0)

    def test_mobile_register_accepts_legacy_field_names(self):
        building = Building.objects.create(name="Gedung A", address="Jakarta")
        response = self.client.post(
            "/api/auth/register/",
            {
                "full_name": "Siti Aminah",
                "phone_number": "08222222222",
                "password": "secret123",
                "buildingId": building.id,
                "lantai": 3,
                "disabilityType": "deaf",
                "fcmToken": "fcm-register",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserProfile.objects.filter(
                phone_number="08222222222",
                disability_type="deaf",
                last_location="3",
                building=building,
            ).exists()
        )

    def test_building_list_is_available_before_login(self):
        building = Building.objects.create(name="Gedung A", address="Jakarta")

        response = self.client.get("/api/buildings/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], building.id)

    def test_mobile_login_updates_fcm_token(self):
        user = User.objects.create_user(username="08111111111", password="secret123")
        UserProfile.objects.create(user=user, phone_number="08111111111", fcm_token="old")

        response = self.client.post(
            "/api/auth/login/",
            {
                "phone": "08111111111",
                "password": "secret123",
                "fcm_token": "new-token",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["tokens"])
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.fcm_token, "new-token")

    def test_mobile_can_poll_active_alert_and_confirm_status(self):
        building = Building.objects.create(name="Gedung A", address="Jakarta")
        user = User.objects.create_user(username="08222222222", password="secret123")
        UserProfile.objects.create(user=user, phone_number="08222222222", status="active", building=building)
        alert = EmergencyAlert.objects.create(
            building=building,
            alert_type="fire",
            title="Kebakaran",
            description="Evakuasi sekarang",
            severity=4,
            triggered_by=user,
        )
        UserAlertConfirmation.objects.create(alert=alert, user=user, building=building)

        login_response = self.client.post(
            "/api/auth/login/",
            {
                "phone": "08222222222",
                "password": "secret123",
                "fcm_token": "token",
            },
            format="json",
        )
        access = login_response.data["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        poll_response = self.client.get("/api/alerts/active_alerts/")
        self.assertEqual(poll_response.status_code, status.HTTP_200_OK)
        self.assertEqual(poll_response.data[0]["id"], alert.id)

        confirm_response = self.client.post(
            "/api/confirmations/confirm_status/",
            {
                "alert_id": alert.id,
                "status": "trapped",
                "location": "Lantai 7 dekat tangga A",
                "notes": "Asap tebal dan pintu terkunci",
            },
            format="json",
        )
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        self.assertEqual(confirm_response.data["status"], "trapped")
        self.assertEqual(confirm_response.data["location"], "Lantai 7 dekat tangga A")
        self.assertEqual(confirm_response.data["notes"], "Asap tebal dan pintu terkunci")

        poll_after_confirm_response = self.client.get("/api/alerts/active_alerts/")
        self.assertEqual(poll_after_confirm_response.status_code, status.HTTP_200_OK)
        self.assertEqual(poll_after_confirm_response.data, [])

    def test_creating_alert_targets_only_users_in_selected_building(self):
        building_a = Building.objects.create(name="Gedung A", address="Jakarta")
        building_b = Building.objects.create(name="Gedung B", address="Bandung")
        admin = User.objects.create_user(username="admin", password="secret123", is_staff=True)
        user_a = User.objects.create_user(username="08100000001", password="secret123")
        user_b = User.objects.create_user(username="08100000002", password="secret123")
        UserProfile.objects.create(
            user=user_a,
            phone_number="08100000001",
            status="active",
            building=building_a,
            fcm_token="token-a",
        )
        UserProfile.objects.create(
            user=user_b,
            phone_number="08100000002",
            status="active",
            building=building_b,
            fcm_token="token-b",
        )
        self.client.force_authenticate(user=admin)

        response = self.client.post(
            "/api/alerts/",
            {
                "building": building_a.id,
                "alert_type": "fire",
                "title": "Kebakaran",
                "description": "Evakuasi sekarang",
                "severity": 4,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        alert = EmergencyAlert.objects.get(title="Kebakaran", building=building_a)
        confirmations = UserAlertConfirmation.objects.filter(alert=alert)
        self.assertEqual(confirmations.count(), 1)
        self.assertTrue(confirmations.filter(user=user_a, building=building_a).exists())
        self.assertFalse(confirmations.filter(user=user_b).exists())

    def test_mobile_update_profile_only_changes_floor(self):
        user = User.objects.create_user(
            username="08333333333",
            password="secret123",
            first_name="Ani",
        )
        profile = UserProfile.objects.create(
            user=user,
            phone_number="08333333333",
            disability_type="blind",
            last_location="3",
        )

        login_response = self.client.post(
            "/api/auth/login/",
            {
                "phone": "08333333333",
                "password": "secret123",
                "fcm_token": "token",
            },
            format="json",
        )
        access = login_response.data["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.patch(
            "/api/users/update_floor/",
            {
                "floor": 12,
                "phone_number": "08999999999",
                "disability_type": "none",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(profile.last_location, "12")
        self.assertEqual(profile.phone_number, "08333333333")
        self.assertEqual(profile.disability_type, "blind")
        self.assertEqual(user.first_name, "Ani")
