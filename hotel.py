# [file name]: hotel.py
# [file location]: root folder

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import database
from datetime import datetime
# After successful login:
from database import db

# Create Blueprint
hotel_bp = Blueprint('hotel', __name__, url_prefix='/hotel')
db = database.db

@hotel_bp.route('/upload', methods=['POST'])
def upload_food():
    """Handle food upload from hotel with map"""
    if 'user_type' not in session or session['user_type'] != 'hotel':
        flash('Please login as hotel first!', 'error')
        return redirect(url_for('login', user_type='hotel'))
    
    try:
        # Get form data
        food_name = request.form.get('food_name')
        quantity = request.form.get('quantity')
        expiry_time = request.form.get('expiry_time')
        location = request.form.get('location')
        map_link = request.form.get('map_link', '')
        
        print(f"\n📝 UPLOADING FOOD DETAILS:")
        print(f"   Food Name: {food_name}")
        print(f"   Quantity: {quantity}")
        print(f"   Expiry Time: {expiry_time}")
        print(f"   Location: {location}")
        print(f"   Map Link: {map_link[:50] if map_link else 'None'}...")
        print(f"   Hotel ID: {session.get('user_id')}")
        print(f"   Hotel Name: {session.get('user_name')}")
        
        # Validate
        if not all([food_name, quantity, expiry_time, location]):
            flash('All fields except map are required!', 'error')
            return redirect(url_for('hotel_dashboard'))
        
        hotel_id = session['user_id']
        hotel_name = session['user_name']
        
        # Format expiry time for database
        # The datetime-local input format is: YYYY-MM-DDTHH:MM
        if expiry_time:
            expiry_time = expiry_time.replace('T', ' ') + ':00'
        
        print(f"   Formatted Expiry: {expiry_time}")
        
        # Add to database with map link
        result = db.add_food(food_name, quantity, expiry_time, location, map_link, hotel_id, hotel_name)
        
        print(f"   Database Result: {result}")
        
        if result:
            flash('Food uploaded successfully! NGOs can see the location map.', 'success')
        else:
            flash('Error uploading food to database. Please check the data.', 'error')
        
        return redirect(url_for('hotel_dashboard'))
        
    except Exception as e:
        print(f"❌ UPLOAD ERROR: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('hotel_dashboard'))

@hotel_bp.route('/delete/<int:food_id>')
def delete_food(food_id):
    """Delete food item"""
    if 'user_type' not in session or session['user_type'] != 'hotel':
        flash('Unauthorized!', 'error')
        return redirect(url_for('hotel_dashboard'))
    
    try:
        # Check if food belongs to this hotel
        food = db.get_food_by_id(food_id)
        
        if not food:
            flash('Food not found!', 'error')
        elif food['hotel_id'] != session['user_id']:
            flash('You can only delete your own food!', 'error')
        elif food['status'] != 'Available':
            flash('Cannot delete food that is already collected!', 'error')
        else:
            # Delete from database
            db.execute_query("DELETE FROM food WHERE id = ?", (food_id,))
            flash('Food deleted successfully!', 'success')
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('hotel_dashboard'))

# Test
if __name__ == "__main__":
    print("Hotel module loaded")