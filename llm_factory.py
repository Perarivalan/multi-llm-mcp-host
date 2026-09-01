"""
LLM Factory - Create LLM clients based on provider
Supports: Gemini, OpenAI, Anthropic, Ollama
"""

import os
from typing import Any, Optional
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2048, **kwargs):
        """Initialize LLM client."""
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
    
    @abstractmethod
    def generate_content(self, prompt: str, tools: list = None) -> Any:
        """Generate content using the LLM."""
        pass


class GeminiClient(BaseLLMClient):
    """Google Gemini LLM Client."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2048, **kwargs):
        """Initialize Gemini client."""
        super().__init__(model, temperature, max_tokens, **kwargs)
        
        try:
            from google import genai
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set")
            self.client = genai.Client(api_key=api_key)
        except ImportError:
            raise ImportError("google-genai package not installed. Run: pip install google-genai")
    
    def generate_content(self, prompt: str, tools: list = None) -> Any:
        """Generate content using Gemini."""
        config = {
            "temperature": self.temperature,
        }
        
        if tools:
            config["tools"] = [{"function_declarations": tools}]
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        
        return response


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM Client."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2048, **kwargs):
        """Initialize OpenAI client."""
        super().__init__(model, temperature, max_tokens, **kwargs)
        
        try:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def generate_content(self, prompt: str, tools: list = None) -> Any:
        """Generate content using OpenAI."""
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        if tools:
            # Convert MCP tools to OpenAI format
            tools_formatted = []
            for tool in tools:
                tools_formatted.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    }
                })
            kwargs["tools"] = tools_formatted
        
        response = self.client.chat.completions.create(**kwargs)
        return response


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude LLM Client."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2048, **kwargs):
        """Initialize Anthropic client."""
        super().__init__(model, temperature, max_tokens, **kwargs)
        
        try:
            from anthropic import Anthropic
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def generate_content(self, prompt: str, tools: list = None) -> Any:
        """Generate content using Claude."""
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
        }
        
        if tools:
            # Convert MCP tools to Anthropic format
            tools_formatted = []
            for tool in tools:
                tools_formatted.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["parameters"],
                })
            kwargs["tools"] = tools_formatted
        
        response = self.client.messages.create(**kwargs)
        return response


class OllamaClient(BaseLLMClient):
    """Ollama Local LLM Client."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2048, 
                 base_url: str = "http://localhost:11434", **kwargs):
        """Initialize Ollama client."""
        super().__init__(model, temperature, max_tokens, **kwargs)
        
        try:
            import ollama
            self.client = ollama
            self.base_url = base_url
        except ImportError:
            raise ImportError("ollama package not installed. Run: pip install ollama")
    
    def generate_content(self, prompt: str, tools: list = None) -> Any:
        """Generate content using Ollama."""
        # Ollama doesn't have native tool support yet, so we'll use simple prompting
        if tools:
            tool_descriptions = "\n".join([
                f"- {tool['name']}: {tool['description']}"
                for tool in tools
            ])
            prompt = f"{prompt}\n\nAvailable tools:\n{tool_descriptions}"
        
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            temperature=self.temperature,
        )
        
        return response


class LLMFactory:
    """Factory to create LLM clients based on provider."""
    
    _clients = {
        "gemini": GeminiClient,
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "ollama": OllamaClient,
    }
    
    @classmethod
    def create_client(cls, provider: str, model: str, temperature: float = 0.7, 
                     max_tokens: int = 2048, **kwargs) -> BaseLLMClient:
        """
        Create an LLM client.
        
        Args:
            provider: LLM provider (gemini, openai, anthropic, ollama)
            model: Model name
            temperature: Temperature parameter
            max_tokens: Maximum tokens in response
            **kwargs: Additional arguments (e.g., base_url for Ollama)
        
        Returns:
            LLM client instance
        """
        provider_lower = provider.lower()
        
        if provider_lower not in cls._clients:
            raise ValueError(f"Unknown provider: {provider}. Supported: {list(cls._clients.keys())}")
        
        client_class = cls._clients[provider_lower]
        return client_class(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported providers."""
        return list(cls._clients.keys())
