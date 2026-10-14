"""
Configuration Manager - Load and manage application configuration
Supports: config file, environment variables, CLI arguments
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manage application configuration from multiple sources."""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize config manager."""
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        return self.config
    
    def save_config(self) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self.config.get("llm", {})
    
    def get_supported_providers(self) -> Dict[str, Any]:
        """Get all supported providers."""
        return self.config.get("supported_providers", {})
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        return self.get_supported_providers().get(provider, {})
    
    def get_provider_models(self, provider: str) -> list:
        """Get available models for a provider."""
        return self.get_provider_config(provider).get("models", [])
    
    def update_llm_config(self, provider: str, model: str, **kwargs) -> None:
        """Update LLM configuration."""
        self.config["llm"] = {
            "provider": provider,
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "api_key_env": self.get_provider_config(provider).get("api_key_env")
        }
        if provider == "ollama":
            self.config["llm"]["base_url"] = kwargs.get(
                "base_url", 
                self.get_provider_config(provider).get("base_url")
            )
    
    def validate_api_key(self, provider: str) -> bool:
        """Check if API key is available for provider."""
        provider_config = self.get_provider_config(provider)
        
        if provider == "ollama":
            # Ollama doesn't need API key
            return True
        
        api_key_env = provider_config.get("api_key_env")
        if not api_key_env:
            return False
        
        return bool(os.environ.get(api_key_env, "").strip())

    def validate_llm_selection(self, provider: str, model: str) -> None:
        """Raise a clear error when the selected provider or model is not configured."""
        provider_config = self.get_provider_config(provider)
        if not provider_config:
            supported = ", ".join(self.get_supported_providers()) or "none"
            raise ValueError(f"LLM provider '{provider}' is not configured. Available providers: {supported}.")

        models = self.get_provider_models(provider)
        if not models:
            raise ValueError(f"No models are configured for provider '{provider}' in config.json.")
        if model not in models:
            raise ValueError(
                f"Model '{model}' is not configured for {provider}. Available models: {', '.join(models)}."
            )

        api_key_env = provider_config.get("api_key_env")
        if api_key_env and not self.validate_api_key(provider):
            raise ValueError(
                f"{provider.upper()} is not configured: set {api_key_env} in .env or the environment."
            )


def parse_cli_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-LLM MCP Host with configurable providers"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        choices=["gemini", "openai", "anthropic", "ollama"],
        help="LLM provider (default: from config)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name (default: from config)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Temperature for LLM (0.0-1.0, default: 0.7)"
    )
    
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Maximum tokens in response (default: 2048)"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Base URL for Ollama (default: http://localhost:11434)"
    )
    
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show current configuration and exit"
    )
    
    return parser.parse_args()


def display_config_menu(config_manager: ConfigManager) -> tuple:
    """
    Display interactive menu to select LLM configuration.
    Returns: (provider, model, temperature, max_tokens, base_url)
    """
    supported_providers = config_manager.get_supported_providers()
    current_llm = config_manager.get_llm_config()
    providers_list = list(supported_providers)

    if not providers_list:
        raise ValueError("No LLM providers are configured in config.json.")
    
    print("\n" + "="*70)
    print("🔧 LLM CONFIGURATION MENU")
    print("="*70)
    
    # Step 1: Select Provider
    print("\n📦 Select LLM Provider:")
    for i, provider in enumerate(providers_list, 1):
        config = supported_providers[provider]
        is_current = "✓ " if current_llm.get("provider") == provider else "  "
        print(f"{is_current}{i}. {provider.upper()} - {config['description']}")
    
    default_provider = current_llm.get("provider")
    if default_provider not in supported_providers:
        default_provider = providers_list[0]

    while True:
        provider_choice = input(
            f"\nEnter choice (1-{len(providers_list)}, or provider name; "
            f"default {default_provider}): "
        ).strip().lower()
        if not provider_choice:
            provider = default_provider
        elif provider_choice.isdigit() and 1 <= int(provider_choice) <= len(providers_list):
            provider = providers_list[int(provider_choice) - 1]
        elif provider_choice in supported_providers:
            provider = provider_choice
        else:
            print(f"⚠️  Unknown provider '{provider_choice}'. Choose from: {', '.join(providers_list)}.")
            continue
        break
    
    # Step 2: Select Model
    print(f"\n📋 Available models for {provider.upper()}:")
    available_models = config_manager.get_provider_models(provider)
    if not available_models:
        raise ValueError(f"No models are configured for provider '{provider}'. Check config.json.")

    current_model = current_llm.get("model") if current_llm.get("provider") == provider else None
    
    for i, model in enumerate(available_models, 1):
        is_current = "✓ " if model == current_model else "  "
        print(f"{is_current}{i}. {model}")
    
    default_model = current_model if current_model in available_models else available_models[0]
    while True:
        model_choice = input(
            f"\nEnter choice (1-{len(available_models)}, or model name; "
            f"default {default_model}): "
        ).strip()
        if not model_choice:
            model = default_model
        elif model_choice.isdigit() and 1 <= int(model_choice) <= len(available_models):
            model = available_models[int(model_choice) - 1]
        elif model_choice in available_models:
            model = model_choice
        else:
            print(f"⚠️  Unknown model '{model_choice}'. Choose from: {', '.join(available_models)}.")
            continue
        break
    
    # Step 3: Select Temperature
    print("\n🌡️  Select Temperature (creativity level):")
    print("1. 0.3 (precise, deterministic)")
    print("2. 0.7 (default, balanced)")
    print("3. 1.0 (creative, variable)")
    
    temp_choice = input("\nEnter choice (1-3, default 2): ").strip() or "2"
    temps = {"1": 0.3, "2": 0.7, "3": 1.0}
    temperature = temps.get(temp_choice, 0.7)
    
    # Step 4: Ollama base URL (if applicable)
    base_url = None
    if provider == "ollama":
        print("\n🌐 Ollama Configuration:")
        default_url = "http://localhost:11434"
        base_url_input = input(f"Enter Ollama base URL (default: {default_url}): ").strip()
        base_url = base_url_input if base_url_input else default_url
    
    # Step 5: Verify API Key
    print("\n🔑 Verifying API Key...")
    if config_manager.validate_api_key(provider):
        print(f"✓ API key found for {provider.upper()}")
    else:
        if provider != "ollama":
            api_key_env = supported_providers[provider].get("api_key_env")
            print(f"⚠️  Warning: {api_key_env} environment variable not found")
            print(f"   Please set it before running the application")
    
    print("\n" + "="*70)
    print(f"✓ Selected: {provider.upper()} - {model} (temperature: {temperature})")
    print("="*70 + "\n")
    
    return provider, model, temperature, 2048, base_url


def display_current_config(config_manager: ConfigManager) -> None:
    """Display current configuration."""
    llm_config = config_manager.get_llm_config()
    
    print("\n" + "="*70)
    print("📊 CURRENT CONFIGURATION")
    print("="*70)
    print(f"Provider:      {llm_config.get('provider', 'gemini').upper()}")
    print(f"Model:         {llm_config.get('model', 'N/A')}")
    print(f"Temperature:   {llm_config.get('temperature', 0.7)}")
    print(f"Max Tokens:    {llm_config.get('max_tokens', 2048)}")
    
    if llm_config.get('provider') == 'ollama':
        print(f"Base URL:      {llm_config.get('base_url', 'http://localhost:11434')}")
    
    print("="*70 + "\n")
