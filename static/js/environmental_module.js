// ============================================================
// Environmental Module JavaScript - Fixed & Rewired
// All data input redirects to Dashboard "Add Emission Data" modal
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    loadAllEnvironmentalData();
    loadEnvironmentalSummaryCards();
    loadIntensityMetrics();
});

// ============================================================
// TAB SWITCHING
// ============================================================

function switchEnvTab(tabName) {
    // Hide all tab content
    document.querySelectorAll('.env-tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });

    // Remove active from all tab buttons
    document.querySelectorAll('.env-tab-btn').forEach(btn => {
        btn.classList.remove('active', 'border-b-2', 'border-emerald-600', 'text-emerald-700', 'font-semibold');
        btn.classList.add('text-gray-500');
    });

    // Show selected tab
    const activeTab = document.getElementById(`tab-${tabName}`);
    if (activeTab) activeTab.classList.remove('hidden');

    // Activate button
    const activeBtn = document.getElementById(`btn-${tabName}`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'border-b-2', 'border-emerald-600', 'text-emerald-700', 'font-semibold');
        activeBtn.classList.remove('text-gray-500');
    }

    // Load data for the tab
    if (tabName === 'emissions') {
        loadEmissionsSummary();
    } else {
        loadModuleData(tabName);
    }
}

// ============================================================
// REDIRECT TO DASHBOARD MODAL
// The centralised data input is on the dashboard
// ============================================================

function goToAddData(tabType) {
    // Store which tab to open in sessionStorage
    sessionStorage.setItem('openESGTab', tabType || 'energy');
    window.location.href = '/dashboard#addData';
}

// ============================================================
// LOAD ALL DATA ON PAGE LOAD
// ============================================================

async function loadAllEnvironmentalData() {
    const tabs = ['energy', 'fuel', 'water', 'waste', 'travel', 'land_biodiversity'];
    for (const tab of tabs) {
        await loadModuleData(tab);
    }
    await loadEmissionsSummary();
}

// ============================================================
// LOAD DATA FOR A SPECIFIC MODULE TAB
// ============================================================

async function loadModuleData(moduleType) {
    // Map fuel/travel to their API module types
   const apiModuleType = (moduleType === 'fuel' || moduleType === 'travel') ? 'energy' : moduleType;
    const tableBodyId = `${moduleType}-table-body`;
    const tableBody = document.getElementById(tableBodyId);

    if (!tableBody) return;

    // Show loading state
    tableBody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-8 text-gray-400">
                <div class="flex items-center justify-center space-x-2">
                    <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-emerald-500"></div>
                    <span>Loading ${moduleType} data...</span>
                </div>
            </td>
        </tr>`;

    try {
        const response = await fetch(`/api/environmental/list?module_type=${apiModuleType}`);
        const result = await response.json();

        if (!result.success) throw new Error(result.error || 'Failed to load data');

        // Filter records based on tab
        let records = result.records || [];

        if (moduleType === 'fuel') {
            const fuelActivities = ['diesel', 'gasoline', 'natural_gas', 'lpg', 'coal', 'ron95', 'ron97', 'petrol'];
            records = records.filter(r => fuelActivities.includes(r.activity_type));
        } else if (moduleType === 'energy') {
            const energyActivities = ['electricity', 'renewable_energy', 'electricity_peninsular', 'electricity_sabah', 'electricity_sarawak', 'solar'];
            records = records.filter(r => energyActivities.includes(r.activity_type));
        } else if (moduleType === 'travel') {
            const travelActivities = ['flight_domestic', 'flight_international', 'car_petrol', 'car_diesel', 'car_electric', 'train', 'bus', 'motorcycle', 'taxi', 'ride_hailing', 'ferry'];
            records = records.filter(r => travelActivities.includes(r.activity_type));
        }
        renderModuleTable(moduleType, records);
        updateTabBadge(moduleType, records.length);

    } catch (error) {
        console.error(`Error loading ${moduleType}:`, error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-8 text-red-400">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    Error loading data. 
                    <button onclick="loadModuleData('${moduleType}')" class="ml-2 text-blue-500 underline">Retry</button>
                </td>
            </tr>`;
    }
}

// ============================================================
// RENDER TABLE ROWS
// ============================================================

