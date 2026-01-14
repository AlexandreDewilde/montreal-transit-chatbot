"""
Chat service for handling Mistral AI interactions with tool calling
"""

import json
import logging
from pathlib import Path
from typing import List

from mistralai import Mistral

from tools import TOOLS, execute_tool


class ChatService:
    """Service for handling Mistral AI chat interactions with function calling"""

    def __init__(
        self,
        mistral_client: Mistral,
        model: str,
        max_iterations: int,
        prompt_file_path: Path,
        logger: logging.Logger,
    ):
        """
        Initialize ChatService

        Args:
            mistral_client: Mistral AI client instance
            model: Model name to use (e.g., "mistral-small-latest")
            max_iterations: Maximum number of tool calling iterations
            prompt_file_path: Path to system prompt file
            logger: Logger instance
        """
        self.client = mistral_client
        self.model = model
        self.max_iterations = max_iterations
        self.logger = logger

        # Load system prompt once at initialization
        self.logger.debug(f"Loading system prompt from {prompt_file_path}")
        with open(prompt_file_path) as f:
            self.system_prompt = f.read()
        self.logger.info(f"✅ System prompt loaded ({len(self.system_prompt)} characters)")

    def process_message(
        self,
        user_content: str,
        session_messages: List[dict],
    ) -> tuple[str, List[dict]]:
        """
        Process a user message through Mistral AI with tool calling

        Args:
            user_content: The user's message content
            session_messages: Conversation history for this session

        Returns:
            Tuple of (assistant's response content, list of new messages including tool calls/results)

        Raises:
            Exception: If Mistral API call fails
        """
        # Build Mistral messages with system prompt
        mistral_messages = self._build_mistral_messages(session_messages)

        # Track new messages to store in session (tool calls + results)
        new_session_messages = []

        # Call Mistral API with tools - loop to handle multiple rounds of tool calls
        response = self.client.chat.complete(
            model=self.model,
            messages=mistral_messages,
            tools=TOOLS,
        )

        # Loop to handle multiple rounds of tool calls
        for iteration in range(1, self.max_iterations + 1):
            assistant_message_obj = response.choices[0].message

            # Check if model wants to call tools
            if not assistant_message_obj.tool_calls:
                # No more tool calls, we're done
                self.logger.debug("No more tool calls requested. Iteration complete.")
                break

            self.logger.info(
                f"🔄 Iteration {iteration}: Model requested {len(assistant_message_obj.tool_calls)} tool call(s)"
            )

            # Add assistant's tool call message to conversation
            tool_call_message = {
                "role": "assistant",
                "content": assistant_message_obj.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_message_obj.tool_calls
                ],
            }
            mistral_messages.append(tool_call_message)
            new_session_messages.append(tool_call_message)  # Store for session history

            # Execute each tool call
            for tool_call in assistant_message_obj.tool_calls:
                # Parse arguments
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"⚠️  Failed to parse tool arguments: {e}")
                    arguments = {}

                # Log tool call details
                self.logger.info(f"📞 Calling tool: {tool_call.function.name}")
                self.logger.debug(f"📋 Arguments: {json.dumps(arguments, indent=2)}")

                # Execute the tool
                tool_result = execute_tool(tool_call.function.name, arguments)

                # Log tool result (truncate if too long)
                result_str = json.dumps(tool_result, indent=2)
                if len(result_str) > 500:
                    self.logger.debug(f"✅ Result (truncated): {result_str[:500]}...")
                else:
                    self.logger.debug(f"✅ Result: {result_str}")

                # Add tool result to messages
                tool_message = {
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": json.dumps(tool_result),
                    "tool_call_id": tool_call.id,
                }
                mistral_messages.append(tool_message)
                new_session_messages.append(tool_message)  # Store for session history

            # Call Mistral again with tool results
            response = self.client.chat.complete(
                model=self.model,
                messages=mistral_messages,
                tools=TOOLS,
            )

        # Extract final assistant response
        assistant_content = response.choices[0].message.content

        # Add final assistant message to session messages
        final_message = {
            "role": "assistant",
            "content": assistant_content,
        }
        new_session_messages.append(final_message)

        self.logger.info(f"✅ Chat processing complete after {iteration} iteration(s)")
        return assistant_content, new_session_messages

    def _build_mistral_messages(self, session_messages: List[dict]) -> List[dict]:
        """
        Build Mistral API message list with system prompt

        Args:
            session_messages: Conversation history for this session

        Returns:
            List of messages formatted for Mistral API
        """
        mistral_messages = []

        # ALWAYS add system prompt to maintain context
        system_prompt = {"role": "system", "content": self.system_prompt}
        mistral_messages.append(system_prompt)

        # Add conversation history, preserving tool calls and tool results
        for msg in session_messages:
            # Build message with required fields
            mistral_msg = {"role": msg["role"], "content": msg["content"]}

            # Preserve tool_calls if present (assistant messages with function calls)
            if "tool_calls" in msg:
                mistral_msg["tool_calls"] = msg["tool_calls"]

            # Preserve tool-specific fields (tool result messages)
            if msg["role"] == "tool":
                if "name" in msg:
                    mistral_msg["name"] = msg["name"]
                if "tool_call_id" in msg:
                    mistral_msg["tool_call_id"] = msg["tool_call_id"]

            mistral_messages.append(mistral_msg)

        return mistral_messages
