import { useState } from "react";
import { ChatWindow } from "@/components/ChatWindow";
import { ChatInput } from "@/components/ChatInput";
import { ThemeToggle } from "@/components/ThemeToggle";
import { type Message } from "@/components/ChatMessage";

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const generateResponse = (userMessage: string): string => {
    const responses = [
      "I'd be happy to help you find the perfect products! What are you looking for today?",
      "Great question! Let me search our inventory for the best options for you.",
      "I understand you're interested in that. Here are some recommendations based on your preferences.",
      "That's a wonderful choice! Many customers love this type of product. Would you like to see similar items?",
      "I can definitely help with that! Our chai selection is particularly popular. What flavor profile are you interested in?",
      "Excellent! Based on what you've told me, I think you might also be interested in these complementary products.",
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const handleSendMessage = async (messageText: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Simulate API call delay
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: generateResponse(messageText),
        sender: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000 + Math.random() * 2000); // Random delay between 1-3 seconds
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-b from-background to-chat-bg">
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
      <ChatWindow messages={messages} />

      {/* Chat Input */}
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
};

export default Index;
