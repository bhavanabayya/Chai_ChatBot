import { cn } from "@/lib/utils";
import React, { useEffect } from "react";

export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'assistant';
    timestamp: Date;
}

interface ChatMessageProps {
    message: Message;
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
    const isUser = message.sender === 'user';
    
    // Log message content and sender on render
    useEffect(() => {
        console.debug(`ChatMessage rendered for message ID: ${message.id}, Sender: ${message.sender}`);
        console.debug("Message text:", message.text);
    }, [message]);
    
    // This function will parse the message and render a button if the link pattern is found
    const renderMessageContent = () => {
        // Regular expression to find the specific pattern: 📄 [Button Text](URL)
        const linkRegex = /(?:📄\s*)?\[(.*?)\]\((.*?)\)\.?/;
        const match = message.text.match(linkRegex);

        // If no link pattern is found, just return the plain text
        if (!match) {
            console.debug("No special link pattern found in message. Rendering plain text.");
            return <>{message.text}</>;
        }

        // If a match is found, extract the parts
        const [fullMatch, buttonText, url] = match;
        console.info(`Special link pattern found. Button Text: '${buttonText}', URL: '${url}'`);

        // Split the message text by the full matched link string to get the text before and after
        const parts = message.text.split(fullMatch);
        const textBefore = parts[0];
        const textAfter = parts[1];

        return (
            <>
                {/* Render the text before the button */}
                {textBefore}

                {/* Render the link as a styled button */}
                <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(
                        "inline-flex items-center justify-center px-4 py-2 my-2 text-sm font-medium rounded-lg shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2",
                        isUser
                            ? "bg-white/20 hover:bg-white/30 text-white focus:ring-white"
                            : "bg-blue-700 hover:bg-blue-800 text-white focus:ring-blue-500"
                    )}
                >
                    {buttonText}
                </a>

                {/* Render the text after the button */}
                {textAfter}
            </>
        );
    };

    return (
        <div className={cn(
            "flex w-full mb-4 animate-in fade-in slide-in-from-bottom-2 duration-300",
            isUser ? "justify-end" : "justify-start"
        )}>
            <div className={cn(
                "max-w-[70%] rounded-2xl px-4 py-3 shadow-sm border transition-all duration-200 hover:shadow-md",
                isUser
                    ? "bg-user-message text-user-message-foreground rounded-tr-sm bg-blue-800 font-medium text-right"
                    : "bg-assistant-message text-assistant-message-foreground border-message-border rounded-tl-sm font-medium text-left"
            )}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                    {renderMessageContent()}
                </p>
                <span className={cn(
                    "text-xs mt-2 block opacity-70",
                    isUser ? "text-user-message-foreground text-left" : "text-muted-foreground text-right"
                )}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>
        </div>
    );
};

export default ChatMessage;