document.addEventListener('DOMContentLoaded', function() {
    const checkoutForm = document.getElementById('checkout-form');

    // Function to update order summary
    function updateOrderSummary() {
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        let subtotal = 0;
    
        cart.forEach(item => {
            item.price = parseFloat(item.price);
            item.quantity = parseInt(item.quantity || 1);
            subtotal += item.price * item.quantity; // Calculate subtotal
        });
    
        const shippingFee = Math.max(subtotal * 0.10, 5); // Calculate shipping fee
        const total = subtotal + shippingFee; // Total includes subtotal and shipping fee
    
        // Update the order summary fields
        document.getElementById('subtotal').textContent = `PHP ${subtotal.toFixed(2)}`;
        document.getElementById('shipping').textContent = `PHP ${shippingFee.toFixed(2)}`;
        document.getElementById('total').textContent = `PHP ${total.toFixed(2)}`;
    }

    // Call updateOrderSummary to display initial totals
    updateOrderSummary();

    // Event listener for the checkout form submission
    checkoutForm.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent the default form submission

        const cart = JSON.parse(localStorage.getItem('cart')) || [];
    
        // Check if the cart is empty
        if (cart.length === 0) {
            alert('Your cart is empty. Please add items to your cart before checking out.');
            return;
        }

        // Collect form data
        const formData = {
            firstName: document.getElementById('first-name').value,
            companyName: document.getElementById('company-name').value,
            country: document.getElementById('country').value,
            streetAddress: document.getElementById('street-address').value,
            city: document.getElementById('city').value,
            province: document.getElementById('province').value,
            zipCode: document.getElementById('zip-code').value,
            phone: document.getElementById('phone').value,
            email: document.getElementById('email').value,
            additionalInfo: document.getElementById('additional-info').value,
            cart: cart, // Include cart data with the order
            subtotal: parseFloat(document.getElementById('subtotal').textContent.replace(/PHP\s|\./g, '')),
            shipping: parseFloat(document.getElementById('shipping').textContent.replace(/PHP\s|\./g, '')),
            total: parseFloat(document.getElementById('total').textContent.replace(/PHP\s|\./g, ''))
        };

        // Disable the button to prevent multiple clicks
        const checkoutBtn = document.getElementById('place-order-btn');
        checkoutBtn.disabled = true;

        // Send a POST request to create the order
        fetch('/create-order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Order placed successfully!');
                localStorage.removeItem('cart'); // Clear the cart from local storage
                window.location.href = '/current_orders'; // Redirect to current orders
            } else {
                alert(data.message || 'Failed to place order. Please try again.');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('An error occurred while placing the order. Please try again later.');
        })
        .finally(() => {
            checkoutBtn.disabled = false; // Re-enable the button
        });
    });
});