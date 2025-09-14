import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, MessageCircle, Lightbulb } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

// API helper - future implementation placeholder
async function giveHint(): Promise<{ text: string }> {
  // FUTURE: return fetch('/api/give_hint').then(r => r.json());
  return { 
    text: `Here's your hint:

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

Need help with a specific equation? Just type it in!` 
  }; // placeholder with better formatting for equations
}

const ClickHintChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (role: 'user' | 'assistant', text: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role,
      text,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  // Handle manual send (user types and hits Send/Enter)
  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    
    addMessage('user', inputValue);
    setInputValue('');
    inputRef.current?.focus();
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle Click Hint button - clearly isolated for future API integration
  const handleClickHint = async () => {
    setIsLoading(true);
    
    try {
      addMessage('user', 'Give Hint');
      
      const thinkingId = Date.now().toString() + '_thinking';
      const thinkingMessage: Message = {
        id: thinkingId,
        role: 'assistant',
        text: 'THINKING_INDICATOR',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, thinkingMessage]);
      
      // 3) Simulate thinking delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 4) Get hint text (current: constant, future: API call)
      const { text: hintText } = await giveHint();
      
      // 5) Replace thinking indicator with actual response
      setMessages(prev => prev.map(msg => 
        msg.id === thinkingId 
          ? { ...msg, text: hintText, id: Date.now().toString() }
          : msg
      ));
    } catch (error) {
      console.error('Error getting hint:', error);
      // Remove thinking indicator and add error message
      setMessages(prev => prev.filter(msg => msg.text !== 'THINKING_INDICATOR'));
      addMessage('assistant', 'Sorry, I could not get a hint right now.');
    } finally {
      setIsLoading(false);
    }
  };

  const TypingIndicator = () => (
    <div className="flex items-center space-x-2 p-3">
      <Avatar className="h-8 w-8">
        <AvatarFallback className="bg-primary text-primary-foreground text-xs">
          AI
        </AvatarFallback>
      </Avatar>
      <div className="flex space-x-1">
        <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce"></div>
        <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
        <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Chat Header */}
      <header className="flex items-center p-4 border-b border-border bg-card">
        <MessageCircle className="h-6 w-6 mr-2 text-primary" />
        <h1 className="text-lg font-semibold text-foreground">Click Hint Chat</h1>
      </header>

      {/* Chat Transcript Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            <Lightbulb className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Click "Click Hint" to get started, or type a message below.</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex items-start space-x-2 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
              {message.role === 'assistant' && (
                <Avatar className="h-8 w-8 mt-1">
                  <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                    AI
                  </AvatarFallback>
                </Avatar>
              )}
              
              <div
                className={`px-4 py-2 rounded-lg shadow-sm ${
                  message.role === 'user'
                    ? 'bg-muted text-foreground ml-auto'
                    : ''
                }`}
              >
                {message.text === 'THINKING_INDICATOR' ? (
                  <div className="flex items-center space-x-2 text-muted-foreground italic">
                    <div className="flex space-x-1">
                      <div className="h-1.5 w-1.5 bg-muted-foreground rounded-full animate-bounce"></div>
                      <div className="h-1.5 w-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="h-1.5 w-1.5 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-sm">Thought for a few seconds</span>
                  </div>
                ) : (
                  <>
                    <div className="text-sm whitespace-pre-wrap">
                      {message.text}
                    </div>
                    <span className="text-xs opacity-70 mt-1 block">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {/* Typing indicator */}
        {isLoading && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Compose Bar - Fixed at bottom */}
      <div className="border-t border-border bg-card p-4">
        <div className="flex items-center space-x-2 max-w-4xl mx-auto">
          {/* Click Hint Button - LEFT side */}
          <Button
            onClick={handleClickHint}
            disabled={isLoading}
            variant="outline"
            size="default"
            aria-label="Click to get a hint"
            className="shrink-0"
          >
            <Lightbulb className="h-4 w-4 mr-2" />
            Click Hint
          </Button>

          {/* Text Input - CENTER */}
          <div className="flex-1">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask anything..."
              disabled={isLoading}
              className="w-full"
              aria-label="Type your message"
            />
          </div>

          {/* Send Button - RIGHT side */}
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            size="default"
            aria-label="Send message"
            className="shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ClickHintChat;
