/**
 * Django Student Management System - Tables JavaScript
 * Static file: static/js/tables.js
 * Vanilla JavaScript UI enhancements:
 * - Client-side table search filter
 * - Status filter
 * - Select-all checkboxes
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Client-Side Live Search for Tables
    const tableSearchInputs = document.querySelectorAll('[data-table-search]');
    tableSearchInputs.forEach(function (input) {
        const tableId = input.getAttribute('data-table-search');
        const table = document.getElementById(tableId);
        if (!table) return;

        input.addEventListener('input', function () {
            const query = input.value.toLowerCase().trim();
            const rows = table.querySelectorAll('tbody tr');
            let visibleCount = 0;

            rows.forEach(function (row) {
                // If it's an empty state row, skip
                if (row.classList.contains('empty-row')) return;

                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // Toggle empty state if present
            const emptyState = document.getElementById(tableId + '_empty');
            if (emptyState) {
                emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
            }
        });
    });

    // 2. Status Dropdown Filter
    const statusFilters = document.querySelectorAll('[data-status-filter]');
    statusFilters.forEach(function (select) {
        const tableId = select.getAttribute('data-status-filter');
        const table = document.getElementById(tableId);
        if (!table) return;

        select.addEventListener('change', function () {
            const filterValue = select.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(function (row) {
                if (row.classList.contains('empty-row')) return;
                const statusCell = row.querySelector('[data-status]');
                if (!statusCell) return;

                const status = statusCell.getAttribute('data-status').toLowerCase();
                if (!filterValue || status === filterValue) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });

    // 3. Select All Checkboxes
    const selectAllCheckboxes = document.querySelectorAll('[data-select-all]');
    selectAllCheckboxes.forEach(function (selectAll) {
        const targetClass = selectAll.getAttribute('data-select-all');
        const checkboxes = document.querySelectorAll('.' + targetClass);

        selectAll.addEventListener('change', function () {
            checkboxes.forEach(function (cb) {
                cb.checked = selectAll.checked;
            });
        });
    });
});
