(function ($) {
    $(document).ready(function () {
        let firstNameInput = $("#id_first_name");
        let lastNameInput = $("#id_last_name");
        let usernameInput = $("#id_username");

        function updateUsername() {
            let firstName = firstNameInput.val().toLowerCase().trim();
            let lastName = lastNameInput.val().toLowerCase().trim();
            usernameInput.val(`${firstName}_${lastName}`);
        }
        firstNameInput.on("input", updateUsername);
        lastNameInput.on("input", updateUsername);
    });
})(django.jQuery);