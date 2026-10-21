/**
 * Django Student Management System - Forms JavaScript
 * Static file: static/js/forms.js
 * Vanilla JavaScript form helpers:
 * - Dynamic dependent dropdowns (Class -> Section / Class -> Subject)
 * - Image file preview for student avatar
 * - Client-side form field validation
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Image Preview for Student Photo
    const imageInput = document.getElementById('id_image');
    const avatarPreview = document.getElementById('avatarPreview');

    if (imageInput && avatarPreview) {
        imageInput.addEventListener('change', function (e) {
            const file = e.target.files && e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (event) {
                    avatarPreview.src = event.target.result;
                    avatarPreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 2. Class to Section / Subject Dependent Dropdown Demonstration
    const classSelect = document.getElementById('id_class');
    const sectionSelect = document.getElementById('id_section');
    const subjectSelect = document.getElementById('id_class_subject');

    if (classSelect && (sectionSelect || subjectSelect)) {
        classSelect.addEventListener('change', function () {
            const selectedClassId = classSelect.value;
            // Example client-side feedback for dynamic loading
            if (sectionSelect) {
                const options = sectionSelect.querySelectorAll('option[data-class-id]');
                if (options.length > 0) {
                    let hasMatch = false;
                    options.forEach(function (opt) {
                        if (!selectedClassId || opt.getAttribute('data-class-id') === selectedClassId) {
                            opt.style.display = '';
                            if (!hasMatch) {
                                opt.selected = true;
                                hasMatch = true;
                            }
                        } else {
                            opt.style.display = 'none';
                        }
                    });
                }
            }
        });
    }

    // 3. Basic Client-Side Form Validation UI
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            let isValid = true;
            const requiredInputs = form.querySelectorAll('[required]');

            requiredInputs.forEach(function (input) {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
        });
    });
});
