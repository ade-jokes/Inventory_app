# Database operations
# database.py
import sqlite3
import os
from datetime import datetime

def get_db_connection():
    # Use Railway's persistent volume or fallback to local file
    db_path = os.environ.get('DATABASE_PATH', 'inventory.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Items table (central table for all item types)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial TEXT UNIQUE,
            item_name TEXT NOT NULL,
            item_type TEXT NOT NULL,  -- e.g., 'conversion_kit', 'spare_part', 'return'
            admin TEXT,
            created_at TEXT,
            units_imported INTEGER DEFAULT 0,
            units_installed INTEGER DEFAULT 0,
            units_available INTEGER DEFAULT 0
        )
    ''')
    
    # Create Allocations table (for conversion kit details and spare parts replacements)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            item_id INTEGER,
            old_item_serial TEXT,
            new_item_serial TEXT,
            rider_number TEXT,
            rider_name TEXT,
            released_to TEXT,
            link TEXT,
            station TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    ''')
    
    # Create Returns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            item_serial TEXT,
            personnel TEXT,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            processed_date TEXT,
            condition_rating INTEGER DEFAULT 5,
            FOREIGN KEY (item_serial) REFERENCES items(serial)
        )
    ''')
    
    # Insert initial data from Excel
    # Conversion Kit overview (Sheet 0)
    conversion_kits = [
        ('15092501', 'Electrical component box', 'conversion_kit', 'Inventory', '45915', 125, 6, 119),
        ('15092502', 'Shaft cups', 'conversion_kit', 'Inventory', '45915', 130, 6, 124),
        ('15092503', 'Motor', 'conversion_kit', 'Inventory', '45915', 125, 6, 119),
        ('15092504', 'Controller', 'conversion_kit', 'Inventory', '45915', 120, 6, 114),
        ('15092505', 'Gear', 'conversion_kit', 'Inventory', '45915', 125, 6, 119),
        ('15092506', 'Engine mount (front)', 'conversion_kit', 'Inventory', '45915', 0, 0, 0),
        ('15092507', 'Engine mount fittings (back)', 'conversion_kit', 'Inventory', '45915', 0, 0, 0),
        ('15092508', 'Engine mount fitting (sides)', 'conversion_kit', 'Inventory', '45915', 0, 0, 0)
    ]
    for serial, name, item_type, admin, created_at, imported, installed, available in conversion_kits:
        cursor.execute('''
            INSERT OR IGNORE INTO items (serial, item_name, item_type, admin, created_at, units_imported, units_installed, units_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (serial, name, item_type, admin, created_at, imported, installed, available))
    
    # Conversion Kit allocations - using actual kit serials
    kit_allocations = [
        ('2024-01-15', '15092501', 'APP 181 QY', 'Adeleke Sikiru', '08012345678', 'Lagos Island'),
        ('2024-01-16', '15092502', 'AGL 874 QD', 'Ayomide Olorunlana', '08023456789', 'Victoria Island'),
        ('2024-01-17', '15092503', 'KSF 199 QM', 'Adekoya Ebenezer', '08034567890', 'Ikeja'),
        ('2024-01-18', '15092504', 'SMK 743 QL', 'Hilary Maanpar', '08045678901', 'Surulere'),
        ('2024-01-19', '15092505', 'XYZ 456 AB', 'Ibrahim Musa', '08056789012', 'Yaba'),
        ('2024-01-20', '15092501', 'DEF 789 CD', 'Chidi Okwu', '08067890123', 'Apapa')
    ]
    
    for date, kit_serial, plate_number, rider_name, rider_phone, station in kit_allocations:
        cursor.execute('''
            INSERT OR IGNORE INTO allocations (date, new_item_serial, old_item_serial, rider_name, rider_number, station)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, kit_serial, plate_number, rider_name, rider_phone, station))
    
    # Sample spare parts with proper inventory data
    spare_parts_inventory = [
        ('SP001', 'Motor', 'spare_part', 'Inventory', '2024-01-01', 50, 12, 38),
        ('SP002', 'Battery', 'spare_part', 'Inventory', '2024-01-01', 75, 20, 55),
        ('SP003', 'Controller', 'spare_part', 'Inventory', '2024-01-01', 40, 8, 32),
        ('SP004', 'Throttle', 'spare_part', 'Inventory', '2024-01-01', 60, 15, 45)
    ]
    
    for serial, name, item_type, admin, created_at, imported, installed, available in spare_parts_inventory:
        cursor.execute('''
            INSERT OR IGNORE INTO items (serial, item_name, item_type, admin, created_at, units_imported, units_installed, units_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (serial, name, item_type, admin, created_at, imported, installed, available))
    
    # Ensure all required columns exist
    try:
        cursor.execute('ALTER TABLE returns ADD COLUMN status TEXT DEFAULT "pending"')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE returns ADD COLUMN notes TEXT')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE returns ADD COLUMN processed_date TEXT')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE returns ADD COLUMN condition_rating INTEGER DEFAULT 5')
    except:
        pass
    
    # Update conversion kit inventory based on allocations
    cursor.execute('''
        UPDATE items SET 
            units_installed = (SELECT COUNT(*) FROM allocations WHERE new_item_serial = items.serial),
            units_available = units_imported - (SELECT COUNT(*) FROM allocations WHERE new_item_serial = items.serial)
        WHERE item_type = 'conversion_kit' AND serial IN (SELECT DISTINCT new_item_serial FROM allocations)
    ''')
    
    # Additional spare parts without inventory data (for options)
    spare_parts_options = [
        ('SP005', 'Charger', 'spare_part'),
        ('SP006', 'Screen', 'spare_part'),
        ('SP007', 'Gear', 'spare_part'),
        ('SP008', 'PSU', 'spare_part'),
        ('SP009', 'Relays', 'spare_part'),
        ('SP010', 'Breakers', 'spare_part'),
        ('SP011', 'Wiper switch', 'spare_part'),
        ('SP012', 'Battery switch', 'spare_part'),
        ('SP013', 'Ignition and key', 'spare_part'),
        ('SP014', 'Connecting wires', 'spare_part'),
        ('SP015', 'Wire holder', 'spare_part')
    ]
    for serial, name, item_type in spare_parts_options:
        cursor.execute('''
            INSERT OR IGNORE INTO items (serial, item_name, item_type, units_imported, units_installed, units_available)
            VALUES (?, ?, ?, 0, 0, 0)
        ''', (serial, name, item_type))
    
    # Sample replacement records for spare parts
    spare_part_replacements = [
        ('2024-01-22', 'SP001-OLD', 'SP001', 'Ahmed Bello', '08011111111', 'Ikeja'),
        ('2024-01-23', 'SP002-OLD', 'SP002', 'Fatima Yusuf', '08022222222', 'Victoria Island'),
        ('2024-01-24', 'SP003-OLD', 'SP003', 'Emeka Okafor', '08033333333', 'Surulere')
    ]
    
    for date, old_serial, new_serial, rider_name, rider_phone, station in spare_part_replacements:
        cursor.execute('''
            INSERT OR IGNORE INTO allocations (date, old_item_serial, new_item_serial, rider_name, rider_number, station)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, old_serial, new_serial, rider_name, rider_phone, station))
    
    # Sample return records
    sample_returns = [
        ('2024-01-25', '15092501', 'John Doe', 'pending', 'Kit returned for maintenance'),
        ('2024-01-26', 'SP001', 'Jane Smith', 'processed', 'Motor replacement completed')
    ]
    
    for date, item_serial, personnel, status, notes in sample_returns:
        cursor.execute('''
            INSERT OR IGNORE INTO returns (date, item_serial, personnel, status, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, item_serial, personnel, status, notes))
    
    conn.commit()
    conn.close()