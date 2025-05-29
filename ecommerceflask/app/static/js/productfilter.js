document.addEventListener("DOMContentLoaded", function() {
    const categoryFilter = document.getElementById("categoryFilter");
    const subcategoryFilter = document.getElementById("subcategoryFilter");
    const searchInput = document.getElementById("searchInput");
    const productRows = document.querySelectorAll("tbody tr");

    // Function to filter products
    function filterProducts() {
        const selectedCategory = categoryFilter.value; // Get the selected category name
        const selectedSubcategory = subcategoryFilter.value; // Get the selected subcategory
        const searchTerm = searchInput.value.toLowerCase(); // Get the search term

        productRows.forEach(row => {
            const productName = row.cells[1].textContent.toLowerCase(); // Assuming Name is in the second column
            const productCategory = row.cells[7].textContent; // Assuming Category is in the seventh column (should be the name)
            const productSubcategory = row.cells[8].textContent; // Assuming Subcategory is in the eighth column

            // Check if the product matches the selected filters
            const matchesCategory = selectedCategory === "" || productCategory === selectedCategory;
            const matchesSubcategory = selectedSubcategory === "" || productSubcategory === selectedSubcategory;
            const matchesSearch = productName.includes(searchTerm);

            // Show or hide the row based on the filters
            if (matchesCategory && matchesSubcategory && matchesSearch) {
                row.style.display = ""; // Show the row
            } else {
                row.style.display = "none"; // Hide the row
            }
        });
    }

    // Event listeners for filters
    categoryFilter.addEventListener("change", filterProducts);
    subcategoryFilter.addEventListener("change", filterProducts);
    searchInput.addEventListener("input", filterProducts);
});