(function ($) {
    $(document).ready(function () {
        async function updateAmountPayable() {
            const order = $("#id_order").val();
            const amount_payable = $(".readonly");

            if (!order) {
                amount_payable.text("");
                return;
            }

            try {
                const response = await fetch(`/products/get_amount_payable/${order}/`);
                const data = await response.json();
                if (response.ok) {
                    let amountPayable = data["amount_payable"];
                    amount_payable.text(amountPayable.toLocaleString());
                } else {
                    console.error(data.error || "Failed to fetch amount payable.");
                    amount_payable.text("");
                }
            } catch (error) {
                console.error("Error fetching amount payable:", error);
                amount_payable.text("");
            }
        }
        $("#id_order").on("change", updateAmountPayable);
        updateAmountPayable();
    });
})(django.jQuery);