function renderModuleTable(moduleType, records) {
    const tableBodyId = `${moduleType}-table-body`;
    const tableBody = document.getElementById(tableBodyId);
    if (!tableBody) return;

    if (!records || records.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-12">
                    <div class="flex flex-col items-center text-gray-400">
                        <i class="fas fa-database text-4xl mb-3 opacity-30"></i>
                        <p class="text-base font-medium text-gray-500">No ${moduleType} data yet</p>
                        <p class="text-sm text-gray-400 mb-4">Upload a bill or add data manually from the dashboard</p>
                        <button onclick="goToAddData('${moduleType}')" 
                            class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700 transition">
                            <i class="fas fa-plus mr-2"></i>Add ${formatModuleName(moduleType)} Data
                        </button>
                    </div>
                </td>
            </tr>`;
        return;
    }

    let html = '';
    records.forEach(record => {
        const co2e = calculateCO2e(record);
        const statusBadge = getStatusBadge(record.status);
        const evidenceBadge = record.evidence_count > 0
            ? `<button onclick="viewEvidence(${record.id})" class="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 text-blue-700 hover:bg-blue-200">
                    <i class="fas fa-paperclip mr-1"></i>${record.evidence_count} file(s)
               </button>`
            : `<span class="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-500">
                    <i class="fas fa-times mr-1"></i>No evidence
               </span>`;

        html += `
            <tr class="hover:bg-gray-50 transition-colors border-b border-gray-100">
                <td class="py-3 px-4">
                    <div class="font-medium text-gray-800">${formatActivityName(record.activity_type)}</div>
                    ${record.is_estimated ? '<span class="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">Estimated</span>' : ''}
                </td>
                <td class="py-3 px-4 text-gray-700">${record.quantity} <span class="text-gray-400 text-sm">${record.unit}</span></td>
                <td class="py-3 px-4 text-gray-700">${co2e > 0 ? co2e.toFixed(2) + ' kg' : '<span class="text-gray-400">—</span>'}</td>
                <td class="py-3 px-4 text-gray-700">${record.reporting_year}</td>
                <td class="py-3 px-4 text-gray-600 text-sm">${formatPeriod(record.reporting_period, record.period_month, record.period_quarter)}</td>
                <td class="py-3 px-4">${statusBadge}</td>
                <td class="py-3 px-4">${evidenceBadge}</td>
                <td class="py-3 px-4">
                    <div class="flex items-center space-x-2">
                        ${record.status === 'draft' ? `
                            <button onclick="submitRecord(${record.id})" 
                                class="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded" title="Submit for review">
                                <i class="fas fa-paper-plane text-sm"></i>
                            </button>` : ''}
                        <button onclick="viewEvidence(${record.id})" 
                            class="p-1.5 text-blue-600 hover:bg-blue-50 rounded" title="View evidence">
                            <i class="fas fa-eye text-sm"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    });

    tableBody.innerHTML = html;
}

// ============================================================
// EMISSIONS SUMMARY TAB
// Calculated from activity data — read only
// ============================================================

