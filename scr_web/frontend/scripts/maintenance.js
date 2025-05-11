document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // Check if user is admin
    fetch('/api/auth/profile', {
        headers: {
            'Authorization': 'Bearer ' + token
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to fetch user profile');
        }
        return response.json();
    })
    .then(data => {
        // Show admin link if user is admin
        if (data.role === 'admin') {
            document.getElementById('admin-link').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error fetching profile:', error);
    });

    // Fetch maintenance data from API
    fetchMaintenanceData();

    // Handle logout
    document.querySelector('.logout a').addEventListener('click', function(e) {
        e.preventDefault();
        localStorage.removeItem('token');
        window.location.href = '/login';
    });
});

async function fetchMaintenanceData() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/maintenance/status', {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch maintenance data');
        }

        const data = await response.json();
        updateMaintenanceUI(data);
    } catch (error) {
        console.error('Error fetching maintenance data:', error);
        // Show error message or use mock data for demo
        updateMaintenanceUI(getMockData());
    }
}

function updateMaintenanceUI(data) {
    // Update Oil Life
    const oilLifeElement = document.querySelector('.oil-icon').closest('.status-card').querySelector('.progress-fill');
    const oilLifeValue = document.querySelector('.oil-icon').closest('.status-card').querySelector('.status-value');
    oilLifeElement.style.width = `${data.oilLife}%`;
    oilLifeValue.textContent = `${data.oilLife}%`;

    // Update Battery Health
    const batteryHealthElement = document.querySelector('.battery-icon').closest('.status-card').querySelector('.progress-fill');
    const batteryHealthValue = document.querySelector('.battery-icon').closest('.status-card').querySelector('.status-value');
    batteryHealthElement.style.width = `${data.batteryHealth}%`;
    batteryHealthValue.textContent = `${data.batteryHealth}%`;

    // Update Current Mileage
    const mileageValue = document.querySelector('.mileage-icon').closest('.status-card').querySelector('.status-value');
    const mileageDetail = document.querySelector('.mileage-icon').closest('.status-card').querySelector('.status-detail');
    mileageValue.textContent = data.currentMileage.toLocaleString();
    mileageDetail.textContent = `Next service in ${data.milesUntilService.toLocaleString()} miles`;

    // Update Engine Temperature
    const tempValue = document.querySelector('.temp-icon').closest('.status-card').querySelector('.status-value');
    const tempDetail = document.querySelector('.temp-icon').closest('.status-card').querySelector('.status-detail');
    tempValue.textContent = data.engineTemperature;
    tempDetail.textContent = data.temperatureStatus;

    // Update Tire Pressure
    const tirePressures = document.querySelectorAll('.tire-pressure');
    tirePressures[0].textContent = data.tirePressure.frontLeft;
    tirePressures[1].textContent = data.tirePressure.frontRight;
    tirePressures[2].textContent = data.tirePressure.rearLeft;
    tirePressures[3].textContent = data.tirePressure.rearRight;

    // Update Alerts
    const alertsList = document.querySelector('.alerts-list');
    alertsList.innerHTML = '';

    data.alerts.forEach(alert => {
        const alertItem = document.createElement('div');
        alertItem.className = `alert-item ${alert.type}`;
        alertItem.innerHTML = `
            <i class="fas fa-${alert.type === 'warning' ? 'exclamation' : 'info'}-circle"></i>
            <div class="alert-content">
                <p>${alert.message}</p>
            </div>
        `;
        alertsList.appendChild(alertItem);
    });

    // Update Maintenance History
    const historyList = document.querySelector('.maintenance-history');
    historyList.innerHTML = '';

    data.maintenanceHistory.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <div class="history-icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <div class="history-details">
                <h3>${item.service}</h3>
                <div class="history-meta">
                    <span class="history-date"><i class="far fa-calendar"></i> ${item.date}</span>
                    <span class="history-mileage"><i class="fas fa-road"></i> ${item.mileage.toLocaleString()} miles</span>
                </div>
            </div>
        `;
        historyList.appendChild(historyItem);
    });
}

// Mock data for testing/demo purposes
function getMockData() {
    return {
        oilLife: 72,
        batteryHealth: 95,
        currentMileage: 45230,
        milesUntilService: 2000,
        engineTemperature: 'Normal',
        temperatureStatus: 'Operating within normal range',
        tirePressure: {
            frontLeft: 32,
            frontRight: 32,
            rearLeft: 30,
            rearRight: 31
        },
        alerts: [
            {
                type: 'warning',
                message: 'Tire rotation recommended'
            },
            {
                type: 'info',
                message: 'Oil change due in 2000 miles'
            }
        ],
        maintenanceHistory: [
            {
                service: 'Oil Change',
                date: '2024-03-15',
                mileage: 43000
            },
            {
                service: 'Brake Inspection',
                date: '2024-02-28',
                mileage: 42500
            },
            {
                service: 'Tire Rotation',
                date: '2024-02-01',
                mileage: 41800
            }
        ]
    };
}
