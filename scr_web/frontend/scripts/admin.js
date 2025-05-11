document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in and is admin
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // Get user info from localStorage
    const userInfoStr = localStorage.getItem('user_info');
    if (userInfoStr) {
        const userInfo = JSON.parse(userInfoStr);
        if (userInfo.role !== 'admin') {
            // Redirect non-admin users
            window.location.href = '/index';
            return;
        }
    } else {
        // If no user info, fetch from API
        fetchUserProfile();
    }

    // Initialize the admin dashboard
    initTabs();
    loadUsers();
    setupEventListeners();
    setupEmailConfigTesting();
});

// Fetch user profile to check admin status
async function fetchUserProfile() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/auth/profile', {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch user profile');
        }

        const userInfo = await response.json();

        // Check if user is admin
        if (userInfo.role !== 'admin') {
            // Redirect non-admin users
            window.location.href = '/index';
            return;
        }

        // Store user info in localStorage
        localStorage.setItem('user_info', JSON.stringify(userInfo));
    } catch (error) {
        console.error('Error fetching user profile:', error);
        window.location.href = '/login';
    }
}

// Initialize tabs
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}

// Load users from API
async function loadUsers() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/auth/admin/users', {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch users');
        }

        const users = await response.json();
        displayUsers(users);
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Failed to load users. Please try again later.');
    }
}

// Display users in the table
function displayUsers(users) {
    const tableBody = document.getElementById('users-table-body');
    tableBody.innerHTML = '';

    users.forEach(user => {
        const row = document.createElement('tr');

        // Format date
        const createdDate = new Date(user.created_at);
        const formattedDate = createdDate.toLocaleDateString();

        // Determine status
        let status = 'Active';
        let statusClass = 'status-active';
        if (!user.email_verified) {
            status = 'Pending';
            statusClass = 'status-pending';
        }

        row.innerHTML = `
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>${user.role}</td>
            <td><span class="user-status ${statusClass}">${status}</span></td>
            <td>${formattedDate}</td>
            <td class="user-actions">
                <button class="btn-icon btn-edit" data-email="${user.email}"><i class="fas fa-edit"></i></button>
                <button class="btn-icon btn-delete" data-email="${user.email}"><i class="fas fa-trash"></i></button>
            </td>
        `;

        tableBody.appendChild(row);
    });

    // Add event listeners to action buttons
    addActionListeners();
}

// Add event listeners to user action buttons
function addActionListeners() {
    // Edit user buttons
    document.querySelectorAll('.btn-edit').forEach(button => {
        button.addEventListener('click', () => {
            const email = button.getAttribute('data-email');
            // TODO: Implement edit user functionality
            alert(`Edit user: ${email}`);
        });
    });

    // Delete user buttons
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', () => {
            const email = button.getAttribute('data-email');
            if (confirm(`Are you sure you want to delete user ${email}?`)) {
                // TODO: Implement delete user functionality
                alert(`Delete user: ${email}`);
            }
        });
    });
}

