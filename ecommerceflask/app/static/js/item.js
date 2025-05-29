document.addEventListener('DOMContentLoaded', function () {
    let cart = [];
    const overlay = document.getElementById('item-added-overlay');

    // Load cart data from localStorage
    try {
        const cartData = localStorage.getItem('cart');
        if (cartData) {
            cart = JSON.parse(cartData);
            console.log("Initial cart data:", cart);
        }
    } catch (error) {
        console.error("Error parsing cart data from localStorage:", error);
        cart = [];
    }

    function updateCartDisplay() {
        const cartPopover = document.querySelector('.cart-items');
        if (!cartPopover) return;

        cartPopover.innerHTML = ''; // Clear current items
        let subtotal = 0;

        cart.forEach(item => {
            const itemPrice = parseFloat(item.price.replace(/[^0-9.]/g, ''));
            const itemQuantity = parseInt(item.quantity);

            if (!isNaN(itemPrice) && !isNaN(itemQuantity)) {
                const itemTotal = itemPrice * itemQuantity;
                subtotal += itemTotal;

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
                cartPopover.appendChild(cartItem);
            }
        });

        const shipping = Math.max(subtotal * 0.10, 5);
        const total = subtotal + shipping;

        // Update the displays
        updatePriceDisplays(subtotal, shipping, total);
    }

    // Update price-related elements in the DOM
    function updatePriceDisplays(subtotal, shipping, total) {
        try {
            const subtotalElement = document.getElementById('subtotal');
            if (subtotalElement) {
                subtotalElement.textContent = `₱${subtotal.toFixed(2)}`;
            } else {
                console.error("Subtotal element not found");
            }

            const shippingElement = document.getElementById('shipping');
            if (shippingElement) {
                shippingElement.textContent = `₱${shipping.toFixed(2)}`;
            } else {
                console.error("Shipping element not found");
            }

            const totalElement = document.getElementById('total');
            if (totalElement) {
                totalElement.textContent = `₱${total.toFixed(2)}`;
            } else {
                console.error("Total element not found");
            }
        } catch (error) {
            console.error("Error updating price displays:", error);
        }
    }

    // Add item to the cart or update quantity if already exists
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const id = this.getAttribute('data-id');
            const name = this.getAttribute('data-name');
            const price = this.getAttribute('data-price');
            const image = this.getAttribute('data-image');
            const quantityInput = document.getElementById(`quantity-${id}`);
            let quantity = parseInt(quantityInput.value, 10) || 1;
    
            // Ensure quantity is valid
            if (quantity <= 0) {
                alert('Quantity must be at least 1.');
                quantityInput.value = 1;
                return;
            }
    
            const existingItem = cart.find(item => item.id === id);
            const availableStock = parseInt(quantityInput.getAttribute('max'), 10);
    
            // Calculate the total quantity including the existing item in the cart
            const totalQuantity = existingItem ? existingItem.quantity + quantity : quantity;
    
            // Check if the total quantity exceeds available stock
            if (totalQuantity > availableStock) {
                alert(`You can only add ${availableStock - (existingItem ? existingItem.quantity : 0)} more of this item.`);
                return; // Exit the function if the limit is exceeded
            }
    
            // Update the cart
            if (existingItem) {
                existingItem.quantity += quantity;
            } else {
                cart.push({ id, name, price, image, quantity });
            }
    
            localStorage.setItem('cart', JSON.stringify(cart)); // Save to localStorage
            updateCartDisplay(); // Update the cart display
    
            // Show overlay after adding item to cart
            overlay.classList.add('visible');
            setTimeout(() => {
                overlay.classList.remove('visible');
            }, 1500);
        });
    });
    
    // Cart button event listener
    document.getElementById('cart-btn').addEventListener('click', function () {
        window.location.href = '/cart'; // Redirect to the cart route
    });
    
    // Handle quantity input changes
    document.querySelectorAll('.quantity input[type="number"]').forEach(quantityInput => {
        const productId = quantityInput.id.split('-').pop();
        const warning = document.getElementById(`stock-warning-${productId}`);
        const addToCartButton = document.querySelector(`.add-to-cart[data-id="${productId}"]`);
    
        quantityInput.addEventListener('input', function () {
            let selectedQuantity = parseInt(quantityInput.value, 10) || 0;
    
            // Ensure quantity is valid
            if (selectedQuantity <= 0) {
                alert('Quantity must be at least 1.');
                quantityInput.value = 1;
                selectedQuantity = 1;
            }
    
            const availableStock = parseInt(quantityInput.getAttribute('max'), 10);
            const existingItem = cart.find(item => item.id === productId);
            const currentQuantity = existingItem ? existingItem.quantity : 0;
    
            // Calculate the total quantity including the existing item in the cart
            const totalQuantity = currentQuantity + selectedQuantity;
    
            if (totalQuantity > availableStock) {
                warning.style.display = 'inline';
                addToCartButton.disabled = true;
                alert(`You can only add ${availableStock - currentQuantity} more of this item.`);
            } else {
                warning.style.display = 'none';
                addToCartButton.disabled = false;
            }
    
            // Update the cart display after changes to quantity
            updateCartDisplay();
        });
    });

    // Remove item from the cart
    function removeFromCart(id) {
        cart = cart.filter(item => item.id !== id); // Filter out the item
        localStorage.setItem('cart', JSON.stringify(cart)); // Update localStorage
        updateCartDisplay(); // Update the display
    }

    // Event delegation for remove buttons
    document.addEventListener('click', function (e) {
        const removeBtn = e.target.closest('.remove-btn');
        if (removeBtn && removeBtn.hasAttribute('data-id')) {
            e.preventDefault();
            const itemId = removeBtn.getAttribute('data-id');
            removeFromCart(itemId);
        }
    });

    // Initial cart display
    updateCartDisplay();
});