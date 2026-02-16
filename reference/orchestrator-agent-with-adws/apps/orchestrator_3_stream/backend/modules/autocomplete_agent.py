import json
import time
import uuid
from pathlib import Path
from typing import List, Optional

import yaml
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
)

from . import database
from .autocomplete_models import (
    AutocompleteExpertiseData,
    AutocompleteItem,
    PreviousCompletionAutocomplete,
    PreviousCompletionNone,
)

# Maximum number of codebase files to include in autocomplete context
# Captures all files from git but only sends first N to keep prompt size manageable
MAX_CODEBASE_FILES = 300


class AutocompleteAgent:
    """
    Autocomplete agent using Claude Agent SDK for session persistence.

    CRITICAL:
    - Uses Claude Agent SDK (not raw Anthropic client) for session management
    - Uses Pydantic models for type-safe expertise.yaml handling
    - All expertise_data access is type-checked via AutocompleteExpertiseData
    """

    def __init__(self, orchestrator_agent_id, logger, working_dir, ws_manager=None):
        self.orchestrator_agent_id = str(orchestrator_agent_id)
        self.logger = logger
        self.working_dir = working_dir
        self.ws_manager = ws_manager

        # Paths
        self.expertise_dir = (
            Path(__file__).parent.parent / "prompts/experts/orch_autocomplete"
        )
        self.expertise_yaml_path = self.expertise_dir / "expertise.yaml"
        self.system_prompt_path = (
            self.expertise_dir / "autocomplete_expert_system_prompt.md"
        )
        self.user_prompt_path = (
            self.expertise_dir / "autocomplete_expert_user_prompt.md"
        )

        # Ensure expertise directory exists
        self.expertise_dir.mkdir(parents=True, exist_ok=True)

        # Load prompts
        self.system_prompt_template = self._load_prompt_file(self.system_prompt_path)
        self.user_prompt_template = self._load_prompt_file(self.user_prompt_path)

        # Claude Agent SDK client (initialized after expertise check)
        self.client: Optional[ClaudeSDKClient] = None

        # CRITICAL: Type-safe expertise data (Pydantic model)
        self.expertise_data: AutocompleteExpertiseData

        # Interrupt support: Track active client and execution state
        self.active_client: Optional[ClaudeSDKClient] = None
        self.is_executing: bool = False

        # Cache for active agents (5-second TTL to avoid repeated DB queries)
        self._cached_agents: List[dict] = []
        self._cache_timestamp: float = 0
        self._cache_ttl: int = 5  # seconds

        # Cache for codebase structure (initialized once)
        self._codebase_structure: Optional[list] = None

        # Load expertise FIRST, then check if we need to reset
        self.expertise_data = self._load_or_init_expertise()

        # Initialize Claude Agent SDK with session resume if available
        self._init_claude_agent()

    def _load_prompt_file(self, path: Path) -> str:
        """Load prompt file, return empty string if not found"""
        if path.exists():
            return path.read_text()
        self.logger.warning(f"Prompt file not found: {path}, using placeholder")
        return ""

    def _load_or_init_expertise(self) -> AutocompleteExpertiseData:
        """
        STEP 1: Load expertise.yaml FIRST with type-safe Pydantic validation

        Returns:
            AutocompleteExpertiseData: Validated expertise data

        CRITICAL: Returns Pydantic model (not dict) for type safety
        """
        if not self.expertise_yaml_path.exists():
            self.logger.info("No expertise.yaml found, creating new")
            # Create new typed data
            new_data = AutocompleteExpertiseData(
                orchestrator_agent_id=self.orchestrator_agent_id,
                completion_agent_id=None,  # Will be set after first interaction
                previous_completions=[],
            )
            # Save initial file
            self._save_expertise_data(new_data)
            return new_data

        # Load YAML file
        with open(self.expertise_yaml_path, "r") as f:
            raw_data = yaml.safe_load(f)

        # CRITICAL: Validate with Pydantic (raises if invalid)
        try:
            expertise = AutocompleteExpertiseData.from_dict(raw_data)
        except Exception as e:
            self.logger.error(f"Invalid expertise.yaml format: {e}")
            self.logger.info("Creating fresh expertise.yaml")
            # Fallback to new data if YAML is corrupt
            new_data = AutocompleteExpertiseData(
                orchestrator_agent_id=self.orchestrator_agent_id,
                completion_agent_id=None,
                previous_completions=[],
            )
            self._save_expertise_data(new_data)
            return new_data

        # STEP 2: Check orchestrator_agent_id match
        if expertise.orchestrator_agent_id != self.orchestrator_agent_id:
            self.logger.info(
                f"Orchestrator changed: {expertise.orchestrator_agent_id} → {self.orchestrator_agent_id}"
            )
            self.logger.info("Resetting expertise.yaml (clearing history)")

            # STEP 3: Reset on orchestrator change
            new_data = AutocompleteExpertiseData(
                orchestrator_agent_id=self.orchestrator_agent_id,
                completion_agent_id=None,  # Clear old session
                previous_completions=[],  # Clear history
            )
            self._save_expertise_data(new_data)
            return new_data

        # Same orchestrator - keep everything
        self.logger.info(
            f"Resuming autocomplete session for orchestrator: {self.orchestrator_agent_id}"
        )
        return expertise

    def _init_claude_agent(self):
        """
        Initialize Claude Agent SDK client with session resume if available.

        If completion_agent_id exists in expertise.yaml, resume that session.
        Otherwise, start fresh and capture session_id after first interaction.
        """
        self.logger.info("Initializing Claude Agent SDK client...")

        # CRITICAL: Type-safe access via Pydantic model
        completion_agent_id = self.expertise_data.completion_agent_id

        # Build placeholder system prompt for initialization
        placeholder_system_prompt = self._load_system_prompt_with_variables("")

        self.logger.debug(
            f"System prompt template loaded (length: {len(placeholder_system_prompt)} chars)"
        )

        # also save this to a file in the local temp directory up two directories
        # .parent - apps/orchestrator_3_stream/backend/modules/
        # .parent.parent - apps/orchestrator_3_stream/backend/
        # .parent.parent.parent - apps/orchestrator_3_stream/
        # .parent.parent.parent /temp - apps/orchestrator_3_stream/temp/
        temp_dir = Path(__file__).parent.parent.parent / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        with open(temp_dir / "autocomplete_expert_system_prompt.md", "w") as f:
            f.write(placeholder_system_prompt)
        self.logger.debug(f"Working directory: {self.working_dir}")

        # Build ClaudeAgentOptions
        options_dict = {
            "system_prompt": placeholder_system_prompt,
            "model": "claude-haiku-4-5-20251001",  # LATEST HAIKU MODEL
            "cwd": self.working_dir,
        }

        # Resume session if we have a completion_agent_id
        if completion_agent_id:
            options_dict["resume"] = completion_agent_id
            self.logger.info(
                f"Resuming Claude Agent SDK session: {completion_agent_id[:20]}..."
            )
        else:
            self.logger.info(
                "Starting fresh Claude Agent SDK session (no existing session_id)"
            )

        # Create client
        self.client = ClaudeSDKClient(ClaudeAgentOptions(**options_dict))
        self.logger.success("Claude Agent SDK client initialized successfully")

    def _save_expertise(self):
        """
        Save expertise data to YAML file with type safety.

        CRITICAL: Converts Pydantic model to dict for YAML serialization
        """
        self._save_expertise_data(self.expertise_data)

    def _save_expertise_data(self, data: AutocompleteExpertiseData):
        """Helper to save expertise data"""
        with open(self.expertise_yaml_path, "w") as f:
            yaml.dump(data.to_dict(), f, default_flow_style=False, sort_keys=False)

    async def _fetch_active_agents(self) -> List[dict]:
        """
        Fetch active agents from database with time-based caching.

        Cache TTL is 5 seconds to avoid repeated DB queries during debounce period.
        Returns list of dicts with agent info: {id, name, status}
        """
        current_time = time.time()

        # Return cached data if still valid
        if (
            self._cached_agents
            and (current_time - self._cache_timestamp) < self._cache_ttl
        ):
            cache_age = current_time - self._cache_timestamp
            self.logger.debug(
                f"Using cached agents (age: {cache_age:.1f}s, {len(self._cached_agents)} agents)"
            )
            return self._cached_agents

        # Fetch fresh data from database
        self.logger.info("Fetching active agents from database...")
        try:
            # Convert orchestrator_agent_id string to UUID
            orchestrator_uuid = uuid.UUID(self.orchestrator_agent_id)

            # Query active agents from database
            agents = await database.list_agents(orchestrator_uuid, archived=False)

            # Convert Agent Pydantic models to simple dicts for JSON serialization
            self._cached_agents = [
                {"id": str(agent.id), "name": agent.name, "status": agent.status}
                for agent in agents
            ]

            # Update cache timestamp
            self._cache_timestamp = current_time

            self.logger.info(
                f"Fetched {len(self._cached_agents)} active agents from database"
            )
            if self._cached_agents:
                agent_names = [agent["name"] for agent in self._cached_agents]
                self.logger.debug(f"Active agents: {', '.join(agent_names)}")

        except Exception as e:
            self.logger.error(f"Failed to fetch active agents: {e}")
            # Return empty list on error to avoid breaking autocomplete
            self._cached_agents = []

        return self._cached_agents

    def _get_codebase_structure(self) -> list:
        """
        Get codebase structure as flat list of file paths using git ls-files with caching.

        Uses git ls-files to get ALL tracked files (no limit on git command).
        Trims result to first MAX_CODEBASE_FILES (300) to keep prompt size manageable.
        Returns a simple list of file paths.

        Returns:
            List of file path strings (max 300), e.g. ["backend/main.py", "frontend/src/App.vue", ...]

        Fallback: If git is not available or not in a repo, uses directory scanning.
        """
        if self._codebase_structure is not None:
            self.logger.debug(
                f"Using cached codebase structure ({len(self._codebase_structure)} files)"
            )
            return self._codebase_structure

        self.logger.info("Loading codebase structure...")
        try:
            import subprocess

            # Get ALL files from git ls-files (no limits on git command)
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # Parse git ls-files output - get ALL files
                all_files = [
                    f.strip() for f in result.stdout.strip().split("\n") if f.strip()
                ]

                # Trim to first MAX_CODEBASE_FILES to keep prompt size manageable
                files = all_files[:MAX_CODEBASE_FILES]

                self._codebase_structure = files

                if len(all_files) > MAX_CODEBASE_FILES:
                    self.logger.info(
                        f"Cached codebase structure via git: {len(files)} files "
                        f"(trimmed from {len(all_files)} total)"
                    )
                else:
                    self.logger.info(
                        f"Cached codebase structure via git: {len(files)} files"
                    )

                return self._codebase_structure

        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
        ) as e:
            self.logger.warning(
                f"git ls-files failed ({e}), falling back to directory scan"
            )

        # Fallback: Manual directory scanning if git not available
        try:
            working_path = Path(self.working_dir)
            all_files = []

            # Recursively scan directories for ALL files
            def scan_directory(path: Path, base: Path):
                for item in path.iterdir():
                    # Skip hidden files and directories
                    if item.name.startswith("."):
                        continue

                    if item.is_file():
                        # Add relative path from base
                        rel_path = str(item.relative_to(base))
                        all_files.append(rel_path)
                    elif item.is_dir():
                        # Recursively scan subdirectories
                        scan_directory(item, base)

            scan_directory(working_path, working_path)

            # Trim to first MAX_CODEBASE_FILES to keep prompt size manageable
            files = all_files[:MAX_CODEBASE_FILES]

            self._codebase_structure = files

            if len(all_files) > MAX_CODEBASE_FILES:
                self.logger.info(
                    f"Cached codebase structure via scan: {len(files)} files "
                    f"(trimmed from {len(all_files)} total)"
                )
            else:
                self.logger.info(
                    f"Cached codebase structure via scan: {len(files)} files"
                )

        except Exception as e:
            self.logger.error(f"Failed to get codebase structure: {e}")
            self._codebase_structure = []

        return self._codebase_structure

    def _get_variable_values(self, user_input: str) -> dict[str, str]:
        """
        Get all 7 variables for prompt replacement.

        Simplified to reduce context usage:
        - AVAILABLE_ACTIVE_AGENTS: Simple list of agent names only
        - AVAILABLE_SLASH_COMMANDS: Simple list of command strings only
        - AVAILABLE_AGENT_TEMPLATES: Simple list of template names only
        - PREVIOUS_AUTOCOMPLETE_ITEMS: Full structure (keeps all detail for learning)
        """
        self.logger.debug("Building variable values for prompt replacement...")

        from .slash_command_parser import discover_slash_commands
        from .subagent_loader import SubagentRegistry

        # CRITICAL: Type-safe access to previous_completions via Pydantic model
        # Keep FULL structure - this is the only variable that needs complete detail
        previous_completions_data = [
            comp.model_dump(mode="python")
            for comp in self.expertise_data.previous_completions
        ]

        # Discover slash commands and agent templates (full objects)
        slash_commands_full = discover_slash_commands(self.working_dir)
        agent_templates_full = SubagentRegistry(
            self.working_dir, self.logger
        ).list_templates()
        codebase_structure = self._get_codebase_structure()

        # Simplify to names/strings only to reduce context usage
        agent_names = [agent["name"] for agent in self._cached_agents]
        command_strings = [
            cmd["name"] for cmd in slash_commands_full
        ]  # Fixed: 'name' not 'command'
        template_names = [tmpl["name"] for tmpl in agent_templates_full]

        self.logger.debug(
            f"Variable counts: {len(previous_completions_data)} completions, "
            f"{len(agent_names)} agents, {len(command_strings)} commands, "
            f"{len(template_names)} templates, {len(codebase_structure)} files"
        )

        return {
            "PREVIOUS_AUTOCOMPLETE_ITEMS": yaml.dump(
                previous_completions_data
            ),  # Full structure
            "AVAILABLE_ACTIVE_AGENTS": json.dumps(
                agent_names, indent=2
            ),  # Simplified: names only
            "AVAILABLE_SLASH_COMMANDS": json.dumps(
                command_strings, indent=2
            ),  # Simplified: commands only
            "AVAILABLE_AGENT_TEMPLATES": json.dumps(
                template_names, indent=2
            ),  # Simplified: names only
            "CODEBASE_STRUCTURE": json.dumps(codebase_structure, indent=2),
        }

    def _load_system_prompt_with_variables(self, user_input: str) -> str:
        """Load system prompt and replace all variables"""
        self.logger.debug("Loading system prompt with variable replacement...")
        variables = self._get_variable_values(user_input)
        result = self.system_prompt_template

        # Replace all variables
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, value)
                self.logger.debug(f"Replaced {{{{{key}}}}} ({len(value)} chars)")

        self.logger.debug(f"System prompt loaded (final length: {len(result)} chars)")
        return result

    async def generate_autocomplete(self, user_input: str) -> List[AutocompleteItem]:
        """
        Generate autocomplete suggestions using Claude Agent SDK.

        CRITICAL: Uses Claude Agent SDK's query() and receive_response() methods.
        After first interaction, captures and stores session_id in expertise.yaml.
        Implements request cancellation - interrupts any existing request before starting new one.
        """
        self.logger.info("=" * 80)
        self.logger.info(
            f"AUTOCOMPLETE REQUEST: {user_input[:100]}{'...' if len(user_input) > 100 else ''}"
        )
        self.logger.info("=" * 80)

        # INTERRUPT CHECK - Cancel any existing autocomplete request
        if self.is_executing and self.active_client:
            try:
                self.logger.warning(
                    "⚠️  Autocomplete is busy with previous request - interrupting..."
                )
                await self.active_client.interrupt()
                self.logger.info("✅ Successfully interrupted previous autocomplete request")
            except Exception as e:
                self.logger.error(f"Failed to interrupt autocomplete request: {e}")
                # Continue with new request even if interrupt fails
                pass

        # Track execution state for interrupt support
        self.is_executing = True
        self.active_client = self.client

        # Broadcast autocomplete started event via WebSocket
        if self.ws_manager:
            await self.ws_manager.broadcast({
                "type": "autocomplete_started",
                "orchestrator_agent_id": self.orchestrator_agent_id,
                "user_input": user_input[:100],  # First 100 chars
                "timestamp": time.time()
            })
            self.logger.debug("📡 Broadcasted autocomplete_started event")

        try:
            # Fetch active agents from database (with caching)
            await self._fetch_active_agents()

            # Update system prompt with current user input context
            self.logger.info("Building system prompt with current context...")
            system_prompt = self._load_system_prompt_with_variables(user_input)

            # Log full system prompt for debugging
            self.logger.info(f"System prompt prepared ({len(system_prompt)} chars)")
            self.logger.debug("=" * 80)
            self.logger.debug("FULL SYSTEM PROMPT:")
            self.logger.debug("-" * 80)
            self.logger.debug(system_prompt)
            self.logger.debug("=" * 80)

            # Update client system prompt if needed
            if self.client.options.system_prompt != system_prompt:
                self.logger.info("System prompt changed, reinitializing client...")
                # Recreate client with updated system prompt
                self._init_claude_agent()
                self.client.options.system_prompt = system_prompt
                # Update active client reference after reinitialization
                self.active_client = self.client
            else:
                self.logger.debug("System prompt unchanged, reusing existing client")

            # Build user prompt
            user_prompt = self.user_prompt_template.replace("$1", user_input)

            # Log full user prompt for debugging
            self.logger.info(f"User prompt prepared ({len(user_prompt)} chars)")
            self.logger.debug("=" * 80)
            self.logger.debug("FULL USER PROMPT:")
            self.logger.debug("-" * 80)
            self.logger.debug(user_prompt)
            self.logger.debug("=" * 80)

            self.logger.info(f"Sending query to Claude Agent SDK...")

            # Send query to Claude Agent SDK with async context manager
            self.logger.debug("Entering async context manager for Claude SDK client...")
            async with self.client:
                self.logger.debug("Claude SDK client connected, sending query...")
                await self.client.query(user_prompt)

                # Collect response text from all AssistantMessage blocks
                content = ""
                session_id = None
                message_count = 0

                self.logger.debug("Receiving response from Claude Agent SDK...")
                async for message in self.client.receive_response():
                    message_count += 1
                    message_type = type(message).__name__

                    if isinstance(message, SystemMessage):
                        # SystemMessage contains metadata in data dictionary
                        data = getattr(message, "data", {})
                        subtype = getattr(message, "subtype", "unknown")
                        # Extract session_id from data dict (not as direct attribute)
                        extracted_session = data.get("session_id") if isinstance(data, dict) else None
                        if extracted_session:
                            session_id = extracted_session
                        self.logger.debug(
                            f"[Message {message_count}] SystemMessage received (subtype: {subtype}, session_id: {session_id[:20] if session_id else 'None'}...)"
                        )
                        continue

                    if isinstance(message, AssistantMessage):
                        # Extract text from all TextBlock items in the response
                        block_count = len(message.content)
                        self.logger.debug(
                            f"[Message {message_count}] AssistantMessage received ({block_count} blocks)"
                        )
                        for idx, block in enumerate(message.content, 1):
                            if isinstance(block, TextBlock):
                                block_text = block.text
                                content += block_text
                                self.logger.debug(
                                    f"  Block {idx}: TextBlock ({len(block_text)} chars)"
                                )
                            else:
                                self.logger.debug(f"  Block {idx}: {type(block).__name__}")

                    # Capture session_id from ResultMessage (final message with session info)
                    elif isinstance(message, ResultMessage):
                        session_id = message.session_id
                        self.logger.debug(
                            f"[Message {message_count}] ResultMessage received (session_id: {session_id[:20] if session_id else 'None'}...)"
                        )

                self.logger.info(f"Received {message_count} messages from Claude Agent SDK")
                self.logger.debug(f"Total response content: {len(content)} chars")

                # CRITICAL: Capture session_id after first interaction (type-safe)
                if session_id and not self.expertise_data.completion_agent_id:
                    self.expertise_data.completion_agent_id = session_id
                    self._save_expertise()
                    self.logger.info(
                        f"Captured autocomplete session_id: {session_id[:20]}..."
                    )
                elif session_id:
                    self.logger.debug(
                        f"Session_id already captured: {self.expertise_data.completion_agent_id[:20]}..."
                    )

            self.logger.debug("Exited async context manager")

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                self.logger.debug("Found JSON markdown code block, extracting...")
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
                self.logger.debug(f"Extracted JSON content ({len(content)} chars)")

            # Log raw response content for debugging
            self.logger.debug("=" * 80)
            self.logger.debug("RAW RESPONSE CONTENT:")
            self.logger.debug("-" * 80)
            self.logger.debug(content[:500] + ("..." if len(content) > 500 else ""))
            self.logger.debug("=" * 80)

            # Parse JSON response
            self.logger.debug("Parsing JSON response...")
            try:
                data = json.loads(content)
                items = [AutocompleteItem(**item) for item in data.get("autocompletes", [])]
                self.logger.success(f"✓ Generated {len(items)} autocomplete suggestions")

                # Log each suggestion
                for idx, item in enumerate(items, 1):
                    self.logger.debug(
                        f"  [{idx}] {item.completion} - {item.reasoning[:50]}..."
                    )

                return items
            except json.JSONDecodeError as e:
                self.logger.error(f"✗ Failed to parse autocomplete JSON response: {e}")
                self.logger.error(f"Response content preview: {content[:200]}")
                self.logger.debug("Full response content:")
                self.logger.debug(content)
                return []
        finally:
            # Reset execution state after autocomplete completes (success or failure)
            self.is_executing = False
            self.active_client = None
            self.logger.debug("Autocomplete execution state reset")

            # Broadcast autocomplete completed event via WebSocket
            if self.ws_manager:
                await self.ws_manager.broadcast({
                    "type": "autocomplete_completed",
                    "orchestrator_agent_id": self.orchestrator_agent_id,
                    "timestamp": time.time()
                })
                self.logger.debug("📡 Broadcasted autocomplete_completed event")

    def add_completion_event(
        self,
        completion_type: str,
        user_input_on_enter: Optional[str] = None,
        user_input_before_completion: Optional[str] = None,
        autocomplete_item: Optional[str] = None,
        reasoning: Optional[str] = None,
    ):
        """
        Add a completion event to expertise.yaml with type safety.

        CRITICAL: Uses Pydantic models to ensure type safety when appending events.

        Args:
            completion_type: 'none' or 'autocomplete'
            user_input_on_enter: Required if completion_type='none'
            user_input_before_completion: Required if completion_type='autocomplete'
            autocomplete_item: Required if completion_type='autocomplete'
            reasoning: Required if completion_type='autocomplete'
        """
        self.logger.info(f"Adding completion event: type={completion_type}")

        # Calculate next order number (type-safe access)
        order = len(self.expertise_data.previous_completions) + 1
        self.logger.debug(f"Event order number: {order}")

        # Create typed event based on completion_type
        if completion_type == "none":
            self.logger.debug(
                f"Creating 'none' completion event (user pressed enter without accepting)"
            )
            event = PreviousCompletionNone(
                completion_type="none",
                user_input_on_enter=user_input_on_enter,
                order=order,
            )
            self.logger.debug(
                f"  user_input_on_enter: {user_input_on_enter[:50] if user_input_on_enter else 'None'}..."
            )
        else:  # autocomplete
            self.logger.debug(
                f"Creating 'autocomplete' completion event (user accepted suggestion)"
            )
            event = PreviousCompletionAutocomplete(
                completion_type="autocomplete",
                user_input_before_completion=user_input_before_completion,
                autocomplete_item=autocomplete_item,
                reasoning=reasoning,
                order=order,
            )
            self.logger.debug(
                f"  user_input_before: {user_input_before_completion[:50] if user_input_before_completion else 'None'}..."
            )
            self.logger.debug(
                f"  autocomplete_item: {autocomplete_item[:50] if autocomplete_item else 'None'}..."
            )
            self.logger.debug(
                f"  reasoning: {reasoning[:50] if reasoning else 'None'}..."
            )

        # Append typed event to list (type-safe)
        self.expertise_data.previous_completions.append(event)
        self.logger.debug(
            f"Event appended to history (total: {len(self.expertise_data.previous_completions)} events)"
        )

        # Save with type safety
        self._save_expertise()
        self.logger.info(f"✓ Completion event saved to expertise.yaml")
