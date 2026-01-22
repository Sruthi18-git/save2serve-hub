# [file name]: database.py
# [file location]: root folder
# [Purpose]: Complete database operations with password hashing and automatic location capture

import sqlite3
import os
import math
from datetime import datetime
import security


class Database:
    def __init__(self, db_name='food.db'):
        """Initialize database connection with enhanced persistence"""
        print(f"📊 Initializing database: {db_name}")
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Establish and return a database connection with timeout"""
        conn = sqlite3.connect(self.db_name, timeout=10)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_database(self):
        """Initialize database with proper table structure including location capture"""
        print("🔨 Initializing database tables with location tracking...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ===== HOTEL TABLE WITH LOCATION CAPTURE COLUMNS =====
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hotel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            location TEXT,
            contact TEXT,
            -- Automatic Location Capture Columns
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            location_captured_at DATETIME,
            location_method VARCHAR(50),
            location_city VARCHAR(100),
            location_country VARCHAR(100),
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # ===== NGO TABLE WITH LOCATION CAPTURE COLUMNS =====
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ngo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            location TEXT,
            contact TEXT,
            -- Automatic Location Capture Columns
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            location_captured_at DATETIME,
            location_method VARCHAR(50),
            location_city VARCHAR(100),
            location_country VARCHAR(100),
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS food (
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
            FOREIGN KEY (hotel_id) REFERENCES hotel (id) ON DELETE CASCADE,
            FOREIGN KEY (collected_by) REFERENCES ngo (id) ON DELETE SET NULL
        )
        ''')
        
        # CREATE ACTIVITY LOG TABLE
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create basic indexes first
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_food_status ON food(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_food_hotel ON food(hotel_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_food_expiry ON food(expiry_time)')
        
        # Check if location columns exist before creating location indexes
        cursor.execute("PRAGMA table_info(hotel)")
        hotel_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(ngo)")
        ngo_columns = [col[1] for col in cursor.fetchall()]
        
        # Only create location indexes if columns exist
        if 'latitude' in hotel_columns and 'longitude' in hotel_columns:
            try:
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_hotel_location ON hotel(latitude, longitude)')
                print("✅ Created hotel location index")
            except:
                print("⚠️ Could not create hotel location index")
        
        if 'latitude' in ngo_columns and 'longitude' in ngo_columns:
            try:
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ngo_location ON ngo(latitude, longitude)')
                print("✅ Created NGO location index")
            except:
                print("⚠️ Could not create NGO location index")
        
        # Ensure admin account exists (only if not already there)
        cursor.execute("SELECT COUNT(*) FROM admin WHERE username = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            print("👑 Creating default admin account...")
            try:
                # HASH THE ADMIN PASSWORD
                hashed_admin_pw = security.hash_password('admin123')
                cursor.execute(
                    "INSERT INTO admin (username, password) VALUES (?, ?)",
                    ('admin', hashed_admin_pw)
                )
                print("✅ Admin account created: admin/admin123 (hashed)")
            except sqlite3.IntegrityError:
                print("✅ Admin account already exists")
        
        conn.commit()
        
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Database initialized with {len(tables)} tables")
        
        # Show table structures
        print("\n📋 Table Structures:")
        for table in ['hotel', 'ngo', 'food', 'admin', 'activity_log']:
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print(f"  {table}: {len(columns)} columns")
            except:
                pass
        
        conn.close()
    
    # ===== LOCATION CAPTURE FUNCTIONS =====
    
    def capture_location_by_ip(self, user_ip=None):
        """Capture location using IP address geolocation"""
        try:
            import geocoder  # Import here to avoid startup errors
            
            print(f"📍 Attempting to capture location for IP: {user_ip or 'current'}")
            g = geocoder.ip(user_ip or 'me')
            
            if g.latlng:
                location_data = {
                    'latitude': g.latlng[0],
                    'longitude': g.latlng[1],
                    'city': g.city,
                    'country': g.country,
                    'address': g.address if hasattr(g, 'address') else None,
                    'method': 'auto_ip',
                    'captured_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                print(f"✅ Location captured: {g.latlng[0]}, {g.latlng[1]} - {g.city}, {g.country}")
                return location_data
            else:
                print(f"⚠️ Could not determine location from IP: {g.status if hasattr(g, 'status') else 'Unknown error'}")
                return None
                
        except ImportError:
            print("❌ Geocoder package not installed. Run: pip install geocoder")
            return None
        except Exception as e:
            print(f"❌ Location capture error: {e}")
            return None
    
    def update_user_location(self, user_id, user_type, location_data):
        """Update user location in database"""
        try:
            if user_type not in ['hotel', 'ngo']:
                print(f"❌ Invalid user type: {user_type}")
                return False
            
            table = user_type
            
            query = f"""
            UPDATE {table} 
            SET latitude = ?, longitude = ?, 
                location_captured_at = ?, location_method = ?,
                location_city = ?, location_country = ?
            WHERE id = ?
            """
            
            params = (
                location_data['latitude'],
                location_data['longitude'],
                location_data['captured_at'],
                location_data['method'],
                location_data.get('city'),
                location_data.get('country'),
                user_id
            )
            
            result = self.execute_query(query, params)
            print(f"✅ Location updated for {user_type} ID {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating location: {e}")
            return False
    
    def capture_and_save_location(self, user_id, user_type, user_ip=None):
        """Capture and save location in one step - Main function for login"""
        try:
            print(f"📍 Capturing location for {user_type} ID {user_id}...")
            
            # First, check if location capture is available
            try:
                import geocoder
                location_available = True
            except ImportError:
                location_available = False
                print("⚠️ Geocoder package not installed. Location capture disabled.")
                print("💡 To enable: pip install geocoder")
            
            if not location_available:
                return None
            
            # Capture location
            location_data = self.capture_location_by_ip(user_ip)
            
            if location_data:
                # Save to database
                success = self.update_user_location(user_id, user_type, location_data)
                if success:
                    print(f"✅ Location successfully saved for {user_type} ID {user_id}")
                    return location_data
                else:
                    print(f"❌ Failed to save location for {user_type} ID {user_id}")
                    return None
            else:
                print(f"⚠️ No location data captured for {user_type} ID {user_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error in capture_and_save_location: {e}")
            return None
    
    def get_user_location(self, user_id, user_type):
        """Get user's location data"""
        try:
            if user_type not in ['hotel', 'ngo']:
                return None
            
            query = f"""
            SELECT latitude, longitude, location_captured_at, 
                   location_method, location_city, location_country
            FROM {user_type}
            WHERE id = ?
            """
            
            result = self.execute_query(query, (user_id,))
            if result and len(result) > 0:
                return dict(result[0])  # Convert Row to dict
            return None
            
        except Exception as e:
            print(f"❌ Error getting user location: {e}")
            return None
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in kilometers"""
        try:
            # Convert decimal degrees to radians
            lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
            lat1, lon1, lat2, lon2 = map(lambda x: x * math.pi / 180, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = (math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth radius in kilometers
            R = 6371.0
            
            distance = R * c
            return round(distance, 2)
        except Exception as e:
            print(f"❌ Error calculating distance: {e}")
            return None
    
    # ===== EXISTING DATABASE OPERATIONS =====
    
    def execute_query(self, query, params=()):
        """Execute a query with proper error handling"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.lastrowid
            
            conn.close()
            return result
        except sqlite3.Error as e:
            print(f"❌ Database error: {e}")
            print(f"   Query: {query[:100]}...")
            print(f"   Params: {params}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def get_user_by_email(self, email, user_type):
        """Get user by email based on user type"""
        try:
            # Use simple queries that work with any schema version
            if user_type == 'hotel':
                query = "SELECT * FROM hotel WHERE email = ?"
            elif user_type == 'ngo':
                query = "SELECT * FROM ngo WHERE email = ?"
            elif user_type == 'admin':
                query = "SELECT * FROM admin WHERE username = ?"
            else:
                return None
            
            result = self.execute_query(query, (email,))
            return result[0] if result and len(result) > 0 else None
        except Exception as e:
            print(f"❌ Error getting user: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def add_user(self, name, email, password, user_type, location="", contact=""):
        """Add a new user (hotel or NGO) to database"""
        try:
            if user_type == 'hotel':
                query = """
                INSERT INTO hotel (name, email, password, location, contact, 
                                  latitude, longitude, location_captured_at, location_method)
                VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)
                """
            elif user_type == 'ngo':
                query = """
                INSERT INTO ngo (name, email, password, location, contact,
                                latitude, longitude, location_captured_at, location_method)
                VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)
                """
            else:
                return False
            
            result = self.execute_query(query, (name, email, password, location, contact))
            return result is not None
        except sqlite3.IntegrityError:
            print(f"❌ User with email {email} already exists")
            return False
        except Exception as e:
            print(f"❌ Error adding user: {e}")
            return False
    
    def add_food(self, food_name, quantity, expiry_time, location, map_link, hotel_id, hotel_name):
        """Add new food entry to database with validation"""
        try:
            # Validate expiry time format
            if isinstance(expiry_time, str):
                # Ensure proper datetime format
                if 'T' in expiry_time:
                    expiry_time = expiry_time.replace('T', ' ') + ':00'
            
            query = """
            INSERT INTO food (food_name, quantity, expiry_time, location, map_link, hotel_id, hotel_name, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Available')
            """
            result = self.execute_query(query, (food_name, quantity, expiry_time, location, map_link, hotel_id, hotel_name))
            return result is not None
        except Exception as e:
            print(f"❌ Error adding food: {e}")
            return False
        
    def update_food_status(self, food_id, status, ngo_id=None):
        """Update food status with timestamp"""
        try:
            if status == 'Collected':
                query = """
                UPDATE food 
                SET status = ?, collected_time = datetime('now'), collected_by = ?
                WHERE id = ? AND status = 'Available'
                """
                params = (status, ngo_id, food_id)
            elif status == 'Delivered':
                query = """
                UPDATE food 
                SET status = ?, delivered_time = datetime('now')
                WHERE id = ? AND status = 'Collected' AND collected_by = ?
                """
                params = (status, food_id, ngo_id)
            else:
                query = "UPDATE food SET status = ? WHERE id = ?"
                params = (status, food_id)
            
            # Execute the query
            result = self.execute_query(query, params)
            return result is not None
        except Exception as e:
            print(f"❌ Error updating food status: {e}")
            return False
    
    def get_all_foods(self, status=None, ngo_location=None):
        """Get all food listings with optional status filter"""
        try:
            if status:
                query = """
                SELECT f.*, h.name as hotel_name_original, h.email as hotel_email
                FROM food f
                LEFT JOIN hotel h ON f.hotel_id = h.id
                WHERE f.status = ? 
                ORDER BY f.uploaded_time DESC
                """
                return self.execute_query(query, (status,))
            else:
                query = """
                SELECT f.*, h.name as hotel_name_original, h.email as hotel_email
                FROM food f
                LEFT JOIN hotel h ON f.hotel_id = h.id
                ORDER BY f.uploaded_time DESC
                """
                return self.execute_query(query)
        except Exception as e:
            print(f"❌ Error getting foods: {e}")
            return []
        
    def get_food_by_hotel(self, hotel_id):
        """Get all foods uploaded by a specific hotel"""
        try:
            query = """
            SELECT f.* 
            FROM food f
            WHERE f.hotel_id = ? 
            ORDER BY f.uploaded_time DESC
            """
            return self.execute_query(query, (hotel_id,))
        except Exception as e:
            print(f"❌ Error getting hotel foods: {e}")
            return []
    
    def get_food_by_id(self, food_id):
        """Get specific food item by ID with details"""
        try:
            query = """
            SELECT f.*, h.email as hotel_email, h.contact as hotel_contact
            FROM food f
            LEFT JOIN hotel h ON f.hotel_id = h.id
            WHERE f.id = ?
            """
            result = self.execute_query(query, (food_id,))
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Error getting food by ID: {e}")
            return None
    
    def get_all_hotels(self):
        """Get all registered hotels with food count"""
        try:
            query = """
            SELECT h.*, 
                   (SELECT COUNT(*) FROM food f WHERE f.hotel_id = h.id) as total_foods,
                   (SELECT COUNT(*) FROM food f WHERE f.hotel_id = h.id AND f.status = 'Delivered') as delivered_foods
            FROM hotel h
            ORDER BY h.registration_date DESC
            """
            return self.execute_query(query)
        except Exception as e:
            print(f"❌ Error getting hotels: {e}")
            return []
    
    def get_all_ngos(self):
        """Get all registered NGOs with collection count"""
        try:
            query = """
            SELECT n.*, 
                   (SELECT COUNT(*) FROM food f WHERE f.collected_by = n.id) as collected_foods,
                   (SELECT COUNT(*) FROM food f WHERE f.collected_by = n.id AND f.status = 'Delivered') as delivered_foods
            FROM ngo n
            ORDER BY n.registration_date DESC
            """
            return self.execute_query(query)
        except Exception as e:
            print(f"❌ Error getting NGOs: {e}")
            return []
    
    def get_stats(self):
        """Get comprehensive system statistics for admin dashboard"""
        stats = {}
        
        try:
            # Get counts
            hotels_result = self.execute_query("SELECT COUNT(*) as cnt FROM hotel")
            stats['total_hotels'] = hotels_result[0]['cnt'] if hotels_result and len(hotels_result) > 0 else 0
            
            ngos_result = self.execute_query("SELECT COUNT(*) as cnt FROM ngo")
            stats['total_ngos'] = ngos_result[0]['cnt'] if ngos_result and len(ngos_result) > 0 else 0
            
            all_foods = self.execute_query("SELECT * FROM food")
            stats['total_foods'] = len(all_foods) if all_foods else 0
            
            # Get status counts
            status_counts = self.execute_query("""
                SELECT status, COUNT(*) as count 
                FROM food 
                GROUP BY status
            """)
            
            # Initialize all counts to 0
            stats['available_foods'] = 0
            stats['collected_foods'] = 0
            stats['delivered_foods'] = 0
            
            if status_counts:
                for row in status_counts:
                    if hasattr(row, 'keys'):
                        row_dict = dict(row)
                        status = row_dict.get('status')
                        count = row_dict.get('count', 0)
                    else:
                        status = row[0] if len(row) > 0 else None
                        count = row[1] if len(row) > 1 else 0
                    
                    if status == 'Available':
                        stats['available_foods'] = count
                    elif status == 'Collected':
                        stats['collected_foods'] = count
                    elif status == 'Delivered':
                        stats['delivered_foods'] = count
            
            # Get recent activity
            recent_foods = self.execute_query("""
                SELECT f.food_name, f.uploaded_time, h.name as hotel_name, f.status
                FROM food f
                JOIN hotel h ON f.hotel_id = h.id
                ORDER BY f.uploaded_time DESC
                LIMIT 5
            """)
            
            # Convert Row objects to dicts
            recent_activity_list = []
            if recent_foods:
                for row in recent_foods:
                    if hasattr(row, 'keys'):
                        recent_activity_list.append(dict(row))
                    else:
                        recent_activity_list.append({
                            'food_name': row[0] if len(row) > 0 else '',
                            'uploaded_time': row[1] if len(row) > 1 else '',
                            'hotel_name': row[2] if len(row) > 2 else '',
                            'status': row[3] if len(row) > 3 else ''
                        })
            stats['recent_activity'] = recent_activity_list
            
            # Get daily summary
            daily_stats = self.execute_query("""
                SELECT DATE(uploaded_time) as date,
                       COUNT(*) as uploads,
                       SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) as delivered
                FROM food
                WHERE DATE(uploaded_time) >= DATE('now', '-7 days')
                GROUP BY DATE(uploaded_time)
                ORDER BY date DESC
            """)
            
            weekly_summary_list = []
            if daily_stats:
                for row in daily_stats:
                    if hasattr(row, 'keys'):
                        weekly_summary_list.append(dict(row))
                    else:
                        weekly_summary_list.append({
                            'date': row[0] if len(row) > 0 else '',
                            'uploads': row[1] if len(row) > 1 else 0,
                            'delivered': row[2] if len(row) > 2 else 0
                        })
            stats['weekly_summary'] = weekly_summary_list
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            import traceback
            traceback.print_exc()
            # Set default values
            stats = {
                'total_hotels': 0,
                'total_ngos': 0,
                'total_foods': 0,
                'available_foods': 0,
                'collected_foods': 0,
                'delivered_foods': 0,
                'recent_activity': [],
                'weekly_summary': []
            }
        
        return stats
    
    def backup_database(self, backup_name=None):
        """Create a backup of the database"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"food_backup_{timestamp}.db"
            
            source = sqlite3.connect(self.db_name)
            backup = sqlite3.connect(backup_name)
            
            source.backup(backup)
            
            source.close()
            backup.close()
            
            print(f"✅ Database backed up to: {backup_name}")
            return backup_name
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None

# Create global database instance
db = Database()

if __name__ == "__main__":
    print("\n🧪 DATABASE TEST MODULE")
    print("=" * 60)
    
    # Test connection
    print("1. Testing database connection...")
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        print(f"   ✅ SQLite version: {version}")
        conn.close()
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
    
    # Test tables
    print("\n2. Checking tables...")
    tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
    if tables:
        for table in tables:
            count = db.execute_query(f"SELECT COUNT(*) as cnt FROM {table['name']}")
            print(f"   📁 {table['name']}: {count[0]['cnt'] if count else 0} records")
    
    # Test admin account
    print("\n3. Testing admin access...")
    admin = db.get_user_by_email('admin', 'admin')
    print(f"   ✅ Admin account: {'Found' if admin else 'Not found'}")
    
    # Test location columns
    print("\n4. Checking location columns...")
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check hotel columns
        cursor.execute("PRAGMA table_info(hotel)")
        hotel_cols = [col[1] for col in cursor.fetchall()]
        print(f"   🏨 Hotel columns: {len(hotel_cols)} total")
        print(f"   📍 Has location columns: {'latitude' in hotel_cols and 'longitude' in hotel_cols}")
        
        # Check NGO columns
        cursor.execute("PRAGMA table_info(ngo)")
        ngo_cols = [col[1] for col in cursor.fetchall()]
        print(f"   🤝 NGO columns: {len(ngo_cols)} total")
        print(f"   📍 Has location columns: {'latitude' in ngo_cols and 'longitude' in ngo_cols}")
        
        conn.close()
    except Exception as e:
        print(f"   ❌ Error checking columns: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Database module is ready!")
    print("\n💡 To enable location capture:")
    print("   1. Install geocoder: pip install geocoder")
    print("   2. Restart the application")