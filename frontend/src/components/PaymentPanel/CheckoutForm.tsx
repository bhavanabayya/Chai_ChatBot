// CheckoutForm.tsx



// TODO: Insert Stripe and PayPal here later







































// // CheckoutForm.tsx
// import React, { useState } from 'react';
// import { CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
// import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";
// // import type { CreateOrderActions, OnApproveActions } from "@paypal/react-paypal-js";
// import type { CreateOrderActions, OnApproveActions } from "@paypal/paypal-js";
// import { StripeCardElement, StripeElements, Stripe, PaymentIntent } from '@stripe/stripe-js';

// // Define the type for the Message component's props
// interface MessageProps {
//     content: string | null;
// }

// // Renders errors or successfull transactions on the screen.
// function Message({ content }: MessageProps) {
//     return <p>{content}</p>;
// }

// const CheckoutForm = () => {
//     const stripe: Stripe | null = useStripe();
//     const elements: StripeElements | null = useElements();
//     const [message, setMessage] = useState<string | null>(null);
//     const [isLoading, setIsLoading] = useState<boolean>(false);

//     const initialOptions = {
//         "clientId": import.meta.env.VITE_PAYPAL_CLIENT_ID as string,
//         "enable-funding": "venmo",
//         "buyer-country": "US",
//         currency: "USD",
//         components: "buttons",
//     };

//     const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
//         event.preventDefault();

//         if (!stripe || !elements) {
//             // Stripe.js has not yet loaded.
//             return;
//         }

//         setIsLoading(true);

//         // 1. Create a payment intent on your server
//         const response = await fetch('http://localhost:808/create-payment-intent', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ amount: 1099 }), // Example amount: $10.99
//         });

//         const { clientSecret, error: backendError } = await response.json();

//         if (backendError) {
//             setMessage(`Server error: ${backendError.message}`);
//             setIsLoading(false);
//             return;
//         }

//         const cardElement = elements.getElement(CardElement);
//         if (!cardElement) {
//             setMessage('Card element not found.');
//             setIsLoading(false);
//             return;
//         }

//         // 2. Confirm the card payment with Stripe
//         const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
//             payment_method: {
//                 card: cardElement as StripeCardElement,
//                 billing_details: {
//                     name: 'Jenny Rosen', // Example billing details
//                 },
//             },
//         });

//         if (stripeError) {
//             setMessage(stripeError.message ?? 'An unknown error occurred with Stripe.');
//         } else {
//             const pi = paymentIntent as PaymentIntent;
//             switch (pi.status) {
//                 case 'succeeded':
//                     setMessage('Payment succeeded! 🎉');
//                     // Fulfill the order, grant access, etc.
//                     break;
//                 case 'processing':
//                     setMessage('Your payment is processing.');
//                     break;
//                 case 'requires_payment_method':
//                     setMessage('Your payment was not successful, please try again.');
//                     break;
//                 default:
//                     setMessage('Something went wrong.');
//                     break;
//             }
//         }

//         setIsLoading(false);
//     };

//     return (
//         <div>
//             <form id="payment-form" onSubmit={handleSubmit}>
//                 <CardElement id="card-element" />
//                 <button disabled={isLoading || !stripe || !elements} id="submit">
//                     <span id="button-text">
//                         {isLoading ? <div className="spinner" id="spinner"></div> : 'Pay now'}
//                     </span>
//                 </button>
//                 {/* Show any error or success messages */}
//                 {message && <div id="payment-message">{message}</div>}
//             </form>

