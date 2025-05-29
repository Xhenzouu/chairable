document.addEventListener("DOMContentLoaded", () => {
    const productList = document.getElementById("productTableBody");
    const addProductBtn = document.getElementById("addProductBtn");
    const productModal = document.getElementById("productModal");
    const saveProductBtn = document.getElementById("saveProductBtn");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const productNameInput = document.getElementById("productName");
    const productPriceInput = document.getElementById("productPrice");
    const searchInput = document.getElementById("searchInput");
    const categoryFilter = document.getElementById("categoryFilter");
    let currentProductId = null;

    let products = []; // Initialize an empty array for products

    function renderProducts(filteredProducts) {
        productList.innerHTML = "";
        filteredProducts.forEach(product => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${product.id}</td>
                <td>${product.name}</td>
                <td>${product.price}</td>
                <td>
                    <img src="${product.imageUrl}" alt="${product.name}" class="thumbnail" onclick="toggleImage(event, '${product.imageUrl}')" />
                    <button class="edit-btn" data-id="${product.id}">Edit</button>
                    <button class="delete-btn" data-id="${product.id}">Delete</button>
                </td>
                <td>
                    <img id="fullImage-${product.id}" class="full-image" style="display: none;" />
                </td>
            `;
            productList.appendChild(row);
        });
    }

    // Function to toggle full-size image display
    window.toggleImage = function(event, imageUrl) {
        const fullImage = document.getElementById(`fullImage-${event.target.parentElement.parentElement.firstElementChild.innerText}`);
        if (fullImage.style.display === 'none' || fullImage.style.display === '') {
            fullImage.style.display = 'block';
            fullImage.src = imageUrl;
            fullImage.onclick = function () {
                fullImage.style.display = 'none';
            };
        } else {
            fullImage.style.display = 'none';
        }
    };

    // Function to filter products based on search input and category
    function filterProducts() {
        const searchValue = searchInput.value.toLowerCase();
        const selectedCategory = categoryFilter.value;

        const filteredProducts = products.filter(product => {
            const matchesSearch = product.name.toLowerCase().includes(searchValue);
            const matchesCategory = selectedCategory ? product.category === selectedCategory : true;
            return matchesSearch && matchesCategory;
        });

        renderProducts(filteredProducts);
    }

    // Function to fetch products from backend (pseudo-code)
    function fetchProducts() {
        // Example fetch request - replace with your actual endpoint
        fetch('/api/products')
            .then(response => response.json())
            .then(data => {
                products = data; // Assume data is an array of product objects
                renderProducts(products); // Initially render all products
            })
            .catch(error => console.error('Error fetching products:', error));
    }

    // Add event listeners for search input and category filter
    searchInput.addEventListener("input", filterProducts);
    categoryFilter.addEventListener("change", filterProducts);

    // Call fetchProducts to load products on page load
    fetchProducts();
});
