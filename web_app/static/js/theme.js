// Theme switching functionality
function setTheme(theme) {
    const body = document.body;
    const themeSelect = document.getElementById('themeSelect');

    // Remove existing theme classes
    body.classList.remove('high-contrast');
    body.classList.remove('light');

    // Add new theme class if needed
    if (theme === 'high-contrast') {
        body.classList.add('high-contrast');
    } else if (theme === 'light') {
        body.classList.add('light');
    }

    // Update dropdown selection if it exists
    if (themeSelect) {
        themeSelect.value = theme;
    }

    // Save preference to localStorage
    localStorage.setItem('theme', theme);
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
}

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', loadTheme);
