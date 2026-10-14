import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from google.genai import types

from mcp_client import MCPClient
from config_manager import ConfigManager, parse_cli_args, display_config_menu, display_current_config
from llm_factory import LLMFactory


load_dotenv()


class LLMMCPHost:
    """Multi-LLM MCP Host - supports Gemini, OpenAI, Anthropic, Ollama."""

    def __init__(self, provider: str, model: str, temperature: float = 0.7, 
                 max_tokens: int = 2048, **kwargs):

        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Create LLM client based on provider
        self.llm = LLMFactory.create_client(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        self.mcp = MCPClient()
        self.conversation_history = []


    async def start(self):

        await self.mcp.connect()


    async def stop(self):

        await self.mcp.disconnect()


    async def run(self, user_question):
        """
        Run a question through the LLM with MCP tools.
        
        Note: Full multi-LLM tool calling support requires adapter logic
        for each provider's tool format. Currently demonstrated with Gemini.
        """

        # -----------------------------------------
        # 1. Get MCP tools
        # -----------------------------------------

        mcp_tools = await self.mcp.list_tools()

        print("\n✨ Available MCP tools:")

        for tool in mcp_tools:

            print(
                f"  • {tool.name}: "
                f"{tool.description}"
            )


        # -----------------------------------------
        # 2. Convert MCP tools to LLM format
        # -----------------------------------------

        llm_tools = []

        for tool in mcp_tools:

            llm_tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                }
            )


        # -----------------------------------------
        # 3. Send request to LLM
        # -----------------------------------------

        print(f"\n🤖 Using {self.provider.upper()} ({self.model})...")

        try:
            response = self.llm.generate_content(
                prompt=user_question,
                tools=llm_tools
            )
        except Exception as e:
            print(
                f"\n❌ Request failed for {self.provider.upper()} model '{self.model}'."
                f"\n   Details: {e}"
            )
            return


        # -----------------------------------------
        # 4. Process LLM response
        # -----------------------------------------

        # Handle different response formats based on provider
        response_text = self._extract_response_text(response)

        if not self._has_tool_calls(response):

            print("\n💡 Response:")
            print(f"{response_text}")
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_question
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            return


        # -----------------------------------------
        # 5. Execute tool calls
        # -----------------------------------------

        tool_results = []
        tool_calls = self._extract_tool_calls(response)

        for tool_call in tool_calls:

            tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
            tool_args = tool_call.get("arguments") or tool_call.get("function", {}).get("arguments", {})

            print(f"\n🔧 Tool: {tool_name}")
            if tool_args:
                print(f"📝 Arguments: {json.dumps(tool_args, indent=2)}")


            # ----------------------------------------
            # MCP CALL
            # ----------------------------------------

            try:
                result = await self.mcp.call_tool(tool_name, tool_args)

                result_text = ""
                for content in result.content:
                    if hasattr(content, "text"):
                        result_text += content.text

                print(f"📊 Result:\n{result_text}")

                # Format based on provider
                if self.provider == "gemini":
                    tool_results.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": result_text},
                        )
                    )
                else:
                    # For other providers, store for context
                    tool_results.append({
                        "tool_name": tool_name,
                        "result": result_text
                    })

            except Exception as e:
                print(f"❌ Error calling tool: {str(e)}")
                continue


        # -----------------------------------------
        # 6. Send results back to LLM
        # -----------------------------------------

        if self.provider == "gemini":
            # Gemini-specific multi-turn conversation
            try:
                final_response = self.llm.client.models.generate_content(
                    model=self.model,
                    contents=[
                        user_question,
                        response.candidates[0].content,
                        types.Content(
                            role="user",
                            parts=tool_results,
                        ),
                    ],
                    config={
                        "temperature": self.temperature,
                        "tools": [
                            {
                                "function_declarations": llm_tools
                            }
                        ]
                    },
                )
                final_text = final_response.text
            except Exception as e:
                print(
                    f"\n❌ {self.provider.upper()} model '{self.model}' failed while processing tool results."
                    f"\n   Details: {e}"
                )
                return
        else:
            # For other providers, create a follow-up prompt
            results_summary = "\n".join([
                f"Tool {r.get('tool_name', 'unknown')}: {r.get('result', '')}"
                for r in tool_results if isinstance(r, dict)
            ])
            
            follow_up_prompt = f"""
Based on these tool results:
{results_summary}

Provide analysis and answer the original question: {user_question}
"""
            
            try:
                follow_up_response = self.llm.generate_content(
                    prompt=follow_up_prompt,
                    tools=None
                )
                final_text = self._extract_response_text(follow_up_response)
            except Exception as e:
                print(
                    f"\n❌ {self.provider.upper()} model '{self.model}' failed while processing tool results."
                    f"\n   Details: {e}"
                )
                return

        print("\n✨ Analysis:")
        print(final_text)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_question
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": final_text
        })

    
    def _extract_response_text(self, response) -> str:
        """Extract text from response based on provider format."""
        if self.provider == "gemini":
            return getattr(response, "text", "")
        elif self.provider == "openai":
            return response.choices[0].message.content
        elif self.provider == "anthropic":
            return response.content[0].text
        elif self.provider == "ollama":
            return response.get("response", "")
        return str(response)
    
    def _has_tool_calls(self, response) -> bool:
        """Check if response contains tool calls."""
        if self.provider == "gemini":
            return bool(getattr(response, "function_calls", None))
        elif self.provider == "openai":
            return any(choice.message.tool_calls for choice in response.choices 
                      if hasattr(choice.message, "tool_calls"))
        elif self.provider == "anthropic":
            return any(block.type == "tool_use" for block in response.content)
        return False
    
    def _extract_tool_calls(self, response) -> list:
        """Extract tool calls from response based on provider format."""
        if self.provider == "gemini":
            return [{"name": call.name, "arguments": dict(call.args or {})} 
                   for call in getattr(response, "function_calls", [])]
        elif self.provider == "openai":
            calls = []
            for choice in response.choices:
                if hasattr(choice.message, "tool_calls"):
                    for call in choice.message.tool_calls:
                        calls.append({"function": {"name": call.function.name, "arguments": call.function.arguments}})
            return calls
        elif self.provider == "anthropic":
            return [{"name": block.name, "arguments": block.input} 
                   for block in response.content if block.type == "tool_use"]
        return []


