# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Session manager for TelcoCLI agent - handles conversation persistence."""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class SessionManager:
    """Manages agent conversation sessions with persistence."""

    def __init__(self, sessions_dir: Optional[Path] = None):
        """Initialize the session manager.

        Args:
            sessions_dir: Directory to store session files. If None, uses ~/.telcocli/sessions/
        """
        if sessions_dir is None:
            sessions_dir = Path.home() / ".telcocli" / "sessions"

        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self.current_session_id: Optional[str] = None
        self.current_session: Dict[str, Any] = {}
        self._dirty = False  # Track if session needs saving
        self._auto_save_threshold = 5  # Save every N messages

    def create_session(self) -> str:
        """Create a new session with a unique ID.

        Returns:
            The new session ID (UUID).
        """
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.current_session = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
            "metadata": {"total_messages": 0, "total_tool_uses": 0},
        }

        self._save_session()
        self._dirty = False
        return session_id

    def load_session(self, session_id: str) -> bool:
        """Load an existing session by ID.

        Args:
            session_id: The session ID to load.

        Returns:
            True if session was loaded successfully, False otherwise.
        """
        # Validate session ID to prevent path traversal
        if not self._is_valid_session_id(session_id):
            return False

        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                self.current_session = json.load(f)

            self.current_session_id = session_id
            return True
        except (json.JSONDecodeError, OSError, KeyError) as e:
            print(f"Error loading session {session_id}: {e}")
            return False

    def add_message(
        self, role: str, content: str, tool_uses: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add a message to the current session.

        Args:
            role: Message role ("user" or "assistant").
            content: Message content.
            tool_uses: Optional list of tool uses in this message.
        """
        if not self.current_session_id:
            self.create_session()

        message: Dict[str, Any] = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if tool_uses:
            message["tool_uses"] = tool_uses
            self.current_session["metadata"]["total_tool_uses"] += len(tool_uses)

        self.current_session["messages"].append(message)
        self.current_session["metadata"]["total_messages"] += 1
        self.current_session["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Mark as dirty and conditionally save
        self._dirty = True

        # Auto-save every N messages or if it's an important message
        message_count = len(self.current_session["messages"])
        if message_count % self._auto_save_threshold == 0 or role == "assistant" or tool_uses:
            self._save_session()
            self._dirty = False

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages from the current session.

        Returns:
            List of message dictionaries.
        """
        return self.current_session.get("messages", [])

    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session.

        Returns:
            Dictionary with session metadata.
        """
        if not self.current_session_id:
            return {}

        return {
            "session_id": self.current_session_id,
            "created_at": self.current_session.get("created_at"),
            "updated_at": self.current_session.get("updated_at"),
            "total_messages": self.current_session.get("metadata", {}).get("total_messages", 0),
            "total_tool_uses": self.current_session.get("metadata", {}).get("total_tool_uses", 0),
        }

    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent sessions.

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            List of session info dictionaries, sorted by most recent first.
        """
        sessions = []

        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)

                sessions.append(
                    {
                        "session_id": session_data.get("session_id"),
                        "created_at": session_data.get("created_at"),
                        "updated_at": session_data.get("updated_at"),
                        "total_messages": session_data.get("metadata", {}).get("total_messages", 0),
                    }
                )
            except (json.JSONDecodeError, OSError, KeyError):
                continue

        # Sort by updated_at, most recent first
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return sessions[:limit]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID.

        Args:
            session_id: The session ID to delete.

        Returns:
            True if session was deleted, False otherwise.
        """
        # Validate session ID to prevent path traversal
        if not self._is_valid_session_id(session_id):
            return False

        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        try:
            session_file.unlink()

            # Clear current session if it was deleted
            if self.current_session_id == session_id:
                self.current_session_id = None
                self.current_session = {}

            return True
        except OSError as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    def _save_session(self) -> None:
        """Save the current session to disk."""
        if not self.current_session_id:
            return

        session_file = self.sessions_dir / f"{self.current_session_id}.json"

        try:
            # Use compact JSON to reduce file size
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(self.current_session, f, separators=(",", ":"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error saving session: {e}")

    def __del__(self):
        """Ensure session is saved on cleanup."""
        if hasattr(self, "_dirty") and self._dirty:
            self._save_session()

    def force_save(self) -> None:
        """Force save the current session."""
        if self._dirty:
            self._save_session()
            self._dirty = False

    def get_conversation_history(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history formatted for the agent.

        Args:
            max_messages: Maximum number of messages to return. If None, returns all.

        Returns:
            List of message dictionaries with role and content.
        """
        messages = self.get_messages()

        if max_messages:
            messages = messages[-max_messages:]

        # Format for agent consumption
        history: List[Dict[str, str]] = []
        for msg in messages:
            history.append({"role": str(msg["role"]), "content": str(msg["content"])})
        return history

    def _is_valid_session_id(self, session_id: str) -> bool:
        """Validate session ID to prevent path traversal attacks.

        Args:
            session_id: The session ID to validate.

        Returns:
            True if session ID is valid, False otherwise.
        """
        # Session IDs should be UUIDs (alphanumeric + hyphens only)
        if not isinstance(session_id, str):
            return False

        # Check for valid UUID format
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
        )
        if not uuid_pattern.match(session_id):
            return False

        # Additional check: ensure no path traversal characters
        if ".." in session_id or "/" in session_id or "\\" in session_id:
            return False

        return True
