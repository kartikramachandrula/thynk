import { MessageSquare, Plus, Settings, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatSidebarProps {
  className?: string;
}

export const ChatSidebar = ({ className }: ChatSidebarProps) => {
  return (
    <div className={cn("flex h-full w-64 flex-col bg-chat-sidebar", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-6 w-6 text-chat-sidebar-foreground" />
          <span className="font-semibold text-chat-sidebar-foreground">Click Hint Chat</span>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="px-4 pb-4">
        <Button 
          variant="outline" 
          className="w-full justify-start gap-2 border-chat-sidebar-hover bg-transparent text-chat-sidebar-foreground hover:bg-chat-sidebar-hover hover:text-chat-sidebar-foreground"
        >
          <Plus className="h-4 w-4" />
          New chat
        </Button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto px-2">
        <div className="space-y-1">
          <div className="rounded-lg bg-chat-sidebar-hover px-3 py-2 text-sm text-chat-sidebar-foreground">
            Click Hint Help Session
          </div>
          <div className="rounded-lg px-3 py-2 text-sm text-chat-sidebar-foreground hover:bg-chat-sidebar-hover cursor-pointer transition-colors">
            Previous Chat
          </div>
          <div className="rounded-lg px-3 py-2 text-sm text-chat-sidebar-foreground hover:bg-chat-sidebar-hover cursor-pointer transition-colors">
            Another Chat
          </div>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="p-4 space-y-2">
        <Button 
          variant="ghost" 
          size="sm" 
          className="w-full justify-start gap-2 text-chat-sidebar-foreground hover:bg-chat-sidebar-hover hover:text-chat-sidebar-foreground"
        >
          <User className="h-4 w-4" />
          Profile
        </Button>
        <Button 
          variant="ghost" 
          size="sm" 
          className="w-full justify-start gap-2 text-chat-sidebar-foreground hover:bg-chat-sidebar-hover hover:text-chat-sidebar-foreground"
        >
          <Settings className="h-4 w-4" />
          Settings
        </Button>
      </div>
    </div>
  );
};
