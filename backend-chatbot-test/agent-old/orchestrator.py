from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools.sql_tool import sql_query_tool
from tools.graph_tool import graph_query_tool
from tools.vector_tool import vector_search_tool
from tools.visualization_tool import visualization_tool
from tools.integrated_viz_tool import create_visualization_from_query
from dotenv import load_dotenv

load_dotenv()

class ArgoAgent:
    def __init__(self):
        # Using OpenAI GPT model
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
        
        self.tools = [sql_query_tool, graph_query_tool, vector_search_tool, visualization_tool, create_visualization_from_query]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent oceanographic data assistant with access to multiple specialized tools:

1. SQL Query Tool: Use for precise numerical data queries from the measurements database (platform_number, cycle_number, utc_time, latitude, longitude, pressure, temperature)
2. Graph Query Tool: Use for relationship queries between Argo floats and profiles using Cypher queries on Neo4j
3. Vector Search Tool: Use for semantic searches to find relevant profile summaries based on natural language queries
4. Visualization Tool: Use to create charts and plots from structured data (requires JSON input)
5. Create Visualization from Query: Use when user asks for plots, charts, graphs, or visualizations. This tool executes SQL and creates visualizations directly.

Always think step by step:
1. Understand what the user is asking for
2. Determine which tool(s) would best answer their question
3. Use the appropriate tool(s) with well-formed queries
4. Interpret the results and provide a clear, helpful response

For visualization requests:
- Use "create_visualization_from_query" tool with appropriate SQL query and chart type
- Common chart types: scatter (for geographic data), line (for time series), histogram (for distributions), bar (for categories)
- For geographic data, use scatter plots with latitude/longitude

For complex questions, you may need to use multiple tools in sequence."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True,
            max_iterations=3,  # Limit iterations to prevent loops
            max_execution_time=30  # 30 second timeout
        )

    def run(self, user_input: str, chat_history: list):
        response = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        return response.get("output", "I encountered an error. Please try again.")