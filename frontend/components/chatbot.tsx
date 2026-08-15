
"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  FlaskConical,
  Plus,
  MessageSquare,
  Trash2,
  Settings,
  Brain,
  Wifi,
  WifiOff,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Card,
  CardContent,
  CardHeader,
  CardFooter,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { backendApi } from "@/lib/backend-api";
import { useFirstVisit } from "@/hooks/use-first-visit";
import { useSessionManager } from "@/hooks/use-session-manager";
import { useBackendStatus } from "@/hooks/use-backend-status";
import { ChatbotGuideModal } from "./chatbot-guide-modal";
import { OceanusIcon } from "./icons";

import { MarkdownRenderer } from "./markdown-renderer";
import { AdvancedVisualizationRenderer, AdvancedVizSpec } from "./advanced-visualization-renderer";

// Component to render message content with markdown support
function MessageContent({ content }: { content: string }) {
  // Extract optional viz block ```viz {json}
  const vizMatch = content.match(/```viz\n([\s\S]*?)\n```/);
  let cleaned = content;
  let vizSpecs: AdvancedVizSpec[] = [];
  if (vizMatch) {
    cleaned = content.replace(vizMatch[0], "").trim();
    try {
      const payload = JSON.parse(vizMatch[1]);
      if (payload && Array.isArray(payload.visualizations)) vizSpecs = payload.visualizations as AdvancedVizSpec[];
    } catch {}
  }
  return (
    <div className="space-y-6">
      {cleaned && <MarkdownRenderer content={cleaned} />}
      {vizSpecs.map((spec, i) => (
        <AdvancedVisualizationRenderer key={i} spec={spec} />
      ))}
    </div>
  );
}
export function Chatbot() {
  const {
    sessions,
    currentSessionId,
    currentMessages,
    isLoading: sessionLoading,
    isLoaded,
    createNewSession,
    switchToSession,
    removeSession,
    sendMessage,
    clearAllSessions,
    validateAndCleanupSessions,
  } = useSessionManager();

  const [input, setInput] = useState("");
  const [isFirstVisit, setVisited] = useFirstVisit("chatbot-guide-visited");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [userPreferences, setUserPreferences] = useState({
    detail_level: "comprehensive",
    preferred_regions: ["Arabian Sea", "Bay of Bengal"],
    analysis_focus: "comprehensive"
  });

  const { isOnline: backendOnline, isChecking: checkingBackend } = useBackendStatus();

  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsModalOpen(isFirstVisit);
  }, [isFirstVisit]);

  // Validate and cleanup sessions when component loads
  useEffect(() => {
    if (isLoaded && sessions.length > 0) {
      // Add a small delay to avoid immediate validation on every load
      const timer = setTimeout(() => {
        validateAndCleanupSessions();
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [isLoaded, sessions.length, validateAndCleanupSessions]);
  
  useEffect(() => {
    if (scrollAreaRef.current) {
        const viewport = scrollAreaRef.current.querySelector('div[data-radix-scroll-area-viewport]');
        if (viewport) {
            viewport.scrollTop = viewport.scrollHeight;
        }
    }
  }, [currentMessages]);

  const handleNewChat = async () => {
    try {
      await createNewSession(userPreferences);
      setInput("");
    } catch (error) {
      console.error('Failed to create new chat:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent, queryOverride?: string) => {
    e.preventDefault();
    
    const query = queryOverride || input;
    if (!query.trim() || sessionLoading) return;

    setInput("");

    try {
      await sendMessage(query, userPreferences);
    } catch (error) {
      console.error('Chat error:', error);
      
      // Show user-friendly error message
      if (error instanceof Error) {
        if (error.message.includes('404') || error.message.includes('SESSION_EXPIRED')) {
          // Session expired, the session manager will handle creating a new one
          console.log('Session expired, will create new session on retry');
        } else if (error.message.includes('timeout') || error.message.includes('cancelled')) {
          console.log('Request timed out or was cancelled');
        } else {
          console.log('Chat request failed:', error.message);
        }
      }
    }
  };

  const handleExampleQuestionClick = (question: string) => {
    setInput(question);
    handleSubmit(new Event('submit') as any, question);
  };

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    removeSession(sessionId);
  };

  const getCurrentSessionContext = () => {
    const currentSession = sessions.find(s => s.id === currentSessionId);
    return currentSession?.context;
  };

  return (
    <TooltipProvider>
      <ChatbotGuideModal isOpen={isModalOpen} onClose={() => {
        setIsModalOpen(false);
        setVisited();
      }} />
      <div className="flex h-full w-full items-center justify-center p-4">
        <Card className="h-full w-full max-w-6xl flex flex-row">
          <aside className="w-1/5 border-r flex flex-col">
            <div className="p-4 border-b">
               <Button onClick={handleNewChat} className="w-full" disabled={sessionLoading}>
                <Plus className="mr-2 h-4 w-4" /> New Chat
              </Button>
            </div>
            
            {/* Session Context Display */}
            {currentSessionId && getCurrentSessionContext() && (
              <div className="p-4 border-b bg-muted/30">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                  <Brain className="inline w-3 h-3 mr-1" />
                  Context
                </h4>
                <div className="space-y-2 text-xs">
                  {getCurrentSessionContext() && getCurrentSessionContext()!.regions_discussed.length > 0 && (
                    <div>
                      <span className="font-medium">Regions:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {getCurrentSessionContext()!.regions_discussed.map(region => (
                          <Badge key={region} variant="secondary" className="text-xs">
                            {region}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {getCurrentSessionContext() && getCurrentSessionContext()!.floats_analyzed.length > 0 && (
                    <div>
                      <span className="font-medium">Floats:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {getCurrentSessionContext()!.floats_analyzed.map(float => (
                          <Badge key={float} variant="outline" className="text-xs">
                            {float}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {getCurrentSessionContext() && getCurrentSessionContext()!.parameters_of_interest.length > 0 && (
                    <div>
                      <span className="font-medium">Parameters:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {getCurrentSessionContext()!.parameters_of_interest.map(param => (
                          <Badge key={param} variant="default" className="text-xs">
                            {param}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            <ScrollArea className="flex-1">
              <div className="p-4 space-y-2">
                 <h3 className="px-2 text-xs font-semibold text-muted-foreground uppercase">Sessions</h3>
                {!isLoaded ? (
                  <div className="space-y-2">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                  </div>
                ) : sessions.length > 0 ? (
                  sessions.map(session => (
                    <div key={session.id} className="relative group">
                      <Button 
                        variant={currentSessionId === session.id ? "secondary" : "ghost"} 
                        className="w-full justify-start text-left h-auto whitespace-normal p-3"
                        onClick={() => switchToSession(session.id)}
                      >
                        <div className="flex flex-col items-start w-full">
                          <div className="flex items-center w-full min-w-0">
                            <MessageSquare className="mr-2 h-4 w-4 flex-shrink-0" />
                            <span className="font-medium whitespace-normal break-words line-clamp-2">{session.name}</span>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                            <span>{session.message_count} messages</span>
                            {session.context && (
                              <span>• {session.context.regions_discussed.length + session.context.floats_analyzed.length} items</span>
                            )}
                          </div>
                        </div>
                      </Button>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="absolute right-1 top-1 opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0"
                            onClick={(e) => handleDeleteSession(session.id, e)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Delete session</TooltipContent>
                      </Tooltip>
                    </div>
                  ))
                ) : (
                  <p className="p-4 text-sm text-center text-muted-foreground">No sessions yet. Start a new chat!</p>
                )}
              </div>
            </ScrollArea>
          </aside>
          <div className="flex flex-col w-4/5">
            <CardHeader className="flex flex-col gap-4 border-b">
              <div className="flex flex-row items-center justify-between">
                <div className="flex items-center gap-3">
                  <Sparkles className="h-6 w-6 text-primary" />
                  <h2 className="text-lg font-semibold">Multi-Agent RAG</h2>
                  {currentSessionId && (
                    <Badge variant="outline" className="text-xs">
                      Session Active
                    </Badge>
                  )}
                  {/* Backend Status Indicator */}
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center gap-1">
                        {checkingBackend ? (
                          <AlertCircle className="h-4 w-4 text-yellow-500 animate-pulse" />
                        ) : backendOnline ? (
                          <Wifi className="h-4 w-4 text-green-500" />
                        ) : (
                          <WifiOff className="h-4 w-4 text-red-500" />
                        )}
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      {checkingBackend ? 'Checking backend...' : backendOnline ? 'Backend connected' : 'Backend offline'}
                    </TooltipContent>
                  </Tooltip>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Brain className="h-4 w-4"/>
                    <span>6 Agents • Cyclic Refinement</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <FlaskConical className="h-4 w-4"/>
                    <span>Research Grade</span>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-1 p-0">
              <ScrollArea className="h-full pr-4" ref={scrollAreaRef}>
                <div className="px-6 pr-8 py-6 space-y-6">
                  {!isLoaded ? (
                    <div className="flex h-full items-center justify-center">
                      <Skeleton className="h-4 w-48" />
                    </div>
                  ) : (
                    <>
                      {currentMessages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex items-start gap-4 min-w-0 w-full ${
                            message.role === "user" ? "justify-end" : ""
                          }`}
                        >
                          {message.role === "assistant" && (
                            <Avatar className="h-9 w-9">
                              <div className="flex h-full w-full items-center justify-center rounded-full bg-primary">
                                  <OceanusIcon className="h-5 w-5 text-primary-foreground"/>
                              </div>
                            </Avatar>
                          )}
                           <div
                             className={`max-w-[90%] min-w-0 space-y-2 rounded-lg px-4 py-3 mx-2 overflow-x-auto break-words whitespace-pre-wrap ${
                              message.role === "user"
                                ? "bg-primary text-primary-foreground"
                                : "bg-secondary"
                            }`}
                          >
                            <MessageContent content={message.content} />
                            {message.role === 'assistant' && message.metadata && (
                              <div className="pt-2 text-xs text-muted-foreground border-t">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span>Response time: {message.metadata.response_time?.toFixed(1)}s</span>
                                  {message.metadata.has_context && (
                                    <Badge variant="secondary" className="text-xs">
                                      <Brain className="w-3 h-3 mr-1" />
                                      Context Used
                                    </Badge>
                                  )}
                                  <span>Cycles: {message.metadata.max_cycles}</span>
                                </div>
                              </div>
                            )}
                          </div>
                          {message.role === "user" && (
                            <Avatar className="h-9 w-9">
                              <AvatarFallback>U</AvatarFallback>
                            </Avatar>
                          )}
                        </div>
                      ))}
                      {sessionLoading && (
                        <div className="flex items-start gap-4">
                          <Avatar className="h-9 w-9">
                              <div className="flex h-full w-full items-center justify-center rounded-full bg-primary">
                                  <OceanusIcon className="h-5 w-5 text-primary-foreground"/>
                              </div>
                            </Avatar>
                            <div className="max-w-[75%] space-y-2 rounded-lg px-4 py-3 bg-secondary">
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Brain className="w-4 h-4 animate-pulse" />
                                <span>Multi-agent system processing...</span>
                              </div>
                              <Skeleton className="h-4 w-48" />
                              <Skeleton className="h-4 w-32" />
                            </div>
                        </div>
                      )}
                      {currentMessages.length === 0 && !sessionLoading && isLoaded && (
                         <div className="flex h-full items-center justify-center text-center">
                            <div className="space-y-4">
                              {!backendOnline && !checkingBackend && (
                                <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                                  <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                                    <WifiOff className="h-4 w-4" />
                                    <span className="font-medium">Backend Offline</span>
                                  </div>
                                  <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                                    The backend service is not responding. Please check if the backend is running on port 8000.
                                  </p>
                                </div>
                              )}
                              <div className="text-muted-foreground">
                                <h3 className="text-lg font-semibold mb-2">Welcome to Multi-Agent RAG</h3>
                                <p>Ask questions about oceanographic data, Argo floats, or regional patterns.</p>
                                <p className="text-sm mt-2">The system will remember our conversation and provide contextual responses.</p>
                              </div>
                              <div className="grid grid-cols-1 gap-2 max-w-md">
                                <Button 
                                  variant="outline" 
                                  className="text-left justify-start h-auto whitespace-normal p-3"
                                  onClick={() => handleExampleQuestionClick("Show me temperature measurements from float 7902073")}
                                >
                                  Show me temperature measurements from float 7902073
                                </Button>
                                <Button 
                                  variant="outline" 
                                  className="text-left justify-start h-auto whitespace-normal p-3"
                                  onClick={() => handleExampleQuestionClick("Compare patterns between Arabian Sea and Bay of Bengal")}
                                >
                                  Compare patterns between Arabian Sea and Bay of Bengal
                                </Button>
                                <Button 
                                  variant="outline" 
                                  className="text-left justify-start h-auto whitespace-normal p-3"
                                  onClick={() => handleExampleQuestionClick("Find unusual temperature inversions in the Bay of Bengal")}
                                >
                                  Find unusual temperature inversions in the Bay of Bengal
                                </Button>
                              </div>
                            </div>
                         </div>
                      )}
                    </>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
            <CardFooter className="border-t p-4">
              <form onSubmit={handleSubmit} className="flex w-full items-center gap-2">
                <Input
                  id="message"
                  placeholder={
                    !backendOnline && !checkingBackend 
                      ? "Backend offline - please start the backend service"
                      : "Ask about oceanographic data, floats, or patterns..."
                  }
                  className="flex-1"
                  autoComplete="off"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={sessionLoading || (!backendOnline && !checkingBackend)}
                />
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button type="submit" size="icon" disabled={sessionLoading || !input.trim() || (!backendOnline && !checkingBackend)}>
                      <Send className="h-4 w-4" />
                      <span className="sr-only">Send</span>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    Send message to multi-agent system
                  </TooltipContent>
                </Tooltip>
              </form>
              {currentSessionId && (
                <div className="text-xs text-muted-foreground mt-2 text-center">
                  Session: {currentSessionId.substring(0, 8)}... • Multi-agent RAG with memory
                </div>
              )}
            </CardFooter>
          </div>
        </Card>
      </div>
    </TooltipProvider>
  );
}
