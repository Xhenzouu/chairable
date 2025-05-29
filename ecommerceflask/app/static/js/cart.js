function cleanCart() {
    // Clear the cart from local storage
    localStorage.removeItem('cart');

    // Reset the displayed cart items to reflect the empty state
    cart = []; // Clear the cart array
    document.querySelector('.cart-items').innerHTML = '<p>Your cart is empty.</p>';
    document.querySelector('#subtotal').innerText = '₱0.00';
    document.querySelector('#total').innerText = '₱0.00';

    // Provide user feedback if needed
    alert('Your cart has been cleared.');

    // Update the cart display
    updateCartDisplay(); // Call to update the cart display after cleaning
}

function updateQuantity(itemId, action, value) {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    const item = cart.find(item => item.id === itemId);
    if (item) {
        switch (action) {
            case 'increase':
                if (item.quantity < 500) item.quantity++;
                break;
            case 'decrease':
                if (item.quantity > 1) item.quantity--;
                break;
            case 'input':
                let newValue = parseInt(value);
                const availableStock = parseInt(document.getElementById(`quantity-${itemId}`).getAttribute('max'));
                if (newValue >= 1 && newValue <= availableStock) {
                    item.quantity = newValue;
                } else if (newValue < 1) {
                    item.quantity = 1;
                } else if (newValue > availableStock) {
                    item.quantity = availableStock;
                }
                break;
        }
        localStorage.setItem('cart', JSON.stringify(cart));  // Save updated cart to localStorage
        document.dispatchEvent(new CustomEvent('updateCart'));  // Trigger update for display
    }
}

document.addEventListener('DOMContentLoaded', function () {
    let cart = [];
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

    // Function to synchronize local storage cart with the server
function syncLocalStorageCartWithServer() {
    const cart = JSON.parse(localStorage.getItem('cart')) || []; // Retrieve cart from local storage

    fetch('/api/cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(cart), // Send the cart data to the server
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error syncing cart with server:', data.error);
        } else {
            console.log("Cart synced with server:", data.message);
        }
    })
    .catch(error => {
        console.error('Error syncing cart with server:', error);
    });
}

