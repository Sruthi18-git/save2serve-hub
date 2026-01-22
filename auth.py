import database
import security  # ADD THIS

# Initialize database
db = database.db

def authenticate_user(email, password, user_type):
    """
    Authenticate user with hashed password verification
    """
    print(f"\n🔐 AUTHENTICATION ATTEMPT")
    print(f"   Type: {user_type}")
    print(f"   Email/Username: {email}")
    
    user = db.get_user_by_email(email, user_type)
    
    if user:
        user_dict = dict(user)
        print(f"✅ User found: {user_dict.get('name', user_dict.get('username', 'Unknown'))}")
        
        # VERIFY HASHED PASSWORD
        if security.verify_password(password, user_dict['password']):
            print("✅ Password matches!")
            
            # Return user info
            user_info = {
                'id': user_dict['id'],
                'type': user_type
            }
            
            if user_type == 'admin':
                user_info['name'] = user_dict.get('username', 'Admin')
            else:
                user_info['name'] = user_dict.get('name', 'User')
                user_info['email'] = user_dict.get('email', email)
            
            print(f"✅ Authentication successful!")
            return user_info
        else:
            print("❌ Password doesn't match!")
    else:
        print("❌ User not found in database")
    
    return None

def register_user(name, email, password, user_type, location="", contact=""):
    """
    Register user with hashed password
    """
    print(f"\n📝 REGISTRATION ATTEMPT")
    print(f"   Type: {user_type}")
    print(f"   Name: {name}")
    print(f"   Email: {email}")
    
    # HASH THE PASSWORD BEFORE STORING
    hashed_password = security.hash_password(password)
    
    return db.add_user(name, email, hashed_password, user_type, location, contact)

if __name__ == "__main__":
    print("🧪 Testing Auth Module")
    
    # Test admin
    admin = authenticate_user("admin", "admin123", "admin")
    print(f"Admin auth: {'✅ Success' if admin else '❌ Failed'}")
    
    # Check for test hotel
    hotel = authenticate_user("hotel@test.com", "hotel123", "hotel")
    print(f"Hotel auth: {'✅ Success' if hotel else '❌ Failed'}")
    
    print("\n✅ Auth module ready!")