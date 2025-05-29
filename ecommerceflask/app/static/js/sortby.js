// Wait for the DOM to fully load
document.addEventListener("DOMContentLoaded", function() {
    const sortBySelect = document.getElementById("sort-by");
    const applyFiltersButton = document.getElementById("apply-filters");
    const filterForm = document.getElementById("filter-form");

    // Function to set the default value when the page loads
    function setDefault() {
        if (sortBySelect.value === "default") {
            sortBySelect.options[0].text = "Default"; // Ensure the default text is shown
        }
    }

    // Function to handle the change event for the dropdown
    sortBySelect.addEventListener("change", function() {
        const selectedOption = sortBySelect.options[sortBySelect.selectedIndex].value;

        // If "default" is selected, keep the text as "Default"
        if (selectedOption === "default") {
            sortBySelect.options[0].text = "Default"; // Set the default text
            sortBySelect.value = "default"; // Make sure the default is set
        } else {
            sortBySelect.options[0].text = "Default"; // Set a neutral text
        }
    });

    // Call setDefault on initial load
    setDefault();

    // Event listener for apply filters button
    applyFiltersButton.addEventListener("click", function() {
        // Get the current values from the filter options
        const searchValue = document.getElementById("search").value;
        const viewValue = document.getElementById("view").value;
        const sortByValue = sortBySelect.value; // Use the already defined sortBySelect
        const showValue = document.getElementById("show").value;

        // Log the current filter values
        console.log("Apply Filters button clicked");
        console.log("Search:", searchValue);
        console.log("View:", viewValue);
        console.log("Sort By:", sortByValue);
        console.log("Show:", showValue);

        // Add your filtering logic here
        // For example, you can filter products displayed based on these values
    });
});
