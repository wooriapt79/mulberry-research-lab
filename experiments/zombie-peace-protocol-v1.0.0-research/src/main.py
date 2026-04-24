"""
main.py

This module serves as the main orchestration script for the Zombie Peace Protocol.
It integrates various components including audio analysis, LLM-driven peace message
extraction, agent protocol management, and real-time broadcasting to synchronize
agents and emit peace messages based on musical rhythms.
"""

import yaml
import os
import logging

# Configure basic logging for the entire application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import necessary modules
from src.audio.audio_analyzer import analyze_music, map_to_triggers
from src.llm.peace_llm import extract_peace_message, ethical_filter
from src.core.agent_protocol import BaseAgent, AgentProtocolManager
from src.broadcast.realtime_broadcast import establish_connection, broadcast_message, listen_for_messages, close_connection

CONFIG_FILE_PATH = "config/config.yaml"

def load_config(config_path):
    """Loads the configuration from a YAML file."""
    # Construct the full path relative to the project root or current working directory
    # Assuming the script is run from the project root or OUTPUT_DIR is defined correctly
    full_path = os.path.join(os.path.dirname(__file__), '..', config_path)
    try:
        with open(full_path, 'r') as file:
            config = yaml.safe_load(file)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Error: Config file not found at {full_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {full_path}: {e}")
        return None

def main():
    """Orchestrates the Zombie Peace Protocol research simulation."""
    logger.info("\n--- Starting Zombie Peace Protocol Simulation ---")

    # Load configuration
    config = load_config(CONFIG_FILE_PATH)
    if config is None:
        logger.error("Failed to load configuration. Exiting.")
        return

    # 1. Initialize AgentProtocolManager
    agent_manager = AgentProtocolManager()

    # 2. Register agents from config
    for agent_id, agent_config in config['agents'].items():
        agent_manager.register_agent(agent_id, agent_config['initial_spirit_score'])

    # 3. Simulate musical input from config
    musical_data = config['musical_data']
    logger.info(f"\nSimulating musical input: {musical_data}")

    # 4. Analyze music and map to triggers, passing config
    musical_features = analyze_music(musical_data, config=config.get('audio', {}))
    musical_triggers = map_to_triggers(musical_features, config=config.get('audio', {}))
    logger.info(f"Musical triggers generated: {musical_triggers}")

    # 5. Synchronize all agents
    agent_manager.synchronize_all_agents(musical_triggers)

    # 6. Load lyrics for LLM processing from config
    lyrics = config['text_content']['lyrics']
    logger.info(f"\nLyrics for LLM analysis: '{lyrics[:70]}...' ")

    # 7. Extract peace message using LLM, passing LLM config
    peace_message = extract_peace_message(lyrics, llm_config=config['llm'])
    logger.info(f"LLM extracted peace message: '{peace_message}'")

    # 8. Apply ethical filtering, passing ethical filter keywords
    filtered_message = ethical_filter(peace_message, ethical_keywords=config['llm']['ethical_filter_keywords'])
    logger.info(f"Ethically filtered message: '{filtered_message}'")

    # 9. Ethical agent selection from config
    min_spirit_score = config['protocol']['min_spirit_score']
    selected_agents = agent_manager.ethical_agent_selection(min_spirit_score)

    # 10. Agents emit peace messages
    logger.info("\nAgents emitting peace messages:")
    for agent_id in selected_agents:
        agent = agent_manager.get_agent(agent_id)
        if agent:
            agent.emit_peace_message(filtered_message)

    # 11. Establish real-time broadcast connection from config
    logger.info("\nEstablishing broadcast connection...")
    broadcast_config = config.get('broadcast', {})
    broadcast_server_url = broadcast_config.get('server_url', 'http://localhost:5000')
    
    # For simulation purposes, we won't actually start a server here.
    # In a real scenario, a Socket.IO server would be running.
    # establish_connection(broadcast_server_url) # This would attempt to connect
    logger.info(f"Simulating connection establishment to {broadcast_server_url}.")

    # 12. Broadcast peace message and selected agents
    broadcast_data = {'message': filtered_message, 'agents': selected_agents}
    broadcast_message('peace_broadcast', broadcast_data) # This will print a message if not connected

    # 13. Close broadcast connection
    logger.info("\nClosing broadcast connection...")
    # close_connection() # This would attempt to disconnect
    logger.info("Simulating connection closure.")

    logger.info("\n--- Zombie Peace Protocol Simulation Complete ---")


if __name__ == "__main__":
    main()
