# [file name]: ngo.py
# [file location]: root folder

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import database
# After successful login:
from database import db

# Create Blueprint
ngo_bp = Blueprint('ngo', __name__, url_prefix='/ngo')
db = database.db

def ngo_login_required(f):
    """Decorator to check if NGO is logged in"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'ngo':
            flash('Please login as NGO first!', 'error')
            return redirect(url_for('login', user_type='ngo'))
        return f(*args, **kwargs)
    return decorated_function

@ngo_bp.route('/collect/<int:food_id>')
@ngo_login_required
def collect_food(food_id):
    """Mark food as collected - FIXED FOR SQLITE"""
    try:
        ngo_id = session['user_id']
        
        # Check if food exists - FIXED: Use ? for SQLite
        food_result = db.execute_query("SELECT * FROM food WHERE id = ?", (food_id,))
        
        if not food_result or len(food_result) == 0:
            flash('Food not found!', 'error')
            return redirect(url_for('ngo_dashboard'))
        
        food = food_result[0]
        
        # Convert SQLite Row to dict
        if hasattr(food, 'keys'):
            food_dict = dict(food)
        else:
            # Handle tuple format if needed
            food_dict = {
                'id': food[0] if len(food) > 0 else None,
                'food_name': food[1] if len(food) > 1 else 'Unknown',
                'status': food[8] if len(food) > 8 else 'Unknown',
                'hotel_id': food[6] if len(food) > 6 else None
            }
        
        food_status = food_dict.get('status', 'Unknown')
        
        if food_status != 'Available':
            flash(f'Food is no longer available! Current status: {food_status}', 'error')
            return redirect(url_for('ngo_dashboard'))
        
        # Use your existing update_food_status method
        success = db.update_food_status(food_id, 'Collected', ngo_id)
        
        if success:
            flash('✅ Food collected successfully! Please arrange pickup.', 'success')
        else:
            flash('❌ Failed to collect food. It may have been collected by someone else.', 'error')
    
    except Exception as e:
        print(f"Error collecting food: {e}")
        flash(f'Error: {str(e)[:100]}', 'error')
    
    return redirect(url_for('ngo_dashboard'))
@ngo_bp.route('/deliver/<int:food_id>')
@ngo_login_required
def deliver_food(food_id):
    """Mark food as delivered - SIMPLIFIED FIXED VERSION"""
    try:
        ngo_id = session['user_id']
        ngo_name = session['user_name']
        
        print(f"\n🚚 DELIVER ATTEMPT - Food ID: {food_id}, NGO ID: {ngo_id}")
        
        # SIMPLE DIRECT UPDATE - This should work
        success = db.execute_query("""
            UPDATE food 
            SET status = 'Delivered', 
                delivered_time = datetime('now')
            WHERE id = ? 
            AND status = 'Collected' 
            AND collected_by = ?
        """, (food_id, ngo_id))
        
        print(f"   Update result: {success}")
        
        if success:
            # Get food name for message
            food_result = db.execute_query("SELECT food_name FROM food WHERE id = ?", (food_id,))
            food_name = "Unknown"
            if food_result and len(food_result) > 0:
                if hasattr(food_result[0], 'keys'):
                    food_name = dict(food_result[0]).get('food_name', 'Unknown')
                else:
                    food_name = food_result[0][0] if len(food_result[0]) > 0 else 'Unknown'
            
            flash(f'✅ Food "{food_name}" marked as delivered! Thank you for your service.', 'success')
            print(f"   ✅ Delivery successful for food {food_id}")
            
        else:
            # Check why it failed
            check_food = db.execute_query("SELECT * FROM food WHERE id = ?", (food_id,))
            if check_food and len(check_food) > 0:
                if hasattr(check_food[0], 'keys'):
                    food_data = dict(check_food[0])
                    status = food_data.get('status', 'Unknown')
                    collected_by = food_data.get('collected_by')
                else:
                    status = check_food[0][8] if len(check_food[0]) > 8 else 'Unknown'
                    collected_by = check_food[0][10] if len(check_food[0]) > 10 else None
                
                print(f"   Current food status: {status}, Collected by: {collected_by}")
                
                if status != 'Collected':
                    flash('Food must be collected first!', 'error')
                elif collected_by != ngo_id:
                    flash('You can only deliver food you collected!', 'error')
                else:
                    flash('Failed to update status. Please try again.', 'error')
            else:
                flash('Food not found!', 'error')
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    return redirect(url_for('ngo_dashboard'))

@ngo_bp.route('/cancel_collect/<int:food_id>')
@ngo_login_required
def cancel_collect(food_id):
    """Cancel food collection (make it available again)"""
    try:
        ngo_id = session['user_id']
        
        # Check if food exists and was collected by this NGO
        food_result = db.execute_query("SELECT * FROM food WHERE id = ? AND collected_by = ?", (food_id, ngo_id))
        
        if not food_result or len(food_result) == 0:
            flash('Cannot cancel! Food not found or not collected by you.', 'error')
        else:
            # Reset food status to Available
            success = db.execute_query("""
                UPDATE food 
                SET status = 'Available', collected_by = NULL, collected_time = NULL
                WHERE id = ? AND collected_by = ?
            """, (food_id, ngo_id))
            
            if success:
                flash('Collection cancelled! Food is now available for other NGOs.', 'success')
            else:
                flash('Failed to cancel collection!', 'error')
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('ngo_dashboard'))

# Test
if __name__ == "__main__":
    print("✅ NGO module loaded successfully")