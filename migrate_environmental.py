#!/usr/bin/env python3
"""
Manual migration script for Environmental Module
Run this to add Environmental tables to database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from datetime import datetime

# Define the models locally to ensure they're available
class EnvironmentalRecord(db.Model):
    """Stores environmental activity data (NOT emissions)"""
    __tablename__ = 'environmental_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    module_type = db.Column(db.String(50), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    normalized_quantity = db.Column(db.Float)
    normalized_unit = db.Column(db.String(50))
    reporting_year = db.Column(db.Integer, nullable=False)
    reporting_period = db.Column(db.String(20))
    period_month = db.Column(db.Integer)
    period_quarter = db.Column(db.Integer)
    is_estimated = db.Column(db.Boolean, default=False)
    reporting_scope = db.Column(db.String(100))
    status = db.Column(db.String(20), default='draft')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<EnvironmentalRecord {self.id}: {self.activity_type} {self.quantity}{self.unit}>'


class EnvironmentalEvidence(db.Model):
    """Evidence files linked to environmental records"""
    __tablename__ = 'environmental_evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    environmental_record_id = db.Column(db.Integer, db.ForeignKey('environmental_records.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    uploaded_by = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.String(100))
    verified_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<EnvironmentalEvidence {self.id}: {self.filename}>'


def migrate_database():
    """Create environmental tables in database"""
    print("Starting database migration for Environmental Module...")
    
    with app.app_context():
        try:
            # Create all tables that don't exist
            db.create_all()
            print("✓ Database tables created/updated")
            
            # Check if tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'environmental_records' in tables:
                print("✓ Environmental records table created")
            else:
                print("✗ Environmental records table NOT created")
                
            if 'environmental_evidence' in tables:
                print("✓ Environmental evidence table created")
            else:
                print("✗ Environmental evidence table NOT created")
                
            print("\nMigration completed successfully!")
            
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            return False
    
    return True


if __name__ == '__main__':
    migrate_database()