// Setup event listeners
function setupEventListeners() {
    // Add user button
    const addUserBtn = document.getElementById('add-user-btn');
    const addUserModal = document.getElementById('add-user-modal');
    const closeBtn = document.querySelector('.close');

    addUserBtn.addEventListener('click', () => {
        addUserModal.style.display = 'block';
    });

    closeBtn.addEventListener('click', () => {
        addUserModal.style.display = 'none';
    });

    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === addUserModal) {
            addUserModal.style.display = 'none';
        }
    });

    // Add user form submission
    const addUserForm = document.getElementById('add-user-form');
    addUserForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = document.getElementById('new-user-name').value;
        const email = document.getElementById('new-user-email').value;
        const password = document.getElementById('new-user-password').value;
        const role = document.getElementById('new-user-role').value;
        const emailVerified = document.getElementById('new-user-verified').checked;

        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/auth/admin/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify({
                    name,
                    email,
                    password,
                    role,
                    email_verified: emailVerified
                })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to add user');
            }

            // Close modal and reload users
            addUserModal.style.display = 'none';
            addUserForm.reset();
            loadUsers();

            // Show success message
            showSuccess('User added successfully');
        } catch (error) {
            console.error('Error adding user:', error);
            showError(error.message);
        }
    });

    // Search functionality
    const searchInput = document.getElementById('user-search');
    searchInput.addEventListener('input', () => {
        const searchTerm = searchInput.value.toLowerCase();
        const rows = document.querySelectorAll('#users-table-body tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });

    // Settings form submission
    const settingsForm = document.getElementById('settings-form');
    settingsForm.addEventListener('submit', (e) => {
        e.preventDefault();
        // TODO: Implement settings save functionality
        showSuccess('Settings saved successfully');
    });

    // Refresh logs button
    const refreshLogsBtn = document.getElementById('refresh-logs');
    refreshLogsBtn.addEventListener('click', () => {
        // TODO: Implement logs refresh functionality
        document.getElementById('logs-content').textContent = 'No logs available';
    });

    // Handle logout
    document.querySelector('.logout a').addEventListener('click', function(e) {
        e.preventDefault();
        localStorage.removeItem('token');
        localStorage.removeItem('user_info');
        window.location.href = '/login';
    });
}

// Show success message
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;

    // Add to the top of the main content
    const mainContent = document.querySelector('.main-content');
    mainContent.insertBefore(successDiv, mainContent.firstChild);

    // Remove after 3 seconds
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;

    // Add to the top of the main content
    const mainContent = document.querySelector('.main-content');
    mainContent.insertBefore(errorDiv, mainContent.firstChild);

    // Remove after 3 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 3000);
}

// Setup email configuration testing
function setupEmailConfigTesting() {
    const testEmailBtn = document.getElementById('test-email-btn');
    const sendTestEmailBtn = document.getElementById('send-test-email-btn');
    const emailStatusIndicator = document.getElementById('email-status-indicator');
    const emailStatusTitle = document.getElementById('email-status-title');
    const emailStatusMessage = document.getElementById('email-status-message');
    const emailConfigDetails = document.getElementById('email-config-details');

    // Test email configuration
    testEmailBtn.addEventListener('click', async () => {
        try {
            // Update UI to show testing state
            emailStatusIndicator.className = 'status-indicator unknown';
            emailStatusIndicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            emailStatusTitle.textContent = 'Testing...';
            emailStatusMessage.textContent = 'Checking email configuration...';
            emailConfigDetails.innerHTML = '';
            sendTestEmailBtn.disabled = true;

            // Call the API to test email configuration
            const token = localStorage.getItem('token');
            const response = await fetch('/api/auth/admin/test-email', {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            });

            if (!response.ok) {
                throw new Error('Failed to test email configuration');
            }

            const result = await response.json();

            // Update UI based on result
            if (result.status === 'success') {
                emailStatusIndicator.className = 'status-indicator success';
                emailStatusIndicator.innerHTML = '<i class="fas fa-check-circle"></i>';
                emailStatusTitle.textContent = 'Email Configuration Valid';
                emailStatusMessage.textContent = result.message;
                sendTestEmailBtn.disabled = false;
            } else if (result.status === 'not_configured') {
                emailStatusIndicator.className = 'status-indicator warning';
                emailStatusIndicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                emailStatusTitle.textContent = 'Email Not Configured';
                emailStatusMessage.textContent = result.message;
                sendTestEmailBtn.disabled = true;
            } else if (result.status === 'error') {
                emailStatusIndicator.className = 'status-indicator error';
                emailStatusIndicator.innerHTML = '<i class="fas fa-times-circle"></i>';
                emailStatusTitle.textContent = 'Email Configuration Error';
                emailStatusMessage.textContent = result.message;
                sendTestEmailBtn.disabled = true;
            } else {
                emailStatusIndicator.className = 'status-indicator unknown';
                emailStatusIndicator.innerHTML = '<i class="fas fa-question-circle"></i>';
                emailStatusTitle.textContent = 'Unknown Status';
                emailStatusMessage.textContent = 'Could not determine email configuration status';
                sendTestEmailBtn.disabled = true;
            }

            // Display configuration details
            if (result.details) {
                let detailsHtml = '<h3>Configuration Details</h3>';
                detailsHtml += '<ul>';

                for (const [key, value] of Object.entries(result.details)) {
                    if (key === 'password' || key === 'error') continue;
                    detailsHtml += `<li><strong>${key}:</strong> ${value}</li>`;
                }

                if (result.details.error) {
                    detailsHtml += `<li><strong>Error:</strong> ${result.details.error}</li>`;
                }

                detailsHtml += '</ul>';

                if (result.help) {
                    detailsHtml += `<p><strong>Help:</strong> ${result.help}</p>`;
                }

                emailConfigDetails.innerHTML = detailsHtml;
            }
        } catch (error) {
            console.error('Error testing email configuration:', error);
            emailStatusIndicator.className = 'status-indicator error';
            emailStatusIndicator.innerHTML = '<i class="fas fa-times-circle"></i>';
            emailStatusTitle.textContent = 'Test Failed';
            emailStatusMessage.textContent = error.message;
            emailConfigDetails.innerHTML = '';
            sendTestEmailBtn.disabled = true;
        }
    });

    // Send test email
    sendTestEmailBtn.addEventListener('click', async () => {
        const email = prompt('Enter email address to send test to:');
        if (!email) return;

        try {
            // TODO: Implement send test email functionality
            showSuccess(`Test email would be sent to ${email} (not implemented yet)`);
        } catch (error) {
            console.error('Error sending test email:', error);
            showError(error.message);
        }
    });
}
