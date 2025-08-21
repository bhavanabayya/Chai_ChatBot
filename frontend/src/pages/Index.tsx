import { useState, useEffect } from "react";
import { ChatWindow } from "@/components/ChatWindow";
import { ChatInput } from "@/components/ChatInput";
import { ThemeToggle } from "@/components/ThemeToggle";
import { type Message } from "@/components/ChatMessage";
import { v4 as uuidv4 } from 'uuid';
import PaymentPanel from "@/components/PaymentPanel/PaymentPanel";

// import './Index.css'

// Define the shape of the expected API response
interface ApiResponse {
    response?: string;
    error?: string;
}

const Index = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string>('');
    const [ws, setWs] = useState<WebSocket>(null);
    const [isPanelOpen, setPanelOpen] = useState(false);
    const [showPaymentPanelButton, setShowPaymentPanelButton] = useState(false);
    const openPanel = () => setPanelOpen(true);
    const [clientSecret, setClientSecret] = useState('');
    const [paypalOrderId, setPaypalOrderId] = useState('');

    // Generate a session ID when the component mounts
    useEffect(() => {

        /* Send server the session ID in every message */
        const sessionUUID = uuidv4();
        setSessionId(sessionUUID);

        const newSocket = new WebSocket(`ws://localhost:8001/ws/${sessionUUID}`);

        newSocket.onopen = () => {
            console.log("WebSocket connection established successfully!");
            console.log("Session UUID: " + sessionUUID);
            setWs(newSocket);
        };

        newSocket.onclose = () => {
            console.log('WebSocket disconnected. ❌');
        }

        newSocket.onmessage = (event) => {
            const msg = JSON.parse(event.data);

            if (msg.type === 'payment_intent_created' && msg.client_secret) {
                // console.log("Client Secret received from server: " + msg.client_secret);
                setClientSecret(msg.client_secret);
                setPaypalOrderId(msg.paypal_order_id);

                console.log("Paypal order id: " + msg.paypal_order_id)

                setPanelOpen(true);
                setShowPaymentPanelButton(true);
            } else if (msg.type === 'agent_message' && msg.ai_message) {
                const aiMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    text: msg.ai_message,
                    sender: 'assistant',
                    timestamp: new Date(),
                };
                setMessages(prev => [...prev, aiMessage])
            }
        };

        newSocket.onerror = (error) => {
            console.error("WebSocket error: ", error);
        };


        /* "Send" an initial message to explaing to the user what to do */
        {

            const timer = setTimeout(() => {
                const inititalMessage: Message = {
                    id: Date.now().toString(),
                    text: "Welcome to Chai Corner! If you're a returning customer, could you please provide your full name? If you'd like to continue as a guest, just let me know!",
                    sender: 'assistant',
                    timestamp: new Date()
                }
                setMessages(prev => [...prev, inititalMessage]);
            }, 1000);

        }

        // return () => {
        //     newSocket.close();
        // };
    }, []);

    const handleSendMessage = async (messageText: string) => {
        const userMessage: Message = {
            id: Date.now().toString(),
            text: messageText,
            sender: 'user',
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8001/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText, session_id: sessionId }),
            });

            // Assert the type of the JSON response
            const data: ApiResponse = await response.json();

            if (data.response) {
                const aiMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    text: data.response,
                    sender: 'assistant',
                    timestamp: new Date(),
                };
                setMessages((prevMessages) => [...prevMessages, aiMessage]);
            } else {
                console.error('Error from backend:', data.error);
                const errorMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    text: "Sorry, something went wrong: " + data.response,
                    sender: 'assistant',
                    timestamp: new Date(),
                };
                setMessages((prevMessages) => [...prevMessages, errorMessage]);
            }
        } catch (error) {
            console.error('Failed to fetch:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: "Sorry, I couldn't connect to the server",
                sender: 'assistant',
                timestamp: new Date(),
            };
            setMessages((prevMessages) => [...prevMessages, errorMessage]);
        }

        setIsLoading(false);

    };

    return (
        <div className="h-screen flex flex-col bg-gradient-to-b from-background to-chat-bg ">
            {/* Header */}
            <div className="border-b border-border bg-background/95 backdrop-blur-sm px-4 py-3">
                <div className="max-w-4xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-primary to-orange-500 rounded-full flex items-center justify-center">
                            <span className="text-sm">🫖</span>
                        </div>
                        <div>
                            <h1 className="font-semibold text-foreground">Chai Corner</h1>
                            <p className="text-xs text-muted-foreground">AI E-commerce Assistant</p>
                        </div>
                    </div>
                    <ThemeToggle />
                </div>
            </div>

            {/* Chat Window */}
            <div className="flex  flex-1">
                <ChatWindow messages={messages} />
                {/* Payment panel button appears once payment is ready to be taken so that if the user accidentally closes it, they can reopen */}
                {showPaymentPanelButton && <button
                    className="toggle-payment-button"
                    onClick={() => setPanelOpen(!isPanelOpen)}
                    aria-label="Toggle panel"
                >
                    {isPanelOpen ? '›' : '‹'}
                </button>
                }
            </div>

            {/* Chat Input */}
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} messages={messages} />

            <PaymentPanel
                isOpen={isPanelOpen}
                setIsOpen={setPanelOpen}
                clientSecret={clientSecret}
                paypalOrderId={paypalOrderId}
                socket={ws}
                setMessages={setMessages}
            />
        </div>
    );
};

export default Index;
