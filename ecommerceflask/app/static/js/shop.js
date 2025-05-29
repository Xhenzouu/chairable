document.getElementById('applyFilters').addEventListener('click', function() {
    const category = document.getElementById('category').value;
    const view = document.getElementById('view').value;
    const sort = document.getElementById('sort').value;
    const show = document.getElementById('show').value;

    const products = document.querySelectorAll('.product');
    
    products.forEach(product => {
        if (category === 'all' || product.querySelector('.description').textContent.includes(category)) {
            product.style.display = 'block';
        } else {
            product.style.display = 'none';
        }
    });

    const productGrid = document.querySelector('.product-grid');
    if (view === 'list') {
        productGrid.classList.add('list-view');
    } else {
        productGrid.classList.remove('list-view');
    }

    const sortedProducts = Array.from(products).sort((a, b) => {
        const priceA = parseFloat(a.querySelector('p').textContent.replace('$', ''));
        const priceB = parseFloat(b.querySelector('p').textContent.replace('$', ''));
        
        return sort === 'low-to-high' ? priceA - priceB : priceB - priceA;
    });

    sortedProducts.forEach(product => {
        productGrid.appendChild(product);
    });

    products.forEach((product, index) => {
        if (index < show) {
            product.style.display = 'block';
        } else {
            product.style.display = 'none';
        }
    });
});
