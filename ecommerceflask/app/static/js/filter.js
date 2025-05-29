document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filter-form');
    const productGrid = document.querySelector('.product-grid');
    const originalProducts = Array.from(productGrid.children); // Store original product elements

    filterForm.addEventListener('input', function() {
        const searchValue = document.getElementById('search').value.toLowerCase();
        const categoryValue = document.getElementById('category').value; // Category value
        const subcategoryValue = document.getElementById('subcategory').value; // Subcategory value
        const sortByValue = document.getElementById('sort-by').value;

        // Filter products based on search input, category, and subcategory
        let filteredProducts = originalProducts.filter(product => {
            const productName = product.querySelector('h3').innerText.toLowerCase();
            const productCategory = product.dataset.category; // This holds the full category name
            const productSubcategory = product.dataset.subcategory; // This holds the subcategory name

            const matchesSearch = productName.includes(searchValue);
            const matchesCategory = categoryValue === '' || productCategory === categoryValue; // Matches against full category names
            const matchesSubcategory = subcategoryValue === '' || productSubcategory === subcategoryValue; // Matches against subcategory

            // Ensure that both category and subcategory conditions are satisfied
            return matchesSearch && matchesCategory && (subcategoryValue === '' || matchesSubcategory);
        });

        // Implement sorting based on sortByValue
        if (sortByValue === 'price-asc') {
            filteredProducts.sort((a, b) => {
                return parseFloat(a.querySelector('.price').innerText.replace(/[^0-9.-]+/g, "")) - 
                       parseFloat(b.querySelector('.price').innerText.replace(/[^0-9.-]+/g, ""));
            });
        } else if (sortByValue === 'price-desc') {
            filteredProducts.sort((a, b) => {
                return parseFloat(b.querySelector('.price').innerText.replace(/[^0-9.-]+/g, "")) - 
                       parseFloat(a.querySelector('.price').innerText.replace(/[^0-9.-]+/g, ""));
            });
        }

        // Clear the product grid and append filtered and sorted products
        productGrid.innerHTML = '';
        filteredProducts.forEach(product => productGrid.appendChild(product));

        // Optional: Handle case when no products are found
        if (filteredProducts.length === 0) {
            const noResultsMessage = document.createElement('p');
            noResultsMessage.textContent = ' No products found.';
            productGrid.appendChild(noResultsMessage);
        }
    });
});
