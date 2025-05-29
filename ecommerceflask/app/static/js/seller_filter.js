document.addEventListener('DOMContentLoaded', function () {
    const filterButton = document.querySelector('.filter-button:nth-of-type(1)');
    const exportButton = document.querySelector('.filter-button:nth-of-type(2)');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');

    // Handle Filter Button Click
    if (filterButton) {
        filterButton.addEventListener('click', function () {
            const startDate = startDateInput.value;
            const endDate = endDateInput.value;

            if (!startDate || !endDate) {
                alert('Please select both start and end dates to filter.');
                return;
            }

            fetch('/dashboard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ start_date: startDate, end_date: endDate }),
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then((html) => {
                    document.body.innerHTML = html;
                })
                .catch((error) => {
                    console.error('Error with the request:', error);
                    alert('An error occurred while filtering data.');
                });
        });
    }

    // Handle Export Report Button Click
    if (exportButton) {
        exportButton.addEventListener('click', function () {
            const startDate = startDateInput.value;
            const endDate = endDateInput.value;

            if (!startDate || !endDate) {
                alert('Please select both start and end dates to export the report.');
                return;
            }

            const exportUrl = `/dashboard/export_report?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`;
            window.location.href = exportUrl;
        });
    }
});