def show_advanced_menu():
    """Display advanced options menu."""
    print("\n" + "="*70)
    print("⚙️  ADVANCED MENU")
    print("="*70)
    print("1. Change LLM provider or model")
    print("2. Adjust temperature")
    print("3. Back to chat")
    print("="*70)
    
    choice = input("\nEnter choice (1-3, default 3): ").strip() or "3"
    return choice


async def main():

    print("\n" + "="*70)
    print("🤖 MULTI-LLM MCP INTERACTIVE CHAT")
    print("="*70)
    
    # Parse command line arguments
    args = parse_cli_args()
    
    # Load configuration
    config_manager = ConfigManager()
    
    # Show configuration if requested
    if args.show_config:
        display_current_config(config_manager)
        return
    
    # Determine LLM configuration
    provider = args.provider or config_manager.get_llm_config().get("provider", "gemini")
    model = args.model or config_manager.get_llm_config().get("model", "gemini-3.5-flash-lite")
    temperature = args.temperature if args.temperature is not None else config_manager.get_llm_config().get("temperature", 0.7)
    max_tokens = args.max_tokens or config_manager.get_llm_config().get("max_tokens", 2048)
    
    # Show configuration menu if no args provided
    if not args.provider and not args.model:
        try:
            provider, model, temperature, max_tokens, base_url = display_config_menu(config_manager)
        except (ValueError, EOFError) as e:
            print(f"\n❌ LLM configuration error: {e}")
            return
        config_manager.update_llm_config(provider, model, temperature=temperature, max_tokens=max_tokens)
        if provider == "ollama" and base_url:
            config_manager.config["llm"]["base_url"] = base_url
    else:
        base_url = args.base_url or config_manager.get_llm_config().get("base_url", "http://localhost:11434")
    
    # Create host with selected configuration
    kwargs = {}
    if provider == "ollama" and base_url:
        kwargs["base_url"] = base_url
    
    try:
        config_manager.validate_llm_selection(provider, model)
        host = LLMMCPHost(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    except (ValueError, ImportError) as e:
        print(f"\n❌ LLM configuration error: {e}")
        return
    except Exception as e:
        print(
            f"\n❌ Could not initialize {provider.upper()} model '{model}'."
            f"\n   Details: {e}"
        )
        return

    try:

        await host.start()
        print("\n✓ MCP Server connected successfully!\n")

        while True:
            
            question = input("\n🤖 Ask a question (or 'quit' to exit, 'config' for settings, 'history' to view): ").strip()
            
            if question.lower() == "quit":
                print("\n👋 Goodbye!")
                break
            
            if question.lower() == "config":
                choice = show_advanced_menu()
                if choice == "1":
                    try:
                        provider, model, temperature, max_tokens, base_url = display_config_menu(config_manager)
                    except (ValueError, EOFError) as e:
                        print(f"\n❌ LLM configuration error: {e}")
                        continue
                    kwargs = {}
                    if provider == "ollama" and base_url:
                        kwargs["base_url"] = base_url
                    try:
                        config_manager.validate_llm_selection(provider, model)
                        new_host = LLMMCPHost(
                            provider=provider,
                            model=model,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            **kwargs
                        )
                        await new_host.start()
                    except Exception as e:
                        print(f"\n❌ Reconfiguration failed: {e}")
                        print("   The current LLM configuration has been kept.\n")
                        continue
                    await host.stop()
                    host = new_host
                    config_manager.update_llm_config(provider, model, temperature=temperature, max_tokens=max_tokens)
                    print("✓ Host reconfigured!\n")
                elif choice == "2":
                    temp_choice = input("\nEnter temperature (0.0-1.0): ").strip()
                    try:
                        host.temperature = float(temp_choice)
                        print(f"✓ Temperature updated to {host.temperature}")
                    except ValueError:
                        print("⚠️  Invalid temperature value")
                continue
            
            if question.lower() == "history":
                print("\n" + "="*70)
                print("📜 CONVERSATION HISTORY")
                print("="*70)
                if not host.conversation_history:
                    print("No conversation history yet.")
                else:
                    for msg in host.conversation_history:
                        role = "👤 You" if msg["role"] == "user" else "🤖 LLM"
                        print(f"\n{role}:")
                        print(msg["content"])
                print("\n" + "="*70)
                continue
            
            if not question:
                print("⚠️  Please enter a question.")
                continue

            await host.run(question)

    except Exception as e:
        print(f"\n❌ Host or MCP server error: {e}")
    finally:
        try:
            await host.stop()
        except Exception as e:
            print(f"\n⚠️  MCP cleanup warning: {e}")
        print("\n✓ MCP Server disconnected.")


if __name__ == "__main__":

    asyncio.run(main())