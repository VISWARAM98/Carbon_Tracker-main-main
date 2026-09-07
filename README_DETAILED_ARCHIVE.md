# 🌱 EmittiF.io - Carbon Tracker Platform

## Project Overview

**EmittiF.io** is an advanced **Flask-based carbon emission management platform** designed to help organizations track, measure, and reduce their carbon footprint across three scopes (Scope 1, 2, and 3) in compliance with international standards like GRI (Global Reporting Initiative) and the GHG Protocol.

The platform combines:
- ✅ Real-time emission tracking and calculation
- ✅ AI-powered consultation (Google Gemini integration)
- ✅ Document analysis with OCR (Tesseract)
- ✅ GRI & GHG Protocol compliant reporting
- ✅ Interactive dashboards and visualizations
- ✅ Carbon marketplace and offset opportunities
- ✅ Regulatory compliance guidance (Malaysia-focused)
- ✅ **NEW**: Comprehensive compliance management system with standards tracking

---

## ✨ **What's New** (January 2026 Update - Final Phase)

### **CRITICAL BUG FIXES** 🔧
1. **Fixed Jinja2 Template Caching Issue**
   - Root cause: Jinja2 template bytecode cache serving stale compiled versions
   - Solution: Added `app.jinja_env.cache = None` to disable template caching in development
   - Impact: Ensures templates always load fresh from disk

2. **Fixed ESG Module Route Resolution**
   - Issue: Template was calling `url_for('environmental_module')` but route didn't exist
   - Solution: Added 4 new compatibility redirect routes
   - New Routes Added:
     - `/environmental-module` → `environmental_module()` → redirects to `esg_environmental`
     - `/social-module` → `social_module()` → redirects to `esg_social`
     - `/governance-module` → `governance_module()` → redirects to `esg_governance`
     - `/supply-chain-module` → `supply_chain_module()` → redirects to `esg_supply_chain`
   - Impact: ESG Data Center module cards now route correctly

3. **Optimized Gemini Model Initialization**
   - Issue: Verbose model listing causing slow startup
   - Solution: Commented out verbose logging to speed up Flask initialization
   - Impact: Flask starts ~30 seconds faster

4. **Added Missing Dependency**
   - Installed: `reportlab` package for PDF generation
   - Status: PDF report generation now fully functional

### **Compliance Management System** 📦
This update introduces a **complete compliance management system** for regulatory standards tracking and evidence management:

### **New Database Models** 📦
- **ComplianceStandard**: 9+ international and local standards (IFRS S1/S2, TCFD, ISO 14064, GHG Protocol, GRI, MGTC, SEDA)
- **ComplianceClause**: ~45 individual clauses/requirements across standards
- **UserComplianceStatus**: Track compliance status for each clause (compliant, partial, non-compliant)
- **EvidenceFile**: Manage supporting documents for audit trail
- **ClauseMapping**: Cross-reference requirements between standards
- **UserProfile**: Extended user information with ESG responsibilities and authority levels
- **CompanySettings**: Organization-wide compliance configuration and reporting parameters

### **New API Endpoints** 🔌
- `GET /api/compliance/matrix` - Complete compliance matrix
- `GET /api/compliance/standard/<id>` - Standard-specific clauses
- `GET /api/compliance/clause/<id>` - Clause details with evidence
- `POST /api/compliance/update-status` - Update assessment status
- `POST /api/compliance/upload-evidence` - Upload supporting documents
- `POST /api/compliance/generate-report` - Generate compliance reports
- `GET /api/compliance/mapping/<id>` - View clause mappings across standards

### **Enhanced Compliance Dashboard** 🎯
- Compliance matrix with 9 standards and ~45 clauses
- Real-time compliance scoring (0-100%)
- Evidence management system
- Deadline tracking with alerts
- Standards mapping to show overlapping requirements
- Audit trail with user actions and timestamps
- Compliance report generation for auditors

### **Key Features Added**
- 🗄️ Full SQLAlchemy ORM database support
- 📊 Compliance percentage calculations per standard
- 📁 Evidence file upload and verification system
- 🔗 Clause mapping across different standards
- 📋 Audit-ready compliance reports
- 🇲🇾 Malaysia-specific standards (MGTC, SEDA)
- ✔️ Comprehensive assessment status tracking

---

## 📍 **Complete Website Features & Functions** (Current Implementation)

This section documents ALL working features and pages of the Carbon Tracker platform as of January 2026.

### **SECTION 1: PUBLIC PAGES** (No Login Required)

#### **1.1 Landing Page** (`/`)
- **File**: `templates/index.html`
- **Functions**:
  - ✅ Hero section with call-to-action
  - ✅ About Us section with company vision
  - ✅ "What is Carbon?" educational content
  - ✅ Services overview (7 main services)
  - ✅ Contact section
  - ✅ Responsive navigation with CTA buttons
  - ✅ Login/Register navigation in header
  - ✅ Get Started button for non-logged-in users

**Key Buttons**:
- 📝 "Get Started Today" → `/register`
- 🔑 "Login" → `/login`
- 📊 "Go to Dashboard" (if logged in) → `/dashboard`

---

### **SECTION 2: AUTHENTICATION** (Public Pages)

#### **2.1 Register Page** (`/register`)
- **File**: `templates/auth/register.html`
- **Functions**:
  - ✅ Create new user account
  - ✅ Form validation (username, email, password, company)
  - ✅ Password hashing with Werkzeug
  - ✅ Duplicate username checking
  - ✅ Empty emission data initialization
  - ✅ Redirect to login after registration

**Form Fields**:
- Username (unique)
- Email address
- Company name
- Password
- Confirm password

**Backend Route**: `@app.route('/register', methods=['GET', 'POST'])`

---

#### **2.2 Login Page** (`/login`)
- **File**: `templates/auth/login.html`
- **Functions**:
  - ✅ User authentication with username/password
  - ✅ Session management (user, email, company stored)
  - ✅ Password verification with hashing
  - ✅ Redirect to dashboard on success
  - ✅ Error flash messages for invalid credentials
  - ✅ Link to registration for new users
  - ✅ Link back to home page

**Form Fields**:
- Username
- Password

**Backend Route**: `@app.route('/login', methods=['GET', 'POST'])`

---

#### **2.3 Logout** (`/logout`)
- **Function**: Clear user session and redirect to home
- **Backend Route**: `@app.route('/logout')`
- ✅ Flash confirmation message

---

### **SECTION 3: AUTHENTICATED PAGES** (Login Required)

#### **3.1 Dashboard** (`/dashboard`)
- **File**: `templates/dashboard.html`
- **Functions**:
  - ✅ Main carbon tracking hub
  - ✅ Quick stats cards (4 KPI cards)
  - ✅ Chart.js visualizations
  - ✅ Real-time emission calculations
  - ✅ Monthly trend analysis
  - ✅ Scope breakdown by source
  - ✅ Add emission data modal
  - ✅ Download PDF reports

**Key Components**:
- 📊 **Total Emissions Card**: Sum of all scopes
- 💳 **Carbon Traded Card**: Credit trading stats
- 🌳 **Carbon Offset Card**: Offset purchases
- ⭐ **Carbon Credited Card**: Credits earned

**Charts**:
- 📈 **Bar Chart**: Scope 1, 2, 3 comparison
- 📉 **Line Chart**: Monthly trends (6 months)
- 🥧 **Pie Chart 1**: Scope 1 breakdown
- 🥧 **Pie Chart 2**: Scope 2 breakdown
- 🥧 **Pie Chart 3**: Scope 3 breakdown

**Action Buttons**:
- ➕ **"Add Emission Data"** → Opens modal for manual entry
- 📄 **"My Report"** → Navigate to `/report`
- 📥 **"Download Report"** → Trigger `/api/generate-report-pdf`

**Backend Route**: `@app.route('/dashboard')`

---

#### **3.2 AI Consultant** (`/ai-consultant`)
- **File**: `templates/ai_consultant.html`
- **Functions**:
  - ✅ AI-powered carbon advice
  - ✅ Emission pattern analysis
  - ✅ Personalized recommendations
  - ✅ Industry best practices
  - ✅ Real-time AI responses
  - ✅ Context-aware suggestions

**Key Features**:
- 🤖 Powered by Google Gemini API
- 📊 Emission analysis dashboard
- 💡 Smart recommendations
- 📈 Trend insights
- 🎯 Priority actions

**Backend Route**: `@app.route('/ai-consultant')`

**API Endpoint**: `@app.route('/api/gemini-advice', methods=['POST'])`

---

#### **3.3 Carbon Sentinel (AI Chat)** (`/sentinel`)
- **File**: `templates/sentinel.html`
- **Functions**:
  - ✅ Real-time AI chat interface
  - ✅ Carbon Q&A responses
  - ✅ Contextual emission analysis
  - ✅ Compliance guidance
  - ✅ Reduction strategies
  - ✅ Malaysia-specific advice

**Features**:
- 💬 Chat-based interface
- 🔄 Multi-turn conversations
- 📋 Priority actions list
- 🔗 Framework references
- 🌍 Global & local guidance

**Backend Route**: `@app.route('/sentinel')`

---

#### **3.4 GRI/GHG Report Generator** (`/report`)
- **File**: `templates/report.html`
- **Functions**:
  - ✅ Generate GRI-compliant reports
  - ✅ GHG Protocol alignment
  - ✅ 8+ report sections
  - ✅ Company information
  - ✅ Emission inventory
  - ✅ Performance metrics
  - ✅ Risk assessment
  - ✅ PDF export

**Report Sections**:
1. Report Metadata (ID, date, version)
2. Organizational Information (GRI 102)
3. GHG Protocol Compliance
4. Emissions Inventory
5. Performance Metrics (GRI 305)
6. Management Approach
7. Risk Assessment
8. Data Quality & Recommendations

**Action Buttons**:
- 📥 **"Download Report (PDF)"** → `/api/generate-report-pdf`
- 📋 **"View Full Report"** → Display HTML version
- 📊 **"View Report Data"** → `/api/report-data`

**Backend Routes**:
- `@app.route('/report')`
- `@app.route('/api/generate-report-pdf')`
- `@app.route('/api/report-data')`

---

#### **3.5 Marketplace** (`/marketplace`)
- **File**: `templates/marketplace.html`
- **Status**: 🟡 Partially implemented
- **Functions**:
  - ✅ Carbon credit marketplace UI
  - ✅ Browse offset projects
  - 🟡 Trading interface (placeholder)
  - 🟡 Portfolio management (placeholder)
  - 🟡 Payment integration (not yet)

**Backend Route**: `@app.route('/marketplace')`

---

#### **3.6 Services Overview** (`/services`)
- **File**: `templates/services.html`
- **Functions**:
  - ✅ Platform services overview
  - ✅ 7 main service cards
  - ✅ Feature descriptions
  - ✅ Benefits highlighting

**Services Listed**:
1. 🧮 Emission Calculation
2. 📊 Analytics Dashboard
3. 🤖 AI Consultant
4. 📄 GRI Reporting
5. 📸 Document Analysis (OCR)
6. 🌳 Carbon Marketplace
7. 🔐 Verification Mode

**Backend Route**: `@app.route('/services')`

---

#### **3.7 Compliance Dashboard** (`/compliance_dashboard`)
- **File**: `templates/compliance_dashboard.html`
- **Functions**:
  - ✅ Standards compliance tracker
  - ✅ 9 standards & frameworks
  - ✅ ~45 individual clauses
  - ✅ Compliance scoring (0-100%)
  - ✅ Status tracking (compliant, partial, non-compliant)
  - ✅ Evidence management
  - ✅ Deadline tracking
  - ✅ Audit trail
  - ✅ Report generation

**Standards Tracked**:

**International Standards** 🌍:
- IFRS S1 (General Requirements)
- IFRS S2 (Climate-related)
- TCFD (Climate Risk)
- ISO 14064 (GHG Accounting)
- GHG Protocol
- GRI Standards

**Malaysia-Specific** 🇲🇾:
- MGTC (Green Technology)
- SEDA (Sustainable Energy)
- Carbon Tax Readiness

**Key Metrics**:
- Overall Compliance Score
- Standards Breakdown
- Evidence Count
- Deadline Status
- Activity Audit Log

**Action Buttons**:
- 📋 **"Generate Compliance Report"** → PDF export
- 🎓 **"View Guidelines"** → Documentation
- 🔔 **"Set Reminders"** → Deadline alerts
- 📞 **"Contact Consultant"** → Support request
- 🔍 **"View Mapping"** → Cross-standard relationships

**Backend Route**: `@app.route('/compliance_dashboard')`

**API Endpoints**:
- `@app.route('/api/compliance/matrix')`
- `@app.route('/api/compliance/standard/<id>')`
- `@app.route('/api/compliance/clause/<id>')`
- `@app.route('/api/compliance/update-status', methods=['POST'])`
- `@app.route('/api/compliance/upload-evidence', methods=['POST'])`
- `@app.route('/api/compliance/mapping/<id>')`
- `@app.route('/api/compliance/generate-report', methods=['POST'])`

---

### **SECTION 4: DATA MANAGEMENT FEATURES**

#### **4.1 Emission Data Entry**
- **API Endpoint**: `POST /api/add-emission`
- **Functions**:
  - ✅ Manual emission data entry
  - ✅ Scope selection (1, 2, 3)
  - ✅ Category selection
  - ✅ Activity data input
  - ✅ Unit selection
  - ✅ Automatic CO₂e calculation
  - ✅ Data storage in session

**Calculation**: `CO₂e = activity_data × emission_factor`

**Response**: JSON with calculated CO₂e and confirmation

---

#### **4.2 Document Analysis & OCR** (Source Documents)
- **File**: `templates/source_documents.html`
- **API Endpoint**: `POST /api/analyze-document`
- **Functions**:
  - ✅ Upload PDF or image files
  - ✅ Extract text with Tesseract OCR
  - ✅ Automatic data parsing
  - ✅ Emission detection
  - ✅ Scope assignment
  - ✅ Confidence scoring
  - ✅ Manual override option
  - ✅ Fallback to PyPDF2

**Supported Files**:
- 📄 PDF documents
- 🖼️ Images (PNG, JPG, JPEG)

**Processing Pipeline**:
1. File upload
2. Text extraction (Tesseract or PyPDF2)
3. Pattern analysis
4. Emission data parsing
5. CO₂e calculation
6. Results display
7. User confirmation/edit

