document.addEventListener('DOMContentLoaded', function() {
    const cartIcon = document.getElementById('cart-icon');
    const cartPopover = document.getElementById('cart-popover');
    const overlay = document.getElementById('overlay');
    const closeCartBtn = document.getElementById('close-cart-btn');

    // Function to show the cart popover
    function showPopover() {
        cartPopover.style.visibility = 'visible';
        cartPopover.style.opacity = '1';
        overlay.classList.add('visible'); // Ensure this class is defined in your CSS to show overlay
    }

    // Function to hide the cart popover
    function hidePopover() {
        cartPopover.style.visibility = 'hidden';
        cartPopover.style.opacity = '0';
        overlay.classList.remove('visible'); // Ensure this class is defined in your CSS to hide overlay
    }

    // Event listener for the cart icon click
    cartIcon.addEventListener('click', function(event) {
        event.preventDefault(); // Prevent default action of the anchor tag
        const isVisible = cartPopover.style.visibility === 'visible';

        // Toggle visibility based on current state
        if (isVisible) {
            hidePopover();
        } else {
            showPopover();
            updateCartDisplay(); // Update the cart display when showing the popover
        }
    });

    // Event listener for closing the cart popover
    closeCartBtn.addEventListener('click', function() {
        hidePopover();
    });

    // Event listener for clicks outside the popover
    window.addEventListener('click', function(event) {
        // Check if the click was outside the cart popover and the cart icon
        if (!cartPopover.contains(event.target) && !cartIcon.contains(event.target)) {
            hidePopover();
        }
    });

    // Function to remove an item from the cart
    function removeItem(itemId) {
        let cart = JSON.parse(localStorage.getItem('cart')) || [];
        cart = cart.filter(item => item.id !== itemId); // Remove the item from the cart
        localStorage.setItem('cart', JSON.stringify(cart)); // Update local storage
        updateCartDisplay(); // Update the cart display
    }

    // Function to update the cart display
    function updateCartDisplay() {
        const cartItemsContainer = document.querySelector('.cart-items');
        cartItemsContainer.innerHTML = ''; // Clear current items
        let cart = JSON.parse(localStorage.getItem('cart')) || [];
        
        cart.forEach(item => {
            const cartItem = document.createElement('div');
            cartItem.classList.add('cart-item');
            cartItem.innerHTML = `
                <img src="${item.image}" alt="${item.name}" class="product-img">
                <div class="product-details">
                    <p>${item.name}</p>
                    <p>${item.quantity} x <span class="price">₱${item.price}</span></p>
                </div>
                <button class="remove-btn" data-id="${item.id}">x</button>
            `;
            cartItemsContainer.appendChild(cartItem);
        });

        // Add event listeners to remove buttons
        cartItemsContainer.querySelectorAll('.remove-btn').forEach(button => {
            button.addEventListener('click', function(event) {
                event.stopPropagation(); // Prevent the click from closing the popover
                const itemId = parseInt(this.getAttribute('data-id'));
                console.log(`Removing item with ID: ${itemId}`); // Debugging log
                removeItem(itemId);
            });
        });
    }

    // Initial update of cart display when the popover is shown
    updateCartDisplay();
});