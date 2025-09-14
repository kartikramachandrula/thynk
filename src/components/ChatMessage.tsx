import React from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  timestamp?: string;
}

// Simple markdown parser for basic formatting
const parseMarkdown = (text: string) => {
  return text
    // Bold text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Code blocks
    .replace(/```([\s\S]*?)```/g, '<pre class="bg-muted p-3 rounded-md my-2 overflow-x-auto"><code>$1</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-sm">$1</code>')
    // Line breaks
    .replace(/\n/g, '<br>');
};

export const ChatMessage = ({ message, isUser, timestamp }: ChatMessageProps) => {
  const formattedMessage = parseMarkdown(message);

  return (
    <div className={cn("flex gap-4 p-6 transition-colors", isUser ? "bg-chat-user-message" : "bg-chat-ai-message")}>
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className={cn("text-xs", isUser ? "bg-primary text-primary-foreground" : "bg-gradient-primary text-white")}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>
      
      <div className="flex-1 space-y-2">
        <div className="prose prose-sm max-w-none">
          <div 
            className="text-foreground leading-relaxed"
            dangerouslySetInnerHTML={{ __html: formattedMessage }}
          />
        </div>
        {timestamp && (
          <div className="text-xs text-muted-foreground">
            {timestamp}
          </div>
        )}
      </div>
    </div>
  );
};
