import React, { useState } from "react";
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";
import type { CreateOrderActions, OnApproveActions } from "@paypal/paypal-js";

// Renders errors or successfull transactions on the screen.
function Message({ content }: { content: string | null }) {
    return <p>{content}</p>;
}

const PayPal = () => {
    console.info("Initializing PayPal component.");

    const [message, setMessage] = useState("");
    const initialOptions = {
        "clientId": import.meta.env.VITE_PAYPAL_CLIENT_ID as string,
        "enable-funding": "venmo",
        "disable-funding": "",
        "buyer-country": "US",
        currency: "USD",
        "data-page-type": "product-details",
        components: "buttons",
        "data-sdk-integration-source": "developer-studio",
    };

    return (
        <div>
            <PayPalScriptProvider options={initialOptions}>
                <PayPalButtons
                    style={{
                        shape: "pill",
                        layout: "vertical",
                        color: "gold",
                        label: "paypal",
                    }}
                    createOrder={async (_data, actions: CreateOrderActions) => {
                        console.info("createOrder triggered.");
                        try {
                            const response = await fetch("/api/orders", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json",
                                },
                                // use the "body" param to optionally pass additional order information
                                // like product ids and quantities
                                body: JSON.stringify({
                                    cart: [
                                        {
                                            id: "YOUR_PRODUCT_ID",
                                            quantity: "YOUR_PRODUCT_QUANTITY",
                                        },
                                    ],
                                }),
                            });

                            const orderData = await response.json();
                            console.debug("Received order data:", orderData);

                            if (orderData.id) {
                                console.info("PayPal order created successfully. ID:", orderData.id);
                                return orderData.id;
                            } else {
                                const errorDetail = orderData?.details?.[0];
                                const errorMessage = errorDetail
                                    ? `${errorDetail.issue} ${errorDetail.description} (${orderData.debug_id})`
                                    : JSON.stringify(orderData);

                                console.error("Error creating PayPal order:", errorMessage);
                                throw new Error(errorMessage);
                            }
                        } catch (error) {
                            console.error("Could not initiate PayPal Checkout. An exception occurred:", error);
                            setMessage(
                                `Could not initiate PayPal Checkout...${error}`
                            );
                            throw error;
                        }
                    }}
                    onApprove={async (data, actions: OnApproveActions) => {
                        console.info("onApprove triggered. Capturing order with ID:", data.orderID);
                        try {
                            const response = await fetch(
                                `/api/orders/${data.orderID}/capture`,
                                {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json",
                                    },
                                }
                            );

                            const orderData = await response.json();
                            console.debug("Received capture data:", orderData);

                            const errorDetail = orderData?.details?.[0];

                            if (errorDetail?.issue === "INSTRUMENT_DECLINED") {
                                console.warn("Payment was declined. Restarting transaction.");
                                return actions.restart();
                            } else if (errorDetail) {
                                console.error("Non-recoverable error during PayPal capture:", errorDetail);
                                throw new Error(
                                    `${errorDetail.description} (${orderData.debug_id})`
                                );
                            } else {
                                const transaction =
                                    orderData.purchase_units[0].payments
                                        .captures[0];
                                console.info("PayPal transaction successful. Status:", transaction.status, "ID:", transaction.id);
                                setMessage(
                                    `Transaction ${transaction.status}: ${transaction.id}. See console for all available details`
                                );
                            }
                        } catch (error) {
                            console.error("An error occurred during PayPal capture:", error);
                            setMessage(
                                `Sorry, your transaction could not be processed...${error}`
                            );
                        }
                    }}
                />
            </PayPalScriptProvider>
            <Message content={message} />
        </div>
    );
};

export default PayPal;