---

#### **4.3 ESG Data Center** (`/esg-data-center`)
- **File**: `templates/esg_data_center.html`
- **Status**: ✅ **FULLY FIXED** (January 2026)
- **Functions**:
  - ✅ ESG data hub with 4 main modules
  - ✅ Completion tracking & progress statistics
  - ✅ Recent activity log with timestamps
  - ✅ Module navigation with card-based UI
  - ✅ Data entry guidance
  - ✅ Quick stats dashboard (72% overall completion)
  - ✅ Evidence file linking system

**ESG Modules** (All Functional):
- 🌱 **Environmental** (85% complete) → `/environmental-module` or `/esg-environmental`
  - Tracks emissions, energy consumption, water usage, waste management
- 👥 **Social & Workforce** (65% complete) → `/social-module` or `/esg-social`
  - Tracks employees, safety, training, community engagement
- ⚖️ **Governance** (45% complete) → `/governance-module` or `/esg-governance`
  - Tracks risk, compliance, ethics, board composition
- 🏭 **Supply Chain** (30% complete) → `/supply-chain-module` or `/esg-supply-chain`
  - Tracks Scope 3 emissions, supplier data, supply chain risks
- **Overall Completion**: 56% complete

**Backend Routes**:
- `@app.route('/esg-data-center')` - Main hub page
- `@app.route('/environmental-module')` → `environmental_module()` - Redirect to ESG Environmental
- `@app.route('/social-module')` → `social_module()` - Redirect to ESG Social
- `@app.route('/governance-module')` → `governance_module()` - Redirect to ESG Governance
- `@app.route('/supply-chain-module')` → `supply_chain_module()` - Redirect to ESG Supply Chain
- `@app.route('/esg-environmental')` → `esg_environmental()` - Environmental module page
- `@app.route('/esg-social')` → `esg_social()` - Social module page
- `@app.route('/esg-governance')` → `esg_governance()` - Governance module page
- `@app.route('/esg-supply-chain')` → `esg_supply_chain()` - Supply Chain module page

**API Endpoints**:
- `POST /api/esg/save-data` - Save ESG environmental data
- `POST /api/esg/save-social-data` - Save social & workforce data
- `POST /api/evidence/upload` - Upload supporting evidence files
- `POST /api/evidence/link` - Link evidence to clauses

**Bug Fix Details** (January 2026):
- ✅ Fixed missing route endpoints for module navigation
- ✅ Added compatibility redirect routes for template flexibility
- ✅ All 4 module cards now properly route to their respective pages
- ✅ Error "BuildError: Could not build url for endpoint 'environmental_module'" **RESOLVED**
- ✅ Jinja2 template caching issue **FIXED**

---

### **SECTION 5: USER SETTINGS & MANAGEMENT**

#### **5.1 Profile Settings** (`/profile_settings`)
- **File**: `templates/profile_settings.html`
- **Status**: 🟡 Partially implemented
- **Functions**:
  - ✅ User profile information
  - ✅ ESG responsibilities
  - ✅ Authority level setting
  - ✅ Declaration acceptance
  - ✅ Contact information
  - ✅ Audit trail

**Fields**:
- Full legal name
- Phone number
- Job title
- Department
- ESG responsibilities (multi-select)
- Authority level (Data Entry, Reviewer, Approver)
- Declaration acceptance

**Backend Route**: `@app.route('/profile_settings', methods=['GET', 'POST'])`

---

#### **5.2 Company Settings** (`/company_settings`)
- **File**: `templates/company_settings.html`
- **Status**: 🟡 Partially implemented
- **Functions**:
  - ✅ Organization configuration
  - ✅ Reporting parameters
  - ✅ Boundary definitions
  - ✅ Policy document links
  - ✅ ESG committee info
  - ✅ Audit mode toggle

**Fields**:
- Legal company name
- Registration number
- Industry classification
- Financial year dates
- Reporting boundary method
- Number of operational sites
- Board oversight status
- ESG committee existence
- External assurance status
- Policy URLs
- Audit mode enable/disable

**Backend Route**: `@app.route('/company_settings', methods=['GET', 'POST'])`

---

### **SECTION 6: ADVANCED FEATURES & MODULES**

#### **6.1 Supplier Portal** (`/supplier_portal`)
- **File**: `templates/supplier_portal.html`
- **Status**: 🟡 Placeholder/In-Progress
- **Functions**:
  - ✅ B2B supplier interface
  - 🟡 Scope 3 data collection (planned)
  - 🟡 Supplier collaboration (planned)
  - 🟡 Invitation system (partially implemented)
  - 🟡 Performance tracking (planned)

**Backend Support**:
- `@app.route('/api/esg/invite-supplier', methods=['POST'])`

---

#### **6.2 Verification Mode** (`/verification_mode`)
- **File**: `templates/verification_mode.html`
- **Status**: 🟡 Placeholder
- **Functions**:
  - 🟡 Third-party audit mode (planned)
  - 🟡 Digital signatures (planned)
  - 🟡 Audit workflows (planned)
  - 🟡 Compliance certification (planned)

---

#### **6.3 Audit Trail** (`/audit_trail`)
- **File**: `templates/audit_trail.html`
- **Status**: 🟡 Partially implemented
- **Functions**:
  - ✅ Immutable logging template
  - ✅ Activity tracking structure
  - 🟡 Real-time logging (planned)
  - 🟡 Change history (in progress)
  - 🟡 User attribution (planned)

---

#### **6.4 Carbon Tax Modeling** (`/carbon_tax_modeling`)
- **File**: `templates/carbon_tax_modeling.html`
- **Status**: 🟡 Placeholder
- **Functions**:
  - 🟡 Tax scenario modeling (planned)
  - 🟡 Cost calculations (planned)
  - 🟡 Reduction impact analysis (planned)
  - 🟡 Malaysia-specific tax rates (planned)

---

#### **6.5 Courses & Training** (`/courses`)
- **File**: `templates/courses.html`
- **Status**: 🟡 Placeholder/Coming Soon
- **Functions**:
  - 🟡 Carbon education modules (planned)
  - 🟡 Video tutorials (planned)
  - 🟡 Certification programs (planned)
  - 🟡 Progress tracking (planned)

---

#### **6.6 Malaysia Reports** (`/malaysian_reports`)
- **File**: `templates/malaysian_reports.html`
- **Status**: 🟡 Partially implemented
- **Functions**:
  - ✅ Malaysia-specific reporting
  - ✅ Report template selection
  - ✅ Framework support (NSRF, SEDG)
  - 🟡 Report generation (in progress)
  - 🟡 Template customization (planned)

**Frameworks**:
- NSRF (National Sustainability Reporting Framework)
- SEDG (Sustainable Energy Development Guidelines)

---

#### **6.7 Supplier Submission** (`/supplier_submission`)
- **File**: `templates/supplier_submission.html`
- **Status**: 🟡 Placeholder
- **Functions**:
  - 🟡 Supplier data submission (planned)
  - 🟡 Scope 3 data entry (planned)
  - 🟡 Format standardization (planned)
  - 🟡 Validation workflows (planned)

---

### **SECTION 7: ADDITIONAL FEATURES**

#### **7.1 Environmental Module** (`/esg-environmental`)
- **File**: `templates/environmental_module.html`
- **Status**: 🟡 Under Development
- **Functions**:
  - 🟡 Energy consumption tracking
  - 🟡 Waste management
  - 🟡 Water usage
  - 🟡 Emissions data entry

---

#### **7.2 Social Module** (`/esg-social`)
- **File**: `templates/social_module.html`
- **Status**: 🟡 Under Development
- **Functions**:
  - 🟡 Workforce data
  - 🟡 Diversity metrics
  - 🟡 Health & safety
  - 🟡 Community engagement

---

#### **7.3 Governance Module** (`/esg-governance`)
- **File**: `templates/governance_module.html`
- **Status**: 🟡 Under Development
- **Functions**:
  - 🟡 Board composition
  - 🟡 Ethics & compliance
  - 🟡 Risk management
  - 🟡 Stakeholder engagement

---

#### **7.4 Supply Chain Module** (`/esg-supply-chain`)
- **File**: `templates/supply_chain_module.html`
- **Status**: 🟡 Under Development
- **Functions**:
  - 🟡 Scope 3 tracking
  - 🟡 Supplier management
  - 🟡 Product lifecycle
  - 🟡 Logistics optimization

---

---

## ✅ **Feature Summary Table**

| Feature | Status | Module | Page |
|---------|--------|--------|------|
| **User Authentication** | ✅ Working | Auth | /login, /register |
| **Dashboard** | ✅ Working | Main | /dashboard |
| **Emission Calculator** | ✅ Working | Main | API endpoint |
| **Document OCR** | ✅ Working | Analysis | /api/analyze-document |
| **AI Consultant** | ✅ Working | AI | /ai-consultant |
| **Sentinel Chat** | ✅ Working | AI | /sentinel |
| **Report Generator** | ✅ Working | Reports | /report |
| **PDF Export** | ✅ Working | Reports | /api/generate-report-pdf |
| **Compliance Dashboard** | ✅ Working | Compliance | /compliance_dashboard |
| **Compliance Matrix** | ✅ Working | Compliance | /api/compliance/matrix |
| **ESG Data Center** | ✅ **FIXED** | ESG | /esg-data-center |
| **Environmental Module** | ✅ **FIXED** | ESG | /esg-environmental |
| **Social Module** | ✅ **FIXED** | ESG | /esg-social |
| **Governance Module** | ✅ **FIXED** | ESG | /esg-governance |
| **Supply Chain Module** | ✅ **FIXED** | ESG | /esg-supply-chain |
| **Marketplace** | 🟡 Partial | Commerce | /marketplace |
| **Services Page** | ✅ Working | Info | /services |
| **Profile Settings** | 🟡 Partial | Settings | /profile_settings |
| **Company Settings** | 🟡 Partial | Settings | /company_settings |
| **Supplier Portal** | 🟡 Partial | B2B | /supplier_portal |
| **Verification Mode** | 🟡 Placeholder | Audit | /verification_mode |
| **Audit Trail** | 🟡 Partial | Audit | /audit_trail |
| **Carbon Tax Modeling** | 🟡 Placeholder | Analysis | /carbon_tax_modeling |
| **Courses** | 🟡 Coming Soon | Education | /courses |
| **Malaysia Reports** | 🟡 Partial | Reports | /malaysian_reports |

---

## 🎯 **Feature Completion Status** (January 2026)

- ✅ **Fully Working**: 15 features (52%)
- 🟡 **Partially Working**: 9 features (31%)
- 🟡 **Planned/Coming Soon**: 5 features (17%)

**Total Routes**: 60+
**Total Templates**: 26
**Total API Endpoints**: 25+
**Recent Fixes**: 4 critical bug fixes (Template caching, ESG routes, dependency installation, model initialization)

---

## 🏗️ Architecture & Technology Stack

### Backend
- **Framework**: Flask (Python web framework)
- **Database**: SQLite (default, with Flask-SQLAlchemy ORM)
- **AI Integration**: Google Gemini API
- **Document Processing**: 
  - Tesseract OCR (text extraction from images)
  - pdf2image + PIL (PDF conversion to images)
  - PyPDF2 (fallback PDF text extraction)
- **PDF Generation**: ReportLab (Windows-compatible)
- **APIs**: Flask RESTful endpoints for data exchange

### Frontend
- **Templates**: HTML with Jinja2 templating
- **Styling**: Tailwind CSS + Bootstrap 5
- **Charts**: Chart.js for real-time data visualization
- **Icons**: FontAwesome 6
- **JavaScript**: Vanilla JS for interactivity

### Key Dependencies
```
Flask
Werkzeug (password hashing & file uploads)
google-generativeai (Gemini AI)
pytesseract (OCR)
pdf2image (PDF processing)
Pillow (image processing)
reportlab (PDF generation)
requests (HTTP calls)
```

---

## 📁 Project Structure

```
Carbon_Tracker/
├── app.py                      # Main Flask application (2162 lines)
├── requirements.txt            # Python dependencies
├── readme.md                   # This file
│
├── templates/                  # HTML templates (Jinja2)
│   ├── base.html              # Base template (inherited by all pages)
│   ├── base_auth.html         # Base template for authenticated pages
│   ├── index.html             # Landing/home page
│   ├── dashboard.html         # Main carbon dashboard
│   ├── report.html            # GRI/GHG report generation
│   ├── sentinel.html          # AI Carbon Sentinel chat interface
│   ├── source_documents.html  # Document upload & OCR processing
│   ├── marketplace.html       # Carbon trading marketplace
│   ├── services.html          # Platform services overview
│   ├── compliance_dashboard.html  # Regulatory compliance tracker
│   ├── carbon_tax_modeling.html   # Carbon tax scenario modeling
│   ├── supplier_portal.html   # B2B supplier emissions interface
│   ├── verification_mode.html # Third-party audit verification
│   ├── audit_trail.html       # Complete emission history log
│   ├── courses.html           # Carbon education modules
│   ├── malaysian_reports.html # Malaysia-specific compliance reports
│   ├── auth/
│   │   ├── login.html         # Login page
│   │   └── register.html      # Registration page
│
├── static/                     # Static files
│   ├── css/
│   │   └── custom.css         # Custom styling
│   ├── js/
│   │   └── main.js            # Frontend JavaScript logic
│   ├── images/                # Logo & graphics
│   └── uploads/               # File storage
│       └── source_docs/       # Uploaded documents
│
├── tools/                      # Development utilities
│   ├── inspect_app_import.py
│   ├── test_login_dashboard.py
│   └── test_routes.py
│
├── migrations/                 # Database migrations (Alembic)
├── instance/                   # Instance-specific files
│   └── carbon_tracker.db      # SQLite database
└── credentials/               # API keys & secrets
```

---

## �️ **Database Models & Data Schema**

The platform uses **SQLAlchemy ORM** with **SQLite** for data persistence. Below is a comprehensive overview of all database models:

### **Core Compliance Models** (NEW)

#### **1. ComplianceStandard** 
Stores regulatory standards and frameworks that organizations must comply with.

