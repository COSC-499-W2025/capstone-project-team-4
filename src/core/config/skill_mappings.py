"""
Language configuration loader with caching.
Loads complete language configuration from YAML file for better maintainability.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Any

# Cache for loaded configuration
_config_cache = None

def get_language_config() -> Dict[str, Any]:
    """
    Load complete language configuration from YAML file with caching
    
    Returns:
        Dict containing all language configuration data
    """
    global _config_cache
    
    if _config_cache is None:
        config_path = Path(__file__).parent / 'language_config.yml'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                _config_cache = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Language config file not found at {config_path}")
            _config_cache = {}
        except yaml.YAMLError as e:
            print(f"Error parsing language config YAML: {e}")
            _config_cache = {}
    
    return _config_cache

def get_language_skills() -> Dict[str, List[str]]:
    """Get language to skills mapping."""
    config = get_language_config()
    return config.get('language_skills', {})

def get_extensions() -> Dict[str, str]:
    """Get file extension to language mapping."""
    config = get_language_config()
    return config.get('extensions', {})

def get_special_files() -> Dict[str, str]:
    """Get special filename to language mapping."""
    config = get_language_config()
    return config.get('special_files', {})

def get_skip_patterns() -> Dict[str, List[str]]:
    """Get file patterns to skip during analysis."""
    config = get_language_config()
    return config.get('skip_patterns', {})

def clear_cache():
    """Clear the configuration cache (useful for testing)."""
    global _config_cache
    _config_cache = None