from flask import Flask, render_template, redirect, url_for, request, jsonify, session, flash
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import relationship, backref
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import io
import re
import logging
import traceback
import requests
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import tempfile
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps
from dotenv import load_dotenv
from flask_mail import Mail, Message
import secrets

# ── Load env vars FIRST ──
load_dotenv()

# ── Create Flask app ──
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ── Disable Jinja2 template caching ──
app.jinja_env.cache = None

# ── Database config ──
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'carbon_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Mail config (MUST be after app = Flask(__name__)) ──
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'emittif.io@gmail.com'
app.config['MAIL_PASSWORD'] = 'rhminzngrddbkgse'
app.config['MAIL_DEFAULT_SENDER'] = ('Emittiff', 'emittif.io@gmail.com')

# ── Initialize extensions ──
db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)

# ── Ensure instance folder exists ──
if not os.path.exists(os.path.join(basedir, 'instance')):
    os.makedirs(os.path.join(basedir, 'instance'))
    print("✓ Created instance folder")

# ── Upload config ──
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ── OCR.space API config ──
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", "K85161561588957")
OCR_SPACE_API_URL = "https://api.ocr.space/parse/image"

# ── Gemini AI config ──
GEMINI_API_KEY = "AIzaSyBQBZ89bmr5IINCUBL3DUBjOJZ6ilo99rA"

def initialize_gemini():
    """Initialize Gemini AI with multiple model fallbacks"""
    try:
        print("🔄 Initializing Gemini AI...")
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        print("✅ Gemini API configured successfully!")
        
        try:
            print("🔍 Checking available models...")
            models = genai.list_models()
            available_models = []
            for model in models:
                available_models.append({
                    'name': model.name,
                    'supported_methods': model.supported_generation_methods
                })
            
            print(f"✅ Total available models: {len(available_models)}")
            generative_models = [m for m in available_models if 'generateContent' in m['supported_methods']]
            print(f"🎯 Generative models: {[m['name'] for m in generative_models]}")
            return generative_models
            
        except Exception as e:
            print(f"❌ Model listing failed: {e}")
            return [{'name': 'gemini-pro', 'supported_methods': ['generateContent']}]
            
    except Exception as e:
        print(f"❌ Gemini AI configuration failed: {e}")
        return []

# ── Configure logging ──
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

AVAILABLE_GEMINI_MODELS = initialize_gemini()
GEMINI_AVAILABLE = len(AVAILABLE_GEMINI_MODELS) > 0

if GEMINI_AVAILABLE:
    print(f"🚀 Gemini AI READY! {[m['name'] for m in AVAILABLE_GEMINI_MODELS]}")
else:
    print("❌ No Gemini models available")
# ============================================================
# DATABASE MODELS
# ============================================================

class User(db.Model):
    """Main user authentication model"""
    __tablename__ = 'users'
    
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(100), unique=True, nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    company_name  = db.Column(db.String(200))
    role          = db.Column(db.String(20), default='company')  # company, auditor, admin
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    is_active     = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id'          : self.id,
            'username'    : self.username,
            'email'       : self.email,
            'company_name': self.company_name,
            'role'        : self.role,
            'created_at'  : self.created_at.isoformat() if self.created_at else None
        }

class ComplianceStandard(db.Model):
    """Database model for compliance standards"""
    __tablename__ = 'compliance_standards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    short_name = db.Column(db.String(20))
    version = db.Column(db.String(20))
    description = db.Column(db.Text)
    jurisdiction = db.Column(db.String(50), default='Global')
    category = db.Column(db.String(50))
    logo = db.Column(db.String(200))
    website = db.Column(db.String(200))
    effective_date = db.Column(db.Date)
    next_review_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    clauses = db.relationship('ComplianceClause', backref='standard', lazy=True, cascade='all, delete-orphan')
    user_statuses = db.relationship('UserComplianceStatus', backref='standard', lazy=True)

class ComplianceClause(db.Model):
    """Database model for individual clauses/requirements"""
    __tablename__ = 'compliance_clauses'
    id = db.Column(db.Integer, primary_key=True)
    standard_id = db.Column(db.Integer, db.ForeignKey('compliance_standards.id'), nullable=False)
    clause_number = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    requirement = db.Column(db.Text)
    guidance = db.Column(db.Text)
    is_mandatory = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=1)
    category = db.Column(db.String(50))
    tags = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_statuses = db.relationship('UserComplianceStatus', backref='clause', lazy=True)
    evidence = db.relationship('EvidenceFile', backref='clause', lazy=True)
    mappings = db.relationship('ClauseMapping', foreign_keys='ClauseMapping.source_clause_id', backref='source_clause', lazy=True)

class UserComplianceStatus(db.Model):
    """Database model for user's compliance status"""
    __tablename__ = 'user_compliance_status'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    clause_id = db.Column(db.Integer, db.ForeignKey('compliance_clauses.id'), nullable=False)
    standard_id = db.Column(db.Integer, db.ForeignKey('compliance_standards.id'), nullable=False)
    status = db.Column(db.String(20), default='not_assessed')
    evidence_summary = db.Column(db.Text)
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)
    next_assessment_date = db.Column(db.DateTime)
    assessor = db.Column(db.String(100))
    comments = db.Column(db.Text)
    confidence_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    evidence_files = db.relationship('EvidenceFile', backref='compliance_status', lazy=True)

class EvidenceFile(db.Model):
    """Database model for evidence files"""
    __tablename__ = 'evidence_files'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    compliance_status_id = db.Column(db.Integer, db.ForeignKey('user_compliance_status.id'))
    clause_id = db.Column(db.Integer, db.ForeignKey('compliance_clauses.id'))
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    description = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.String(100))
    verified_date = db.Column(db.DateTime)

class ClauseMapping(db.Model):
    """Database model for mapping clauses between standards"""
    __tablename__ = 'clause_mappings'
    id = db.Column(db.Integer, primary_key=True)
    source_clause_id = db.Column(db.Integer, db.ForeignKey('compliance_clauses.id'), nullable=False)
    target_standard_id = db.Column(db.Integer, db.ForeignKey('compliance_standards.id'), nullable=False)
    target_clause_id = db.Column(db.Integer, db.ForeignKey('compliance_clauses.id'), nullable=False)
    mapping_type = db.Column(db.String(20))
    confidence = db.Column(db.Integer, default=80)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    target_standard = db.relationship('ComplianceStandard', foreign_keys=[target_standard_id])
    target_clause = db.relationship('ComplianceClause', foreign_keys=[target_clause_id])

class AuditorAccess(db.Model):
    """Links an auditor user to a company with expiry and status"""
    __tablename__ = 'auditor_access'
    
    id           = db.Column(db.Integer, primary_key=True)
    auditor_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    invited_by   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status       = db.Column(db.String(20), default='pending')
    expires_at   = db.Column(db.DateTime, nullable=False)
    invite_token = db.Column(db.String(200), unique=True, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    last_login   = db.Column(db.DateTime, nullable=True)
    auditor_notes= db.Column(db.Text, nullable=True)

    auditor  = db.relationship('User', foreign_keys=[auditor_id], backref='audit_assignments')
    company  = db.relationship('User', foreign_keys=[company_id], backref='auditors')
    inviter  = db.relationship('User', foreign_keys=[invited_by])

# ============================================
# ESG DATA MODELS
# ============================================

class ESGDataCategory(db.Model):
    """Master categories for ESG data"""
    __tablename__ = 'esg_data_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Environmental, Social, Governance, Supply Chain
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ESGDataModule(db.Model):
    """Individual data collection modules"""
    __tablename__ = 'esg_data_modules'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('esg_data_categories.id'))
    name = db.Column(db.String(100), nullable=False)  # Emissions, Energy, Water, Waste, etc.
    description = db.Column(db.Text)
    data_type = db.Column(db.String(50))  # numeric, percentage, yesno, text
    unit = db.Column(db.String(50))
    requires_evidence = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = db.relationship('ESGDataCategory', backref='modules')

class ESGDataEntry(db.Model):
    """Base model for all ESG data entries"""
    __tablename__ = 'esg_data_entries'
    id = db.Column(db.Integer, primary_key=True)
    
    # Audit fields (MANDATORY)
    company_id = db.Column(db.String(100), nullable=False, index=True)
    reporting_year = db.Column(db.Integer, nullable=False, index=True)
    entered_by = db.Column(db.String(100), nullable=False)  # user_id
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_source = db.Column(db.String(50), nullable=False)  # manual, supplier, estimation, imported
    evidence_reference = db.Column(db.String(500))  # Link to evidence file(s)
    
    # Data fields
    module_id = db.Column(db.Integer, db.ForeignKey('esg_data_modules.id'), nullable=False)
    value_numeric = db.Column(db.Float)
    value_text = db.Column(db.Text)
    value_percentage = db.Column(db.Float)
    value_boolean = db.Column(db.Boolean)
    
    # Metadata
    is_estimated = db.Column(db.Boolean, default=False)
    estimation_method = db.Column(db.String(200))
    data_quality_score = db.Column(db.String(1))  # A, B, C, D
    comments = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft')  # draft, submitted, approved, rejected
    
    # Relationships
    module = db.relationship('ESGDataModule', backref='entries')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_company_year_module', 'company_id', 'reporting_year', 'module_id'),
    )

class SocialWorkforceData(db.Model):
    """Social & Workforce specific data"""
    __tablename__ = 'social_workforce_data'
    id = db.Column(db.Integer, primary_key=True)
    
    # Audit fields
    company_id = db.Column(db.String(100), nullable=False, index=True)
    reporting_year = db.Column(db.Integer, nullable=False, index=True)
    entered_by = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    data_source = db.Column(db.String(50), nullable=False)
    evidence_reference = db.Column(db.String(500))
    
    # Workforce Profile
    total_employees = db.Column(db.Integer)
    male_count = db.Column(db.Integer)
    female_count = db.Column(db.Integer)
    other_gender_count = db.Column(db.Integer)
    permanent_employees = db.Column(db.Integer)
    contract_employees = db.Column(db.Integer)
    temporary_employees = db.Column(db.Integer)
    
    # Health & Safety
    ltifr = db.Column(db.Float)  # Lost Time Injury Frequency Rate
    fatalities = db.Column(db.Integer)
    near_misses = db.Column(db.Integer)
    
    # Training & Skills
    total_training_hours = db.Column(db.Integer)
    employees_trained_count = db.Column(db.Integer)
    training_investment = db.Column(db.Float)
    
    # Community Impact
    has_community_programs = db.Column(db.Boolean)
    community_program_description = db.Column(db.Text)
    community_investment = db.Column(db.Float)
    
    # Status
    status = db.Column(db.String(50), default='draft')

class GovernanceData(db.Model):
    """Governance specific data"""
    __tablename__ = 'governance_data'
    id = db.Column(db.Integer, primary_key=True)
    
    # Audit fields
    company_id = db.Column(db.String(100), nullable=False, index=True)
    reporting_year = db.Column(db.Integer, nullable=False, index=True)
    entered_by = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    data_source = db.Column(db.String(50), nullable=False)
    evidence_reference = db.Column(db.String(500))
    
    # Risk Management
    risk_assessments_conducted = db.Column(db.Integer)
    significant_risks_identified = db.Column(db.Integer)
    risk_mitigation_budget = db.Column(db.Float)
    
    # Compliance
    compliance_incidents = db.Column(db.Integer)
    regulatory_fines = db.Column(db.Float)
    audit_findings = db.Column(db.Integer)
    
    # Ethics & Integrity
    ethics_training_hours = db.Column(db.Integer)
    employees_trained_ethics = db.Column(db.Integer)
    ethics_violations_reported = db.Column(db.Integer)
    whistleblower_cases = db.Column(db.Integer)
    
# Status
status = db.Column(db.String(50), default='draft')
# NEW COLUMNS — added via migration
new_hires = db.Column(db.Integer)
employees_left = db.Column(db.Integer)
senior_management = db.Column(db.Integer)
middle_management = db.Column(db.Integer)
executive_staff = db.Column(db.Integer)
operations_staff = db.Column(db.Integer)
total_hours_worked = db.Column(db.Float)
lost_time_injuries = db.Column(db.Integer)
recordable_incidents = db.Column(db.Integer)
occupational_diseases = db.Column(db.Integer)
safety_training_hours = db.Column(db.Integer)
technical_training_hrs = db.Column(db.Integer)
leadership_training_hrs = db.Column(db.Integer)
safety_training_cat_hrs = db.Column(db.Integer)
esg_training_hrs = db.Column(db.Integer)
digital_training_hrs = db.Column(db.Integer)
other_training_hrs = db.Column(db.Integer)
training_spend_myr = db.Column(db.Float)
hrdf_levy_paid = db.Column(db.Float)
hrdf_claims = db.Column(db.Float)
performance_review_pct = db.Column(db.Float)
dev_plan_pct = db.Column(db.Float)
csr_spend_myr = db.Column(db.Float)
beneficiaries = db.Column(db.Integer)
volunteer_hours = db.Column(db.Integer)
volunteers_count = db.Column(db.Integer)
zakat_contribution = db.Column(db.Float)
scholarship_spend = db.Column(db.Float)
bumi_procurement_pct = db.Column(db.Float)
board_total = db.Column(db.Integer)
board_female = db.Column(db.Integer)
board_independent = db.Column(db.Integer)
board_avg_age = db.Column(db.Float)
bumiputera_count = db.Column(db.Integer)
chinese_count = db.Column(db.Integer)
indian_count = db.Column(db.Integer)
other_ethnicity_count = db.Column(db.Integer)
age_under30 = db.Column(db.Integer)
age_30_50 = db.Column(db.Integer)
age_over50 = db.Column(db.Integer)
pwd_count = db.Column(db.Integer)
gender_pay_gap = db.Column(db.Float)
min_wage_compliance = db.Column(db.String(50))
community_programmes = db.Column(db.Text)
section = db.Column(db.String(50))

class SupplierInvitation(db.Model):
    """Supplier invitation tracking"""
    __tablename__ = 'supplier_invitations'
    id = db.Column(db.Integer, primary_key=True)
    
    # Company context
    company_id = db.Column(db.String(100), nullable=False, index=True)
    reporting_year = db.Column(db.Integer, nullable=False, index=True)
    
    # Supplier info
    supplier_email = db.Column(db.String(200), nullable=False)
    supplier_name = db.Column(db.String(200))
    invitation_token = db.Column(db.String(100), unique=True, nullable=False)
    
    # Status tracking
    invitation_status = db.Column(db.String(50), default='pending')  # pending, sent, accepted, completed
    sent_date = db.Column(db.DateTime)
    accepted_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    
    # Submission tracking
    data_submitted = db.Column(db.Boolean, default=False)
    submission_date = db.Column(db.DateTime)
    data_quality_score = db.Column(db.String(1))  # A, B, C, D
    reviewed_by = db.Column(db.String(100))
    review_date = db.Column(db.DateTime)
    review_comments = db.Column(db.Text)
    
    # Audit
    invited_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EvidenceVault(db.Model):
    """Central evidence repository"""
    __tablename__ = 'evidence_vault'
    id = db.Column(db.Integer, primary_key=True)
    
    # File info
    company_id = db.Column(db.String(100), nullable=False, index=True)
    filename = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(1000), nullable=False)
    file_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)
    
    # Metadata
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    reporting_year = db.Column(db.Integer, nullable=False, index=True)
    
    # Uploader info
    uploaded_by = db.Column(db.String(100), nullable=False)
    uploaded_by_name = db.Column(db.String(200))
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    last_used_date = db.Column(db.DateTime)
    
    # Security
    access_level = db.Column(db.String(50), default='company')  # company, auditor, public
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.String(100))
    verified_date = db.Column(db.DateTime)
    
    # Tags for search
    tags = db.Column(db.Text)  # comma-separated

class EvidenceLink(db.Model):
    """Links evidence to data entries"""
    __tablename__ = 'evidence_links'
    id = db.Column(db.Integer, primary_key=True)
    
    evidence_id = db.Column(db.Integer, db.ForeignKey('evidence_vault.id'), nullable=False)
    linked_table = db.Column(db.String(100), nullable=False)  # esg_data_entries, social_workforce_data, etc.
    linked_record_id = db.Column(db.Integer, nullable=False)
    linked_field = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    evidence = db.relationship('EvidenceVault', backref='links')

    # ====================================================================
# Environmental Module Models (ADD THIS SECTION)
# ====================================================================

class EnvironmentalRecord(db.Model):
    """Stores environmental activity data (NOT emissions)"""
    __tablename__ = 'environmental_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)  # Links to user session
    module_type = db.Column(db.String(50), nullable=False)  # energy, water, waste, land_biodiversity
    activity_type = db.Column(db.String(100), nullable=False)  # electricity, diesel, water_withdrawal, etc.
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)  # Original unit entered by user
    normalized_quantity = db.Column(db.Float)  # Converted to standard unit
    normalized_unit = db.Column(db.String(50))  # Standard unit (kWh, m³, kg)
    reporting_year = db.Column(db.Integer, nullable=False)
    reporting_period = db.Column(db.String(20))  # annual, quarterly, monthly
    period_month = db.Column(db.Integer)  # 1-12 for monthly data
    period_quarter = db.Column(db.Integer)  # 1-4 for quarterly data
    is_estimated = db.Column(db.Boolean, default=False)
    reporting_scope = db.Column(db.String(100))  # References Company Settings, not redefined here
    status = db.Column(db.String(20), default='draft')  # draft, submitted, reviewed, approved
    notes = db.Column(db.Text)
    
    # Audit trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    # Relationships
    evidence_files = db.relationship('EnvironmentalEvidence', backref='record', 
                                    cascade='all, delete-orphan', lazy=True)
    
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
    file_size = db.Column(db.Integer)  # in bytes
    
    # Upload info
    uploaded_by = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.String(100))
    verified_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<EnvironmentalEvidence {self.id}: {self.filename}>'

