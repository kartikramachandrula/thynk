import React, { useState, useRef, useEffect } from "react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: string;
}

const HINT_TEXT = `Here's your hint:

**Solution Steps:**
1. First, identify the key variables in your equation
2. Apply the appropriate mathematical operations
3. Simplify step by step

**Example:**
\`\`\`
x² + 5x - 6 = 0
(x + 6)(x - 1) = 0
x = -6 or x = 1
\`\`\`

Need help with a specific equation? Just type it in!`;

export const ChatContainer = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const addMessage = (content: string, isUser: boolean) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      isUser,
      timestamp,
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const simulateTyping = async (message: string) => {
    setIsTyping(true);
    
    // Simulate typing delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    addMessage(message, false);
    setIsTyping(false);
  };

  const handleSendMessage = (message: string) => {
    addMessage(message, true);
    
    // Simulate AI response
    setTimeout(() => {
      simulateTyping("I understand your message. How can I help you further?");
    }, 500);
  };

  const handleClickHint = () => {
    // Add user message "give hint"
    addMessage("give hint", true);
    
    // Simulate AI response with the constant hint
    setTimeout(() => {
      simulateTyping(HINT_TEXT);
    }, 500);
  };

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages, isTyping]);

  return (
    <div className="flex h-full flex-col bg-chat-main">
      {/* Header with Logo and Name */}
      <header className="flex items-center justify-between px-4 md:px-8 lg:px-16 py-4 border-b border-border bg-background shadow-sm">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-gradient-primary flex items-center justify-center">
            <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-semibold text-foreground">Click Hint Chat</h1>
            <p className="text-sm text-muted-foreground">AI-powered assistance</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 bg-green-500 rounded-full"></div>
          <span className="text-sm text-muted-foreground">Online</span>
        </div>
      </header>

      {/* Chat Messages */}
      <ScrollArea ref={scrollAreaRef} className="flex-1">
        <div className="w-full px-4 md:px-8 lg:px-16">
          {messages.length === 0 && (
            <div className="flex h-64 items-center justify-center">
              <div className="text-center space-y-4">
                <h2 className="text-2xl font-semibold text-foreground">Click Hint Chat</h2>
                <p className="text-muted-foreground max-w-md">
                  Welcome! Click "Click Hint" for helpful suggestions or type your own message to get started.
                </p>
              </div>
            </div>
          )}
          
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message.content}
              isUser={message.isUser}
              timestamp={message.timestamp}
            />
          ))}
          
          {isTyping && (
            <div className="flex gap-4 p-6 bg-chat-ai-message">
              <div className="h-8 w-8 shrink-0 rounded-full bg-gradient-primary flex items-center justify-center">
                <div className="text-white text-xs font-medium">AI</div>
              </div>
              <div className="flex items-center space-x-1">
                <div className="flex space-x-1">
                  <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce"></div>
                  <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Chat Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        onClickHint={handleClickHint}
        disabled={isTyping}
      />
    </div>
  );
};
