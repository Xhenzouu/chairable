document.addEventListener('DOMContentLoaded', function() {
    const paginationContainer = document.querySelector('.pagination');
    const pageItems = paginationContainer.querySelectorAll('.page-item');
    const prevButton = paginationContainer.querySelector('.page-item:first-child');
    const nextButton = paginationContainer.querySelector('.page-item:last-child');

    let currentPage = 1;
    const totalPages = pageItems.length - 2; // Subtract 2 for prev and next buttons

    function updatePagination() {
        // Update active state
        pageItems.forEach((item, index) => {
            if (index === 0 || index === pageItems.length - 1) return; // Skip prev and next buttons
            if (index === currentPage) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Update prev and next button states
        prevButton.classList.toggle('disabled', currentPage === 1);
        nextButton.classList.toggle('disabled', currentPage === totalPages);

        // Update URLs
        prevButton.querySelector('.page-link').href = `?page=${currentPage - 1}`;
        nextButton.querySelector('.page-link').href = `?page=${currentPage + 1}`;
    }

    function handlePageClick(e) {
        e.preventDefault();
        const clickedItem = e.target.closest('.page-item');
        if (!clickedItem || clickedItem.classList.contains('disabled')) return;

        if (clickedItem === prevButton && currentPage > 1) {
            currentPage--;
        } else if (clickedItem === nextButton && currentPage < totalPages) {
            currentPage++;
        } else {
            const pageNum = parseInt(e.target.textContent);
            if (!isNaN(pageNum)) {
                currentPage = pageNum;
            }
        }

        updatePagination();
        loadPage(currentPage);
    }

    function loadPage(pageNumber) {
        // Here you would typically make an AJAX call to load new content
        console.log(`Loading page ${pageNumber}`);
        // For now, we'll just update the URL
        window.history.pushState({page: pageNumber}, '', `?page=${pageNumber}`);
    }

    // Add click event listener to pagination container
    paginationContainer.addEventListener('click', handlePageClick);

    // Initialize pagination
    updatePagination();

    // Check if there's a page number in the URL on load
    const urlParams = new URLSearchParams(window.location.search);
    const pageParam = urlParams.get('page');
    if (pageParam) {
        currentPage = parseInt(pageParam);
        if (currentPage < 1 || currentPage > totalPages) {
            currentPage = 1;
        }
        updatePagination();
    }
});