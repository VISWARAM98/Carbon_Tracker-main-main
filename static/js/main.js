// Smooth scrolling for navigation links
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    const links = document.querySelectorAll('a[href^="#"]');
    for (const link of links) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    }

    // Add particles on mousemove
    document.addEventListener('mousemove', function(e) {
        createParticle(e.clientX, e.clientY);
    });

    function createParticle(x, y) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        document.body.appendChild(particle);

        const size = Math.random() * 5 + 2;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${x}px`;
        particle.style.top = `${y}px`;

        const moveX = (Math.random() - 0.5) * 100;
        const moveY = (Math.random() - 0.5) * 100;

        particle.style.transform = `translate(${moveX}px, ${moveY}px)`;
        particle.style.opacity = '0';

        setTimeout(() => {
            particle.remove();
        }, 1000);
    }

    // Add intersection observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
            }
        });
    }, observerOptions);

    // Observe all sections for animation
    document.querySelectorAll('section').forEach(section => {
        observer.observe(section);
    });

    // Initialize the emission form if it exists
    initializeEmissionForm();
});

// ============================================================================
// REGION MANAGEMENT FUNCTIONS
// ============================================================================

// Category data based on scope
const categoryData = {
    scope1: [
        { value: 'diesel', text: 'Diesel Fuel' },
        { value: 'gasoline', text: 'Gasoline' },
        { value: 'natural_gas', text: 'Natural Gas' },
        { value: 'lpg', text: 'LPG' },
        { value: 'coal', text: 'Coal' }
    ],
    scope2: [
        { value: 'electricity', text: 'Electricity' }
    ],
    scope3: [
        { value: 'business_travel_air', text: 'Business Travel - Air' },
        { value: 'business_travel_car', text: 'Business Travel - Car' },
        { value: 'employee_commute', text: 'Employee Commute' },
        { value: 'purchased_goods', text: 'Purchased Goods' },
        { value: 'waste_disposal', text: 'Waste Disposal' }
    ]
};

// Emission factors with regional electricity factors
const emissionFactors = {
    scope1: {
        diesel: 2.68,        // kg CO2e per liter
        gasoline: 2.31,      // kg CO2e per liter
        natural_gas: 2.75,   // kg CO2e per m3
        lpg: 1.55,          // kg CO2e per liter
        coal: 2.42          // kg CO2e per kg
    },
    scope2: {
        electricity: {
            peninsular_malaysia: 0.85,  // kg CO2e per kWh
            sabah: 0.92,                // kg CO2e per kWh  
            sarawak: 0.78               // kg CO2e per kWh
        }
    },
    scope3: {
        business_travel_air: 0.25,      // kg CO2e per km
        business_travel_car: 0.21,      // kg CO2e per km
        employee_commute: 0.12,         // kg CO2e per km
        purchased_goods: 0.15,          // kg CO2e per RM
        waste_disposal: 0.85            // kg CO2e per kg
    }
};

// Initialize emission form
function initializeEmissionForm() {
    const emissionFormEl = document.getElementById('emissionForm');
    if (emissionFormEl) {
        // Attach event listeners to form elements
        const scopeRadios = document.querySelectorAll('input[name="scope"]');
        const categorySelect = document.getElementById('category');
        const amountInput = document.getElementById('amount');
        const regionSelect = document.getElementById('region');
        
        if (scopeRadios.length > 0) {
            scopeRadios.forEach(radio => {
                radio.addEventListener('change', function() {
                    handleScopeChange(this.value);
                });
            });
        }
        
        if (categorySelect) {
            categorySelect.addEventListener('change', handleCategoryChange);
        }
        
        if (amountInput) {
            amountInput.addEventListener('input', calculateCO2e);
        }
        
        if (regionSelect) {
            regionSelect.addEventListener('change', calculateCO2e);
        }
        
        // Attach submit handler
        emissionFormEl.addEventListener('submit', handleEmissionFormSubmit);
    }
}

// Scope Selection Handler with region toggle
function handleScopeChange(scope) {
    const categorySelect = document.getElementById('category');
    const regionSelection = document.getElementById('regionSelection');

    // Clear existing options
    if (categorySelect) categorySelect.innerHTML = '<option value="">Select a category</option>';

    // Add new options based on selected scope
    if (categorySelect && categoryData[scope]) {
        categoryData[scope].forEach(category => {
            const option = document.createElement('option');
            option.value = category.value;
            option.textContent = category.text;
            categorySelect.appendChild(option);
        });
    }

    // Show/hide region selection for Scope 2 Electricity
    if (regionSelection) {
        if (scope === 'scope2') {
            regionSelection.classList.remove('hidden');
        } else {
            regionSelection.classList.add('hidden');
        }
    }

    // Reset CO2e calculation
    const co2eRes = document.getElementById('co2eResult');
    if (co2eRes) co2eRes.classList.add('hidden');
}

// Handle category change to show region only for electricity
function handleCategoryChange() {
    const scope = document.querySelector('input[name="scope"]:checked');
    const categoryEl = document.getElementById('category');
    const regionSelection = document.getElementById('regionSelection');
    const category = categoryEl ? categoryEl.value : null;

    if (scope && scope.value === 'scope2' && category === 'electricity') {
        if (regionSelection) regionSelection.classList.remove('hidden');
    } else {
        if (regionSelection) regionSelection.classList.add('hidden');
    }

    calculateCO2e();
}

// Real-time CO2e Calculation with regional support
function calculateCO2e() {
    const scope = document.querySelector('input[name="scope"]:checked');
    const categoryEl = document.getElementById('category');
    const amountEl = document.getElementById('amount');
    const unitEl = document.getElementById('unit');
    const regionEl = document.getElementById('region');
    const category = categoryEl ? categoryEl.value : '';
    const amount = amountEl ? parseFloat(amountEl.value) : 0;
    const unit = unitEl ? unitEl.value : '';
    const region = regionEl ? regionEl.value : 'peninsular_malaysia';

    const calculatedEl = document.getElementById('calculatedCO2e');
    const co2eResultEl = document.getElementById('co2eResult');

    if (scope && category && amount && unit) {
        let factor = 0;

        if (scope.value === 'scope2' && category === 'electricity') {
            // Use regional electricity factor
            factor = emissionFactors.scope2.electricity[region] || 0.85;
        } else {
            // Use standard emission factor
            factor = emissionFactors[scope.value] ? (emissionFactors[scope.value][category] || 0) : 0;
        }

        const co2e = amount * factor;
        if (calculatedEl) calculatedEl.textContent = `${co2e.toFixed(2)} kg CO₂e`;
        if (co2eResultEl) co2eResultEl.classList.remove('hidden');
    } else {
        if (co2eResultEl) co2eResultEl.classList.add('hidden');
    }
}

// Display REAL Analysis Results with region
function displayRealAnalysisResults(analysisData) {
    // Hide processing
    const proc = document.getElementById('aiProcessing');
    if (proc) proc.classList.add('hidden');

    // Display REAL results from OCR
    const aiScope = document.getElementById('aiScope');
    const aiCategory = document.getElementById('aiCategory');
    const aiAmount = document.getElementById('aiAmount');
    const aiUnit = document.getElementById('aiUnit');
    const aiCalculated = document.getElementById('aiCalculatedCO2e');

    if (aiScope) aiScope.textContent = analysisData.scope.replace('scope', 'Scope ');
    if (aiCategory) aiCategory.textContent = analysisData.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    if (aiAmount) aiAmount.textContent = analysisData.amount.toFixed(1);
    if (aiUnit) aiUnit.textContent = analysisData.unit;
    if (aiCalculated) aiCalculated.textContent = `${analysisData.co2e.toFixed(2)} kg CO₂e`;

    // Display region if available
    const regionContainer = document.getElementById('aiRegionContainer');
    const regionElement = document.getElementById('aiRegion');

    if (analysisData.region && regionElement) {
        const regionNames = {
            'peninsular_malaysia': 'Peninsular Malaysia',
            'sabah': 'Sabah', 
            'sarawak': 'Sarawak'
        };
        regionElement.textContent = regionNames[analysisData.region] || analysisData.region;
        if (regionContainer) regionContainer.classList.remove('hidden');
    } else if (regionContainer) {
        regionContainer.classList.add('hidden');
    }

    // Store analysis result for confirmation
    window.currentAIAnalysis = analysisData;

    // Show results
    const res = document.getElementById('aiAnalysisResult');
    if (res) res.classList.remove('hidden');
}

// Confirm AI Analysis with region
function confirmAIAnalysis() {
    const analysis = window.currentAIAnalysis;
    if (!analysis) return;

    // Prepare data with region
    const requestData = {
        scope: analysis.scope,
        category: analysis.category,
        amount: analysis.amount,
        unit: analysis.unit,
        co2e: analysis.co2e
    };

    // Add region if detected
    if (analysis.region) {
        requestData.region = analysis.region;
    }

    // Send to backend
    fetch('/api/add-emission', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeAddDataModal();
            alert('Emission data added successfully! ' + data.message);
            location.reload();
        } else {
            alert('Error adding emission data: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding emission data. Please try again.');
    });
}

// Form Submission for Manual Input with region (guarded)
function handleEmissionFormSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const scope = formData.get('scope');
    const category = formData.get('category');
    const amount = parseFloat(formData.get('amount'));
    const unit = formData.get('unit');
    const region = scope === 'scope2' && category === 'electricity' ? formData.get('region') : null;

    // Calculate final CO2e
    calculateCO2e();
    const co2eTextEl = document.getElementById('calculatedCO2e');
    const co2e = co2eTextEl ? parseFloat(co2eTextEl.textContent.replace(' kg CO₂e', '')) : null;

    // Send to backend with region
    const requestData = {
        scope: scope,
        category: category,
        amount: amount,
        unit: unit,
        co2e: co2e
    };

    // Add region if applicable
    if (region) {
        requestData.region = region;
    }

    fetch('/api/add-emission', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeAddDataModal();
            alert('Emission data added successfully! ' + data.message);
            location.reload();
        } else {
            alert('Error adding emission data: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding emission data. Please try again.');
    });
}

// Modal open/close helpers
function openAddDataModal() {
    const m = document.getElementById('addDataModal');
    if (m) m.classList.remove('hidden');
}

function closeAddDataModal() {
    const m = document.getElementById('addDataModal');
    if (m) m.classList.add('hidden');
    // reset form if present
    const form = document.getElementById('emissionForm');
    if (form) {
        form.reset();
        // Reset category dropdown
        const categorySelect = document.getElementById('category');
        if (categorySelect) categorySelect.innerHTML = '<option value="">Select a category</option>';
    }
    const result = document.getElementById('co2eResult');
    if (result) result.classList.add('hidden');
}

// Make functions globally available
window.handleScopeChange = handleScopeChange;
window.handleCategoryChange = handleCategoryChange;
window.calculateCO2e = calculateCO2e;
window.displayRealAnalysisResults = displayRealAnalysisResults;
window.confirmAIAnalysis = confirmAIAnalysis;
window.openAddDataModal = openAddDataModal;
window.closeAddDataModal = closeAddDataModal;

// Add CSS for particles
const style = document.createElement('style');
style.textContent = `
    .particle {
        position: fixed;
        background: linear-gradient(45deg, #10B981, #0F3B2E);
        border-radius: 50%;
        pointer-events: none;
        z-index: 9999;
        transition: transform 1s ease-out, opacity 1s ease-out;
        transform-origin: center;
    }

    .animate-fade-in {
        animation: fadeInUp 0.6s ease-out forwards;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .hidden {
        display: none !important;
    }
`;
document.head.appendChild(style);