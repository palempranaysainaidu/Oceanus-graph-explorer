"use client";
import { useState, useEffect } from "react";
import { v4 as uuidv4 } from 'uuid';
import { backendApi, ChatResponse } from "@/lib/backend-api";

export interface Session {
  id: string;
  name: string;
  created_at: string;
  last_activity: string;
  message_count: number;
  context?: {
    regions_discussed: string[];
    floats_analyzed: string[];
    parameters_of_interest: string[];
  };
}

export interface SessionMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  metadata?: any;
}

const SESSIONS_KEY = "oceanus-sessions";
const CURRENT_SESSION_KEY = "oceanus-current-session";

export const useSessionManager = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentMessages, setCurrentMessages] = useState<SessionMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load sessions from localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        const savedSessions = localStorage.getItem(SESSIONS_KEY);
        const savedCurrentSession = localStorage.getItem(CURRENT_SESSION_KEY);
        if (savedSessions) {
          const parsedSessions = JSON.parse(savedSessions);
          setSessions(parsedSessions);
        }
        if (savedCurrentSession) {
          setCurrentSessionId(savedCurrentSession);
        }
      } catch (error) {
        console.error("Failed to load sessions:", error);
        // Clear corrupted data
        localStorage.removeItem(SESSIONS_KEY);
        localStorage.removeItem(CURRENT_SESSION_KEY);
      } finally {
        setIsLoaded(true);
      }
    }
  }, []);

  // Save sessions to localStorage whenever they change
  useEffect(() => {
    if (isLoaded && typeof window !== "undefined") {
      try {
        localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
      } catch (error) {
        console.error("Failed to save sessions:", error);
      }
    }
  }, [sessions, isLoaded]);

  // Save current session ID to localStorage
  useEffect(() => {
    if (isLoaded && typeof window !== "undefined") {
      if (currentSessionId) {
        localStorage.setItem(CURRENT_SESSION_KEY, currentSessionId);
      } else {
        localStorage.removeItem(CURRENT_SESSION_KEY);
      }
    }
  }, [currentSessionId, isLoaded]);

  // Load messages for current session
  useEffect(() => {
    if (currentSessionId && isLoaded) {
      loadSessionMessages(currentSessionId);
    } else {
      setCurrentMessages([]);
    }
  }, [currentSessionId, isLoaded]);

  const loadSessionMessages = async (sessionId: string) => {
    try {
      setIsLoading(true);
      const history = await backendApi.getConversationHistory(sessionId);

      // Check if history and conversation_history exist
      if (!history || !history.conversation_history) {
        console.error("Invalid history structure:", history);
        setCurrentMessages([]);
        return;
      }

      // Map the conversation_history to the expected format
      const messages: SessionMessage[] = history.conversation_history.map((msg) => ({
        id: msg.id || uuidv4(), // Use a unique ID if not provided
        role: msg.role as "user" | "assistant",
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString(), // Add timestamp if not provided
        metadata: msg.metadata,
      }));

      setCurrentMessages(messages);
    } catch (error) {
      console.error("Failed to load session messages:", error);
      // If session doesn't exist on backend, remove it from local storage and clear current session
      if (error instanceof Error && error.message.includes('404')) {
        console.log(`Session ${sessionId} not found on backend, removing from local storage`);
        removeSession(sessionId);
        setCurrentMessages([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const createNewSession = async (userPreferences?: Record<string, any>) => {
    try {
      setIsLoading(true);
      // Create session on backend
      const sessionResponse = await backendApi.createSession(userPreferences);
      // Create local session object
      const newSession: Session = {
        id: sessionResponse.session_id,
        name: `Chat ${new Date().toLocaleDateString()}`,
        created_at: new Date().toISOString(),
        last_activity: new Date().toISOString(),
        message_count: 0,
      };
      // Add to sessions list
      setSessions(prev => [newSession, ...prev]);
      // Set as current session
      setCurrentSessionId(sessionResponse.session_id);
      setCurrentMessages([]);
      return sessionResponse.session_id;
    } catch (error) {
      console.error("Failed to create new session:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const switchToSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
  };

  const removeSession = (sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null);
      setCurrentMessages([]);
    }
    // Also delete from backend (but don't throw error if it doesn't exist)
    backendApi.deleteSession(sessionId).catch(error => {
      // Only log if it's not a 404 error (session already doesn't exist)
      if (!error.message.includes('404')) {
        console.error("Failed to delete session from backend:", error);
      }
    });
  };

  const sendMessage = async (query: string, userPreferences?: Record<string, any>): Promise<ChatResponse> => {
    try {
      setIsLoading(true);
      // If no current session, create one
      let sessionId = currentSessionId;
      if (!sessionId) {
        sessionId = await createNewSession(userPreferences);
      }
      // Send message to backend
      const response = await backendApi.sendChatMessage(query, sessionId, userPreferences);
      // Add messages to current messages
      const userMessage: SessionMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: query,
        timestamp: new Date().toISOString(),
      };
      const assistantMessage: SessionMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        metadata: response.metadata,
      };
      setCurrentMessages(prev => [...prev, userMessage, assistantMessage]);
      // Update session info
      setSessions(prev => prev.map(session =>
        session.id === response.session_id
          ? {
            ...session,
            last_activity: new Date().toISOString(),
            message_count: session.message_count + 2,
            context: response.conversation_context,
            name: session.message_count === 0 ? generateSessionName(query) : session.name
          }
          : session
      ));
      return response;
    } catch (error) {
      console.error("Failed to send message:", error);
      // Handle session expiration
      if (error instanceof Error && error.message === 'SESSION_EXPIRED') {
        // Remove expired session and create new one
        if (currentSessionId) {
          removeSession(currentSessionId);
        }
        // Retry with new session
        const newSessionId = await createNewSession(userPreferences);
        return await backendApi.sendChatMessage(query, newSessionId, userPreferences);
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const generateSessionName = (firstMessage: string): string => {
    // Generate a meaningful name from the first message
    const words = firstMessage.split(' ').slice(0, 4);
    return words.join(' ') + (firstMessage.split(' ').length > 4 ? '...' : '');
  };

  const clearAllSessions = () => {
    setSessions([]);
    setCurrentSessionId(null);
    setCurrentMessages([]);
    if (typeof window !== "undefined") {
      localStorage.removeItem(SESSIONS_KEY);
      localStorage.removeItem(CURRENT_SESSION_KEY);
    }
  };

  const updateSessionPreferences = async (preferences: Record<string, any>) => {
    if (!currentSessionId) return;
    try {
      await backendApi.updateUserPreferences(currentSessionId, preferences);
    } catch (error) {
      console.error("Failed to update session preferences:", error);
      // If session doesn't exist, remove it
      if (error instanceof Error && error.message.includes('404')) {
        removeSession(currentSessionId);
      }
      throw error;
    }
  };

  const validateAndCleanupSessions = async () => {
    if (sessions.length === 0) return;
    // First check if backend is healthy
    try {
      const isHealthy = await backendApi.healthCheck();
      if (!isHealthy) {
        console.log('Backend is not healthy, skipping session validation');
        return;
      }
    } catch (error) {
      console.log('Backend health check failed, skipping session validation');
      return;
    }
    const validSessions: Session[] = [];
    for (const session of sessions) {
      try {
        await backendApi.getSessionInfo(session.id);
        validSessions.push(session);
      } catch (error) {
        if (error instanceof Error && error.message.includes('404')) {
          console.log(`Removing invalid session: ${session.id}`);
        } else {
          // Keep session if it's a network error (backend might be down)
          validSessions.push(session);
        }
      }
    }
    if (validSessions.length !== sessions.length) {
      console.log(`Cleaned up ${sessions.length - validSessions.length} invalid sessions`);
      setSessions(validSessions);
      // If current session was removed, clear it
      if (currentSessionId && !validSessions.find(s => s.id === currentSessionId)) {
        setCurrentSessionId(null);
        setCurrentMessages([]);
      }
    }
  };

  return {
    sessions,
    currentSessionId,
    currentMessages,
    isLoading,
    isLoaded,
    createNewSession,
    switchToSession,
    removeSession,
    sendMessage,
    clearAllSessions,
    updateSessionPreferences,
    validateAndCleanupSessions,
  };
};
