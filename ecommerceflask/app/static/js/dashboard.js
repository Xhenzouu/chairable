document.addEventListener('DOMContentLoaded', () => {
    const addProductBtn = document.getElementById('addProductBtn');
    const productTableBody = document.getElementById('productTableBody');

    // Function to display products
    function displayProducts(products) {
        productTableBody.innerHTML = '';
        products.forEach(product => {
            const productRow = document.createElement('tr');
            productRow.innerHTML = `
                <td>${product.id}</td>
                <td>${product.name}</td>
                <td>PHP ${product.price}</td>
                <td>${product.description}</td>
                <td>${product.stock}</td>
                <td>${product.category}</td>
                <td>
                    <button class="editBtn" data-id="${product.id}">Edit</button>
                    <button class="deleteBtn" data-id="${product.id}">Delete</button>
                </td>
            `;
            productTableBody.appendChild(productRow);
        });
    }

    // Function to fetch products from the server
    async function fetchProducts() {
        try {
            const response = await fetch('/api/products'); // Replace with your actual API endpoint
            const products = await response.json();
            displayProducts(products);
        } catch (error) {
            console.error('Error fetching products:', error);
        }
    }

    // Add product button click event (this can be adjusted to your needs)
    addProductBtn.addEventListener('click', () => {
        // Implement logic for adding a new product (e.g., open a modal or redirect to add product page)
        window.location.href = '/add_product'; // Redirect to add product page
    });

    // Fetch and display initial products
    fetchProducts();
});
