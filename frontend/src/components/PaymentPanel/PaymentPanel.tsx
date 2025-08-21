import React, { useState, Dispatch, SetStateAction, useCallback } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { EmbeddedCheckoutProvider, EmbeddedCheckout } from '@stripe/react-stripe-js';
import { type Message } from "@/components/ChatMessage";
import './Payment.css';
import { PayPalButtons, PayPalScriptProvider } from '@paypal/react-paypal-js';
import { CreateOrderActions, OnApproveActions } from '@paypal/paypal-js';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY as string);
const PAYPAL_CLIENT_ID = import.meta.env.VITE_PAYPAL_CLIENT_ID as string

// Define the type for the component's props
interface PaymentPanelProps {
    isOpen: boolean,
    setIsOpen: Dispatch<SetStateAction<boolean>>,
    clientSecret: string,
    paypalOrderId: string,
    socket: WebSocket,
    setMessages: Dispatch<SetStateAction<Message[]>>
    // sessionId: String
}

function PaymentPanel({ isOpen, setIsOpen, clientSecret, paypalOrderId, socket, setMessages }: PaymentPanelProps) {


    const initialOptions = {
        "clientId": PAYPAL_CLIENT_ID,
        "enable-funding": "venmo",
        "disable-funding": "",
        "buyer-country": "US",
        currency: "USD",
        "data-page-type": "product-details",
        components: "buttons",
        "data-sdk-integration-source": "developer-studio",
    };

    // console.log("Client Secret in PaymentPanel:", clientSecret);
    const [isComplete, setIsComplete] = useState(false);
    const [open, setOpen] = useState(false);

    // Prevent clicks inside the panel from closing it
    const handlePanelClick = (e: React.MouseEvent<HTMLDivElement>) => {
        e.stopPropagation();
    };


    // useEffect(() => {
    //     scrollToBottom();
    // }, [isComplete]);

    const handleComplete = useCallback(() => {
        console.log("payment completed!")

        // send a message here (fake AI) that says Please hold on while I confirm your payment was made

        const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: "Please wait while I confirm your payment.",
            sender: 'assistant',
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiMessage])

        setIsComplete(true)
        setIsOpen(false);

        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                event: 'payment_complete', // Send the event name as part of the data
                status: 'success'
            }));
        } else {
            console.log("Oh no, socket was closed, payment notification didn't go through")
        }
    }, [socket]);

    return (
        <>
            {/* Backdrop: Only renders when the panel is open */}
            {isOpen && (
                <div
                    className="panel-backdrop"
                    onClick={() => (setIsOpen(false))}
                ></div>
            )}

            {/* Main Panel */}
            <div className={`payment-panel ${isOpen ? 'open' : ''}`}
                onClick={handlePanelClick}>
                <div className="panel-header">
                    <h2>Complete Your Payment</h2>
                    <button className="close-btn" onClick={() => (setIsOpen(false))}>
                        &times; {/* A simple 'X' icon */}
                    </button>
                </div>

                <div className="panel-body flex-1 min-h-0 overflow-y-auto overscroll-contain">
                {/* <div className="flex-grow p-4 overflow-y-auto min-h-0"> */}
                    {/* Only render the Stripe Checkout when the clientSecret is available. */}
                    {clientSecret && stripePromise && EmbeddedCheckoutProvider && EmbeddedCheckout ? (
                        <EmbeddedCheckoutProvider
                            key={clientSecret}
                            stripe={stripePromise}
                            options={{ clientSecret, onComplete: handleComplete }}
                        >
                            <EmbeddedCheckout />
                        </EmbeddedCheckoutProvider>
                    ) : (
                        <div className="flex items-center justify-center h-full">
                            <p>Loading payment options...</p>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}

export default PaymentPanel;