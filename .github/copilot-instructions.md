# Carbon Tracker AI Agent Instructions

This document provides essential context for AI agents working in the Carbon Tracker codebase.

## Project Overview

Carbon Tracker is a Flask-based web application for tracking and analyzing carbon emissions across different scopes (1, 2, and 3). The application provides authentication, emission calculations, and dashboard visualizations.

## Architecture

### Core Components

- **Authentication System**: Uses Flask-Login with SQLite backend (`User` model)
- **Emissions Tracking**: Centered around `Emission` model with scope-based categorization
- **Dashboard Visualization**: Real-time calculations and filtering by year/month

### Key Files

- `app.py`: Main application file containing all routes and models
- `templates/`: HTML templates using Bootstrap for styling
- `instance/carbon_tracker.db`: SQLite database (auto-generated)

## Data Model

### User Model
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(200))
    emissions = db.relationship('Emission', backref='user')
```

### Emission Model
```python
class Emission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scope = db.Column(db.String(50))
    source = db.Column(db.String(100))
    activity_data = db.Column(db.Float)
    emission_factor = db.Column(db.Float)
    total_emission = db.Column(db.Float)
```

## Key Patterns

1. **Emission Calculations**:
   - Uses predefined `EMISSION_FACTORS` dictionary for different scopes
   - Total emission = activity_data * emission_factor

2. **Authentication Flow**:
   - Login required for all routes except landing page
   - Password hashing using Werkzeug security

3. **Dashboard Data Processing**:
   - Supports year/month filtering
   - Aggregates emissions by scope
   - Generates monthly trend data

## Development Workflow

1. **Database Setup**:
   - Database automatically created on first run
   - Tables created using `db.create_all()`

2. **Running the Application**:
   ```bash
   flask run
   # or
   python app.py
   ```

3. **Environment Variables**:
   - `SECRET_KEY`: For Flask session management (defaults to 'dev-secret-key')

## Common Operations

1. **Adding New Emission Sources**:
   - Update `EMISSION_FACTORS` dictionary in `app.py`
   - Update corresponding units in `calculate.html` template

2. **Modifying Dashboard Metrics**:
   - Edit aggregation logic in `dashboard_home` route
   - Update corresponding visualizations in `dashboard_home.html`

## Future Integration Points

1. **AI Consultation**:
   - `generate_ai_reply()` function is a placeholder for future GPT integration
   - Currently uses simple keyword matching

## Testing

The project currently lacks formal tests. When adding tests:
- Focus on emission calculation accuracy
- Verify authentication flows
- Test dashboard data aggregation

## Error Handling

- Uses Flask's flash messages for user feedback
- Input validation in calculation routes
- Database error handling should be added for production

---

**Note**: This is a development version. For production deployment, ensure:
- Change default secret key
- Add proper error handling
- Implement proper logging
- Add test coverage