```python
class ComplianceStandard(db.Model):
    id (Integer) - Primary key
    name (String) - Full standard name (e.g., "IFRS S2")
    short_name (String) - Abbreviated name (e.g., "IFRS S2")
    version (String) - Standard version (e.g., "2023")
    description (Text) - Detailed description
    jurisdiction (String) - Geographic scope (Global, Malaysia, etc.)
    category (String) - Category (Financial Reporting, Climate Risk, etc.)
    logo (String) - Logo file path
    website (String) - Official standard website URL
    effective_date (Date) - When standard becomes effective
    next_review_date (Date) - Scheduled review date
    created_at (DateTime) - Record creation timestamp
    updated_at (DateTime) - Last modification timestamp
    
    Relationships:
    - clauses → ComplianceClause (one-to-many)
    - user_statuses → UserComplianceStatus (one-to-many)
```

**Standards Currently Tracked**:
- ✅ IFRS S1 (General Requirements)
- ✅ IFRS S2 (Climate-related Disclosures)
- ✅ TCFD (Task Force on Climate-related Financial Disclosures)
- ✅ ISO 14064-1 (GHG Accounting & Verification)
- ✅ GHG Protocol (Corporate Accounting Standard)
- ✅ GRI Standards (Global Reporting Initiative)
- ✅ Malaysia MGTC (Green Technology Corporation)
- ✅ Malaysia SEDA (Sustainable Energy Development)
- ✅ Carbon Tax Readiness Framework

---

#### **2. ComplianceClause**
Individual requirements and clauses within each standard.

```python
class ComplianceClause(db.Model):
    id (Integer) - Primary key
    standard_id (Integer, FK) - Reference to ComplianceStandard
    clause_number (String) - Clause identifier (e.g., "S2-3")
    title (String) - Clause title
    description (Text) - Full clause description
    requirement (Text) - Specific requirement details
    guidance (Text) - Implementation guidance
    is_mandatory (Boolean) - Whether clause is mandatory
    priority (Integer) - Priority level (1=critical, 2=high, 3=medium)
    category (String) - Clause category (governance, strategy, risk, etc.)
    tags (Text) - Comma-separated tags for search
    created_at (DateTime) - Record creation timestamp
    updated_at (DateTime) - Last modification timestamp
    
    Relationships:
    - standard → ComplianceStandard (many-to-one)
    - user_statuses → UserComplianceStatus (one-to-many)
    - evidence → EvidenceFile (one-to-many)
    - mappings → ClauseMapping (one-to-many)
```

**Example Clauses**:
- IFRS S2-3: Greenhouse gas emissions
- TCFD-1: Governance disclosure
- GRI 305: Emissions reporting
- ISO 14064-4.2: Organizational boundaries

---

#### **3. UserComplianceStatus** 
Tracks organization's compliance status for each clause.

```python
class UserComplianceStatus(db.Model):
    id (Integer) - Primary key
    user_id (String, 100) - User identifier
    clause_id (Integer, FK) - Reference to ComplianceClause
    standard_id (Integer, FK) - Reference to ComplianceStandard
    status (String) - Status: 'not_assessed', 'compliant', 'partial', 'non_compliant'
    evidence_summary (Text) - Summary of supporting evidence
    assessment_date (DateTime) - When assessment was performed
    next_assessment_date (DateTime) - Scheduled next assessment
    assessor (String) - Who performed the assessment
    comments (Text) - Assessment notes and findings
    confidence_score (Integer) - Confidence level (0-100)
    created_at (DateTime) - Record creation timestamp
    updated_at (DateTime) - Last modification timestamp
    
    Relationships:
    - standard → ComplianceStandard (many-to-one)
    - clause → ComplianceClause (many-to-one)
    - evidence_files → EvidenceFile (one-to-many)
```

**Status Values**:
- 🟢 **compliant**: All requirements met (100%)
- 🟡 **partial**: Some requirements met (50-99%)
- 🔴 **non_compliant**: Not meeting requirements
- ⚪ **not_assessed**: Not yet evaluated

---

#### **4. EvidenceFile**
Supporting documents and evidence for compliance claims.

```python
class EvidenceFile(db.Model):
    id (Integer) - Primary key
    user_id (String) - User identifier
    compliance_status_id (Integer, FK) - Reference to UserComplianceStatus
    clause_id (Integer, FK) - Reference to ComplianceClause
    filename (String) - Original filename
    file_path (String) - Storage path in file system
    file_type (String) - MIME type (application/pdf, image/png, etc.)
    file_size (Integer) - File size in bytes
    description (Text) - What this evidence demonstrates
    upload_date (DateTime) - When file was uploaded
    verified (Boolean) - Whether auditor verified the file
    verified_by (String) - Auditor username
    verified_date (DateTime) - When verification occurred
    
    Relationships:
    - compliance_status → UserComplianceStatus (many-to-one)
    - clause → ComplianceClause (many-to-one)
```

**Accepted Evidence Types**:
- 📄 PDF documents (policies, reports, certificates)
- 📊 Excel/CSV spreadsheets (data, calculations)
- 🖼️ Images (screenshots, photos of procedures)
- 📝 Text files (notes, descriptions)

---

#### **5. ClauseMapping** (NEW)
Maps corresponding clauses across different standards.

```python
class ClauseMapping(db.Model):
    id (Integer) - Primary key
    source_clause_id (Integer, FK) - Reference to source ComplianceClause
    target_standard_id (Integer, FK) - Reference to target ComplianceStandard
    target_clause_id (Integer, FK) - Reference to target ComplianceClause
    mapping_type (String) - Type of mapping (equivalent, related, overlapping)
    confidence (Integer) - Mapping confidence (0-100)
    notes (Text) - Explanation of the mapping
    created_at (DateTime) - Record creation timestamp
    
    Relationships:
    - source_clause → ComplianceClause (many-to-one)
    - target_standard → ComplianceStandard (many-to-one)
    - target_clause → ComplianceClause (many-to-one)
```

**Example Mappings**:
- IFRS S2-3 (Greenhouse gas emissions) ↔ GRI 305 (Emissions)
- ISO 14064-4.2 (Organizational boundaries) ↔ GHG Protocol (Boundary Definition)

---

### **User & Company Models**

#### **6. UserProfile** (NEW)
Extended user profile information for audit traceability.

```python
class UserProfile(db.Model):
    id (Integer) - Primary key
    user_id (String, 50) - User identifier
    company_id (String, 100) - Organization identifier
    full_legal_name (String) - User's full legal name
    phone_number (String) - Contact phone
    job_title (String) - Position/role
    department (String) - Organizational department
    esg_responsibility (Text, JSON) - ESG responsibilities (multi-select)
    authority_level (String) - Data Entry, Reviewer, or Approver
    declaration_accepted (Boolean) - Signed declaration
    declaration_timestamp (DateTime) - When declaration was signed
    created_at (DateTime) - Profile creation date
    updated_at (DateTime) - Last modification date
    updated_by (String) - Who last updated
```

**Authority Levels**:
- 👤 **Data Entry**: Can only input data
- 👥 **Reviewer**: Can review and comment on data
- ✅ **Approver**: Can approve emissions data for reporting

---

#### **7. CompanySettings** (NEW)
Organization-level configuration and reporting parameters.

```python
class CompanySettings(db.Model):
    id (Integer) - Primary key
    company_id (String, 100) - Unique company identifier
    legal_company_name (String) - Official registered company name
    company_registration_number (String) - Registration/incorporation number
    country_of_incorporation (String) - Headquarters country
    industry_classification (String) - MSIC/NAICS code
    financial_year_start (String) - MM-DD format (e.g., "01-01")
    financial_year_end (String) - MM-DD format (e.g., "12-31")
    reporting_currency (String) - Currency code (USD, MYR, etc.)
    reporting_boundary_method (String) - Operational Control, Financial Control, or Equity Share
    included_entities (Text) - Entities in reporting boundary
    excluded_entities (Text) - Entities excluded from boundary
    excluded_entities_justification (Text) - Why entities are excluded
    number_of_operational_sites (Integer) - Total operational locations
    site_locations (Text, JSON) - Array of site locations
    primary_business_activities (Text) - Main business activities
    board_oversight (Boolean) - Whether board oversees climate/ESG
    esg_committee_exists (Boolean) - Has dedicated ESG committee
    role_responsible_for_esg (String) - Job title of ESG lead
    external_assurance_status (String) - None, Limited, or Reasonable
    esg_policy_url (String) - Link to ESG policy document
    environmental_policy_url (String) - Link to environmental policy
    health_safety_policy_url (String) - Link to H&S policy
    supplier_code_url (String) - Link to supplier code of conduct
    policy_issue_dates (Text, JSON) - Dates when policies were issued
    reporting_scope (Text, JSON) - Scope 1, 2, 3 inclusions
    audit_mode_enabled (Boolean) - Whether audit mode is active
    created_by (String) - Who created the record
    updated_by (String) - Who last updated
    created_at (DateTime) - Creation timestamp
    updated_at (DateTime) - Last modification timestamp
    version (Integer) - Configuration version number
```

---

### **Emission Data (Existing)**

#### **8. Emission** (Mock Data - In-Memory)
Currently stored as Python dictionaries, to be migrated to database model.

```python
# Current structure (in-memory):
emission_data = {
    'username': {
        'scope1': [
            {
                'category': 'diesel',
                'amount': 100,
                'unit': 'liters',
                'date': '2025-01-15',
                'co2e': 1340  # (100 * 13.4)
            }
        ],
        'scope2': [...],
        'scope3': [...]
    }
}

# Will be migrated to:
class Emission(db.Model):
    id (Integer)
    user_id (String, FK)
    scope (String: 'scope1', 'scope2', 'scope3')
    source (String)
    activity_data (Float)
    emission_factor (Float)
    total_emission (Float)
    unit (String)
    date (Date)
    created_at (DateTime)
```

---

### **Database Relationships Diagram**

```
ComplianceStandard (1) ──────── (Many) ComplianceClause
         │                               │
         │                               │
         │                        UserComplianceStatus (1) ──── (Many) EvidenceFile
         │                               │
         └───────────────┬───────────────┘
                         │
                   ClauseMapping
                   (Standard Cross-Reference)

UserProfile ──────── (1 to 1) ──────── CompanySettings
         │
         └─────── (1) ──────── (Many) UserComplianceStatus
                                        │
                                        └─ EvidenceFile
```

---

### **Database Initialization**

The database is automatically initialized on application startup:

```python
# In app.py
def initialize_compliance_database():
    """Initialize compliance database - safe for Windows"""
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        # Seed initial standards and clauses (if not already present)
        if ComplianceStandard.query.count() == 0:
            seed_compliance_standards()
```

**Initial Seeding**: 9 standards × ~4-5 clauses each = ~45 compliance clauses ready for assessment

---

## �🚀 Key Features & Pages

### 1. **Landing Page** (`/` → `index.html`)
**Purpose**: Public marketing & information hub

**Buttons & Sections**:
- **Navigation Bar**:
  - 🏠 **Logo/Home**: Redirects to landing page
  - 📖 **About Us**: Scroll to about section
  - 🌍 **What is Carbon?**: Educational content about carbon emissions
  - 🛠️ **Our Services**: Platform services overview
  - 📞 **Contact Us**: Contact section
  - 🔑 **Login**: Redirect to `/login`
  - 📝 **Register**: Redirect to `/register`

- **Hero Section**:
  - 🎯 **"Explore Solutions"**: Anchor scroll to services
  - 📚 **"Learn More"**: Anchor scroll to carbon education

- **About Us Section**:
  - 🎯 **"Pioneering Carbon Intelligence"**: Company info & value proposition
  - Display features like "Accurate Measurement", "AI-Powered Insights", "Regulatory Compliance"

- **Services Section**:
  - 🧮 **Emission Calculation**: Real-time CO2e calculation
  - 📊 **Dashboard Analytics**: Visual data representation
  - 🤖 **AI Consultation**: Gemini-powered advice
  - 📋 **GRI Reporting**: Standards-compliant reports
  - 🔍 **Document Analysis**: OCR-based receipt parsing
  - 🌳 **Carbon Offsetting**: Offset marketplace
  - ✅ **Compliance Checking**: Regulatory guidance (Malaysia-focused)

---

### 2. **Authentication Pages**

#### **Register Page** (`/register` → `templates/auth/register.html`)
**Purpose**: Create new user account

**Buttons & Fields**:
- 📝 **Username Input Field**: Unique username
- 📧 **Email Input Field**: User email
- 🏢 **Company Name Input**: Organization name
- 🔐 **Password Input**: Secure password
- 📝 **Confirm Password Input**: Password verification
- ✅ **"Register" Button**: Creates account and redirects to `/login`
- 🔗 **"Already have an account? Login"**: Redirect to `/login`

**Form Validation**:
- Check if username already exists
- Store password as hashed value
- Create empty emission data structure for new user

#### **Login Page** (`/login` → `templates/auth/login.html`)
**Purpose**: Authenticate existing users

**Buttons & Fields**:
- 👤 **Username Input Field**: User identification
- 🔐 **Password Input Field**: Authentication
- 🚀 **"Login" Button**: Authenticates and redirects to `/dashboard`
- 🔗 **"Need an account? Register"**: Redirect to `/register`
- 🏠 **"Back to Home"**: Redirect to `/`

**Authentication Flow**:
- Verify username exists in `users` dictionary
- Compare provided password with stored hash using `check_password_hash()`
- Set session variables: `user`, `email`, `company`
- Redirect to `/dashboard`

---

### 3. **Dashboard Pages** (Authenticated)

#### **Dashboard Home** (`/dashboard` → `templates/dashboard.html`)
**Purpose**: Main carbon monitoring & analytics hub

**Quick Stats Cards**:
- 📊 **Total Emissions**: Sum of all Scope 1, 2, 3 emissions (kg CO₂e)
- 💳 **Carbon Traded**: Carbon credits traded (450 kg)
- 🌳 **Carbon Offset**: Carbon offsets purchased (320 kg)
- ⭐ **Carbon Credited**: Carbon credits earned (280 kg)

**Main Charts**:
- 📈 **Carbon Activities Bar Chart**: Compares Scope 1, 2, 3 totals
- 📉 **Monthly Emission Trends**: Line chart showing trends over 6 months
- 🥧 **Scope 1 Sources Pie Chart**: Breakdown by fuel type (diesel, natural gas, etc.)
- 🥧 **Scope 2 Sources Pie Chart**: Electricity consumption breakdown
- 🥧 **Scope 3 Sources Pie Chart**: Supply chain & travel emissions breakdown

