document.addEventListener('DOMContentLoaded', function() {
    // Define valid status transitions
    const validStatusTransitions = {
        'PENDING': ['PENDING', 'APPROVED', 'CANCELLED'],
        'APPROVED': ['APPROVED', 'SHIPPED', 'CANCELLED'],
        'SHIPPED': ['SHIPPED', 'IN_TRANSIT'],
        'IN_TRANSIT': ['IN_TRANSIT'],
        'DELIVERED': ['DELIVERED'],
        'CANCELLED': ['CANCELLED']
    };

    // Initialize dropdowns to enforce valid transitions
    document.querySelectorAll('.order-status-select').forEach(select => {
        const orderId = select.dataset.orderId;
        const currentStatus = select.value;

        // Disable options that are not valid transitions
        Array.from(select.options).forEach(option => {
            const isValid = validStatusTransitions[currentStatus].includes(option.value);
            option.disabled = !isValid;
        });

        // Handle status change
        select.addEventListener('change', function() {
            const newStatus = this.value;
            const etaInput = this.closest('tr').querySelector('.eta-input');
            const statusMessage = this.closest('tr').querySelector('.status-message');

            console.log(`Order ID: ${orderId}, New Status: ${newStatus}`);

            // Handle SHIPPED status (requires ETA)
            if (newStatus === 'SHIPPED') {
                etaInput.classList.remove('hidden');
                statusMessage.classList.add('hidden');

                $(`#eta-${orderId}`).daterangepicker({
                    minDate: moment(),
                    startDate: moment(),
                    endDate: moment().add(2, 'days'),
                    opens: 'left',
                    autoApply: false,
                    locale: {
                        format: 'MM/DD/YY',
                        separator: ' - ',
                        applyLabel: 'Set ETA',
                        cancelLabel: 'Cancel'
                    },
                    drops: 'down',
                    buttonClasses: 'btn',
                    applyButtonClasses: 'btn-primary',
                    cancelButtonClasses: 'btn-default'
                }, function(start, end) {
                    console.log(`ETA set for Order ID ${orderId}: ${start.format('YYYY-MM-DD')} - ${end.format('YYYY-MM-DD')}`);
                    updateOrderWithETA(orderId, start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD'), select);
                });

                setTimeout(() => {
                    $(`#eta-${orderId}`).data('daterangepicker').show();
                }, 100);
            } 
            // Handle IN_TRANSIT status
            else if (newStatus === 'IN_TRANSIT') {
                etaInput.classList.add('hidden');
                statusMessage.classList.remove('hidden');
                updateOrderStatusWithTransitDate(orderId, newStatus);
            } 
            // Handle other statuses
            else {
                etaInput.classList.add('hidden');
                statusMessage.classList.remove('hidden');
                updateOrderStatus(orderId, newStatus);
            }
        });
    });
});

function updateOrderStatusWithTransitDate(orderId, newStatus) {
    const transitDate = moment().format('YYYY-MM-DD');

    console.log(`Updating order ${orderId} to status: ${newStatus} on ${transitDate}`);
    console.log(`Payload being sent:`, {
        status: newStatus,
        in_transit_date: transitDate
    });

    fetch(`/update-order-status/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: newStatus,
            in_transit_date: transitDate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Failed to update order status: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the order status');
    });
}

function updateOrderWithETA(orderId, startDate, endDate, selectElement) {
    console.log(`Updating order ${orderId} with ETA: ${startDate} - ${endDate}`);
    fetch(`/update-order-eta/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            eta_start: startDate,
            eta_end: endDate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const statusMessage = selectElement.closest('tr').querySelector('.status-message');
            statusMessage.innerHTML = `
                Shipped on ${data.updated_shipped_date}<br>
                Expected delivery: ${startDate} - ${endDate}
            `;
            selectElement.value = 'SHIPPED';
            // Update disabled options for new status
            Array.from(selectElement.options).forEach(option => {
                const isValid = validStatusTransitions['SHIPPED'].includes(option.value);
                option.disabled = !isValid;
            });
        } else {
            alert('Failed to update ETA: ' + data.message);
            selectElement.value = selectElement.dataset.currentStatus || 'PENDING';
        } 
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the ETA');
        selectElement.value = selectElement.dataset.currentStatus || 'PENDING';
    });
}

function updateOrderStatus(orderId, newStatus) {
    console.log(`Updating order ${orderId} to status: ${newStatus}`);
    fetch(`/update-order-status/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Failed to update order status: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the order status');
    });
}