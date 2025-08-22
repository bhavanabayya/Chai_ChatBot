import React, { useState, Dispatch, SetStateAction, useCallback } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { EmbeddedCheckoutProvider, EmbeddedCheckout } from '@stripe/react-stripe-js';
import { type Message } from "@/components/ChatMessage";
import './Payment.css';
import { PayPalButtons, PayPalScriptProvider } from '@paypal/react-paypal-js';
import { CreateOrderActions, OnApproveActions } from '@paypal/paypal-js';

console.info("Loading PaymentPanel component and Stripe/PayPal libraries...");

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY as string);
const PAYPAL_CLIENT_ID = import.meta.env.VITE_PAYPAL_CLIENT_ID as string;
console.info("Stripe promise created. PayPal client ID loaded.");

// Define the type for the component's props
interface PaymentPanelProps {
    isOpen: boolean,
    setIsOpen: Dispatch<SetStateAction<boolean>>,
    clientSecret: string,
    paypalOrderId: string,
    socket: WebSocket,
    setMessages: Dispatch<SetStateAction<Message[]>>
}

function PaymentPanel({ isOpen, setIsOpen, clientSecret, paypalOrderId, socket, setMessages }: PaymentPanelProps) {
    
    // Log component re-renders and prop changes
    console.debug(`PaymentPanel re-rendered. isOpen: ${isOpen}, clientSecret: ${!!clientSecret}`);
    
    const [isComplete, setIsComplete] = useState(false);
    const [open, setOpen] = useState(false);

    // Prevent clicks inside the panel from closing it
    const handlePanelClick = (e: React.MouseEvent<HTMLDivElement>) => {
        e.stopPropagation();
    };

    const handleComplete = useCallback(() => {
        console.info("Stripe payment completed! Notifying backend.");
        // send a message here (fake AI) that says Please hold on while I confirm your payment was made

        const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: "Please wait while I confirm your payment.",
            sender: 'assistant',
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiMessage]);
        
        setIsComplete(true);
        setIsOpen(false);

        if (socket && socket.readyState === WebSocket.OPEN) {
            console.info("WebSocket is open. Sending 'payment_complete' event.");
            socket.send(JSON.stringify({
                event: 'payment_complete',
                status: 'success'
            }));
        } else {
            console.error("WebSocket is not open. Payment notification could not be sent to backend.");
        }
    }, [socket, setMessages, setIsOpen]);

    return (
        <>
            {/* Backdrop: Only renders when the panel is open */}
            {isOpen && (
                <div
                    className="panel-backdrop"
                    onClick={() => {
                        console.info("Panel backdrop clicked. Closing panel.");
                        setIsOpen(false);
                    }}
                ></div>
            )}

            {/* Main Panel */}
            <div className={`payment-panel ${isOpen ? 'open' : ''}`}
                onClick={handlePanelClick}>
                <div className="panel-header">
                    <h2>Complete Your Payment</h2>
                    <button className="close-btn" onClick={() => {
                        console.info("Close button clicked. Closing payment panel.");
                        setIsOpen(false);
                    }}>
                        &times; {/* A simple 'X' icon */}
                    </button>
                </div>

                <div className="panel-body flex-1 min-h-0 overflow-y-auto overscroll-contain">
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
                            {/* Log when the loading state is shown */}
                            <p>Loading payment options...</p>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}

export default PaymentPanel;