**Action Buttons**:
- ➕ **"Add Emission Data"**: Opens modal to manually enter emissions
- 📄 **"My Report"**: Navigate to `/report` for GRI/GHG compliant report generation
- 🔄 **"Download Report"**: Export PDF with `/api/generate-report-pdf`

**Chart Calculation Logic** (in `main.js`):
```javascript
// Initialize charts with Chart.js
const carbonChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Scope 1', 'Scope 2', 'Scope 3'],
    datasets: [{
      label: 'Emissions (kg CO₂e)',
      data: chart_data.scope_totals,
      backgroundColor: ['#0F3B2E', '#2E7D32', '#FF6F00']
    }]
  }
});
```

---

#### **Report Generation** (`/report` → `templates/report.html`)
**Purpose**: Generate GRI & GHG Protocol compliant carbon reports

**Report Sections Generated**:
1. **Report Metadata**: Report ID, date, standard version
2. **Organizational Information (GRI 102)**:
   - Company name, reporting entity, boundary type
   - Email, governance structure, assurance status

3. **GHG Protocol Compliance**:
   - Standard: GHG Protocol Corporate Accounting
   - Organizational boundary: Operational Control
   - Calculation methodology & emission factors
   - Global Warming Potentials (AR5)

4. **Emissions Inventory**:
   - Scope 1, 2, 3 totals in kg CO₂e and tonnes CO₂e
   - Percentage breakdown by scope
   - Category-wise breakdown (e.g., diesel, electricity, travel)

5. **Performance Metrics (GRI 305)**:
   - Carbon intensity (kg CO₂e per revenue unit)
   - Reduction targets (25% short-term, 50% medium-term, Net-zero 2050)
   - Current achievements

6. **Risk Assessment**:
   - Physical risks, transition risks, opportunities
   - Scenario analysis recommendations

7. **Data Quality & Verification**:
   - Data collection method, calculation accuracy
   - Completeness & consistency assessment

8. **Recommendations**:
   - Immediate actions (0-3 months)
   - Medium-term initiatives (3-12 months)
   - Long-term strategies (1-3 years)

**Buttons**:
- 📥 **"Download PDF"**: Calls `/api/generate-report-pdf` to download PDF report
- 🖨️ **"Print Report"**: Browser print dialog
- 📧 **"Email Report"**: Share report via email
- 💾 **"Save as Draft"**: Store report for later editing

**PDF Generation** (using ReportLab):
- Generates professional PDF with tables, styled text, colors
- Includes company logo, header/footer information
- Exportable for regulatory submission

---

#### **Carbon Sentinel AI Chat** (`/sentinel` → `templates/sentinel.html`)
**Purpose**: AI-powered carbon consultation and advice

**Header Section**:
- 📊 **Total Emissions Card**: Display total kg CO₂e
- 📉 **Reduction Potential Card**: Show savings opportunity (30% of total)
- 🎯 **Highest Emission Scope**: Which scope contributes most
- ⭐ **Priority Areas**: Number of high-emission sources to address

**Action Buttons**:
- 🔧 **"How to Fix?" Button**: Pre-populate with "how_to_fix" question type
- 💬 **"New Chat" Button**: Clear chat history and start fresh

**Sidebar - Your Emission Profile**:
- 📊 **Top Emission Sources**: List top 3 sources with CO₂e amounts
- 💡 **Reduction Tips**: AI-suggested actions for top sources
- 🎯 **Quick Actions**:
  - 📉 **"Reduce Emissions"**: Get reduction strategies
  - 💰 **"Carbon Credits"**: Explore crediting opportunities
  - 🌳 **"Carbon Offsetting"**: Find offset projects
  - 📋 **"Compliance"**: Regulatory guidance
  - ⚖️ **"Carbon Tax"**: Tax scenario modeling

**Chat Interface**:
- 💬 **Message Input Box**: User types questions/requests
- 🚀 **"Send" Button**: Submit message to `/api/gemini-advice` endpoint
- 🤖 **AI Response Display**: Formatted markdown response from Gemini API

**AI Responses Include**:
- 📌 **Title & Summary**: Main recommendation
- 📋 **Sections**: Detailed action items with sub-recommendations
- 📊 **Priority Actions**: Top 3 immediate actions
- 🔗 **References**: Links to Malaysia compliance frameworks

**Backend Integration**:
```python
@app.route('/api/gemini-advice', methods=['POST'])
def gemini_advice():
    # Gets user emission data
    # Analyzes emission patterns
    # Calls Gemini API with context
    # Returns formatted advice
    return jsonify(advice)
```

---

### 4. **Document Analysis & Source Management** (`/source-documents` → `templates/source_documents.html`)

**Purpose**: Upload bills/receipts for automatic emission data extraction

**Upload Stats Cards**:
- 📁 **Total Documents**: Number of uploaded files
- ✅ **Linked to Data**: Documents connected to emission records
- 🔐 **Verified**: Documents auditor-verified
- 💾 **Total Size**: Storage used (MB)

**Action Buttons**:
- ⬆️ **"Upload Document"**: Opens file upload modal
- 🔍 **"Verify Document"**: Third-party audit verification
- 🔗 **"Link to Record"**: Connect document to emission entry
- 🗑️ **"Delete"**: Remove document from system

**Document Processing Flow**:
1. User uploads PDF or image (utility bill, fuel receipt, etc.)
2. System calls `extract_text_from_pdf()` or `extract_text_from_image()`
3. Tesseract OCR extracts text
4. `parse_extracted_text()` analyzes content:
   - 🔍 **Fuel Type Detection**: Identifies fuel (diesel, RON95, electricity, etc.)
   - 🔢 **Quantity Extraction**: Extracts liters, kWh, RM amounts
   - 📊 **Scope Determination**: Assigns to Scope 1, 2, or 3
   - 🧮 **CO₂e Calculation**: Multiplies by emission factor
5. Results displayed with confidence score
6. User can confirm or manually edit values

**Example - Fuel Receipt Processing**:
```
Input: Fuel receipt image with "10.5 L RON95 @ RM 45.50"

OCR Output: "10.5 L RON95 @ RM 45.50"

Parse Results:
  - Fuel Type: ron95 (gasoline)
  - Quantity: 10.5 liters
  - Scope: scope1 (direct emission)
  - Emission Factor: 2.31 kg CO₂e/L
  - CO₂e: 24.25 kg
  - Confidence: 95%
```

**Example - Electricity Bill Processing**:
```
Input: Electric utility bill from Tenaga Nasional Berhad (TNB)

OCR Output: "Monthly Consumption: 450 kWh ... Charges: RM 180"

Parse Results:
  - Fuel Type: electricity
  - Quantity: 450 kWh
  - Scope: scope2 (indirect emission)
  - Emission Factor: 0.85 kg CO₂e/kWh (Malaysia average)
  - CO₂e: 382.5 kg
  - Confidence: 98%
```

---

### 5. **Carbon Marketplace** (`/marketplace` → `templates/marketplace.html`)

**Purpose**: Browse and trade carbon credits

**Features**:
- 🔍 **Search & Filter**: Find offset projects by type, location, price
- 📊 **Project Details**: Methodology, verification status, impact metrics
- 💰 **Pricing**: Cost per credit (₱/tonne CO₂e)
- 🛒 **Shopping Cart**: Add offsets to cart and checkout
- 📈 **Portfolio Tracking**: Monitor owned/traded credits

**Button Actions**:
- ✅ **"Add to Cart"**: Add offset project
- 💳 **"Purchase"**: Proceed to payment
- 📋 **"View Details"**: See project methodology & verification
- 📊 **"Compare Projects"**: Side-by-side comparison

---

### 6. **Compliance Dashboard** (`/compliance_dashboard` → `templates/compliance_dashboard.html`) ✨ ENHANCED

**Purpose**: Comprehensive regulatory compliance management and standards tracking

**Enhanced Features** (NEW):
- 📊 **Standards Compliance Matrix**: Track 9+ international and local standards
- 🔍 **Detailed Clause Assessment**: Evaluate specific requirements for each standard
- 📁 **Evidence Management**: Upload and manage supporting documents
- 🗓️ **Deadline Tracking**: Monitor upcoming compliance deadlines
- 📈 **Compliance Scoring**: Overall compliance percentage and per-standard scores
- 🔗 **Clause Mapping**: See how requirements overlap across standards
- 📋 **Audit Trail**: Track all assessments and changes with timestamps
- 📊 **Compliance Reports**: Generate audit-ready compliance documentation

**Standards Tracked** (9 total):

**International Standards** 🌍:
- ✅ **IFRS S1**: General Sustainability Requirements (Financial Reporting)
- ✅ **IFRS S2**: Climate-related Disclosures (Climate Risk)
- ✅ **TCFD**: Task Force on Climate-related Financial Disclosures
- ✅ **ISO 14064-1**: Greenhouse Gas Accounting & Verification
- ✅ **GHG Protocol**: Corporate Accounting & Reporting Standard
- ✅ **GRI Standards**: Global Reporting Initiative Standards

**Malaysia-Specific** 🇲🇾:
- ✅ **MGTC**: Malaysian Green Technology Corporation Guidelines
- ✅ **SEDA**: Sustainable Energy Development Authority
- ✅ **Carbon Tax Framework**: Malaysia carbon tax readiness

**Dashboard Components**:

1. **Overall Compliance Score Card**:
   - Shows aggregate compliance percentage (0-100%)
   - Color-coded status (🟢 Compliant, 🟡 Partial, 🔴 Action Needed)
   - Standards breakdown (compliant/partial/action needed)

2. **International Standards Section**:
   - Table listing all global standards
   - Compliance percentage per standard
   - Category (Financial Reporting, Climate Risk, GHG Accounting)
   - Jurisdiction filter
   - Detailed "View" button for each standard

3. **Malaysia Standards Section**:
   - Dedicated area for local compliance requirements
   - MGTC, SEDA, and Carbon Tax requirements
   - Local deadline tracking
   - Malaysia-specific guidance

4. **Evidence Status Sidebar**:
   - Count of uploaded evidence files
   - Evidence by standard and clause
   - Verification status (verified/pending)
   - Quick upload button

5. **Upcoming Deadlines**:
   - Sorted by urgency (urgent, warning, on-track)
   - Standard name and specific requirement
   - Due date and days remaining
   - Alert notifications

6. **Audit Activity Log**:
   - Recent assessments and changes
   - User actions (upload, verify, assess)
   - Timestamps for audit trail
   - Record IDs for traceability

**Status Indicators**:
- 🟢 **Compliant**: All clause requirements met
- 🟡 **Partial**: Some requirements met, evidence provided
- 🔴 **Non-compliant**: Requirements not met, action needed
- ⚪ **Not Assessed**: Clause not yet evaluated

**Action Buttons**:
- 📋 **"Generate Compliance Report"**: Create PDF compliance report for auditors
- 🎓 **"View Guidelines"**: Access regulatory documents and requirements
- 🔔 **"Set Reminders"**: Configure email alerts for upcoming deadlines
- 📞 **"Contact Consultant"**: Request expert compliance assistance
- 📁 **"Upload Evidence"**: Add supporting documents for clauses
- 🔍 **"View Mapping"**: See how clauses relate across standards

**Database Support**:
- 📦 **ComplianceStandard**: Stores all 9+ standards with metadata
- 📋 **ComplianceClause**: ~45 individual clauses/requirements
- ✔️ **UserComplianceStatus**: Tracks assessment status for each user
- 📄 **EvidenceFile**: Manages uploaded supporting documents
- 🔗 **ClauseMapping**: Shows equivalencies between standards

**API Integration**:
- `GET /api/compliance/matrix` - Full compliance matrix
- `GET /api/compliance/standard/<id>` - Standard-specific clauses
- `GET /api/compliance/clause/<id>` - Clause details and evidence
- `POST /api/compliance/update-status` - Update assessment status
- `POST /api/compliance/upload-evidence` - Upload evidence files
- `POST /api/compliance/generate-report` - Generate compliance report

---

### 7. **Services** (`/services` → `templates/services.html`)

**Purpose**: Overview of all platform features

**Service Cards**:
1. 🧮 **Emission Calculation**
   - Real-time CO₂e calculation
   - Multiple scopes (1, 2, 3)
   - Regional emission factors

2. 📊 **Analytics Dashboard**
   - Monthly trends, charts, breakdowns
   - Custom date range filtering
   - Export capabilities

3. 🤖 **AI Consultant**
   - Powered by Google Gemini
   - Personalized advice
   - Industry best practices

4. 📄 **GRI Reporting**
   - Standards-compliant reports
   - PDF export with styling
   - Audit-ready documentation

5. 📸 **Document Analysis**
   - OCR text extraction
   - Automatic data parsing
   - Receipt/bill processing

6. 🌳 **Carbon Marketplace**
   - Browse offset projects
   - Trading platform
   - Portfolio management

7. 🔐 **Verification Mode**
   - Third-party audit support
   - Digital signatures
   - Compliance certification

---

## 📊 **CURRENT PROGRESS & STATUS** (January 2026)

### **Project Status**: 🟢 **ACTIVE DEVELOPMENT**

This section documents the current state of the EmittiF.io platform, including implemented features, in-progress development, and known limitations.

---

## 📈 **Implementation Status Summary**

### **✅ FULLY IMPLEMENTED & WORKING**

| Component | Status | Details |
|-----------|--------|---------|
| **Authentication System** | ✅ Working | Login, Register, Logout with password hashing |
| **Dashboard** | ✅ Working | Chart.js integration, emissions display, carbon stats |
| **Emission Calculator** | ✅ Working | Scope 1, 2, 3 calculations with real emission factors |
| **GRI/GHG Reports** | ✅ Working | PDF generation with ReportLab, 8+ sections |
| **Document OCR** | ✅ Working | Tesseract OCR for receipts/bills, automatic parsing |
| **Compliance Dashboard** | ✅ Enhanced | 9 standards, clause management, evidence tracking, API endpoints |
| **Navigation Bar** | ✅ Working | Audit dropdown, Services dropdown, User profile menu |
| **Compliance Standards Database** | ✅ Working | 9 standards, ~45 clauses, SQLAlchemy models |
| **Compliance API Endpoints** | ✅ Working | 7 new endpoints for matrix, standards, evidence, reports |
| **Carbon Sentinel AI** | ✅ Partially | Base template ready, Gemini integration working |
| **Marketplace** | ✅ Rendered | Template exists, basic structure ready |
| **Services Page** | ✅ Rendered | Overview of 7+ platform services |

