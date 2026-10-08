/**
 * Django Student Management System - Main JavaScript
 * Static file: static/js/main.js
 * Vanilla JavaScript (No frameworks, No external JS dependencies)
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Sidebar Toggle (Mobile and Desktop)
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.app-sidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('active');
            if (sidebarBackdrop) {
                sidebarBackdrop.classList.toggle('active');
            }
        });
    }

    if (sidebarBackdrop && sidebar) {
        sidebarBackdrop.addEventListener('click', function () {
            sidebar.classList.remove('active');
            sidebarBackdrop.classList.remove('active');
        });
    }

    // 2. User Dropdown Menu
    const userDropdownBtn = document.getElementById('userDropdownBtn');
    const userDropdownMenu = document.getElementById('userDropdownMenu');

    if (userDropdownBtn && userDropdownMenu) {
        userDropdownBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            userDropdownMenu.classList.toggle('active');
        });

        document.addEventListener('click', function (e) {
            if (!userDropdownBtn.contains(e.target)) {
                userDropdownMenu.classList.remove('active');
            }
        });
    }

    // 3. Django Message / Alert Dismiss
    const dismissBtns = document.querySelectorAll('.alert-dismiss');
    dismissBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const alert = btn.closest('.alert');
            if (alert) {
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-6px)';
                alert.style.transition = 'all 150ms ease';
                setTimeout(function () {
                    alert.remove();
                }, 150);
            }
        });
    });

    // 4. Modals Controller
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    const genericModal = document.getElementById('genericModal');
    const genericModalTitle = document.getElementById('genericModalTitle');
    const genericModalMessage = document.getElementById('genericModalMessage');
    const genericModalConfirmBtn = document.getElementById('genericModalConfirmBtn');
    let pendingModalForm = null;

    modalTriggers.forEach(function (trigger) {
        trigger.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = trigger.getAttribute('data-modal-target');
            const targetModal = document.getElementById(targetId);
            if (targetModal) {
                pendingModalForm = trigger.getAttribute('data-modal-confirm-form');
                if (genericModalTitle && trigger.dataset.modalTitle) {
                    genericModalTitle.textContent = trigger.dataset.modalTitle;
                }
                if (genericModalMessage && trigger.dataset.modalMessage) {
                    genericModalMessage.textContent = trigger.dataset.modalMessage;
                }
                targetModal.classList.add('active');
                targetModal.setAttribute('aria-hidden', 'false');
            }
        });
    });

    if (genericModalConfirmBtn) {
        genericModalConfirmBtn.addEventListener('click', function () {
            if (!pendingModalForm) return;
            const form = document.getElementById(pendingModalForm);
            if (form) {
                form.submit();
            }
        });
    }

    const modalCloseButtons = document.querySelectorAll('[data-modal-close]');
    modalCloseButtons.forEach(function (closeBtn) {
        closeBtn.addEventListener('click', function () {
            const modal = closeBtn.closest('.modal-backdrop');
            if (modal) {
                modal.classList.remove('active');
                modal.setAttribute('aria-hidden', 'true');
                pendingModalForm = null;
            }
        });
    });

    // Close modal on backdrop click
    const modalBackdrops = document.querySelectorAll('.modal-backdrop');
    modalBackdrops.forEach(function (backdrop) {
        backdrop.addEventListener('click', function (e) {
            if (e.target === backdrop) {
                backdrop.classList.remove('active');
                backdrop.setAttribute('aria-hidden', 'true');
                pendingModalForm = null;
            }
        });
    });

    // Escape key closes modals and dropdowns
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            modalBackdrops.forEach(function (m) {
                m.classList.remove('active');
                m.setAttribute('aria-hidden', 'true');
            });
            pendingModalForm = null;
            if (userDropdownMenu) userDropdownMenu.classList.remove('active');
            if (sidebar) sidebar.classList.remove('active');
            if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
        }
    });

});
