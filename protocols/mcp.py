"""Protocolo MCP (Model Context Protocol) para gerenciamento de contexto avançado"""

import json
import uuid
import threading
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

class ContextType(Enum):
    """Enumeration of MCP context types.

    Defines the various types of contexts that can be managed in the
    Model Context Protocol.

    Attributes:
        CONVERSATION: Context related to conversation history.
        TASK: Context related to specific tasks or jobs.
        KNOWLEDGE: Context containing knowledge base information.
        MEMORY: Context for agent memory and learning.
        SYSTEM: Context for system-level information.
        USER_PROFILE: Context containing user profile data.
    """
    CONVERSATION = "conversation"
    TASK = "task"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    SYSTEM = "system"
    USER_PROFILE = "user_profile"

class ContextPriority(Enum):
    """Enumeration of context priority levels.

    Defines the priority levels for contexts in the MCP protocol.
    Higher priority contexts are more important and should be retained longer.

    Attributes:
        LOW: Low priority context.
        MEDIUM: Medium priority context.
        HIGH: High priority context.
        CRITICAL: Critical priority context that should be retained.
    """
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class MCPContext:
    """Individual context in the MCP protocol.

    Represents a single context item with content, metadata, and relationships
    to other contexts. Contexts can be organized hierarchically and tagged for
    easy retrieval.

    Attributes:
        id: Unique identifier for the context.
        context_type: The type of context (conversation, task, etc.).
        content: The context data as a dictionary.
        priority: The priority level of the context.
        created_at: ISO format timestamp when the context was created.
        updated_at: ISO format timestamp when the context was last updated.
        expires_at: Optional ISO format timestamp when the context expires.
        tags: List of tags for categorization and filtering.
        metadata: Additional metadata about the context.
        parent_id: Optional ID of the parent context for hierarchical organization.
        children_ids: List of IDs of child contexts.
    """
    id: str
    context_type: ContextType
    content: Dict[str, Any]
    priority: ContextPriority
    created_at: str
    updated_at: str
    expires_at: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    
    def __post_init__(self):
        """Initializes default values for optional fields.

        Ensures that optional list and dict fields are initialized to empty
        collections rather than None.
        """
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.children_ids is None:
            self.children_ids = []
    
    @classmethod
    def create(cls, context_type: ContextType, content: Dict[str, Any],
               priority: ContextPriority = ContextPriority.MEDIUM,
               expires_in_hours: Optional[int] = None,
               tags: List[str] = None,
               parent_id: Optional[str] = None) -> 'MCPContext':
        """Creates a new MCP context.

        Factory method to create a new context with auto-generated ID and timestamps.

        Args:
            context_type: The type of context to create.
            content: The context data as a dictionary.
            priority: The priority level of the context (default: MEDIUM).
            expires_in_hours: Optional hours until the context expires.
            tags: Optional list of tags for categorization.
            parent_id: Optional ID of the parent context for hierarchical organization.

        Returns:
            A new MCPContext instance with auto-generated ID and timestamps.
        """
        now = datetime.now().isoformat()
        expires_at = None
        if expires_in_hours:
            expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()

        return cls(
            id=str(uuid.uuid4()),
            context_type=context_type,
            content=content,
            priority=priority,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            tags=tags or [],
            parent_id=parent_id
        )
    
    def update_content(self, new_content: Dict[str, Any]):
        """Updates the context content.

        Merges new content into the existing content dictionary and updates
        the timestamp.

        Args:
            new_content: New content to merge into the context.
        """
        self.content.update(new_content)
        self.updated_at = datetime.now().isoformat()
    
    def add_tag(self, tag: str):
        """Adds a tag to the context.

        Adds the specified tag if it's not already present and updates the timestamp.

        Args:
            tag: The tag to add to the context.
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now().isoformat()
    
    def is_expired(self) -> bool:
        """Checks if the context has expired.

        Returns:
            True if the context has an expiration time and it has passed,
            False otherwise.
        """
        if not self.expires_at:
            return False
        return datetime.now() > datetime.fromisoformat(self.expires_at)
    
    def get_hash(self) -> str:
        """Generates a hash of the content for change detection.

        Creates an MD5 hash of the context content, useful for detecting
        when content has changed.

        Returns:
            An MD5 hash string of the context content.
        """
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the context to a dictionary.

        Serializes the context to a dictionary format, converting enum values
        to their string representations.

        Returns:
            A dictionary representation of the context with enum values converted to strings.
        """
        data = asdict(self)
        data['context_type'] = self.context_type.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPContext':
        """Creates a context from a dictionary.

        Deserializes a dictionary representation of a context back into an
        MCPContext instance, converting string enum values back to enums.

        Args:
            data: A dictionary containing the context data with enum values as strings.

        Returns:
            An MCPContext instance reconstructed from the dictionary data.

        Raises:
            ValueError: If the context_type or priority values are not valid enum values.
        """
        data['context_type'] = ContextType(data['context_type'])
        data['priority'] = ContextPriority(data['priority'])
        return cls(**data)

