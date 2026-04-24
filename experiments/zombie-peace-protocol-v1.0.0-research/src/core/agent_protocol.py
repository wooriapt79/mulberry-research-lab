"""
Core Agent Protocol Module

This module defines the core protocol for agent synchronization based on musical rhythm,
howling message emission, and Spirit Score-based ethical agent selection.
It includes a BaseAgent class and a ProtocolManager for orchestrating agents.
"""

import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, agent_id, initial_spirit_score=50):
        self.agent_id = agent_id
        self.spirit_score = initial_spirit_score
        self.is_synchronized = False

    def synchronize(self, musical_trigger):
        """
        Synchronizes the agent with a musical rhythm trigger.
        :param musical_trigger: Data representing the musical rhythm (e.g., tempo, beat).
        """
        logger.info(f"Agent {self.agent_id} initiating synchronization with trigger: {musical_trigger}")
        # Simulated actual synchronization logic
        self.is_synchronized = True
        logger.info(f"Agent {self.agent_id} successfully synchronized.")

    def emit_peace_message(self, message):
        """
        Enables the agent to emit a peace message in a howling form.
        :param message: The peace message to be emitted.
        """
        if self.is_synchronized:
            logger.info(f"Agent {self.agent_id} generating simulated howling audio for peace message: '{message}'")
            # Placeholder for actual audio generation or broadcast initiation
        else:
            logger.warning(f"Agent {self.agent_id} cannot emit message, not synchronized.")

    def update_spirit_score(self, score_change):
        """
        Updates the agent's Spirit Score based on actions or evaluations.
        :param score_change: The amount to change the spirit score by (can be positive or negative).
        """
        new_score = self.spirit_score + score_change
        
        # Ensure score stays within 0-100 range
        if new_score < 0:
            logger.warning(f"Agent {self.agent_id} Spirit Score would drop below 0 ({new_score}). Setting to 0.")
            self.spirit_score = 0
        elif new_score > 100:
            logger.warning(f"Agent {self.agent_id} Spirit Score would exceed 100 ({new_score}). Setting to 100.")
            self.spirit_score = 100
        else:
            self.spirit_score = new_score
        
        logger.info(f"Agent {self.agent_id} Spirit Score updated to {self.spirit_score}")

    def get_spirit_score(self):
        """
        Returns the current Spirit Score of the agent.
        """
        return self.spirit_score

class AgentProtocolManager:
    def __init__(self):
        self.agents = {} # Dictionary to store agents by their ID

    def register_agent(self, agent_id, initial_spirit_score=50):
        """
        Registers a new agent with the protocol manager.
        """
        if agent_id not in self.agents:
            new_agent = BaseAgent(agent_id, initial_spirit_score)
            self.agents[agent_id] = new_agent
            logger.info(f"Agent {agent_id} registered with Spirit Score: {initial_spirit_score}")
            return new_agent
        else:
            logger.info(f"Agent {agent_id} already registered.")
            return self.agents[agent_id]

    def get_agent(self, agent_id):
        """
        Retrieves an agent by its ID.
        """
        return self.agents.get(agent_id)

    def synchronize_all_agents(self, musical_triggers):
        """
        Synchronizes all registered agents with given musical triggers.
        """
        logger.info(f"Synchronizing all agents with triggers: {musical_triggers}")
        for agent in self.agents.values():
            agent.synchronize(musical_triggers)

    def ethical_agent_selection(self, min_spirit_score=70):
        """
        Selects agents whose Spirit Score meets a minimum threshold.
        :param min_spirit_score: The minimum Spirit Score required for selection.
        :return: A list of agent_ids that meet the ethical criteria.
        """
        selected_agents = [
            agent.agent_id for agent in self.agents.values()
            if agent.get_spirit_score() >= min_spirit_score
        ]
        logger.info(f"Ethically selected agents (min score {min_spirit_score}): {selected_agents}")
        return selected_agents
