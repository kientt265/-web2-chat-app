"""Zookeeper client for service coordination."""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from kazoo.client import KazooClient
from kazoo.protocol.states import EventType, KazooState
from kazoo.exceptions import NoNodeError, NodeExistsError

from .logging import get_logger

logger = get_logger(__name__)


def serialize_for_json(obj: Any) -> Any:
    """Convert datetime objects to strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj


class ZookeeperClient:
    """Zookeeper client for distributed coordination and service discovery."""
    
    def __init__(self, hosts: str, timeout: int = 10):
        """Initialize Zookeeper client.
        
        Args:
            hosts: Comma-separated list of Zookeeper hosts
            timeout: Connection timeout in seconds
        """
        self.hosts = hosts
        self.timeout = timeout
        self.client: Optional[KazooClient] = None
        self._connected = False
        self._watchers: Dict[str, List[Callable]] = {}
        
    async def connect(self) -> None:
        """Connect to Zookeeper cluster."""
        try:
            self.client = KazooClient(
                hosts=self.hosts,
                timeout=self.timeout,
                logger=logger
            )
            
            # Add connection state listener
            self.client.add_listener(self._connection_listener)
            
            # Start the client
            self.client.start(timeout=self.timeout)
            self._connected = True
            
            logger.info(f"Connected to Zookeeper at {self.hosts}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Zookeeper: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Zookeeper cluster."""
        if self.client:
            self.client.stop()
            self.client.close()
            self._connected = False
            logger.info("Disconnected from Zookeeper")
    
    def _connection_listener(self, state: KazooState) -> None:
        """Handle Zookeeper connection state changes."""
        if state == KazooState.LOST:
            logger.warning("Zookeeper connection lost")
            self._connected = False
        elif state == KazooState.SUSPENDED:
            logger.warning("Zookeeper connection suspended")
            self._connected = False
        elif state == KazooState.CONNECTED:
            logger.info("Zookeeper connection established")
            self._connected = True
    
    def is_connected(self) -> bool:
        """Check if connected to Zookeeper."""
        return self._connected and self.client is not None
    
    def ensure_path(self, path: str) -> None:
        """Ensure a path exists in Zookeeper."""
        if not self.client:
            raise RuntimeError("Not connected to Zookeeper")
        
        try:
            self.client.ensure_path(path)
            logger.debug(f"Ensured path exists: {path}")
        except Exception as e:
            logger.error(f"Failed to ensure path {path}: {e}")
            raise
    
    def create_node(self, path: str, data: Dict, ephemeral: bool = True, sequence: bool = False) -> str:
        """Create a node in Zookeeper.
        
        Args:
            path: Node path
            data: Node data as dictionary
            ephemeral: Whether node is ephemeral (deleted on disconnect)
            sequence: Whether to append sequence number to path
            
        Returns:
            Actual path of created node
        """
        if not self.client:
            raise RuntimeError("Not connected to Zookeeper")
        
        try:
            # Serialize datetime objects before JSON encoding
            serializable_data = serialize_for_json(data)
            json_data = json.dumps(serializable_data).encode('utf-8')
            actual_path = self.client.create(
                path,
                json_data,
                ephemeral=ephemeral,
                sequence=sequence,
                makepath=True
            )
            logger.debug(f"Created node: {actual_path}")
            return actual_path
            
        except NodeExistsError:
            logger.warning(f"Node already exists: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to create node {path}: {e}")
            raise
    
    def get_node_data(self, path: str) -> Optional[Dict]:
        """Get data from a Zookeeper node.
        
        Args:
            path: Node path
            
        Returns:
            Node data as dictionary or None if not found
        """
        if not self.client:
            raise RuntimeError("Not connected to Zookeeper")
        
        try:
            data, stat = self.client.get(path)
            if data:
                return json.loads(data.decode('utf-8'))
            return None
            
        except NoNodeError:
            logger.debug(f"Node not found: {path}")
            return None
        except Exception as e:
            logger.error(f"Failed to get node data from {path}: {e}")
            raise
    
    def update_node_data(self, path: str, data: Dict) -> None:
        """Update data in a Zookeeper node.
        
        Args:
            path: Node path
            data: New data as dictionary
        """
        if not self.client:
            raise RuntimeError("Not connected to Zookeeper")
        
        try:
            # Serialize datetime objects before JSON encoding
            serializable_data = serialize_for_json(data)
            json_data = json.dumps(serializable_data).encode('utf-8')
            self.client.set(path, json_data)
            logger.debug(f"Updated node data: {path}")
            
        except NoNodeError:
            logger.error(f"Node not found for update: {path}")
            raise
        except Exception as e:
            logger.error(f"Failed to update node {path}: {e}")
            raise
    
    def delete_node(self, path: str, recursive: bool = False) -> None:
        """Delete a node from Zookeeper.
        
        Args:
            path: Node path
            recursive: Whether to delete recursively
        """
        if not self.client:
            raise RuntimeError("Not connected to Zookeeper")
        
        try:
            self.client.delete(path, recursive=recursive)
            logger.debug(f"Deleted node: {path}")
            
        except NoNodeError:
            logger.debug(f"Node not found for deletion: {path}")
        except Exception as e:
            logger.error(f"Failed to delete node {path}: {e}")
            raise
    
    def get_children(self, path: str) -> List[str]:
        """Get children of a Zookeeper node.
        
        Args:
            path: Parent node path
            
        Returns:
            List of child node names
        """
        if not self.client:
            raise RuntimeError("Not connected to Zookeeper")
        
        try:
            children = self.client.get_children(path)
            return children
            
        except NoNodeError:
            logger.debug(f"Node not found: {path}")
            return []
        except Exception as e:
            logger.error(f"Failed to get children of {path}: {e}")
            raise
    
    def watch_children(self, path: str, callback: Callable[[List[str]], None]) -> None:
        """Watch for changes in child nodes.
        
        Args:
            path: Parent node path
            callback: Function to call when children change
        """
        if not self.client:
            raise RuntimeError("Not connected to Zookeeper")
        
        def watcher(children):
            """Internal watcher function."""
            try:
                callback(children)
            except Exception as e:
                logger.error(f"Error in children watcher callback: {e}")
        
        try:
            # Add to watchers registry
            if path not in self._watchers:
                self._watchers[path] = []
            self._watchers[path].append(callback)
            
            # Set up the watcher
            self.client.ChildrenWatch(path, watcher)
            logger.debug(f"Set up children watcher for: {path}")
            
        except Exception as e:
            logger.error(f"Failed to set up children watcher for {path}: {e}")
            raise
    
    def watch_node_data(self, path: str, callback: Callable[[Dict], None]) -> None:
        """Watch for changes in node data.
        
        Args:
            path: Node path
            callback: Function to call when data changes
        """
        if not self.client:
            raise RuntimeError("Not connected to Zookeeper")
        
        def watcher(data, stat, event):
            """Internal watcher function."""
            try:
                if data and event is None:  # Initial data
                    node_data = json.loads(data.decode('utf-8'))
                    callback(node_data)
                elif event and event.type == EventType.CHANGED:
                    # Node data changed
                    updated_data = self.get_node_data(path)
                    if updated_data:
                        callback(updated_data)
            except Exception as e:
                logger.error(f"Error in data watcher callback: {e}")
        
        try:
            self.client.DataWatch(path, watcher)
            logger.debug(f"Set up data watcher for: {path}")
            
        except Exception as e:
            logger.error(f"Failed to set up data watcher for {path}: {e}")
            raise
