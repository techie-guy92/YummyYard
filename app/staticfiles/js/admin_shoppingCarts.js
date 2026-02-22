(function ($) {
    $(document).ready(function () {
        async function updateTotals() {
            const rows = $(".dynamic-CartItem_cart");
            const totalAmountField = $(".field-total_price .readonly");
            let totalAmount = 0;

            for (let index = 0; index < rows.length; index++) {
                const row = rows[index];
                const productField = $(row).find("select[name*='product']");
                const quantityField = $(row).find("input[name*='quantity']");
                const priceField = $(row).find(".field-price p");
                const grandTotalField = $(row).find(".field-grand_total p");
                const productId = productField.val();
                const quantity = quantityField.val();

                if (productId && quantity) {
                    try {
                        const numericQuantity = parseFloat(quantity);
                        if (isNaN(numericQuantity) || numericQuantity <= 0) {
                            console.error("Invalid quantity:", quantity);
                            continue;
                        }
                        const response = await fetch(`/products/get_product_price/${productId}/`);
                        const data = await response.json();

                        if (data.error) {
                            console.error(data.error);
                        } else {
                            const price = parseFloat(data.price);
                            if (isNaN(price)) {
                                console.error("Invalid price:", data.price);
                                continue;
                            }
                            const grandTotal = price * numericQuantity;
                            if (grandTotalField.length) {
                                grandTotalField.text(grandTotal);
                            }
                            if (priceField.length) {
                                priceField.text(price);
                            }
                            totalAmount += grandTotal;
                        }
                    } catch (error) {
                        console.error(`Error fetching price for product ${productId}:`, error);
                    }
                }
            }
            if (totalAmountField.length) {
                totalAmountField.text(totalAmount);
            }
        }
        $(".inline-group").on("change", "select[name*='product'], input[name*='quantity']", updateTotals);
        $(".inline-group").on("input", "input[name*='quantity']", updateTotals);
        updateTotals();
    });
})(django.jQuery);


// ==========================================================================================================

// (function ($) {
//     $(document).ready(function () {
//         async function updateTotals() {
//             const rows = $(".dynamic-CartItem_cart");
//             const totalAmountField = $(".field-total_price .readonly");
//             let totalAmount = 0;

//             for (let index = 0; index < rows.length; index++) {
//                 const row = rows[index];
//                 const productField = $(row).find("select[name*='product']");
//                 const quantityField = $(row).find("input[name*='quantity']");
//                 const priceField = $(row).find(".field-price p");
//                 const grandTotalField = $(row).find(".field-grand_total p");

//                 const productId = productField.val();
//                 const quantity = quantityField.val();

//                 if (productId && quantity) {
//                     try {
//                         const response = await fetch(`/main/get_product_price/${productId}/`);
//                         const data = await response.json();

//                         if (data.error) {
//                             console.error(data.error);
//                         } else {
//                             const price = data.price;
//                             const grandTotal = price * quantity;

//                             // Update grand total for the current row
//                             if (grandTotalField.length) {
//                                 grandTotalField.text(grandTotal);
//                             }

//                             // Update price if applicable
//                             if (priceField.length) {
//                                 priceField.text(price);
//                             }

//                             // Add to total amount
//                             totalAmount += grandTotal;
//                         }
//                     } catch (error) {
//                         console.error(`Error fetching price for product ${productId}:`, error);
//                     }
//                 }
//             }

//             // Update total price field
//             if (totalAmountField.length) {
//                 totalAmountField.text(totalAmount);
//             }
//         }

//         // Attach event listeners to dynamically update totals
//         $(".inline-group").on("change", "select[name*='product'], input[name*='quantity']", updateTotals);
//         $(".inline-group").on("input", "input[name*='quantity']", updateTotals);

//         // Trigger totals update on page load
//         updateTotals();
//     });
// })(django.jQuery);