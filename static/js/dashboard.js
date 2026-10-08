/**
 * Django Student Management System - Dashboard JavaScript
 * Static file: static/js/dashboard.js
 * Vanilla JavaScript UI enhancements for dashboard statistics & overview
 */

document.addEventListener('DOMContentLoaded', function () {
    // Session quick switcher simulation / notification
    const sessionBadges = document.querySelectorAll('.badge-session-interactive');
    sessionBadges.forEach(function (badge) {
        badge.addEventListener('click', function () {
            const sessionName = badge.dataset.session;
            console.log('Selected academic session: ' + sessionName);
        });
    });

    // Animate capacity progress bars smoothly on load
    const progressBars = document.querySelectorAll('.capacity-bar');
    progressBars.forEach(function (bar) {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(function () {
            bar.style.transition = 'width 600ms cubic-bezier(0.16, 1, 0.3, 1)';
            bar.style.width = width;
        }, 100);
    });
});