### **🟡 IN PROGRESS / PARTIAL**

| Component | Status | Details |
|-----------|--------|---------|
| **Gemini AI Integration** | 🟡 Partial | Works with fallback system, direct API available |
| **Carbon Sentinel Chat** | 🟡 Partial | UI ready, backend needs optimization |
| **Marketplace Features** | 🟡 Placeholder | Structure ready, payment integration pending |
| **Source Documents** | 🟡 Partial | Upload/OCR working, linking to emissions pending |
| **Supplier Portal** | 🟡 Placeholder | Template created, B2B features pending |
| **Courses & Training** | 🟡 Placeholder | Listed as "Coming Soon" |
| **Audit Trail** | 🟡 Placeholder | Template exists, real-time logging pending |

### **🔴 NOT IMPLEMENTED / NEEDS WORK**

| Component | Status | Details |
|-----------|--------|---------|
| **Real Database** | 🔴 Needed | Currently mock data (dict), needs SQLAlchemy migration |
| **User Roles** | 🔴 Partial | Defined in UI but not enforced in backend |
| **Third-party Audit** | 🔴 Not Started | Verification Mode page exists but no backend |
| **Carbon Tax Modeling** | 🔴 Partial | Page template exists, calculation engine pending |
| **Supplier Collaboration** | 🔴 Not Started | Portal template exists, invitation system pending |
| **Email Notifications** | 🔴 Not Started | Flash messages work, email integration pending |
| **API Documentation** | 🔴 Pending | Swagger/OpenAPI docs needed |
| **Unit Tests** | 🔴 Needed | Minimal test coverage exists |

---

## 🔄 **Website Navigation Flow**

### **Complete User Journey Map**

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANDING PAGE (/)                             │
│  - Hero Section with CTA                                        │
│  - About Us, Services, Features                                 │
│  - Call-to-Action: Login/Register                               │
└──────────────┬────────────────────────────────────────┬─────────┘
               │                                        │
        ┌──────▼──────┐                         ┌──────▼──────┐
        │   REGISTER  │                         │    LOGIN    │
        │  /register  │                         │   /login    │
        └──────┬──────┘                         └──────┬──────┘
               │                                        │
        Create User                            Authenticate User
        (POST form)                            (POST form)
               │                                        │
               └────────────────┬─────────────────────┘
                                │
                   ┌────────────▼──────────────┐
                   │   SESSION CREATED         │
                   │  (user, email, company)   │
                   └────────────┬──────────────┘
                                │
                   ┌────────────▼──────────────┐
                   │  DASHBOARD (/dashboard)  │
                   │  ✅ MAIN HUB              │
                   └────────────┬──────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        │              [AUDIT]  │  [SERVICES]          │
        │             DROPDOWN  │  DROPDOWN           │
        │                       │                       │
        ▼                       ▼                       ▼

    ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐
    │  AUDIT TOOLS    │   │  SERVICES MENU   │   │  USER PROFILE    │
    │  (8 items)      │   │  (6 items)       │   │  DROPDOWN        │
    └─────────────────┘   └──────────────────┘   └──────────────────┘
        │                       │                       │
        ├─ Overview        ├─ ESG Services       ├─ Profile Settings
        ├─ Compliance      ├─ Marketplace        ├─ Company Settings
        ├─ Carbon Tax      ├─ Courses            ├─ Notifications
        ├─ Suppliers       ├─ AI Consultant      └─ Logout
        ├─ Audit Trail     ├─ Sentinel
        ├─ Documents       └─ Reports
        ├─ Verification
        └─ Malaysia Reports
```

### **Step-by-Step User Flows**

#### **Flow 1: New User Onboarding**
```
1. User visits "/" (Landing)
   └─ Clicks "Register" button
      └─ Fills form (username, email, password, company)
         └─ Backend creates user in users{} dict
            └─ Initializes empty emission_data{}
               └─ Redirects to /login
                  └─ User logs in
                     └─ Session set (user, email, company)
                        └─ Redirects to /dashboard
                           └─ Empty dashboard loads
                              └─ "Add Emission Data" button ready
```

#### **Flow 2: Adding Emission Data (Manual)**
```
1. User on /dashboard
   └─ Clicks "Add Emission Data" button
      └─ Modal opens with form
         ├─ Select Scope (1/2/3)
         │  └─ Category dropdown populates (based on scope)
         ├─ Enter Activity Data (number)
         ├─ Unit selected automatically
         └─ Submit button → /api/add-emission (POST)
            └─ Backend calculates: CO₂e = amount × factor
               └─ Saves to emission_data[user][scope]
                  └─ Dashboard charts update automatically
                     └─ Success notification shown
```

#### **Flow 3: Document Analysis (OCR)**
```
1. User on /source_documents
   └─ Clicks "Upload Document" button
      └─ Selects PDF or image file (bill/receipt)
         └─ File sent to /api/analyze-document (POST)
            └─ Backend extracts text:
               ├─ detect_fuel_type_enhanced() → fuel type
               ├─ extract_amount_enhanced() → quantity
               ├─ determine_scope_enhanced() → scope assignment
               └─ parse_extracted_text() → CO₂e calculation
                  └─ Results shown with confidence score
                     └─ User confirms or manually edits
                        └─ Saves to emission_data
```

#### **Flow 4: AI Consultation (Carbon Sentinel)**
```
1. User on /sentinel
   └─ Views emission stats & top sources
      └─ Types question in chat box
         └─ Clicks "Send" → /api/gemini-advice (POST)
            └─ Backend:
               ├─ Gets user's emission_data
               ├─ Analyzes patterns
               ├─ Builds Gemini prompt with context
               ├─ Calls genai.GenerativeModel()
               └─ Returns formatted response
                  └─ Chat displays AI advice
                     └─ User can ask follow-up questions
```

#### **Flow 5: Report Generation**
```
1. User on /dashboard
   └─ Clicks "My Report" button → /report
      └─ Backend generates_gri_ghg_report():
         ├─ Aggregates all user emissions
         ├─ Calculates scope totals & percentages
         ├─ Builds 8+ GRI/GHG sections
         ├─ Creates performance metrics
         └─ Renders HTML report view
            └─ User clicks "Download PDF"
               └─ /api/generate-report-pdf generates:
                  ├─ Uses ReportLab to create PDF
                  ├─ Styled tables, sections, data
                  ├─ Company logo & branding
                  └─ Returns PDF file download
```

#### **Flow 6: Compliance Tracking**
```
1. User on /dashboard
   └─ Clicks [Audit] dropdown → "Compliance & Standards"
      └─ Navigate to /compliance_dashboard
         └─ Shows 9 standards with status:
            ├─ IFRS S1/S2 (Financial reporting)
            ├─ TCFD (Climate risk)
            ├─ ISO 14064 (GHG accounting)
            ├─ GHG Protocol (GHG standard)
            ├─ GRI Standards (Sustainability)
            ├─ MGTC (Malaysia green tech)
            ├─ SEDA (Malaysia energy)
            ├─ Carbon Tax Readiness
            └─ Shows:
               ├─ Overall compliance score
               ├─ Standards assessment matrix
               ├─ Urgent actions needed
               ├─ Upcoming deadlines
               └─ Evidence tracking
```

---

## 🔘 **Buttons & Features Status**

### **DASHBOARD PAGE (/dashboard)**

#### **Working Buttons ✅**

| Button | Icon | Function | Status |
|--------|------|----------|--------|
| **Add Emission Data** | ➕ | Opens modal to manually add emissions | ✅ Working |
| **My Report** | 📄 | Navigate to /report for PDF generation | ✅ Working |
| **Download Report (in report page)** | 📥 | Download PDF report via /api/generate-report-pdf | ✅ Working |

#### **Dashboard Features ✅**

| Feature | Status | Notes |
|---------|--------|-------|
| **Quick Stats Cards** | ✅ Working | Total emissions, carbon traded, offset, credited |
| **Carbon Activities Bar Chart** | ✅ Working | Chart.js visualization of Scope 1, 2, 3 |
| **Monthly Trends Chart** | ✅ Working | 6-month trend line chart |
| **Scope Breakdown Pie Charts** | ✅ Working | 3 pie charts for each scope's sources |
| **Real-time Updates** | ✅ Working | Charts update when new emissions added |

---

### **AUDIT DROPDOWN MENU (Navigation Bar)**

#### **Audit Overview** 📊
- **Status**: ✅ Working
- **Link**: `/dashboard` (same as Home)
- **Feature**: Shows dashboard with all emission data

#### **Compliance & Standards** 🛡️
- **Status**: ✅ Working
- **Link**: `/compliance_dashboard`
- **Features**:
  - ✅ 9 Standards tracked (IFRS, GRI, ISO 14064, MGTC, SEDA)
  - ✅ Overall compliance score displayed
  - ✅ Standards assessment matrix
  - ✅ Evidence tracking
  - ✅ Deadlines management
  - 🟡 Full clause-by-clause assessment (API ready)

#### **Carbon Tax & Pricing** 💰
- **Status**: 🟡 Partial
- **Link**: `/carbon_tax_modeling`
- **Template**: exists in `templates/carbon_tax_modeling.html`
- **Features Needed**:
  - 🔴 Tax calculation engine
  - 🔴 Scenario modeling
  - 🔴 Price impact calculator

#### **Suppliers (Scope 3)** 🏭
- **Status**: 🟡 Partial
- **Link**: `/supplier_portal`
- **Template**: exists in `templates/supplier_portal.html`
- **Features Needed**:
  - 🔴 Supplier invitation system
  - 🔴 Data collection forms
  - 🔴 B2B collaboration

#### **Audit Trail** 🧾
- **Status**: 🟡 Partial
- **Link**: `/audit_trail`
- **Template**: exists in `templates/audit_trail.html`
- **Features Implemented**:
  - Basic structure in `compliance_dashboard()` → `audit_stats`
- **Features Needed**:
  - 🔴 Real-time change logging
  - 🔴 User action tracking
  - 🔴 Historical data view

#### **Source Documents** 📂
- **Status**: ✅ Working
- **Link**: `/source_documents`
- **Features**:
  - ✅ Document upload functionality
  - ✅ OCR processing (Tesseract)
  - ✅ Automatic data parsing
  - ✅ Confidence scoring
  - 🟡 Linking to emissions (UI ready)

#### **Verification & Assurance** 🧪
- **Status**: 🟡 Partial
- **Link**: `/verification_mode`
- **Template**: exists in `templates/verification_mode.html`
- **Features Needed**:
  - 🔴 Third-party audit workflow
  - 🔴 Digital signatures
  - 🔴 Approval process

#### **Malaysia Regulatory Reports** 🇲🇾
- **Status**: 🟡 Partial
- **Link**: `/malaysian_reports`
- **Template**: exists in `templates/malaysian_reports.html`
- **Features**:
  - Malaysia-specific report templates
  - MGTC compliance format
  - SEDA reporting structure

---

### **SERVICES DROPDOWN MENU (Navigation Bar)**

#### **ESG & Carbon Services** 🛠️
- **Status**: ✅ Working
- **Link**: `/services`
- **Features**: Overview of 7+ platform services displayed

#### **Marketplace** 🧩
- **Status**: 🟡 Partial (Placeholder)
- **Link**: `/marketplace`
- **Features**:
  - ✅ Template renders
  - 🔴 Carbon credit search
  - 🔴 Trading functionality
  - 🔴 Shopping cart
  - 🔴 Payment integration

#### **Courses & Training** 🎓
- **Status**: 🔴 Coming Soon
- **Link**: `/courses`
- **Features**: 
  - Label shows "Coming Soon"
  - 🔴 Course modules not implemented

#### **AI Consultant** 🤖
- **Status**: ✅ Working
- **Link**: `/ai_consultant`
- **Features**:
  - ✅ Page loads with user data
  - ✅ Emission pattern analysis
  - ✅ Advice generation (fallback system)
  - 🟡 Gemini AI integration (works with fallback)

#### **Carbon Sentinel** 🛡️
- **Status**: ✅ Working
- **Link**: `/sentinel`
- **Features**:
  - ✅ Chat interface ready
  - ✅ User emission stats displayed
  - ✅ Top sources listed
  - 🟡 Gemini API integration (with fallback)
  - 🟡 Message persistence (in-session only)

#### **Reports** 📋
- **Status**: ✅ Working
- **Link**: `/carbon_report` (maps to `/report`)
- **Features**:
  - ✅ GRI/GHG report generation
  - ✅ PDF export with styling
  - ✅ 8+ compliance sections
  - ✅ Recommendations included

---

### **USER PROFILE DROPDOWN MENU (Navigation Bar)**

#### **Profile Settings** 👤
- **Status**: 🔴 Not Implemented
- **Link**: `/profile_settings`
- **Features Needed**:
  - User info editing
  - Password change
  - Preferences

#### **Company Settings** 🏢
- **Status**: 🔴 Not Implemented
- **Link**: `/company_settings`
- **Features Needed**:
  - Company info editing
  - Department management
  - Integration settings

#### **Notifications** 🔔
- **Status**: 🟡 Partial
- **Link**: `/notifications`
- **Features**:
  - ✅ Flash messages working (top-right)
  - 🔴 Persistent notification system needed
  - 🔴 Email notification integration

#### **Logout** 🚪
- **Status**: ✅ Working
- **Function**: `@app.route('/logout')`
- **Features**:
  - ✅ Clears session
  - ✅ Confirmation dialog
  - ✅ Redirects to landing page

---

### **LOGIN & AUTHENTICATION BUTTONS**

#### **Login Page (/login)**
- **Status**: ✅ Working
- **Fields**: Username, Password
- **Button**: "Login" → POST /login
- **Features**:
  - ✅ Form validation
  - ✅ Password hashing (Werkzeug)
  - ✅ Session management
  - ✅ Error messages

#### **Register Page (/register)**
- **Status**: ✅ Working
- **Fields**: Username, Email, Password, Company
- **Button**: "Register" → POST /register
- **Features**:
  - ✅ Duplicate username check
  - ✅ Password hashing
  - ✅ User initialization
  - ✅ Emission data creation

---

### **API ENDPOINTS STATUS**

#### **Working APIs** ✅

| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/api/add-emission` | POST | ✅ Working | Add emission record |
| `/api/analyze-document` | POST | ✅ Working | OCR document processing |
| `/api/gemini-advice` | POST | ✅ Working | AI consultation (with fallback) |
| `/api/ai-advice` | POST | ✅ Working | Rule-based advice |
| `/api/generate-report-pdf` | GET | ✅ Working | PDF report download |
| `/api/report-data` | GET | ✅ Working | Report JSON data |

