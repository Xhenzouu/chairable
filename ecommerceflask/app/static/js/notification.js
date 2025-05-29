document.addEventListener('DOMContentLoaded', function() {
    const notificationIcon = document.getElementById('notification-icon');
    const notificationPopover = document.getElementById('notification-popover');
    const deleteSelectedBtn = document.getElementById('delete-button'); // Corrected ID

    // Function to show the notification popover
    function showPopover() {
        notificationPopover.style.visibility = 'visible';
        notificationPopover.style.opacity = '1';
        updateDeleteButtonVisibility(); // Update delete button visibility
    }

    // Function to hide the notification popover
    function hidePopover() {
        notificationPopover.style.visibility = 'hidden';
        notificationPopover.style.opacity = '0';
    }

    // Event listener for the notification icon click
    notificationIcon.addEventListener('click', function(event) {
        event.preventDefault(); // Prevent default action of the anchor tag
        const isVisible = notificationPopover.style.visibility === 'visible';

        // Toggle visibility based on current state
        if (isVisible) {
            hidePopover();
        } else {
            showPopover();
        }
    });

    // Event listener for clicks outside the popover
    window.addEventListener('click', function(event) {
        // Check if the click was outside the notification popover and the notification icon
        if (!notificationPopover.contains(event.target) && !notificationIcon.contains(event.target)) {
            hidePopover();
        }
    });

    // Update delete button visibility based on checkbox selection
    function updateDeleteButtonVisibility() {
        const checkboxes = document.querySelectorAll('.notification-checkbox');
        const anyChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);
        console.log("Any checked:", anyChecked); // Debug log
        deleteSelectedBtn.style.display = anyChecked ? 'block' : 'none'; // Show or hide the button
    }

    // Add event listener to checkboxes
    document.querySelectorAll('.notification-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateDeleteButtonVisibility);
    });

    // Delete selected notifications
    deleteSelectedBtn.addEventListener('click', function() {
        const selectedIds = Array.from(document.querySelectorAll('.notification-checkbox:checked'))
            .map(checkbox => checkbox.getAttribute('data-id'));

        if (selectedIds.length > 0) {
            // Send a request to delete notifications
            fetch('/notifications/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ids: selectedIds }),
            })
            .then(response => {
                if (response.ok) {
                    // Optionally, refresh the notifications or remove them from the DOM
                    selectedIds.forEach(id => {
                        const checkbox = document.querySelector(`.notification-checkbox[data-id="${id}"]`);
                        if (checkbox) {
                            checkbox.closest('li').remove(); // Remove the notification from the DOM
                        }
                    });
                    updateDeleteButtonVisibility(); // Update the delete button visibility
                } else {
                    alert('Error deleting notifications. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while deleting notifications.');
            });
        }
    });
});