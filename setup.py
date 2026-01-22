# [file name]: setup.py
# [file location]: root folder
# [Purpose]: Setup database with hashed passwords

import os
import sqlite3
import security  # ADD THIS IMPORT

print("🔧 SAVE2SERVE HUB - COMPLETE SETUP")
print("=" * 60)

# Delete old database if exists
if os.path.exists('food.db'):
    os.remove('food.db')
    print("🗑️  Deleted old database")

# Create fresh database
print("\n📁 Creating fresh database...")
conn = sqlite3.connect('food.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE hotel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    location TEXT,
    contact TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE ngo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    location TEXT,
    contact TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE food (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_name TEXT NOT NULL,
    quantity TEXT NOT NULL,
    expiry_time DATETIME NOT NULL,
    location TEXT NOT NULL,
    map_link TEXT,
    hotel_id INTEGER NOT NULL,
    hotel_name TEXT NOT NULL,
    status TEXT DEFAULT 'Available',
    uploaded_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    collected_time TIMESTAMP,
    delivered_time TIMESTAMP,
    collected_by INTEGER,
    FOREIGN KEY (hotel_id) REFERENCES hotel (id),
    FOREIGN KEY (collected_by) REFERENCES ngo (id)
)
''')

# Insert admin user with HASHED PASSWORD
admin_hashed = security.hash_password('admin123')
cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", 
               ('admin', admin_hashed))

# Insert test hotel with HASHED PASSWORD
hotel_hashed = security.hash_password('hotel123')
cursor.execute("INSERT INTO hotel (name, email, password, location, contact) VALUES (?, ?, ?, ?, ?)",
               ('Test Hotel', 'hotel@test.com', hotel_hashed, 'Mumbai', '9876543210'))

# Insert test NGO with HASHED PASSWORD
ngo_hashed = security.hash_password('ngo123')
cursor.execute("INSERT INTO ngo (name, email, password, location, contact) VALUES (?, ?, ?, ?, ?)",
               ('Test NGO', 'ngo@test.com', ngo_hashed, 'Delhi', '9123456789'))

# Add some sample food data
cursor.execute("""
INSERT INTO food (food_name, quantity, expiry_time, location, hotel_id, hotel_name)
VALUES 
('Vegetable Biryani', '25 plates', datetime('now', '+2 hours'), 'Hotel Lobby', 1, 'Test Hotel'),
('Pizza & Pasta', '30 servings', datetime('now', '+3 hours'), 'Back Entrance', 1, 'Test Hotel'),
('Sandwiches', '50 pieces', datetime('now', '+1 hour'), 'Kitchen Door', 1, 'Test Hotel')
""")

conn.commit()
conn.close()

print("✅ Database created with test users and sample food!")
print("\n📋 TEST ACCOUNTS:")
print("   ADMIN:")
print("     Username: admin")
print("     Password: admin123")
print("\n   HOTEL:")
print("     Email: hotel@test.com")
print("     Password: hotel123")
print("\n   NGO:")
print("     Email: ngo@test.com")
print("     Password: ngo123")
print("\n🍽️  Sample food items added for testing")
print("\n🔗 Run the app: python app.py")
print("🌐 Open: http://localhost:5000")