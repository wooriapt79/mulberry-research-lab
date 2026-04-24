"""
Audio Analyzer Module

This module is responsible for analyzing musical signals (tempo, energy, lyrics, structure)
and mapping them to agent triggers for synchronization.
"""

import logging

logger = logging.getLogger(__name__)

def analyze_music(audio_data, config=None):
    """Analyzes audio data to extract musical features.
    :param audio_data: Raw audio input data.
    :param config: Configuration for audio analysis.
                   Expected keys: 'analysis_params' (e.g., 'tempo_sensitivity', 'energy_threshold')
    """
    logger.info(f"Analyzing audio data: {audio_data}")

    # Extract analysis parameters from config, with defaults
    analysis_params = config.get('analysis_params', {}) if config else {}
    tempo_sensitivity = analysis_params.get('tempo_sensitivity', 1.0)
    energy_threshold = analysis_params.get('energy_threshold', 1.0)

    # Placeholder for actual analysis logic using config
    # Adjust musical_data values based on config parameters
    musical_features = {
        'tempo': audio_data.get('tempo', 0) * tempo_sensitivity,
        'energy': audio_data.get('energy', 0) * energy_threshold,
        'rhythm_pattern': audio_data.get('rhythm_pattern', 'unknown')
    }
    logger.info(f"Musical features generated with config: {musical_features}")
    return musical_features

def map_to_triggers(musical_features, config=None):
    """Maps extracted musical features to agent synchronization triggers.
    :param musical_features: Extracted musical features.
    :param config: Configuration for trigger mapping.
                   Expected keys: 'trigger_params' (e.g., 'trigger_type', 'sensitivity', 'rhythm_pattern_mapping')
    """
    logger.info(f"Mapping musical features to triggers: {musical_features}")

    # Extract trigger parameters from config, with defaults
    trigger_params = config.get('trigger_params', {}) if config else {}
    trigger_type = trigger_params.get('trigger_type', 'tempo_sync')

    # Validate and get sensitivity
    sensitivity = trigger_params.get('sensitivity', 1.0)
    if not isinstance(sensitivity, (int, float)) or sensitivity <= 0:
        logger.warning(f"Invalid sensitivity value '{sensitivity}' in config. Using default 1.0.")
        sensitivity = 1.0

    # Handle invalid musical_features input
    if not isinstance(musical_features, dict) or not musical_features:
        return {'type': 'default_sync', 'value': 1.0 * sensitivity}

    trigger_value = 1.0 * sensitivity # Default value before specific logic, scaled by sensitivity
    output_trigger_type = 'default_sync' # Default output type

    # Logic for different trigger types
    if trigger_type == 'tempo_sync':
        tempo = musical_features.get('tempo', 0.0)
        if isinstance(tempo, (int, float)):
            trigger_value = (tempo / 60.0) * sensitivity
            output_trigger_type = 'tempo_sync'
        else:
            logger.warning(f"Invalid 'tempo' value '{tempo}' in musical_features for tempo_sync. Falling back to default.")
    elif trigger_type == 'energy_sync':
        energy = musical_features.get('energy', 0.0)
        if isinstance(energy, (int, float)):
            trigger_value = energy * sensitivity
            output_trigger_type = 'energy_sync'
        else:
            logger.warning(f"Invalid 'energy' value '{energy}' in musical_features for energy_sync. Falling back to default.")
    elif trigger_type == 'rhythm_pattern_sync':
        pattern = musical_features.get('rhythm_pattern', 'unknown')
        rhythm_mapping = trigger_params.get('rhythm_pattern_mapping', {})
        if isinstance(rhythm_mapping, dict):
            mapped_value = rhythm_mapping.get(pattern, 1.0)
            if isinstance(mapped_value, (int, float)):
                trigger_value = mapped_value * sensitivity
                output_trigger_type = 'rhythm_pattern_sync'
            else:
                 logger.warning(f"Invalid mapped_value '{mapped_value}' for pattern '{pattern}'. Falling back to default.")
        else:
            logger.warning(f"Invalid 'rhythm_pattern_mapping' in config. Falling back to default.")
    else:
        logger.warning(f"Unrecognized trigger_type '{trigger_type}' in config. Falling back to default.")

    return {'type': output_trigger_type, 'value': trigger_value}
