"""
Seed script untuk membuat mock data untuk testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth.models import User
from api.models import Building, UserProfile, EmergencyAlert, UserAlertConfirmation, AlertLog
from django.utils import timezone

def clear_data():
    """Hapus data lama"""
    print("Clearing old data...")
    UserAlertConfirmation.objects.all().delete()
    AlertLog.objects.all().delete()
    EmergencyAlert.objects.all().delete()
    UserProfile.objects.all().delete()
    Building.objects.all().delete()
    User.objects.filter(username__startswith='user_').delete()
    print("[OK] Data cleared")


def create_buildings():
    """Buat data gedung"""
    print("\nCreating buildings...")
    buildings = [
        Building.objects.create(
            name="Gedung A - Kantor Pusat",
            address="Jl. Jenderal Sudirman No. 1, Jakarta",
            latitude=-6.2088,
            longitude=106.8000,
            total_capacity=500
        ),
        Building.objects.create(
            name="Gedung B - Kantor Operasional",
            address="Jl. Gatot Subroto No. 55, Jakarta",
            latitude=-6.2215,
            longitude=106.8000,
            total_capacity=300
        ),
    ]
    print(f"[OK] Created {len(buildings)} buildings")
    return buildings


def create_users(buildings):
    """Buat data user"""
    print("\nCreating users...")
    
    users_data = [
        # 5 Active Users
        {'username': 'user_001', 'email': 'user001@safealert.local', 'first_name': 'Budi', 'last_name': 'Santoso'},
        {'username': 'user_002', 'email': 'user002@safealert.local', 'first_name': 'Siti', 'last_name': 'Rahayu'},
        {'username': 'user_003', 'email': 'user003@safealert.local', 'first_name': 'Ahmad', 'last_name': 'Wijaya'},
        {'username': 'user_004', 'email': 'user004@safealert.local', 'first_name': 'Dina', 'last_name': 'Kusuma'},
        {'username': 'user_005', 'email': 'user005@safealert.local', 'first_name': 'Eko', 'last_name': 'Pratama'},
        # 3 Pending Users
        {'username': 'user_006', 'email': 'user006@safealert.local', 'first_name': 'Fitra', 'last_name': 'Hidayat'},
        {'username': 'user_007', 'email': 'user007@safealert.local', 'first_name': 'Gita', 'last_name': 'Permata'},
        {'username': 'user_008', 'email': 'user008@safealert.local', 'first_name': 'Hanif', 'last_name': 'Rahman'},
    ]
    
    disability_types = ['none', 'deaf', 'blind']
    
    created_users = []
    for i, user_data in enumerate(users_data):
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password='password123',
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        
        # Determine status dan building
        if i < 5:
            status = 'active'
            building = buildings[i % 2]
        else:
            status = 'pending'
            building = buildings[0]
        
        # Create profile
        profile = UserProfile.objects.create(
            user=user,
            building=building,
            phone_number=f"0812-{1000000 + i:07d}",
            disability_type=disability_types[i % len(disability_types)],
            special_needs="Butuh bantuan khusus" if i % 3 == 0 else "",
            status=status,
            fcm_token=f"fcm_token_{i}_{user.username}" if status == 'active' else "",
            is_inside_building=i < 5,
            last_location="Lantai 3, Ruang Meeting" if i < 5 else ""
        )
        created_users.append(user)
    
    print(f"[OK] Created {len(created_users)} users with profiles")
    return created_users


def create_emergency_alerts(buildings, users):
    """Buat data alert darurat"""
    print("\nCreating emergency alerts...")
    
    building = buildings[0]
    admin_user = User.objects.get(username='admin_gedung')
    
    alert = EmergencyAlert.objects.create(
        building=building,
        alert_type='fire',
        title='Kebakaran di Lantai 3',
        description='Terdeteksi asap dan api di area ruang server Lantai 3',
        status='active',
        severity=4,
        triggered_by=admin_user,
    )
    print(f"[OK] Created emergency alert: {alert.title}")
    return alert


def create_alert_confirmations(alert, users):
    """Buat data konfirmasi alert dari user"""
    print("\nCreating user alert confirmations...")
    
    statuses = ['safe', 'safe', 'trapped', 'needs_help', 'no_response']
    locations = ['Lantai 3', 'Lantai 2', 'Tangga Darurat', 'Parkiran', '']
    
    confirmations = []
    for i, user in enumerate(users[:5]):
        confirmation = UserAlertConfirmation.objects.create(
            alert=alert,
            user=user,
            status=statuses[i],
            location=locations[i],
            notes="Update status pengguna" if statuses[i] != 'no_response' else "",
        )
        if statuses[i] != 'no_response':
            confirmation.confirmed_at = timezone.now()
            confirmation.save()
        confirmations.append(confirmation)
    
    print(f"[OK] Created {len(confirmations)} alert confirmations")
    return confirmations


def create_alert_logs(alert):
    """Buat log alert"""
    print("\nCreating alert logs...")
    
    admin_user = User.objects.get(username='admin_gedung')
    
    actions = [
        ('created', 'Alert darurat dibuat oleh operator'),
        ('sent', 'Alert dikirim ke semua pengguna aktif'),
        ('confirmed', 'Pengguna mulai memberikan konfirmasi status'),
    ]
    
    logs = []
    for action, description in actions:
        log = AlertLog.objects.create(
            alert=alert,
            action=action,
            description=description,
            performed_by=admin_user if action == 'created' else None
        )
        logs.append(log)
    
    print(f"[OK] Created {len(logs)} alert logs")


def main():
    """Main seeding function"""
    print("=" * 60)
    print("SafeAlert Mock Data Seeding")
    print("=" * 60)
    
    try:
        clear_data()
        
        # Ensure admin_gedung exists
        admin_user, created = User.objects.get_or_create(
            username='admin_gedung',
            defaults={
                'email': 'admin@safealert.local',
                'first_name': 'Admin',
                'last_name': 'Gedung',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('password123')
            admin_user.save()
            print("[OK] Created superuser: admin_gedung")
        else:
            print("[OK] Superuser admin_gedung already exists")

        buildings = create_buildings()
        users = create_users(buildings)
        alert = create_emergency_alerts(buildings, users)
        create_alert_confirmations(alert, users)
        create_alert_logs(alert)
        
        print("\n" + "=" * 60)
        print("[OK] Seeding completed successfully!")
        print("=" * 60)
        print("\nLogin credentials:")
        print("  Username: admin_gedung")
        print("  Password: password123")
        print("\nTest user credentials:")
        print("  Username: user_001")
        print("  Password: password123")
        
    except Exception as e:
        print(f"\n[ERROR] Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
