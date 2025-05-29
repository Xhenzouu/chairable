document.addEventListener('DOMContentLoaded', () => {
    const showMoreButton = document.getElementById('showMoreButton');
    const hiddenProducts = document.querySelectorAll('.product.hidden');
    let isExpanded = false;

    showMoreButton.addEventListener('click', (event) => {
        event.preventDefault();

        if (isExpanded) {
            hiddenProducts.forEach(product => {
                product.classList.add('hidden');
            });
            showMoreButton.textContent = 'Show More';
        } else {
            hiddenProducts.forEach(product => {
                product.classList.remove('hidden');
            });
            showMoreButton.textContent = 'Show Less';
        }

        isExpanded = !isExpanded;
    });
});