#### **Partial APIs** 🟡

| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/api/compliance/matrix` | GET | 🟡 Ready | Compliance data (needs DB) |
| `/api/compliance/standard/<id>` | GET | 🟡 Ready | Standard details (needs DB) |
| `/api/compliance/clause/<id>` | GET | 🟡 Ready | Clause details (needs DB) |
| `/api/compliance/update-status` | POST | 🟡 Ready | Status updates (needs DB) |
| `/api/compliance/upload-evidence` | POST | 🟡 Ready | Evidence upload (needs DB) |

---

## 🎛️ Navigation Bar & Dropdown Menus (base_auth.html)

The authenticated pages feature a comprehensive navigation bar with multiple dropdown menus. This section documents all buttons and their functions.

### **Navigation Bar Structure**

Located in `templates/base_auth.html`, the fixed navigation bar includes:
- **Left**: Brand/Logo with link to dashboard
- **Center**: Navigation links with dropdowns (Audit, Services)
- **Right**: User profile menu with role display

---

### **1. HOME Button** 🏠

**Location**: Left side of navbar
- **Icon**: Home icon
- **Link**: `/dashboard`
- **Function**: Redirects to main dashboard
- **Active State**: Highlighted if currently on dashboard page
- **Responsive**: Hidden on mobile, shown on desktop (md+)

---

### **2. AUDIT Dropdown Menu** 📊

**Location**: Center navbar
- **Icon**: Chart line icon
- **Trigger**: Hover on desktop, click on mobile

**Dropdown Menu Items**:

| Item | Icon | Link | Function |
|------|------|------|----------|
| **Audit Overview** | 📊 | `/dashboard` | View overall audit status & emission data |
| **Compliance & Standards** | 🛡️ | `/compliance_dashboard` | Track regulatory compliance (GRI, GHG, ISO 14064, MGTC, SEDA) |
| **Carbon Tax & Pricing** | 💰 | `/carbon_tax_modeling` | Model carbon tax scenarios & pricing impacts |
| **Suppliers (Scope 3)** | 🏭 | `/supplier_portal` | Manage supplier emissions & B2B integration |
| **Audit Trail** | 🧾 | `/audit_trail` | View complete emission history with timestamps |
| **Source Documents** | 📂 | `/source_documents` | Upload & manage source documents (bills, receipts) |
| **Verification & Assurance** | 🧪 | `/verifier_mode` | Third-party audit verification tools |
| **Regulatory Reports (Malaysia)** | 🇲🇾 | `/malaysian_reports` | Malaysia-specific compliance reports (MGTC, SEDA) |

**Header Section**:
- Title: "Audit Management"
- Subtitle: "Comprehensive audit tools"

**Styling**: 
- Dark green gradient background
- Hover: Semi-transparent white background
- Icons with menu indicators for external links
- Width: 500px on desktop

---

### **3. SERVICES Dropdown Menu** 🛠️

**Location**: Center navbar
- **Icon**: Cogs icon
- **Trigger**: Hover on desktop, click on mobile

**Dropdown Menu Items**:

| Item | Icon | Link | Function |
|------|------|------|----------|
| **ESG & Carbon Services** | 🛠️ | `/services` | Overview of all platform services |
| **Marketplace** | 🧩 | `/marketplace` | Carbon credit trading & offset marketplace |
| **Courses & Training** | 🎓 | `/courses` | Carbon education & training modules (Coming Soon) |
| **AI Consultant** | 🤖 | `/ai_consultant` | Get AI-powered carbon advice |
| **Carbon Sentinel** | 🛡️ | `/sentinel` | AI chat for carbon consultation |
| **Reports** | 📋 | `/carbon_report` | Generate GRI/GHG compliant reports |

**Header Section**:
- Title: "Platform Services"
- Subtitle: "Tools & resources"

**Special Features**:
- Divider line separating main services from quick access links
- "Coming Soon" badge on Courses option
- Width: 350px on desktop

**Styling**: Same as Audit dropdown

---

### **4. USER PROFILE Menu** 👤

**Location**: Right side of navbar
- **Icon**: User avatar with initials
- **Display**: Shows username and role badge
- **Trigger**: Hover on desktop, click on mobile
- **Mobile**: Icon and initials only

**User Profile Header**:
- Avatar circle with user's first initial
- Username display
- Email address
- Role badge with color-coding:
  - 👑 **Admin** (Red - #EF4444)
  - 🔍 **Auditor** (Yellow - #F59E0B)
  - 🏭 **Supplier** (Blue - #3B82F6)
  - 🌱 **Sustainability Lead** (Green - #10B981) [default]

**Company Info Box**:
- Displays user's company name
- Semi-transparent dark background

**Dropdown Menu Items**:

| Item | Icon | Link | Function |
|------|------|------|----------|
| **Profile Settings** | 👤 | `/profile_settings` | Edit personal profile & account info |
| **Company Settings** | 🏢 | `/company_settings` | Manage company details & settings |
| **Notifications** | 🔔 | `/notifications` | View system notifications (shows count badge) |
| **Logout** | 🚪 | `/logout` | Sign out of platform |

**Security Section**:
- Shows: "Session active"
- Green checkmark: "Secured connection"
- Located below notifications before divider

**Logout Confirmation**:
- Triggers: `confirm('Are you sure you want to logout?')`
- Styling: Red text on hover
- Safety: Requires user confirmation

**Width**: 320px on desktop
**Responsive**: Collapses to avatar-only on mobile

---

## 📱 Responsive Behavior

### **Desktop (md+)**
- All navigation links visible
- Username and role displayed next to avatar
- Dropdowns trigger on hover
- Full menu text visible

### **Mobile & Tablet**
- Center navigation links hidden
- User menu simplified to avatar only
- Dropdowns trigger on click
- Touch-friendly sizing (increased padding)
- Menus open/close with JavaScript toggle

---

## 🎨 Styling Features

### **Navigation Styling**:
```css
/* Navigation Bar */
.nav-gradient {
    background: linear-gradient(135deg, #0F3B2E 0%, #1A5C48 100%);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* Navigation Links */
.nav-link-custom {
    color: rgba(255, 255, 255, 0.8);
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    transition: all 0.3s ease;
}

.nav-link-custom:hover {
    color: white;
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);  /* Subtle lift effect */
}

.nav-link-custom.active {
    color: white;
    background: rgba(255, 255, 255, 0.15);
    font-weight: 600;
}

/* Dropdown Menus */
.dropdown-menu-custom {
    background: linear-gradient(135deg, #0F3B2E 0%, #1A5C48 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.75rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.dropdown-item-custom {
    color: rgba(255, 255, 255, 0.8);
    padding: 0.75rem 1.5rem;
    display: flex;
    align-items: center;
    transition: all 0.3s ease;
}

.dropdown-item-custom:hover {
    color: white;
    background: rgba(255, 255, 255, 0.1);
}
```

### **Icons & Indicators**:
- Menu icons: Font Awesome 6 icons with emojis
- Menu icon width: 24px (centered alignment)
- Submenu indicators (→, ↗️): Shows external link or expandable item
- Role badges: Color-coded per user role

---

## 🔧 JavaScript Functionality

### **Dropdown Toggle Logic** (in `base_auth.html`):

```javascript
// Hover effect for dropdowns
document.querySelectorAll('.group').forEach(dropdown => {
    // On mouse enter: Show dropdown
    dropdown.addEventListener('mouseenter', function() {
        const menu = this.querySelector('.dropdown-menu-custom');
        if (menu) {
            menu.classList.remove('invisible', 'opacity-0');
            menu.classList.add('visible', 'opacity-100');
        }
    });
    
    // On mouse leave: Hide dropdown (with 300ms delay)
    dropdown.addEventListener('mouseleave', function() {
        const menu = this.querySelector('.dropdown-menu-custom');
        if (menu) {
            setTimeout(() => {
                menu.classList.remove('visible', 'opacity-100');
                menu.classList.add('invisible', 'opacity-0');
            }, 300);  // Smooth transition delay
        }
    });
});

// Mobile click behavior
const userMenu = document.querySelector('.relative.group:last-child');
if (userMenu) {
    userMenu.addEventListener('click', function(e) {
        if (window.innerWidth < 768) {  // Mobile breakpoint
            e.preventDefault();
            const menu = this.querySelector('.dropdown-menu-custom');
            const isVisible = menu.classList.contains('visible');
            
            // Close all other menus
            document.querySelectorAll('.dropdown-menu-custom').forEach(m => {
                m.classList.remove('visible', 'opacity-100');
                m.classList.add('invisible', 'opacity-0');
            });
            
            // Toggle current menu
            if (!isVisible) {
                menu.classList.remove('invisible', 'opacity-0');
                menu.classList.add('visible', 'opacity-100');
            }
        }
    });
}

// Set active nav link based on current URL
const currentPath = window.location.pathname;
document.querySelectorAll('.nav-link-custom').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
        link.classList.add('active');
    }
});
```

### **Key Features**:
- Smooth transitions (300ms delay on close)
- Active page highlighting
- Mobile-optimized touch interactions
- Confirmation dialog for logout
- Real-time notification badge

---

## 🌐 Navigation Flow Diagram

```
Landing Page (/)
    ↓
Login (/login)
    ↓
Dashboard (/dashboard) ← [Home Button]
    ├─ [Audit] Dropdown Menu
    │   ├─ Audit Overview
    │   ├─ Compliance & Standards (/compliance_dashboard)
    │   ├─ Carbon Tax & Pricing (/carbon_tax_modeling)
    │   ├─ Suppliers Portal (/supplier_portal)
    │   ├─ Audit Trail (/audit_trail)
    │   ├─ Source Documents (/source_documents)
    │   ├─ Verification & Assurance (/verifier_mode)
    │   └─ Malaysia Reports (/malaysian_reports)
    │
    ├─ [Services] Dropdown Menu
    │   ├─ ESG & Carbon Services (/services)
    │   ├─ Marketplace (/marketplace)
    │   ├─ Courses & Training (/courses)
    │   ├─ AI Consultant (/ai_consultant)
    │   ├─ Carbon Sentinel (/sentinel)
    │   └─ Reports (/carbon_report)
    │
    └─ [User Profile] Dropdown Menu
        ├─ Profile Settings (/profile_settings)
        ├─ Company Settings (/company_settings)
        ├─ Notifications (/notifications)
        └─ Logout (/logout)
```

---

## 🎯 User Roles & Permissions

Based on dropdown display, the platform supports 4 user roles:

### **1. Admin** 👑
- **Color**: Red (#EF4444)
- **Access**: Full platform access
- **Features**: All dropdowns & settings visible
- **Permissions**: Create users, manage company, system settings

### **2. Auditor** 🔍
- **Color**: Yellow (#F59E0B)
- **Access**: Audit & verification features
- **Features**: Audit Trail, Verification Mode, Reports
- **Permissions**: Review emissions, approve data, generate audit reports

### **3. Supplier** 🏭
- **Color**: Blue (#3B82F6)
- **Access**: Scope 3 submission features
- **Features**: Supplier Portal
- **Permissions**: Submit emissions data, respond to requests

### **4. Sustainability Lead** 🌱 (Default)
- **Color**: Green (#10B981)
- **Access**: Core platform features
- **Features**: Dashboard, Marketplace, AI Consultant
- **Permissions**: Create emissions, view reports, access services

---

## 🔔 Flash Messages

The navigation includes a **flash message system** for user feedback:

```html
<!-- Positioned: Fixed top-right, z-50 -->
<div class="fixed top-24 right-6 z-50 space-y-2">
    <!-- Error messages: Red background -->
    <div class="bg-red-500 text-white px-6 py-3 rounded-xl shadow-lg">
        Error message here
    </div>
    
    <!-- Success messages: Green background -->
    <div class="bg-emerald-500 text-white px-6 py-3 rounded-xl shadow-lg">
        Success message here
    </div>
</div>
```

**Message Types**:
- 🔴 Error: Red (#EF4444) background
- 🟢 Success: Emerald (#10B981) background
- Animation: Fade-in on display
- Duration: Auto-dismiss or manual close

---

## 📊 Emission Calculation System

### Emission Factors (Malaysia-based)

**Scope 1 - Direct Emissions** (in `app.py`):
```python
EMISSION_FACTORS['scope1'] = {
    'diesel': 2.68,           # kg CO₂e per liter
    'gasoline': 2.31,         # kg CO₂e per liter
    'ron95': 2.31,            # kg CO₂e per liter (premium unleaded)
    'ron97': 2.31,            # kg CO₂e per liter (super premium)
    'natural_gas': 2.75,      # kg CO₂e per m³
    'lpg': 1.55,              # kg CO₂e per liter
    'coal': 2.42              # kg CO₂e per kg
}
```

**Scope 2 - Indirect Energy Emissions**:
```python
EMISSION_FACTORS['scope2'] = {
    'electricity': 0.85       # kg CO₂e per kWh (Malaysia grid average)
}
```

**Scope 3 - Other Indirect Emissions**:
```python
EMISSION_FACTORS['scope3'] = {
    'business_travel_air': 0.25,    # kg CO₂e per km
    'business_travel_car': 0.21,    # kg CO₂e per km
    'employee_commute': 0.12,       # kg CO₂e per km
    'purchased_goods': 0.15,        # kg CO₂e per RM (estimated)
    'waste_disposal': 0.85          # kg CO₂e per kg
}
```

### Calculation Formula

```
Total CO₂e = Activity Data (amount) × Emission Factor × Unit Conversion

Example:
- 10.5 liters of RON95 gasoline
- Emission factor: 2.31 kg CO₂e per liter
- CO₂e = 10.5 × 2.31 = 24.26 kg CO₂e
```

### Add Emission Data Flow

**API Endpoint**: `POST /api/add-emission`

```javascript
// Frontend sends:
{
  "scope": "scope1",
  "category": "diesel",
  "amount": 50.5,
  "unit": "liters"
}

