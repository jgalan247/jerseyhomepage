// static/js/add-to-cart.js

document.addEventListener('DOMContentLoaded', function() {
    // Add to cart functionality
    const addToCartForm = document.getElementById('add-to-cart-form');
    
    if (addToCartForm) {
        addToCartForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const button = this.querySelector('button[type="submit"]');
            const originalText = button.textContent;
            
            // Disable button and show loading
            button.disabled = true;
            button.textContent = 'Adding...';
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update cart badge
                    updateCartBadge(data.cart_items_count);
                    
                    // Show success message
                    showNotification(data.message, 'success');
                    
                    // Show mini cart preview
                    showMiniCart(data);
                } else {
                    showNotification(data.error, 'error');
                }
            })
            .catch(error => {
                showNotification('An error occurred. Please try again.', 'error');
            })
            .finally(() => {
                // Re-enable button
                button.disabled = false;
                button.textContent = originalText;
            });
        });
    }
    
    // Update cart badge
    function updateCartBadge(count) {
        const badges = document.querySelectorAll('.cart-badge');
        badges.forEach(badge => {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'block' : 'none';
        });
    }
    
    // Show notification
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    // Show mini cart preview
    function showMiniCart(data) {
        const miniCart = document.getElementById('mini-cart-preview');
        if (!miniCart) return;
        
        miniCart.innerHTML = `
            <div class="p-4 bg-white rounded-lg shadow-lg">
                <p class="font-semibold mb-2">Added to cart!</p>
                <p class="text-sm text-gray-600 mb-3">${data.cart_items_count} items - £${parseFloat(data.cart_total).toFixed(2)}</p>
                <div class="flex gap-2">
                    <a href="/booking/cart/" class="flex-1 text-center py-2 bg-gray-200 rounded hover:bg-gray-300">
                        View Cart
                    </a>
                    <a href="/booking/checkout/" class="flex-1 text-center py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                        Checkout
                    </a>
                </div>
            </div>
        `;
        
        miniCart.classList.remove('hidden');
        
        // Hide after 5 seconds
        setTimeout(() => {
            miniCart.classList.add('hidden');
        }, 5000);
    }
    
    // Cart dropdown toggle
    const cartToggle = document.getElementById('cart-dropdown-toggle');
    const cartDropdown = document.getElementById('cart-dropdown');
    
    if (cartToggle && cartDropdown) {
        cartToggle.addEventListener('click', function(e) {
            e.preventDefault();
            cartDropdown.classList.toggle('hidden');
            
            // Load cart items if visible
            if (!cartDropdown.classList.contains('hidden')) {
                loadCartPreview();
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!cartToggle.contains(e.target) && !cartDropdown.contains(e.target)) {
                cartDropdown.classList.add('hidden');
            }
        });
    }
    
    // Load cart preview
    function loadCartPreview() {
        // This would fetch cart items via AJAX
        // For now, just show a loading message
        const cartDropdown = document.getElementById('cart-dropdown');
        cartDropdown.innerHTML = '<div class="p-4">Loading cart...</div>';
    }
});