//             <div className="paypal-button-container">
//                 <PayPalScriptProvider options={initialOptions}>
//                     <PayPalButtons
//                         style={{
//                             shape: "pill",
//                             layout: "vertical",
//                             color: "gold",
//                             label: "paypal",
//                         }}
//                         createOrder={async (_data, actions: CreateOrderActions) => {
//                             try {
//                                 const response = await fetch("/api/orders", {
//                                     method: "POST",
//                                     headers: {
//                                         "Content-Type": "application/json",
//                                     },
//                                     // use the "body" param to optionally pass additional order information
//                                     // like product ids and quantities
//                                     body: JSON.stringify({
//                                         cart: [
//                                             {
//                                                 id: "YOUR_PRODUCT_ID",
//                                                 quantity: "YOUR_PRODUCT_QUANTITY",
//                                             },
//                                         ],
//                                     }),
//                                 });

//                                 const orderData = await response.json();

//                                 if (orderData.id) {
//                                     return orderData.id;
//                                 } else {
//                                     const errorDetail = orderData?.details?.[0];
//                                     const errorMessage = errorDetail
//                                         ? `${errorDetail.issue} ${errorDetail.description} (${orderData.debug_id})`
//                                         : JSON.stringify(orderData);

//                                     throw new Error(errorMessage);
//                                 }
//                             } catch (error) {
//                                 console.error(error);
//                                 setMessage(
//                                     `Could not initiate PayPal Checkout...${error}`
//                                 );
//                                 throw error;
//                             }
//                         }}
//                         onApprove={async (data, actions: OnApproveActions) => {
//                             try {
//                                 const response = await fetch(
//                                     `/api/orders/${data.orderID}/capture`,
//                                     {
//                                         method: "POST",
//                                         headers: {
//                                             "Content-Type": "application/json",
//                                         },
//                                     }
//                                 );

//                                 const orderData = await response.json();
//                                 // Three cases to handle:
//                                 //   (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
//                                 //   (2) Other non-recoverable errors -> Show a failure message
//                                 //   (3) Successful transaction -> Show confirmation or thank you message

//                                 const errorDetail = orderData?.details?.[0];

//                                 if (errorDetail?.issue === "INSTRUMENT_DECLINED") {
//                                     // (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()
//                                     // recoverable state, per https://developer.paypal.com/docs/checkout/standard/customize/handle-funding-failures/
//                                     if (actions) {
//                                         return actions.restart();
//                                     }
//                                 } else if (errorDetail) {
//                                     // (2) Other non-recoverable errors -> Show a failure message
//                                     throw new Error(
//                                         `${errorDetail.description} (${orderData.debug_id})`
//                                     );
//                                 } else {
//                                     // (3) Successful transaction -> Show confirmation or thank you message
//                                     // Or go to another URL:  actions.redirect('thank_you.html');
//                                     const transaction =
//                                         orderData.purchase_units[0].payments
//                                             .captures[0];
//                                     setMessage(
//                                         `Transaction ${transaction.status}: ${transaction.id}. See console for all available details`
//                                     );
//                                     console.log(
//                                         "Capture result",
//                                         orderData,
//                                         JSON.stringify(orderData, null, 2)
//                                     );
//                                 }
//                             } catch (error) {
//                                 console.error(error);
//                                 setMessage(
//                                     `Sorry, your transaction could not be processed...${error}`
//                                 );
//                             }
//                         }}
//                     />
//                 </PayPalScriptProvider>
//                 <Message content={message} />
//             </div>
//         </div>
//     );
// };

// export default CheckoutForm;



// src/components/CheckoutForm.js

// import React, { useState } from 'react';
// import { CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

// // Define the style for the CardElement
// const cardElementOptions = {
//     style: {
//         base: {
//             iconColor: '#666ee8',
//             color: '#31325f',
//             fontWeight: '400',
//             fontFamily: 'Roboto, Open Sans, Segoe UI, sans-serif',
//             fontSize: '16px',
//             '::placeholder': {
//                 color: '#aab7c4',
//             },
//         },
//         invalid: {
//             iconColor: '#ffc7ee',
//             color: '#ffc7ee',
//         },
//     },
// };

// export default function CheckoutForm({ clientSecret }) {
//     const [isProcessing, setProcessing] = useState(false);
//     const [error, setError] = useState(null);
//     const [paymentSuccess, setPaymentSuccess] = useState(false);

