# 🔧 **COMPLETE FUNCTIONS & BUTTONS DOCUMENTATION**

**Last Updated**: April 1, 2026  
**Version**: 2.0 - Complete Technical Reference  
**Total Routes**: 70+  
**Total Functions**: 40+  
**Total API Endpoints**: 35+  

---

## 📋 **TABLE OF CONTENTS**

1. [All Routes & Functions](#all-routes--functions)
2. [Buttons & UI Elements](#buttons--ui-elements)
3. [Report Generation Process](#report-generation-process)
4. [Calculation Functions](#calculation-functions)
5. [AI & Analytics Functions](#ai--analytics-functions)
6. [Database Operations](#database-operations)
7. [JavaScript Functions](#javascript-functions)

---

## 🛣️ **All Routes & Functions**

### **PUBLIC ROUTES** (No Authentication Required)

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/` | GET | Display landing page | Home/welcome page with services overview |
| `/login` | GET, POST | User login | Authenticate user with email/password |
| `/register` | GET, POST | User registration | Create new user account |
| `/logout` | GET | Logout user | Clear session and redirect to home |

### **MAIN DASHBOARD ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/dashboard` | GET | `dashboard_home()` | Main dashboard with charts and emission summary |
| `/report` | GET | `generate_report()` | GRI/GHG compliance report page |
| `/api/report-data` | GET | `report_data()` | Fetch report data as JSON |
| `/api/generate-report-pdf` | GET | `generate_report_pdf()` | Generate and download PDF report |
| `/sentinel` | GET | `sentinel_page()` | AI consultant chat interface |
| `/services` | GET | `services_page()` | Services overview page |

### **COMPLIANCE & ESG ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/compliance_dashboard` | GET | `compliance_dashboard()` | Compliance matrix with 9 standards |
| `/api/compliance/matrix` | GET | `get_compliance_matrix()` | Complete compliance matrix data |
| `/api/compliance/standard/<id>` | GET | `get_standard_details()` | Get clauses for specific standard |
| `/api/compliance/clause/<id>` | GET | `get_clause_details()` | Get clause with evidence links |
| `/api/compliance/update-status` | POST | `update_compliance_status()` | Update clause assessment status |
| `/api/compliance/upload-evidence` | POST | `upload_evidence()` | Upload evidence files |
| `/api/compliance/generate-report` | POST | `generate_compliance_report()` | Generate compliance assessment report |
| `/api/compliance/mapping/<id>` | GET | `get_clause_mapping()` | View clause mappings across standards |

### **ESG DATA CENTER ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/esg-data-center` | GET | `esg_data_center()` | ESG hub with 4 modules and stats |
| `/esg-environmental` | GET | `esg_environmental()` | Environmental data collection (Scope 1,2,3) |
| `/esg-social` | GET | `esg_social()` | Social & workforce data collection |
| `/esg-governance` | GET | `esg_governance()` | Governance & ethics data collection |
| `/esg-supply-chain` | GET | `esg_supply_chain()` | Supply chain (Scope 3) data collection |
| `/environmental-module` | GET | `environmental_module()` | Redirect to esg_environmental |
| `/social-module` | GET | `social_module()` | Redirect to esg_social |
| `/governance-module` | GET | `governance_module()` | Redirect to esg_governance |
| `/supply-chain-module` | GET | `supply_chain_module()` | Redirect to esg_supply_chain |

### **USER SETTINGS ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/profile_settings` | GET, POST | `profile_settings()` | Edit user profile and ESG responsibilities |
| `/company_settings` | GET, POST | `company_settings()` | Edit company configuration |

### **AI & DOCUMENT ANALYSIS ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/ai-consultant` | GET | `ai_consultant()` | AI chat interface |
| `/api/gemini-advice` | POST | `get_gemini_advice()` | Get advice from Google Gemini AI |
| `/api/ai-advice` | POST | `get_ai_advice()` | Get fallback AI advice |
| `/api/analyze-document` | POST | `analyze_document()` | OCR document analysis with Tesseract |
| `/api/add-emission` | POST | `add_emission()` | Manually add emission record |

### **ENVIRONMENTAL DATA ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/api/environmental/create` | POST | `create_environmental_data()` | Create new environmental record |
| `/api/environmental/list` | GET | `list_environmental_data()` | Get all environmental records |
| `/api/environmental/update/<id>` | PUT | `update_environmental_data()` | Update environmental record |
| `/api/environmental/submit/<id>` | POST | `submit_environmental_data()` | Submit for approval |
| `/api/environmental/upload-evidence/<id>` | POST | `upload_environmental_evidence()` | Attach supporting documents |
| `/api/environmental/evidence/<id>` | GET | `get_environmental_evidence()` | Get evidence for record |
| `/api/environmental/delete-evidence/<id>` | DELETE | `delete_environmental_evidence()` | Remove evidence file |
| `/api/environmental/intensity` | GET | `get_environmental_intensity()` | Calculate intensity metrics |

### **SOCIAL DATA ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/api/social/save` | POST | `save_social_data()` | Save workforce and social data |
| `/api/social/data` | GET | `get_social_data()` | Retrieve social data |
| `/api/social/survey/create` | POST | `create_survey()` | Create employee survey |
| `/api/social/survey/responses` | GET | `get_survey_responses()` | Get survey results |
| `/survey/<token>` | GET | `employee_survey()` | Survey landing page (public token-based) |
| `/api/survey/validate/<token>` | GET | `validate_survey_token()` | Validate survey token |
| `/api/survey/submit` | POST | `submit_survey()` | Submit survey response |

### **GOVERNANCE DATA ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/api/governance/save` | POST | `save_governance_data()` | Save governance data |
| `/api/governance/data` | GET | `get_governance_data()` | Retrieve governance records |

### **SUPPLY CHAIN ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/api/supply_chain/suppliers` | GET | `list_suppliers()` | Get all suppliers |
| `/api/supply_chain/invite` | POST | `invite_supplier()` | Send supplier invitation |
| `/api/supply_chain/resend/<id>` | POST | `resend_invitation()` | Resend invitation to supplier |
| `/api/supply_chain/supplier/<id>` | DELETE | `delete_supplier()` | Remove supplier record |
| `/api/supply_chain/reminders` | POST | `send_reminders()` | Send completion reminders |
| `/api/supply_chain/export` | GET | `export_supply_chain_data()` | Export supplier data |

### **EVIDENCE & AUDIT ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/api/evidence/upload` | POST | `upload_evidence()` | Upload supporting documents |
| `/api/evidence/link` | POST | `link_evidence()` | Link evidence to clauses |

### **DASHBOARD STATS ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/api/dashboard/stats` | GET | `get_dashboard_stats()` | Get dashboard metrics and charts |

### **CARBON TOOLS ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/carboniq` | GET | `carboniq()` | CarbonIQ calculator tool |
| `/carbon_roadmap` | GET | `carbon_roadmap()` | Carbon reduction roadmap planner |
| `/api/roadmap/emissions` | GET | `roadmap_emissions()` | Get historical emissions |
| `/api/roadmap/generate` | POST | `generate_roadmap()` | Generate reduction roadmap |

### **MARKETPLACE ROUTES**

| Route | Method | Function | Purpose |
|-------|--------|----------|---------|
| `/marketplace` | GET | `marketplace_page()` | Carbon offset marketplace |
| `/api/marketplace/enquiry` | POST | `marketplace_enquiry()` | Send marketplace inquiry |
| `/api/marketplace/listing` | POST | `create_marketplace_listing()` | Create new listing |

---

## 🔘 **Buttons & UI Elements**

### **NAVIGATION BAR BUTTONS** (`base_auth.html`)

| Button | Location | Icon | Function | Route |
|--------|----------|------|----------|-------|
| **Logo/Home** | Left navbar | 🏠 | Go to dashboard | `/dashboard` |
| **Audit** | Center navbar | 📊 | Dropdown menu | Expands submenu |
| **Services** | Center navbar | 🛠️ | Dropdown menu | Expands submenu |
| **User Profile** | Right navbar | 👤 | Dropdown menu | Expands profile menu |

### **AUDIT DROPDOWN MENU**

| Item | Icon | Function | Route |
|------|------|----------|-------|
| **ESG Data Center** | 🌱 | Access all ESG modules | `/esg-data-center` |
| **Compliance Dashboard** | ✅ | View compliance matrix | `/compliance_dashboard` |
| **Source Documents** | 📄 | Upload/manage documents | `/source_documents` |
| **Verification Mode** | 🔍 | Auditor verification view | `/verification_mode` |
| **Audit Trail** | 📋 | View all user actions | `/audit_trail` |

### **SERVICES DROPDOWN MENU**

| Item | Icon | Function | Route |
|------|------|----------|-------|
| **AI Consultant** | 🤖 | Chat with Gemini AI | `/ai-consultant` |
| **My Report** | 📄 | Generate GRI/GHG report | `/report` |
| **Marketplace** | 🌳 | Browse carbon offsets | `/marketplace` |
| **CarbonIQ** | 🧮 | Carbon calculator | `/carboniq` |
| **Carbon Roadmap** | 🛣️ | Reduction planning | `/carbon_roadmap` |
| **Employee Survey** | 📊 | Create/view surveys | Survey creation |

### **USER PROFILE DROPDOWN MENU**

| Item | Icon | Function | Action |
|------|------|----------|--------|
| **Profile Settings** | ⚙️ | Edit user information | `/profile_settings` |
| **Company Settings** | 🏢 | Edit company details | `/company_settings` |
| **Logout** | 🚪 | Sign out | `/logout` |

### **DASHBOARD PAGE BUTTONS** (`/dashboard`)

| Button | Icon | Location | Function | Action |
|--------|------|----------|----------|--------|
| **Add Emission Data** | ➕ | Main card | Add manual emission | Opens modal form |
| **Analyze Document** | 📸 | Main card | OCR analysis | File upload |
| **My Report** | 📄 | Main card | View GRI report | Navigates to `/report` |
| **Download Report** | 📥 | Report page | Download as PDF | API: `/api/generate-report-pdf` |
| **View Full Report** | 👁️ | Report page | Display HTML report | Inline display |

### **ESG DATA CENTER BUTTONS** (`/esg-data-center`)

| Button | Module | Icon | Function | Route |
|--------|--------|------|----------|-------|
| **Environmental Card** | Environmental | 🌱 | Access environmental data | `/esg-environmental` |
| **Social Card** | Social | 👥 | Access social data | `/esg-social` |
| **Governance Card** | Governance | ⚖️ | Access governance data | `/esg-governance` |
| **Supply Chain Card** | Supply Chain | 🏭 | Access supply chain data | `/esg-supply-chain` |

### **ENVIRONMENTAL MODULE BUTTONS** (`/esg-environmental`)

| Tab/Button | Function | Action |
|------------|----------|--------|
| **Energy Tab** | Track energy consumption | Scope 2 data entry |
| **Water Tab** | Track water usage | Water consumption data |
| **Emissions Tab** | Track direct emissions | Scope 1 data entry |
| **Waste Tab** | Track waste management | Waste disposal data |
| **Save Button** | Submit data | POST to `/api/environmental/create` |
| **Attach Evidence** | Upload documents | File upload handler |
| **Submit for Review** | Approval workflow | POST to `/api/environmental/submit/<id>` |

### **SOCIAL MODULE BUTTONS** (`/esg-social`)

| Tab/Button | Function | Action |
|------------|----------|--------|
| **Workforce Tab** | Employee data | Headcount & demographics |
| **Safety Tab** | Safety metrics | Incidents & training |
| **Training Tab** | Training programs | Hours & participants |
| **Community Tab** | CSR activities | Community engagement |
| **Diversity Tab** | Diversity metrics | Gender/ethnicity ratios |
| **Create Survey** | Employee survey | POST to `/api/social/survey/create` |
| **Import Responses** | Import survey data | Integrate survey results |
| **Save Button** | Submit data | POST to `/api/social/save` |

### **GOVERNANCE MODULE BUTTONS** (`/esg-governance`)

| Tab/Button | Function | Action |
|------------|----------|--------|
| **Risk Tab** | Risk management | Risk identification/mitigation |
| **Compliance Tab** | Compliance tracking | Regulatory compliance |
| **Ethics Tab** | Ethics & conduct | Code of conduct |
| **Board Tab** | Board composition | Diversity metrics |
| **Tax Tab** | Tax strategy | Carbon tax modeling |
| **Save Button** | Submit data | POST to `/api/governance/save` |

### **SUPPLY CHAIN BUTTONS** (`/esg-supply-chain`)

| Button | Function | Action |
|--------|----------|--------|
| **Add Supplier** | Add new supplier | Opens form |
| **Invite Supplier** | Send survey link | POST to `/api/supply_chain/invite` |
| **Resend Invitation** | Resend to non-respondents | POST to `/api/supply_chain/resend/<id>` |
| **Delete Supplier** | Remove from list | DELETE to `/api/supply_chain/supplier/<id>` |
| **Send Reminders** | Notify pending | POST to `/api/supply_chain/reminders` |
| **Export Data** | Download CSV | GET to `/api/supply_chain/export` |

### **SENTINEL (AI CONSULTANT) BUTTONS** (`/sentinel`)

| Button | Icon | Function | Action |
|--------|------|----------|--------|
| **Send Message** | ✈️ | Submit question to AI | POST to `/api/gemini-advice` |
| **Quick Questions** | 💡 | Pre-defined questions | Triggers Gemini AI |
| **How to Fix** | 🔧 | Get reduction strategies | Gemini analysis |
| **New Chat** | ➕ | Start fresh conversation | Clears chat history |

### **COMPLIANCE DASHBOARD BUTTONS** (`/compliance_dashboard`)

| Button | Function | Action |
|--------|----------|--------|
| **Update Status** | Change compliance status | Marks as compliant/partial/non-compliant |
| **Upload Evidence** | Attach proof document | POST to `/api/compliance/upload-evidence` |
| **Generate Report** | Create compliance report | POST to `/api/compliance/generate-report` |
| **View Mapping** | See standard relationships | GET to `/api/compliance/mapping/<id>` |

---

## 📊 **Report Generation Process**

### **GRI/GHG COMPLIANCE REPORT** (`/report` → `/api/generate-report-pdf`)

#### **Step 1: Data Preparation**
```
User navigates to /report
  ↓
Fetch user emissions data from database
  ↓
Calculate totals per scope (Scope 1, 2, 3)
  ↓
Compute CO₂e equivalents using emission factors
```

#### **Step 2: Report Structure**
The generated PDF includes:

1. **Report Metadata** (5 pages)
   - Report ID & generation date
   - Organization name
   - Reporting period
   - Report version
   - Assurance level

2. **Organizational Information** (GRI 102)
   - Company profile
   - Organizational structure
   - Geographic locations
   - Number of employees
   - Revenue (if available)

3. **GHG Protocol Alignment**
   - Scopes covered
   - Boundaries defined
   - Organizational boundaries
   - Operational boundaries
   - Equity share basis

4. **Emissions Inventory**
   - Scope 1: Direct emissions
     - Fuel combustion
     - Refrigerants
     - Company vehicles
   - Scope 2: Indirect (electricity)
     - Purchased electricity
     - Grid location-based
     - Market-based (if available)
   - Scope 3: Value chain
     - Business travel
     - Waste
     - Supply chain

5. **Performance Metrics** (GRI 305)
   - Total emissions trend
   - Emissions per unit
   - Intensity ratios
   - Year-over-year changes

6. **Management Approach**
   - Reduction targets
   - Initiatives in progress
   - Expected improvements
   - Timeline

7. **Risk Assessment**
   - Physical climate risks
   - Transition risks
   - Supply chain vulnerabilities

8. **Data Quality & Recommendations**
   - Data sources used
   - Estimation methods
   - Confidence intervals
   - Areas for improvement

#### **Step 3: PDF Generation**
```
Using ReportLab library:
  ↓
Create PDF document object
  ↓
Add report pages/sections sequentially
  ↓
Insert tables with emission data
  ↓
Add charts (matplotlib/plotly integration)
  ↓
Generate file in-memory BytesIO
  ↓
Return as download response
```

#### **Step 4: Download & Export**
```
PDF generated successfully
  ↓
Set response headers:
   - Content-Type: application/pdf
   - Content-Disposition: attachment; filename=report_YYYY.pdf
  ↓
Stream file to browser
  ↓
User downloads to local machine
```

#### **Function: `generate_report_pdf()`** (app.py line 3525)

```python
@app.route('/api/generate-report-pdf')
@login_required
def generate_report_pdf():
    """Generate and download GRI/GHG compliance PDF report"""
    # 1. Fetch user data
    user = User.query.filter_by(id=session['user_id']).first()
    
    # 2. Calculate totals per scope
    scope1_total = calculate_scope1_total(user.id)
    scope2_total = calculate_scope2_total(user.id)
    scope3_total = calculate_scope3_total(user.id)
    
    # 3. Create report data dict
    report_data = {
        'report_id': f"RPT-{user.id}-{datetime.now().strftime('%Y%m%d')}",
        'date_generated': datetime.now(),
        'organization': user.company_name,
        'scope1': scope1_total,
        'scope2': scope2_total,
        'scope3': scope3_total,
        # ... more data
    }
    
    # 4. Generate PDF using generate_pdf_report()
    pdf_buffer = generate_pdf_report(report_data)
    
    # 5. Return as download
    return send_file(pdf_buffer, mimetype='application/pdf', 
                    as_attachment=True, 
                    download_name=f"Report_{user.id}_{datetime.now().year}.pdf")
```

#### **Function: `generate_gri_ghg_report()`** (app.py line 2119)

```python
def generate_gri_ghg_report(user_data, username, user_info):
    """
    Generate comprehensive GRI & GHG Protocol aligned report
    
    Args:
        user_data: Dict with emission calculations
        username: User identifier
        user_info: User profile information
    
    Returns:
        Dict with report sections ready for PDF generation
    """
    report = {
        'title': 'GRI & GHG Protocol Compliance Report',
        'sections': [
            {'name': 'Executive Summary', 'content': generate_exec_summary()},
            {'name': 'GRI 102', 'content': generate_gri_102()},
            {'name': 'GHG Protocol', 'content': generate_ghg_protocol()},
            {'name': 'Emissions Inventory', 'content': generate_inventory()},
            {'name': 'Performance Metrics', 'content': generate_metrics()},
            # ... more sections
        ]
    }
    return report
```

---

### **COMPLIANCE ASSESSMENT REPORT** (`/api/compliance/generate-report`)

#### **Report Components**

1. **Compliance Matrix**
   - 9 standards × ~45 clauses
   - Status: Compliant/Partial/Non-compliant
   - Risk level: High/Medium/Low

2. **Standards Included**
   - IFRS S1 (General Requirements)
   - IFRS S2 (Climate-related Disclosures)
   - TCFD (Task Force on Climate-related Financial Disclosures)
   - ISO 14064-1 (Quantification & reporting of GHG)
   - GHG Protocol (Corporate Standard)
   - GRI Standards (Global Reporting Initiative)
   - MGTC (Malaysia Green Technology Corporation)
   - SEDA (Sustainable Energy Development Authority)

3. **Evidence Tracking**
   - File uploads linked to clauses
   - Audit trail of submissions
   - Review/approval workflow

4. **Risk Assessment**
   - Non-compliant clauses flagged
   - Remediation timeline
   - Responsible party assignments

#### **Generation Function** (app.py line 4173)

```python
@app.route('/api/compliance/generate-report', methods=['POST'])
@login_required
def generate_compliance_report():
    """Generate compliance assessment report"""
    data = request.json
    
    # Get all standards
    standards = ComplianceStandard.query.all()
    
    # Get user compliance status
    report_data = []
    for standard in standards:
        clauses = ComplianceClause.query.filter_by(standard_id=standard.id).all()
        
        for clause in clauses:
            status = UserComplianceStatus.query.filter_by(
                user_id=session['user_id'],
                clause_id=clause.id
            ).first()
            
            report_data.append({
                'standard': standard.name,
                'clause': clause.requirement,
                'status': status.status if status else 'Not Started',
                'evidence': status.evidence_files if status else []
            })
    
    # Generate PDF/XLSX report
    return jsonify({'report': report_data, 'status': 'success'})
```

---

## 🧮 **Calculation Functions**

### **Emission Calculations**

#### **Main Function: `calculate_emissions()`** (app.py line 1659)

```python
def calculate_emissions(scope, category, amount, unit):
    """
    Calculate CO₂e from activity data
    
    Parameters:
        scope: 1, 2, or 3
        category: Specific emission source
        amount: Activity quantity
        unit: kg, tons, kWh, km, etc.
    
    Returns:
        CO₂e in metric tons
    """
    # 1. Get emission factor from database/dict
    emission_factor = EMISSION_FACTORS[scope][category]
    
    # 2. Convert unit to standard (kg)
    if unit == 'tons':
        amount_kg = amount * 1000
    elif unit == 'kWh':
        amount_kg = amount  # Already in standard form
    
    # 3. Calculate CO₂e
    co2e = (amount_kg * emission_factor) / 1000
    
    # 4. Store in database
    emission = Emission(
        user_id=session['user_id'],
        scope=scope,
        category=category,
        activity_data=amount,
        emission_factor=emission_factor,
        total_emission=co2e,
        date=datetime.now()
    )
    db.session.add(emission)
    db.session.commit()
    
    return co2e
```

#### **Intensity Calculations**

```python
def calculate_energy_intensity(energy_data, company_factors):
    """CO₂e per unit of energy consumed"""
    return total_co2e / total_energy_kwh

def calculate_water_intensity(water_data, company_factors):
    """CO₂e per cubic meter of water"""
    return total_co2e / total_water_m3

def calculate_waste_intensity(waste_data, company_factors):
    """CO₂e per ton of waste"""
    return total_co2e / total_waste_tons

def calculate_land_intensity(land_data, company_factors):
    """CO₂e per hectare of land"""
    return total_co2e / total_land_hectares
```

---

## 🤖 **AI & Analytics Functions**

### **Gemini AI Integration**

#### **Function: `get_gemini_advice()`** (app.py line 3304)

```python
@app.route('/api/gemini-advice', methods=['POST'])
@login_required
def get_gemini_advice():
    """Get advice from Google Gemini AI"""
    data = request.json
    question_type = data.get('type')  # how_to_fix, reduction, offsetting, etc.
    user_message = data.get('message')
    
    # Get user emission data for context
    user_emissions = get_user_emissions(session['user_id'])
    
    # Prepare prompt with context
    context = f"""
    User Emissions Data:
    - Scope 1: {user_emissions['scope1']} tCO₂e
    - Scope 2: {user_emissions['scope2']} tCO₂e
    - Scope 3: {user_emissions['scope3']} tCO₂e
    
    Question Type: {question_type}
    User Question: {user_message}
    """
    
    # Call Gemini API
    response = genai.GenerativeModel('gemini-pro').generate_content(context)
    
    return jsonify({
        'response': response.text,
        'type': question_type,
        'timestamp': datetime.now()
    })
```

### **Fallback AI Advice**

#### **Function: `generate_ai_advice()`** (app.py line 1733)

```python
def generate_ai_advice(user_data, question_type="general"):
    """Fallback advice if Gemini unavailable"""
    
    if question_type == "how_to_fix":
        return generate_fix_advice(user_data)
    elif question_type == "reduction":
        return generate_reduction_advice(user_data)
    elif question_type == "offsetting":
        return generate_offsetting_advice(user_data)
    elif question_type == "compliance":
        return generate_compliance_advice(user_data)
    else:
        return generate_general_advice(user_data)
```

#### **Specific Advice Functions**

```python
def generate_fix_advice(analysis):
    """Provide specific reduction strategies"""
    # Analyze emission breakdown
    # Suggest top 3 reduction opportunities
    # Provide implementation steps
    # Estimate potential savings

def generate_reduction_advice(analysis):
    """Long-term reduction roadmap"""
    # SBTi aligned targets
    # Phased implementation plan
    # Investment requirements
    # Timeline and milestones

def generate_offsetting_advice(analysis):
    """Carbon offset recommendations"""
    # Verified offset projects
    # Cost estimates
    # Co-benefits
    # Certification standards

def generate_compliance_advice(analysis):
    """Regulatory compliance guidance"""
    # Applicable standards
    # Disclosure requirements
    # Timeline for implementation
    # Documentation needed
```

---

## 💾 **Database Operations**

### **Core Models**

```python
class User(UserMixin, db.Model):
    """User authentication & profile"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(200))
    company_name = db.Column(db.String(200))
    emissions = db.relationship('Emission', backref='user')

class Emission(db.Model):
    """Individual emission records"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    scope = db.Column(db.String(50))  # 1, 2, or 3
    category = db.Column(db.String(100))
    activity_data = db.Column(db.Float)
    emission_factor = db.Column(db.Float)
    total_emission = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.now)

class ComplianceStandard(db.Model):
    """Compliance frameworks"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  # IFRS S1, TCFD, ISO 14064, etc.
    description = db.Column(db.Text)
    clauses = db.relationship('ComplianceClause', backref='standard')

class ESGDataModule(db.Model):
    """Environmental data records"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    module_type = db.Column(db.String(50))  # environmental, social, governance
    data = db.Column(db.JSON)  # Flexible data storage
    status = db.Column(db.String(20))  # draft, submitted, approved

class SupplierInvitation(db.Model):
    """Supply chain supplier tracking"""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer)
    supplier_name = db.Column(db.String(200))
    email = db.Column(db.String(150))
    status = db.Column(db.String(50))  # pending, responded, declined
    token = db.Column(db.String(200), unique=True)  # Survey token
```

---

## 🔧 **JavaScript Functions**

### **Dashboard Functions** (`static/js/main.js`)

```javascript
// Handle scope selection change
function handleScopeChange(scope) {
    // Update categories dropdown based on scope
    const categories = {
        1: ['Fuel Combustion', 'Vehicles', 'Refrigerants'],
        2: ['Purchased Electricity', 'Purchased Heat'],
        3: ['Business Travel', 'Waste', 'Supply Chain']
    };
    updateCategoriesDropdown(categories[scope]);
}

// Calculate CO₂e when form inputs change
function calculateCO2e() {
    const scope = document.getElementById('scope').value;
    const category = document.getElementById('category').value;
    const amount = document.getElementById('amount').value;
    const unit = document.getElementById('unit').value;
    
    // Fetch from backend
    fetch('/api/calculate-emissions', {
        method: 'POST',
        body: JSON.stringify({ scope, category, amount, unit })
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('result').innerText = 
            `${data.co2e.toFixed(2)} tCO₂e`;
    });
}

// Open/close modals
function openAddDataModal() {
    document.getElementById('addDataModal').style.display = 'block';
}

function closeAddDataModal() {
    document.getElementById('addDataModal').style.display = 'none';
}

// Handle form submission
function handleEmissionFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(document.getElementById('emissionForm'));
    
    fetch('/api/add-emission', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast('Emission data added successfully');
            location.reload();
        }
    });
}
```

### **Sentinel (AI Consultant) Functions** (`templates/sentinel.html`)

```javascript
// Send message to Gemini AI
function sendMessage() {
    const message = document.getElementById('chatInput').value;
    const type = document.getElementById('questionType').value;
    
    fetch('/api/gemini-advice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, type })
    })
    .then(r => r.json())
    .then(data => {
        addAIMessage('AI Consultant', data.response, type);
    });
}

// Quick question handlers
document.querySelectorAll('.quick-question').forEach(btn => {
    btn.addEventListener('click', () => {
        const question = btn.textContent;
        getGeminiAdvice('general', question);
    });
});

// How to Fix button
document.getElementById('howToFixBtn').addEventListener('click', () => {
    getGeminiAdvice('how_to_fix', 'Analyze my emissions and provide reduction strategies');
});

// New Chat button
document.getElementById('newChatBtn').addEventListener('click', () => {
    document.getElementById('chatMessages').innerHTML = '';
    addAIMessage('System', 'Chat cleared. How can I assist you?', 'general');
});
```

### **Navigation Functions** (`templates/base_auth.html`)

```javascript
// Dropdown hover effects
document.querySelectorAll('.group').forEach(dropdown => {
    dropdown.addEventListener('mouseenter', function() {
        const menu = this.querySelector('.dropdown-menu-custom');
        if (menu) {
            menu.classList.remove('invisible', 'opacity-0');
            menu.classList.add('visible', 'opacity-100');
        }
    });
    
    dropdown.addEventListener('mouseleave', function() {
        const menu = this.querySelector('.dropdown-menu-custom');
        if (menu) {
            setTimeout(() => {
                menu.classList.remove('visible', 'opacity-100');
                menu.classList.add('invisible', 'opacity-0');
            }, 300);
        }
    });
});

// Mobile dropdown behavior
document.querySelector('.relative.group:last-child')?.addEventListener('click', (e) => {
    if (window.innerWidth < 768) {
        e.preventDefault();
        const menu = this.querySelector('.dropdown-menu-custom');
        menu.classList.toggle('visible');
    }
});

// Active link highlighting
const currentPath = window.location.pathname;
document.querySelectorAll('.nav-link-custom').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
        link.classList.add('active');
    }
});
```

### **ESG Module Functions** (various templates)

```javascript
// Tab switching
function switchTab(tab) {
    ['tab1', 'tab2', 'tab3'].forEach(t => {
        document.getElementById(t).classList.add('hidden');
        document.getElementById(t + '-btn').classList.remove('active');
    });
    document.getElementById(tab).classList.remove('hidden');
    document.getElementById(tab + '-btn').classList.add('active');
}

// Live calculations in governance
function calcRisk() {
    const identified = parseFloat(document.getElementById('sig-risks').value) || 0;
    const mitigated = parseFloat(document.getElementById('risks-mitigated').value) || 0;
    const riskCoverage = identified > 0 ? (mitigated / identified * 100).toFixed(1) : 0;
    document.getElementById('risk-coverage').innerText = riskCoverage + '%';
}

// Evidence file handling
function uploadEvidence(recordId) {
    const fileInput = document.getElementById('evidence-file');
    const file = fileInput.files[0];
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('record_id', recordId);
    
    fetch(`/api/environmental/upload-evidence/${recordId}`, {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        showToast('Evidence uploaded successfully');
    });
}
```

---

## ⚙️ **Additional Utility Functions**

### **Document Analysis** (OCR)

```python
@app.route('/api/analyze-document', methods=['POST'])
@login_required
def analyze_document():
    """Analyze uploaded documents with OCR and AI"""
    file = request.files['file']
    
    # Convert PDF/image to text
    if file.filename.endswith('.pdf'):
        text = extract_text_from_pdf(file)
    else:
        text = extract_text_from_image(file)
    
    # Parse with Gemini AI
    response = genai.GenerativeModel('gemini-pro').generate_content(
        f"Extract emission data from this text: {text}"
    )
    
    return jsonify({
        'extracted_text': text,
        'parsed_data': parse_extracted_text(response.text),
        'confidence': calculate_confidence_enhanced(text, 'document', 1)
    })
```

---

**Total Lines**: 2,000+  
**Functions Documented**: 40+  
**Routes Documented**: 70+  
**API Endpoints**: 35+  

This comprehensive guide serves as the technical reference for all platform functions, buttons, and operations.

