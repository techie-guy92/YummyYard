(function ($) {
    $(document).ready(function () {
        async function updateTotalAmount() {
            const shoppingCart = $("#id_shopping_cart").val();
            const deliverySchedule = $("#id_delivery_schedule").val();
            const totalAmountInput = $("#id_total_amount");

            if (!shoppingCart || !deliverySchedule) {
                totalAmountInput.val("");
                return;
            }

            try {
                const response = await fetch(`/main/get_cart_price/${shoppingCart}/`);
                const data = await response.json();
                if (response.ok) {
                    let totalAmount = data["total_amount"];

                    if (deliverySchedule === "normal") {
                        totalAmount += 35000;
                    } else if (deliverySchedule === "fast") {
                        totalAmount += 50000;
                    } else if (deliverySchedule === "postal") {
                        totalAmount += 20000;
                    }
                    totalAmountInput.val(totalAmount);
                } else {
                    console.error(data.error || "Failed to fetch cart price.");
                    totalAmountInput.val("");
                }
            } catch (error) {
                console.error("Error fetching cart price:", error);
                totalAmountInput.val("");
            }
        }
        $("#id_shopping_cart, #id_delivery_schedule").on("change", updateTotalAmount);
        updateTotalAmount();
    });
})(django.jQuery);
