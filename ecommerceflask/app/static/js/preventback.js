function confirmLogout() {
    if (confirm("Are you sure you want to log out?")) {
        window.location.href = "/logout"; 
        setTimeout(() => {
            window.history.forward();
        }, 0);
    }
}

window.history.pushState(null, document.title, window.location.href);
window.addEventListener('popstate', function(event) {
    window.history.pushState(null, document.title, window.location.href);
});
