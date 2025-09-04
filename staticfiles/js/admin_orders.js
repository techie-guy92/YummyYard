(function ($) {
    $(document).ready(function () {
        async function updateTotalAmount() {
            const shoppingCart = $("#id_shopping_cart").val();
            const deliverySchedule = $("#id_delivery_schedule").val();
            const totalAmountInput = $(".readonly");

            if (!shoppingCart) {
                totalAmountInput.text("");
                return;
            }

            try {
                const response = await fetch(`/products/get_cart_price/${shoppingCart}/`);
                const data = await response.json();
                if (response.ok) {
                    let totalAmount = data["total_amount"];
                    totalAmountInput.text(totalAmount.toLocaleString());
                } else {
                    console.error(data.error || "Failed to fetch cart price.");
                    totalAmountInput.text("");
                }
            } catch (error) {
                console.error("Error fetching cart price:", error);
                totalAmountInput.text("");
            }
        }
        $("#id_shopping_cart, #id_delivery_schedule").on("change", updateTotalAmount);
        updateTotalAmount();
    });
})(django.jQuery);