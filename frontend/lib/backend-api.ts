  /**
   * Service for communicating with the Multi-Agent RAG FastAPI backend
   */
  export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
  }

  export interface ChatRequest {
    query: string;
    session_id?: string;
    timeout?: number;
    user_preferences?: Record<string, any>;
  }

  export interface ChatResponse {
    response: string;
    agents_used: string[];
    execution_time: number;
    session_id: string;
    status: string;
  }

  export interface SessionCreateRequest {
    user_preferences?: Record<string, any>;
  }

  export interface SessionResponse {
    session_id: string;
    message: string;
  }

  export interface ConversationHistoryResponse {
    session_id: string;
    conversation_history: Array<{
      role: string;
      content: string;
    }>;
    message_count: number;
  }

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  export class BackendApiService {
    private baseUrl: string;

    constructor(baseUrl: string = BACKEND_URL) {
      this.baseUrl = baseUrl;
    }

    /**
     * Create a new conversation session
     */
    async createSession(userPreferences?: Record<string, any>): Promise<SessionResponse> {
      try {
        console.log('Creating new session with preferences:', userPreferences);

        const response = await fetch(`${this.baseUrl}/session/create`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ user_preferences: userPreferences }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Session creation error:', errorText);
          throw new Error(`Failed to create session: ${response.status}`);
        }

        const data: SessionResponse = await response.json();
        console.log('Created session:', data);
        return data;
      } catch (error) {
        console.error('Error creating session:', error);
        throw new Error(`Failed to create session: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    /**
     * Send a chat message to the backend with session support
     */
    async sendChatMessage(
      query: string,
      sessionId?: string,
      userPreferences?: Record<string, any>
    ): Promise<ChatResponse> {
      try {
        console.log('Sending chat message:', { query: query.substring(0, 100), sessionId, userPreferences });

        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };

        if (sessionId) {
          headers['X-Session-ID'] = sessionId;
        }

        const response = await fetch(`${this.baseUrl}/query`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ query }),
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
          const errorData = await response.json().catch(() => null);
          console.error('Chat error response:', errorData);

          if (response.status === 404 && errorData?.detail?.includes('Session not found')) {
            throw new Error('SESSION_EXPIRED');
          }

          throw new Error(errorData?.detail || `HTTP error! status: ${response.status}`);
        }

        const data: ChatResponse = await response.json();
        console.log('Chat response received:', {
          sessionId: data.session_id,
          responseLength: data.response.length,
          agentsUsed: data.agents_used,
          executionTime: data.execution_time,
        });

        return data;
      } catch (error) {
        console.error('Error sending chat message:', error);

        if (error instanceof Error && error.name === 'AbortError') {
          throw new Error('Request was cancelled or timed out');
        }

        throw error;
      }
    }

    /**
     * Get conversation history for a session
     */
    async getConversationHistory(sessionId: string, limit?: number): Promise<ConversationHistoryResponse> {
      try {
        const url = new URL(`${this.baseUrl}/session/${sessionId}/history`);
        if (limit) {
          url.searchParams.set('limit', limit.toString());
        }

        const response = await fetch(url.toString());

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`Session not found: 404`);
          }
          throw new Error(`Failed to get conversation history: ${response.status}`);
        }

        const data: ConversationHistoryResponse = await response.json();
        return data;
      } catch (error) {
        console.error('Error getting conversation history:', error);
        throw error;
      }
    }

    /**
     * Delete a session
     */
    async deleteSession(sessionId: string): Promise<void> {
      try {
        const response = await fetch(`${this.baseUrl}/session/${sessionId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`Session not found: 404`);
          }
          throw new Error(`Failed to delete session: ${response.status}`);
        }
      } catch (error) {
        console.error('Error deleting session:', error);
        throw error;
      }
    }

    /**
     * Check if the backend is healthy
     */
    async healthCheck(): Promise<boolean> {
      try {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.ok;
      } catch (error) {
        console.error('Backend health check failed:', error);
        return false;
      }
    }
  }

  // Export a singleton instance
  export const backendApi = new BackendApiService();
