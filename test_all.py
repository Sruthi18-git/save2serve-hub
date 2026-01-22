import database
import auth

print("🧪 COMPLETE SYSTEM TEST")
print("=" * 60)

# Initialize database
db = database.db
print("✅ Database initialized")

# Test admin
print("\n1. Testing admin account...")
admin = auth.authenticate_user("admin", "admin123", "admin")
if admin:
    print(f"   ✅ Admin login successful")
    print(f"   Admin ID: {admin['id']}")
else:
    print("   ❌ Admin login failed")

# Test hotel registration
print("\n2. Registering test hotel...")
success = auth.register_user(
    name="Grand Hotel",
    email="grand@hotel.com",
    password="hotel123",
    user_type="hotel",
    location="Chennai",
    contact="9998887777"
)
print(f"   Result: {'✅ Success' if success else '❌ Failed'}")

# Test hotel login
print("\n3. Logging in as hotel...")
hotel = auth.authenticate_user("grand@hotel.com", "hotel123", "hotel")
if hotel:
    print(f"   ✅ Hotel login successful")
    print(f"   Hotel ID: {hotel['id']}")
    print(f"   Hotel Name: {hotel['name']}")
else:
    print("   ❌ Hotel login failed")

print("\n" + "=" * 60)
print("✅ Test completed!")