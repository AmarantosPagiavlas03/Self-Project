document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('register-form');

    form.addEventListener('submit', function (event) {
        event.preventDefault(); // prevent form submission

        // clear previous errors
        clearErrors();

        // validate fields
        let isValid = true;

        const firstName = document.getElementById('id_first_name');
        if (!firstName.value.trim()) {
            showError('first_name_error', 'Please enter your first name.');
            isValid = false;
        }

        const lastName = document.getElementById('id_last_name');
        if (!lastName.value.trim()) {
            showError('last_name_error', 'Please enter your last name.');
            isValid = false;
        }

        const email = document.getElementById('id_email');
        if (!email.value.trim()) {
            showError('email_error', 'Please enter your email address.');
            isValid = false;
        } else if (!validateEmail(email.value)) {
            showError('email_error', 'Please enter a valid email address.');
            isValid = false;
        }

        const role = document.getElementById('id_role');
        if (!role.value) {
            showError('role_error', 'Please select a role.');
            isValid = false;
        }

        // password
        const password1 = document.getElementById('id_password1');
        if (!password1.value.trim()) {
            showError('password1_error', 'Please enter a password.');
            isValid = false;
        }

        const password2 = document.getElementById('id_password2');
        if (!password2.value.trim()) {
            showError('password2_error', 'Please confirm your password.');
            isValid = false;
        } else if (password1.value !== password2.value) {
            showError('password2_error', 'Passwords do not match.');
            isValid = false;
        }

        // if all fields valid, submit the form
        if (isValid) {
            form.submit();
        }
    });

    /**
     * displays an error message for a specific field
     * the ID of the error message element
     * the error message to display
     */
    function showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        errorElement.textContent = message;
        errorElement.style.display = 'block'; 
        const inputElement = errorElement.previousElementSibling;
        inputElement.classList.add('is-invalid'); 
    }

    function clearErrors() {
        const errorElements = document.querySelectorAll('.invalid-feedback');
        errorElements.forEach(function (element) {
            element.style.display = 'none'; // hide all error messages
        });

        const inputElements = document.querySelectorAll('.form-control');
        inputElements.forEach(function (element) {
            element.classList.remove('is-invalid'); 
        });

        document.getElementById('non_field_errors').style.display = 'none'; 
    }

    /**
     * validates an email address using a regular expression
     * the email address to validate
     * true if the email is valid, otherwise false
     */
    function validateEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }
});