//     const stripe = useStripe();
//     const elements = useElements();

//     const handleSubmit = async (event) => {
//         event.preventDefault();

//         if (!stripe || !elements) {
//             // Stripe.js has not yet loaded.
//             // Make sure to disable form submission until Stripe.js has loaded.
//             return;
//         }

//         setProcessing(true);
//         setError(null);

//         const { error: paymentError, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
//             payment_method: {
//                 card: elements.getElement(CardElement),
//                 // You can add billing details here if needed
//                 // billing_details: { name: 'John Doe' },
//             },
//         });

//         if (paymentError) {
//             setError(paymentError.message);
//             setProcessing(false);
//             return;
//         }

//         if (paymentIntent.status === 'succeeded') {
//             setPaymentSuccess(true);
//             // FULFILLMENT:
//             // The payment is complete. You can show a success message.
//             // IMPORTANT: Always rely on your server's webhooks to fulfill the order.
//         }

//         setProcessing(false);
//     };

//     if (paymentSuccess) {
//         return (
//             <div className="payment-success">
//                 <h3>Payment Successful! 🎉</h3>
//                 <p>Thank you for your purchase.</p>
//             </div>
//         );
//     }

//     return (
//         <div>
//             <form id="payment-form" onSubmit={handleSubmit}>
//                 <label htmlFor="card-element">Card Details</label>
//                 <CardElement id="card-element" options={cardElementOptions} />
//                 {error && <div id="card-errors" role="alert">{error}</div>}
//                 <button disabled={isProcessing || !stripe} id="submit-button">
//                     {isProcessing ? "Processing..." : "Pay Now"}
//                 </button>
//             </form>
//         </div>
//     );
// }




// import React, { useCallback, useState, useEffect } from "react";
// import { loadStripe } from '@stripe/stripe-js';
// import {
//     EmbeddedCheckoutProvider,
//     EmbeddedCheckout
// } from '@stripe/react-stripe-js';
// import {
//     BrowserRouter as Router,
//     Route,
//     Routes,
//     Navigate
// } from "react-router-dom";

// // Make sure to call `loadStripe` outside of a component’s render to avoid
// // recreating the `Stripe` object on every render.

// const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY as string);

// const CheckoutForm = () => {
//     const fetchClientSecret = useCallback(() => {
//         // Create a Checkout Session
//         return fetch("/create-checkout-session", {
//             method: "POST",
//         })
//             .then((res) => res.json())
//             .then((data) => data.clientSecret);
//     }, []);

//     const options = { fetchClientSecret };

//     return (
//         <div id="checkout">
//             <EmbeddedCheckoutProvider
//                 stripe={stripePromise}
//                 options={options}
//             >
//                 <EmbeddedCheckout />
//             </EmbeddedCheckoutProvider>
//         </div>
//     )
// }

// // const Return = () => {
// //     const [status, setStatus] = useState(null);
// //     const [customerEmail, setCustomerEmail] = useState('');

// //     useEffect(() => {
// //         const queryString = window.location.search;
// //         const urlParams = new URLSearchParams(queryString);
// //         const sessionId = urlParams.get('session_id');

// //         fetch(`/session-status?session_id=${sessionId}`)
// //             .then((res) => res.json())
// //             .then((data) => {
// //                 setStatus(data.status);
// //                 setCustomerEmail(data.customer_email);
// //             });
// //     }, []);

// //     if (status === 'open') {
// //         return (
// //             <Navigate to="/checkout" />
// //         )
// //     }

// //     if (status === 'complete') {
// //         return (
// //             <section id="success">
// //                 <p>
// //                     We appreciate your business! A confirmation email will be sent to {customerEmail}.

// //                     If you have any questions, please email <a href="mailto:orders@example.com">orders@example.com</a>.
// //                 </p>
// //             </section>
// //         )
// //     }

// //     return null;
// // }

// export default CheckoutForm