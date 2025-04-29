document.addEventListener("DOMContentLoaded", function() {
    const passwordInput = document.getElementById("password");
    const confirmPasswordInput = document.getElementById("confirm_password");
    const passwordHelp = document.getElementById("passwordHelp");
    const confirmPasswordHelp = document.getElementById("confirmPasswordHelp");
    const emailInput = document.getElementById("email");
    const emailHelp = document.getElementById("emailHelp");
    const form = document.getElementById("signupForm");

    // Password requirements
    const requirements = [
        { text: "At least 6 characters", test: pw => pw.length >= 6 },
        { text: "At least one uppercase letter", test: pw => /[A-Z]/.test(pw) },
        { text: "At least one number", test: pw => /[0-9]/.test(pw) },
        { text: "At least one special character", test: pw => /[^A-Za-z0-9]/.test(pw) }
    ];

    // Render the requirements list
    passwordHelp.innerHTML = `<ul id="pw-req-list" style="list-style: none; padding-left: 0; margin: 0;">
        ${requirements.map((r, i) => `<li id="pw-req-${i}" style="color: #b00;">${r.text}</li>`).join("")}
    </ul>`;

    function updateRequirements(pw) {
        requirements.forEach((req, i) => {
            const el = document.getElementById(`pw-req-${i}`);
            if (req.test(pw)) {
                el.style.color = "green";
            } else {
                el.style.color = "#b00";
            }
        });
    }

    function validateConfirmPassword() {
        if (confirmPasswordInput.value === "") {
            confirmPasswordHelp.textContent = "";
            return false;
        }
        if (passwordInput.value !== confirmPasswordInput.value) {
            confirmPasswordHelp.textContent = "Passwords do not match.";
            confirmPasswordHelp.style.color = "#b00";
            return false;
        } else {
            confirmPasswordHelp.textContent = "Passwords match.";
            confirmPasswordHelp.style.color = "green";
            return true;
        }
    }

    function validateEmail() {
        const email = emailInput.value;
        // Simple email regex
        const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        if (!valid && email.length > 0) {
            emailHelp.textContent = "Please enter a valid email address.";
            emailHelp.style.color = "#b00";
            return false;
        } else {
            emailHelp.textContent = "";
            return true;
        }
    }

    passwordInput.addEventListener("input", function() {
        updateRequirements(passwordInput.value);
        validateConfirmPassword();
    });

    confirmPasswordInput.addEventListener("input", validateConfirmPassword);

    emailInput.addEventListener("input", validateEmail);

    form.addEventListener("submit", function(e) {
        const pw = passwordInput.value;
        const allValid = requirements.every(req => req.test(pw));
        const emailValid = validateEmail();
        const confirmValid = validateConfirmPassword();
        updateRequirements(pw);
        if (!allValid || !emailValid || !confirmValid) {
            e.preventDefault();
        }
    });

    // Initial state
    updateRequirements(passwordInput.value);
    validateEmail();
    validateConfirmPassword();
});