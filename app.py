# Main application
# app.py
import os
from flask import Flask, render_template, request, redirect, url_for
import database
import sqlite3

app = Flask(__name__)

# Initialize database on startup
with app.app_context():
    database.init_db()

@app.route('/')
def dashboard():
    conn = database.get_db_connection()
    
    # Get all data
    conversion_kits = conn.execute("SELECT * FROM items WHERE item_type = 'conversion_kit'").fetchall()
    spare_parts = conn.execute("SELECT * FROM items WHERE item_type = 'spare_part'").fetchall()
    
    # Get recent returns (latest 5)
    returns = conn.execute('SELECT * FROM returns ORDER BY date DESC LIMIT 5').fetchall()
    
    # Get recent allocations - separate conversion kits from spare part replacements
    kit_allocations = conn.execute('''
        SELECT a.* FROM allocations a
        INNER JOIN items i ON a.new_item_serial = i.serial
        WHERE i.item_type = 'conversion_kit'
        ORDER BY a.date DESC LIMIT 5
    ''').fetchall()
    
    spare_replacements = conn.execute('''
        SELECT a.* FROM allocations a
        LEFT JOIN items i ON a.new_item_serial = i.serial
        WHERE (i.item_type = 'spare_part' OR i.item_type IS NULL)
        AND a.old_item_serial IS NOT NULL
        ORDER BY a.date DESC LIMIT 5
    ''').fetchall()
    
    # Calculate accurate totals from database
    totals_query = conn.execute('''
        SELECT 
            COALESCE(SUM(CASE WHEN units_imported IS NOT NULL THEN units_imported ELSE 0 END), 0) as total_imported,
            COALESCE(SUM(CASE WHEN units_installed IS NOT NULL THEN units_installed ELSE 0 END), 0) as total_installed,
            COALESCE(SUM(CASE WHEN units_available IS NOT NULL THEN units_available ELSE 0 END), 0) as total_available,
            COUNT(CASE WHEN item_name IS NOT NULL AND item_name != '' THEN 1 END) as total_items
        FROM items 
        WHERE item_type IN ('conversion_kit', 'spare_part')
    ''').fetchone()
    
    # Get additional statistics
    stats_query = conn.execute('''
        SELECT 
            COUNT(CASE WHEN item_type = 'conversion_kit' AND item_name IS NOT NULL AND item_name != '' THEN 1 END) as conversion_kits_count,
            COUNT(CASE WHEN item_type = 'spare_part' AND item_name IS NOT NULL AND item_name != '' THEN 1 END) as spare_parts_count,
            COUNT(CASE WHEN (units_available IS NULL OR units_available = 0) AND item_name IS NOT NULL AND item_name != '' THEN 1 END) as out_of_stock_count,
            COUNT(CASE WHEN units_available > 0 AND units_available <= 5 AND item_name IS NOT NULL AND item_name != '' THEN 1 END) as low_stock_count
        FROM items 
        WHERE item_type IN ('conversion_kit', 'spare_part')
    ''').fetchone()
    
    # Get return and allocation counts
    return_count = conn.execute('SELECT COUNT(*) as count FROM returns').fetchone()['count']
    allocation_count = conn.execute('SELECT COUNT(*) as count FROM allocations').fetchone()['count']
    pending_returns = conn.execute("SELECT COUNT(*) as count FROM returns WHERE status = 'pending' OR status IS NULL").fetchone()['count']
    
    conn.close()
    
    # Calculate stock availability percentage
    stock_availability = 0
    if totals_query['total_imported'] > 0:
        stock_availability = round((totals_query['total_available'] / totals_query['total_imported']) * 100, 1)
    
    return render_template('dashboard.html', 
                           conversion_kits=conversion_kits, 
                           spare_parts=spare_parts, 
                           returns=returns, 
                           kit_allocations=kit_allocations,
                           spare_replacements=spare_replacements,
                           total_imported=totals_query['total_imported'],
                           total_installed=totals_query['total_installed'],
                           total_available=totals_query['total_available'],
                           total_items=totals_query['total_items'],
                           conversion_kits_count=stats_query['conversion_kits_count'],
                           spare_parts_count=stats_query['spare_parts_count'],
                           out_of_stock_count=stats_query['out_of_stock_count'],
                           low_stock_count=stats_query['low_stock_count'],
                           return_count=return_count,
                           allocation_count=allocation_count,
                           pending_returns=pending_returns,
                           stock_availability=stock_availability)

@app.route('/conversion_kits')
def conversion_kits():
    try:
        conn = database.get_db_connection()
        kits = conn.execute("SELECT * FROM items WHERE item_type = 'conversion_kit' ORDER BY serial").fetchall()
        
        # Get allocations for conversion kits only
        allocations = conn.execute('''
            SELECT a.* FROM allocations a
            INNER JOIN items i ON a.new_item_serial = i.serial
            WHERE i.item_type = 'conversion_kit'
            ORDER BY a.date DESC
        ''').fetchall()
        
        conn.close()
        return render_template('conversion_kits.html', kits=kits, allocations=allocations)
    except Exception as e:
        # Initialize database if tables don't exist
        database.init_db()
        return redirect(url_for('conversion_kits'))