async function loadEmissionsSummary() {
    const container = document.getElementById('emissions-summary-container');
    if (!container) return;

    container.innerHTML = `<div class="flex items-center justify-center py-8 text-gray-400">
        <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-emerald-500 mr-2"></div>
        Calculating emissions...
    </div>`;

    try {
        // Fetch all records
        const response = await fetch('/api/environmental/list');
        const result = await response.json();

        if (!result.success) throw new Error(result.error);

        const records = result.records || [];

        // Emission factors (kg CO2e per unit)
        const factors = {
            // Scope 2 - Energy
            electricity: 0.85, electricity_peninsular: 0.85, electricity_sabah: 0.92,
            electricity_sarawak: 0.78, solar: 0.0, renewable_energy: 0.0, renewable_other: 0.02,
            // Scope 1 - Fuel
            diesel: 2.68, gasoline: 2.31, natural_gas: 2.75, lpg: 1.55,
            coal: 2.42, ron95: 2.31, ron97: 2.31, petrol: 2.31, fuel: 2.31,
            // Scope 3 - Water
            water_withdrawal: 0.344, water_consumption: 0.344, water_discharge: 0.10,
            municipal: 0.344, tap_water: 0.344, recycled: 0.05, groundwater: 0.10,
            // Scope 3 - Waste
            waste_general: 0.58, general_landfill: 0.58,
            hazardous_waste: 1.10, hazardous: 1.10,
            recycled_waste: 0.02, organic_waste: 0.10, organic: 0.10,
            // Scope 3 - Travel
            flight_domestic: 0.255, flight_international: 0.195,
            car_petrol: 0.192, car_diesel: 0.171, car_electric: 0.053,
            train: 0.041, bus: 0.089, motorcycle: 0.114,
            taxi: 0.192, ride_hailing: 0.192, ferry: 0.115,
        };

        let scope1 = 0, scope2 = 0, scope3 = 0;
        const scope1Activities = ['diesel', 'gasoline', 'natural_gas', 'lpg', 'coal', 'ron95', 'ron97', 'petrol', 'fuel'];
        const scope2Activities = ['electricity', 'electricity_peninsular', 'electricity_sabah', 'electricity_sarawak', 'solar', 'renewable_energy', 'renewable_other'];
        const travelActivities = ['flight_domestic', 'flight_international', 'car_petrol', 'car_diesel', 'car_electric', 'train', 'bus', 'motorcycle', 'taxi', 'ride_hailing', 'ferry'];

        records.forEach(r => {
            const factor = factors[r.activity_type] || 0;
            const co2e = r.quantity * factor;
            if (scope1Activities.includes(r.activity_type)) scope1 += co2e;
            else if (scope2Activities.includes(r.activity_type)) scope2 += co2e;
            else scope3 += co2e; // water, waste, travel all go to scope3
        });

        const total = scope1 + scope2 + scope3;

        container.innerHTML = `
            <!-- Scope Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div class="bg-orange-50 border border-orange-200 rounded-xl p-5">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium text-orange-700">Scope 1</span>
                        <span class="text-xs bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full">Direct</span>
                    </div>
                    <div class="text-2xl font-bold text-orange-800">${(scope1/1000).toFixed(3)}</div>
                    <div class="text-sm text-orange-600">tCO₂e — Fuel combustion</div>
                    <div class="mt-2 text-xs text-orange-500">${total > 0 ? ((scope1/total)*100).toFixed(1) : 0}% of total</div>
                </div>
                <div class="bg-blue-50 border border-blue-200 rounded-xl p-5">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium text-blue-700">Scope 2</span>
                        <span class="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">Energy</span>
                    </div>
                    <div class="text-2xl font-bold text-blue-800">${(scope2/1000).toFixed(3)}</div>
                    <div class="text-sm text-blue-600">tCO₂e — Purchased electricity</div>
                    <div class="mt-2 text-xs text-blue-500">${total > 0 ? ((scope2/total)*100).toFixed(1) : 0}% of total</div>
                </div>
                <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-5">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-sm font-medium text-emerald-700">Scope 3</span>
                        <span class="text-xs bg-emerald-100 text-emerald-600 px-2 py-0.5 rounded-full">Indirect</span>
                    </div>
                    <div class="text-2xl font-bold text-emerald-800">${(scope3/1000).toFixed(3)}</div>
                    <div class="text-sm text-emerald-600">tCO₂e — Water, waste, travel</div>
                    <div class="mt-2 text-xs text-emerald-500">${total > 0 ? ((scope3/total)*100).toFixed(1) : 0}% of total</div>
                </div>
            </div>

            <!-- Total Banner -->
            <div class="bg-gray-800 rounded-xl p-5 flex items-center justify-between">
                <div>
                    <div class="text-gray-400 text-sm">Total GHG Emissions</div>
                    <div class="text-3xl font-bold text-white">${(total/1000).toFixed(3)} <span class="text-lg text-gray-400">tCO₂e</span></div>
                </div>
                <div class="text-right">
                    <div class="text-gray-400 text-sm">Based on ${records.length} activity records</div>
                    <a href="/dashboard" class="mt-2 inline-flex items-center text-emerald-400 hover:text-emerald-300 text-sm">
                        View full dashboard <i class="fas fa-arrow-right ml-1"></i>
                    </a>
                </div>
            </div>

            <!-- Info note -->
            <div class="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start space-x-2">
                <i class="fas fa-info-circle text-blue-500 mt-0.5"></i>
                <p class="text-sm text-blue-700">
                    Emissions are automatically calculated from your activity data in the Energy, Fuel, Water, and Waste tabs.
                    To add new data, use the <a href="/dashboard" class="font-semibold underline">Dashboard → Add Emission Data</a> button.
                </p>
            </div>`;

    } catch (error) {
        container.innerHTML = `<div class="text-center py-8 text-red-400">
            <i class="fas fa-exclamation-triangle mr-2"></i>Error loading emissions data.
            <button onclick="loadEmissionsSummary()" class="ml-2 text-blue-500 underline">Retry</button>
        </div>`;
    }
}

