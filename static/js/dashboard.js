// ============================================
// DASHBOARD.JS - Main dashboard functionality
// ============================================

let currentOrderId = null;

// Quick Status Update Modal
function quickStatusUpdate(orderId) {
    const modal = document.getElementById('statusModal');
    const orderIdSpan = document.getElementById('modalOrderId');
    
    currentOrderId = orderId;
    orderIdSpan.textContent = `#${orderId.substring(0, 8).toUpperCase()}`;
    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('statusModal');
    modal.style.display = 'none';
    currentOrderId = null;
}

function confirmStatusUpdate() {
    const statusSelect = document.getElementById('statusSelect');
    const newStatus = statusSelect.value;
    
    if (!currentOrderId) return;
    
    // Show loading state
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = 'Updating...';
    btn.disabled = true;
    
    // Make AJAX request to update order
    fetch(`/admin/quick-order-update/${currentOrderId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: `status=${newStatus}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification('✅ Order status updated successfully!', 'success');
            
            // Close modal
            closeModal();
            
            // Refresh page after 1 second
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('❌ Failed to update order status', 'error');
            btn.textContent = originalText;
            btn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('❌ An error occurred', 'error');
        btn.textContent = originalText;
        btn.disabled = false;
    });
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('statusModal');
    if (event.target == modal) {
        closeModal();
    }
}

// Close modal with close button
document.addEventListener('DOMContentLoaded', function() {
    const closeBtn = document.querySelector('.close');
    if (closeBtn) {
        closeBtn.onclick = closeModal;
    }
});

// ============================================
// ORDER_QUICK_UPDATE.JS - Order list page updates
// ============================================

function updateOrderStatus(selectElement, orderId) {
    const newStatus = selectElement.value;
    const originalValue = selectElement.getAttribute('data-original');
    
    // Confirm before updating
    if (confirm(`Are you sure you want to change this order to "${newStatus}"?`)) {
        // Show loading state
        selectElement.disabled = true;
        
        // Make AJAX request
        fetch(`/admin/quick-order-update/${orderId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `status=${newStatus}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('✅ ' + data.message, 'success');
                selectElement.setAttribute('data-original', newStatus);
                
                // Update the select element color based on new status
                updateSelectColor(selectElement, newStatus);
            } else {
                showNotification('❌ Failed to update order', 'error');
                selectElement.value = originalValue;
            }
            selectElement.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('❌ An error occurred', 'error');
            selectElement.value = originalValue;
            selectElement.disabled = false;
        });
    } else {
        // Reset to original value if cancelled
        selectElement.value = originalValue;
    }
}

function updateSelectColor(selectElement, status) {
    const colors = {
        'pending': '#f39c12',
        'paid': '#3498db',
        'processing': '#9b59b6',
        'shipped': '#1abc9c',
        'delivered': '#27ae60',
        'cancelled': '#e74c3c',
        'refunded': '#95a5a6'
    };
    
    const color = colors[status] || '#95a5a6';
    selectElement.style.background = color;
    selectElement.style.borderColor = color;
}

// Stock adjustment function (for inventory page)
function adjustStock(inventoryId, amount) {
    if (confirm(`Are you sure you want to adjust stock by ${amount > 0 ? '+' : ''}${amount}?`)) {
        fetch(`/admin/adjust-stock/${inventoryId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `amount=${amount}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`✅ Stock adjusted by ${amount}`, 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showNotification('❌ Failed to adjust stock', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('❌ An error occurred', 'error');
        });
    }
}

// Review approval function
function approveReview(reviewId) {
    if (confirm('Approve this review?')) {
        fetch(`/admin/approve-review/${reviewId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('✅ Review approved!', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showNotification('❌ Failed to approve review', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('❌ An error occurred', 'error');
        });
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show notification toast
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification-toast');
    if (existing) {
        existing.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification-toast notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#27ae60' : '#e74c3c'};
        color: white;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 10000;
        font-weight: 600;
        font-size: 15px;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations to CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize tooltips and other UI enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading animation to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Loading...';
            }
        });
    });
    
    // Auto-hide Django messages after 5 seconds
    setTimeout(() => {
        const messages = document.querySelectorAll('.messagelist li, .messages li');
        messages.forEach(msg => {
            msg.style.transition = 'opacity 0.5s';
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        });
    }, 5000);
    
    // Add print functionality
    const printBtns = document.querySelectorAll('[data-print]');
    printBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            window.print();
        });
    });
    
    // Add export functionality hint
    console.log('%c🎨 Custom Admin Dashboard Loaded Successfully!', 'color: #27ae60; font-size: 16px; font-weight: bold;');
    console.log('%c💡 Tip: Use Ctrl+P to print any page', 'color: #3498db; font-size: 14px;');
});