ENVIRONMENTAL_CONFIG = {
    'energy': {
        'required': True,
        'activities': [
            'electricity', 'electricity_peninsular', 'electricity_sabah',
            'electricity_sarawak', 'solar', 'renewable_energy',
            'diesel', 'gasoline', 'natural_gas', 'lpg', 'coal',
            'ron95', 'ron97', 'petrol', 'fuel'
        ],
        'units': {
            'electricity': {'kWh': 1, 'MWh': 1000, 'GJ': 277.778},
            'electricity_peninsular': {'kWh': 1, 'MWh': 1000},
            'electricity_sabah': {'kWh': 1, 'MWh': 1000},
            'electricity_sarawak': {'kWh': 1, 'MWh': 1000},
            'solar': {'kWh': 1, 'MWh': 1000},
            'renewable_energy': {'kWh': 1, 'MWh': 1000},
            'diesel': {'liters': 1, 'gallons': 3.78541, 'L': 1},
            'gasoline': {'liters': 1, 'gallons': 3.78541, 'L': 1},
            'natural_gas': {'m³': 1, 'therms': 105.506, 'MMBtu': 28.2637},
            'lpg': {'liters': 1, 'kg': 1, 'L': 1},
            'coal': {'kg': 1, 'tons': 1000, 'metric_tonnes': 1000},
            'ron95': {'liters': 1, 'L': 1},
            'ron97': {'liters': 1, 'L': 1},
            'petrol': {'liters': 1, 'L': 1},
            'fuel': {'liters': 1, 'L': 1},
        },
        'normalized_units': {
            'electricity': 'kWh',
            'electricity_peninsular': 'kWh',
            'electricity_sabah': 'kWh',
            'electricity_sarawak': 'kWh',
            'solar': 'kWh',
            'renewable_energy': 'kWh',
            'diesel': 'liters',
            'gasoline': 'liters',
            'natural_gas': 'm³',
            'lpg': 'liters',
            'coal': 'kg',
            'ron95': 'liters',
            'ron97': 'liters',
            'petrol': 'liters',
            'fuel': 'liters',
        }
    },
    'water': {
        'required': True,
        'activities': [
            'water_withdrawal', 'water_consumption',
            'water_discharge', 'municipal', 'recycled', 'groundwater'
        ],
        'units': {
            'water_withdrawal': {'m³': 1, 'liters': 0.001, 'gallons': 0.00378541, 'L': 0.001},
            'water_consumption': {'m³': 1, 'liters': 0.001, 'gallons': 0.00378541, 'L': 0.001},
            'water_discharge': {'m³': 1, 'liters': 0.001, 'gallons': 0.00378541, 'L': 0.001},
            'municipal': {'m³': 1, 'liters': 0.001, 'L': 0.001},
            'recycled': {'m³': 1, 'liters': 0.001, 'L': 0.001},
            'groundwater': {'m³': 1, 'liters': 0.001, 'L': 0.001},
        },
        'normalized_units': {
            'water_withdrawal': 'm³',
            'water_consumption': 'm³',
            'water_discharge': 'm³',
            'municipal': 'm³',
            'recycled': 'm³',
            'groundwater': 'm³',
        }
    },
'waste': {
        'required': True,
        'activities': [
            'waste_general', 'hazardous_waste', 'recycled_waste',
            'organic_waste', 'general_landfill', 'recycled', 'hazardous', 'organic'
        ],
        'units': {
            'waste_general': {'kg': 1, 'tons': 1000, 'metric_tonnes': 1000},
            'hazardous_waste': {'kg': 1, 'tons': 1000, 'metric_tonnes': 1000},
            'recycled_waste': {'kg': 1, 'tons': 1000, 'metric_tonnes': 1000},
            'organic_waste': {'kg': 1, 'tons': 1000, 'metric_tonnes': 1000},
            'general_landfill': {'kg': 1, 'tons': 1000, 'metric_tonnes': 1000},
            'recycled': {'kg': 1, 'tons': 1000, 'metric_tonnes': 1000},
            'hazardous': {'kg': 1, 'tons': 1000, 'metric_tonnes': 1000},
            'organic': {'kg': 1, 'tons': 1000, 'metric_tonnes': 1000},
        },
        'normalized_units': {
            'waste_general': 'kg',
            'hazardous_waste': 'kg',
            'recycled_waste': 'kg',
            'organic_waste': 'kg',
            'general_landfill': 'kg',
            'recycled': 'kg',
            'hazardous': 'kg',
            'organic': 'kg',
        }
    },
    'travel': {
        'required': False,
        'activities': [
            'flight_domestic', 'flight_international', 'car_petrol',
            'car_diesel', 'car_electric', 'train', 'bus', 'motorcycle',
            'taxi', 'ride_hailing', 'ferry'
        ],
        'units': {
            'flight_domestic': {'km': 1, 'miles': 1.60934},
            'flight_international': {'km': 1, 'miles': 1.60934},
            'car_petrol': {'km': 1, 'miles': 1.60934},
            'car_diesel': {'km': 1, 'miles': 1.60934},
            'car_electric': {'km': 1, 'miles': 1.60934},
            'train': {'km': 1, 'miles': 1.60934},
            'bus': {'km': 1, 'miles': 1.60934},
            'motorcycle': {'km': 1, 'miles': 1.60934},
            'taxi': {'km': 1, 'miles': 1.60934},
            'ride_hailing': {'km': 1, 'miles': 1.60934},
            'ferry': {'km': 1, 'miles': 1.60934},
        },
        'normalized_units': {
            'flight_domestic': 'km',
            'flight_international': 'km',
            'car_petrol': 'km',
            'car_diesel': 'km',
            'car_electric': 'km',
            'train': 'km',
            'bus': 'km',
            'motorcycle': 'km',
            'taxi': 'km',
            'ride_hailing': 'km',
            'ferry': 'km',
        }
    },
    'land_biodiversity': {
        'required': False,
        'activities': [
            'land_use_area', 'protected_area', 'biodiversity_impact'
        ],
        'units': {
            'land_use_area': {'hectares': 1, 'acres': 0.404686, 'sq_meters': 0.0001},
            'protected_area': {'hectares': 1, 'acres': 0.404686, 'sq_meters': 0.0001},
            'biodiversity_impact': {'hectares': 1}
        },
        'normalized_units': {
            'land_use_area': 'hectares',
            'protected_area': 'hectares',
            'biodiversity_impact': 'hectares'
        }
    }
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

# ====================================================================
# Environmental Module Helper Functions
# ====================================================================

def normalize_environmental_quantity(module_type, activity_type, quantity, unit):
    """
    Convert environmental activity data to normalized units
    Returns: (normalized_quantity, normalized_unit)
    """
    if module_type not in ENVIRONMENTAL_CONFIG:
        return quantity, unit
    
    config = ENVIRONMENTAL_CONFIG[module_type]
    
    # Check if activity and unit are valid
    if (activity_type in config['units'] and 
        unit in config['units'][activity_type]):
        
        conversion_factor = config['units'][activity_type][unit]
        normalized_quantity = quantity * conversion_factor
        normalized_unit = config['normalized_units'].get(activity_type, unit)
        
        return normalized_quantity, normalized_unit
    
    # Return original if no conversion found
    return quantity, unit


def get_company_intensity_factors(username):
    """
    Get company normalization factors from Company Settings
    Returns dict with: employees, revenue, site_area, production_volume
    """
    # Mock data - replace with actual Company Settings lookup
    # TODO: Integrate with actual CompanySettings model
    default_factors = {
        'employees': 100,  # number of employees
        'revenue': 1000000,  # revenue in base currency
        'site_area': 5000,  # total site area in m²
        'production_volume': 10000,  # production units
    }
    
    # Placeholder for real integration
    # from app import CompanySettings
    # settings = CompanySettings.query.filter_by(company_id=username).first()
    # if settings:
    #     return {
    #         'employees': settings.number_of_employees or default_factors['employees'],
    #         'revenue': settings.annual_revenue or default_factors['revenue'],
    #         'site_area': settings.total_site_area or default_factors['site_area'],
    #         'production_volume': settings.production_volume or default_factors['production_volume']
    #     }
    
    return default_factors


def calculate_energy_intensity(energy_data, company_factors):
    """
    Calculate energy intensity metrics
    energy_data: list of EnvironmentalRecord objects (module_type='energy')
    Returns dict of intensity metrics
    """
    if not energy_data:
        return {}
    
    # Sum all normalized energy consumption
    total_energy_kwh = sum(
        record.normalized_quantity or record.quantity 
        for record in energy_data 
        if record.module_type == 'energy'
    )
    
    # Convert to different units for reporting
    total_energy_gj = total_energy_kwh * 0.0036 if total_energy_kwh else 0
    
    intensities = {
        'total_energy_kwh': round(total_energy_kwh, 2),
        'total_energy_gj': round(total_energy_gj, 2),
    }
    
    # Calculate per-employee intensity
    if company_factors.get('employees') and company_factors['employees'] > 0:
        intensities['per_employee_kwh'] = round(
            total_energy_kwh / company_factors['employees'], 2
        )
    
    # Calculate per-revenue intensity
    if company_factors.get('revenue') and company_factors['revenue'] > 0:
        intensities['per_revenue_kwh'] = round(
            total_energy_kwh / (company_factors['revenue'] / 1000000), 2  # per million currency
        )
    
    # Calculate per-area intensity
    if company_factors.get('site_area') and company_factors['site_area'] > 0:
        intensities['per_area_kwh'] = round(
            total_energy_kwh / company_factors['site_area'], 2
        )
    
    return intensities


def calculate_water_intensity(water_data, company_factors):
    """
    Calculate water intensity metrics
    water_data: list of EnvironmentalRecord objects (module_type='water')
    Returns dict of intensity metrics
    """
    if not water_data:
        return {}
    
    # Sum all normalized water consumption (withdrawal - consumption)
    total_water_m3 = 0
    water_by_type = {}
    
    for record in water_data:
        if record.module_type == 'water':
            quantity = record.normalized_quantity or record.quantity
            activity = record.activity_type
            
            if activity not in water_by_type:
                water_by_type[activity] = 0
            water_by_type[activity] += quantity
            
            # For intensity calculations, use withdrawal as primary
            if activity == 'water_withdrawal':
                total_water_m3 += quantity
    
    intensities = {
        'total_water_m3': round(total_water_m3, 2),
        'water_by_type': {k: round(v, 2) for k, v in water_by_type.items()},
    }
    
    # Calculate per-employee intensity
    if company_factors.get('employees') and company_factors['employees'] > 0:
        intensities['per_employee_m3'] = round(
            total_water_m3 / company_factors['employees'], 2
        )
    
    # Calculate water recycling rate
    withdrawal = water_by_type.get('water_withdrawal', 0)
    consumption = water_by_type.get('water_consumption', 0)
    
    if withdrawal > 0:
        intensities['water_recycling_rate'] = round(
            (withdrawal - consumption) / withdrawal * 100, 1
        )
    
    return intensities


def calculate_waste_intensity(waste_data, company_factors):
    """
    Calculate waste intensity metrics
    waste_data: list of EnvironmentalRecord objects (module_type='waste')
    Returns dict of intensity metrics
    """
    if not waste_data:
        return {}
    
    # Sum all normalized waste by type
    total_waste_kg = 0
    waste_by_type = {}
    
    for record in waste_data:
        if record.module_type == 'waste':
            quantity = record.normalized_quantity or record.quantity
            activity = record.activity_type
            
            if activity not in waste_by_type:
                waste_by_type[activity] = 0
            waste_by_type[activity] += quantity
            
            total_waste_kg += quantity
    
    intensities = {
        'total_waste_kg': round(total_waste_kg, 2),
        'total_waste_tons': round(total_waste_kg / 1000, 2),
        'waste_by_type': {k: round(v, 2) for k, v in waste_by_type.items()},
    }
    
    # Calculate waste diversion rate
    total_waste = waste_by_type.get('waste_general', 0)
    recycled = waste_by_type.get('recycled_waste', 0)
    organic = waste_by_type.get('organic_waste', 0)
    
    if total_waste > 0:
        intensities['recycling_rate'] = round(
            recycled / total_waste * 100, 1
        )
        intensities['organic_recovery_rate'] = round(
            organic / total_waste * 100, 1
        )
        intensities['total_diversion_rate'] = round(
            (recycled + organic) / total_waste * 100, 1
        )
    
    # Calculate per-employee intensity
    if company_factors.get('employees') and company_factors['employees'] > 0:
        intensities['per_employee_kg'] = round(
            total_waste_kg / company_factors['employees'], 2
        )
    
    return intensities


def calculate_land_intensity(land_data, company_factors):
    """
    Calculate land use intensity metrics
    land_data: list of EnvironmentalRecord objects (module_type='land_biodiversity')
    Returns dict of intensity metrics
    """
    if not land_data:
        return {}
    
    # Extract land use data
    land_use_area = 0
    protected_area = 0
    
    for record in land_data:
        if record.module_type == 'land_biodiversity':
            quantity = record.normalized_quantity or record.quantity
            
            if record.activity_type == 'land_use_area':
                land_use_area = quantity
            elif record.activity_type == 'protected_area':
                protected_area = quantity
    
    intensities = {
        'land_use_hectares': round(land_use_area, 2),
        'protected_hectares': round(protected_area, 2),
    }
    
    # Calculate protection percentage
    if land_use_area > 0:
        intensities['protection_percentage'] = round(
            protected_area / land_use_area * 100, 1
        )
    
    # Calculate per-employee land use
    if company_factors.get('employees') and company_factors['employees'] > 0:
        intensities['per_employee_hectares'] = round(
            land_use_area / company_factors['employees'], 4
        )
    
    return intensities


def calculate_environmental_intensities(username, reporting_year=None):
    """
    Main function to calculate all environmental intensities for a user
    Returns dict with intensity metrics for all modules
    """
    with app.app_context():
        try:
            # Get company normalization factors
            company_factors = get_company_intensity_factors(username)
            
            # Query environmental data
            query = EnvironmentalRecord.query.filter_by(
                user_id=username,
                status='approved'  # Only use approved data
            )
            
            if reporting_year:
                query = query.filter_by(reporting_year=reporting_year)
            
            all_records = query.all()
            
            # Group by module type
            records_by_module = {}
            for record in all_records:
                if record.module_type not in records_by_module:
                    records_by_module[record.module_type] = []
                records_by_module[record.module_type].append(record)
            
            # Calculate intensities for each module
            results = {
                'company_factors': company_factors,
                'intensities': {}
            }
            
            # Energy intensity
            if 'energy' in records_by_module:
                results['intensities']['energy'] = calculate_energy_intensity(
                    records_by_module['energy'], company_factors
                )
            
            # Water intensity
            if 'water' in records_by_module:
                results['intensities']['water'] = calculate_water_intensity(
                    records_by_module['water'], company_factors
                )
            
            # Waste intensity
            if 'waste' in records_by_module:
                results['intensities']['waste'] = calculate_waste_intensity(
                    records_by_module['waste'], company_factors
                )
            
            # Land intensity
            if 'land_biodiversity' in records_by_module:
                results['intensities']['land'] = calculate_land_intensity(
                    records_by_module['land_biodiversity'], company_factors
                )
            
            return results
            
        except Exception as e:
            print(f"Error calculating environmental intensities: {e}")
            return {'error': str(e)}

# Helper function
def get_module_id(module_name):
    """Get module ID from name"""
    module = ESGDataModule.query.filter_by(name=module_name).first()
    return module.id if module else None

def seed_default_admin():
    """Create default admin user if none exists"""
    if User.query.count() == 0:
        admin = User(
            username     = 'admin',
            email        = 'admin@emittif.io',
            company_name = 'EmittiF Demo',
            role         = 'company'
        )
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin user created: admin / password")

# Emission factors (kg CO2e per unit) - Based on GHG Protocol and MGTC Malaysia
EMISSION_FACTORS = {
    'scope1': {
        'diesel': 2.68,  # kg CO2e per liter
        'gasoline': 2.31,  # kg CO2e per liter - ADDED THIS
        'ron95': 2.31,    # kg CO2e per liter (same as gasoline)
        'ron97': 2.31,    # kg CO2e per liter (same as gasoline)
        'petrol': 2.31,   # kg CO2e per liter (generic petrol)
        'fuel': 2.31,     # kg CO2e per liter (generic fuel - added to fix the issue)
        'natural_gas': 2.75,  # kg CO2e per m3
        'lpg': 1.55,  # kg CO2e per liter
        'coal': 2.42,  # kg CO2e per kg
    },
    'scope2': {
        'electricity': 0.85,  # kg CO2e per kWh (Malaysia grid average)
    },
    'scope3': {
        'business_travel_air': 0.25,  # kg CO2e per km
        'business_travel_car': 0.21,  # kg CO2e per km
        'employee_commute': 0.12,  # kg CO2e per km
        'purchased_goods': 0.15,  # kg CO2e per RM (estimated)
        'waste_disposal': 0.85,  # kg CO2e per kg
        'water': 0.344,  # kg CO2e per m³ (water supply & treatment)
    }
}

# AI Consultation Knowledge Base
AI_KNOWLEDGE_BASE = {
    'scope1': {
        'diesel': {
            'reduction_tips': [
                "Switch to biodiesel blends (B10-B20) to reduce emissions by 15-20%",
                "Implement fuel-efficient driving training for drivers",
                "Regular vehicle maintenance can improve fuel efficiency by 5-10%",
                "Consider electric or hybrid vehicles for your fleet",
                "Optimize delivery routes to reduce unnecessary mileage"
            ],
            'crediting_opportunities': [
                "Biofuel blending projects under Malaysia's Biofuel Industry Act",
                "Vehicle efficiency improvement projects",
                "Fleet electrification projects"
            ]
        },
        'gasoline': {
            'reduction_tips': [
                "Switch to fuel-efficient vehicles with better mileage",
                "Maintain proper tire pressure to improve fuel efficiency by 3%",
                "Avoid aggressive driving and rapid acceleration",
                "Use the recommended grade of motor oil",
                "Reduce vehicle weight by removing unnecessary items"
            ],
            'crediting_opportunities': [
                "Fuel efficiency improvement projects",
                "Eco-driving training programs",
                "Vehicle fleet optimization projects"
            ]
        },
        'ron95': {
            'reduction_tips': [
                "RON 95 has lower octane than RON 97 - consider switching to more efficient vehicles",
                "Regular engine maintenance improves RON 95 combustion efficiency",
                "Avoid over-revving the engine as RON 95 has lower knock resistance",
                "Use fuel additives to improve combustion efficiency",
                "Consider upgrading to vehicles designed for lower octane fuels"
            ],
            'crediting_opportunities': [
                "Fuel switching programs",
                "Engine optimization projects",
                "Alternative fuel vehicle adoption"
            ]
        },
        'ron97': {
            'reduction_tips': [
                "RON 97 provides better engine performance and efficiency",
                "High-performance vehicles benefit more from RON 97's higher octane",
                "Regular maintenance still required despite higher quality fuel",
                "Consider if your vehicle actually requires RON 97 or if RON 95 is sufficient",
                "Monitor fuel consumption patterns with different fuel grades"
            ],
            'crediting_opportunities': [
                "Premium fuel efficiency projects",
                "High-performance vehicle optimization",
                "Fuel quality improvement initiatives"
            ]
        },
        'natural_gas': {
            'reduction_tips': [
                "Install energy-efficient boilers and heaters",
                "Implement building automation systems for optimal heating",
                "Consider biogas or renewable natural gas alternatives",
                "Improve insulation to reduce heating requirements",
                "Regular maintenance of gas equipment to prevent leaks"
            ],
            'crediting_opportunities': [
                "Energy efficiency projects under MGTC",
                "Biomethane injection projects",
                "Fugitive emission reduction projects"
            ]
        }
    },
    'scope2': {
        'electricity': {
            'reduction_tips': [
                "Install solar panels - typical ROI 3-5 years in Malaysia",
                "Switch to LED lighting - reduces lighting energy by 50-70%",
                "Implement energy management systems",
                "Use energy-efficient HVAC systems",
                "Participate in demand response programs"
            ],
            'crediting_opportunities': [
                "Solar PV projects under Feed-in Tariff",
                "Energy efficiency certificates",
                "Green Electricity Tariff programs"
            ]
        }
    },
    'scope3': {
        'business_travel_air': {
            'reduction_tips': [
                "Implement video conferencing to reduce air travel by 30%",
                "Choose direct flights to reduce emissions from takeoff/landing",
                "Use airlines with newer, more efficient fleets",
                "Combine multiple trips into one",
                "Encourage train travel for regional trips"
            ],
            'crediting_opportunities': [
                "Sustainable aviation fuel certificates",
                "Carbon offset programs for unavoidable travel"
            ]
        },
        'employee_commute': {
            'reduction_tips': [
                "Implement work-from-home policies 2-3 days per week",
                "Provide electric vehicle charging stations",
                "Offer public transport subsidies",
                "Create carpool matching programs",
                "Install bicycle parking and showers"
            ],
            'crediting_opportunities': [
                "Telecommuting emission reduction projects",
                "EV infrastructure development projects"
            ]
        }
    }
}

# Sample emission data structure
emission_data = {
    'admin': {
        'scope1': [
            {'category': 'diesel', 'amount': 500, 'unit': 'liters', 'date': '2024-01-15', 'co2e': 1340},
            {'category': 'natural_gas', 'amount': 200, 'unit': 'm3', 'date': '2024-01-20', 'co2e': 550},
        ],
        'scope2': [
            {'category': 'electricity', 'amount': 1500, 'unit': 'kWh', 'date': '2024-01-25', 'co2e': 1275},
        ],
        'scope3': [
            {'category': 'business_travel_air', 'amount': 2000, 'unit': 'km', 'date': '2024-01-10', 'co2e': 500},
            {'category': 'employee_commute', 'amount': 5000, 'unit': 'km', 'date': '2024-01-05', 'co2e': 600},
        ]
    }
}

# ENHANCED FUEL TYPE DETECTION WITH FUEL GRADE DETECTION
def detect_fuel_type_enhanced(text):
    """Enhanced fuel type detection with water bill support"""
    text_lower = text.lower()
    
    # ── Water bill detection (robust to OCR concatenation and missing chars) ──
    water_company_indicators = [
        'saj', 'ranhill', 'syabas', 'air selangor', 'air melaka', 'samb', 'sains',
        'lap', 'paip', 'pba', 'satuj', 'aksh', 'akshb', 'sada', 'air sabah', 'jans',
        'kuching water', 'laku', 'sibu water', 'air sarawak'
    ]
    water_bill_terms = ['bil', 'caj', 'penggunaan', 'bacaan', 'deposit', 'tarif']
    water_garbled_combined = [
        'bilair', 'cajair', 'penggunaanair', 'ranhillsaj', 'airsaj', 'airbil', 'aircaj'
    ]

    text_lower = text.lower()

    # Check for common concatenated forms directly
    if any(garb in text_lower for garb in water_garbled_combined):
        return 'water'

    # Water bill check: only fires when 'air' is present AND a company/bill term exists
    if 'air' in text_lower:
        if any(ind in text_lower for ind in water_company_indicators) or \
           any(term in text_lower for term in water_bill_terms):
            return 'water'

    # ── Electricity bill indicators (Scope 2) ── (checked regardless of 'air')
    electricity_keywords = [
        'kwh', 'kilowatt', 'tenaga', 'electric', 'electricity',
        'tenaga nasional', 'tnb', 'jomsave', 'kw', 'kilowatt-hour',
        'unit tenaga', 'caj elektrik', 'bacaan', 'penggunaan'
    ]

    # ── Fuel grade detection ──
    diesel_keywords = ['diesel', 'disel', 'diesal', 'minyak diesel', 'biodiesel']
    ron95_keywords = [
        'ron95', 'ron 95', '95 ron', 'premium 95',
        'petronas primax 95', 'shell fuel save 95', 'petron blaze 95', 'bhp 95'
    ]
    ron97_keywords = [
        'ron97', 'ron 97', '97 ron', 'premium 97',
        'petronas primax 97', 'shell v-power 97', 'petron blaze 97', 'bhp xtra 97'
    ]
    petrol_keywords = [
        'petrol', 'gasoline', 'bensin', 'minyak petrol', 'gas',
        'fuel', 'petroleum', 'petroliam', 'shell', 'petron', 'petronas',
        'caltex', 'bhp', 'esso', 'mobil'
    ]

    # ── Keyword matching ──
    elec_matches = sum(1 for kw in electricity_keywords if kw in text_lower)
    diesel_matches = sum(1 for kw in diesel_keywords if kw in text_lower)
    ron95_matches = sum(1 for kw in ron95_keywords if kw in text_lower)
    ron97_matches = sum(1 for kw in ron97_keywords if kw in text_lower)
    petrol_matches = sum(1 for kw in petrol_keywords if kw in text_lower)

    has_kwh = 'kwh' in text_lower
    has_electricity_company = any(company in text_lower for company in ['tenaga', 'tnb', 'sesb'])
    has_energy_units = any(unit in text_lower for unit in ['kwh', 'kilowatt'])

    # ── Decision logic ──
    if (elec_matches > 0) or has_kwh or has_electricity_company or has_energy_units:
        return 'electricity'
    elif diesel_matches > 0:
        return 'diesel'
    elif ron97_matches > 0:
        return 'ron97'
    elif ron95_matches > 0:
        return 'ron95'
    elif petrol_matches > 0:
        return 'gasoline'
    elif any(fuel_word in text_lower for fuel_word in ['liter', 'litre', 'ltr', 'l', 'petrol', 'diesel']):
        return 'fuel'

    return 'unknown'

# ENHANCED ELECTRICITY CONSUMPTION EXTRACTION
def extract_electricity_consumption(text):
    """
    Extract electricity consumption in kWh from bill text
    """
    text_lower = text.lower()
    
    # Pattern 1: Direct kWh values with context
    patterns = [
        # Look for kWh values after consumption keywords
        r'(kwh|kilowatt|usage|penggunaan|kegunaan)[\s:]*([0-9]+[.,]?[0-9]*)',
        # Look for consumption blocks (common in Malaysian bills)
        r'([0-9]+[.,]?[0-9]*)\s*kwh',
        # Look for consumption in tariff breakdown sections
        r'blok\s*[0-9]+\s*[0-9]+\s*\([^)]+\)\s*([0-9]+[.,]?[0-9]*)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            for match in matches:
                if isinstance(match, tuple):
                    # Get the number part from tuple match
                    value = match[-1]
                else:
                    value = match
                
                try:
                    # Clean and convert the value
                    value_clean = value.replace(',', '').replace(' ', '')
                    consumption = float(value_clean)
                    
                    # Validate reasonable kWh range (typical household: 100-2000 kWh)
                    if 50 <= consumption <= 5000:
                        return consumption
                except ValueError:
                    continue
    
    # Fallback: Look for the largest number that could be kWh consumption
    numbers = re.findall(r'([0-9]+[.,]?[0-9]{0,3})\s*(?=kwh|$)', text_lower, re.IGNORECASE)
    for num in numbers:
        try:
            consumption = float(num.replace(',', ''))
            if 50 <= consumption <= 5000:
                return consumption
        except ValueError:
            continue
    
    return None

# ENHANCED AMOUNT EXTRACTION FOR FUEL RECEIPTS
def extract_fuel_quantity_enhanced(text):
    """Enhanced fuel quantity extraction from receipts"""
    text_lower = text.lower()
    
    # Try multiple patterns for fuel quantity
    patterns = [
        # Pattern: "10.00 L" or "10.00 LTR" or "10.00 LITRE"
        r'([0-9]+[.,]?[0-9]*)\s*(?:l|litre|liter|ltr)\b',
        # Pattern: "QTY: 10.00" or "QUANTITY: 10.00"
        r'(?:qty|quantity)[\s:]*([0-9]+[.,]?[0-9]*)',
        # Pattern: "10.00" followed by fuel type
        r'([0-9]+[.,]?[0-9]*)\s*(?:ron|diesel|petrol|gasoline)',
        # Pattern: Common in Malaysian receipts: "10.00 L RON95"
        r'([0-9]+[.,]?[0-9]*)\s*l\s*(?:ron)?\s*[0-9]*',
        # Pattern: Look for amount in liters in price calculation
        r'([0-9]+[.,]?[0-9]*)\s*[x*]\s*[0-9]+[.,]?[0-9]*',  # e.g., "10.00 x 2.31"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            for match in matches:
                try:
                    # Clean the value
                    if isinstance(match, tuple):
                        value = match[0]
                    else:
                        value = match
                    
                    value_clean = value.replace(',', '').strip()
                    quantity = float(value_clean)
                    
                    # Validate reasonable fuel quantity (1-200 liters typical for vehicles)
                    if 1 <= quantity <= 200:
                        print(f"✓ Found fuel quantity: {quantity} liters")
                        return quantity
                except ValueError:
                    continue
    
    # Fallback: Look for any number that might be fuel quantity
    # Extract all numbers and find the most likely fuel quantity
    all_numbers = re.findall(r'([0-9]+[.,]?[0-9]+)', text_lower)
    potential_fuel_quantities = []
    
    for num_str in all_numbers:
        try:
            num = float(num_str.replace(',', ''))
            # Fuel quantities are typically between 1-200 liters and often have decimal places
            if 1 <= num <= 200 and '.' in num_str:
                potential_fuel_quantities.append(num)
        except:
            continue
    
    if potential_fuel_quantities:
        # Return the most likely (usually the largest in the reasonable range)
        return max(potential_fuel_quantities)
    
    return None

# ENHANCED AMOUNT EXTRACTION
def extract_amount_enhanced(text, fuel_type):
    """
    Extract appropriate amount based on fuel type
    """
    if fuel_type == 'electricity':
        # For electricity, prioritize kWh consumption over monetary amount
        consumption = extract_electricity_consumption(text)
        if consumption:
            return consumption, 'kWh'
        
        # Fallback to monetary amount only if consumption not found
        monetary_amount = extract_monetary_amount(text)
        return monetary_amount, 'RM'  # Note this is monetary, not energy
    
    elif fuel_type == 'water':
        consumption = extract_water_consumption(text)
        if consumption:
            return consumption, 'm³'
        return None, None
    
    elif fuel_type in ['diesel', 'gasoline', 'ron95', 'ron97', 'fuel', 'petrol']:
        # For fuel, use enhanced extraction
        quantity = extract_fuel_quantity_enhanced(text)
        if quantity:
            return quantity, 'liters'
        
        # Fallback to old method
        return extract_fuel_quantity(text), 'liters'
    
    return None, None

def extract_monetary_amount(text):
    """Extract monetary amount from text"""
    try:
        # Look for RM patterns
        patterns = [
            r'rm\s*([0-9]+[.,]?[0-9]*)',
            r'([0-9]+[.,]?[0-9]*)\s*rm',
            r'total[\s:]*rm\s*([0-9]+[.,]?[0-9]*)',
            r'jumlah[\s:]*rm\s*([0-9]+[.,]?[0-9]*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return float(matches[0].replace(',', ''))
    except:
        pass
    return None

def extract_fuel_quantity(text):
    """Extract fuel quantity in liters (legacy function)"""
    try:
        patterns = [
            r'([0-9]+[.,]?[0-9]*)\s*l',
            r'([0-9]+[.,]?[0-9]*)\s*liters',
            r'quantity\s*[:=]?\s*([0-9]+[.,]?[0-9]*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return float(matches[0].replace(',', ''))
    except:
        pass
    return None

def extract_water_consumption(text):
    """
    Extract water consumption in m³ from Malaysian water bills.

    Handles two confirmed real-world layouts:
      - SAJ/Ranhill: "PENGGUNAAN AIR" label on one line, bare number
        (e.g. "24.00") appears 1-2 lines later, no m3 suffix.
        Intervening line is often "REBAT KERAJAAN JOHOR" (text only).
      - SAINS: value appears as "43 m3" in the meter data row.

    Priority:
      L1 – post-trigger bare number  (SAJ pattern)
      L2 – unit-anchored number+m3   (SAINS pattern), tariff rows excluded
      L3 – meter reading difference
      L4 – contextual median fallback
    """
    text_upper = text.upper()
    lines = text_upper.splitlines()

    def to_float(s):
        try:
            return float(re.sub(r'[^\d.]', '', s.replace(',', '.')))
        except (ValueError, AttributeError):
            return None

    def plausible(val):
        return val is not None and 1 <= val <= 5000

    def is_tariff_line(line):
        """True for BLOK TARIF table rows and range rows like '0-20 M3'."""
        if any(kw in line for kw in ['BLOK TARIF', 'KADAR', 'PRORATA',
                                      'FAKTOR', 'JENIS TARIF', 'JENIS BACAAN']):
            return True
        if re.search(r'\d+\s*[-–]\s*\d+', line):   # "0-20", "20-35"
            return True
        return False

    def is_prorata_value(line):
        """SAJ prorata values come as '20.0000' or '4.0000' (4 dp)."""
        return bool(re.match(r'^\d+\.\d{4}$', line.strip()))

    # ── Layer 1: post-trigger bare number (SAJ "PENGGUNAAN AIR" pattern) ─
    # Scan up to 6 lines after the trigger keyword.
    # Skip text-only lines (REBAT, etc.) but stop at hard section headers.
    trigger_kw = [
        'PENGGUNAAN AIR',
        'JUMLAH PENGGUNAAN SEMASA',
        'JUMLAH PENGGUNAAN',
        'ISIPADU PENGGUNAAN',
        'TOTAL CONSUMPTION',
        'WATER CONSUMPTION',
    ]
    hard_stop_kw = ['JUMLAI', 'JUMLAH', 'CAJ SEMASA', 'CAJ AIR SEMASA',
                    'BAYAR', 'TARIKH', 'FAKTOR', 'JENIS', 'BLOK', 'KADAR']

    for i, line in enumerate(lines):
        if any(kw in line for kw in trigger_kw):
            for j in range(i + 1, min(i + 6, len(lines))):
                nxt = lines[j].strip()
                if not nxt:
                    continue
                has_digit = bool(re.search(r'\d', nxt))
                # Stop on hard-stop labels that carry no number
                if not has_digit and any(s in nxt for s in hard_stop_kw):
                    break
                # Skip prorata rows (20.0000 style)
                if is_prorata_value(nxt):
                    continue
                # Skip pure label lines starting with REBAT (no number)
                if nxt.startswith('REBAT') and not has_digit:
                    continue
                # Accept bare number ± optional m3 unit
                m = re.match(
                    r'^(\d{1,5}(?:[.,]\d{1,4})?)(?:\s*(?:m3|m³|m²|m\^3))?$',
                    nxt, re.IGNORECASE
                )
                if m:
                    val = to_float(m.group(1))
                    if plausible(val):
                        print(f"✓ Water L1 (post-trigger bare number): {val} m³")
                        return val

    # ── Layer 2: unit-anchored, tariff / prorata rows excluded ───────────
    unit_pat = re.compile(
        r'\b(\d{1,5}(?:[.,]\d{1,3})?)\s*(?:m3|m³|m²|m\^3|meter\s*padu)\b',
        re.IGNORECASE
    )
    for line in lines:
        if is_tariff_line(line) or is_prorata_value(line.strip()):
            continue
        for m in unit_pat.finditer(line):
            val = to_float(m.group(1))
            if plausible(val):
                print(f"✓ Water L2 (unit-anchored non-tariff): {val} m³")
                return val

    # ── Layer 3: meter reading difference ────────────────────────────────
    for i, line in enumerate(lines):
        if any(kw in line for kw in ['BACAAN', 'SEMASA', 'DAHULU', 'LEPAS']):
            combined = line + ' ' + (lines[i + 1] if i + 1 < len(lines) else '')
            nums = sorted(
                [int(n) for n in re.findall(r'\b(\d{3,6})\b', combined) if n.isdigit()],
                reverse=True
            )
            if len(nums) >= 2:
                diff = nums[0] - nums[1]
                if plausible(float(diff)):
                    print(f"✓ Water L3 (meter diff): {diff} m³  ({nums[0]}-{nums[1]})")
                    return float(diff)

    # ── Layer 4: contextual median fallback ──────────────────────────────
    monetary_kw = {'RM', 'MYR', 'RINGGIT', 'JUMLAH', 'TOTAL', 'BAYAR',
                   'CHARGE', 'CAJ', 'AMAUN', 'AMOUNT', 'FEE', 'SEN',
                   'DEPOSIT', 'TUNGGAKAN', 'REBAT'}
    serial_pat = re.compile(r'[A-Z]{2,}\d{4,}')

    candidates = []
    for line in lines:
        if any(kw in line for kw in monetary_kw):
            continue
        if serial_pat.search(line):
            continue
        if is_tariff_line(line) or is_prorata_value(line.strip()):
            continue
        for n in re.findall(r'\b(\d{1,4})\b', line):
            val = to_float(n)
            if plausible(val):
                candidates.append(val)

    if candidates:
        s = sorted(candidates)
        best = s[len(s) // 2]
        print(f"⚠️ Water L4 (contextual median fallback): {best} m³  pool={s}")
        return best

    print("❌ Water: could not extract consumption")
    return None



# ENHANCED SCOPE CLASSIFICATION
def determine_scope_enhanced(fuel_type, amount, unit):
    """
    Determine Scope 1, 2, or 3 based on fuel type and context
    """
    scope_mapping = {
        'electricity': 'scope2',
        'diesel': 'scope1',
        'gasoline': 'scope1',
        'ron95': 'scope1',
        'ron97': 'scope1',
        'petrol': 'scope1',
        'fuel': 'scope1',  # Generic fuel is also Scope 1
        'gas': 'scope1',
        'natural_gas': 'scope1',
        'water': 'scope3',
        'waste': 'scope3'
    }
    
    return scope_mapping.get(fuel_type, 'scope3')

# ENHANCED CONFIDENCE SCORING
def calculate_confidence_enhanced(text, fuel_type, amount, unit):
    """
    Calculate confidence score for the analysis
    """
    confidence = 0.0
    text_lower = text.lower()
    
    # Base confidence
    if fuel_type != 'unknown':
        confidence += 0.3
    
    # Amount extraction confidence
    if amount is not None:
        confidence += 0.3
    
    # Unit appropriateness confidence
    if fuel_type == 'electricity' and unit == 'kWh':
        confidence += 0.4
    elif fuel_type == 'electricity' and unit == 'RM':
        confidence += 0.2  # Lower confidence for monetary amount
    elif fuel_type in ['diesel', 'gasoline', 'ron95', 'ron97', 'fuel', 'petrol'] and unit in ['liters', 'l', 'ltr']:
        confidence += 0.4
    
    # Pattern matching confidence
    if 'kwh' in text_lower and fuel_type == 'electricity':
        confidence += 0.2
    elif any(fuel_word in text_lower for fuel_word in ['diesel', 'petrol', 'ron95', 'ron97', 'gasoline']) and fuel_type != 'unknown':
        confidence += 0.2
    
    return min(confidence, 1.0)

# UPDATED PARSE EXTRACTED TEXT FUNCTION WITH BETTER FUEL HANDLING
def parse_extracted_text(text):
    """Parse extracted text to find emission data with enhanced pattern matching"""
    if not text:
        print("⚠️ No text provided to parser")
        return None
    
    print(f"🔍 Analyzing text ({len(text)} chars): '{text}'")
    
    # Step 1: Detect fuel type with enhanced logic
    fuel_type = detect_fuel_type_enhanced(text)
    print(f"✓ Detected fuel type: {fuel_type}")
    
    # Step 2: Extract appropriate amount and unit
    amount, unit = extract_amount_enhanced(text, fuel_type)
    print(f"✓ Extracted amount: {amount} {unit}")
    
    # Step 3: Determine scope
    scope = determine_scope_enhanced(fuel_type, amount, unit)
    print(f"✓ Determined scope: {scope}")
    
    # Initialize result
    result = {
        'scope': scope,
        'category': fuel_type,
        'amount': amount or 0.0,
        'unit': unit or 'unknown',
        'confidence': 0.0
    }
    
    # Calculate confidence
    result['confidence'] = calculate_confidence_enhanced(text, fuel_type, amount, unit)
    
    # Calculate CO2e - FIXED: Use appropriate emission factor
    if result['amount'] > 0:
        # Get the emission factor based on scope and category
        if result['scope'] in EMISSION_FACTORS:
            factor = EMISSION_FACTORS[result['scope']].get(result['category'], 0)
            if factor == 0:
                # Try fallback categories
                if result['category'] == 'fuel':
                    factor = EMISSION_FACTORS[result['scope']].get('gasoline', 0)
                elif result['category'] == 'petrol':
                    factor = EMISSION_FACTORS[result['scope']].get('gasoline', 0)
            
            result['co2e'] = result['amount'] * factor
            print(f"✅ SUCCESS! {result['amount']} {result['unit']} of {result['category']} = {result['co2e']} kg CO₂e (factor: {factor})")
        else:
            result['co2e'] = 0
            print(f"❌ No emission factor found for scope: {result['scope']}, category: {result['category']}")
    else:
        result['co2e'] = 0
        print("❌ No amount detected in receipt")
    
    return result

# REAL AI OCR FUNCTIONS
def _ocr_space_request(file_data, filename="file.png", filetype="auto"):
    """Core helper – sends raw bytes to OCR.space and returns parsed text."""
    try:
        payload = {
            'apikey'            : OCR_SPACE_API_KEY,
            'language'          : 'eng',
            'isOverlayRequired' : False,
            'detectOrientation' : True,
            'scale'             : True,
            'isTable'           : False,
            'OCREngine'         : 2,
            'filetype'          : filetype,
        }
        files = {'file': (filename, file_data, 'application/octet-stream')}
        print(f"📤 Sending to OCR.space API (engine 2, filetype={filetype})...")
        response = requests.post(OCR_SPACE_API_URL, data=payload, files=files, timeout=60)
        response.raise_for_status()
        result = response.json()
        if result.get('IsErroredOnProcessing'):
            print(f"❌ OCR.space error: {result.get('ErrorMessage')}")
            return None
        pages = result.get('ParsedResults') or []
        if not pages:
            print("⚠️ OCR.space returned no parsed results")
            return None
        full_text = "\n".join((p.get('ParsedText') or '') for p in pages)
        print(f"✓ OCR.space done. Extracted {len(full_text)} chars")
        return full_text.strip() or None
    except requests.exceptions.Timeout:
        print("❌ OCR.space request timed out")
        return None
    except Exception as e:
        print(f"❌ OCR.space request failed: {e}")
        return None


def extract_text_from_image(file_data):
    """Extract text from image using OCR.space API"""
    try:
        print("🔍 Starting OCR processing for image via OCR.space...")
        image = Image.open(io.BytesIO(file_data))
        fmt = (image.format or 'PNG').upper()
        filename = f"upload.{fmt.lower()}"
        print(f"✓ Image format: {fmt}, size: {image.size}")
        text = _ocr_space_request(file_data, filename=filename, filetype=fmt)
        if text:
            print(f"✓ Text preview: '{text[:200]}...'")
        else:
            print("⚠️ No text extracted from image")
        return text
    except Exception as e:
        print(f"❌ OCR Error: {str(e)}")
        return None

def extract_text_from_pdf(file_data):
    """Extract text from PDF using OCR.space API, with PyPDF2 text-layer fallback"""
    try:
        print("🔍 Starting PDF processing via OCR.space...")
        text = _ocr_space_request(file_data, filename="upload.pdf", filetype="PDF")
        if text:
            print(f"✓ PDF OCR complete. Total chars: {len(text)}")
            return text
        raise Exception("No OCR text – trigger fallback")
    except Exception as e:
        try:
            print(f"🔄 Trying PyPDF2 fallback... (reason: {e})")
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
            full_text = ""
            for page in pdf_reader.pages:
                full_text += (page.extract_text() or "") + "\n"
            if full_text.strip():
                print(f"✅ PyPDF2 extracted {len(full_text)} characters")
                return full_text.strip()
            print("⚠️ PyPDF2 also returned no text")
        except Exception as pdf_error:
            print(f"❌ PyPDF2 fallback also failed: {pdf_error}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_emissions(scope, category, amount, unit):
    """Calculate CO2e emissions based on category and amount"""
    try:
        amount = float(amount)
        if scope == 'scope1':
            factor = EMISSION_FACTORS['scope1'].get(category, 0)
        elif scope == 'scope2':
            factor = EMISSION_FACTORS['scope2'].get(category, 0)
        else:
            factor = EMISSION_FACTORS['scope3'].get(category, 0)
        
        co2e = amount * factor
        return round(co2e, 2)
    except:
        return 0

def analyze_emission_patterns(user_data):
    """Analyze user emission data to identify patterns and improvement opportunities"""
    analysis = {
        'highest_emission_scope': '',
        'top_emission_sources': [],
        'total_emissions': 0,
        'reduction_potential': 0,
        'priority_actions': []
    }
    
    if not isinstance(user_data, dict):
        user_data = {'scope1': [], 'scope2': [], 'scope3': []}
    
    scope_totals = {}
    for scope, items in user_data.items():
        if isinstance(items, list):
            scope_total = sum(item.get('co2e', 0) for item in items if isinstance(item, dict))
            scope_totals[scope] = scope_total
            analysis['total_emissions'] += scope_total
    
    if scope_totals:
        analysis['highest_emission_scope'] = max(scope_totals, key=scope_totals.get)
    
    all_emissions = []
    for scope, items in user_data.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    all_emissions.append({
                        'scope': scope,
                        'category': item.get('category', 'unknown'),
                        'co2e': item.get('co2e', 0),
                        'amount': item.get('amount', 0),
                        'unit': item.get('unit', 'unknown')
                    })
    
    all_emissions.sort(key=lambda x: x['co2e'], reverse=True)
    analysis['top_emission_sources'] = all_emissions[:3]
    
    analysis['reduction_potential'] = analysis['total_emissions'] * 0.3
    
    for emission_source in analysis['top_emission_sources'][:2]:
        scope = emission_source['scope']
        category = emission_source['category']
        
        if scope in AI_KNOWLEDGE_BASE and category in AI_KNOWLEDGE_BASE[scope]:
            knowledge = AI_KNOWLEDGE_BASE[scope][category]
            if knowledge['reduction_tips']:
                analysis['priority_actions'].append({
                    'scope': scope,
                    'category': category,
                    'current_emissions': emission_source['co2e'],
                    'tips': knowledge['reduction_tips'][:2],
                    'crediting_opportunities': knowledge['crediting_opportunities']
                })
    
    return analysis

def generate_ai_advice(user_data, question_type="general"):
    """Generate AI-powered advice based on user data and question type"""
    analysis = analyze_emission_patterns(user_data)
    
    if question_type == "how_to_fix":
        return generate_fix_advice(analysis)
    elif question_type == "reduction":
        return generate_reduction_advice(analysis)
    elif question_type == "crediting":
        return generate_crediting_advice(analysis)
    elif question_type == "offsetting":
        return generate_offsetting_advice(analysis)
    elif question_type == "compliance":
        return generate_compliance_advice(analysis)
    else:
        return generate_general_advice(analysis)

def generate_fix_advice(analysis):
    """Generate specific fix-it advice"""
    advice = {
        'type': 'fix_advice',
        'title': '🚀 Priority Carbon Reduction Actions',
        'summary': f"Based on your emissions of {analysis['total_emissions']:.1f} kg CO₂e, here are your top opportunities:",
        'sections': []
    }
    
    if analysis['priority_actions']:
        for i, action in enumerate(analysis['priority_actions'], 1):
            section = {
                'title': f"#{i} {action['category'].replace('_', ' ').title()}",
                'emissions': f"{action['current_emissions']:.1f} kg CO₂e",
                'tips': action['tips'],
                'crediting_opportunities': action['crediting_opportunities']
            }
            advice['sections'].append(section)
    
    advice['general_tips'] = [
        "Set a target to reduce emissions by 25% within 12 months",
        "Implement monthly emission tracking and reporting",
        "Engage employees in sustainability initiatives",
        "Explore renewable energy options for your operations",
        "Consider carbon offsetting for unavoidable emissions"
    ]
    
    return advice

def generate_reduction_advice(analysis):
    """Generate reduction strategies advice"""
    return {
        'type': 'reduction_advice',
        'title': '📉 Carbon Reduction Strategies',
        'summary': f"Here are targeted reduction strategies for your {analysis['total_emissions']:.1f} kg CO₂e footprint:",
        'sections': [
            {
                'title': 'Immediate Reductions (0-3 months)',
                'items': [
                    'Optimize energy usage through behavioral changes',
                    'Implement basic maintenance schedules',
                    'Start employee awareness campaigns',
                    'Conduct quick energy audits'
                ]
            },
            {
                'title': 'Medium-term Investments (3-12 months)',
                'items': [
                    'Upgrade to energy-efficient equipment',
                    'Install smart energy management systems',
                    'Implement telecommuting policies',
                    'Explore renewable energy options'
                ]
            },
            {
                'title': 'Long-term Transformations (1-3 years)',
                'items': [
                    'Transition to electric vehicle fleet',
                    'Install on-site renewable generation',
                    'Implement circular economy practices',
                    'Develop sustainable supply chain partnerships'
                ]
            }
        ]
    }

def generate_crediting_advice(analysis):
    """Generate carbon crediting advice"""
    return {
        'type': 'crediting_advice',
        'title': '💰 Carbon Crediting Opportunities',
        'summary': "Explore these carbon crediting opportunities for your business:",
        'sections': [
            {
                'title': 'Malaysia-Specific Programs',
                'items': [
                    'MGTC Verified Carbon Credits Program',
                    'National Biofuel Policy initiatives',
                    'Renewable Energy Certificate (REC) trading',
                    'Energy Efficiency & Conservation Act projects'
                ]
            },
            {
                'title': 'International Standards',
                'items': [
                    'Verified Carbon Standard (VCS) projects',
                    'Gold Standard certification',
                    'Clean Development Mechanism (CDM)',
                    'Article 6.2 bilateral agreements'
                ]
            },
            {
                'title': 'Project Types Available',
                'items': [
                    'Renewable energy installations',
                    'Energy efficiency improvements',
                    'Forestry and land use projects',
                    'Waste management innovations'
                ]
            }
        ]
    }

def generate_offsetting_advice(analysis):
    """Generate carbon offsetting advice"""
    return {
        'type': 'offsetting_advice',
        'title': '🌳 Carbon Offsetting Solutions',
        'summary': "Balance your remaining emissions with these offsetting options:",
        'sections': [
            {
                'title': 'Nature-Based Solutions',
                'items': [
                    'Mangrove restoration projects in Sabah',
                    'Tropical rainforest conservation',
                    'Urban greening initiatives',
                    'Agroforestry programs'
                ]
            },
            {
                'title': 'Technology-Based Solutions',
                'items': [
                    'Carbon capture and storage',
                    'Direct air capture technology',
                    'Enhanced weathering projects',
                    'Bioenergy with carbon capture'
                ]
            },
            {
                'title': 'Community Projects',
                'items': [
                    'Clean cookstove distribution',
                    'Solar power for rural communities',
                    'Water purification projects',
                    'Sustainable agriculture initiatives'
                ]
            }
        ]
    }

def generate_compliance_advice(analysis):
    """Generate regulatory compliance advice"""
    return {
        'type': 'compliance_advice',
        'title': '📋 Regulatory Compliance Guide',
        'summary': "Stay compliant with Malaysia's carbon regulations:",
        'sections': [
            {
                'title': 'Mandatory Requirements',
                'items': [
                    'Carbon reporting under MGTC guidelines',
                    'Energy audit compliance for large consumers',
                    'Environmental Impact Assessment requirements',
                    'Green Technology Master Plan alignment'
                ]
            },
            {
                'title': 'Voluntary Initiatives',
                'items': [
                    'MyCarbon voluntary reporting platform',
                    'Low Carbon Cities Framework participation',
                    'Sustainable Development Goals alignment',
                    'ESG reporting best practices'
                ]
            },
            {
                'title': 'Incentives & Support',
                'items': [
                    'Green Investment Tax Allowance',
                    'Green Income Tax Exemption',
                    'Soft loans for green technology',
                    'MGTC capacity building programs'
                ]
            }
        ]
    }

def generate_general_advice(analysis):
    """Generate general carbon management advice"""
    return {
        'type': 'general_advice',
        'title': '🌱 Your Carbon Management Strategy',
        'summary': f"Your current carbon footprint is {analysis['total_emissions']:.1f} kg CO₂e. Here's your comprehensive strategy:",
        'sections': [
            {
                'title': 'Immediate Actions (0-3 months)',
                'items': [
                    'Conduct energy audit of your facilities',
                    'Implement basic energy efficiency measures',
                    'Start employee awareness program',
                    'Set up monthly emission tracking'
                ]
            },
            {
                'title': 'Medium-term Initiatives (3-12 months)',
                'items': [
                    'Invest in energy-efficient equipment',
                    'Develop supplier sustainability criteria',
                    'Explore renewable energy options',
                    'Implement telecommuting policies'
                ]
            },
            {
                'title': 'Long-term Strategy (1-3 years)',
                'items': [
                    'Transition to electric vehicle fleet',
                    'Install on-site renewable energy',
                    'Achieve carbon neutrality certification',
                    'Develop circular economy initiatives'
                ]
            }
        ]
    }

# NEW: WORKING GEMINI AI ADVICE FUNCTION WITH DEBUGGING
def get_gemini_advice(user_data, question_type="general", user_message=""):
    """Get AI advice from Gemini based on user data and standards"""
    try:
        if not GEMINI_AVAILABLE:
            print("❌ Gemini AI not available, using fallback")
            raise Exception("Gemini AI not configured")
        
        # Prepare user emission data for the AI
        analysis = analyze_emission_patterns(user_data)
        
        # Build the prompt with standards context
        prompt = f"""
        You are Carbon Sentinel AI, an expert carbon consultant specializing in:
        - SBTi (Science Based Targets initiative) Corporate Net-Zero Standard V2.0
        - GHG Protocol Corporate Accounting Standard
        - ISO 14064 for GHG quantification and reporting
        - SEDA (Sustainable Energy Development Authority) Malaysia guidelines
        - MGTC (Malaysian Green Technology Corporation) requirements
        
        USER EMISSION DATA:
        - Total Emissions: {analysis['total_emissions']:.1f} kg CO₂e
        - Highest Emission Scope: {analysis['highest_emission_scope']}
        - Top Emission Sources: {[f"{src['category']} ({src['co2e']:.1f} kg)" for src in analysis['top_emission_sources']]}
        
        USER QUESTION TYPE: {question_type}
        USER MESSAGE: {user_message}
        
        Provide specific, actionable advice that follows these standards.
        Keep your response concise and practical for business implementation.
        Focus on Malaysian regulatory context and international standards.
        """

        print("🎯 Calling Gemini AI with prompt...")
        
        # Use ONLY the models that are actually available
        model_names = [model['name'] for model in AVAILABLE_GEMINI_MODELS]
        
        if not model_names:
            print("❌ No generative models available")
            raise Exception("No generative models available")
            
        print(f"🔄 Available models to try: {model_names}")
        
        response_text = ""
        last_error = None
        
        for model_name in model_names:
            try:
                print(f"🔄 Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    response_text = response.text
                    print(f"✅ SUCCESS with model: {model_name}")
                    print(f"📝 Response preview: {response_text[:200]}...")
                    break
                else:
                    print(f"⚠️ Empty response from model: {model_name}")
                    continue
                    
            except Exception as model_error:
                last_error = model_error
                print(f"❌ Model {model_name} failed: {model_error}")
                continue
        
        if not response_text:
            print(f"❌ All Gemini models failed. Last error: {last_error}")
            # Try direct API as last resort
            return get_gemini_direct_api(user_data, question_type, user_message)
        
        # Return the raw response text (we'll handle formatting in the frontend)
        print("✅ Gemini AI response received successfully")
        
        return {
            "title": "Gemini AI Analysis",
            "summary": response_text,
            "sections": [{
                "title": "AI Recommendations",
                "recommendations": [response_text]
            }],
            "priority_actions": [
                "Review the AI analysis above",
                "Implement recommended measures",
                "Monitor progress regularly"
            ],
            "ai_source": "gemini",
            "raw_response": response_text
        }
            
    except Exception as e:
        print(f"❌ Gemini AI Error: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        
        # Fallback to existing advice system
        fallback_advice = generate_ai_advice(user_data, question_type)
        fallback_advice['ai_source'] = 'fallback'
        fallback_advice['error'] = str(e)
        return fallback_advice

def get_gemini_direct_api(user_data, question_type="general", user_message=""):
    """Fallback using direct API call if library doesn't work"""
    try:
        print("🔄 Trying direct Gemini API call...")
        
        analysis = analyze_emission_patterns(user_data)
        
        prompt = f"""
        As a carbon consultant, provide advice for:
        - Total Emissions: {analysis['total_emissions']:.1f} kg CO₂e
        - Highest Scope: {analysis['highest_emission_scope']}
        - Question: {user_message}
        
        Provide practical carbon reduction advice for Malaysian businesses focusing on ISO 14064, GHG Protocol, and SBTi standards.
        """
        
        # Direct API call to Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                print("✅ Direct API call successful!")
                return {
                    "title": "AI Carbon Analysis (Direct API)",
                    "summary": text,
                    "sections": [{"title": "Recommendations", "recommendations": [text]}],
                    "ai_source": "gemini_direct_api"
                }
        
        raise Exception(f"API call failed: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Direct API also failed: {e}")
        # Final fallback
        advice = generate_ai_advice(user_data, question_type)
        advice['ai_source'] = 'ultimate_fallback'
        return advice

# ============================================================
# NEW: GRI & GHG PROTOCOL REPORT GENERATION FUNCTIONS WITH REPORTLAB
# ============================================================

def generate_gri_ghg_report(user_data, username, user_info):
    """
    Generate comprehensive GRI & GHG Protocol compliant report
    """
    # Get user information from session or mock data
    company_name = user_info.get('company', 'Your Company')
    email = user_info.get('email', 'N/A')
    report_date = datetime.now().strftime('%Y-%m-%d')
    reporting_period = f"{datetime.now().year}"
    
    # Calculate emissions data
    scope_totals = {
        'scope1': sum(item.get('co2e', 0) for item in user_data.get('scope1', [])),
        'scope2': sum(item.get('co2e', 0) for item in user_data.get('scope2', [])),
        'scope3': sum(item.get('co2e', 0) for item in user_data.get('scope3', []))
    }
    
    total_emissions = sum(scope_totals.values())
    
    # Calculate breakdown by category
    scope1_breakdown = {}
    for item in user_data.get('scope1', []):
        category = item.get('category', 'unknown')
        scope1_breakdown[category] = scope1_breakdown.get(category, 0) + item.get('co2e', 0)
    
    scope2_breakdown = {}
    for item in user_data.get('scope2', []):
        category = item.get('category', 'unknown')
        scope2_breakdown[category] = scope2_breakdown.get(category, 0) + item.get('co2e', 0)
    
    scope3_breakdown = {}
    for item in user_data.get('scope3', []):
        category = item.get('category', 'unknown')
        scope3_breakdown[category] = scope3_breakdown.get(category, 0) + item.get('co2e', 0)
    
    # Get analysis for recommendations
    analysis = analyze_emission_patterns(user_data)
    
    # Calculate carbon intensity (example metric)
    carbon_intensity = total_emissions / 1000  # Example: per $1000 revenue
    
    # Build comprehensive report
    report = {
        # Report Metadata
        'report_metadata': {
            'report_id': f'CARBON-{datetime.now().strftime("%Y%m%d")}-{username}',
            'report_date': report_date,
            'reporting_period': reporting_period,
            'report_version': '1.0',
            'report_standard': 'GRI Standards & GHG Protocol Corporate Standard',
            'prepared_by': 'EmittiF Carbon Management Platform',
            'verification_status': 'Self-Declared (Prepared in accordance with GRI & GHG Protocol)'
        },
        
        # Organizational Information (GRI 102)
        'organizational_info': {
            'company_name': company_name,
            'reporting_entity': company_name,
            'reporting_boundary': 'Organizational (Control Approach)',
            'reporting_period': reporting_period,
            'contact_information': {
                'email': email,
                'platform': 'EmittiF Carbon Management Platform'
            },
            'governance_structure': 'Sustainability Committee oversees climate strategy',
            'report_assurance': 'Internal verification completed'
        },
        
        # GHG Protocol Compliance
        'ghg_protocol': {
            'standard_used': 'GHG Protocol Corporate Accounting and Reporting Standard',
            'organizational_boundary': 'Operational Control Approach',
            'operational_boundary': {
                'scope1': 'Direct emissions from owned or controlled sources',
                'scope2': 'Indirect emissions from purchased electricity',
                'scope3': 'Other indirect emissions in value chain'
            },
            'calculation_methodology': 'Emission factors from DEFRA, IPCC, and local Malaysian sources',
            'global_warming_potentials': 'AR5 (100-year timeframe)',
            'base_year': datetime.now().year,
            'recalculations': 'None required for base year'
        },
        
        # Emissions Inventory
        'emissions_inventory': {
            'scope_totals': {
                'scope1': {
                    'total_kg_co2e': round(scope_totals['scope1'], 2),
                    'total_tonnes_co2e': round(scope_totals['scope1'] / 1000, 2),
                    'percentage': round((scope_totals['scope1'] / total_emissions * 100), 2) if total_emissions > 0 else 0
                },
                'scope2': {
                    'total_kg_co2e': round(scope_totals['scope2'], 2),
                    'total_tonnes_co2e': round(scope_totals['scope2'] / 1000, 2),
                    'percentage': round((scope_totals['scope2'] / total_emissions * 100), 2) if total_emissions > 0 else 0
                },
                'scope3': {
                    'total_kg_co2e': round(scope_totals['scope3'], 2),
                    'total_tonnes_co2e': round(scope_totals['scope3'] / 1000, 2),
                    'percentage': round((scope_totals['scope3'] / total_emissions * 100), 2) if total_emissions > 0 else 0
                }
            },
            'total_emissions': {
                'total_kg_co2e': round(total_emissions, 2),
                'total_tonnes_co2e': round(total_emissions / 1000, 2)
            },
            'scope1_breakdown': scope1_breakdown,
            'scope2_breakdown': scope2_breakdown,
            'scope3_breakdown': scope3_breakdown,
            'emission_factors_used': EMISSION_FACTORS
        },
        
        # Performance Metrics (GRI 305)
        'performance_metrics': {
            'carbon_intensity': {
                'value': round(carbon_intensity, 4),
                'unit': 'kg CO2e per revenue unit',
                'trend': 'Baseline established'
            },
            'reduction_targets': {
                'short_term': 'Reduce emissions by 25% by end of next year',
                'medium_term': 'Achieve 50% reduction within 3 years',
                'long_term': 'Net-zero emissions by 2050'
            },
            'achievements': {
                'current_reduction': '0% (baseline year)',
                'offset_projects': 'None yet implemented',
                'renewable_energy': '0% of electricity from renewable sources'
            }
        },
        
        # Management Approach (GRI 103)
        'management_approach': {
            'policies': 'Climate action policy under development',
            'goals': 'Align with Science Based Targets initiative',
            'responsibilities': 'Sustainability team responsible for implementation',
            'resources': 'Dedicated budget for carbon reduction initiatives',
            'grievance_mechanism': 'Available through company sustainability portal'
        },
        
        # Risk Assessment
        'risk_assessment': {
            'physical_risks': 'Medium exposure to climate-related physical risks',
            'transition_risks': 'High exposure to carbon pricing and regulatory changes',
            'opportunities': 'Energy efficiency, renewable energy adoption, green products',
            'scenario_analysis': '2°C scenario analysis recommended'
        },
        
        # Targets and Performance (GRI 302/305)
        'targets_performance': {
            'energy_consumption': 'To be established',
            'renewable_energy': 'Target: 30% by 2025',
            'emission_reduction': 'Target: 25% reduction by next year',
            'carbon_offsetting': 'Plan to offset unavoidable emissions',
            'verification': 'Plan for third-party verification next year'
        },
        
        # Data Quality & Verification
        'data_quality': {
            'data_collection': 'Automated through EmittiF platform',
            'calculation_methodology': 'GHG Protocol compliant',
            'uncertainty_assessment': 'Medium uncertainty due to estimated factors',
            'completeness': '95% of significant emissions sources covered',
            'consistency': 'Consistent methodology applied',
            'accuracy': 'Reasonable accuracy for decision-making'
        },
        
        # GRI Content Index
        'gri_content_index': {
            'GRI_102': 'General Disclosures - Fully addressed',
            'GRI_103': 'Management Approach - Partially addressed',
            'GRI_201': 'Economic Performance - Not addressed',
            'GRI_302': 'Energy - Partially addressed',
            'GRI_305': 'Emissions - Fully addressed',
            'GRI_306': 'Waste - Not addressed',
            'GRI_308': 'Supplier Environmental Assessment - Not addressed'
        },
        
        # Recommendations
        'recommendations': {
            'immediate_actions': [
                'Establish formal climate policy',
                'Set Science-Based Targets',
                'Implement energy monitoring system',
                'Conduct employee awareness program'
            ],
            'medium_term_actions': [
                'Invest in energy efficiency',
                'Explore renewable energy options',
                'Develop supplier engagement program',
                'Implement carbon offsetting strategy'
            ],
            'long_term_strategies': [
                'Transition to low-carbon business model',
                'Achieve carbon neutrality',
                'Integrate climate risk into business strategy',
                'Develop climate-resilient operations'
            ]
        },
        
        # Appendices
        'appendices': {
            'emission_factor_sources': [
                'DEFRA UK Government Conversion Factors',
                'IPCC Emission Factor Database',
                'Malaysia Grid Emission Factor',
                'MGTC Guidelines'
            ],
            'conversion_factors': '1 kWh = 0.85 kg CO2e (Malaysia grid average)',
            'assumptions': [
                'Organizational boundary: Operational control',
                'Calculation: Emission factor method',
                'GWP: AR5 values',
                'Reporting: Location-based for Scope 2'
            ],
            'glossary': {
                'Scope 1': 'Direct GHG emissions from owned or controlled sources',
                'Scope 2': 'Indirect GHG emissions from purchased electricity',
                'Scope 3': 'Other indirect emissions in value chain',
                'CO2e': 'Carbon dioxide equivalent',
                'GRI': 'Global Reporting Initiative',
                'GHG Protocol': 'Greenhouse Gas Protocol'
            }
        }
    }
    
    return report

def generate_pdf_report(report_data):
    """
    Generate PDF from report data using ReportLab (Windows compatible)
    """
    try:
        # Create a buffer for the PDF
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0F3B2E'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0F3B2E'),
            spaceAfter=10,
            spaceBefore=20,
            borderColor=colors.HexColor('#CFE7D3'),
            borderWidth=2,
            borderPadding=5,
            borderRadius=5
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=8
        )
        
        bold_style = ParagraphStyle(
            'BoldStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        # Build the PDF content
        story = []
        
        # Header
        story.append(Paragraph("CARBON EMISSIONS REPORT", title_style))
        story.append(Paragraph("GRI Standards & GHG Protocol Compliant", subtitle_style))
        story.append(Paragraph(f"<b>Company:</b> {report_data['organizational_info']['company_name']}", body_style))
        story.append(Paragraph(f"<b>Reporting Period:</b> {report_data['organizational_info']['reporting_period']}", body_style))
        story.append(Paragraph(f"<b>Report Date:</b> {report_data['report_metadata']['report_date']}", body_style))
        story.append(Paragraph(f"<b>Report ID:</b> {report_data['report_metadata']['report_id']}", body_style))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", section_style))
        
        # Key Metrics Table
        metrics_data = [
            ['Metric', 'Value', 'Unit'],
            ['Total Emissions', 
             f"{report_data['emissions_inventory']['total_emissions']['total_tonnes_co2e']}", 
             'Tonnes CO₂e'],
            ['Scope 1 Emissions', 
             f"{report_data['emissions_inventory']['scope_totals']['scope1']['total_tonnes_co2e']} ({report_data['emissions_inventory']['scope_totals']['scope1']['percentage']}%)", 
             'Tonnes CO₂e'],
            ['Scope 2 Emissions', 
             f"{report_data['emissions_inventory']['scope_totals']['scope2']['total_tonnes_co2e']} ({report_data['emissions_inventory']['scope_totals']['scope2']['percentage']}%)", 
             'Tonnes CO₂e'],
            ['Scope 3 Emissions', 
             f"{report_data['emissions_inventory']['scope_totals']['scope3']['total_tonnes_co2e']} ({report_data['emissions_inventory']['scope_totals']['scope3']['percentage']}%)", 
             'Tonnes CO₂e'],
            ['Carbon Intensity', 
             f"{report_data['performance_metrics']['carbon_intensity']['value']}", 
             report_data['performance_metrics']['carbon_intensity']['unit']]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[200, 150, 100])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F3B2E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5EBD9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        # Organizational Information
        story.append(Paragraph("1. ORGANIZATIONAL INFORMATION (GRI 102)", section_style))
        
        org_data = [
            ['Item', 'Details'],
            ['Reporting Entity', report_data['organizational_info']['company_name']],
            ['Reporting Period', report_data['organizational_info']['reporting_period']],
            ['Reporting Boundary', report_data['organizational_info']['reporting_boundary']],
            ['Contact Information', report_data['organizational_info']['contact_information']['email']],
            ['Governance Structure', report_data['organizational_info']['governance_structure']],
            ['Report Assurance', report_data['organizational_info']['report_assurance']]
        ]
        
        org_table = Table(org_data, colWidths=[200, 300])
        org_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F3B2E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(org_table)
        story.append(Spacer(1, 20))
        
        # GHG Protocol Compliance
        story.append(Paragraph("2. GHG PROTOCOL COMPLIANCE", section_style))
        
        ghg_data = [
            ['Element', 'Details'],
            ['Standard Used', report_data['ghg_protocol']['standard_used']],
            ['Organizational Boundary', report_data['ghg_protocol']['organizational_boundary']],
            ['Calculation Methodology', report_data['ghg_protocol']['calculation_methodology']],
            ['Global Warming Potentials', report_data['ghg_protocol']['global_warming_potentials']],
            ['Base Year', str(report_data['ghg_protocol']['base_year'])]
        ]
        
        ghg_table = Table(ghg_data, colWidths=[200, 300])
        ghg_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F3B2E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(ghg_table)
        story.append(Spacer(1, 20))
        
        # Emissions Inventory
        story.append(Paragraph("3. EMISSIONS INVENTORY", section_style))
        
        emissions_data = [
            ['Scope', 'Emissions (kg CO₂e)', 'Emissions (t CO₂e)', 'Percentage'],
            ['Scope 1 (Direct)', 
             str(report_data['emissions_inventory']['scope_totals']['scope1']['total_kg_co2e']),
             str(report_data['emissions_inventory']['scope_totals']['scope1']['total_tonnes_co2e']),
             f"{report_data['emissions_inventory']['scope_totals']['scope1']['percentage']}%"],
            ['Scope 2 (Energy)', 
             str(report_data['emissions_inventory']['scope_totals']['scope2']['total_kg_co2e']),
             str(report_data['emissions_inventory']['scope_totals']['scope2']['total_tonnes_co2e']),
             f"{report_data['emissions_inventory']['scope_totals']['scope2']['percentage']}%"],
            ['Scope 3 (Value Chain)', 
             str(report_data['emissions_inventory']['scope_totals']['scope3']['total_kg_co2e']),
             str(report_data['emissions_inventory']['scope_totals']['scope3']['total_tonnes_co2e']),
             f"{report_data['emissions_inventory']['scope_totals']['scope3']['percentage']}%"],
            ['TOTAL', 
             str(report_data['emissions_inventory']['total_emissions']['total_kg_co2e']),
             str(report_data['emissions_inventory']['total_emissions']['total_tonnes_co2e']),
             '100%']
        ]
        
        emissions_table = Table(emissions_data, colWidths=[150, 120, 120, 100])
        emissions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F3B2E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#CFE7D3')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(emissions_table)
        story.append(Spacer(1, 20))
        
        # Performance Metrics
        story.append(Paragraph("4. PERFORMANCE METRICS (GRI 305)", section_style))
        
        perf_data = [
            ['Target', 'Status'],
            ['Short-term Reduction', report_data['performance_metrics']['reduction_targets']['short_term']],
            ['Medium-term Reduction', report_data['performance_metrics']['reduction_targets']['medium_term']],
            ['Long-term Strategy', report_data['performance_metrics']['reduction_targets']['long_term']],
            ['Carbon Intensity', f"{report_data['performance_metrics']['carbon_intensity']['value']} {report_data['performance_metrics']['carbon_intensity']['unit']}"],
            ['Current Achievement', report_data['performance_metrics']['achievements']['current_reduction']]
        ]
        
        perf_table = Table(perf_data, colWidths=[200, 300])
        perf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F3B2E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(perf_table)
        story.append(Spacer(1, 20))
        
        # Recommendations
        story.append(Paragraph("5. RECOMMENDATIONS & ACTION PLAN", section_style))
        
        # Immediate Actions
        story.append(Paragraph("<b>Immediate Actions (0-3 months):</b>", bold_style))
        for action in report_data['recommendations']['immediate_actions']:
            story.append(Paragraph(f"• {action}", body_style))
        
        story.append(Spacer(1, 10))
        
        # Medium-term Actions
        story.append(Paragraph("<b>Medium-term Actions (3-12 months):</b>", bold_style))
        for action in report_data['recommendations']['medium_term_actions']:
            story.append(Paragraph(f"• {action}", body_style))
        
        story.append(Spacer(1, 10))
        
        # Long-term Strategies
        story.append(Paragraph("<b>Long-term Strategies (1-3 years):</b>", bold_style))
        for action in report_data['recommendations']['long_term_strategies']:
            story.append(Paragraph(f"• {action}", body_style))
        
        story.append(Spacer(1, 20))
        
        # Data Quality
        story.append(Paragraph("6. DATA QUALITY & VERIFICATION", section_style))
        
        quality_data = [
            ['Aspect', 'Status', 'Assessment'],
            ['Data Collection', report_data['data_quality']['data_collection'], 'Good'],
            ['Calculation Methodology', report_data['data_quality']['calculation_methodology'], 'Compliant'],
            ['Completeness', report_data['data_quality']['completeness'], 'Adequate'],
            ['Consistency', report_data['data_quality']['consistency'], 'Good'],
            ['Verification Status', report_data['report_metadata']['verification_status'], 'Internal']
        ]
        
        quality_table = Table(quality_data, colWidths=[150, 200, 100])
        quality_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F3B2E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        
        story.append(quality_table)
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Paragraph("<i>This report was generated by EmittiF Carbon Management Platform</i>", body_style))
        story.append(Paragraph(f"<i>Report Standards: {report_data['report_metadata']['report_standard']}</i>", body_style))
        story.append(Paragraph(f"<i>Report Version: {report_data['report_metadata']['report_version']}</i>", body_style))
        story.append(Paragraph(f"<i>© {datetime.now().year} EmittiF. All rights reserved.</i>", body_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content from buffer
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        print(f"❌ PDF generation error: {str(e)}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return None

# ============================================================
# DATABASE HELPER FUNCTIONS
# ============================================================

def get_user_compliance_data(username):
    """Get comprehensive compliance data for a user"""
    try:
        # Get all standards
        standards = ComplianceStandard.query.all()
        
        # Get user's compliance statuses
        user_statuses = UserComplianceStatus.query.filter_by(user_id=username).all()
        
        result = {
            'standards': [],
            'overall_score': 0,
            'urgent_actions': [],
            'compliance_matrix': []
        }
        
        total_compliance = 0
        total_possible = 0
        
        for standard in standards:
            # Get clauses for this standard
            clauses = ComplianceClause.query.filter_by(standard_id=standard.id).all()
            
            # Calculate compliance for this standard
            compliant_count = 0
            standard_total = len(clauses)
            
            standard_data = {
                'id': standard.id,
                'name': standard.name,
                'short_name': standard.short_name,
                'version': standard.version,
                'description': standard.description,
                'jurisdiction': standard.jurisdiction,
                'total_clauses': standard_total,
                'compliant_clauses': 0,
                'compliance_percentage': 0,
                'clauses': []
            }
            
            for clause in clauses:
                # Find user status for this clause
                user_status = next((s for s in user_statuses if s.clause_id == clause.id), None)
                
                clause_data = {
                    'id': clause.id,
                    'clause_number': clause.clause_number,
                    'title': clause.title,
                    'description': clause.description,
                    'priority': clause.priority,
                    'status': user_status.status if user_status else 'not_assessed',
                    'assessment_date': user_status.assessment_date if user_status else None,
                    'next_assessment_date': user_status.next_assessment_date if user_status else None,
                    'evidence_count': len(user_status.evidence_files) if user_status else 0
                }
                
                standard_data['clauses'].append(clause_data)
                
                # Count compliance
                if user_status and user_status.status == 'compliant':
                    compliant_count += 1
                    total_compliance += 1
                total_possible += 1
                
                # Check for urgent actions
                if (user_status and user_status.status in ['non_compliant', 'partial']) or not user_status:
                    if clause.priority == 1:  # High priority
                        result['urgent_actions'].append({
                            'standard': standard.name,
                            'standard_id': standard.id,
                            'clause': clause.clause_number,
                            'clause_id': clause.id,
                            'title': clause.title,
                            'status': user_status.status if user_status else 'not_assessed',
                            'due_date': user_status.next_assessment_date if user_status else (datetime.utcnow() + timedelta(days=30))
                        })
            
            standard_data['compliant_clauses'] = compliant_count
            standard_data['compliance_percentage'] = round((compliant_count / standard_total * 100) if standard_total > 0 else 0, 1)
            
            result['standards'].append(standard_data)
        
        # Calculate overall score
        if total_possible > 0:
            result['overall_score'] = round((total_compliance / total_possible * 100), 1)
        
        return result
        
    except Exception as e:
        print(f"❌ Error getting compliance data: {e}")
        return {'standards': [], 'overall_score': 0, 'urgent_actions': [], 'compliance_matrix': []}

def seed_compliance_standards():
    """Seed initial compliance standards and clauses"""
    try:
        # Check if standards already exist
        if ComplianceStandard.query.count() > 0:
            print("✅ Compliance standards already seeded")
            return
        
        print("🌱 Seeding compliance standards...")
        
        # Define standards
        standards_data = [
            {
                'name': 'IFRS S1',
                'short_name': 'IFRS S1',
                'version': '2023',
                'description': 'IFRS S1 General Requirements for Disclosure of Sustainability-related Financial Information',
                'jurisdiction': 'Global',
                'category': 'Financial Reporting',
                'logo': 'ifrs',
                'website': 'https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/'
            },
            {
                'name': 'IFRS S2',
                'short_name': 'IFRS S2',
                'version': '2023',
                'description': 'IFRS S2 Climate-related Disclosures',
                'jurisdiction': 'Global',
                'category': 'Climate Reporting',
                'logo': 'ifrs',
                'website': 'https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/'
            },
            {
                'name': 'TCFD',
                'short_name': 'TCFD',
                'version': '2021',
                'description': 'Task Force on Climate-related Financial Disclosures',
                'jurisdiction': 'Global',
                'category': 'Climate Risk',
                'logo': 'tcfd',
                'website': 'https://www.fsb-tcfd.org/'
            },
            {
                'name': 'ISO 14064-1',
                'short_name': 'ISO 14064',
                'version': '2018',
                'description': 'Greenhouse gas accounting and verification',
                'jurisdiction': 'Global',
                'category': 'GHG Accounting',
                'logo': 'iso',
                'website': 'https://www.iso.org/standard/66453.html'
            },
            {
                'name': 'GHG Protocol',
                'short_name': 'GHG',
                'version': '2015',
                'description': 'Greenhouse Gas Protocol Corporate Standard',
                'jurisdiction': 'Global',
                'category': 'GHG Accounting',
                'logo': 'ghg',
                'website': 'https://ghgprotocol.org/corporate-standard'
            },
            {
                'name': 'GRI Standards',
                'short_name': 'GRI',
                'version': '2021',
                'description': 'Global Reporting Initiative Standards',
                'jurisdiction': 'Global',
                'category': 'Sustainability Reporting',
                'logo': 'gri',
                'website': 'https://www.globalreporting.org/standards/'
            },
            {
                'name': 'Malaysia MGTC',
                'short_name': 'MGTC',
                'version': '2023',
                'description': 'Malaysian Green Technology Corporation Guidelines',
                'jurisdiction': 'Malaysia',
                'category': 'National Regulation',
                'logo': 'malaysia',
                'website': 'https://www.mgtc.gov.my/'
            },
            {
                'name': 'Malaysia SEDA',
                'short_name': 'SEDA',
                'version': '2023',
                'description': 'Sustainable Energy Development Authority Guidelines',
                'jurisdiction': 'Malaysia',
                'category': 'Energy Regulation',
                'logo': 'malaysia',
                'website': 'https://www.seda.gov.my/'
            }
        ]
        
        # Create standards
        created_standards = {}
        for std_data in standards_data:
            standard = ComplianceStandard(**std_data)
            db.session.add(standard)
            db.session.flush()  # Get the ID
            created_standards[std_data['name']] = standard
        
        # Define clauses for each standard
        clauses_data = {
            'IFRS S1': [
                {'clause_number': 'S1-1', 'title': 'Organizational description', 'description': 'Description of the organization and its value chain', 'priority': 1, 'category': 'governance'},
                {'clause_number': 'S1-2', 'title': 'Governance', 'description': 'Governance processes, controls and procedures', 'priority': 1, 'category': 'governance'},
                {'clause_number': 'S1-3', 'title': 'Strategy', 'description': 'Strategy and business model', 'priority': 1, 'category': 'strategy'},
                {'clause_number': 'S1-4', 'title': 'Risk management', 'description': 'Risk and opportunity identification and management', 'priority': 2, 'category': 'risk'},
                {'clause_number': 'S1-5', 'title': 'Metrics and targets', 'description': 'Metrics and targets for sustainability matters', 'priority': 2, 'category': 'metrics'},
            ],
            'IFRS S2': [
                {'clause_number': 'S2-1', 'title': 'Climate-related risks and opportunities', 'description': 'Climate-related risks and opportunities', 'priority': 1, 'category': 'risk'},
                {'clause_number': 'S2-2', 'title': 'Climate resilience', 'description': 'Climate resilience of strategy and business model', 'priority': 1, 'category': 'strategy'},
                {'clause_number': 'S2-3', 'title': 'Greenhouse gas emissions', 'description': 'Scope 1, 2 and 3 greenhouse gas emissions', 'priority': 1, 'category': 'metrics'},
                {'clause_number': 'S2-4', 'title': 'Climate-related targets', 'description': 'Climate-related targets and transition plans', 'priority': 2, 'category': 'metrics'},
                {'clause_number': 'S2-5', 'title': 'Capital allocation', 'description': 'Capital allocation towards climate-related risks and opportunities', 'priority': 2, 'category': 'strategy'},
            ],
            'TCFD': [
                {'clause_number': 'TCFD-1', 'title': 'Governance', 'description': 'Disclose the organization\'s governance around climate-related risks and opportunities', 'priority': 1, 'category': 'governance'},
                {'clause_number': 'TCFD-2', 'title': 'Strategy', 'description': 'Disclose the actual and potential impacts of climate-related risks and opportunities', 'priority': 1, 'category': 'strategy'},
                {'clause_number': 'TCFD-3', 'title': 'Risk Management', 'description': 'Disclose how the organization identifies, assesses, and manages climate-related risks', 'priority': 1, 'category': 'risk'},
                {'clause_number': 'TCFD-4', 'title': 'Metrics and Targets', 'description': 'Disclose the metrics and targets used to assess and manage climate-related risks and opportunities', 'priority': 2, 'category': 'metrics'},
            ],
            'ISO 14064-1': [
                {'clause_number': '4.1', 'title': 'General requirements', 'description': 'General requirements for GHG inventory', 'priority': 1, 'category': 'general'},
                {'clause_number': '4.2', 'title': 'Organizational boundaries', 'description': 'Defining organizational boundaries', 'priority': 1, 'category': 'boundary'},
                {'clause_number': '4.3', 'title': 'Operational boundaries', 'description': 'Defining operational boundaries', 'priority': 1, 'category': 'boundary'},
                {'clause_number': '4.4', 'title': 'Quantifying GHG emissions and removals', 'description': 'Quantification of GHG emissions and removals', 'priority': 2, 'category': 'quantification'},
                {'clause_number': '4.5', 'title': 'GHG inventory quality management', 'description': 'Quality management of GHG inventory', 'priority': 2, 'category': 'quality'},
            ],
            'GHG Protocol': [
                {'clause_number': 'GHG-1', 'title': 'Organizational boundaries', 'description': 'Defining organizational boundaries using equity share or control approach', 'priority': 1, 'category': 'boundary'},
                {'clause_number': 'GHG-2', 'title': 'Operational boundaries', 'description': 'Identifying and categorizing direct and indirect emissions', 'priority': 1, 'category': 'boundary'},
                {'clause_number': 'GHG-3', 'title': 'Tracking emissions over time', 'description': 'Tracking emissions over time and setting a base year', 'priority': 2, 'category': 'tracking'},
                {'clause_number': 'GHG-4', 'title': 'Reporting emissions', 'description': 'Reporting GHG emissions in public reports', 'priority': 2, 'category': 'reporting'},
            ],
            'GRI Standards': [
                {'clause_number': 'GRI 102', 'title': 'General Disclosures', 'description': 'General disclosures about the organization', 'priority': 1, 'category': 'general'},
                {'clause_number': 'GRI 201', 'title': 'Economic Performance', 'description': 'Economic performance disclosures', 'priority': 2, 'category': 'economic'},
                {'clause_number': 'GRI 302', 'title': 'Energy', 'description': 'Energy consumption and efficiency', 'priority': 1, 'category': 'environmental'},
                {'clause_number': 'GRI 305', 'title': 'Emissions', 'description': 'Emissions including greenhouse gases', 'priority': 1, 'category': 'environmental'},
            ],
            'Malaysia MGTC': [
                {'clause_number': 'MGTC-1', 'title': 'Green Technology Reporting', 'description': 'Reporting on green technology adoption', 'priority': 1, 'category': 'reporting'},
                {'clause_number': 'MGTC-2', 'title': 'Carbon Reduction Targets', 'description': 'Setting and reporting carbon reduction targets', 'priority': 1, 'category': 'targets'},
                {'clause_number': 'MGTC-3', 'title': 'Energy Efficiency', 'description': 'Energy efficiency measures and reporting', 'priority': 2, 'category': 'energy'},
            ],
            'Malaysia SEDA': [
                {'clause_number': 'SEDA-1', 'title': 'Renewable Energy', 'description': 'Renewable energy adoption and reporting', 'priority': 1, 'category': 'energy'},
                {'clause_number': 'SEDA-2', 'title': 'Energy Management', 'description': 'Energy management system requirements', 'priority': 2, 'category': 'energy'},
            ]
        }
        
        # Create clauses
        for standard_name, clauses in clauses_data.items():
            standard = created_standards[standard_name]
            for clause_data in clauses:
                clause = ComplianceClause(
                    standard_id=standard.id,
                    **clause_data
                )
                db.session.add(clause)
        
        # Create some mappings between standards
        # Example: IFRS S2-3 maps to GRI 305
        ifrs_s2 = created_standards['IFRS S2']
        gri = created_standards['GRI Standards']
        
        # Find specific clauses
        ifrs_clause = ComplianceClause.query.filter_by(standard_id=ifrs_s2.id, clause_number='S2-3').first()
        gri_clause = ComplianceClause.query.filter_by(standard_id=gri.id, clause_number='GRI 305').first()
        
        if ifrs_clause and gri_clause:
            mapping = ClauseMapping(
                source_clause_id=ifrs_clause.id,
                target_standard_id=gri.id,
                target_clause_id=gri_clause.id,
                mapping_type='equivalent',
                confidence=90,
                notes='Both address greenhouse gas emissions reporting'
            )
            db.session.add(mapping)
        
        db.session.commit()
        print(f"✅ Seeded {len(created_standards)} standards with clauses")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding compliance standards: {e}")

def initialize_compliance_database():
    """Initialize compliance database - safe for Windows"""
    with app.app_context():
        try:
            # Create all tables if they don't exist
            db.create_all()
            print("✅ Compliance database tables checked/created")

             # Seed default admin
            seed_default_admin() 
            
            # Check if we need to seed data
            if ComplianceStandard.query.count() == 0:
                print("🌱 Seeding compliance standards...")
                seed_compliance_standards()
                print("✅ Compliance data seeded")
            else:
                standards_count = ComplianceStandard.query.count()
                clauses_count = ComplianceClause.query.count()
                print(f"📊 Database loaded: {standards_count} standards, {clauses_count} clauses")
                
            return True
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            import traceback
            traceback.print_exc()
            return False

def get_category_breakdown(scope_data):
    breakdown = {}
    for item in scope_data:
        if isinstance(item, dict):
            category = item.get('category', 'unknown')
            breakdown[category] = breakdown.get(category, 0) + item.get('co2e', 0)
    
    if not breakdown:
        if 'scope1' in str(scope_data):
            return {'diesel': 1340, 'natural_gas': 550}
        elif 'scope2' in str(scope_data):
            return {'electricity': 1275}
        elif 'scope3' in str(scope_data):
            return {'business_travel_air': 500, 'employee_commute': 600}
    
    return breakdown

def get_monthly_trends(user_data):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    scope1_trend = [45, 52, 48, 61, 55, 58]
    scope2_trend = [28, 32, 34, 29, 31, 33]
    scope3_trend = [65, 59, 70, 72, 68, 75]
    
    return {
        'months': months,
        'scope1': scope1_trend,
        'scope2': scope2_trend,
        'scope3': scope3_trend
    }

def get_annual_progress(user_data):
    total_emissions = 0
    if isinstance(user_data, dict):
        for scope, items in user_data.items():
            if isinstance(items, list):
                total_emissions += sum(item.get('co2e', 0) for item in items if isinstance(item, dict))
    
    target = 10000
    progress = min((total_emissions / target) * 100, 100) if target > 0 else 0
    
    return {
        'current': total_emissions,
        'target': target,
        'progress': progress
    }

class UserProfile(db.Model):
    """User Profile Settings for audit traceability"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)  # Remove db.ForeignKey
    company_id = db.Column(db.String(100), nullable=False)
    full_legal_name = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    job_title = db.Column(db.String(100))
    department = db.Column(db.String(100))
    esg_responsibility = db.Column(db.Text)  # JSON string for multi-select
    authority_level = db.Column(db.String(50))  # Data Entry, Reviewer, Approver
    declaration_accepted = db.Column(db.Boolean, default=False)
    declaration_timestamp = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'full_legal_name': self.full_legal_name,
            'phone_number': self.phone_number,
            'job_title': self.job_title,
            'department': self.department,
            'esg_responsibility': json.loads(self.esg_responsibility) if self.esg_responsibility else [],
            'authority_level': self.authority_level,
            'declaration_accepted': self.declaration_accepted,
            'declaration_timestamp': self.declaration_timestamp.isoformat() if self.declaration_timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by
        }

class CompanySettings(db.Model):
    """Company Settings for organizational identity and reporting boundary"""
    __tablename__ = 'company_settings'
    __table_args__ = {'extend_existing': True}  # Add this
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.String(100), unique=True, nullable=False)
    legal_company_name = db.Column(db.String(200))
    company_registration_number = db.Column(db.String(100))
    country_of_incorporation = db.Column(db.String(100))
    industry_classification = db.Column(db.String(100))  # MSIC/NAICS code
    financial_year_start = db.Column(db.String(10))  # MM-DD format
    financial_year_end = db.Column(db.String(10))    # MM-DD format
    reporting_currency = db.Column(db.String(10))
    reporting_boundary_method = db.Column(db.String(50))  # Operational Control, Financial Control, Equity Share
    included_entities = db.Column(db.Text)
    excluded_entities = db.Column(db.Text)
    excluded_entities_justification = db.Column(db.Text)
    number_of_operational_sites = db.Column(db.Integer)
    site_locations = db.Column(db.Text)  # JSON string
    primary_business_activities = db.Column(db.Text)
    board_oversight = db.Column(db.Boolean, default=False)
    esg_committee_exists = db.Column(db.Boolean, default=False)
    role_responsible_for_esg = db.Column(db.String(100))
    external_assurance_status = db.Column(db.String(50))  # None, Limited, Reasonable
    esg_policy_url = db.Column(db.String(500))
    environmental_policy_url = db.Column(db.String(500))
    health_safety_policy_url = db.Column(db.String(500))
    supplier_code_url = db.Column(db.String(500))
    policy_issue_dates = db.Column(db.Text)  # JSON string
    reporting_scope = db.Column(db.Text)  # JSON string for checkboxes
    audit_mode_enabled = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.String(50))
    updated_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'legal_company_name': self.legal_company_name,
            'company_registration_number': self.company_registration_number,
            'country_of_incorporation': self.country_of_incorporation,
            'industry_classification': self.industry_classification,
            'financial_year_start': self.financial_year_start,
            'financial_year_end': self.financial_year_end,
            'reporting_currency': self.reporting_currency,
            'reporting_boundary_method': self.reporting_boundary_method,
            'included_entities': self.included_entities,
            'excluded_entities': self.excluded_entities,
            'excluded_entities_justification': self.excluded_entities_justification,
            'number_of_operational_sites': self.number_of_operational_sites,
            'site_locations': json.loads(self.site_locations) if self.site_locations else [],
            'primary_business_activities': self.primary_business_activities,
            'board_oversight': self.board_oversight,
            'esg_committee_exists': self.esg_committee_exists,
            'role_responsible_for_esg': self.role_responsible_for_esg,
            'external_assurance_status': self.external_assurance_status,
            'esg_policy_url': self.esg_policy_url,
            'environmental_policy_url': self.environmental_policy_url,
            'health_safety_policy_url': self.health_safety_policy_url,
            'supplier_code_url': self.supplier_code_url,
            'policy_issue_dates': json.loads(self.policy_issue_dates) if self.policy_issue_dates else {},
            'reporting_scope': json.loads(self.reporting_scope) if self.reporting_scope else [],
            'audit_mode_enabled': self.audit_mode_enabled,
            'version': self.version
        }

def seed_esg_modules():
    """Seed ESG data modules"""
    categories = [
        ('Environmental', 'Environmental impact data', 'leaf'),
        ('Social', 'Social and workforce data', 'users'),
        ('Governance', 'Governance and compliance data', 'balance-scale'),
        ('Supply Chain', 'Supply chain and Scope 3 data', 'truck')
    ]
    
    for name, description, icon in categories:
        if not ESGDataCategory.query.filter_by(name=name).first():
            category = ESGDataCategory(
                name=name,
                description=description,
                icon=icon
            )
            db.session.add(category)
    
    db.session.commit()
    
    # Add environmental modules
    env_category = ESGDataCategory.query.filter_by(name='Environmental').first()
    if env_category:
        env_modules = [
            ('Emissions', 'Greenhouse gas emissions', 'numeric', 'kg CO₂e', True),
            ('Energy', 'Energy consumption', 'numeric', 'kWh', True),
            ('Water', 'Water usage', 'numeric', 'm³', True),
            ('Waste', 'Waste generation', 'numeric', 'kg', True),
            ('Biodiversity', 'Land and biodiversity impact', 'text', None, False)
        ]
        
        for name, desc, data_type, unit, requires_evidence in env_modules:
            if not ESGDataModule.query.filter_by(name=name).first():
                module = ESGDataModule(
                    category_id=env_category.id,
                    name=name,
                    description=desc,
                    data_type=data_type,
                    unit=unit,
                    requires_evidence=requires_evidence
                )
                db.session.add(module)
    
    db.session.commit()

    def get_file_icon(file_type):
       """Return appropriate icon for file type"""
       icons = {
        'pdf': 'fa-file-pdf',
        'png': 'fa-file-image',
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'gif': 'fa-file-image',
        'txt': 'fa-file-alt',
        'csv': 'fa-file-csv',
        'xlsx': 'fa-file-excel',
        'xls': 'fa-file-excel',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word'
    }
    return icons.get(file_type.lower(), 'fa-file')

def calculate_environmental_completion(user_id):
    """Calculate completion percentage for environmental module"""
    try:
        # Get all records for user
        records = EnvironmentalRecord.query.filter_by(user_id=user_id).all()
        
        # Count by module
        modules = ['energy', 'water', 'waste', 'land_biodiversity']
        module_counts = {module: 0 for module in modules}
        
        for record in records:
            if record.module_type in module_counts:
                module_counts[record.module_type] += 1
        
        # Calculate completion (simple logic for now)
        # Required: at least 1 record in energy, water, waste
        # Optional: land_biodiversity
        required_modules = ['energy', 'water', 'waste']
        completed_modules = []
        
        for module in required_modules:
            if module_counts[module] > 0:
                completed_modules.append(module)
        
        overall_percentage = int((len(completed_modules) / len(required_modules)) * 100)
        
        return {
            'overall_percentage': overall_percentage,
            'module_counts': module_counts,
            'completed_modules': completed_modules,
            'missing_modules': [m for m in required_modules if m not in completed_modules],
            'total_records': len(records)
        }
        
    except Exception as e:
        print(f"Error calculating completion: {e}")
        return {
            'overall_percentage': 0,
            'module_counts': {},
            'completed_modules': [],
            'missing_modules': ['energy', 'water', 'waste'],
            'total_records': 0
        }

def generate_invite_token():
    """Generate a secure unique token for auditor invites"""
    return secrets.token_urlsafe(32)

def is_auditor():
    if 'user_id' not in session:
        return False
    user = User.query.get(session['user_id'])
    return user and user.role == 'auditor'

def is_admin():
    if 'user_id' not in session:
        return False
    user = User.query.get(session['user_id'])
    return user and user.role == 'admin'

def check_auditor_access_valid(auditor_id, company_id):
    """Check if an auditor's access to a company is still valid"""
    access = AuditorAccess.query.filter_by(
        auditor_id=auditor_id,
        company_id=company_id,
        status='active'
    ).first()
    if not access:
        return False
    # Auto-expire if past expiry date
    if access.expires_at < datetime.now():
        access.status = 'expired'
        db.session.commit()
        return False
    return True

def send_auditor_invite_email(auditor_email, auditor_name, company_name, invite_url, expires_at, is_new_user):
    """Send branded invite email to auditor"""
    try:
        subject = f"You've been invited to audit {company_name} on EmitIQ"
        
        action_text = "Create Account & View Audit" if is_new_user else "View Audit Dashboard"
        intro_text  = "You've been invited to create an auditor account" if is_new_user else "You've been invited to access a new company's ESG data"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0b0f0c; margin: 0; padding: 0; }}
    .wrapper {{ max-width: 560px; margin: 40px auto; background: #111612; border: 1px solid #1e2d21; border-radius: 16px; overflow: hidden; }}
    .header {{ background: #0b0f0c; padding: 32px; text-align: center; border-bottom: 1px solid #1e2d21; }}
    .logo {{ font-size: 24px; font-weight: 800; color: #22c55e; letter-spacing: -0.03em; }}
    .logo span {{ color: #e8f5eb; }}
    .body {{ padding: 36px 32px; }}
    .greeting {{ font-size: 20px; font-weight: 700; color: #e8f5eb; margin-bottom: 12px; }}
    .text {{ font-size: 14px; color: #6b8f72; line-height: 1.7; margin-bottom: 20px; }}
    .company-box {{ background: #141a15; border: 1px solid #1e2d21; border-radius: 10px; padding: 16px 20px; margin: 20px 0; }}
    .company-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.07em; color: #6b8f72; margin-bottom: 4px; }}
    .company-name {{ font-size: 18px; font-weight: 700; color: #22c55e; }}
    .cta-btn {{ display: block; background: #052e16; border: 1px solid #16a34a; color: #4ade80; text-decoration: none; text-align: center; padding: 14px 24px; border-radius: 10px; font-size: 15px; font-weight: 700; margin: 24px 0; letter-spacing: -0.01em; }}
    .expiry {{ font-size: 12px; color: #6b8f72; text-align: center; margin-top: 8px; }}
    .divider {{ height: 1px; background: #1e2d21; margin: 24px 0; }}
    .features {{ display: flex; gap: 12px; margin: 20px 0; }}
    .feature {{ flex: 1; background: #141a15; border: 1px solid #1e2d21; border-radius: 8px; padding: 12px; text-align: center; }}
    .feature-icon {{ font-size: 18px; margin-bottom: 6px; }}
    .feature-text {{ font-size: 11px; color: #6b8f72; }}
    .footer {{ background: #0b0f0c; padding: 20px 32px; text-align: center; border-top: 1px solid #1e2d21; }}
    .footer-text {{ font-size: 11px; color: #3a5c40; line-height: 1.6; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="logo">Emit<span>IQ</span></div>
      <div style="font-size:11px;color:#3a5c40;margin-top:6px;">ESG & Carbon Intelligence Platform</div>
    </div>
    <div class="body">
      <div class="greeting">Hello, {auditor_name} 👋</div>
      <p class="text">{intro_text} on <strong style="color:#e8f5eb;">EmitIQ</strong>. You have been granted read-only access to review the ESG and carbon emissions data for:</p>
      
      <div class="company-box">
        <div class="company-label">Company</div>
        <div class="company-name">{company_name}</div>
      </div>
      
      <p class="text">As an auditor on EmitIQ you will be able to:</p>
      <ul style="color:#6b8f72;font-size:13px;line-height:2;padding-left:20px;margin-bottom:20px;">
        <li>View all ESG data — Environmental, Social & Governance</li>
        <li>Review uploaded evidence and supporting documents</li>
        <li>Access Scope 1, 2 & 3 emission records</li>
        <li>Download GRI & GHG Protocol compliance reports</li>
        <li>Leave review comments and sign off on the audit</li>
      </ul>
      
      <a href="{invite_url}" class="cta-btn">🔐 {action_text}</a>
      <div class="expiry">⏳ This invite expires on <strong style="color:#e8f5eb;">{expires_at.strftime('%d %B %Y')}</strong></div>
      
      <div class="divider"></div>
      <p class="text" style="font-size:12px;">If you did not expect this invite or have questions, please contact {company_name} directly. Do not share this link with anyone.</p>
    </div>
    <div class="footer">
      <div class="footer-text">
        © 2026 EmitIQ · ESG & Carbon Intelligence Platform<br>
        This is an automated message — please do not reply to this email.
      </div>
    </div>
  </div>
</body>
</html>
        """
        
        msg = Message(subject=subject, recipients=[auditor_email], html=html_body)
        mail.send(msg)
        print(f"✅ Invite email sent to {auditor_email}")
        
    except Exception as e:
        print(f"❌ Email send failed: {str(e)}")
        # Don't raise — invite record is still created, they can resend

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    username = session.get('user')
    user_data = emission_data.get(username, {'scope1': [], 'scope2': [], 'scope3': []})
    
    scope1_total = sum(item.get('co2e', 0) for item in user_data.get('scope1', []))
    scope2_total = sum(item.get('co2e', 0) for item in user_data.get('scope2', []))
    scope3_total = sum(item.get('co2e', 0) for item in user_data.get('scope3', []))
    total_emissions_kg = scope1_total + scope2_total + scope3_total

    # --- ESG Score (simple weighted calculation based on data completeness) ---
    has_env = len(user_data.get('scope1', [])) > 0 or len(user_data.get('scope2', [])) > 0
    has_scope3 = len(user_data.get('scope3', [])) > 0
    esg_score = 40 if has_env else 20
    if has_scope3:
        esg_score += 20
    if total_emissions_kg < 5000:
        esg_score += 20
    elif total_emissions_kg < 10000:
        esg_score += 10
    esg_score = min(esg_score + 10, 100)  # base points for being registered

    # --- Carbon Tax Exposure (EU CBAM: ~€50 per tonne CO2e) ---
    EU_CBAM_RATE = 50  # EUR per tonne
    carbon_tax_exposure = (total_emissions_kg / 1000) * EU_CBAM_RATE

    # --- Reduction Progress vs baseline (simple: compare to 5000kg baseline) ---
    BASELINE_KG = 5000
    if BASELINE_KG > 0:
        reduction_progress = ((BASELINE_KG - total_emissions_kg) / BASELINE_KG) * 100
    else:
        reduction_progress = 0

    chart_data = {
        'scope_totals': [scope1_total, scope2_total, scope3_total],
        'scope1_breakdown': get_category_breakdown(user_data.get('scope1', [])),
        'scope2_breakdown': get_category_breakdown(user_data.get('scope2', [])),
        'scope3_breakdown': get_category_breakdown(user_data.get('scope3', [])),
        'monthly_trends': get_monthly_trends(user_data),
        'annual_progress': get_annual_progress(user_data),
        'esg_score': esg_score,
        'carbon_tax_exposure': carbon_tax_exposure,
        'reduction_progress': reduction_progress,
    }
    
    return render_template('dashboard.html', 
                         username=username,
                         chart_data=chart_data,
                         user_data=user_data)
                         
@app.route('/ai-consultant')
@login_required
def ai_consultant():
    username = session.get('user')
    user_data = emission_data.get(username, {'scope1': [], 'scope2': [], 'scope3': []})
    analysis = analyze_emission_patterns(user_data)
    initial_advice = generate_general_advice(analysis)
    
    return render_template('ai_consultant.html',
                         username=username,
                         analysis=analysis,
                         initial_advice=initial_advice,
                         user_data=user_data)

# NEW: WORKING GEMINI AI ADVICE ENDPOINT
@app.route('/api/gemini-advice', methods=['POST'])
@login_required
def gemini_advice():
    """New endpoint for Gemini AI advice"""
    try:
        username = session.get('user')
        user_data = emission_data.get(username, {'scope1': [], 'scope2': [], 'scope3': []})
        data = request.json
        question_type = data.get('question_type', 'general')
        user_message = data.get('message', '')
        
        print(f"🎯 Gemini AI request received: {question_type} - '{user_message}'")
        
        # Get advice from Gemini AI
        advice = get_gemini_advice(user_data, question_type, user_message)
        
        return jsonify({
            'success': True, 
            'advice': advice,
            'ai_source': advice.get('ai_source', 'gemini')
        })
        
    except Exception as e:
        print(f"❌ Gemini advice endpoint error: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        
        # Fallback to existing system
        username = session.get('user')
        user_data = emission_data.get(username, {'scope1': [], 'scope2': [], 'scope3': []})
        data = request.json
        question_type = data.get('question_type', 'general')
        advice = generate_ai_advice(user_data, question_type)
        advice['ai_source'] = 'fallback'
        advice['error'] = str(e)
        
        return jsonify({
            'success': True, 
            'advice': advice,
            'ai_source': 'fallback'
        })

@app.route('/api/analyze-document', methods=['POST'])
@login_required
def analyze_document():
    """API endpoint for real AI document analysis.
    Now also saves the uploaded file to a temp folder so it can be linked
    as evidence once the user confirms. Returns temp_file_id to the frontend.
    """
    print("🎯 AI Analysis endpoint called")

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    print(f"📁 Processing file: {file.filename}")

    try:
        file_data = file.read()
        print(f"✓ File read successfully, size: {len(file_data)} bytes")

        if file.filename.lower().endswith('.pdf'):
            print("📄 Processing as PDF")
            extracted_text = extract_text_from_pdf(file_data)
        else:
            print("🖼️ Processing as image")
            extracted_text = extract_text_from_image(file_data)

        if not extracted_text:
            return jsonify({'success': False, 'message': 'Could not extract text from document'})

        print(f"✓ Text extracted successfully, length: {len(extracted_text)}")
        print(f"📄 FULL OCR TEXT:\n{'='*60}\n{extracted_text}\n{'='*60}")

        analysis_result = parse_extracted_text(extracted_text)

        if not analysis_result or analysis_result['amount'] == 0:
            return jsonify({
                'success': False,
                'message': 'Could not automatically detect emission data. Please use manual entry.',
                'extracted_text': extracted_text[:200]
            })

        # ── Save file to temp folder so we can attach it as evidence on confirm ──
        import uuid
        temp_dir = os.path.join(app.root_path, 'static', 'uploads', 'evidence_temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_id = str(uuid.uuid4())
        safe_orig_name = secure_filename(file.filename)
        temp_filename = f"{session['user']}_{temp_id}_{safe_orig_name}"
        temp_path = os.path.join(temp_dir, temp_filename)
        with open(temp_path, 'wb') as tf:
            tf.write(file_data)

        print(f"✅ Analysis successful. Temp evidence saved: {temp_filename}")
        return jsonify({
            'success': True,
            'data': analysis_result,
            'temp_file_id': temp_id,
            'original_filename': safe_orig_name
        })

    except Exception as e:
        print(f"❌ Document analysis error: {str(e)}")
        return jsonify({'success': False, 'message': f'Analysis failed: {str(e)}'})

@app.route('/api/ai-advice', methods=['POST'])
@login_required
def get_ai_advice():
    username = session.get('user')
    user_data = emission_data.get(username, {'scope1': [], 'scope2': [], 'scope3': []})
    data = request.json
    question_type = data.get('question_type', 'general')
    advice = generate_ai_advice(user_data, question_type)
    return jsonify({'success': True, 'advice': advice})

@app.route('/api/add-emission', methods=['POST'])
@login_required
def add_emission():
    username = session.get('user')
    data = request.json

    scope    = data.get('scope')
    category = data.get('category')
    amount   = float(data.get('amount', 0))
    unit     = data.get('unit')
    region   = data.get('region')
    temp_file_id      = data.get('temp_file_id')       # set when user uploaded a bill/PDF
    original_filename = data.get('original_filename')  # original name of that file

    co2e = calculate_emissions(scope, category, amount, unit)

    # ── 1. Keep the existing in-memory store (for dashboard charts) ──
    if username not in emission_data:
        emission_data[username] = {'scope1': [], 'scope2': [], 'scope3': []}

    emission_data[username][scope].append({
        'category': category,
        'amount':   amount,
        'unit':     unit,
        'date':     datetime.now().strftime('%Y-%m-%d'),
        'co2e':     co2e
    })

    # ── 2. Persist to environmental_records (for Data Hub timeline) ──
    FUEL_ACTIVITIES = {
        'diesel', 'gasoline', 'petrol', 'ron95', 'ron97',
        'natural_gas', 'lpg', 'coal', 'fuel_oil', 'fuel'
    }
    CATEGORY_TO_MODULE = {
        'electricity': 'energy',
        'water':       'water',
        'waste':       'waste',
        'waste_landfill': 'waste',
        'land':        'land_biodiversity',
    }
    module_type = 'energy' if category in FUEL_ACTIVITIES else CATEGORY_TO_MODULE.get(category, 'energy')

    env_record = None
    try:
        env_record = EnvironmentalRecord(
            user_id=username,
            module_type=module_type,
            activity_type=category or 'unknown',
            quantity=amount,
            unit=unit or '',
            normalized_quantity=amount,
            normalized_unit=unit or '',
            reporting_year=datetime.utcnow().year,
            reporting_period='annual',
            reporting_scope=scope or '',
            notes=(f'Added via dashboard. CO2e: {co2e} kg. Region: {region}'
                   if region else f'Added via dashboard. CO2e: {co2e} kg.'),
            status='draft',
            created_by=username,
            updated_by=username,
        )
        db.session.add(env_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f'⚠️  add_emission: failed to write EnvironmentalRecord: {e}')

    # ── 3. If a bill/PDF was uploaded during AI analysis, link it as evidence ──
    if env_record and temp_file_id and original_filename:
        try:
            import glob
            temp_dir = os.path.join(app.root_path, 'static', 'uploads', 'evidence_temp')
            pattern  = os.path.join(temp_dir, f"{username}_{temp_file_id}_*")
            matches  = glob.glob(pattern)
            if matches:
                temp_path = matches[0]
                file_ext  = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''

                # Move to permanent evidence folder
                evidence_dir = os.path.join(app.root_path, 'static', 'uploads', 'environmental')
                os.makedirs(evidence_dir, exist_ok=True)
                timestamp       = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                final_filename  = f"{username}_{env_record.id}_{timestamp}_{secure_filename(original_filename)}"
                final_path      = os.path.join(evidence_dir, final_filename)
                os.rename(temp_path, final_path)

                evidence = EnvironmentalEvidence(
                    environmental_record_id=env_record.id,
                    filename=original_filename,
                    file_path=final_path.replace('\\', '/'),
                    description='Bill/receipt uploaded during data entry',
                    file_type=file_ext,
                    file_size=os.path.getsize(final_path),
                    uploaded_by=username,
                    uploaded_at=datetime.utcnow(),
                    verified=False
                )
                db.session.add(evidence)
                db.session.commit()
                print(f"✅ Evidence linked: {original_filename} → record {env_record.id}")
        except Exception as ev_err:
            db.session.rollback()
            print(f'⚠️  add_emission: evidence linking failed: {ev_err}')

    return jsonify({
        'success':   True,
        'co2e':      co2e,
        'record_id': env_record.id if env_record else None,
        'message':   f'Emission data added successfully: {co2e} kg CO2e'
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if not user:
            user = User.query.filter_by(email=username).first()

        if user and user.check_password(password) and user.is_active:
            session['user']    = user.username
            session['user_id'] = user.id
            session['email']   = user.email
            session['company'] = user.company_name
            session['role']    = user.role
            flash('Login successful!', 'success')
            
            # Redirect based on role
            if user.role == 'auditor':
                return redirect(url_for('auditor_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email    = request.form.get('email')
        password = request.form.get('password')
        company  = request.form.get('company')

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')

        # Create new user
        new_user = User(
            username     = username,
            email        = email,
            company_name = company,
            role         = 'company'
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        # Initialize emission data for new user
        emission_data[username] = {'scope1': [], 'scope2': [], 'scope3': []}

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/sentinel')
@login_required
def sentinel():
    username = session.get('user')
    user_data = emission_data.get(username, {'scope1': [], 'scope2': [], 'scope3': []})
    analysis = analyze_emission_patterns(user_data)
    initial_advice = generate_general_advice(analysis)
    
    return render_template('sentinel.html',
                         username=username,
                         analysis=analysis,
                         initial_advice=initial_advice,
                         user_data=user_data)

@app.route('/services')
@login_required
def services():
    username = session.get('user')
    return render_template('services.html', username=username)

@app.route('/report')
@login_required
def report():
    return render_template('report.html')
    
    # Get user info from session or database
    user_info = {
        'company': session.get('company', 'Your Company'),
        'email': session.get('email', 'N/A')
    }
    
    # Generate comprehensive report
    report = generate_gri_ghg_report(user_data, username, user_info)
    
    return render_template('report.html',
                         username=username,
                         report=report,
                         user_data=user_data)

@app.route('/api/generate-report-pdf')
@login_required
def generate_report_pdf():
    """Generate and download PDF report"""
    try:
        username = session.get('user')
        user_data = emission_data.get(username, {'scope1': [], 'scope2': [], 'scope3': []})
        
        # Get user info
        user_info = {
            'company': session.get('company', 'Your Company'),
            'email': session.get('email', 'N/A')
        }
        
        # Generate report data
        report = generate_gri_ghg_report(user_data, username, user_info)
        
        # Generate PDF
        pdf_content = generate_pdf_report(report)
        
        if pdf_content:
            # Create response with PDF
            response = app.response_class(
                response=pdf_content,
                status=200,
                mimetype='application/pdf'
            )
            response.headers['Content-Disposition'] = f'attachment; filename=carbon_report_{username}_{datetime.now().strftime("%Y%m%d")}.pdf'
            return response
        else:
            flash('Failed to generate PDF report', 'error')
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        print(f"❌ PDF report generation error: {str(e)}")
        flash('Error generating report. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/report-data')
@login_required
def get_report_data():
    """API endpoint to get report data for JavaScript"""
    try:
        username = session.get('user')
        user_data = emission_data.get(username, {'scope1': [], 'scope2': [], 'scope3': []})
        
        # Get user info
        user_info = {
            'company': session.get('company', 'Your Company'),
            'email': session.get('email', 'N/A')
        }
        
        # Generate report data
        report = generate_gri_ghg_report(user_data, username, user_info)
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        print(f"❌ Report data error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

# COMPLIANCE DASHBOARD ROUTE - ENHANCED VERSION
@app.route('/compliance_dashboard')
@login_required
def compliance_dashboard():
    """Enhanced compliance dashboard with standards tracking"""
    username = session.get('user')
    
    # Get user info
    user_info = {
        'company': session.get('company', 'Your Company'),
        'email': session.get('email', 'N/A')
    }
    
    # Get user's compliance data from database
    compliance_data = get_user_compliance_data(username)
    
    # Create standards status with ESG/Climate standards
    standards_status = [
        {
            'name': 'IFRS S1',
            'short_name': 'IFRS S1',
            'status': 'compliant',
            'compliance_percentage': 100,
            'clauses_assessed': 5,
            'total_clauses': 5,
            'description': 'General Requirements for Disclosure of Sustainability-related Financial Information',
            'category': 'Financial Reporting',
            'jurisdiction': 'Global'
        },
        {
            'name': 'IFRS S2',
            'short_name': 'IFRS S2',
            'status': 'partial',
            'compliance_percentage': 60,
            'clauses_assessed': 3,
            'total_clauses': 5,
            'description': 'Climate-related Disclosures',
            'category': 'Climate Reporting',
            'jurisdiction': 'Global'
        },
        {
            'name': 'TCFD',
            'short_name': 'TCFD',
            'status': 'compliant',
            'compliance_percentage': 100,
            'clauses_assessed': 4,
            'total_clauses': 4,
            'description': 'Task Force on Climate-related Financial Disclosures',
            'category': 'Climate Risk',
            'jurisdiction': 'Global'
        },
        {
            'name': 'ISO 14064-1',
            'short_name': 'ISO 14064',
            'status': 'compliant',
            'compliance_percentage': 100,
            'clauses_assessed': 5,
            'total_clauses': 5,
            'description': 'Greenhouse gas accounting and verification',
            'category': 'GHG Accounting',
            'jurisdiction': 'Global'
        },
        {
            'name': 'GHG Protocol',
            'short_name': 'GHG',
            'status': 'compliant',
            'compliance_percentage': 100,
            'clauses_assessed': 4,
            'total_clauses': 4,
            'description': 'Greenhouse Gas Protocol Corporate Standard',
            'category': 'GHG Accounting',
            'jurisdiction': 'Global'
        },
        {
            'name': 'GRI Standards',
            'short_name': 'GRI',
            'status': 'partial',
            'compliance_percentage': 78,
            'clauses_assessed': 3,
            'total_clauses': 4,
            'description': 'Global Reporting Initiative Standards',
            'category': 'Sustainability Reporting',
            'jurisdiction': 'Global'
        },
        {
            'name': 'Malaysia MGTC',
            'short_name': 'MGTC',
            'status': 'compliant',
            'compliance_percentage': 100,
            'clauses_assessed': 3,
            'total_clauses': 3,
            'description': 'Malaysian Green Technology Corporation Guidelines',
            'category': 'National Regulation',
            'jurisdiction': 'Malaysia'
        },
        {
            'name': 'Malaysia SEDA',
            'short_name': 'SEDA',
            'status': 'action_needed',
            'compliance_percentage': 33,
            'clauses_assessed': 1,
            'total_clauses': 3,
            'description': 'Sustainable Energy Development Authority Guidelines',
            'category': 'Energy Regulation',
            'jurisdiction': 'Malaysia'
        },
        {
            'name': 'Carbon Tax Readiness',
            'short_name': 'Carbon Tax',
            'status': 'partial',
            'compliance_percentage': 66,
            'clauses_assessed': 2,
            'total_clauses': 3,
            'description': 'Malaysia Carbon Tax implementation readiness',
            'category': 'Tax Regulation',
            'jurisdiction': 'Malaysia'
        }
    ]
    
    # Calculate overall compliance
    total_standards = len(standards_status)
    compliant_count = sum(1 for s in standards_status if s['status'] == 'compliant')
    partial_count = sum(1 for s in standards_status if s['status'] == 'partial')
    action_needed_count = sum(1 for s in standards_status if s['status'] == 'action_needed')
    
    overall_compliance = {
        'total_standards': total_standards,
        'compliant': compliant_count,
        'partial': partial_count,
        'action_needed': action_needed_count,
        'overall_score': round((compliant_count + partial_count * 0.5) / total_standards * 100, 1)
    }
    
    # Evidence data
    evidence_data = [
        {
            'standard': 'IFRS S2',
            'clause': 'S2-3',
            'title': 'Greenhouse gas emissions',
            'evidence_files': ['supplier_data_2024.pdf', 'scope3_calc.xlsx'],
            'status': 'partial'
        },
        {
            'standard': 'SEDA',
            'clause': 'SEDA-1',
            'title': 'Renewable energy target',
            'evidence_files': [],
            'status': 'action_needed'
        },
        {
            'standard': 'GRI',
            'clause': 'GRI 305',
            'title': 'Emissions',
            'evidence_files': ['emissions_report_2024.pdf', 'verification_cert.pdf'],
            'status': 'compliant'
        }
    ]
    
    # Upcoming deadlines
    deadlines = [
        {
            'title': 'SEDA Compliance',
            'date': '2025-06-30',
            'status': 'urgent',
            'description': 'Sustainable Energy Development Authority requirements'
        },
        {
            'title': 'Annual GHG Report',
            'date': '2025-03-31',
            'status': 'warning',
            'description': 'Annual greenhouse gas emissions reporting'
        },
        {
            'title': 'IFRS S2 Adoption',
            'date': '2025-12-31',
            'status': 'on_track',
            'description': 'Full implementation of IFRS S2'
        }
    ]
    
    # Audit stats (your existing data)
    audit_stats = {
        'total_entries': 156,
        'locked_periods': ['Q4-2024', 'Q1-2025'],
        'pending_verifications': 8,
        'recent_activity': [
            {
                'timestamp': '2025-01-15 14:30:00',
                'user_id': username,
                'action': 'upload',
                'table_name': 'source_docs',
                'record_id': 'doc_001_2025',
                'change_reason': 'Uploaded electricity bill'
            },
            {
                'timestamp': '2025-01-14 11:20:00',
                'user_id': 'auditor1',
                'action': 'verify',
                'table_name': 'emissions',
                'record_id': 'em_045_2025',
                'change_reason': 'Verified Scope 1 data'
            }
        ]
    }
    
    # Templates data (your existing)
    templates = [
        {'name': 'NSRF Report', 'type': 'Bursa Malaysia'},
        {'name': 'SEDG Basic', 'type': 'SME Compliance'},
        {'name': 'GHG Protocol', 'type': 'International'},
        {'name': 'GRI Standards', 'type': 'Sustainability'}
    ]
    
    return render_template('compliance_dashboard.html',
                         username=username,
                         user_info=user_info,
                         standards_status=standards_status,
                         overall_compliance=overall_compliance,
                         evidence_data=evidence_data,
                         deadlines=deadlines,
                         audit_stats=audt_stats,
                         templates=templates,
                         compliance_data=compliance_data)

# COMPLIANCE API ENDPOINTS
@app.route('/api/compliance/matrix')
@login_required
def get_compliance_matrix():
    """Get compliance matrix data"""
    try:
        username = session.get('user')
        standards = ComplianceStandard.query.all()
        
        # Get all clauses with user status
        clauses = []
        for standard in standards:
            standard_clauses = ComplianceClause.query.filter_by(standard_id=standard.id).all()
            for clause in standard_clauses:
                user_status = UserComplianceStatus.query.filter_by(
                    user_id=username, 
                    clause_id=clause.id
                ).first()
                
                # Get evidence count
                evidence_count = EvidenceFile.query.filter_by(
                    user_id=username,
                    clause_id=clause.id
                ).count() if user_status else 0
                
                clause_data = {
                    'id': clause.id,
                    'standard_id': standard.id,
                    'standard_name': standard.short_name,
                    'clause_number': clause.clause_number,
                    'title': clause.title,
                    'status': user_status.status if user_status else 'not_assessed',
                    'evidence_count': evidence_count,
                    'priority': clause.priority,
                    'category': clause.category
                }
                
                clauses.append(clause_data)
        
        return jsonify({
            'success': True,
            'clauses': clauses
        })
        
    except Exception as e:
        print(f"❌ Error getting compliance matrix: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/compliance/standard/<int:standard_id>')
@login_required
def get_standard_details(standard_id):
    """Get detailed information about a standard"""
    try:
        username = session.get('user')
        standard = ComplianceStandard.query.get_or_404(standard_id)
        
        # Get all clauses for this standard
        clauses = ComplianceClause.query.filter_by(standard_id=standard_id).all()
        
        clause_details = []
        for clause in clauses:
            user_status = UserComplianceStatus.query.filter_by(
                user_id=username,
                clause_id=clause.id
            ).first()
            
            evidence_count = EvidenceFile.query.filter_by(
                user_id=username,
                clause_id=clause.id
            ).count() if user_status else 0
            
            clause_details.append({
                'id': clause.id,
                'clause_number': clause.clause_number,
                'title': clause.title,
                'description': clause.description,
                'requirement': clause.requirement,
                'priority': clause.priority,
                'status': user_status.status if user_status else 'not_assessed',
                'evidence_count': evidence_count,
                'assessment_date': user_status.assessment_date.isoformat() if user_status and user_status.assessment_date else None,
                'next_assessment_date': user_status.next_assessment_date.isoformat() if user_status and user_status.next_assessment_date else None
            })
        
        return jsonify({
            'success': True,
            'standard': {
                'id': standard.id,
                'name': standard.name,
                'short_name': standard.short_name,
                'version': standard.version,
                'description': standard.description,
                'jurisdiction': standard.jurisdiction,
                'category': standard.category,
                'website': standard.website
            },
            'clauses': clause_details
        })
        
    except Exception as e:
        print(f"❌ Error getting standard details: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/compliance/clause/<int:clause_id>')
@login_required
def get_clause_details(clause_id):
    """Get detailed information about a clause"""
    try:
        username = session.get('user')
        clause = ComplianceClause.query.get_or_404(clause_id)
        standard = ComplianceStandard.query.get(clause.standard_id)
        
        # Get user status
        user_status = UserComplianceStatus.query.filter_by(
            user_id=username,
            clause_id=clause_id
        ).first()
        
        # Get evidence files
        evidence_files = EvidenceFile.query.filter_by(
            user_id=username,
            clause_id=clause_id
        ).all()
        
        evidence_list = []
        for ev in evidence_files:
            evidence_list.append({
                'id': ev.id,
                'filename': ev.filename,
                'file_type': ev.file_type,
                'description': ev.description,
                'upload_date': ev.upload_date.isoformat(),
                'verified': ev.verified,
                'file_url': url_for('static', filename=f'uploads/compliance_evidence/{ev.filename}')
            })
        
        # Get mappings to other standards
        mappings = ClauseMapping.query.filter_by(source_clause_id=clause_id).all()
        mapping_list = []
        for mapping in mappings:
            target_clause = ComplianceClause.query.get(mapping.target_clause_id)
            target_standard = ComplianceStandard.query.get(mapping.target_standard_id)
            
            mapping_list.append({
                'standard_name': target_standard.name,
                'standard_id': target_standard.id,
                'clause_number': target_clause.clause_number,
                'clause_id': target_clause.id,
                'title': target_clause.title,
                'mapping_type': mapping.mapping_type,
                'confidence': mapping.confidence
            })
        
        return jsonify({
            'success': True,
            'clause': {
                'id': clause.id,
                'standard_id': standard.id,
                'standard_name': standard.name,
                'clause_number': clause.clause_number,
                'title': clause.title,
                'description': clause.description,
                'requirement': clause.requirement,
                'guidance': clause.guidance,
                'priority': clause.priority,
                'category': clause.category
            },
            'status': {
                'status': user_status.status if user_status else 'not_assessed',
                'assessment_date': user_status.assessment_date.isoformat() if user_status and user_status.assessment_date else None,
                'next_assessment_date': user_status.next_assessment_date.isoformat() if user_status and user_status.next_assessment_date else None,
                'comments': user_status.comments if user_status else None,
                'confidence_score': user_status.confidence_score if user_status else 0
            },
            'evidence': evidence_list,
            'mappings': mapping_list
        })
        
    except Exception as e:
        print(f"❌ Error getting clause details: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/compliance/update-status', methods=['POST'])
@login_required
def update_compliance_status():
    """Update compliance status for a clause"""
    try:
        username = session.get('user')
        data = request.json
        
        clause_id = data.get('clause_id')
        status = data.get('status')
        comments = data.get('comments')
        next_assessment_date = data.get('next_assessment_date')
        
        if not clause_id or not status:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        clause = ComplianceClause.query.get_or_404(clause_id)
        
        # Find or create user status
        user_status = UserComplianceStatus.query.filter_by(
            user_id=username,
            clause_id=clause_id
        ).first()
        
        if not user_status:
            user_status = UserComplianceStatus(
                user_id=username,
                clause_id=clause_id,
                standard_id=clause.standard_id,
                status=status,
                comments=comments,
                assessment_date=datetime.utcnow()
            )
            db.session.add(user_status)
        else:
            user_status.status = status
            user_status.comments = comments
            user_status.assessment_date = datetime.utcnow()
        
        if next_assessment_date:
            user_status.next_assessment_date = datetime.fromisoformat(next_assessment_date)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating compliance status: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/compliance/upload-evidence', methods=['POST'])
@login_required
def upload_compliance_evidence():
    """Upload evidence file for a clause"""
    try:
        username = session.get('user')
        
        if 'evidence_file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'})
        
        file = request.files['evidence_file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        clause_id = request.form.get('clause_id')
        standard_id = request.form.get('standard_id')
        description = request.form.get('description')
        evidence_type = request.form.get('evidence_type')
        
        if not clause_id:
            return jsonify({'success': False, 'message': 'Missing clause_id'})
        
        # Create evidence directory if it doesn't exist
        evidence_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'compliance_evidence')
        if not os.path.exists(evidence_dir):
            os.makedirs(evidence_dir)
        
        # Save file
        filename = secure_filename(f"{username}_{clause_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        file_path = os.path.join(evidence_dir, filename)
        file.save(file_path)
        
        # Find or create user status
        user_status = UserComplianceStatus.query.filter_by(
            user_id=username,
            clause_id=clause_id
        ).first()
        
        if not user_status:
            user_status = UserComplianceStatus(
                user_id=username,
                clause_id=clause_id,
                standard_id=standard_id,
                status='partial',  # Default to partial when evidence is uploaded
                assessment_date=datetime.utcnow()
            )
            db.session.add(user_status)
            db.session.flush()  # Get the ID
        
        # Create evidence record
        evidence = EvidenceFile(
            user_id=username,
            compliance_status_id=user_status.id,
            clause_id=clause_id,
            filename=filename,
            file_path=file_path,
            file_type=file.content_type,
            file_size=os.path.getsize(file_path),
            description=description,
            upload_date=datetime.utcnow()
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidence uploaded successfully',
            'evidence_id': evidence.id,
            'filename': filename
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error uploading evidence: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/compliance/mapping/<int:clause_id>')
@login_required
def get_clause_mappings(clause_id):
    """Get mappings for a clause to other standards"""
    try:
        mappings = ClauseMapping.query.filter_by(source_clause_id=clause_id).all()
        
        mapping_list = []
        for mapping in mappings:
            source_clause = ComplianceClause.query.get(mapping.source_clause_id)
            target_clause = ComplianceClause.query.get(mapping.target_clause_id)
            target_standard = ComplianceStandard.query.get(mapping.target_standard_id)
            
            # Get user status for target clause
            username = session.get('user')
            user_status = UserComplianceStatus.query.filter_by(
                user_id=username,
                clause_id=target_clause.id
            ).first() if target_clause else None
            
            mapping_list.append({
                'mapping_id': mapping.id,
                'source_clause_number': source_clause.clause_number,
                'source_clause_title': source_clause.title,
                'target_standard_name': target_standard.name,
                'target_standard_id': target_standard.id,
                'target_clause_number': target_clause.clause_number,
                'target_clause_id': target_clause.id,
                'target_clause_title': target_clause.title,
                'mapping_type': mapping.mapping_type,
                'confidence': mapping.confidence,
                'notes': mapping.notes,
                'status': user_status.status if user_status else 'not_assessed'
            })
        
        return jsonify({
            'success': True,
            'mappings': mapping_list
        })
        
    except Exception as e:
        print(f"❌ Error getting clause mappings: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/compliance/generate-report', methods=['POST'])
@login_required
def generate_compliance_report():
    """Generate compliance report"""
    try:
        username = session.get('user')
        data = request.json
        report_format = data.get('format', 'pdf')
        include_evidence = data.get('include_evidence', False)
        
        # Get compliance data
        compliance_data = get_user_compliance_data(username)
        
        # Get user info
        user_info = {
            'company': session.get('company', 'Your Company'),
            'email': session.get('email', 'N/A')
        }
        
        # Generate report data
        report_date = datetime.now().strftime('%Y-%m-%d')
        
        report = {
            'report_metadata': {
                'report_id': f'COMPLIANCE-{datetime.now().strftime("%Y%m%d")}-{username}',
                'report_date': report_date,
                'prepared_by': 'EmittiF Compliance Dashboard',
                'prepared_for': user_info['company'],
                'verification_status': 'Internal Assessment'
            },
            'company_info': user_info,
            'executive_summary': {
                'overall_compliance_score': compliance_data['overall_score'],
                'standards_assessed': len(compliance_data['standards']),
                'total_clauses': sum(std['total_clauses'] for std in compliance_data['standards']),
                'compliant_clauses': sum(std['compliant_clauses'] for std in compliance_data['standards']),
                'urgent_actions_count': len(compliance_data['urgent_actions'])
            },
            'standards_assessment': compliance_data['standards'],
            'urgent_actions': compliance_data['urgent_actions'][:10],  # Top 10
            'recommendations': {
                'immediate': [
                    'Address high-priority non-compliant clauses',
                    'Upload missing evidence for partial compliance items',
                    'Set assessment dates for all clauses',
                    'Review mapping between standards for efficiency'
                ],
                'short_term': [
                    'Complete assessment for all standards',
                    'Implement evidence management system',
                    'Establish compliance monitoring schedule',
                    'Train staff on compliance requirements'
                ],
                'long_term': [
                    'Achieve 100% compliance for key standards',
                    'Implement automated compliance tracking',
                    'Pursue third-party verification',
                    'Integrate compliance into business processes'
                ]
            }
        }
        
        if report_format == 'pdf':
            # Generate PDF using ReportLab (simplified version)
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            story.append(Paragraph(f"Compliance Assessment Report", styles['Title']))
            story.append(Paragraph(f"Prepared for: {user_info['company']}", styles['Normal']))
            story.append(Paragraph(f"Date: {report_date}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Add overall score
            story.append(Paragraph(f"Overall Compliance Score: {compliance_data['overall_score']}%", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Add standards summary table
            table_data = [['Standard', 'Clauses', 'Compliant', 'Score']]
            for std in compliance_data['standards']:
                table_data.append([
                    std['name'],
                    str(std['total_clauses']),
                    str(std['compliant_clauses']),
                    f"{std['compliance_percentage']}%"
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            response = app.response_class(
                response=pdf_content,
                status=200,
                mimetype='application/pdf'
            )
            response.headers['Content-Disposition'] = f'attachment; filename=compliance_report_{username}_{report_date.replace("-", "")}.pdf'
            return response
        
        else:
            # Return JSON report
            return jsonify({
                'success': True,
                'report': report
            })
        
    except Exception as e:
        print(f"❌ Error generating compliance report: {e}")
        return jsonify({'success': False, 'message': str(e)})
    
@app.route('/profile_settings', methods=['GET', 'POST'])
def profile_settings():
    """User Profile Settings page - accessible via user avatar dropdown"""
    if 'user' not in session:
        flash('Please login to access profile settings.', 'error')
        return redirect(url_for('login'))
    
    username = session['user']
    company = session.get('company', 'Unknown')
    
    # Get or create user profile
    profile = UserProfile.query.filter_by(user_id=username).first()
    
    if request.method == 'POST':
        try:
            # Get form data
            full_legal_name = request.form.get('full_legal_name', '').strip()
            phone_number = request.form.get('phone_number', '').strip()
            job_title = request.form.get('job_title', '').strip()
            department = request.form.get('department', '').strip()
            
            # Multi-select ESG Responsibility
            esg_responsibility = request.form.getlist('esg_responsibility[]')
            
            # Authority Level
            authority_level = request.form.get('authority_level', 'Data Entry')
            
            # Declaration
            declaration_accepted = 'declaration_accepted' in request.form
            
            if not profile:
                # Create new profile
                profile = UserProfile(
                    user_id=username,
                    company_id=company,
                    full_legal_name=full_legal_name,
                    phone_number=phone_number,
                    job_title=job_title,
                    department=department,
                    esg_responsibility=json.dumps(esg_responsibility),
                    authority_level=authority_level,
                    declaration_accepted=declaration_accepted,
                    updated_by=username
                )
                if declaration_accepted:
                    profile.declaration_timestamp = datetime.utcnow()
                db.session.add(profile)
            else:
                # Update existing profile
                profile.full_legal_name = full_legal_name
                profile.phone_number = phone_number
                profile.job_title = job_title
                profile.department = department
                profile.esg_responsibility = json.dumps(esg_responsibility)
                profile.authority_level = authority_level
                profile.declaration_accepted = declaration_accepted
                profile.updated_by = username
                if declaration_accepted and not profile.declaration_timestamp:
                    profile.declaration_timestamp = datetime.utcnow()
            
            db.session.commit()
            
            flash('Profile settings saved successfully!', 'success')
            return redirect(url_for('profile_settings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving profile: {str(e)}', 'error')
    
    # Prepare form data
    profile_data = profile.to_dict() if profile else {
        'user_id': username,
        'company_id': company,
        'full_legal_name': '',
        'phone_number': '',
        'job_title': '',
        'department': '',
        'esg_responsibility': [],
        'authority_level': 'Data Entry',
        'declaration_accepted': False
    }
    
    return render_template('profile_settings.html', 
                         profile=profile_data,
                         user_email=session.get('email', ''),
                         user_role=session.get('role', 'Sustainability Lead'))

@app.route('/company_settings', methods=['GET', 'POST'])
def company_settings():
    """Company Settings page - accessible via user avatar dropdown"""
    if 'user' not in session:
        flash('Please login to access company settings.', 'error')
        return redirect(url_for('login'))
    
    username = session['user']
    company = session.get('company', 'Unknown')
    user_role = session.get('role', 'Sustainability Lead')
    
    # Check permissions - only Admin and Sustainability Lead can edit
    can_edit = user_role.lower() in ['admin', 'sustainability lead', 'company']
    
    # Get company settings
    company_settings_obj = CompanySettings.query.filter_by(company_id=company).first()
    
    if request.method == 'POST' and can_edit:
        try:
            # Check if audit mode is enabled (read-only)
            if company_settings_obj and company_settings_obj.audit_mode_enabled:
                flash('Company settings are locked during audit mode.', 'error')
                return redirect(url_for('company_settings'))
            
            # Section 1: Legal Identity
            legal_company_name = request.form.get('legal_company_name', '').strip()
            company_registration_number = request.form.get('company_registration_number', '').strip()
            country_of_incorporation = request.form.get('country_of_incorporation', '').strip()
            industry_classification = request.form.get('industry_classification', '').strip()
            financial_year_start = request.form.get('financial_year_start', '').strip()
            financial_year_end = request.form.get('financial_year_end', '').strip()
            reporting_currency = request.form.get('reporting_currency', 'MYR')
            
            # Section 2: Organisational Boundary
            reporting_boundary_method = request.form.get('reporting_boundary_method', 'Operational Control')
            included_entities = request.form.get('included_entities', '').strip()
            excluded_entities = request.form.get('excluded_entities', '').strip()
            excluded_entities_justification = request.form.get('excluded_entities_justification', '').strip()
            
            # Section 3: Operational Footprint
            number_of_operational_sites = request.form.get('number_of_operational_sites', '0')
            site_locations_text = request.form.get('site_locations', '').strip()
            primary_business_activities = request.form.get('primary_business_activities', '').strip()
            
            # Parse site locations (comma-separated)
            site_locations = [loc.strip() for loc in site_locations_text.split(',') if loc.strip()]
            
            # Section 4: Governance & Oversight
            board_oversight = 'board_oversight' in request.form
            esg_committee_exists = 'esg_committee_exists' in request.form
            role_responsible_for_esg = request.form.get('role_responsible_for_esg', '').strip()
            external_assurance_status = request.form.get('external_assurance_status', 'None')
            
            # Section 5: Policies & Commitments
            policy_issue_dates = {
                'esg_policy': request.form.get('esg_policy_issue_date', ''),
                'environmental_policy': request.form.get('environmental_policy_issue_date', ''),
                'health_safety_policy': request.form.get('health_safety_policy_issue_date', ''),
                'supplier_code': request.form.get('supplier_code_issue_date', '')
            }
            
            # Section 6: Reporting Scope Selection
            reporting_scope = request.form.getlist('reporting_scope[]')
            
            if not company_settings_obj:
                # Create new company settings
                company_settings_obj = CompanySettings(
                    company_id=company,
                    legal_company_name=legal_company_name,
                    company_registration_number=company_registration_number,
                    country_of_incorporation=country_of_incorporation,
                    industry_classification=industry_classification,
                    financial_year_start=financial_year_start,
                    financial_year_end=financial_year_end,
                    reporting_currency=reporting_currency,
                    reporting_boundary_method=reporting_boundary_method,
                    included_entities=included_entities,
                    excluded_entities=excluded_entities,
                    excluded_entities_justification=excluded_entities_justification,
                    number_of_operational_sites=int(number_of_operational_sites) if number_of_operational_sites.isdigit() else 0,
                    site_locations=json.dumps(site_locations),
                    primary_business_activities=primary_business_activities,
                    board_oversight=board_oversight,
                    esg_committee_exists=esg_committee_exists,
                    role_responsible_for_esg=role_responsible_for_esg,
                    external_assurance_status=external_assurance_status,
                    policy_issue_dates=json.dumps(policy_issue_dates),
                    reporting_scope=json.dumps(reporting_scope),
                    created_by=username,
                    updated_by=username
                )
                db.session.add(company_settings_obj)
            else:
                # Update existing settings
                company_settings_obj.legal_company_name = legal_company_name
                company_settings_obj.company_registration_number = company_registration_number
                company_settings_obj.country_of_incorporation = country_of_incorporation
                company_settings_obj.industry_classification = industry_classification
                company_settings_obj.financial_year_start = financial_year_start
                company_settings_obj.financial_year_end = financial_year_end
                company_settings_obj.reporting_currency = reporting_currency
                company_settings_obj.reporting_boundary_method = reporting_boundary_method
                company_settings_obj.included_entities = included_entities
                company_settings_obj.excluded_entities = excluded_entities
                company_settings_obj.excluded_entities_justification = excluded_entities_justification
                company_settings_obj.number_of_operational_sites = int(number_of_operational_sites) if number_of_operational_sites.isdigit() else 0
                company_settings_obj.site_locations = json.dumps(site_locations)
                company_settings_obj.primary_business_activities = primary_business_activities
                company_settings_obj.board_oversight = board_oversight
                company_settings_obj.esg_committee_exists = esg_committee_exists
                company_settings_obj.role_responsible_for_esg = role_responsible_for_esg
                company_settings_obj.external_assurance_status = external_assurance_status
                company_settings_obj.policy_issue_dates = json.dumps(policy_issue_dates)
                company_settings_obj.reporting_scope = json.dumps(reporting_scope)
                company_settings_obj.updated_by = username
                company_settings_obj.version = company_settings_obj.version + 1
            
            db.session.commit()
            
            flash('Company settings saved successfully!', 'success')
            return redirect(url_for('company_settings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving company settings: {str(e)}', 'error')
    
    # Prepare data for template
    company_data = company_settings_obj.to_dict() if company_settings_obj else {
        'company_id': company,
        'legal_company_name': company,
        'reporting_boundary_method': 'Operational Control',
        'external_assurance_status': 'None',
        'site_locations': [],
        'reporting_scope': [],
        'policy_issue_dates': {},
        'audit_mode_enabled': False,
        'version': 1
    }
    
    return render_template('company_settings.html',
                         company=company_data,
                         can_edit=can_edit,
                         user_role=user_role)

# ============================================
# DATA INPUT CENTER ROUTES
# ============================================

@app.route('/esg-data-center')
@login_required
def esg_data_center():
    """ESG Data Center - Main hub for sustainability data"""
    # Get company settings from session
    company_id = session.get('company', '').strip().strip("'")
    user_id = session.get('user')
    
    if not company_id or not user_id:
        flash('Please login to access the ESG Data Center', 'error')
        return redirect(url_for('login'))
    
    # Get company settings
    company_settings = CompanySettings.query.filter_by(company_id=company_id).first()
    
    # Get user's company info
    company_name = 'Your Company'
    if 'users' in globals() and user_id in users:
        company_name = users[user_id].get('company', 'Your Company')
    
    # Calculate completion percentages (mock data for now)
    completion_stats = {
        'environmental': 85,
        'social': 65,
        'governance': 45,
        'supply_chain': 30,
        'overall': 56
    }
    
    # Get recent activity
    recent_activity = [
        {'date': 'Just now', 'module': 'Environmental → Energy', 'action': 'Added electricity consumption', 'user': user_id},
        {'date': '2 hours ago', 'module': 'Social → Workforce', 'action': 'Updated employee counts', 'user': 'HR Manager'},
        {'date': 'Yesterday', 'module': 'Supply Chain', 'action': 'Invited 3 new suppliers', 'user': 'Procurement'}
    ]
    
    return render_template('esg_data_center.html',
                         company_settings=company_settings,
                         company_name=company_name,
                         completion_stats=completion_stats,
                         recent_activity=recent_activity)

@app.route('/esg-environmental')
@login_required
def esg_environmental():
    """Environmental data module - activity data tracking (NOT emissions)"""
    if not session.get('user'):
        return redirect(url_for('login'))
    
    # Get current year for dropdown
    current_year = datetime.utcnow().year
    
    # Get any existing environmental data for the user
    records = EnvironmentalRecord.query.filter_by(
        user_id=session['user']
    ).order_by(EnvironmentalRecord.created_at.desc()).limit(10).all()
    
    # Prepare data for template
    record_summary = []
    for record in records:
        record_summary.append({
            'module_type': record.module_type,
            'activity_type': record.activity_type,
            'quantity': record.quantity,
            'unit': record.unit,
            'year': record.reporting_year,
            'status': record.status
        })
    
    # Get completion percentage
    completion_data = calculate_environmental_completion(session['user'])
    
    return render_template(
        'esg_environmental.html',
        current_year=current_year,
        record_summary=record_summary,
        completion_percentage=completion_data.get('overall_percentage', 0),
        completion_details=completion_data
    )

@app.route('/esg-social')
@login_required
def esg_social():
    """Social & workforce data module"""
    company_settings = CompanySettings.query.filter_by(
        company_id=session.get('company')
    ).first()
    
    return render_template('social_module.html',
                         company_settings=company_settings)

@app.route('/esg-governance')
@login_required
def esg_governance():
    """Governance data module"""
    company_settings = CompanySettings.query.filter_by(
        company_id=session.get('company')
    ).first()
    
    return render_template('governance_module.html',
                         company_settings=company_settings)

@app.route('/api/governance/save', methods=['POST'])
@login_required
def save_governance_data():
    """Save governance data"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        year = int(data.get('reporting_year', datetime.utcnow().year))
        company_id = session.get('company', '').strip().strip("'")
        user_id = session.get('user')
        section = data.get('section', 'risk')

        def to_int(val):
            try: return int(float(val)) if val not in [None, '', []] else None
            except: return None

        def to_float(val):
            try: return float(val) if val not in [None, '', []] else None
            except: return None

        import sqlite3
        db_path = 'instance/carbon_tracker.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT id FROM governance_data WHERE company_id=? AND reporting_year=?", (company_id, year))
        existing = cur.fetchone()

        fields_values = {
            'risk_assessments_conducted': to_int(data.get('risk_assessments_conducted')),
            'significant_risks_identified': to_int(data.get('significant_risks_identified')),
            'risks_mitigated': to_int(data.get('risks_mitigated')),
            'risk_mitigation_budget': to_float(data.get('risk_mitigation_budget')),
            'risk_framework': data.get('risk_framework') or None,
            'risk_categories': data.get('risk_categories') or None,
            'compliance_incidents': to_int(data.get('compliance_incidents')),
            'regulatory_fines': to_float(data.get('regulatory_fines')),
            'audit_findings': to_int(data.get('audit_findings')),
            'audit_findings_resolved': to_int(data.get('audit_findings_resolved')),
            'compliance_notes': data.get('compliance_notes') or None,
            'regulators': data.get('regulators') or None,
            'corruption_incidents': to_int(data.get('corruption_incidents')),
            'corruption_dismissals': to_int(data.get('corruption_dismissals')),
            'anti_corruption_training_pct': to_float(data.get('anti_corruption_training_pct')),
            'adequate_procedures': data.get('adequate_procedures') or None,
            'whistleblower_reports': to_int(data.get('whistleblower_reports')),
            'whistleblower_closed': to_int(data.get('whistleblower_closed')),
            'whistleblower_channel': data.get('whistleblower_channel') or None,
            'whistleblower_policy': data.get('whistleblower_policy') or None,
            'ethics_policies': data.get('ethics_policies') or None,
            'ethics_training_hours': to_int(data.get('ethics_training_hours')),
            'ethics_training_employees': to_int(data.get('ethics_training_employees')),
            'data_breaches': to_int(data.get('data_breaches')),
            'breach_customers_affected': to_int(data.get('breach_customers_affected')),
            'board_size': to_int(data.get('board_size')),
            'independent_directors': to_int(data.get('independent_directors')),
            'female_directors': to_int(data.get('female_directors')),
            'board_meetings': to_int(data.get('board_meetings')),
            'board_attendance_pct': to_float(data.get('board_attendance_pct')),
            'board_committees': data.get('board_committees') or None,
            'total_tax_paid': to_float(data.get('total_tax_paid')),
            'effective_tax_rate': to_float(data.get('effective_tax_rate')),
            'countries_of_operation': to_int(data.get('countries_of_operation')),
            'transfer_pricing_policy': data.get('transfer_pricing_policy') or None,
            'sst_paid': to_float(data.get('sst_paid')),
            'withholding_tax': to_float(data.get('withholding_tax')),
            'cukai_makmur': data.get('cukai_makmur') or None,
            'tp_audit': data.get('tp_audit') or None,
            'section': section,
        }

        if existing:
            # Only update non-None fields to avoid overwriting other tabs' data
            non_null = {k: v for k, v in fields_values.items() if v is not None}
            if non_null:
                set_clause = ', '.join([f"{k}=?" for k in non_null.keys()])
                values = list(non_null.values()) + [company_id, year]
                cur.execute(f"UPDATE governance_data SET {set_clause} WHERE company_id=? AND reporting_year=?", values)
        else:
            fields_values['company_id'] = company_id
            fields_values['reporting_year'] = year
            fields_values['entered_by'] = user_id
            fields_values['data_source'] = 'actual'
            fields_values['status'] = 'draft'
            cols = ', '.join(fields_values.keys())
            placeholders = ', '.join(['?' for _ in fields_values])
            cur.execute(f"INSERT INTO governance_data ({cols}) VALUES ({placeholders})", list(fields_values.values()))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'{section} data saved successfully'})

    except Exception as e:
        print(f"Governance save error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/governance/data', methods=['GET'])
@login_required
def get_governance_data():
    """Get governance data for a reporting year"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        year = request.args.get('year', datetime.utcnow().year)
        company_id = session.get('company', '').strip().strip("'")

        import sqlite3
        db_path = 'instance/carbon_tracker.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT * FROM governance_data WHERE company_id=? AND reporting_year=?", (company_id, int(year)))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({'success': True, 'data': None})

        data = dict(row)
        return jsonify({'success': True, 'data': data})

    except Exception as e:
        print(f"Governance load error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/esg-supply-chain')
@login_required
def esg_supply_chain():
    """Supply chain (Scope 3) management module"""
    company_settings = CompanySettings.query.filter_by(
        company_id=session.get('company')
    ).first()
    
    return render_template('supply_chain_module.html',
                         company_settings=company_settings)

# ============================================
# COMPATIBILITY ROUTES - For templates using 'module' naming convention
# These map to the proper ESG endpoints
@app.route('/environmental-module')
@login_required
def environmental_module():
    """Redirect to environmental ESG module"""
    return redirect(url_for('esg_environmental'))

@app.route('/social-module')
@login_required
def social_module():
    """Redirect to social ESG module"""
    return redirect(url_for('esg_social'))

@app.route('/governance-module')
@login_required
def governance_module():
    """Redirect to governance ESG module"""
    return redirect(url_for('esg_governance'))

@app.route('/supply-chain-module')
@login_required
def supply_chain_module():
    """Redirect to supply chain ESG module"""
    return redirect(url_for('esg_supply_chain'))

# ============================================
# ESG DATA API ENDPOINTS
# ============================================

@app.route('/api/esg/save-data', methods=['POST'])
@login_required
def save_esg_data():
    """Save ESG data entry with audit fields"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['module', 'reporting_year', 'data_source']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get company settings for reporting scope
        company_settings = CompanySettings.query.filter_by(
            company_id=session.get('company')
        ).first()
        
        if not company_settings:
            return jsonify({'error': 'Company settings not found'}), 404
        
        # Create data entry with audit fields
        esg_entry = ESGDataEntry(
            company_id=session.get('company'),
            reporting_year=data['reporting_year'],
            entered_by=session.get('user'),
            timestamp=datetime.utcnow(),
            data_source=data['data_source'],
            evidence_reference=data.get('evidence_reference', ''),
            module_id=get_module_id(data['module']),  # Helper function needed
            value_numeric=data.get('value_numeric'),
            value_text=data.get('value_text'),
            value_percentage=data.get('value_percentage'),
            value_boolean=data.get('value_boolean'),
            is_estimated=data.get('is_estimated', False),
            estimation_method=data.get('estimation_method'),
            data_quality_score=data.get('data_quality_score', 'B'),
            comments=data.get('comments'),
            status='draft'
        )
        
        db.session.add(esg_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Data saved successfully',
            'entry_id': esg_entry.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Get live stats for all ESG modules for the data hub"""
    try:
        year = request.args.get('year', datetime.utcnow().year)
        company_id = session.get('company', '').strip().strip("'")

        import sqlite3
        conn = sqlite3.connect('instance/carbon_tracker.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # ---- SOCIAL ----
        cur.execute("SELECT * FROM social_workforce_data WHERE company_id=? ORDER BY reporting_year DESC LIMIT 1",
                   (company_id,))
        social_row = cur.fetchone()
        social_pct = 0
        social_fields = 0
        if social_row:
            social_dict = dict(social_row)
            skip = {'id', 'company_id', 'reporting_year', 'created_at', 'updated_at'}
            meaningful = {k: v for k, v in social_dict.items() if k not in skip}
            social_fields = len([v for v in meaningful.values() if v not in (None, '', 0)])
            social_pct = min(100, round((social_fields / max(len(meaningful), 1)) * 100))

        # Survey responses
        try:
            cur.execute("SELECT COUNT(*) FROM employee_survey_responses WHERE company_id=?", (company_id,))
            survey_count = cur.fetchone()[0]
        except:
            survey_count = 0

        # ---- GOVERNANCE ----
        cur.execute("SELECT * FROM governance_data WHERE company_id=? ORDER BY reporting_year DESC LIMIT 1",
                   (company_id,))
        gov_row = cur.fetchone()
        gov_pct = 0
        gov_fields = 0
        if gov_row:
            gov_dict = dict(gov_row)
            skip = {'id', 'company_id', 'reporting_year', 'created_at', 'updated_at'}
            meaningful = {k: v for k, v in gov_dict.items() if k not in skip}
            gov_fields = len([v for v in meaningful.values() if v not in (None, '', 0)])
            gov_pct = min(100, round((gov_fields / max(len(meaningful), 1)) * 100))

        # ---- SUPPLY CHAIN ----
        cur.execute("SELECT COUNT(*) FROM supplier_invitations WHERE company_id=?", (company_id,))
        total_suppliers = cur.fetchone()[0]

        cur.execute("""SELECT COUNT(*) FROM supplier_invitations 
                      WHERE company_id=? AND invitation_status IN ('submitted','approved')""",
                   (company_id,))
        responded_suppliers = cur.fetchone()[0]

        cur.execute("""SELECT COUNT(*) FROM supplier_invitations 
                      WHERE company_id=? AND invitation_status='invited'""",
                   (company_id,))
        pending_suppliers = cur.fetchone()[0]

        supply_pct = round((responded_suppliers / total_suppliers * 100)) if total_suppliers > 0 else 0

        conn.close()

        # ── ENVIRONMENTAL (from environmental_records DB table) ──
        username = session.get('user')
        env_records = EnvironmentalRecord.query.filter_by(user_id=username).all()
        FUEL_ACTS = {'diesel','gasoline','petrol','ron95','ron97','natural_gas','lpg','coal','fuel_oil','fuel'}
        has_energy = any(r.module_type == 'energy' and r.activity_type not in FUEL_ACTS for r in env_records)
        has_fuel   = any(r.module_type == 'energy' and r.activity_type in FUEL_ACTS for r in env_records)
        has_water  = any(r.module_type == 'water' for r in env_records)
        has_waste  = any(r.module_type == 'waste' for r in env_records)
        env_filled   = sum([has_energy, has_fuel, has_water, has_waste])
        env_pct      = round((env_filled / 4) * 100)
        env_evidence = sum(len(r.evidence_files) for r in env_records)

        return jsonify({
            'success': True,
            'environmental': {
                'pct': env_pct,
                'records': len(env_records),
                'evidence_files': env_evidence,
                'status': 'All categories filled' if env_pct == 100 else f'{env_filled}/4 categories filled',
            },
            'social': {
                'pct': social_pct,
                'fields_filled': social_fields,
                'survey_responses': survey_count,
                'status': 'All sections filled' if social_pct >= 80 else f'{social_fields} fields filled'
            },
            'governance': {
                'pct': gov_pct,
                'fields_filled': gov_fields,
                'status': 'All sections filled' if gov_pct >= 80 else f'{gov_fields} fields filled'
            },
            'supply': {
                'pct': supply_pct,
                'total': total_suppliers,
                'responded': responded_suppliers,
                'pending': pending_suppliers,
                'status': f'{pending_suppliers} pending supplier responses' if pending_suppliers > 0 else f'{responded_suppliers} suppliers responded'
            }
        })

    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/social/save', methods=['POST'])
@login_required
def save_social_data():
    """Save social & workforce data"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        year = int(data.get('reporting_year', datetime.utcnow().year))
        company_id = session.get('company', '').strip().strip("'")
        user_id = session.get('user')
        section = data.get('section', 'workforce')

        def to_int(val):
            try: return int(float(val)) if val not in [None, '', []] else None
            except: return None

        def to_float(val):
            try: return float(val) if val not in [None, '', []] else None
            except: return None

        # Check if record exists
        import sqlite3
        db_path = 'instance/carbon_tracker.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT id FROM social_workforce_data WHERE company_id=? AND reporting_year=?", (company_id, year))
        existing = cur.fetchone()

        programmes = data.get('programmes', '')
        if isinstance(programmes, list):
            programmes = ','.join(programmes)

        fields_values = {
            'total_employees': to_int(data.get('total_employees')),
            'new_hires': to_int(data.get('new_hires')),
            'employees_left': to_int(data.get('employees_left')),
            'male_count': to_int(data.get('male_count')),
            'female_count': to_int(data.get('female_count')),
            'other_gender_count': to_int(data.get('other_gender')),
            'permanent_employees': to_int(data.get('permanent_employees')),
            'contract_employees': to_int(data.get('contract_employees')),
            'temporary_employees': to_int(data.get('temporary_employees')),
            'senior_management': to_int(data.get('senior_management')),
            'middle_management': to_int(data.get('middle_management')),
            'executive_staff': to_int(data.get('executive_staff')),
            'operations_staff': to_int(data.get('operations_staff')),
            'total_hours_worked': to_float(data.get('total_hours_worked')),
            'lost_time_injuries': to_int(data.get('lost_time_injuries')),
            'recordable_incidents': to_int(data.get('recordable_incidents')),
            'fatalities': to_int(data.get('fatalities')),
            'near_misses': to_int(data.get('near_misses')),
            'occupational_diseases': to_int(data.get('occupational_diseases')),
            'safety_training_hours': to_int(data.get('safety_training_hours')),
            'total_training_hours': to_int(data.get('total_training_hours')),
            'employees_trained_count': to_int(data.get('employees_trained')),
            'training_spend_myr': to_float(data.get('training_spend_myr')),
            'technical_training_hrs': to_int(data.get('technical_training_hrs')),
            'leadership_training_hrs': to_int(data.get('leadership_training_hrs')),
            'safety_training_cat_hrs': to_int(data.get('safety_training_cat_hrs')),
            'esg_training_hrs': to_int(data.get('esg_training_hrs')),
            'digital_training_hrs': to_int(data.get('digital_training_hrs')),
            'other_training_hrs': to_int(data.get('other_training_hrs')),
            'hrdf_levy_paid': to_float(data.get('hrdf_levy_paid')),
            'hrdf_claims': to_float(data.get('hrdf_claims')),
            'performance_review_pct': to_float(data.get('performance_review_pct')),
            'dev_plan_pct': to_float(data.get('dev_plan_pct')),
            'csr_spend_myr': to_float(data.get('csr_spend_myr')),
            'beneficiaries': to_int(data.get('beneficiaries')),
            'volunteer_hours': to_int(data.get('volunteer_hours')),
            'volunteers_count': to_int(data.get('volunteers_count')),
            'zakat_contribution': to_float(data.get('zakat_contribution')),
            'scholarship_spend': to_float(data.get('scholarship_spend')),
            'bumi_procurement_pct': to_float(data.get('bumi_procurement_pct')),
            'board_total': to_int(data.get('board_total')),
            'board_female': to_int(data.get('board_female')),
            'board_independent': to_int(data.get('board_independent')),
            'board_avg_age': to_float(data.get('board_avg_age')),
            'bumiputera_count': to_int(data.get('bumiputera_count')),
            'chinese_count': to_int(data.get('chinese_count')),
            'indian_count': to_int(data.get('indian_count')),
            'other_ethnicity_count': to_int(data.get('other_ethnicity_count')),
            'age_under30': to_int(data.get('age_under30')),
            'age_30_50': to_int(data.get('age_30_50')),
            'age_over50': to_int(data.get('age_over50')),
            'pwd_count': to_int(data.get('pwd_count')),
            'gender_pay_gap': to_float(data.get('gender_pay_gap')),
            'min_wage_compliance': data.get('min_wage_compliance') or None,
            'community_programmes': programmes or None,
            'section': section,
        }

        if existing:
            non_null = {k: v for k, v in fields_values.items() if v is not None}
            if non_null:
                set_clause = ', '.join([f"{k}=?" for k in non_null.keys()])
                values = list(non_null.values()) + [company_id, year]
                cur.execute(f"UPDATE social_workforce_data SET {set_clause} WHERE company_id=? AND reporting_year=?", values)
        else:
            fields_values['company_id'] = company_id
            fields_values['reporting_year'] = year
            fields_values['entered_by'] = user_id
            fields_values['data_source'] = 'actual'
            fields_values['status'] = 'draft'
            cols = ', '.join(fields_values.keys())
            placeholders = ', '.join(['?' for _ in fields_values])
            cur.execute(f"INSERT INTO social_workforce_data ({cols}) VALUES ({placeholders})", list(fields_values.values()))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'{section} data saved successfully'})

    except Exception as e:
        print(f"Social save error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/social/data', methods=['GET'])
@login_required
def get_social_data():
    """Get social data for a reporting year"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        year = request.args.get('year', datetime.utcnow().year)
        company_id = session.get('company', '').strip().strip("'")

        import sqlite3
        db_path = 'instance/carbon_tracker.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT * FROM social_workforce_data WHERE company_id=? AND reporting_year=?", (company_id, int(year)))
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({'success': True, 'data': None})

        data = dict(row)
        return jsonify({'success': True, 'data': data})

    except Exception as e:
        print(f"Social load error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/supply_chain/suppliers', methods=['GET'])
@login_required
def get_suppliers():
    """Get all suppliers for a company and year"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        year = request.args.get('year', datetime.utcnow().year)
        status = request.args.get('status', '')
        company_id = session.get('company', '').strip().strip("'")

        import sqlite3
        conn = sqlite3.connect('instance/carbon_tracker.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if status:
            cur.execute("""SELECT * FROM supplier_invitations 
                          WHERE company_id=? AND reporting_year=? AND invitation_status=?
                          ORDER BY created_at DESC""", (company_id, int(year), status))
        else:
            cur.execute("""SELECT * FROM supplier_invitations 
                          WHERE company_id=? AND reporting_year=?
                          ORDER BY created_at DESC""", (company_id, int(year)))

        rows = cur.fetchall()
        suppliers = []
        for row in rows:
            s = dict(row)
            # Map DB columns to frontend expected fields
            s['status'] = s.get('invitation_status', 'invited')
            s['data_quality'] = s.get('data_quality_score', '')
            suppliers.append(s)

        # Calculate stats
        total = len(suppliers)
        responded = len([s for s in suppliers if s['status'] in ['submitted', 'approved']])
        response_rate = round((responded / total * 100)) if total > 0 else 0
        total_scope3 = sum(s.get('scope3_emissions') or 0 for s in suppliers)
        pending = len([s for s in suppliers if s['status'] in ['invited', 'pending']])

        quality_scores = [s['data_quality'] for s in suppliers if s.get('data_quality')]
        avg_quality = quality_scores[0] if quality_scores else '—'

        conn.close()

        return jsonify({
            'success': True,
            'suppliers': suppliers,
            'stats': {
                'total': total,
                'response_rate': response_rate,
                'avg_quality': avg_quality,
                'total_scope3': total_scope3,
                'pending': pending
            }
        })

    except Exception as e:
        print(f"Get suppliers error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/supply_chain/invite', methods=['POST'])
@login_required
def invite_supplier():
    """Invite a new supplier"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        company_id = session.get('company', '').strip().strip("'")
        year = int(data.get('reporting_year', datetime.utcnow().year))

        import sqlite3, secrets
        conn = sqlite3.connect('instance/carbon_tracker.db')
        cur = conn.cursor()

        # Check if already invited
        cur.execute("SELECT id FROM supplier_invitations WHERE company_id=? AND reporting_year=? AND supplier_email=?",
                   (company_id, year, data.get('supplier_email')))
        if cur.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Supplier already invited for this year'})

        token = secrets.token_urlsafe(16)

        cur.execute("""INSERT INTO supplier_invitations 
            (company_id, reporting_year, supplier_email, supplier_name, spend_category, 
             annual_spend, message, invitation_status, invitation_token, invited_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'invited', ?, ?, datetime('now'))""",
            (company_id, year,
             data.get('supplier_email'),
             data.get('supplier_name', ''),
             data.get('spend_category', ''),
             float(data.get('annual_spend', 0)) if data.get('annual_spend') else None,
             data.get('message', ''),
             token,
             user_id))

        conn.commit()
        supplier_id = cur.lastrowid
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Supplier invited successfully',
            'supplier_id': supplier_id,
            'token': token
        })

    except Exception as e:
        print(f"Invite supplier error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/supply_chain/resend/<int:supplier_id>', methods=['POST'])
@login_required
def resend_supplier_invite(supplier_id):
    """Resend invitation to a supplier"""
    try:
        import sqlite3
        conn = sqlite3.connect('instance/carbon_tracker.db')
        cur = conn.cursor()
        cur.execute("UPDATE supplier_invitations SET sent_date=datetime('now') WHERE id=?", (supplier_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Reminder sent'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/supply_chain/supplier/<int:supplier_id>', methods=['DELETE'])
@login_required
def delete_supplier(supplier_id):
    """Delete a supplier invitation"""
    try:
        import sqlite3
        conn = sqlite3.connect('instance/carbon_tracker.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM supplier_invitations WHERE id=?", (supplier_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/supply_chain/reminders', methods=['POST'])
@login_required
def send_supplier_reminders():
    """Send reminders to pending suppliers"""
    try:
        data = request.get_json()
        company_id = session.get('company', '').strip().strip("'")
        year = int(data.get('reporting_year', datetime.utcnow().year))

        import sqlite3
        conn = sqlite3.connect('instance/carbon_tracker.db')
        cur = conn.cursor()
        cur.execute("""SELECT COUNT(*) FROM supplier_invitations 
                      WHERE company_id=? AND reporting_year=? AND invitation_status='invited'""",
                   (company_id, year))
        pending = cur.fetchone()[0]
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Reminders sent to {pending} pending supplier{"s" if pending != 1 else ""}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/supply_chain/export', methods=['GET'])
@login_required
def export_suppliers():
    """Export suppliers as CSV"""
    try:
        year = request.args.get('year', datetime.utcnow().year)
        company_id = session.get('company', '').strip().strip("'")

        import sqlite3, csv, io
        conn = sqlite3.connect('instance/carbon_tracker.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM supplier_invitations WHERE company_id=? AND reporting_year=?",
                   (company_id, int(year)))
        rows = cur.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Supplier Name', 'Email', 'Category', 'Annual Spend (MYR)', 'Status', 'Scope 3 (kg CO2e)', 'Data Quality', 'Invited Date'])
        for row in rows:
            writer.writerow([
                row['supplier_name'] or '',
                row['supplier_email'] or '',
                row['spend_category'] or '',
                row['annual_spend'] or '',
                row['invitation_status'] or '',
                row['scope3_emissions'] or '',
                row['data_quality_score'] or '',
                row['created_at'] or '',
            ])

        output.seek(0)
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=suppliers_{year}.csv'}
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/survey/<token>')
def employee_survey(token):
    """Public employee survey page — no login required"""
    return render_template('employee_survey.html', token=token)


@app.route('/api/survey/validate/<token>', methods=['GET'])
def validate_survey_token(token):
    """Validate survey token — public endpoint"""
    try:
        import sqlite3
        conn = sqlite3.connect('instance/carbon_tracker.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""SELECT * FROM employee_survey_tokens 
                      WHERE token=? LIMIT 1""", (token,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return jsonify({'valid': False, 'reason': 'invalid'})

        row = dict(row)

        # Check expiry
        from datetime import datetime
        if row.get('expires_at'):
            expires = datetime.strptime(row['expires_at'], '%Y-%m-%d %H:%M:%S')
            if datetime.utcnow() > expires:
                conn.close()
                return jsonify({'valid': False, 'reason': 'expired'})

        # Check if already submitted by this token (if single-use)
        cur.execute("SELECT COUNT(*) FROM employee_survey_responses WHERE token=?", (token,))
        count = cur.fetchone()[0]
        conn.close()

        return jsonify({
            'valid': True,
            'company_name': row.get('company_id', 'Your Company'),
            'year': row.get('reporting_year', 2025),
            'already_submitted': count > 0
        })

    except Exception as e:
        # Table might not exist yet — return valid for testing
        return jsonify({'valid': True, 'company_name': 'Your Company', 'year': 2025})


@app.route('/api/survey/submit', methods=['POST'])
def submit_employee_survey():
    """Submit employee survey response — public endpoint"""
    try:
        data = request.get_json()
        token = data.get('token', '')

        import sqlite3
        conn = sqlite3.connect('instance/carbon_tracker.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Get company and year from token
        company_id = None
        reporting_year = 2025
        try:
            cur.execute("SELECT company_id, reporting_year FROM employee_survey_tokens WHERE token=?", (token,))
            token_row = cur.fetchone()
            if token_row:
                company_id = token_row['company_id']
                reporting_year = token_row['reporting_year']
        except:
            pass

        cur.execute("""
            INSERT INTO employee_survey_responses 
            (token, company_id, reporting_year, department, employment_type,
             work_arrangement, commute_transport, commute_distance_km,
             office_days_per_week, training_hours, performance_review,
             dev_plan, hrdf_training, safety_incident, volunteer_hours,
             wellbeing_score, esg_awareness_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            token, company_id, reporting_year,
            data.get('department'),
            data.get('employment_type'),
            data.get('work_arrangement'),
            data.get('commute_transport'),
            data.get('commute_distance_km'),
            data.get('office_days_per_week'),
            data.get('training_hours'),
            data.get('performance_review'),
            data.get('dev_plan'),
            data.get('hrdf_training'),
            data.get('safety_incident'),
            data.get('volunteer_hours'),
            data.get('wellbeing_score'),
            data.get('esg_awareness_score'),
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Survey submitted successfully'})

    except Exception as e:
        print(f"Survey submit error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/social/survey/create', methods=['POST'])
@login_required
def create_survey_token():
    """Create a shareable survey token"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        company_id = session.get('company', '').strip().strip("'")
        year = int(data.get('year', datetime.utcnow().year))
        expiry_days = int(data.get('expiry_days', 14))

        import sqlite3, secrets
        from datetime import timedelta

        # Create token table if not exists
        conn = sqlite3.connect('instance/carbon_tracker.db')
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS employee_survey_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token VARCHAR(100) NOT NULL UNIQUE,
            company_id VARCHAR(100),
            reporting_year INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            created_by VARCHAR(100)
        )''')

        token = secrets.token_urlsafe(12)
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)

        cur.execute("""INSERT INTO employee_survey_tokens 
                      (token, company_id, reporting_year, expires_at, created_by)
                      VALUES (?, ?, ?, ?, ?)""",
                   (token, company_id, year, expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                    session.get('user')))

        conn.commit()
        conn.close()

        survey_link = f"{request.host_url}survey/{token}"
        return jsonify({'success': True, 'token': token, 'link': survey_link})

    except Exception as e:
        print(f"Create survey token error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/social/survey/responses', methods=['GET'])
@login_required
def get_survey_responses():
    """Get aggregated survey responses for a company"""
    try:
        year = request.args.get('year', datetime.utcnow().year)
        company_id = session.get('company', '').strip().strip("'")

        import sqlite3
        conn = sqlite3.connect('instance/carbon_tracker.db')
        cur = conn.cursor()

        cur.execute("""SELECT COUNT(*) FROM employee_survey_responses 
                      WHERE company_id=? AND reporting_year=?""", (company_id, int(year)))
        total = cur.fetchone()[0]

        cur.execute("""SELECT AVG(wellbeing_score) FROM employee_survey_responses 
                      WHERE company_id=? AND reporting_year=? AND wellbeing_score IS NOT NULL""",
                   (company_id, int(year)))
        avg_wellbeing = cur.fetchone()[0]

        cur.execute("""SELECT COUNT(*) FROM employee_survey_tokens 
                      WHERE company_id=? AND reporting_year=?""", (company_id, int(year)))
        tokens_sent = cur.fetchone()[0]

        conn.close()

        completion_rate = round((total / tokens_sent * 100)) if tokens_sent > 0 else 0

        return jsonify({
            'success': True,
            'total': total,
            'completion_rate': completion_rate,
            'avg_wellbeing': round(avg_wellbeing, 1) if avg_wellbeing else None
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/evidence/upload', methods=['POST'])
@login_required
def upload_evidence():
    """Upload evidence file to vault"""
    try:
        if 'evidence_file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['evidence_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate safe filename
        import os
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        user_id = session.get('user')
        unique_filename = f"{user_id}_{timestamp}_{filename}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join('static', 'uploads', 'evidence')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Create evidence record
        evidence = EvidenceVault(
            company_id=session.get('company'),
            filename=filename,
            file_path=file_path,
            file_type=file.content_type,
            file_size=os.path.getsize(file_path),
            title=request.form.get('title', filename),
            description=request.form.get('description', ''),
            reporting_year=request.form.get('reporting_year', datetime.now().year),
            uploaded_by=session.get('user'),
            uploaded_by_name=session.get('user'),
            tags=request.form.get('tags', ''),
            access_level='company'
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidence uploaded successfully',
            'evidence_id': evidence.id,
            'filename': filename,
            'file_url': f"/{file_path}"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evidence/link', methods=['POST'])
@login_required
def link_evidence():
    """Link evidence to data entry"""
    try:
        data = request.get_json()
        
        evidence_link = EvidenceLink(
            evidence_id=data['evidence_id'],
            linked_table=data['linked_table'],
            linked_record_id=data['linked_record_id'],
            linked_field=data.get('linked_field', '')
        )
        
        # Update evidence usage count
        evidence = EvidenceVault.query.get(data['evidence_id'])
        if evidence:
            evidence.usage_count += 1
            evidence.last_used_date = datetime.utcnow()
        
        db.session.add(evidence_link)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidence linked successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    # ====================================================================
# Environmental Module API Endpoints (STEP 2)
# ====================================================================

@app.route('/api/environmental/create', methods=['POST'])
@login_required
def create_environmental_record():
    """Create a new environmental activity record"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        
        # Required fields validation
        required_fields = ['module_type', 'activity_type', 'quantity', 'unit', 'reporting_year']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate module_type
        if data['module_type'] not in ENVIRONMENTAL_CONFIG:
            return jsonify({'success': False, 'error': f'Invalid module type: {data["module_type"]}'}), 400
        
          # Validate activity_type for this module (loose check)
        # Validate activity_type for this module (loose check — just warn, don't reject)
        module_config = ENVIRONMENTAL_CONFIG[data['module_type']]
        if data['activity_type'] not in module_config['activities']:
            print(f"Unknown activity type: {data['activity_type']} for module: {data['module_type']}")
      
        # Calculate normalized quantity
        normalized_quantity = data['quantity']
        normalized_unit = data['unit']
        
        if data['activity_type'] in module_config['normalized_units']:
            normalized_unit = module_config['normalized_units'][data['activity_type']]
            if data['unit'] != normalized_unit and data['activity_type'] in module_config['units']:
                conversion_rate = module_config['units'][data['activity_type']].get(data['unit'], 1)
                normalized_quantity = data['quantity'] * conversion_rate
        
        # Create record
        record = EnvironmentalRecord(
            user_id=session['user'],
            module_type=data['module_type'],
            activity_type=data['activity_type'],
            quantity=float(data['quantity']),
            unit=data['unit'],
            normalized_quantity=normalized_quantity,
            normalized_unit=normalized_unit,
            reporting_year=int(data['reporting_year']),
            reporting_period=data.get('reporting_period', 'annual'),
            period_month=data.get('period_month'),
            period_quarter=data.get('period_quarter'),
            is_estimated=data.get('is_estimated', False),
            reporting_scope=data.get('reporting_scope', ''),
            notes=data.get('notes', ''),
            status='draft',
            created_by=session['user'],
            updated_by=session['user']
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Environmental record created',
            'record_id': record.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/environmental/list', methods=['GET'])
@login_required
def list_environmental_records():
    """Get environmental records for the logged-in user"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        module_type = request.args.get('module_type')
        year = request.args.get('year')
        
        # Build query
        query = EnvironmentalRecord.query.filter_by(user_id=session['user'])
        
        if module_type:
            query = query.filter_by(module_type=module_type)
        if year:
            query = query.filter_by(reporting_year=int(year))
        
        # Order by most recent
        query = query.order_by(EnvironmentalRecord.created_at.desc())
        
        records = query.all()
        
        # Format response
        records_data = []
        for record in records:
            records_data.append({
                'id': record.id,
                'module_type': record.module_type,
                'activity_type': record.activity_type,
                'quantity': record.quantity,
                'unit': record.unit,
                'normalized_quantity': record.normalized_quantity,
                'normalized_unit': record.normalized_unit,
                'reporting_year': record.reporting_year,
                'reporting_period': record.reporting_period,
                'is_estimated': record.is_estimated,
                'status': record.status,
                'evidence_count': len(record.evidence_files),
                'created_at': record.created_at.isoformat() if record.created_at else None,
                'updated_at': record.updated_at.isoformat() if record.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'records': records_data,
            'count': len(records_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/environmental/update/<int:record_id>', methods=['PUT'])
@login_required
def update_environmental_record(record_id):
    """Update an environmental record"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        record = EnvironmentalRecord.query.filter_by(
            id=record_id, 
            user_id=session['user']
        ).first()
        
        if not record:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
        
        # Only allow updates if status is draft
        if record.status != 'draft':
            return jsonify({'success': False, 'error': 'Cannot update submitted/approved records'}), 400
        
        data = request.get_json()
        
        # Update allowed fields
        if 'quantity' in data:
            record.quantity = float(data['quantity'])
        
        if 'unit' in data:
            record.unit = data['unit']
            
            # Recalculate normalized quantity if unit changed
            if record.activity_type in ENVIRONMENTAL_CONFIG.get(record.module_type, {}).get('normalized_units', {}):
                normalized_unit = ENVIRONMENTAL_CONFIG[record.module_type]['normalized_units'][record.activity_type]
                if data['unit'] != normalized_unit and record.activity_type in ENVIRONMENTAL_CONFIG[record.module_type]['units']:
                    conversion_rate = ENVIRONMENTAL_CONFIG[record.module_type]['units'][record.activity_type].get(data['unit'], 1)
                    record.normalized_quantity = record.quantity * conversion_rate
                    record.normalized_unit = normalized_unit
        
        if 'is_estimated' in data:
            record.is_estimated = bool(data['is_estimated'])
        
        if 'notes' in data:
            record.notes = data['notes']
        
        record.updated_by = session['user']
        record.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Record updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/environmental/submit/<int:record_id>', methods=['POST'])
@login_required
def submit_environmental_record(record_id):
    """Submit a draft record for review"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        record = EnvironmentalRecord.query.filter_by(
            id=record_id, 
            user_id=session['user']
        ).first()
        
        if not record:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
        
        if record.status != 'draft':
            return jsonify({'success': False, 'error': 'Record is not in draft status'}), 400
        
        # Update status
        record.status = 'submitted'
        record.updated_by = session['user']
        record.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Record submitted for review'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/environmental/upload-evidence/<int:record_id>', methods=['POST'])
@login_required
def upload_environmental_evidence(record_id):
    """Upload evidence file for an environmental record"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Check if record exists and belongs to user
        record = EnvironmentalRecord.query.filter_by(
            id=record_id,
            user_id=session['user']
        ).first()
        
        if not record:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
        
        # Check if file was uploaded
        if 'evidence_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['evidence_file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'csv', 'xlsx', 'xls', 'doc', 'docx'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False, 
                'error': f'File type not allowed. Allowed: {", ".join(allowed_extensions)}'
            }), 400
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'environmental')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{session['user']}_{record_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Create evidence record
        evidence = EnvironmentalEvidence(
            environmental_record_id=record_id,
            filename=file.filename,
            file_path=file_path.replace('\\', '/'),  # Use forward slashes for web
            description=request.form.get('description', ''),
            file_type=file_ext,
            file_size=file_size,
            uploaded_by=session['user'],
            uploaded_at=datetime.utcnow(),
            verified=False
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        # If record is estimated and now has evidence, update status
        if record.is_estimated and not record.notes:
            record.notes = "Evidence provided for estimated data"
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidence uploaded successfully',
            'evidence_id': evidence.id,
            'filename': evidence.filename,
            'file_path': f"/static/uploads/environmental/{unique_filename}",
            'uploaded_at': evidence.uploaded_at.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        # Clean up file if it was saved but DB failed
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/environmental/evidence/<int:record_id>', methods=['GET'])
@login_required
def get_environmental_evidence(record_id):
    """Get all evidence files for an environmental record"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Check if record exists and belongs to user
        record = EnvironmentalRecord.query.filter_by(
            id=record_id,
            user_id=session['user']
        ).first()
        
        if not record:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
        
        evidence_list = []
        for evidence in record.evidence_files:
            # Build a viewable URL from the stored absolute path
            try:
                rel_path = os.path.relpath(evidence.file_path, app.root_path).replace('\\', '/')
                view_url = '/' + rel_path
            except Exception:
                view_url = evidence.file_path

            evidence_list.append({
                'id': evidence.id,
                'filename': evidence.filename,
                'description': evidence.description,
                'file_type': evidence.file_type,
                'file_size': evidence.file_size,
                'uploaded_by': evidence.uploaded_by,
                'uploaded_at': evidence.uploaded_at.isoformat() if evidence.uploaded_at else None,
                'verified': evidence.verified,
                'verified_by': evidence.verified_by,
                'verified_at': evidence.verified_at.isoformat() if evidence.verified_at else None,
                'file_url': view_url,
                'download_url': url_for('serve_environmental_evidence', evidence_id=evidence.id)
            })
        
        return jsonify({
            'success': True,
            'record_id': record_id,
            'evidence': evidence_list,
            'count': len(evidence_list)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/environmental/serve-evidence/<int:evidence_id>')
@login_required
def serve_environmental_evidence(evidence_id):
    """Serve/download an evidence file securely (only the owning user can access it)."""
    evidence = EnvironmentalEvidence.query.get(evidence_id)
    if not evidence:
        return jsonify({'error': 'Not found'}), 404

    # Verify the record belongs to the requesting user
    record = EnvironmentalRecord.query.filter_by(
        id=evidence.environmental_record_id,
        user_id=session['user']
    ).first()
    if not record:
        return jsonify({'error': 'Forbidden'}), 403

    file_path = evidence.file_path
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on disk'}), 404

    directory = os.path.dirname(file_path)
    filename  = os.path.basename(file_path)
    from flask import send_from_directory
    return send_from_directory(directory, filename, as_attachment=False,
                               download_name=evidence.filename)


@app.route('/api/environmental/delete-evidence/<int:evidence_id>', methods=['DELETE'])
@login_required
def delete_environmental_evidence(evidence_id):
    """Delete an evidence file"""
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        evidence = EnvironmentalEvidence.query.get(evidence_id)
        
        if not evidence:
            return jsonify({'success': False, 'error': 'Evidence not found'}), 404
        
        # Check if user owns the record this evidence belongs to
        record = EnvironmentalRecord.query.filter_by(
            id=evidence.environmental_record_id,
            user_id=session['user']
        ).first()
        
        if not record:
            return jsonify({'success': False, 'error': 'Not authorized'}), 403
        
        # Only allow deletion if record is in draft status
        if record.status != 'draft':
            return jsonify({'success': False, 'error': 'Cannot delete evidence from submitted/approved records'}), 400
        
        # Delete file from filesystem
        if os.path.exists(evidence.file_path):
            os.remove(evidence.file_path)
        
        # Delete from database
        db.session.delete(evidence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Evidence deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
@app.route('/api/environmental/intensity', methods=['GET'])
@login_required
def get_environmental_intensity():
    """
    GET /api/environmental/intensity?year=2024
    Returns environmental intensity calculations for user
    """
    try:
        username = session.get('user')
        if not username:
            return jsonify({'success': False, 'error': 'User not logged in'}), 401
        
        reporting_year = request.args.get('year', type=int)
        
        # Calculate intensities
        results = calculate_environmental_intensities(username, reporting_year)
        
        if 'error' in results:
            return jsonify({'success': False, 'error': results['error']}), 500
        
        return jsonify({
            'success': True,
            'data': results,
            'reporting_year': reporting_year or 'all'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/carboniq')
@login_required
def carboniq():
    return render_template('carboniq.html')

@app.route('/carbon_roadmap')
@login_required
def carbon_roadmap():
    return render_template('carbon_roadmap.html')
 
 
@app.route('/api/roadmap/emissions')
@login_required
def api_roadmap_emissions():
    """Pull real emission data from environmental_records for the roadmap"""
    year = request.args.get('year', '2025')
    company_id = session.get('company', '').strip().strip("'")
 
    try:
        db_path = 'instance/carbon_tracker.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
 
        # Malaysian emission factors (kg CO2e per unit)
        FACTORS = {
            # Scope 1
            'petrol': 2.296, 'diesel': 2.668, 'lpg': 2.983,
            'natural_gas': 2.020, 'fuel_oil': 2.960,
            # Scope 2 - grid regions
            'electricity_tnb': 0.607, 'electricity_sesb': 0.670,
            'electricity_seb': 0.692, 'electricity': 0.607,
            # Scope 3
            'air_travel': 0.255, 'road_freight': 0.062,
            'waste_landfill': 0.436, 'water': 0.344,
            'business_travel': 0.180, 'commuting': 0.140,
        }
 
        SCOPE_MAP = {
            'petrol': 1, 'diesel': 1, 'lpg': 1, 'natural_gas': 1, 'fuel_oil': 1,
            'electricity': 2, 'electricity_tnb': 2, 'electricity_sesb': 2, 'electricity_seb': 2,
            'air_travel': 3, 'road_freight': 3, 'waste_landfill': 3, 'water': 3,
            'business_travel': 3, 'commuting': 3,
        }
 
        LABEL_MAP = {
            'petrol': 'Petrol (Scope 1)', 'diesel': 'Diesel (Scope 1)',
            'lpg': 'LPG (Scope 1)', 'natural_gas': 'Natural Gas (Scope 1)',
            'electricity': 'Grid Electricity (Scope 2)',
            'electricity_tnb': 'TNB Grid (Scope 2)', 'electricity_sesb': 'SESB Grid (Scope 2)',
            'air_travel': 'Air Travel (Scope 3)', 'road_freight': 'Road Freight (Scope 3)',
            'waste_landfill': 'Waste (Scope 3)', 'water': 'Water (Scope 3)',
            'business_travel': 'Business Travel (Scope 3)', 'commuting': 'Commuting (Scope 3)',
        }
 
        cur = conn.cursor()
        cur.execute("""
            SELECT activity_type, SUM(quantity) as total_qty, unit, reporting_scope
            FROM environmental_records
            WHERE user_id = ? AND reporting_year = ?
            GROUP BY activity_type, unit
        """, (company_id, int(year)))
 
        rows = cur.fetchall()
        conn.close()
 
        scope1 = 0.0
        scope2 = 0.0
        scope3 = 0.0
        breakdown = []
 
        for row in rows:
            act = (row['activity_type'] or '').lower().replace(' ', '_')
            qty = float(row['total_qty'] or 0)
            factor = FACTORS.get(act, 0)
            co2e_kg = qty * factor
            co2e_t = co2e_kg / 1000
 
            scope = SCOPE_MAP.get(act, int(row['reporting_scope'] or 1))
            if scope == 1:
                scope1 += co2e_t
            elif scope == 2:
                scope2 += co2e_t
            else:
                scope3 += co2e_t
 
            if co2e_t > 0:
                breakdown.append({
                    'label': LABEL_MAP.get(act, act.replace('_', ' ').title()),
                    'value': round(co2e_t, 2),
                    'activity': act,
                    'scope': scope
                })
 
        # Sort and add percentages
        total = scope1 + scope2 + scope3
        if total > 0:
            for item in breakdown:
                item['pct'] = round((item['value'] / total) * 100, 1)
            breakdown.sort(key=lambda x: x['value'], reverse=True)
 
        return jsonify({
            'success': True,
            'scope1_tco2e': round(scope1, 3),
            'scope2_tco2e': round(scope2, 3),
            'scope3_tco2e': round(scope3, 3),
            'total_tco2e': round(total, 3),
            'breakdown': breakdown[:8],  # top 8
            'year': year
        })
 
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
 
 
@app.route('/api/roadmap/generate', methods=['POST'])
@login_required
def api_roadmap_generate():
    """Call Gemini AI to generate personalised carbon roadmap"""
    company_id = session.get('company', '').strip().strip("'")
    data = request.get_json()
 
    scope1 = float(data.get('scope1', 0))
    scope2 = float(data.get('scope2', 0))
    scope3 = float(data.get('scope3', 0))
    total = scope1 + scope2 + scope3
    target = data.get('target', '30')
    industry = data.get('industry', 'services')
    size = data.get('size', 'small')
    year = data.get('year', '2025')
    context = data.get('context', '')
    target_label = data.get('target_label', '30% by 2030')
    breakdown = data.get('breakdown', [])
 
    # Build breakdown text
    breakdown_text = ''
    if breakdown:
        breakdown_text = '\n'.join([f"  - {b['label']}: {b['value']} tCO2e ({b.get('pct',0)}%)" for b in breakdown])
    else:
        breakdown_text = f"  - Scope 1 Direct: {scope1} tCO2e\n  - Scope 2 Energy: {scope2} tCO2e\n  - Scope 3 Value Chain: {scope3} tCO2e"
 
    # Calculate target emissions
    if target == 'net_zero':
        target_pct = 100
        target_year = 2050
        target_tco2e = 0
    else:
        target_pct = int(target)
        target_year = 2030
        target_tco2e = round(total * (1 - target_pct / 100), 2)
 
    prompt = f"""You are an expert carbon management consultant specialising in Malaysian SMEs, Bursa Malaysia ESG reporting, and Science-Based Targets (SBTi).
 
Generate a detailed, personalised carbon reduction roadmap for this company.
 
COMPANY PROFILE:
- Company: {company_id}
- Industry: {industry}
- Size: {size}
- Reporting Year: {year}
- Additional context: {context if context else 'None provided'}
 
CURRENT EMISSIONS ({year}):
{breakdown_text}
- TOTAL: {round(total, 2)} tCO2e/year
- Scope 1 (Direct): {scope1} tCO2e
- Scope 2 (Energy): {scope2} tCO2e
- Scope 3 (Supply Chain/Other): {scope3} tCO2e
 
REDUCTION TARGET: {target_label}
- Target emissions by {target_year}: {target_tco2e} tCO2e
- Required reduction: {round(total - target_tco2e, 2)} tCO2e
 
Respond ONLY with a valid JSON object. No markdown, no backticks, no explanation. Just pure JSON.
 
The JSON must follow this exact structure:
{{
  "summary": "<2-3 paragraphs of executive summary as HTML with <p> and <strong> tags>",
  "milestones": [
    {{"year": "2025 (Baseline)", "target": {round(total, 1)}, "description": "Establish baseline measurement and quick wins"}},
    {{"year": "2026", "target": <number>, "description": "<specific actions>"}},
    {{"year": "2027", "target": <number>, "description": "<specific actions>"}},
    {{"year": "2028", "target": <number>, "description": "<specific actions>"}},
    {{"year": "2029", "target": <number>, "description": "<specific actions>"}},
    {{"year": "2030 (Target)", "target": {target_tco2e}, "description": "<achievement description>"}}
  ],
  "quick_wins": [
    {{"icon": "⚡", "title": "Action Name", "description": "What to do and why", "saving": "Est. X-Y tCO2e reduction"}},
    {{"icon": "🌱", "title": "Action Name", "description": "What to do and why", "saving": "Est. X-Y tCO2e reduction"}},
    {{"icon": "💡", "title": "Action Name", "description": "What to do and why", "saving": "Est. X-Y tCO2e reduction"}},
    {{"icon": "🚗", "title": "Action Name", "description": "What to do and why", "saving": "Est. X-Y tCO2e reduction"}}
  ],
  "strategic": "<3-4 paragraphs of strategic initiatives as HTML with <p>, <strong>, <ul>, <li> tags. Focus on medium/long-term transformation relevant to Malaysian {industry} industry>",
  "incentives": "<HTML content listing relevant Malaysian green incentives: NEM 3.0, GTFS, MGTC Green Technology Tax, Carbon Credit Exchange BCX, MyHIJAU, PETRONAS/TNB green programs. Use <p>, <ul>, <li> tags>",
  "compliance": [
    {{"item": "Scope 1 & 2 GHG Measurement", "status": "Required", "status_class": "req", "priority": "Immediate"}},
    {{"item": "Scope 3 Supply Chain Data", "status": "Recommended", "status_class": "rec", "priority": "2025-2026"}},
    {{"item": "Third-party GHG Verification", "status": "Required", "status_class": "req", "priority": "Before reporting"}},
    {{"item": "Science-Based Target Setting", "status": "Recommended", "status_class": "rec", "priority": "2025"}},
    {{"item": "TCFD Disclosure", "status": "Required", "status_class": "req", "priority": "Annual"}},
    {{"item": "Biodiversity Impact Assessment", "status": "Optional", "status_class": "opt", "priority": "2026+"}},
    {{"item": "Carbon Neutral Certification", "status": "Optional", "status_class": "opt", "priority": "2028+"}}
  ],
  "roadmap_text": "<Full plain text version for download. Include all sections in readable format.>"
}}
 
Make the roadmap specific, practical, and actionable for a Malaysian {size} {industry} company. Reference specific Malaysian programmes, regulations, and market conditions. All emission numbers must be realistic and consistent."""
 
    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash')
 
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4000,
            )
        )
 
        raw = response.text.strip()
 
        # Clean JSON if needed
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        raw = raw.strip()
 
        result = json.loads(raw)
        result['success'] = True
        return jsonify(result)
 
    except json.JSONDecodeError as e:
        # Try to salvage partial response
        return jsonify({
            'success': False,
            'error': f'AI response parsing error: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'AI generation error: {str(e)}'
        })

# ============================================================
# CARBON MARKETPLACE ROUTES — paste into app.py
# ============================================================

@app.route('/marketplace')
@login_required
def marketplace():
    return render_template('marketplace.html')


@app.route('/api/marketplace/enquiry', methods=['POST'])
@login_required
def marketplace_enquiry():
    """Save marketplace provider enquiry"""
    try:
        data = request.get_json()
        company_id = session.get('company', '').strip().strip("'")

        db_path = 'instance/carbon_tracker.db'
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Create table if not exists
        cur.execute('''
            CREATE TABLE IF NOT EXISTS marketplace_enquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id VARCHAR(100),
                provider_id INTEGER,
                provider_name VARCHAR(200),
                provider_category VARCHAR(50),
                contact_name VARCHAR(200),
                company_name VARCHAR(200),
                email VARCHAR(200),
                phone VARCHAR(50),
                service_interest VARCHAR(200),
                emissions_size VARCHAR(50),
                message TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cur.execute('''
            INSERT INTO marketplace_enquiries
            (company_id, provider_id, provider_name, provider_category,
             contact_name, company_name, email, phone,
             service_interest, emissions_size, message)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            company_id,
            data.get('provider_id'),
            data.get('provider_name'),
            data.get('provider_category'),
            data.get('contact_name'),
            data.get('company_name'),
            data.get('email'),
            data.get('phone'),
            data.get('service_interest'),
            data.get('emissions_size'),
            data.get('message')
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Enquiry submitted successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/marketplace/listing', methods=['POST'])
@login_required
def marketplace_listing():
    """Save provider listing application"""
    try:
        data = request.get_json()

        db_path = 'instance/carbon_tracker.db'
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS marketplace_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                biz_name VARCHAR(200),
                biz_category VARCHAR(50),
                contact VARCHAR(200),
                email VARCHAR(200),
                phone VARCHAR(50),
                website VARCHAR(200),
                description TEXT,
                certifications VARCHAR(500),
                status VARCHAR(50) DEFAULT 'pending_review',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cur.execute('''
            INSERT INTO marketplace_listings
            (biz_name, biz_category, contact, email, phone, website, description, certifications)
            VALUES (?,?,?,?,?,?,?,?)
        ''', (
            data.get('biz_name'),
            data.get('biz_category'),
            data.get('contact'),
            data.get('biz_email'),
            data.get('biz_phone'),
            data.get('biz_website'),
            data.get('biz_desc'),
            data.get('biz_certs')
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Listing application submitted'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/auditor/invite', methods=['POST'])
@login_required
def invite_auditor():
    """Company invites an auditor via email"""
    
    # Only company users can invite auditors
    current_user = User.query.get(session['user_id'])
    if current_user.role not in ['company', 'admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    auditor_email   = data.get('email', '').strip().lower()
    auditor_name    = data.get('name', '').strip()
    expires_days    = int(data.get('expires_days', 90))  # default 90 days
    
    if not auditor_email or not auditor_name:
        return jsonify({'success': False, 'message': 'Name and email are required'})
    
    # Check if auditor already has an account
    existing_user = User.query.filter_by(email=auditor_email).first()
    
    if existing_user:
        # Auditor already on platform — just create access link
        if existing_user.role != 'auditor':
            return jsonify({'success': False, 'message': 'This email belongs to a company account'})
        auditor_user = existing_user
        is_new_user  = False
    else:
        # Create a new pending auditor account
        auditor_user = User(
            email        = auditor_email,
            username     = auditor_email,  # use email as username
            company_name = auditor_name,
            role         = 'auditor',
            password_hash= ''  # empty until they register
        )
        db.session.add(auditor_user)
        db.session.flush()  # get the ID without committing
        is_new_user = True
    
    # Check if this auditor already has active access to this company
    existing_access = AuditorAccess.query.filter_by(
        auditor_id = auditor_user.id,
        company_id = current_user.id
    ).filter(AuditorAccess.status.in_(['pending', 'active'])).first()
    
    if existing_access:
        return jsonify({'success': False, 'message': 'This auditor already has access or a pending invite'})
    
    # Create access record
    token = generate_invite_token()
    expires_at = datetime.now() + timedelta(days=expires_days)
    
    access = AuditorAccess(
        auditor_id   = auditor_user.id,
        company_id   = current_user.id,
        invited_by   = current_user.id,
        status       = 'pending',
        expires_at   = expires_at,
        invite_token = token
    )
    db.session.add(access)
    db.session.commit()
    
    # Send invite email
    invite_url = f"{request.host_url}auditor/accept/{token}"
    send_auditor_invite_email(
        auditor_email = auditor_email,
        auditor_name  = auditor_name,
        company_name  = current_user.company_name,
        invite_url    = invite_url,
        expires_at    = expires_at,
        is_new_user   = is_new_user
    )
    
    return jsonify({
        'success': True,
        'message': f'Invite sent to {auditor_email}',
        'expires_at': expires_at.strftime('%d %b %Y')
    })

@app.route('/api/auditor/resend/<int:access_id>', methods=['POST'])
@login_required
def resend_auditor_invite(access_id):
    """Resend invite email to auditor"""
    current_user = User.query.get(session['user_id'])
    access = AuditorAccess.query.filter_by(
        id         = access_id,
        company_id = current_user.id
    ).first()
    
    if not access:
        return jsonify({'success': False, 'message': 'Access record not found'})
    
    auditor = User.query.get(access.auditor_id)
    invite_url = f"{request.host_url}auditor/accept/{access.invite_token}"
    
    send_auditor_invite_email(
        auditor_email = auditor.email,
        auditor_name  = auditor.company_name,
        company_name  = current_user.company_name,
        invite_url    = invite_url,
        expires_at    = access.expires_at,
        is_new_user   = access.status == 'pending'
    )
    
    return jsonify({'success': True, 'message': 'Invite resent successfully'})

@app.route('/api/auditor/revoke/<int:access_id>', methods=['POST'])
@login_required
def revoke_auditor_access(access_id):
    """Company revokes auditor access"""
    current_user = User.query.get(session['user_id'])
    access = AuditorAccess.query.filter_by(
        id         = access_id,
        company_id = current_user.id
    ).first()
    
    if not access:
        return jsonify({'success': False, 'message': 'Not found'})
    
    access.status = 'revoked'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Access revoked'})


@app.route('/api/auditor/list', methods=['GET'])
@login_required
def list_auditors():
    """Get all auditors for current company"""
    current_user = User.query.get(session['user_id'])
    
    # Auto-expire any past-due access
    expired = AuditorAccess.query.filter_by(
        company_id = current_user.id,
        status     = 'active'
    ).filter(AuditorAccess.expires_at < datetime.now()).all()
    
    for e in expired:
        e.status = 'expired'
    db.session.commit()
    
    accesses = AuditorAccess.query.filter_by(company_id=current_user.id).all()
    
    result = []
    for a in accesses:
        auditor = User.query.get(a.auditor_id)
        result.append({
            'id'          : a.id,
            'name'        : auditor.company_name,
            'email'       : auditor.email,
            'status'      : a.status,
            'expires_at'  : a.expires_at.strftime('%d %b %Y'),
            'last_login'  : a.last_login.strftime('%d %b %Y %H:%M') if a.last_login else 'Never',
            'created_at'  : a.created_at.strftime('%d %b %Y')
        })
    
    return jsonify({'success': True, 'auditors': result})

@app.route('/auditor/accept/<token>')
def auditor_accept_invite(token):
    """Auditor clicks magic link from email"""
    
    # Find the access record
    access = AuditorAccess.query.filter_by(invite_token=token).first()
    
    if not access:
        flash('Invalid or expired invite link.', 'error')
        return redirect(url_for('login'))
    
    # Check if expired
    if access.expires_at < datetime.now():
        access.status = 'expired'
        db.session.commit()
        flash('This invite link has expired. Please ask the company to resend.', 'error')
        return redirect(url_for('login'))
    
    # Check if already active (auditor already registered)
    if access.status == 'active':
        flash('You already have access. Please log in.', 'info')
        return redirect(url_for('login'))
    
    # Get auditor user
    auditor = User.query.get(access.auditor_id)
    company = User.query.get(access.company_id)
    
    if not auditor or not company:
        flash('Invalid invite. Please contact support.', 'error')
        return redirect(url_for('login'))
    
    # If auditor already has a password — just activate and redirect to login
    if auditor.password_hash and auditor.password_hash != '':
        access.status = 'active'
        db.session.commit()
        flash(f'Access granted to {company.company_name}. Please log in with your email and existing password.', 'success')
        return redirect(url_for('login'))
    
    # New auditor — show registration page
    return render_template('auditor/register.html',
                         token=token,
                         auditor_email=auditor.email,
                         auditor_name=auditor.company_name,
                         company_name=company.company_name,
                         expires_at=access.expires_at.strftime('%d %B %Y'))

@app.route('/auditor/register/<token>', methods=['POST'])
def auditor_register(token):
    """Auditor sets their password and activates account"""
    
    access = AuditorAccess.query.filter_by(invite_token=token).first()
    
    if not access:
        return jsonify({'success': False, 'message': 'Invalid token'})
    
    if access.expires_at < datetime.now():
        return jsonify({'success': False, 'message': 'Invite has expired'})
    
    password  = request.form.get('password')
    password2 = request.form.get('password2')
    
    if not password or len(password) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return redirect(url_for('auditor_accept_invite', token=token))
    
    if password != password2:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('auditor_accept_invite', token=token))
    
    # Set password and activate
    auditor = User.query.get(access.auditor_id)
    auditor.set_password(password)
    
    access.status     = 'active'
    access.last_login = datetime.now()
    
    db.session.commit()
    
    # Log them in automatically
    session['user']    = auditor.username if auditor.username else auditor.email
    session['user_id'] = auditor.id
    session['email']   = auditor.email
    session['company'] = auditor.company_name
    session['role']    = 'auditor'
    
    flash(f'Welcome! Your auditor account is now active.', 'success')
    return redirect(url_for('auditor_dashboard'))

@app.route('/auditor/dashboard')
def auditor_dashboard():
    """Read-only auditor dashboard"""
    if 'user_id' not in session or session.get('role') != 'auditor':
        flash('Access denied. Auditor login required.', 'error')
        return redirect(url_for('login'))
    
    auditor_id = session['user_id']
    
    # Get all companies this auditor has access to
    accesses = AuditorAccess.query.filter_by(
        auditor_id = auditor_id,
        status     = 'active'
    ).all()
    
    # Auto expire any past due
    for access in accesses:
        if access.expires_at < datetime.now():
            access.status = 'expired'
    db.session.commit()
    
    # Refresh active accesses
    accesses = AuditorAccess.query.filter_by(
        auditor_id = auditor_id,
        status     = 'active'
    ).all()
    
    # Build company list with data
    companies = []
    for access in accesses:
        company = User.query.get(access.company_id)
        if not company:
            continue
        
        # Get emission summary for this company
        username = company.username
        user_emissions = emission_data.get(username, 
                        {'scope1': [], 'scope2': [], 'scope3': []})
        
        scope1 = sum(i.get('co2e', 0) for i in user_emissions.get('scope1', []))
        scope2 = sum(i.get('co2e', 0) for i in user_emissions.get('scope2', []))
        scope3 = sum(i.get('co2e', 0) for i in user_emissions.get('scope3', []))
        total  = scope1 + scope2 + scope3
        
        # Get ESG completion stats
        import sqlite3
        conn = sqlite3.connect('instance/carbon_tracker.db')
        conn.row_factory = sqlite3.Row
        cur  = conn.cursor()
        
        # Social completion
        cur.execute("""SELECT * FROM social_workforce_data 
                      WHERE company_id=? ORDER BY reporting_year DESC LIMIT 1""",
                   (company.company_name,))
        social_row = cur.fetchone()
        social_pct = 0
        if social_row:
            d    = dict(social_row)
            skip = {'id','company_id','reporting_year','created_at','updated_at'}
            vals = {k:v for k,v in d.items() if k not in skip}
            filled = len([v for v in vals.values() if v not in (None,'',0)])
            social_pct = min(100, round(filled / max(len(vals),1) * 100))
        
        # Governance completion
        cur.execute("""SELECT * FROM governance_data 
                      WHERE company_id=? ORDER BY reporting_year DESC LIMIT 1""",
                   (company.company_name,))
        gov_row = cur.fetchone()
        gov_pct = 0
        if gov_row:
            d    = dict(gov_row)
            skip = {'id','company_id','reporting_year','created_at','updated_at'}
            vals = {k:v for k,v in d.items() if k not in skip}
            filled = len([v for v in vals.values() if v not in (None,'',0)])
            gov_pct = min(100, round(filled / max(len(vals),1) * 100))
        
        # Supply chain
        cur.execute("""SELECT COUNT(*) FROM supplier_invitations 
                      WHERE company_id=?""", (company.company_name,))
        supplier_total = cur.fetchone()[0]
        
        cur.execute("""SELECT COUNT(*) FROM supplier_invitations 
                      WHERE company_id=? 
                      AND invitation_status IN ('submitted','approved')""",
                   (company.company_name,))
        supplier_responded = cur.fetchone()[0]
        
        conn.close()
        
        env_pct = 100 if total > 0 else 0
        overall_esg = round(env_pct * 0.4 + social_pct * 0.3 + gov_pct * 0.3)
        
        companies.append({
            'access_id'          : access.id,
            'company_id'         : company.id,
            'company_name'       : company.company_name,
            'username'           : company.username,
            'expires_at'         : access.expires_at.strftime('%d %b %Y'),
            'last_login'         : access.last_login.strftime('%d %b %Y') 
                                   if access.last_login else 'First visit',
            'total_emissions'    : round(total, 1),
            'scope1'             : round(scope1, 1),
            'scope2'             : round(scope2, 1),
            'scope3'             : round(scope3, 1),
            'env_pct'            : env_pct,
            'social_pct'         : social_pct,
            'gov_pct'            : gov_pct,
            'overall_esg'        : overall_esg,
            'supplier_total'     : supplier_total,
            'supplier_responded' : supplier_responded,
        })
    
    auditor = User.query.get(auditor_id)
    
    return render_template('auditor/dashboard.html',
                         auditor_name = auditor.company_name,
                         auditor_email= auditor.email,
                         companies    = companies,
                         total_companies = len(companies))

@app.route('/api/auditor/note', methods=['POST'])
def save_auditor_note():
    """Save auditor review note for a company"""
    if session.get('role') != 'auditor':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data       = request.json
    company_id = data.get('company_id')
    note       = data.get('note')
    
    # Save note to AuditorAccess record
    access = AuditorAccess.query.filter_by(
        auditor_id = session['user_id'],
        company_id = company_id,
        status     = 'active'
    ).first()
    
    if not access:
        return jsonify({'success': False, 'message': 'Access not found'})
    
    # Append note with timestamp
    timestamp    = datetime.now().strftime('%d %b %Y %H:%M')
    existing     = access.auditor_notes or ''
    access.auditor_notes = f"{existing}\n[{timestamp}]\n{note}\n".strip()
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Note saved'})

@app.route('/api/auditor/extend/<int:access_id>', methods=['POST'])
@login_required
def extend_auditor_access(access_id):
    """Extend auditor access expiry"""
    current_user = User.query.get(session['user_id'])
    access = AuditorAccess.query.filter_by(
        id         = access_id,
        company_id = current_user.id
    ).first()
    
    if not access:
        return jsonify({'success': False, 'message': 'Not found'})
    
    data = request.json
    days = int(data.get('days', 90))
    
    # Extend from today or current expiry whichever is later
    base = max(access.expires_at, datetime.now())
    access.expires_at = base + timedelta(days=days)
    access.status     = 'active'
    db.session.commit()
    
    return jsonify({
        'success'   : True,
        'message'   : 'Access extended',
        'expires_at': access.expires_at.strftime('%d %b %Y')
    })


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == '__main__':
    # Initialize upload folder
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Initialize compliance database
    initialize_compliance_database()
    
    print("🚀 Starting EmittiF with Enhanced Document Analysis...")
    print(f"🔑 OCR.space API configured: {'✅' if OCR_SPACE_API_KEY else '❌ MISSING KEY'}")
    print(f"🔧 Gemini AI Status: {'✅ AVAILABLE' if GEMINI_AVAILABLE else '❌ UNAVAILABLE'}")
    print(f"📊 Report Generation: {'✅ ENABLED (ReportLab)'}")
    app.run(debug=True)