// ============================================================
// SUMMARY CARDS AT TOP OF PAGE
// ============================================================

async function loadEnvironmentalSummaryCards() {
    try {
        const response = await fetch('/api/environmental/list');
        const result = await response.json();
        if (!result.success) return;

        const records = result.records || [];

        // Count by module
        const counts = { energy: 0, fuel: 0, water: 0, waste: 0, travel: 0, land_biodiversity: 0 };
        const fuelActivities = ['diesel', 'gasoline', 'natural_gas', 'lpg', 'coal', 'ron95', 'ron97', 'petrol'];
        const travelActivities = ['flight_domestic', 'flight_international', 'car_petrol', 'car_diesel', 'car_electric', 'train', 'bus', 'motorcycle', 'taxi', 'ride_hailing', 'ferry'];

        records.forEach(r => {
            if (r.module_type === 'energy') {
                if (fuelActivities.includes(r.activity_type)) counts.fuel++;
                else counts.energy++;
            } else if (r.module_type === 'travel' || travelActivities.includes(r.activity_type)) {
                counts.travel++;
            } else if (r.module_type in counts) {
                counts[r.module_type]++;
            }
        });

        // Update completion badge
        const completionEl = document.getElementById('env-completion-badge');
        if (completionEl) {
            const hasEnergy = counts.energy > 0;
            const hasFuel = counts.fuel > 0;
            const hasWater = counts.water > 0;
            const hasWaste = counts.waste > 0;
            const filled = [hasEnergy, hasFuel, hasWater, hasWaste].filter(Boolean).length;
            completionEl.textContent = `${filled * 25}%`;
        }

        // Update record counts in tabs
        Object.entries(counts).forEach(([module, count]) => {
            const badge = document.getElementById(`${module}-count-badge`);
            if (badge) badge.textContent = count;
        });

    } catch (e) {
        console.error('Error loading summary cards:', e);
    }
}

// ============================================================
// INTENSITY METRICS
// ============================================================

async function loadIntensityMetrics() {
    const container = document.getElementById('intensity-metrics');
    if (!container) return;

    try {
        const response = await fetch('/api/environmental/intensity');
        const result = await response.json();

        if (!result.success || !result.data) return;

        const { intensities, company_factors } = result.data;

        let html = '';

        if (intensities.energy) {
            html += `
                <div class="bg-white rounded-lg border p-4">
                    <div class="flex items-center mb-3">
                        <i class="fas fa-bolt text-yellow-500 mr-2"></i>
                        <span class="font-medium text-gray-700">Energy Intensity</span>
                    </div>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div class="bg-yellow-50 rounded p-2">
                            <div class="text-xs text-gray-500">Total</div>
                            <div class="font-semibold">${intensities.energy.total_energy_kwh} kWh</div>
                        </div>
                        ${intensities.energy.per_employee_kwh ? `
                        <div class="bg-yellow-50 rounded p-2">
                            <div class="text-xs text-gray-500">Per Employee</div>
                            <div class="font-semibold">${intensities.energy.per_employee_kwh} kWh/emp</div>
                        </div>` : ''}
                    </div>
                </div>`;
        }

        if (intensities.water) {
            html += `
                <div class="bg-white rounded-lg border p-4">
                    <div class="flex items-center mb-3">
                        <i class="fas fa-tint text-blue-500 mr-2"></i>
                        <span class="font-medium text-gray-700">Water Intensity</span>
                    </div>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div class="bg-blue-50 rounded p-2">
                            <div class="text-xs text-gray-500">Total</div>
                            <div class="font-semibold">${intensities.water.total_water_m3} m³</div>
                        </div>
                        ${intensities.water.per_employee_m3 ? `
                        <div class="bg-blue-50 rounded p-2">
                            <div class="text-xs text-gray-500">Per Employee</div>
                            <div class="font-semibold">${intensities.water.per_employee_m3} m³/emp</div>
                        </div>` : ''}
                    </div>
                </div>`;
        }

        if (intensities.waste) {
            html += `
                <div class="bg-white rounded-lg border p-4">
                    <div class="flex items-center mb-3">
                        <i class="fas fa-trash text-gray-500 mr-2"></i>
                        <span class="font-medium text-gray-700">Waste Intensity</span>
                    </div>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div class="bg-gray-50 rounded p-2">
                            <div class="text-xs text-gray-500">Total</div>
                            <div class="font-semibold">${intensities.waste.total_waste_tons} tons</div>
                        </div>
                        ${intensities.waste.recycling_rate !== undefined ? `
                        <div class="bg-green-50 rounded p-2">
                            <div class="text-xs text-gray-500">Recycling Rate</div>
                            <div class="font-semibold">${intensities.waste.recycling_rate}%</div>
                        </div>` : ''}
                    </div>
                </div>`;
        }

        if (html) container.innerHTML = html;

    } catch (e) {
        console.error('Error loading intensity metrics:', e);
    }
}