// Backend calculates:
co2e = 50.5 × 2.68 = 135.34 kg CO₂e

// Returns:
{
  "success": true,
  "co2e": 135.34,
  "message": "Emission data added successfully"
}

// Stored in emission_data[username]['scope1']:
{
  "category": "diesel",
  "amount": 50.5,
  "unit": "liters",
  "date": "2025-01-15",
  "co2e": 135.34
}
```

---

## 🤖 AI Integration - Google Gemini

### Gemini API Configuration

```python
# In app.py:
GEMINI_API_KEY = "AIzaSyBQBZ89bmr5IINCUBL3DUBjOJZ6ilo99rA"

genai.configure(api_key=GEMINI_API_KEY)
```

### AI Consultation Features

#### **Question Types**:
1. **"general"** - General carbon management advice
2. **"how_to_fix"** - Specific fixes for top emission sources
3. **"reduction"** - Carbon reduction strategies
4. **"crediting"** - Carbon crediting opportunities
5. **"offsetting"** - Carbon offset solutions
6. **"compliance"** - Regulatory compliance guidance

#### **Gemini Prompt Structure**:
```python
prompt = f"""
You are Carbon Sentinel AI, an expert in:
- SBTi Corporate Net-Zero Standard
- GHG Protocol Corporate Accounting
- ISO 14064 GHG Quantification
- SEDA Malaysia Guidelines
- MGTC Requirements

USER EMISSION DATA:
- Total: {total_emissions} kg CO₂e
- Highest Scope: {highest_scope}
- Top Sources: {top_sources}

QUESTION: {user_message}

Provide actionable advice per international standards.
"""
```

#### **API Endpoint**:
```python
@app.route('/api/gemini-advice', methods=['POST'])
def gemini_advice():
    # Gets user data from session
    # Analyzes emission patterns
    # Calls Gemini with structured prompt
    # Returns formatted response
    return jsonify({
        'success': True,
        'advice': advice,
        'ai_source': 'gemini'
    })
```

#### **Fallback System**:
If Gemini API fails:
1. Try direct API call via HTTP (if SDK fails)
2. Fall back to rule-based `generate_ai_advice()` function
3. Return pre-generated advice based on emission patterns

---

## 🗄️ Data Model

### User Dictionary (Mock Database)
```python
users = {
    'admin': {
        'password': hashed_password,  # bcrypt hash
        'email': 'admin@emittif.io',
        'company': 'EmittiF Demo'
    },
    'username2': { ... }
}
```

### Emission Data Structure
```python
emission_data = {
    'username': {
        'scope1': [
            {
                'category': 'diesel',
                'amount': 50.5,
                'unit': 'liters',
                'date': '2025-01-15',
                'co2e': 135.34
            }
        ],
        'scope2': [
            {
                'category': 'electricity',
                'amount': 450,
                'unit': 'kWh',
                'date': '2025-01-20',
                'co2e': 382.5
            }
        ],
        'scope3': [...]
    }
}
```

---

## 🔄 Key Application Flows

### **1. User Registration & Login Flow**

```
User clicks "Register"
    ↓
Fills username, email, password, company
    ↓
Backend validates (username unique?)
    ↓
Hash password with Werkzeug security
    ↓
Create user entry in users{}
    ↓
Initialize empty emission_data{}
    ↓
Redirect to login page
    ↓
User logs in with credentials
    ↓
Backend verifies password hash
    ↓
Set session variables (user, email, company)
    ↓
Redirect to /dashboard
```

### **2. Emission Data Entry Flow**

```
User on Dashboard clicks "Add Emission Data"
    ↓
Modal opens with form:
  - Scope selector (1, 2, or 3)
  - Category dropdown (dynamically populated)
  - Amount input field
  - Unit selector
    ↓
User fills form and clicks "Calculate & Save"
    ↓
Frontend validates input
    ↓
POST to /api/add-emission with JSON data
    ↓
Backend calculates:
  CO₂e = amount × emission_factor
    ↓
Emission record appended to emission_data[username][scope]
    ↓
Dashboard automatically refreshes charts
    ↓
Success notification displayed
```

### **3. Document Analysis Flow**

```
User uploads utility bill (PDF/image)
    ↓
Frontend sends to POST /api/analyze-document
    ↓
Backend extracts file
    ↓
Determine file type (PDF or image)
    ↓
PDF: convert_from_bytes() → image → OCR
Image: direct OCR with pytesseract
    ↓
Tesseract extracts text
    ↓
parse_extracted_text() analyzes:
  - detect_fuel_type_enhanced(): Identify fuel/electricity
  - extract_amount_enhanced(): Find quantity
  - determine_scope_enhanced(): Assign scope
  - calculate_emissions(): Compute CO₂e
    ↓
Return results with confidence score:
  {
    "scope": "scope2",
    "category": "electricity",
    "amount": 450,
    "unit": "kWh",
    "co2e": 382.5,
    "confidence": 0.98
  }
    ↓
User reviews and confirms (or manually edits)
    ↓
Save to emission_data
```

### **4. AI Consultation Flow**

```
User on Sentinel page types question
    ↓
Clicks "Send"
    ↓
POST /api/gemini-advice with:
  {
    "question_type": "how_to_fix",
    "message": "How can I reduce Scope 1 emissions?"
  }
    ↓
Backend retrieves user emission_data
    ↓
analyze_emission_patterns() extracts:
  - Total emissions
  - Highest scope
  - Top sources
  - Reduction potential
    ↓
Build Gemini prompt with context
    ↓
genai.GenerativeModel("gemini-pro").generate_content(prompt)
    ↓
Parse Gemini response
    ↓
Format response with sections & recommendations
    ↓
Return JSON with AI advice
    ↓
Frontend displays formatted response in chat
    ↓
User can ask follow-up questions
```

### **5. Report Generation Flow**

```
User on Dashboard clicks "My Report"
    ↓
Navigate to /report
    ↓
Backend calls generate_gri_ghg_report():
  - Aggregates user's emission_data
  - Calculates scope totals & percentages
  - Generates 8+ GRI/GHG sections
  - Creates performance metrics
  - Builds recommendations
    ↓
Render report.html with full report data
    ↓
User sees formatted report on screen
    ↓
User clicks "Download PDF"
    ↓
Backend calls generate_pdf_report():
  - Use ReportLab to create PDF
  - Add styled tables, sections, data
  - Embed company info & logo
  - Generate file in memory
    ↓
Return PDF as downloadable attachment
    ↓
Browser downloads as "carbon_report_[user]_[date].pdf"
```

---

## 🔌 API Endpoints Reference

### **General Endpoints**

| Method | Endpoint | Purpose | Returns |
|--------|----------|---------|---------|
| GET | `/` | Landing page | HTML |
| GET/POST | `/login` | User authentication | HTML/redirect |
| GET/POST | `/register` | New user creation | HTML/redirect |
| GET | `/logout` | Clear session | Redirect |
| GET | `/dashboard` | Main dashboard | HTML with charts |
| GET | `/report` | Report generation page | HTML with data |
| POST | `/api/add-emission` | Create emission record | JSON |
| POST | `/api/analyze-document` | OCR & analyze files | JSON |
| POST | `/api/gemini-advice` | Get AI consultation | JSON |
| GET | `/api/generate-report-pdf` | Download PDF report | PDF file |
| GET | `/api/report-data` | Get report JSON | JSON |
| GET | `/sentinel` | AI chat interface | HTML |
| GET | `/marketplace` | Carbon trading | HTML |
| GET | `/services` | Services overview | HTML |
| GET | `/compliance_dashboard` | Compliance tracker | HTML |

---

### **NEW: Compliance Management API Endpoints** ✨

These endpoints manage regulatory compliance standards, clauses, and evidence tracking:

#### **Standards & Framework Management**

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/api/compliance/matrix` | Get compliance matrix for all standards | ✅ Working |
| GET | `/api/compliance/standard/<int:standard_id>` | Get detailed standard info & all clauses | ✅ Working |
| GET | `/api/compliance/clause/<int:clause_id>` | Get clause details with evidence & mappings | ✅ Working |
| GET | `/api/compliance/mapping/<int:clause_id>` | Get clause mappings to other standards | ✅ Working |

#### **Compliance Assessment & Evidence**

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| POST | `/api/compliance/update-status` | Update compliance status for a clause | ✅ Working |
| POST | `/api/compliance/upload-evidence` | Upload evidence file for a clause | ✅ Working |
| POST | `/api/compliance/generate-report` | Generate compliance report | ✅ Working |

---

#### **API Endpoint Details**

##### **1. GET `/api/compliance/matrix`**
Retrieves complete compliance matrix with all standards and clauses.

**Request**:
```http
GET /api/compliance/matrix
Authorization: Login required
```

**Response**:
```json
{
  "success": true,
  "clauses": [
    {
      "id": 1,
      "standard_id": 1,
      "standard_name": "IFRS S1",
      "clause_number": "S1-1",
      "title": "Organizational description",
      "description": "Description of the organization and its value chain",
      "status": "compliant",
      "evidence_count": 2,
      "priority": 1
    },
    ...
  ]
}
```

---

##### **2. GET `/api/compliance/standard/<int:standard_id>`**
Get all clauses and compliance information for a specific standard.

**Request**:
```http
GET /api/compliance/standard/1
Authorization: Login required
```

**Response**:
```json
{
  "success": true,
  "standard": {
    "id": 1,
    "name": "IFRS S1",
    "short_name": "IFRS S1",
    "version": "2023",
    "description": "IFRS S1 General Requirements...",
    "jurisdiction": "Global",
    "category": "Financial Reporting",
    "website": "https://www.ifrs.org/..."
  },
  "clauses": [
    {
      "id": 1,
      "clause_number": "S1-1",
      "title": "Organizational description",
      "priority": 1,
      "status": "compliant",
      "evidence_count": 3,
      "assessment_date": "2025-01-15T10:30:00"
    },
    ...
  ]
}
```

---

##### **3. GET `/api/compliance/clause/<int:clause_id>`**
Get detailed clause information, current status, and all supporting evidence.

**Request**:
```http
GET /api/compliance/clause/5
Authorization: Login required
```

**Response**:
```json
{
  "success": true,
  "clause": {
    "id": 5,
    "standard_id": 2,
    "standard_name": "IFRS S2",
    "clause_number": "S2-3",
    "title": "Greenhouse gas emissions",
    "requirement": "Disclose Scope 1, 2, and 3 GHG emissions...",
    "priority": 1
  },
  "status": {
    "status": "partial",
    "assessment_date": "2025-01-10T09:00:00",
    "next_assessment_date": "2025-04-10",
    "confidence_score": 75
  },
  "evidence": [
    {
      "id": 1,
      "filename": "emissions_report_2024.pdf",
      "description": "Annual GHG inventory",
      "upload_date": "2025-01-15T14:30:00",
      "verified": true
    },
    ...
  ],
  "mappings": [
    {
      "target_standard": "GRI Standards",
      "target_clause": "GRI 305",
      "mapping_type": "equivalent",
      "confidence": 90
    }
  ]
}
```

---

##### **4. POST `/api/compliance/update-status`**
Update the compliance status for a clause (used when performing assessments).

**Request**:
```http
POST /api/compliance/update-status
Content-Type: application/json

{
  "clause_id": 5,
  "status": "partial",
  "comments": "Evidence collected for Scope 1 and 2, Scope 3 still in progress",
  "next_assessment_date": "2025-04-10"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Status updated successfully"
}
```

**Status Values**:
- `compliant`: Clause fully satisfied
- `partial`: Some evidence provided
- `non_compliant`: Not meeting requirements
- `not_assessed`: Not yet evaluated

---

##### **5. POST `/api/compliance/upload-evidence`**
Upload supporting documents as evidence for compliance with a clause.

**Request**:
```http
POST /api/compliance/upload-evidence
Content-Type: multipart/form-data

{
  "evidence_file": <binary file>,
  "clause_id": 5,
  "standard_id": 2,
  "description": "Q4 2024 GHG emissions calculation",
  "evidence_type": "calculation"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Evidence uploaded successfully",
  "evidence_id": 42,
  "filename": "admin_5_20250115_143022_emissions_calc.pdf"
}
```

**Supported File Types**:
- PDF documents (.pdf)
- Excel/CSV (.xlsx, .csv)
- Images (.jpg, .png)
- Text files (.txt, .docx)

---

##### **6. POST `/api/compliance/generate-report`**
Generate a comprehensive compliance report for audit purposes.

**Request**:
```http
POST /api/compliance/generate-report
Content-Type: application/json

{
  "report_type": "full",
  "include_standards": ["IFRS S1", "IFRS S2", "TCFD"],
  "format": "pdf"
}
```

**Response**:
```json
{
  "success": true,
  "report_id": "COMP-20250115-001",
  "file_url": "/static/compliance_reports/COMP-20250115-001.pdf",
  "generated_date": "2025-01-15T15:45:00",
  "summary": {
    "total_standards": 3,
    "compliant": 2,
    "partial": 1,
    "overall_compliance": 83.3
  }
}
```

---

##### **7. GET `/api/compliance/mapping/<int:clause_id>`**
Get all standards that this clause maps to (for cross-standard consistency).

**Request**:
```http
GET /api/compliance/mapping/5
Authorization: Login required
```

**Response**:
```json
{
  "success": true,
  "source_clause": {
    "standard": "IFRS S2",
    "clause_number": "S2-3",
    "title": "Greenhouse gas emissions"
  },
  "mappings": [
    {
      "target_standard": "GRI Standards",
      "target_clause": "GRI 305",
      "mapping_type": "equivalent",
      "confidence": 90,
      "notes": "Both address greenhouse gas emissions reporting"
    },
    {
      "target_standard": "GHG Protocol",
      "target_clause": "GHG-3",
      "mapping_type": "related",
      "confidence": 75,
      "notes": "Both track emissions data over time"
    }
  ]
}
```

---

## 🛠️ Development & Deployment