@app.route('/spare_parts')
def spare_parts():
    try:
        conn = database.get_db_connection()
        parts = conn.execute("SELECT * FROM items WHERE item_type = 'spare_part'").fetchall()
        replacements = conn.execute('SELECT * FROM allocations WHERE old_item_serial IS NOT NULL').fetchall()
        conn.close()
        return render_template('spare_parts.html', parts=parts, replacements=replacements)
    except Exception as e:
        # Initialize database if tables don't exist
        database.init_db()
        return redirect(url_for('spare_parts'))

@app.route('/returns')
def returns():
    try:
        conn = database.get_db_connection()
        returns_list = conn.execute('SELECT * FROM returns ORDER BY date DESC').fetchall()
        conn.close()
        return render_template('returns.html', returns=returns_list)
    except Exception as e:
        # Initialize database if tables don't exist
        database.init_db()
        return redirect(url_for('returns'))

@app.route('/add_item', methods=['POST'])
def add_item():
    conn = database.get_db_connection()
    try:
        conn.execute('''
            INSERT INTO items (serial, item_name, item_type, admin, created_at, units_imported, units_installed, units_available)
            VALUES (?, ?, ?, ?, date('now'), ?, ?, ?)
        ''', (request.form['serial'], request.form['item_name'], request.form['item_type'], 
              request.form.get('admin', ''), int(request.form.get('units_imported', 0)), 
              int(request.form.get('units_installed', 0)), int(request.form.get('units_available', 0))))
        conn.commit()
    except sqlite3.IntegrityError:
        # Serial number already exists, ignore and continue
        pass
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/add_conversion_kit', methods=['POST'])
def add_conversion_kit():
    conn = database.get_db_connection()
    
    units_imported = int(request.form['units_imported'] or 0)
    units_available = int(request.form['units_available'] or units_imported)
    
    conn.execute('''
        INSERT INTO items (serial, item_name, item_type, admin, created_at, units_imported, units_installed, units_available)
        VALUES (?, ?, ?, ?, date('now'), ?, 0, ?)
    ''', (request.form['serial'], request.form['item_name'], 'conversion_kit', 
          request.form['admin'], units_imported, units_available))
    conn.commit()
    conn.close()
    return redirect(url_for('conversion_kits'))

@app.route('/add_allocation', methods=['POST'])
def add_allocation():
    conn = database.get_db_connection()
    
    # Add allocation record
    conn.execute('''
        INSERT INTO allocations (date, old_item_serial, new_item_serial, rider_number, rider_name, station)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (request.form['date'], request.form['old_item_serial'], request.form['new_item_serial'],
          request.form['rider_number'], request.form['rider_name'], request.form['station']))
    
    # Update units_installed and units_available for the allocated item
    new_serial = request.form['new_item_serial']
    
    # Check if item exists and has available units
    item_check = conn.execute('SELECT units_available FROM items WHERE serial = ?', (new_serial,)).fetchone()
    
    if item_check and item_check['units_available'] > 0:
        conn.execute('''
            UPDATE items 
            SET units_installed = COALESCE(units_installed, 0) + 1,
                units_available = CASE 
                    WHEN COALESCE(units_available, 0) > 0 THEN COALESCE(units_available, 0) - 1 
                    ELSE 0 
                END
            WHERE serial = ?
        ''', (new_serial,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('conversion_kits'))

@app.route('/add_replacement', methods=['POST'])
def add_replacement():
    conn = database.get_db_connection()
    conn.execute('''
        INSERT INTO allocations (date, old_item_serial, new_item_serial, rider_number, rider_name, released_to, link, station)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (request.form['date'], request.form['old_item_serial'], request.form['new_item_serial'],
          request.form['rider_number'], request.form['rider_name'], request.form['released_to'],
          request.form.get('link', ''), request.form.get('station', '')))
    conn.commit()
    conn.close()
    return redirect(url_for('spare_parts'))

