# [file name]: app.py
# [file location]: root folder
# [Purpose]: Main Flask application with improved routing and error handling

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import database
import auth
from hotel import hotel
from ngo import ngo_bp
from admin import admin_bp

app = Flask(__name__)
app.secret_key = 'save2serve_secret_key_2024_secure_123'

# Configuration - UPDATED SESSION SETTINGS
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'save2serve_secret_key_2024_secure_123'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_NAME'] = 'save2serve_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Register Blueprints with proper error handling
try:
    app.register_blueprint(hotel_bp)
    app.register_blueprint(ngo_bp)
    app.register_blueprint(admin_bp)
    print("✅ Blueprints registered successfully")
except Exception as e:
    print(f"❌ Error registering blueprints: {e}")

# Initialize database
db = database.db

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(e):
    return '<h1>404 - Page Not Found</h1><p>The page you requested does not exist.</p><p><a href="/">Go Home</a></p>', 404

@app.errorhandler(500)
def internal_server_error(e):
    print(f"❌ Server Error: {e}")
    return '<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p><p><a href="/">Go Home</a></p>', 500

# ==================== MAIN ROUTES ====================

@app.route('/')
def home():
    """Home page with system statistics"""
    try:
        # Get basic stats for home page
        stats = {
            'hotels': db.execute_query("SELECT COUNT(*) as cnt FROM hotel")[0]['cnt'],
            'ngos': db.execute_query("SELECT COUNT(*) as cnt FROM ngo")[0]['cnt'],
            'foods_saved': db.execute_query("SELECT COUNT(*) as cnt FROM food WHERE status = 'Delivered'")[0]['cnt']
        }
        return render_template('index.html', stats=stats)
    except Exception as e:
        print(f"❌ Error loading home: {e}")
        return render_template('index.html', stats={'hotels': 0, 'ngos': 0, 'foods_saved': 0})

@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    """Handle login for all user types with enhanced security"""
    if user_type not in ['hotel', 'ngo', 'admin']:
        flash('Invalid user type!', 'error')
        return redirect(url_for('home'))
    
    # Clear any existing session
    if 'user_id' in session and session.get('user_type') != user_type:
        session.clear()
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        print(f"\n=== LOGIN ATTEMPT ===")
        print(f"User Type: {user_type}")
        print(f"Email: {email}")
        
        # Basic validation
        if not email or not password:
            flash('Email and password are required!', 'error')
            return render_template(f'{user_type}_login.html')
        
        # Authenticate user
        user = auth.authenticate_user(email, password, user_type)
        
        if user:
            print(f"✅ Login successful for {user.get('name', 'User')}")
            
            # Store user info in session - FIXED: Ensure all session data is set
            session.permanent = True
            session['user_id'] = user['id']
            session['user_type'] = user_type
            session['user_name'] = user.get('name', user.get('username', 'User'))
            session['user_email'] = user.get('email', email)
            session['login_time'] = datetime.now().isoformat()
            
            # Debug session
            print(f"SESSION DATA SET: user_id={session.get('user_id')}, user_type={session.get('user_type')}")
            
            flash('Login successful!', 'success')
            
            # Redirect to dashboard
            if user_type == 'hotel':
                return redirect(url_for('hotel_dashboard'))
            elif user_type == 'ngo':
                return redirect(url_for('ngo_dashboard'))
            elif user_type == 'admin':
                return redirect(url_for('admin.dashboard'))
        else:
            print(f"❌ Login failed for {email}")
            flash('Invalid email or password!', 'error')
    
    # GET request - render login page
    return render_template(f'{user_type}_login.html')

