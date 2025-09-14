import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Lightbulb } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onClickHint: () => void;
  disabled?: boolean;
}

export const ChatInput = ({ onSendMessage, onClickHint, disabled }: ChatInputProps) => {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-border bg-background p-4">
      <div className="w-full px-4 md:px-8 lg:px-16">
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          {/* Click Hint Button */}
          <Button
            type="button"
            onClick={onClickHint}
            variant="outline"
            size="sm"
            className="shrink-0 gap-2 bg-gradient-primary text-white border-none hover:bg-chat-button-primary-hover shadow-glow transition-all"
            disabled={disabled}
          >
            <Lightbulb className="h-4 w-4" />
            Click Hint
          </Button>

          {/* Message Input */}
          <div className="flex-1 relative">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything..."
              disabled={disabled}
              className={cn(
                "pr-12 py-3 text-base resize-none bg-chat-input-bg border-chat-input-border",
                "focus:ring-2 focus:ring-chat-button-primary focus:border-transparent",
                "transition-all duration-200"
              )}
            />
            
            {/* Send Button */}
            <Button
              type="submit"
              size="sm"
              disabled={!message.trim() || disabled}
              className={cn(
                "absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 p-0",
                "bg-chat-button-primary hover:bg-chat-button-primary-hover",
                "disabled:bg-muted disabled:text-muted-foreground",
                "transition-all duration-200"
              )}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
        
        <p className="text-xs text-muted-foreground text-center mt-2">
          Click "Click Hint" for helpful suggestions or type your own message
        </p>
      </div>
    </div>
  );
};
