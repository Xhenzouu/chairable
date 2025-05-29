document.addEventListener("DOMContentLoaded", function () {
    const statusFilter = document.getElementById("statusFilter");
    const searchInput = document.getElementById("searchInput");

    // Select the container where orders are displayed
    const orderContainer = document.getElementById("orders"); 

    // Function to render the order list dynamically
    function renderOrders(orderList) {
        orderContainer.innerHTML = ""; // Clear current orders

        if (orderList.length === 0) {
            orderContainer.innerHTML = "<p>No orders found matching the criteria.</p>";
            return;
        }

        const ul = document.createElement("ul");
        ul.classList.add("orders-list");

        orderList.forEach(order => {
            const li = document.createElement("li");
            li.textContent = `Order ID: ${order.id}, Buyer: ${order.buyer}, Status: ${order.status}`;
            ul.appendChild(li);
        });

        orderContainer.appendChild(ul);
    }

    // Fetch orders from the server (Replace URL with your actual endpoint)
    async function fetchOrders() {
        try {
            const response = await fetch('/api/orders'); // This must match the Flask endpoint.
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            allOrders = data; 
            filterOrders(allOrders);
        } catch (error) {
            console.error("Failed to fetch orders:", error);
            orderContainer.innerHTML = "<p>Error loading orders.</p>";
        }
    }
    

    // Filter logic
    function filterOrders(orders) {
        const selectedStatus = statusFilter.value.toUpperCase();
        const searchTerm = searchInput.value.toLowerCase();

        const filteredOrders = orders.filter(order => {
            const matchesStatus = selectedStatus === "" || order.status === selectedStatus;
            const matchesSearch = 
                order.id.toLowerCase().includes(searchTerm) || 
                order.buyer.toLowerCase().includes(searchTerm);

            return matchesStatus && matchesSearch;
        });

        renderOrders(filteredOrders);
    }

    let allOrders = [];

    // Attach event listeners
    statusFilter.addEventListener("change", () => filterOrders(allOrders));
    searchInput.addEventListener("input", () => filterOrders(allOrders));

    // Fetch initial data
    fetchOrders().then(() => {
        filterOrders(allOrders);
    });

    async function initialize() {
        try {
            const response = await fetch('/api/orders');
            allOrders = await response.json();
            filterOrders(allOrders);
        } catch (error) {
            console.error("Error fetching orders for filtering:", error);
        }
    }

    initialize();
});