@app.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):
    """Handle registration for hotels and NGOs with validation"""
    if user_type not in ['hotel', 'ngo']:
        flash('Invalid user type!', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        location = request.form.get('location', '').strip()
        contact = request.form.get('contact', '').strip()
        
        print(f"\n=== REGISTRATION ATTEMPT ===")
        print(f"User Type: {user_type}")
        print(f"Name: {name}")
        print(f"Email: {email}")
        
        # Validation
        errors = []
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters')
        if not email or '@' not in email:
            errors.append('Valid email is required')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        elif auth.register_user(name, email, password, user_type, location, contact):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login', user_type=user_type))
        else:
            flash('Email already exists!', 'error')
    
    return render_template(f'{user_type}_register.html')

@app.route('/hotel/dashboard')
def hotel_dashboard():
    """Hotel dashboard with food management"""
    if 'user_type' not in session or session['user_type'] != 'hotel':
        print(f"❌ Hotel dashboard access denied. Session: {dict(session)}")
        flash('Please login as hotel first!', 'error')
        return redirect(url_for('login', user_type='hotel'))
    
    try:
        hotel_id = session['user_id']
        foods = db.get_food_by_hotel(hotel_id)
        
        # Get hotel statistics
        stats = {
            'total_uploads': len(foods) if foods else 0,
            'available': len([f for f in foods if f['status'] == 'Available']) if foods else 0,
            'collected': len([f for f in foods if f['status'] == 'Collected']) if foods else 0,
            'delivered': len([f for f in foods if f['status'] == 'Delivered']) if foods else 0,
        }
        
        return render_template('hotel_dashboard.html',
                             hotel_name=session['user_name'],
                             foods=foods,
                             stats=stats,
                             db=db)
    except Exception as e:
        print(f"❌ Hotel dashboard error: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading dashboard', 'error')
        return redirect(url_for('login', user_type='hotel'))

@app.route('/ngo/dashboard')
def ngo_dashboard():
    """NGO dashboard with real-time food updates"""
    if 'user_type' not in session or session['user_type'] != 'ngo':
        print(f"❌ NGO dashboard access denied. Session: {dict(session)}")
        flash('Please login as NGO first!', 'error')
        return redirect(url_for('login', user_type='ngo'))
    
    try:
        ngo_id = session['user_id']
        
        # Get all foods with details
        foods_db = db.execute_query("""
            SELECT f.*, h.name as hotel_name, h.contact as hotel_contact, h.email as hotel_email,
                   n.name as collected_ngo_name, n.contact as ngo_contact
            FROM food f
            LEFT JOIN hotel h ON f.hotel_id = h.id
            LEFT JOIN ngo n ON f.collected_by = n.id
            WHERE f.status IN ('Available', 'Collected', 'Delivered')
            ORDER BY 
                CASE f.status
                    WHEN 'Available' THEN 1
                    WHEN 'Collected' THEN 2
                    WHEN 'Delivered' THEN 3
                    ELSE 4
                END,
                f.expiry_time ASC
        """)
        
        # Convert to list of dictionaries
        food_list = []
        if foods_db:
            for food in foods_db:
                food_dict = dict(food)
                food_list.append(food_dict)
        
        # Get NGO statistics
        stats = {
            'available': len([f for f in food_list if f['status'] == 'Available']),
            'collected': len([f for f in food_list if f.get('collected_by') == ngo_id and f['status'] == 'Collected']),
            'delivered': len([f for f in food_list if f.get('collected_by') == ngo_id and f['status'] == 'Delivered']),
            'total_collected': len([f for f in food_list if f.get('collected_by') == ngo_id])
        }
        
        return render_template('ngo_dashboard.html',
                             ngo_name=session['user_name'],
                             foods=food_list,
                             stats=stats,
                             ngo_id=ngo_id,
                             db=db)
    except Exception as e:
        print(f"❌ NGO dashboard error: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading dashboard', 'error')
        return redirect(url_for('login', user_type='ngo'))

@app.route('/hotel/login')
def hotel_login():
    return redirect(url_for('login', user_type='hotel'))

@app.route('/ngo/login')
def ngo_login():
    return redirect(url_for('login', user_type='ngo'))

@app.route('/admin/login')
def admin_login():
    return redirect(url_for('login', user_type='admin'))

@app.route('/hotel/register')
def hotel_register():
    return redirect(url_for('register', user_type='hotel'))

@app.route('/ngo/register')
def ngo_register():
    return redirect(url_for('register', user_type='ngo'))

@app.route('/logout')
def logout():
    """Secure logout with session clearing"""
    user_type = session.get('user_type', 'Guest')
    user_name = session.get('user_name', 'User')
    
    session.clear()
    flash(f'Goodbye {user_name}! You have been logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/about')
def about():
    """About page"""
    return '<h1>About SAVE2SERVE HUB</h1><p>Food Exchange System</p>'

@app.route('/contact')
def contact():
    """Contact page"""
    return '<h1>Contact Us</h1><p>Email: contact@save2serve.com</p>'

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics (for potential future use)"""
    try:
        stats = {
            'hotels': db.execute_query("SELECT COUNT(*) as cnt FROM hotel")[0]['cnt'],
            'ngos': db.execute_query("SELECT COUNT(*) as cnt FROM ngo")[0]['cnt'],
            'total_foods': db.execute_query("SELECT COUNT(*) as cnt FROM food")[0]['cnt'],
            'delivered_foods': db.execute_query("SELECT COUNT(*) as cnt FROM food WHERE status = 'Delivered'")[0]['cnt'],
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db.execute_query("SELECT 1")
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== MIDDLEWARE FOR SESSION DEBUG ====================

@app.before_request
def before_request():
    """Debug middleware to check session state"""
    if request.endpoint and ('ngo' in request.endpoint or 'collect' in request.endpoint or 'deliver' in request.endpoint):
        print(f"\n🔍 BEFORE REQUEST: {request.endpoint}")
        print(f"   Session: user_id={session.get('user_id')}, user_type={session.get('user_type')}")
        print(f"   Path: {request.path}")

@app.route('/check-food/<int:food_id>')
def check_food(food_id):
    """Simple debug route to check food status"""
    if 'user_type' not in session:
        return "Not logged in"
    
    food = db.execute_query("SELECT * FROM food WHERE id = ?", (food_id,))
    if food:
        return f"Food {food_id}: Status = {dict(food[0]).get('status', 'Unknown')}"
    else:
        return f"Food {food_id} not found"

        # Add these routes to your app.py

@app.route('/test/admin-routes')
def test_admin_routes():
    """Test all admin routes"""
    return '''
    <h1>Admin Route Test</h1>
    <ul>
        <li><a href="/admin/dashboard">Dashboard</a></li>
        <li><a href="/admin/users">All Users</a></li>
        <li><a href="/admin/hotels">All Hotels</a></li>
        <li><a href="/admin/ngos">All NGOs</a></li>
        <li><a href="/admin/foods">All Foods</a></li>
        <li><a href="/admin/debug/db">Debug Database</a></li>
    </ul>
    '''

@app.route('/test/session')
def test_session():
    """Test session for admin"""
    session['user_id'] = 1
    session['user_type'] = 'admin'
    session['user_name'] = 'Test Admin'
    return 'Session set for admin. <a href="/admin/dashboard">Go to Dashboard</a>'


        



# ==================== MAIN APPLICATION ====================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 SAVE2SERVE HUB - Food Exchange System")
    print("=" * 60)
    print("📁 Database: food.db (Persistent Storage)")
    print("👥 User Types: Hotel, NGO, Admin")
    print("📊 Data: All records are stored permanently")
    print("🔄 Restart Safe: Data persists across restarts")
    print("🌐 Server: http://localhost:5000")
    print("=" * 60)
    
    try:
        # Perform database health check
        print("🔍 Performing system check...")
        
        # Check if database is accessible
        test_result = db.execute_query("SELECT sqlite_version()")
        if test_result:
            print(f"✅ Database: Connected (SQLite {test_result[0][0]})")
        else:
            print("⚠️  Database: Check failed")
        
        # Check admin access
        admin = db.get_user_by_email('admin', 'admin')
        print(f"✅ Admin Account: {'Found' if admin else 'Not found'}")
        
        # Count records
        hotels = db.execute_query("SELECT COUNT(*) as cnt FROM hotel")
        ngos = db.execute_query("SELECT COUNT(*) as cnt FROM ngo")
        foods = db.execute_query("SELECT COUNT(*) as cnt FROM food")
        
        print(f"📊 Records: {hotels[0]['cnt'] if hotels else 0} Hotels, "
              f"{ngos[0]['cnt'] if ngos else 0} NGOs, "
              f"{foods[0]['cnt'] if foods else 0} Food items")
        
        print("\n✅ System ready! Starting Flask server...")
        print("=" * 60)
        
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Check if food.db exists in the project folder")
        print("2. Check file permissions")
        print("3. Try running: python setup.py (to recreate database)")
        print("4. Check if port 5000 is available")