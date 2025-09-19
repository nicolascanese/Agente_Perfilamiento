"""
Base agent class for Agente_Perfilamiento LangGraph agents.

This module provides the base functionality for all agent nodes,
following hexagonal architecture principles with separated concerns.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from agente_perfilamiento.domain.models.conversation_state import ConversationState
from agente_perfilamiento.infrastructure.config.settings import get_llm_model
from agente_perfilamiento.infrastructure.logging.logger import get_logger


class BaseAgent(ABC):
    """Base class for all LangGraph agent nodes."""

    def __init__(self, agent_name: str):
        """
        Initialize the base agent.

        Args:
            agent_name: Name of the agent (used for prompt loading)
        """
        self.agent_name = agent_name
        self.logger = get_logger(f"{__name__}.{agent_name}")
        self._prompt_template = None
        self._tools = []

    def load_prompt(self) -> str:
        """
        Load the prompt template for this agent from the prompts folder.

        Returns:
            str: The prompt template content
        """
        if self._prompt_template is None:
            prompt_path = Path(__file__).parent / "prompts" / f"{self.agent_name}.txt"
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self._prompt_template = f.read().strip()
                self.logger.info(f"Loaded prompt for {self.agent_name}")
            except FileNotFoundError:
                self.logger.error(f"Prompt file not found: {prompt_path}")
                self._prompt_template = (
                    f"You are a helpful assistant for {self.agent_name}."
                )
            except Exception as e:
                self.logger.error(f"Error loading prompt: {e}")
                self._prompt_template = (
                    f"You are a helpful assistant for {self.agent_name}."
                )

        return self._prompt_template

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """
        Get the tools available for this agent.

        Returns:
            List[BaseTool]: List of tools for this agent
        """
        pass

    def create_chat_prompt(
        self, additional_messages: Optional[List] = None
    ) -> ChatPromptTemplate:
        """
        Create the chat prompt template for this agent.

        Args:
            additional_messages: Additional message templates to include

        Returns:
            ChatPromptTemplate: The configured prompt template
        """
        system_prompt = self.load_prompt()

        messages = [
            ("system", system_prompt),
            ("human", "{user_message}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]

        if additional_messages:
            # Insert additional messages before the scratchpad
            messages = messages[:-1] + additional_messages + [messages[-1]]

        return ChatPromptTemplate.from_messages(messages)

    def execute_agent(self, state: ConversationState, **kwargs) -> str:
        """
        Execute the agent with the given state and parameters.

        Args:
            state: Current conversation state
            **kwargs: Additional parameters for agent execution

        Returns:
            str: Agent response
        """
        try:
            # Get tools and create agent
            tools = self.get_tools()

            # Build optional memory context as additional messages if available
            additional_msgs = None
            ctx = state.get("context_data") or {}
            window = ctx.get("short_term_memory") if isinstance(ctx, dict) else None
            if window:
                try:
                    lines = []
                    for item in window:
                        role = item.get("role", "?")
                        content = item.get("content", "")
                        lines.append(f"{role}: {content}")
                    memory_block = "\n".join(lines)
                    additional_msgs = [("system", f"Memoria reciente:\n{memory_block}")]
                except Exception:
                    additional_msgs = None

            chat_prompt = self.create_chat_prompt(additional_msgs)
            llm = get_llm_model()

            # Create and execute agent (provider-agnostic)
            agent = create_tool_calling_agent(llm, tools, chat_prompt)
            executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

            # Prepare input parameters
            input_params = {
                "user_message": state.get("input_usuario", ""),
                "id_user": state.get("id_user", ""),
                **kwargs,
            }

            response = executor.invoke(input_params)["output"].strip()
            self.logger.info(f"Agent {self.agent_name} executed successfully")

            return response

        except Exception as e:
            self.logger.error(f"Error executing agent {self.agent_name}: {e}")
            return self.get_fallback_response()

    @abstractmethod
    def get_fallback_response(self) -> str:
        """
        Get a fallback response when agent execution fails.

        Returns:
            str: Fallback response message
        """
        pass

    @abstractmethod
    def process(self, state: ConversationState) -> ConversationState:
        """
        Process the conversation state through this agent.

        Args:
            state: Current conversation state

        Returns:
            ConversationState: Updated conversation state
        """
        pass
