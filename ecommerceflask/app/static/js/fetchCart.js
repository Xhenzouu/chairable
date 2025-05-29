document.addEventListener("DOMContentLoaded", () => {
    updateCartDisplay();
});

function updateCartDisplay() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    let subtotal = 0;

    cart.forEach(item => {
        const itemPrice = parseFloat(item.price);
        const quantity = parseInt(item.quantity || 1);
        subtotal += itemPrice * quantity;
    });

    // Calculate shipping and total
    const shipping = subtotal * 0.10; // 10% shipping fee
    const total = subtotal + shipping;

    // Update the order summary in checkout
    if (document.getElementById('subtotal')) {
        document.getElementById('subtotal').textContent = `PHP ${subtotal.toFixed(2)}`;
    }
    if (document.getElementById('total')) {
        document.getElementById('total').textContent = `PHP ${total.toFixed(2)}`;
    }
}

function removeItem(itemId) {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const updatedCart = cart.filter(item => item.id !== itemId);
    localStorage.setItem('cart', JSON.stringify(updatedCart));
    updateCartDisplay();
}
function removeItem(itemId) {
    // Implement remove item logic here
    console.log(`Removing item with ID: ${itemId}`);
}

function updateOrderSummary(subtotal, total) {
    // Update the order summary fields in the checkout
    document.getElementById('subtotal').textContent = `PHP ${subtotal.toFixed(2)}`;
    document.getElementById('total').textContent = `PHP ${total.toFixed(2)}`; // Total includes subtotal and shipping
}