// ============================================================
// EVIDENCE VIEWER
// ============================================================

async function viewEvidence(recordId) {
    const modal = document.getElementById('evidenceModal');
    const evidenceList = document.getElementById('evidenceList');

    if (!modal || !evidenceList) return;

    evidenceList.innerHTML = '<div class="text-center py-4 text-gray-400">Loading...</div>';
    modal.classList.remove('hidden');

    try {
        const response = await fetch(`/api/environmental/evidence/${recordId}`);
        const result = await response.json();

        if (!result.success) throw new Error(result.error);

        if (result.count === 0) {
            evidenceList.innerHTML = `
                <div class="text-center py-8 text-gray-400">
                    <i class="fas fa-folder-open text-3xl mb-2 opacity-40"></i>
                    <p>No evidence files attached to this record.</p>
                </div>`;
            return;
        }

        let html = '';
        result.evidence.forEach(ev => {
            const icon = getFileIcon(ev.file_type);
            const date = ev.uploaded_at ? new Date(ev.uploaded_at).toLocaleDateString('en-MY') : '—';
            const size = ev.file_size ? formatFileSize(ev.file_size) : '—';

            html += `
                <div class="flex items-start justify-between p-3 bg-gray-50 rounded-lg mb-2">
                    <div class="flex items-start space-x-3">
                        <i class="fas ${icon} text-gray-400 text-lg mt-1"></i>
                        <div>
                            <div class="font-medium text-gray-800 text-sm">${ev.filename}</div>
                            ${ev.description ? `<div class="text-xs text-gray-500">${ev.description}</div>` : ''}
                            <div class="text-xs text-gray-400 mt-1">${size} · Uploaded ${date}</div>
                            ${ev.verified ? '<span class="text-xs text-green-600"><i class="fas fa-check-circle mr-1"></i>Verified</span>' : ''}
                        </div>
                    </div>
                    <a href="${ev.file_path}" target="_blank" 
                        class="text-sm text-blue-600 hover:text-blue-800 ml-4 shrink-0">
                        <i class="fas fa-download"></i>
                    </a>
                </div>`;
        });

        evidenceList.innerHTML = html;

    } catch (error) {
        evidenceList.innerHTML = `<div class="text-center py-4 text-red-400">Error loading evidence: ${error.message}</div>`;
    }
}

function closeEvidenceModal() {
    const modal = document.getElementById('evidenceModal');
    if (modal) modal.classList.add('hidden');
}

// ============================================================
// SUBMIT RECORD FOR REVIEW
// ============================================================

