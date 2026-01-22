# [file name]: admin.py
# [file location]: root folder
# [Purpose]: Admin blueprint for system administration

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
import database
from datetime import datetime

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Database instance
db = database.db

# Admin login decorator
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            flash('Please login as admin first!', 'error')
            return redirect(url_for('login', user_type='admin'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== ADMIN ROUTES ====================

# Admin Dashboard
@admin_bp.route('/dashboard')
@admin_login_required
def dashboard():
    """Admin Dashboard with system statistics"""
    try:
        print("\n🔵 ADMIN DASHBOARD ACCESSED")
        
        # Get comprehensive statistics
        stats = {}
        
        # Count hotels
        hotels_count = db.execute_query("SELECT COUNT(*) as cnt FROM hotel")
        stats['total_hotels'] = hotels_count[0]['cnt'] if hotels_count else 0
        
        # Count NGOs
        ngos_count = db.execute_query("SELECT COUNT(*) as cnt FROM ngo")
        stats['total_ngos'] = ngos_count[0]['cnt'] if ngos_count else 0
        
        # Count foods
        foods_count = db.execute_query("SELECT COUNT(*) as cnt FROM food")
        stats['total_foods'] = foods_count[0]['cnt'] if foods_count else 0
        
        # Count delivered foods
        delivered_count = db.execute_query("SELECT COUNT(*) as cnt FROM food WHERE status = 'Delivered'")
        stats['delivered_foods'] = delivered_count[0]['cnt'] if delivered_count else 0
        
        # Count available foods
        available_count = db.execute_query("SELECT COUNT(*) as cnt FROM food WHERE status = 'Available'")
        stats['available_foods'] = available_count[0]['cnt'] if available_count else 0
        
        # Count collected foods
        collected_count = db.execute_query("SELECT COUNT(*) as cnt FROM food WHERE status = 'Collected'")
        stats['collected_foods'] = collected_count[0]['cnt'] if collected_count else 0
        
        # Get recent activity (last 10 activities)
        recent_activity = db.execute_query("""
            SELECT 
                f.food_name, 
                h.name as hotel_name, 
                f.status, 
                f.uploaded_time,
                CASE 
                    WHEN f.status = 'Collected' AND f.collected_time IS NOT NULL THEN f.collected_time
                    WHEN f.status = 'Delivered' AND f.delivered_time IS NOT NULL THEN f.delivered_time
                    ELSE f.uploaded_time
                END as activity_time,
                CASE 
                    WHEN f.status = 'Collected' THEN '📦 Collected'
                    WHEN f.status = 'Delivered' THEN '✅ Delivered'
                    ELSE '📤 Uploaded'
                END as activity_type
            FROM food f 
            LEFT JOIN hotel h ON f.hotel_id = h.id 
            ORDER BY activity_time DESC 
            LIMIT 10
        """)
        
        # Get all hotels (limit to 5 for dashboard)
        hotels = db.execute_query("SELECT * FROM hotel ORDER BY registration_date DESC LIMIT 5")
        
        # Get all NGOs (limit to 5 for dashboard)
        ngos = db.execute_query("SELECT * FROM ngo ORDER BY registration_date DESC LIMIT 5")
        
        # Get recent foods (limit to 5 for dashboard)
        foods = db.execute_query("""
            SELECT f.*, h.name as hotel_name 
            FROM food f 
            LEFT JOIN hotel h ON f.hotel_id = h.id 
            ORDER BY f.uploaded_time DESC 
            LIMIT 5
        """)
        
        # Calculate success rate
        success_rate = 0
        if stats['total_foods'] > 0:
            success_rate = round((stats['delivered_foods'] / stats['total_foods']) * 100, 1)
        
        # Get today's date for filtering
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Count today's registrations
        today_hotels = db.execute_query("""
            SELECT COUNT(*) as cnt FROM hotel 
            WHERE DATE(registration_date) = ?
        """, (today,))
        stats['today_hotels'] = today_hotels[0]['cnt'] if today_hotels else 0
        
        today_ngos = db.execute_query("""
            SELECT COUNT(*) as cnt FROM ngo 
            WHERE DATE(registration_date) = ?
        """, (today,))
        stats['today_ngos'] = today_ngos[0]['cnt'] if today_ngos else 0
        
        return render_template('admin_dashboard.html',
                             stats=stats,
                             hotels=hotels,
                             ngos=ngos,
                             foods=foods,
                             recent_activity=recent_activity,
                             success_rate=success_rate,
                             now=datetime.now(),
                             db=db)
    except Exception as e:
        print(f"❌ Admin dashboard error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading dashboard: {str(e)[:100]}', 'error')
        return redirect(url_for('login', user_type='admin'))

# View All Users (Main users page)
@admin_bp.route('/users')
@admin_login_required
def view_users():
    """View all registered users - MAIN USERS PAGE"""
    try:
        # Get all hotels
        hotels = db.execute_query("SELECT * FROM hotel ORDER BY registration_date DESC")
        
        # Get all NGOs
        ngos = db.execute_query("SELECT * FROM ngo ORDER BY registration_date DESC")
        
        return render_template('admin_users.html',
                             hotels=hotels,
                             ngos=ngos)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

# View All Hotels - NEW ROUTE
@admin_bp.route('/all_hotels')
@admin_bp.route('/hotels')
@admin_login_required
def view_hotels():
    """View all hotels specifically"""
    try:
        # Get all hotels with details
        hotels = db.execute_query("""
            SELECT h.*, COUNT(f.id) as total_foods,
                   SUM(CASE WHEN f.status = 'Delivered' THEN 1 ELSE 0 END) as delivered_foods
            FROM hotel h
            LEFT JOIN food f ON h.id = f.hotel_id
            GROUP BY h.id
            ORDER BY h.registration_date DESC
        """)
        
        return render_template('admin_hotels.html',
                             hotels=hotels,
                             title="All Hotels")
    except Exception as e:
        print(f"Error loading hotels: {str(e)}")
        flash(f'Error loading hotels: {str(e)[:100]}', 'error')
        return redirect(url_for('admin.dashboard'))

# View All NGOs - NEW ROUTE
@admin_bp.route('/all_ngos')
@admin_bp.route('/ngos')
@admin_login_required
def view_ngos():
    """View all NGOs specifically"""
    try:
        # Get all NGOs with details
        ngos = db.execute_query("""
            SELECT n.*, 
                   COUNT(CASE WHEN f.status = 'Collected' THEN 1 END) as collected_foods,
                   COUNT(CASE WHEN f.status = 'Delivered' THEN 1 END) as delivered_foods
            FROM ngo n
            LEFT JOIN food f ON n.id = f.collected_by
            GROUP BY n.id
            ORDER BY n.registration_date DESC
        """)
        
        return render_template('admin_ngos.html',
                             ngos=ngos,
                             title="All NGOs")
    except Exception as e:
        print(f"Error loading NGOs: {str(e)}")
        flash(f'Error loading NGOs: {str(e)[:100]}', 'error')
        return redirect(url_for('admin.dashboard'))

# View All Food Items
@admin_bp.route('/foods')
@admin_login_required
def view_foods():
    """View all food items"""
    try:
        # Get status filter from URL
        status_filter = request.args.get('status', '')
        
        # Build query based on filter
        if status_filter:
            query = """
                SELECT f.*, h.name as hotel_name, n.name as ngo_name
                FROM food f
                LEFT JOIN hotel h ON f.hotel_id = h.id
                LEFT JOIN ngo n ON f.collected_by = n.id
                WHERE f.status = ?
                ORDER BY f.uploaded_time DESC
            """
            foods = db.execute_query(query, (status_filter,))
        else:
            query = """
                SELECT f.*, h.name as hotel_name, n.name as ngo_name
                FROM food f
                LEFT JOIN hotel h ON f.hotel_id = h.id
                LEFT JOIN ngo n ON f.collected_by = n.id
                ORDER BY f.uploaded_time DESC
            """
            foods = db.execute_query(query)
        
        # Get status counts for filter
        status_counts = {}
        statuses = ['Available', 'Collected', 'Delivered']
        for status in statuses:
            count_result = db.execute_query("SELECT COUNT(*) as cnt FROM food WHERE status = ?", (status,))
            status_counts[status] = count_result[0]['cnt'] if count_result else 0
        
        # Get total stats
        total_foods = sum(status_counts.values())
        
        # Get dashboard stats
        stats = {
            'total_foods': total_foods,
            'delivered_foods': status_counts.get('Delivered', 0)
        }
        
        return render_template('admin_foods.html',
                             foods=foods,
                             status_filter=status_filter,
                             status_counts=status_counts,
                             total_foods=total_foods,
                             stats=stats,
                             db=db)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

# Delete User
@admin_bp.route('/delete-user/<user_type>/<int:user_id>', methods=['POST'])
@admin_login_required
def delete_user(user_type, user_id):
    """Delete a user (hotel or NGO)"""
    try:
        if user_type == 'hotel':
            # Check if hotel has any food items
            food_check = db.execute_query("SELECT COUNT(*) as cnt FROM food WHERE hotel_id = ?", (user_id,))
            if food_check and food_check[0]['cnt'] > 0:
                flash(f'Cannot delete hotel #{user_id}. It has {food_check[0]["cnt"]} food items!', 'error')
            else:
                db.execute_query("DELETE FROM hotel WHERE id = ?", (user_id,))
                flash(f'Hotel #{user_id} deleted successfully!', 'success')
        elif user_type == 'ngo':
            # Check if NGO has collected any food
            food_check = db.execute_query("SELECT COUNT(*) as cnt FROM food WHERE collected_by = ?", (user_id,))
            if food_check and food_check[0]['cnt'] > 0:
                flash(f'Cannot delete NGO #{user_id}. It has collected {food_check[0]["cnt"]} food items!', 'error')
            else:
                db.execute_query("DELETE FROM ngo WHERE id = ?", (user_id,))
                flash(f'NGO #{user_id} deleted successfully!', 'success')
        else:
            flash('Invalid user type!', 'error')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin.view_users'))

# Update Food Status (Admin override)
@admin_bp.route('/update-food-status/<int:food_id>', methods=['POST'])
@admin_login_required
def update_food_status(food_id):
    """Admin update food status"""
    try:
        new_status = request.form.get('status')
        db.execute_query("UPDATE food SET status = ? WHERE id = ?", (new_status, food_id))
        flash(f'Food #{food_id} status updated to {new_status}!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin.view_foods'))

# View Single Hotel
@admin_bp.route('/view_hotel/<int:hotel_id>')
@admin_login_required
def view_hotel(hotel_id):
    """View detailed information about a specific hotel"""
    try:
        hotel = db.execute_query("SELECT * FROM hotel WHERE id = ?", (hotel_id,))
        if not hotel:
            flash(f'Hotel #{hotel_id} not found!', 'error')
            return redirect(url_for('admin.view_hotels'))
        
        # Get hotel's food donations
        foods = db.execute_query("""
            SELECT * FROM food 
            WHERE hotel_id = ? 
            ORDER BY uploaded_time DESC
        """, (hotel_id,))
        
        return render_template('admin_view_hotel.html',
                             hotel=hotel[0],
                             foods=foods)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.view_hotels'))

# View Single NGO
@admin_bp.route('/view_ngo/<int:ngo_id>')
@admin_login_required
def view_ngo(ngo_id):
    """View detailed information about a specific NGO"""
    try:
        ngo = db.execute_query("SELECT * FROM ngo WHERE id = ?", (ngo_id,))
        if not ngo:
            flash(f'NGO #{ngo_id} not found!', 'error')
            return redirect(url_for('admin.view_ngos'))
        
        # Get NGO's collected foods
        foods = db.execute_query("""
            SELECT f.*, h.name as hotel_name
            FROM food f
            JOIN hotel h ON f.hotel_id = h.id
            WHERE f.collected_by = ?
            ORDER BY f.collected_time DESC
        """, (ngo_id,))
        
        return render_template('admin_view_ngo.html',
                             ngo=ngo[0],
                             foods=foods)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.view_ngos'))

# System Settings
@admin_bp.route('/settings')
@admin_login_required
def settings():
    """System settings page"""
    return render_template('admin_settings.html')

# Admin Logout
@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.clear()
    flash('Admin logged out successfully!', 'success')
    return redirect(url_for('home'))

# Debug route for testing
@admin_bp.route('/debug/db')
@admin_login_required
def debug_db():
    """Debug database connection"""
    try:
        result = "<h1>Database Debug Info</h1>"
        
        # Test hotel table
        hotels = db.execute_query("SELECT COUNT(*) as cnt FROM hotel")
        result += f"<p>Hotels: {hotels[0]['cnt'] if hotels else 0}</p>"
        
        # Test NGO table
        ngos = db.execute_query("SELECT COUNT(*) as cnt FROM ngo")
        result += f"<p>NGOs: {ngos[0]['cnt'] if ngos else 0}</p>"
        
        # Test food table
        foods = db.execute_query("SELECT COUNT(*) as cnt FROM food")
        result += f"<p>Foods: {foods[0]['cnt'] if foods else 0}</p>"
        
        # List all tables
        tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        result += "<h2>Tables:</h2><ul>"
        for table in tables:
            result += f"<li>{table['name']}</li>"
        result += "</ul>"
        
        return result
    except Exception as e:
        return f"<h1>Error</h1><pre>{str(e)}</pre>"