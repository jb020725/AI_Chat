import { cn } from "../lib/utils";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Shield, Info } from "lucide-react";

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  timestamp?: Date;
  safety_violation?: any;
  risk_level?: string;
}

export const ChatMessage = ({ message, isUser, timestamp, safety_violation, risk_level }: ChatMessageProps) => {
  return (
    <div className={cn(
      "flex w-full mb-4 animate-in fade-in-0 slide-in-from-bottom-2 duration-300",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "max-w-[85%] sm:max-w-[70%] rounded-2xl px-4 py-3 shadow-sm",
        isUser 
          ? "bg-chat-user text-chat-user-foreground rounded-br-md" 
          : "bg-chat-assistant text-chat-assistant-foreground rounded-bl-md"
      )}>
        {/* Safety Violation Alert */}
        {safety_violation && !isUser && (
          <Alert className="mb-3 border-orange-200 bg-orange-50">
            <AlertTriangle className="h-4 w-4 text-orange-600" />
            <AlertDescription className="text-orange-800 text-xs">
              <strong>Safety Notice:</strong> {safety_violation.description}
            </AlertDescription>
          </Alert>
        )}

        {/* Risk Level Badge */}
        {risk_level && !isUser && (
          <div className="mb-2">
            <Badge 
              variant={risk_level === 'high' || risk_level === 'critical' ? 'destructive' : 
                      risk_level === 'medium' ? 'secondary' : 'outline'}
              className="text-xs"
            >
              <Shield className="w-3 h-3 mr-1" />
              Risk: {risk_level}
            </Badge>
          </div>
        )}

        <p className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap break-words">
          {message}
        </p>
        
        {timestamp && (
          <div className="text-xs opacity-70 mt-1">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </div>
  );
};