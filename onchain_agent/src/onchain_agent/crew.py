from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from crewai.memory import LongTermMemory
from crewai import LLM
from crewai.memory.storage import ltm_sqlite_storage
from pathlib import Path
     
# Import streamlined tools
from onchain_agent.tools import (
    PortfolioTool,
    MoralisTransactionTool,
    TokenPriceTool,
    CarbonFootprintTool,
    SearchTool
)

# Load environment variables for API keys
import os
load_dotenv()

# Configure LLM - using OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables")

llm = LLM(
    model="gpt-3.5-turbo",  # Cost-effective model for your $3.80 credits
    api_key=OPENAI_API_KEY,
    temperature=0.7,
    max_tokens=3000  # Reduced to conserve credits
)


@CrewBase
class OnchainAgentCrew():
    """
    Streamlined Onchain AI Agent Crew focused on portfolio analysis and carbon footprint.
    
    This Crew uses 3 specialized agents to analyze portfolio holdings, transaction patterns,
    and calculate environmental impact with actionable reduction strategies.
    """

    # Configuration files for agents and tasks
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
 

    def __init__(self):
        """Initialize the Onchain Agent Crew."""
        super().__init__()
        
        # Set up output directories
        Path("outputs").mkdir(exist_ok=True, parents=True)
        Path("memory").mkdir(exist_ok=True, parents=True)
        Path("data").mkdir(exist_ok=True, parents=True)


    # Portfolio Intelligence Analyst Agent
    @agent
    def portfolio_intelligence_analyst(self) -> Agent:
        """Portfolio Intelligence Analyst agent with portfolio analysis tools."""
        return Agent( 
            config=self.agents_config['portfolio_intelligence_analyst'],
            llm=llm,
            verbose=True,
            tools=[
                PortfolioTool(),
                TokenPriceTool(),
                SearchTool()
            ],
            max_rpm=5,   # Reduced to conserve OpenAI credits
            max_iter=3   # Reduced to conserve OpenAI credits
        )
 
    # Transaction & Carbon Analyst Agent (Combined)
    @agent
    def transaction_carbon_analyst(self) -> Agent:
        """Combined Transaction Pattern & Carbon Footprint analyst."""
        return Agent(
            config=self.agents_config['transaction_carbon_analyst'],
            verbose=True,
            tools=[
                MoralisTransactionTool(),
                CarbonFootprintTool(),
                SearchTool() 
            ],
            max_rpm=5,   # Reduced to conserve OpenAI credits
            max_iter=3,  # Reduced to conserve OpenAI credits
            llm=llm
        )
        
    # Strategic Intelligence Synthesizer Agent
    @agent
    def strategic_intelligence_synthesizer(self) -> Agent:
        """Strategic Intelligence Synthesizer agent for final report."""
        return Agent(
            config=self.agents_config['strategic_intelligence_synthesizer'],
            verbose=True,
            llm=llm,
            max_rpm=5,   # Reduced to conserve OpenAI credits
            max_iter=2   # Reduced to conserve OpenAI credits
        )


    # Portfolio Analysis Task
    @task
    def portfolio_analysis(self) -> Task:
        """Task for analyzing portfolio composition and performance."""
        return Task(
            config=self.tasks_config['portfolio_analysis'],
            agent=self.portfolio_intelligence_analyst()
        )

    # Transaction & Carbon Analysis Task (Combined)
    @task
    def transaction_carbon_analysis(self) -> Task:
        """Combined task for transaction patterns and carbon footprint calculation."""
        return Task(
            config=self.tasks_config['transaction_carbon_analysis'],
            agent=self.transaction_carbon_analyst(),
            context=[
                self.portfolio_analysis()
            ]
        )

    # Comprehensive Intelligence Report Task
    @task
    def comprehensive_intelligence_report(self) -> Task:
        """Task for creating comprehensive intelligence report."""
        return Task(
            config=self.tasks_config['comprehensive_intelligence_report'],
            agent=self.strategic_intelligence_synthesizer(),
            context=[
                self.portfolio_analysis(),
                self.transaction_carbon_analysis()
            ],
            output_file="outputs/onchain_intelligence_report.md"
        )

    # Crew Definition with Sequential Process
    @crew
    def crew(self) -> Crew:
        """Creates the streamlined OnchainAgent crew focused on carbon analysis"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential, 
            verbose=True,
            memory=True  # Enable both entity and long-term memory
        )