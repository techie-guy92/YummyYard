(function ($) {
    $(document).ready(function () {
        function calculateDeliveryCost() {
            const deliveryMethod = $("select[name='delivery_method']").val();
            const deliveryCost = $(".field-delivery_cost .readonly");

            if (deliveryMethod === "normal") {
                deliveryCost.text(35000);
            } else if (deliveryMethod === "fast") {
                deliveryCost.text(50000);
            } else if (deliveryMethod === "postal") {
                deliveryCost.text(20000);
            }
        }

        $("select[name='delivery_method']").change(calculateDeliveryCost);

        calculateDeliveryCost();
    });
})(django.jQuery);