// Call this function whenever you want to sync the cart
syncLocalStorageCartWithServer();
    
    function updateCartDisplay() {
        let cart = JSON.parse(localStorage.getItem('cart')) || [];
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

        // Display cart items
        displayCartItems(cart, cartPopover);
    
        // Update the main cart table
        updateMainCartTable(cart);
    }
            
    function updatePriceDisplays(subtotal, shipping, total) {
        try {
            // Debug log before updates
            console.log("Attempting to update prices:");
            console.log("Subtotal to update:", subtotal);
            console.log("Shipping to update:", shipping);
            console.log("Total to update:", total);
    
            // Update subtotal
            const subtotalElement = document.getElementById('subtotal');
            if (subtotalElement) {
                subtotalElement.textContent = `₱${subtotal.toFixed(2)}`;
                console.log("Updated subtotal element:", subtotalElement.textContent);
            } else {
                console.error("Subtotal element not found");
            }
    
            // Update shipping
            const shippingElement = document.getElementById('shipping');
            if (shippingElement) {
                shippingElement.textContent = `₱${shipping.toFixed(2)}`;
                console.log("Updated shipping element:", shippingElement.textContent);
            } else {
                console.error("Shipping element not found");
            }
    
            // Update total
            const totalElement = document.getElementById('total');
            if (totalElement) {
                totalElement.textContent = `₱${total.toFixed(2)}`;
                console.log("Updated total element:", totalElement.textContent);
            } else {
                console.error("Total element not found");
            }
    
            // Update cart summary/popover if it exists
            const popoverSubtotal = document.querySelector('.subtotal-row .price');
            if (popoverSubtotal) {
                popoverSubtotal.textContent = `₱${subtotal.toFixed(2)}`;
            }
    
        } catch (error) {
            console.error("Error updating price displays:", error);
        }
    }

    function displayCartItems(cart, cartPopover) {
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
            cartPopover.appendChild(cartItem);
        });
    }

    function updateMainCartTable(cartItems) {
        const tableBody = document.querySelector('.table tbody');
        if (!tableBody) {
            console.error("Cart table body not found");
            return;
        }
    
        tableBody.innerHTML = '';
    
        if (cartItems.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Your cart is empty.</td></tr>';
        } else {
            cartItems.forEach(item => {
                const itemPrice = parseFloat(item.price.replace(/[^0-9.]/g, ''));
                const itemTotal = itemPrice * item.quantity;
                
                const row = `
                <tr>
                    <td class="text-center"><img src="${item.image}" alt="${item.name}" class="cart-item-image"></td>
                    <td class="text-center">${item.name}</td>
                    <td class="text-center">
                        <div class="quantity-controls">
                            <button type="button" 
                                    class="icon-button quantity-btn" 
                                    onclick="updateQuantity('${item.id}', 'decrease')"
                                    title="Decrease quantity"
                                    aria-label="Decrease quantity for ${item.name}">
                                <i class="fas fa-minus"></i>
                            </button>
                            <input type="number" 
                                   class="quantity-input" 
                                   value="${item.quantity}" 
                                   min="1" 
                                   max="500"
                                   data-id="${item.id}"
                                   onchange="updateQuantity('${item.id}', 'input', this.value)"
                                   title="Product quantity"
                                   aria-label="Quantity for ${item.name}"
                                   id="quantity-${item.id}"
                                   name="quantity-${item.id}">
                            <button type="button" 
                                    class="icon-button quantity-btn" 
                                    onclick="updateQuantity('${item.id}', 'increase')"
                                    title="Increase quantity"
                                    aria-label="Increase quantity for ${item.name}">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </td>
                    <td class="text-center">₱${itemPrice.toFixed(2)}</td>
                    <td class="text-center">₱${itemTotal.toFixed(2)}</td>
                    <td class="text-center">
                        <button type="button" 
                                class="icon-button" 
                                data-id="${item.id}" 
                                title="Remove item"
                                aria-label="Remove ${item.name} from cart">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                </tr>
            `;
        tableBody.innerHTML += row;
            });
        }
    }

    function syncCartWithServer(cart) {
        fetch('/update_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({cart: cart}),
        })
        .then(response => response.json())
        .then(data => {
            console.log("Cart synced with server:", data);
        })
        .catch((error) => {
            console.error('Error syncing cart with server:', error);
        });
    }

    function removeFromCart(id) {
        cart = cart.filter(item => item.id !== id);  // Filter out the item
        localStorage.setItem('cart', JSON.stringify(cart));  // Update localStorage
        updateCartDisplay();  // Update the display
    }
        
    // Event delegation for remove buttons in both the cart popover and main cart table
    document.addEventListener('click', function (e) {
        // Check if the clicked element is the remove button or its icon
        const removeBtn = e.target.closest('.icon-button');
    
        if (removeBtn && removeBtn.hasAttribute('data-id')) {
            e.preventDefault(); // Prevent default action
            e.stopPropagation(); // Stop event from bubbling up
    
            // Get the item ID from the button's data-id attribute
            const itemId = removeBtn.getAttribute('data-id');
    
            // Call the remove function with the item ID
            removeFromCart(itemId);
        }
    });

    // Checkout button event listener
    document.getElementById('checkout-btn').addEventListener('click', function() {
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        if (cart.length === 0) {
            alert('Your cart is empty. Please add items to your cart before checking out.');
            return;
        }

        const stockCheckPromises = cart.map(item => {
            return fetch(`/api/product-stock/${item.id}`)
                .then(response => response.json())
                .then(data => {
                    if (!data.success || data.stock < item.quantity) {
                        throw new Error(`Not enough stock for ${item.name}. Available: ${data.stock}, Required: ${item.quantity}`);
                    }
                });
        });

        Promise.all(stockCheckPromises)
            .then(() => {
                window.location.href = '/checkout';
            })
            .catch(error => {
                alert(error.message);
            });
    });
        // Add event listener to add to cart buttons
        document.querySelectorAll('.add-to-cart').forEach(button => {
            button.addEventListener('click', function (e) {
                e.preventDefault();
                const id = this.getAttribute('data-id');
                const name = this.getAttribute('data-name');
                const price = this.getAttribute('data-price');
                const image = this.getAttribute('data-image');
                const quantityInput = document.querySelector(`#quantity-${id}`);
        
                // Ensure a valid quantity is parsed
                const selectedQuantity = quantityInput && quantityInput.value !== "" 
                    ? parseInt(quantityInput.value) 
                    : 1;
        
                // Debugging logs
                console.log("Adding to cart:");
                console.log(`ID: ${id}, Name: ${name}, Price: ${price}, Quantity: ${selectedQuantity}`);
        
                // Check if the item already exists in the cart
                const existingItem = cart.find(item => item.id === id);
                if (existingItem) {
                    // Update existing item quantity with a cap at 99
                    existingItem.quantity = Math.min(existingItem.quantity + selectedQuantity, 500);
                } else {
                    // Add new item to the cart
                    cart.push({ id, name, price, image, quantity: selectedQuantity });
                }
        
                // Save and update
                localStorage.setItem('cart', JSON.stringify(cart));
                updateCartDisplay();
                syncCartWithServer(cart);
            });
        });
            // Initial display of cart items
    updateCartDisplay();
});