@app.route('/add_return', methods=['POST'])
def add_return():
    conn = database.get_db_connection()
    conn.execute('''
        INSERT INTO returns (date, item_serial, personnel, status, notes, condition_rating)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (request.form['date'], request.form['item_serial'], request.form['personnel'], 
          request.form.get('status', 'pending'), request.form.get('notes', ''), 
          request.form.get('condition_rating', 5)))
    conn.commit()
    conn.close()
    return redirect(url_for('returns'))

@app.route('/update_item/<int:item_id>', methods=['POST'])
def update_item(item_id):
    conn = database.get_db_connection()
    
    # Get the item type to determine redirect
    item = conn.execute('SELECT item_type FROM items WHERE id = ?', (item_id,)).fetchone()
    item_type = item['item_type'] if item else 'conversion_kit'
    
    # Validate and calculate proper values
    units_imported = int(request.form['units_imported'] or 0)
    units_installed = int(request.form['units_installed'] or 0)
    units_available = int(request.form['units_available'] or 0)
    
    # Ensure data integrity: available + installed should not exceed imported
    if units_installed + units_available > units_imported:
        units_available = max(0, units_imported - units_installed)
    
    conn.execute('''
        UPDATE items SET serial=?, item_name=?, item_type=?, admin=?, created_at=?, 
        units_imported=?, units_installed=?, units_available=? WHERE id=?
    ''', (request.form['serial'], request.form['item_name'], request.form['item_type'],
          request.form['admin'], request.form.get('created_at', ''), units_imported,
          units_installed, units_available, item_id))
    conn.commit()
    conn.close()
    
    # Redirect based on item type
    if item_type == 'conversion_kit':
        return redirect(url_for('conversion_kits'))
    elif item_type == 'spare_part':
        return redirect(url_for('spare_parts'))
    else:
        return redirect(url_for('dashboard'))

@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    conn = database.get_db_connection()
    
    # Get the item type to determine redirect
    item = conn.execute('SELECT item_type FROM items WHERE id = ?', (item_id,)).fetchone()
    item_type = item['item_type'] if item else 'conversion_kit'
    
    conn.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    
    # Redirect based on item type
    if item_type == 'conversion_kit':
        return redirect(url_for('conversion_kits'))
    elif item_type == 'spare_part':
        return redirect(url_for('spare_parts'))
    else:
        return redirect(url_for('dashboard'))

@app.route('/delete_allocation/<int:alloc_id>')
def delete_allocation(alloc_id):
    conn = database.get_db_connection()
    conn.execute('DELETE FROM allocations WHERE id = ?', (alloc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('conversion_kits'))

@app.route('/delete_return/<int:return_id>')
def delete_return(return_id):
    conn = database.get_db_connection()
    conn.execute('DELETE FROM returns WHERE id = ?', (return_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('returns'))

@app.route('/delete_replacement/<int:replacement_id>')
def delete_replacement(replacement_id):
    conn = database.get_db_connection()
    conn.execute('DELETE FROM allocations WHERE id = ?', (replacement_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('spare_parts'))

@app.route('/update_replacement/<int:replacement_id>', methods=['POST'])
def update_replacement(replacement_id):
    conn = database.get_db_connection()
    conn.execute('''
        UPDATE allocations SET date = ?, old_item_serial = ?, new_item_serial = ?, 
        rider_name = ?, rider_number = ?, station = ? WHERE id = ?
    ''', (request.form['date'], request.form['old_item_serial'], request.form['new_item_serial'],
          request.form['rider_name'], request.form['rider_number'], request.form['station'], replacement_id))
    conn.commit()
    conn.close()
    return redirect(url_for('spare_parts'))

@app.route('/update_return_status/<int:return_id>', methods=['POST'])
def update_return_status(return_id):
    conn = database.get_db_connection()
    conn.execute('''
        UPDATE returns SET status = ?, notes = ? WHERE id = ?
    ''', (request.form['status'], request.form['notes'], return_id))
    conn.commit()
    conn.close()
    return redirect(url_for('returns'))

@app.route('/update_return/<int:return_id>', methods=['POST'])
def update_return(return_id):
    conn = database.get_db_connection()
    conn.execute('''
        UPDATE returns SET date = ?, item_serial = ?, personnel = ?, status = ?, notes = ? WHERE id = ?
    ''', (request.form['date'], request.form['item_serial'], request.form['personnel'], 
          request.form['status'], request.form['notes'], return_id))
    conn.commit()
    conn.close()
    return redirect(url_for('returns'))

@app.route('/process_return/<int:return_id>')
def process_return(return_id):
    conn = database.get_db_connection()
    
    # Get return details
    return_item = conn.execute('SELECT * FROM returns WHERE id = ?', (return_id,)).fetchone()
    
    if return_item:
        # Update return status
        conn.execute('''
            UPDATE returns SET status = 'processed', processed_date = date('now') WHERE id = ?
        ''', (return_id,))
        
        # Update inventory - add returned item back to available stock
        item_exists = conn.execute('SELECT id FROM items WHERE serial = ?', (return_item['item_serial'],)).fetchone()
        
        if item_exists:
            conn.execute('''
                UPDATE items 
                SET units_available = COALESCE(units_available, 0) + 1,
                    units_installed = CASE 
                        WHEN COALESCE(units_installed, 0) > 0 THEN COALESCE(units_installed, 0) - 1 
                        ELSE 0 
                    END
                WHERE serial = ?
            ''', (return_item['item_serial'],))
        else:
            # If item doesn't exist in inventory, just mark return as processed
            pass
    
    conn.commit()
    conn.close()
    return redirect(url_for('returns'))

# Initialize database on startup
database.init_db()

# ⚠️ CRITICAL: Railway-specific changes below
if __name__ == '__main__':
    # Get port from Railway environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app - debug=False for production
    app.run(host='0.0.0.0', port=port, debug=False)