@dataclass
class MCPSession:
    """MCP session for grouping contexts.

    Represents a session that groups related contexts together, providing
    a way to organize and manage contexts for specific tasks or time periods.

    Attributes:
        id: Unique identifier for the session.
        name: Human-readable name for the session.
        created_at: ISO format timestamp when the session was created.
        updated_at: ISO format timestamp when the session was last updated.
        context_ids: List of context IDs belonging to this session.
        metadata: Additional metadata about the session.
    """
    id: str
    name: str
    created_at: str
    updated_at: str
    context_ids: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initializes default values for optional fields.

        Ensures that the optional metadata field is initialized to an empty
        dictionary rather than None.
        """
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def create(cls, name: str) -> 'MCPSession':
        """Creates a new MCP session.

        Factory method to create a new session with auto-generated ID and timestamps.

        Args:
            name: The name for the new session.

        Returns:
            A new MCPSession instance with auto-generated ID and timestamps.
        """
        now = datetime.now().isoformat()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            created_at=now,
            updated_at=now,
            context_ids=[]
        )

class MCPProtocol:
    """MCP context management protocol implementation.

    Manages contexts, sessions, and their relationships in the Model Context Protocol.
    Provides functionality for adding, retrieving, updating, and searching contexts
    with support for expiration, priorities, and tag-based indexing.

    Attributes:
        contexts: Dictionary of all contexts keyed by context ID.
        sessions: Dictionary of all sessions keyed by session ID.
        max_contexts: Maximum number of contexts to store (default: 1000).
        context_index: Tag-based index mapping tags to context IDs.
        _lock: Reentrant lock for thread-safe operations.
    """

    def __init__(self, max_contexts: int = 1000):
        """Initializes the MCP protocol.

        Args:
            max_contexts: Maximum number of contexts to store (default: 1000).
        """
        self.contexts: Dict[str, MCPContext] = {}
        self.sessions: Dict[str, MCPSession] = {}
        self.max_contexts = max_contexts
        self.context_index: Dict[str, List[str]] = {}  # tag -> context_ids
        self._lock = threading.RLock()  # Lock for thread-safe operations
        
    def add_context(self, context: MCPContext, session_id: Optional[str] = None) -> str:
        """Adds a context to the MCP protocol.

        Adds the context to storage, optionally associating it with a session.
        Cleans up expired contexts and removes old contexts if the limit is exceeded.
        Updates the tag index for efficient searching.

        Args:
            context: The MCPContext to add.
            session_id: Optional session ID to associate the context with.

        Returns:
            The ID of the added context.
        """
        with self._lock:
            # Remove expired contexts if necessary
            self._cleanup_expired_contexts()

            # Remove old contexts if limit exceeded
            if len(self.contexts) >= self.max_contexts:
                self._remove_oldest_contexts()

            self.contexts[context.id] = context

            # Add to session if specified
            if session_id and session_id in self.sessions:
                self.sessions[session_id].context_ids.append(context.id)
                self.sessions[session_id].updated_at = datetime.now().isoformat()

            # Update tag index
            for tag in context.tags:
                if tag not in self.context_index:
                    self.context_index[tag] = []
                self.context_index[tag].append(context.id)

            return context.id
    
    def get_context(self, context_id: str) -> Optional[MCPContext]:
        """Retrieves a context by ID.

        Returns the context with the specified ID if it exists and is not expired.
        Removes expired contexts automatically.

        Args:
            context_id: The ID of the context to retrieve.

        Returns:
            The MCPContext if found and not expired, None otherwise.
        """
        context = self.contexts.get(context_id)
        if context and context.is_expired():
            self.remove_context(context_id)
            return None
        return context
    
    def update_context(self, context_id: str, new_content: Dict[str, Any]) -> bool:
        """Updates the content of a context.

        Merges new content into the specified context if it exists and is not expired.

        Args:
            context_id: The ID of the context to update.
            new_content: The new content to merge into the context.

        Returns:
            True if the context was updated, False if not found or expired.
        """
        context = self.get_context(context_id)
        if context:
            context.update_content(new_content)
            return True
        return False
    
    def remove_context(self, context_id: str) -> bool:
        """Removes a context.

        Removes the context from storage, the tag index, and all sessions
        that reference it.

        Args:
            context_id: The ID of the context to remove.

        Returns:
            True if the context was removed, False if not found.
        """
        if context_id in self.contexts:
            context = self.contexts[context_id]

            # Remove from tags
            for tag in context.tags:
                if tag in self.context_index:
                    self.context_index[tag] = [cid for cid in self.context_index[tag] if cid != context_id]
                    if not self.context_index[tag]:
                        del self.context_index[tag]

            # Remove from sessions
            for session in self.sessions.values():
                if context_id in session.context_ids:
                    session.context_ids.remove(context_id)
                    session.updated_at = datetime.now().isoformat()

            del self.contexts[context_id]
            return True
        return False
    
    def find_contexts_by_tag(self, tag: str) -> List[MCPContext]:
        """Finds contexts by tag.

        Retrieves all non-expired contexts that have the specified tag.

        Args:
            tag: The tag to search for.

        Returns:
            A list of MCPContext instances with the specified tag.
        """
        context_ids = self.context_index.get(tag, [])
        return [self.get_context(cid) for cid in context_ids if self.get_context(cid)]
    
    def find_contexts_by_type(self, context_type: ContextType) -> List[MCPContext]:
        """Finds contexts by type.

        Retrieves all non-expired contexts of the specified type.

        Args:
            context_type: The context type to search for.

        Returns:
            A list of MCPContext instances of the specified type.
        """
        return [ctx for ctx in self.contexts.values() if ctx.context_type == context_type and not ctx.is_expired()]
    
    def find_contexts_by_priority(self, min_priority: ContextPriority) -> List[MCPContext]:
        """Finds contexts by minimum priority.

        Retrieves all non-expired contexts with priority equal to or higher
        than the specified minimum priority.

        Args:
            min_priority: The minimum priority level to search for.

        Returns:
            A list of MCPContext instances with priority >= min_priority.
        """
        return [ctx for ctx in self.contexts.values()
                if ctx.priority.value >= min_priority.value and not ctx.is_expired()]
    
    def create_session(self, name: str) -> str:
        """Creates a new session.

        Creates a new session with the specified name and adds it to storage.

        Args:
            name: The name for the new session.

        Returns:
            The ID of the created session.
        """
        with self._lock:
            session = MCPSession.create(name)
            self.sessions[session.id] = session
            return session.id
    
    def get_session_contexts(self, session_id: str) -> List[MCPContext]:
        """Retrieves all contexts from a session.

        Returns all non-expired contexts belonging to the specified session.

        Args:
            session_id: The ID of the session to retrieve contexts from.

        Returns:
            A list of MCPContext instances belonging to the session.
        """
        session = self.sessions.get(session_id)
        if not session:
            return []

        return [self.get_context(cid) for cid in session.context_ids if self.get_context(cid)]
    
    def get_relevant_contexts(self, query: str, max_results: int = 10) -> List[MCPContext]:
        """Finds contexts relevant to a query.

        Performs a simple keyword search across context content and tags,
        scoring contexts based on keyword matches, tag matches, and priority.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return (default: 10).

        Returns:
            A list of MCPContext instances sorted by relevance score.
        """
        query_words = query.lower().split()
        scored_contexts = []

        for context in self.contexts.values():
            if context.is_expired():
                continue

            score = 0
            content_str = json.dumps(context.content).lower()

            # Score by keywords in content
            for word in query_words:
                score += content_str.count(word)

            # Score by tags
            for tag in context.tags:
                if any(word in tag.lower() for word in query_words):
                    score += 2

            # Score by priority
            score += context.priority.value

            if score > 0:
                scored_contexts.append((score, context))

        # Sort by score and return the best matches
        scored_contexts.sort(key=lambda x: x[0], reverse=True)
        return [ctx for _, ctx in scored_contexts[:max_results]]
    
    def _cleanup_expired_contexts(self):
        """Removes all expired contexts.

        Identifies and removes all contexts that have passed their expiration time.
        """
        expired_ids = [cid for cid, ctx in self.contexts.items() if ctx.is_expired()]
        for cid in expired_ids:
            self.remove_context(cid)
    
    def _remove_oldest_contexts(self, count: int = 100):
        """Removes the oldest contexts.

        Removes the specified number of oldest contexts based on creation time.
        Used when the context limit is exceeded.

        Args:
            count: The number of contexts to remove (default: 100).
        """
        # Sort by creation date and remove the oldest
        sorted_contexts = sorted(self.contexts.items(), key=lambda x: x[1].created_at)
        for i in range(min(count, len(sorted_contexts))):
            context_id = sorted_contexts[i][0]
            self.remove_context(context_id)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Returns a summary of the current context state.

        Provides statistics about contexts, sessions, and tags, excluding
        expired contexts from the counts.

        Returns:
            A dictionary containing summary statistics including total contexts,
            total sessions, contexts by type, contexts by priority, and total tags.
        """
        type_counts = {}
        priority_counts = {}

        for context in self.contexts.values():
            if not context.is_expired():
                type_counts[context.context_type.value] = type_counts.get(context.context_type.value, 0) + 1
                priority_counts[context.priority.value] = priority_counts.get(context.priority.value, 0) + 1

        return {
            "total_contexts": len([ctx for ctx in self.contexts.values() if not ctx.is_expired()]),
            "total_sessions": len(self.sessions),
            "contexts_by_type": type_counts,
            "contexts_by_priority": priority_counts,
            "total_tags": len(self.context_index)
        }