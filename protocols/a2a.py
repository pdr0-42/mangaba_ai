"""A2A (Agent-to-Agent) Protocol for Mangaba AI agent communication.

This module implements the Agent-to-Agent communication protocol,
enabling direct message passing, broadcasting, and agent discovery
for multi-agent systems.

Classes:
    MessageType: Enumeration of message types (request, response, broadcast, etc.)
    A2AMessage: Standard message format for A2A communication
    A2AProtocol: Protocol implementation for message handling
    A2AAgent: Base agent class with A2A capabilities
"""

import json
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

class MessageType(Enum):
    """Enumeration of A2A message types.

    Defines the various types of messages that can be sent between agents
    in the Agent-to-Agent communication protocol.

    Attributes:
        REQUEST: A message requesting an action or information from another agent.
        RESPONSE: A message responding to a previous request.
        BROADCAST: A message sent to all connected agents.
        NOTIFICATION: A message informing agents of an event or update.
        ERROR: A message indicating an error occurred.
    """
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    NOTIFICATION = "notification"
    ERROR = "error"

@dataclass
class A2AMessage:
    """Standard message format for A2A communication.

    Represents a message sent between agents in the Agent-to-Agent protocol.
    Messages can be of various types including requests, responses, broadcasts,
    notifications, and errors.

    Attributes:
        id: Unique identifier for the message.
        sender_id: ID of the agent sending the message.
        receiver_id: ID of the agent receiving the message (None for broadcasts).
        message_type: The type of message (request, response, broadcast, etc.).
        content: The message payload as a dictionary.
        timestamp: ISO format timestamp when the message was created.
        correlation_id: ID of the related message for request-response pairs.
        metadata: Additional metadata about the message.
    """
    id: str
    sender_id: str
    receiver_id: Optional[str]
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, sender_id: str, message_type: MessageType, content: Dict[str, Any],
               receiver_id: Optional[str] = None, correlation_id: Optional[str] = None) -> 'A2AMessage':
        """Creates a new A2A message.

        Factory method to create a new message with auto-generated ID and timestamp.

        Args:
            sender_id: ID of the agent sending the message.
            message_type: The type of message to create.
            content: The message payload as a dictionary.
            receiver_id: ID of the receiving agent (optional, None for broadcasts).
            correlation_id: ID of related message for request-response pairs (optional).

        Returns:
            A new A2AMessage instance with auto-generated ID and timestamp.
        """
        return cls(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            correlation_id=correlation_id,
            metadata={}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the message to a dictionary.

        Serializes the message to a dictionary format, converting the MessageType
        enum to its string value.

        Returns:
            A dictionary representation of the message with enum values converted to strings.
        """
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'A2AMessage':
        """Creates a message from a dictionary.

        Deserializes a dictionary representation of a message back into an
        A2AMessage instance, converting the message_type string back to MessageType enum.

        Args:
            data: A dictionary containing the message data with message_type as a string.

        Returns:
            An A2AMessage instance reconstructed from the dictionary data.

        Raises:
            ValueError: If the message_type value is not a valid MessageType.
        """
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)

class A2AProtocol:
    """Agent-to-Agent communication protocol implementation.

    Handles message passing between agents, including direct messaging,
    broadcasting, and agent discovery. Manages message handlers and maintains
    a history of sent and received messages.

    Attributes:
        agent_id: The ID of the agent using this protocol.
        message_handlers: Dictionary mapping message types to lists of handler functions.
        connected_agents: Dictionary of connected agents keyed by agent ID.
        message_history: List of all messages sent and received by this protocol.
        _lock: Reentrant lock for thread-safe operations.
    """

    def __init__(self, agent_id: str):
        """Initializes the A2A protocol for an agent.

        Args:
            agent_id: The unique identifier for the agent using this protocol.
        """
        self.agent_id = agent_id
        self.message_handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }
        self.connected_agents: Dict[str, 'A2AAgent'] = {}
        self.message_history: List[A2AMessage] = []
        self._lock = threading.RLock()  # Lock for thread-safe operations
        
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Registers a handler function for a specific message type.

        When a message of the specified type is received, all registered handlers
        for that type will be called.

        Args:
            message_type: The type of message this handler should process.
            handler: A callable function that accepts an A2AMessage as its argument.
        """
        self.message_handlers[message_type].append(handler)
    
    def connect_agent(self, agent: 'A2AAgent'):
        """Connects another agent for communication.

        Adds the specified agent to the list of connected agents, enabling
        direct message passing between them.

        Args:
            agent: The A2AAgent instance to connect to.
        """
        with self._lock:
            self.connected_agents[agent.agent_id] = agent
        
    def disconnect_agent(self, agent_id: str):
        """Disconnects an agent.

        Removes the specified agent from the list of connected agents,
        preventing further message passing to that agent.

        Args:
            agent_id: The ID of the agent to disconnect.
        """
        with self._lock:
            if agent_id in self.connected_agents:
                del self.connected_agents[agent_id]
    
    def send_message(self, message: A2AMessage) -> bool:
        """Sends a message to another agent or broadcasts to all connected agents.

        For direct messages, sends to the specified receiver if connected.
        For broadcast messages, sends to all connected agents. Optionally filters
        by tags specified in message metadata.

        Args:
            message: The A2AMessage to send.

        Returns:
            True if the message was sent successfully, False otherwise.

        Raises:
            Exception: If an error occurs during message sending (caught and logged).
        """
        try:
            with self._lock:
                if message.receiver_id and message.receiver_id in self.connected_agents:
                    target_agent = self.connected_agents[message.receiver_id]
                    target_agent.receive_message(message)
                    self.message_history.append(message)
                    return True
                elif message.message_type == MessageType.BROADCAST:
                    # Broadcast to all connected agents
                    # Filter by tags if specified
                    target_tags = message.metadata.get('target_tags') if message.metadata else None

                    for agent in self.connected_agents.values():
                        # If target_tags specified, check if agent has the tags
                        if target_tags:
                            # Simplification: sends to all (filter would be implemented in agent)
                            agent.receive_message(message)
                        else:
                            agent.receive_message(message)
                    self.message_history.append(message)
                    return True
                return False
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def receive_message(self, message: A2AMessage):
        """Receives and processes an incoming message.

        Adds the message to history and executes all registered handlers
        for the message type. Handler exceptions are caught and logged.

        Args:
            message: The A2AMessage to receive and process.
        """
        self.message_history.append(message)

        # Execute registered handlers
        for handler in self.message_handlers[message.message_type]:
            try:
                handler(message)
            except Exception as e:
                print(f"Error in handler: {e}")
    
    def create_request(self, receiver_id: str, action: str, params: Dict[str, Any]) -> A2AMessage:
        """Creates a request message.

        Creates a REQUEST type message with the specified action and parameters.

        Args:
            receiver_id: The ID of the agent to send the request to.
            action: The action to be performed by the receiving agent.
            params: Parameters for the action as a dictionary.

        Returns:
            An A2AMessage of type REQUEST containing the action and parameters.
        """
        return A2AMessage.create(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=MessageType.REQUEST,
            content={
                "action": action,
                "params": params
            }
        )
    
    def create_response(self, original_message: A2AMessage, result: Any, success: bool = True) -> A2AMessage:
        """Creates a response message.

        Creates a RESPONSE type message in reply to a previous request.
        The correlation ID links the response to the original request.

        Args:
            original_message: The original request message to respond to.
            result: The result data to include in the response.
            success: Whether the request was successful (default: True).

        Returns:
            An A2AMessage of type RESPONSE with the result and correlation ID.
        """
        return A2AMessage.create(
            sender_id=self.agent_id,
            receiver_id=original_message.sender_id,
            message_type=MessageType.RESPONSE,
            content={
                "result": result,
                "success": success
            },
            correlation_id=original_message.id
        )
    
    def broadcast(self, content: Dict[str, Any], target_tags: Optional[List[str]] = None) -> A2AMessage:
        """Creates and sends a broadcast message with optional tag filtering.

        Creates a BROADCAST type message and sends it to all connected agents.
        Target tags can be specified in metadata for filtering purposes.

        Args:
            content: The message content as a dictionary.
            target_tags: Optional list of tags to filter recipients by.

        Returns:
            The A2AMessage that was broadcast.
        """
        message = A2AMessage.create(
            sender_id=self.agent_id,
            message_type=MessageType.BROADCAST,
            content=content
        )

        # Add tags to metadata if specified
        if target_tags:
            if message.metadata is None:
                message.metadata = {}
            message.metadata['target_tags'] = target_tags

        self.send_message(message)
        return message

class A2AAgent:
    """Base agent class with A2A communication capabilities.

    Provides Agent-to-Agent communication functionality including message
    sending, receiving, and handler management. Can connect to other agents
    and participate in multi-agent systems.

    Attributes:
        agent_id: The unique identifier for this agent.
        a2a_protocol: The A2AProtocol instance handling communication.
    """

    def __init__(self, agent_id: str):
        """Initializes the A2A agent.

        Args:
            agent_id: The unique identifier for this agent.
        """
        self.agent_id = agent_id
        self.a2a_protocol = A2AProtocol(agent_id)
        self.setup_default_handlers()
    
    def setup_default_handlers(self):
        """Sets up default message handlers.

        Registers the default handlers for REQUEST, RESPONSE, and NOTIFICATION
        message types. These can be overridden in subclasses for custom behavior.
        """
        self.a2a_protocol.register_handler(MessageType.REQUEST, self.handle_request)
        self.a2a_protocol.register_handler(MessageType.RESPONSE, self.handle_response)
        self.a2a_protocol.register_handler(MessageType.NOTIFICATION, self.handle_notification)
    
    def handle_request(self, message: A2AMessage):
        """Default handler for request messages.

        Processes a request message and sends a response. This is a simple
        default implementation that should be overridden in subclasses for
        specific agent behavior.

        Args:
            message: The REQUEST message to handle.
        """
        action = message.content.get("action")

        # Implement agent-specific logic here
        result = f"Action '{action}' processed by agent {self.agent_id}"

        response = self.a2a_protocol.create_response(message, result)
        self.a2a_protocol.send_message(response)
    
    def handle_response(self, message: A2AMessage):
        """Default handler for response messages.

        Prints the received response. This is a simple default implementation
        that should be overridden in subclasses for specific agent behavior.

        Args:
            message: The RESPONSE message to handle.
        """
        print(f"Response received from {message.sender_id}: {message.content}")
    
    def handle_notification(self, message: A2AMessage):
        """Default handler for notification messages.

        Prints the received notification. This is a simple default implementation
        that should be overridden in subclasses for specific agent behavior.

        Args:
            message: The NOTIFICATION message to handle.
        """
        print(f"Notification from {message.sender_id}: {message.content}")
    
    def receive_message(self, message: A2AMessage):
        """Receives a message via the A2A protocol.

        Delegates message reception to the underlying A2AProtocol instance.

        Args:
            message: The A2AMessage to receive.
        """
        self.a2a_protocol.receive_message(message)
    
    def connect_to(self, other_agent: 'A2AAgent'):
        """Connects to another agent.

        Establishes a bidirectional connection between this agent and another agent,
        enabling message passing in both directions.

        Args:
            other_agent: The A2AAgent to connect to.
        """
        self.a2a_protocol.connect_agent(other_agent)
        other_agent.a2a_protocol.connect_agent(self)
    
    def send_request(self, receiver_id: str, action: str, params: Dict[str, Any]):
        """Sends a request to another agent.

        Creates and sends a REQUEST message to the specified agent.

        Args:
            receiver_id: The ID of the agent to send the request to.
            action: The action to be performed by the receiving agent.
            params: Parameters for the action as a dictionary.

        Returns:
            True if the request was sent successfully, False otherwise.
        """
        message = self.a2a_protocol.create_request(receiver_id, action, params)
        return self.a2a_protocol.send_message(message)
    
    def notify_all(self, content: Dict[str, Any]):
        """Sends a notification to all connected agents.

        Creates and broadcasts a NOTIFICATION message to all connected agents.

        Args:
            content: The notification content as a dictionary.

        Returns:
            True if the notification was sent successfully, False otherwise.
        """
        return self.a2a_protocol.broadcast(content)