### **Installation**:
```bash
# Clone repository
git clone <repo-url>
cd Carbon_Tracker

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
source venv/bin/activate      # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# Set Tesseract path in app.py:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### **Running the Application**:
```bash
python app.py
# Server starts at http://localhost:5000
```

### **Environment Variables** (if using .env):
```
GEMINI_API_KEY=your-api-key-here
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### **Database**:
- Default: SQLite at `instance/carbon_tracker.db`
- Auto-created on first run
- Use Flask-Migrate for schema updates

---

## 📈 Analytics & Reporting Standards

### **GRI Standards Covered**:
- **GRI 102**: General Disclosures (organizational info)
- **GRI 103**: Management Approach
- **GRI 201**: Economic Performance
- **GRI 305**: Emissions (GHG-specific)
- **GRI 306**: Waste

### **GHG Protocol Compliance**:
- ✅ Scope 1: Direct emissions (vehicles, heating)
- ✅ Scope 2: Indirect energy (electricity)
- ✅ Scope 3: Other indirect (travel, supply chain)
- ✅ Operational boundary: Control approach
- ✅ Emission factors: DEFRA, IPCC, Malaysia-specific

### **Malaysia-Specific Integration**:
- 🌍 **MGTC** (Malaysian Green Technology Corporation): Guidelines compliance
- 🔋 **SEDA**: Sustainable Energy Development Authority requirements
- 💚 **MyCarbon**: National voluntary reporting platform
- 📊 **Grid Emission Factor**: 0.85 kg CO₂e/kWh (Malaysia average)

---

## 🧪 Testing

### **Test Files** (in `tools/` folder):
- `test_login_dashboard.py`: Authentication flow tests
- `test_routes.py`: Route & endpoint tests
- `inspect_app_import.py`: App configuration inspection

### **Running Tests**:
```bash
python -m pytest tools/test_routes.py -v
python tools/test_login_dashboard.py
```

---

## 🐛 Troubleshooting

### **ESG Module Route Errors** (RESOLVED - January 2026):
```
Error: "BuildError: Could not build url for endpoint 'environmental_module'"
Root Cause: Missing route endpoints for ESG module compatibility
Solution: Added 4 compatibility redirect routes in app.py
  - @app.route('/environmental-module') → environmental_module()
  - @app.route('/social-module') → social_module()
  - @app.route('/governance-module') → governance_module()
  - @app.route('/supply-chain-module') → supply_chain_module()
Status: ✅ FIXED - All ESG module cards now route correctly
```

### **Jinja2 Template Caching Issues** (RESOLVED - January 2026):
```
Error: Template serving stale bytecode despite file updates
Symptoms: Changes to templates not reflecting after file save
Root Cause: Jinja2 template cache accumulating compiled bytecode in memory
Solution: Added app.jinja_env.cache = None in app.py after Flask init
         Forces templates to always load fresh from disk in development
Status: ✅ FIXED - Templates now reload immediately on save
```

### **Missing reportlab Package** (RESOLVED - January 2026):
```
Error: ModuleNotFoundError: No module named 'reportlab'
Symptoms: PDF report generation fails at startup
Solution: pip install reportlab
Status: ✅ FIXED - PDF export fully functional
```

### **Slow Flask Startup** (OPTIMIZED - January 2026):
```
Issue: Gemini model listing taking 30+ seconds at startup
Solution: Commented out verbose model listing logging
         Models still loaded, just silently without output
Status: ✅ OPTIMIZED - Flask now starts in ~5-10 seconds
```

### **Tesseract OCR Issues**:
```
Error: "tesseract is not installed or it's not in your PATH"
Solution: Download from https://github.com/UB-Mannheim/tesseract/wiki
         Set path in app.py: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### **Gemini API Errors**:
```
Error: "No generative models available"
Solution: Check API key in app.py
         Ensure google-generativeai package is installed: pip install google-generativeai
         Test API: curl https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY
```

### **PDF Generation Failures**:
```
Error: "Failed to generate PDF report"
Solution: Ensure ReportLab is installed: pip install reportlab
         Check that document data is valid before generation
```

---

## 🔐 Security Considerations

⚠️ **Development Mode Notes**:
- Default secret key is hardcoded (change for production)
- Mock user database (use proper DB in production)
- API keys exposed in source code (use environment variables)
- No HTTPS enforced (add in production)

### **For Production**:
1. Use environment variables for sensitive data
2. Implement proper database authentication
3. Add CSRF protection & rate limiting
4. Enable HTTPS with SSL certificates
5. Implement proper logging & monitoring
6. Add user permission levels
7. Implement audit logging for all changes

---

## 📚 Key Functions Reference

### **Emission Calculations**
- `calculate_emissions(scope, category, amount, unit)` - Computes CO₂e
- `analyze_emission_patterns(user_data)` - Pattern analysis & recommendations

### **AI & Analytics**
- `get_gemini_advice(user_data, question_type, message)` - Gemini API integration
- `generate_ai_advice(user_data, question_type)` - Fallback advice system
- `generate_gri_ghg_report(user_data, username, user_info)` - Full report generation

### **Document Processing**
- `extract_text_from_image(file_data)` - OCR from images
- `extract_text_from_pdf(file_data)` - PDF to text conversion
- `parse_extracted_text(text)` - Parse OCR output for emission data
- `detect_fuel_type_enhanced(text)` - Identify fuel type from text
- `extract_fuel_quantity_enhanced(text)` - Extract amount from receipt

### **PDF Generation**
- `generate_pdf_report(report_data)` - ReportLab PDF creation

---

## 🎯 Future Enhancement Opportunities

- [ ] Real database migration (PostgreSQL/MySQL)
- [ ] User roles & permission system
- [ ] Real carbon marketplace integration
- [ ] Mobile application
- [ ] Advanced scenario modeling
- [ ] Supplier emissions collaboration
- [ ] Blockchain-based carbon credits
- [ ] Real-time API integrations (utility companies)
- [ ] Machine learning for emission prediction
- [ ] Multi-language support
- [ ] Third-party audit workflows
- [ ] Integration with accounting systems

---

## 📞 Support & Contact

For issues, feature requests, or questions:
- 📧 Email: admin@emittif.io
- 🐛 GitHub Issues: [Repository Issues]
- 💬 Slack Community: [Community Link]

---

## 📜 License

© 2025 EmittiF.io. All rights reserved.

---

**Last Updated**: January 2026
**Version**: 1.0
**Python Version**: 3.8+
**Flask Version**: 2.0+

---

## 🐛 **Known Issues & Limitations**

### **Data Persistence** ⚠️
- **Issue**: All data stored in memory (Python dicts)
- **Impact**: Data lost on server restart
- **Solution**: Implement SQLAlchemy ORM with SQLite/PostgreSQL
- **Priority**: 🔴 CRITICAL

### **Gemini AI Integration** ⚠️
- **Issue**: Requires valid API key, may rate-limit
- **Impact**: Falls back to rule-based system if API fails
- **Solution**: Implement caching, queue system
- **Current Status**: ✅ Fallback working

### **OCR Accuracy** ⚠️
- **Issue**: Tesseract accuracy depends on image quality
- **Impact**: May fail on handwritten or poor-quality documents
- **Solution**: Add manual data entry override (✅ Already exists)
- **Current Status**: ✅ Working

### **Placeholder Routes** ⚠️
- **Issue**: Some routes render templates but have no backend logic
- **Example**: `/profile_settings`, `/carbon_tax_modeling`
- **Solution**: Implement backend logic for these routes
- **Priority**: 🟡 MEDIUM

### **No Real Database** ⚠️
- **Issue**: Uses mock data dictionaries instead of database
- **Impact**: 
  - No persistence
  - No user isolation issues
  - No query optimization
- **Solution**: Migrate to SQLAlchemy
- **Priority**: 🔴 CRITICAL

### **User Role Enforcement** ⚠️
- **Issue**: Roles defined in UI but not enforced in backend
- **Impact**: Any authenticated user can access any page
- **Solution**: Add `@require_role()` decorators
- **Priority**: 🟡 MEDIUM (security)

### **Email Integration** ⚠️
- **Issue**: No email sending functionality
- **Impact**: Notifications, password reset not available
- **Solution**: Implement Flask-Mail with SMTP
- **Priority**: 🟡 MEDIUM

---

## 🚀 **Next Priority Actions**

### **Phase 1: Core Stability** (Weeks 1-2)
- [ ] Migrate data to SQLAlchemy ORM
- [ ] Implement real SQLite/PostgreSQL database
- [ ] Add unit tests (pytest)
- [ ] Fix data persistence issue

### **Phase 2: Complete Features** (Weeks 3-4)
- [ ] Implement `/profile_settings` backend
- [ ] Implement `/company_settings` backend
- [ ] Add email notification system
- [ ] Implement Courses page

### **Phase 3: User Roles & Security** (Weeks 5-6)
- [ ] Enforce role-based access control
- [ ] Add Admin dashboard
- [ ] Implement Auditor approval workflow
- [ ] Add supplier invitation system

### **Phase 4: Advanced Features** (Weeks 7-8)
- [ ] Carbon tax modeling engine
- [ ] Marketplace payment integration
- [ ] Real-time audit logging
- [ ] Supplier collaboration tools

### **Phase 5: Polish & Deploy** (Weeks 9-10)
- [ ] API documentation (Swagger)
- [ ] Performance optimization
- [ ] Security audit
- [ ] Production deployment

---

## 📝 **Testing Guide**

### **Quick Test Credentials**
```
Username: admin
Password: password
Email: admin@emittif.io
Company: EmittiF Demo
```

### **Test Scenarios**

#### **Scenario 1: Add Emissions & View Dashboard**
1. Login with credentials above
2. Click "Add Emission Data"
3. Select Scope 1 → Diesel Fuel
4. Enter amount: 50.5 liters
5. Click "Calculate & Save"
6. Return to dashboard → Charts should update

#### **Scenario 2: Upload & Process Document**
1. From sidebar, navigate to "Source Documents"
2. Click "Upload Document"
3. Upload a fuel receipt or utility bill
4. System extracts text via Tesseract
5. Confirm or edit the parsed data
6. Save → Emission record created

#### **Scenario 3: Generate Report**
1. Go to Dashboard
2. Click "My Report"
3. Review GRI/GHG report sections
4. Click "Download PDF"
5. Open PDF in browser/file explorer

#### **Scenario 4: AI Consultation**
1. Navigate to "Carbon Sentinel" from Services dropdown
2. View your emission stats
3. Type a question: "How can I reduce Scope 1 emissions?"
4. Click Send
5. AI response should appear in chat

#### **Scenario 5: Compliance Tracking**
1. Go to Dashboard
2. Click [Audit] dropdown → "Compliance & Standards"
3. View 9 standards and their status
4. Check overall compliance score
5. Review upcoming deadlines

---

## 🔗 **Related Documentation**

- [Installation Guide](#installation)
- [API Reference](#api-endpoints-reference)
- [Data Model](#data-model)
- [Emission Calculation System](#emission-calculation-system)
- [Standards Compliance](#emissions-inventory)

---

## 💬 **Support & Contribution**

### **Reporting Issues**
Please report bugs with:
- Screenshots/videos
- Steps to reproduce
- Browser/OS version
- Expected vs actual behavior

### **Contributing**
1. Fork repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes with tests
4. Submit pull request with description

### **Contact**
- 📧 Email: admin@emittif.io
- 💼 Website: https://emittif.io
- 🐙 GitHub: https://github.com/VISWARAM98/Carbon_Tracker

---

**Last Updated**: January 2, 2026 (Latest Bug Fixes Applied)
**Version**: 1.1 (Production-Ready with Critical Fixes)
**Python Version**: 3.8+
**Flask Version**: 2.0+
**Status**: ✅ All critical bugs fixed, ESG modules fully functional

Developer setup / running locally
---------------------------------
1. Create and activate a virtual environment (example on Windows PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
pip install Flask-Migrate
```

3. Initialize migrations (first run only) and create DB:

```powershell
$env:FLASK_APP='app.py'
python -m flask db init
python -m flask db migrate -m "initial migration"
python -m flask db upgrade
```

Note: the project contains a `migrations/` folder generated when migrations were initialized. If the DB has old schema or you are in a dev environment, it's acceptable to remove `instance/carbon_tracker.db` and re-run the migration commands.

4. Run the app:

```powershell
python app.py
# or
flask run
```

Project-specific conventions and patterns
----------------------------------------
- Templates extend `templates/base.html` for consistent navbar and flash handling. Use `{% block content %}` and `{% block scripts %}`.
- `EMISSION_FACTORS` is defined in `app.py` as an in-memory dictionary and passed to `calculate.html` where client-side JavaScript uses it to populate sources.
- Routes rely on `Flask-Login` (`@login_required`) to protect pages.
- Emission calculation contract: inputs (scope:string, source:string, activity_data:float) → output (total_emission: float saved on `Emission`).

How to add a new emission source
--------------------------------
1. Add the source and factor to the `EMISSION_FACTORS` dict in `app.py`. Example:

```py
EMISSION_FACTORS['Scope 2']['New Source'] = 0.42
```

2. If the client JS needs a custom unit, add a mapping in the `calculate.html` JavaScript `units` object.

3. No schema change required since `Emission` stores `source`, `emission_factor` and raw numbers.

Testing and troubleshooting tips
-------------------------------
- TemplateNotFound errors: confirm the template file exists under `templates/` and that the route uses the correct name (e.g. `render_template('calculate.html')`).
- `flask_migrate` import error: ensure `Flask-Migrate` is installed in the virtual environment (`pip install Flask-Migrate`).
- Migration failures when altering existing tables: in a dev environment prefer recreating the DB (`Remove instance/carbon_tracker.db`) and re-running `flask db upgrade`. For production, craft an Alembic migration preserving data (use `op.batch_alter_table` with nullable transitional columns).
- If charts show no data: confirm `Emission.date` values and that the logged-in user has `Emission` rows; `/api/emissions` can be used to validate returned JSON.

Next steps and suggestions
--------------------------
- Add unit tests for emission calculation (e.g., pytest small suite asserting correct multiplication and DB save logic).
- Add form CSRF protection (Flask-WTF) for improved security.
- Extract larger blueprint boundaries as the app grows (e.g., `auth`, `emissions`, `reports` blueprints) to keep `app.py` manageable.

Contact / support
-----------------
If anything in this README is unclear or you want me to expand any section (routes, tests, deploy steps), tell me which area to focus on and I will update the documentation or implement the change.