async function submitRecord(recordId) {
    if (!confirm('Submit this record for review? It cannot be edited after submission.')) return;

    try {
        const response = await fetch(`/api/environmental/submit/${recordId}`, { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            showToast('Record submitted for review', 'success');
            loadAllEnvironmentalData();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
    }
}

// ============================================================
// HELPER: CALCULATE CO2E FROM RECORD
// ============================================================

function calculateCO2e(record) {
    const factors = {
        // Scope 2 - Energy
        electricity: 0.85, electricity_peninsular: 0.85, electricity_sabah: 0.92,
        electricity_sarawak: 0.78, solar: 0.0, renewable_energy: 0.0, renewable_other: 0.02,
        // Scope 1 - Fuel
        diesel: 2.68, gasoline: 2.31, natural_gas: 2.75, lpg: 1.55,
        coal: 2.42, ron95: 2.31, ron97: 2.31, petrol: 2.31, fuel: 2.31,
        // Scope 3 - Water
        water_withdrawal: 0.344, water_consumption: 0.344, water_discharge: 0.10,
        municipal: 0.344, tap_water: 0.344, recycled: 0.05, groundwater: 0.10,
        // Scope 3 - Waste
        waste_general: 0.58, general_landfill: 0.58,
        hazardous_waste: 1.10, hazardous: 1.10,
        recycled_waste: 0.02, organic_waste: 0.10, organic: 0.10,
        // Scope 3 - Travel (kg CO2e per km)
        flight_domestic: 0.255, flight_international: 0.195,
        car_petrol: 0.192, car_diesel: 0.171, car_electric: 0.053,
        train: 0.041, bus: 0.089, motorcycle: 0.114,
        taxi: 0.192, ride_hailing: 0.192, ferry: 0.115,
    };
    return (factors[record.activity_type] || 0) * (record.quantity || 0);
}

// ============================================================
// HELPER FUNCTIONS
// ============================================================

function updateTabBadge(moduleType, count) {
    const badge = document.getElementById(`${moduleType}-count-badge`);
    if (badge) {
        badge.textContent = count;
        badge.classList.toggle('hidden', count === 0);
    }
}

function formatModuleName(moduleType) {
    const names = {
        energy: 'Energy', fuel: 'Fuel', water: 'Water',
        waste: 'Waste', land_biodiversity: 'Land & Biodiversity', emissions: 'Emissions'
    };
    return names[moduleType] || moduleType;
}

function formatActivityName(activity) {
    if (!activity) return '—';
    return activity.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function formatPeriod(period, month, quarter) {
    if (!period) return '—';
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    if (period === 'monthly' && month) return monthNames[month - 1] || `Month ${month}`;
    if (period === 'quarterly' && quarter) return `Q${quarter}`;
    return period.charAt(0).toUpperCase() + period.slice(1);
}

function getStatusBadge(status) {
    const badges = {
        draft: '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">Draft</span>',
        submitted: '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-amber-100 text-amber-700">Submitted</span>',
        reviewed: '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-700">Reviewed</span>',
        approved: '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-emerald-100 text-emerald-700"><i class="fas fa-check mr-1"></i>Approved</span>'
    };
    return badges[status] || `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-500">${status}</span>`;
}

function getFileIcon(fileType) {
    const icons = {
        pdf: 'fa-file-pdf text-red-400', png: 'fa-file-image text-blue-400',
        jpg: 'fa-file-image text-blue-400', jpeg: 'fa-file-image text-blue-400',
        csv: 'fa-file-csv text-green-400', xlsx: 'fa-file-excel text-green-500',
        xls: 'fa-file-excel text-green-500', doc: 'fa-file-word text-blue-500',
        docx: 'fa-file-word text-blue-500', txt: 'fa-file-alt text-gray-400'
    };
    return icons[(fileType || '').toLowerCase()] || 'fa-file text-gray-400';
}

function formatFileSize(bytes) {
    if (!bytes) return '—';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    const colors = { success: 'bg-emerald-600', error: 'bg-red-500', info: 'bg-blue-500' };
    toast.className = `fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg text-white text-sm shadow-lg ${colors[type] || colors.info} transition-all`;
    toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle mr-2"></i>${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ============================================================
// ALSO: If dashboard has openESGTab in sessionStorage, auto-open
// the right tab in the ESG modal on dashboard page
// ============================================================
if (window.location.pathname === '/dashboard') {
    const tabToOpen = sessionStorage.getItem('openESGTab');
    if (tabToOpen) {
        sessionStorage.removeItem('openESGTab');
        // Wait for dashboard to load then trigger modal
        setTimeout(() => {
            if (typeof openAddDataModal === 'function') openAddDataModal();
            if (typeof switchESGTab === 'function') switchESGTab(tabToOpen);
        }, 500);
    }
}

// Export for HTML onclick attributes
window.switchEnvTab = switchEnvTab;
window.goToAddData = goToAddData;
window.loadModuleData = loadModuleData;
window.viewEvidence = viewEvidence;
window.closeEvidenceModal = closeEvidenceModal;
window.submitRecord = submitRecord;