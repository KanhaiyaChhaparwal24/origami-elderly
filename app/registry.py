"""
Plugin Registry System for Origami Framework
Manages application plugins and routes data processing based on app_id
"""

from typing import Dict, List, Optional, Protocol, Any
from abc import ABC, abstractmethod
import generated.origami.core_pb2 as core_pb
from datetime import datetime
import logging


class PluginInterface(Protocol):
    """Interface that all application plugins must implement"""
    
    @property
    def app_id(self) -> str:
        """Return the unique application identifier"""
        ...
    
    @property
    def app_name(self) -> str:
        """Return the human-readable application name"""
        ...
    
    @property
    def supported_data_types(self) -> List[str]:
        """Return list of data types this plugin can process"""
        ...
    
    def parse_data_packet(self, data_packet: core_pb.DataPacket) -> Any:
        """Parse the payload from a DataPacket into application-specific object"""
        ...
    
    def generate_alerts(self, parsed_data: Any, app_config: Optional[core_pb.ApplicationConfig] = None) -> List[core_pb.Alert]:
        """Generate alerts from parsed application data"""
        ...
    
    def get_contacts(self, entity_id: str) -> List[core_pb.Contact]:
        """Get contacts for a specific entity (patient, field, zone, etc.)"""
        ...
    
    def process_alert(self, alert: core_pb.Alert) -> List[core_pb.Notification]:
        """Process an alert and generate appropriate notifications"""
        ...
    
    def generate_summary(self, entity_id: str, period: str, alerts: List[core_pb.Alert], 
                        notifications: List[core_pb.Notification]) -> core_pb.ApplicationSummary:
        """Generate a summary report for the given entity and period"""
        ...


class PluginRegistry:
    """Central registry for managing application plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, PluginInterface] = {}
        self._logger = logging.getLogger(__name__)
        
    def register_plugin(self, plugin: PluginInterface) -> None:
        """Register a new application plugin"""
        app_id = plugin.app_id
        if app_id in self._plugins:
            self._logger.warning(f"Plugin for app_id '{app_id}' already registered. Overwriting.")
        
        self._plugins[app_id] = plugin
        self._logger.info(f"Registered plugin: {app_id} ({plugin.app_name})")
    
    def unregister_plugin(self, app_id: str) -> None:
        """Unregister an application plugin"""
        if app_id in self._plugins:
            del self._plugins[app_id]
            self._logger.info(f"Unregistered plugin: {app_id}")
        else:
            self._logger.warning(f"No plugin found for app_id: {app_id}")
    
    def get_plugin(self, app_id: str) -> Optional[PluginInterface]:
        """Get a specific plugin by app_id"""
        return self._plugins.get(app_id)
    
    def list_plugins(self) -> List[str]:
        """List all registered plugin app_ids"""
        return list(self._plugins.keys())
    
    def get_applications(self) -> List[core_pb.Application]:
        """Get Application protobuf objects for all registered plugins"""
        applications = []
        for plugin in self._plugins.values():
            app = core_pb.Application()
            app.app_id = plugin.app_id
            app.app_name = plugin.app_name
            app.version = "1.0.0"  # Could be made configurable
            app.description = f"Application plugin for {plugin.app_name}"
            app.data_types.extend(plugin.supported_data_types)
            applications.append(app)
        return applications
    
    def route_data_packet(self, data_packet: core_pb.DataPacket) -> Optional[Any]:
        """Route a data packet to the appropriate plugin for parsing"""
        plugin = self.get_plugin(data_packet.app_id)
        if not plugin:
            self._logger.error(f"No plugin found for app_id: {data_packet.app_id}")
            return None
        
        try:
            return plugin.parse_data_packet(data_packet)
        except Exception as e:
            self._logger.error(f"Error parsing data packet in {data_packet.app_id}: {e}")
            return None
    
    def generate_alerts(self, data_packet: core_pb.DataPacket, 
                       app_config: Optional[core_pb.ApplicationConfig] = None) -> List[core_pb.Alert]:
        """Generate alerts for a data packet using the appropriate plugin"""
        plugin = self.get_plugin(data_packet.app_id)
        if not plugin:
            self._logger.error(f"No plugin found for app_id: {data_packet.app_id}")
            return []
        
        try:
            parsed_data = plugin.parse_data_packet(data_packet)
            if parsed_data is None:
                return []
            
            alerts = plugin.generate_alerts(parsed_data, app_config)
            
            # Ensure alerts have correct app_id and core fields
            for alert in alerts:
                alert.app_id = data_packet.app_id
                if not alert.timestamp.seconds:
                    alert.timestamp.CopyFrom(data_packet.timestamp)
                if not alert.source_packet_id:
                    alert.source_packet_id = data_packet.packet_id
            
            return alerts
            
        except Exception as e:
            self._logger.error(f"Error generating alerts in {data_packet.app_id}: {e}")
            return []
    
    def process_alert(self, alert: core_pb.Alert) -> List[core_pb.Notification]:
        """Process an alert using the appropriate plugin"""
        plugin = self.get_plugin(alert.app_id)
        if not plugin:
            self._logger.error(f"No plugin found for app_id: {alert.app_id}")
            return []
        
        try:
            notifications = plugin.process_alert(alert)
            
            # Ensure notifications have correct app_id and core fields
            for notification in notifications:
                notification.app_id = alert.app_id
                if not notification.timestamp.seconds:
                    notification.timestamp.CopyFrom(alert.timestamp)
                if not notification.alert_id:
                    notification.alert_id = alert.alert_id
            
            return notifications
            
        except Exception as e:
            self._logger.error(f"Error processing alert in {alert.app_id}: {e}")
            return []
    
    def validate_plugin(self, plugin: PluginInterface) -> bool:
        """Validate that a plugin implements the required interface correctly"""
        try:
            # Check required properties
            assert isinstance(plugin.app_id, str) and plugin.app_id.strip()
            assert isinstance(plugin.app_name, str) and plugin.app_name.strip()
            assert isinstance(plugin.supported_data_types, list)
            
            # Check that required methods exist and are callable
            assert hasattr(plugin, 'parse_data_packet') and callable(plugin.parse_data_packet)
            assert hasattr(plugin, 'generate_alerts') and callable(plugin.generate_alerts)
            assert hasattr(plugin, 'get_contacts') and callable(plugin.get_contacts)
            assert hasattr(plugin, 'process_alert') and callable(plugin.process_alert)
            assert hasattr(plugin, 'generate_summary') and callable(plugin.generate_summary)
            
            return True
            
        except (AssertionError, AttributeError) as e:
            self._logger.error(f"Plugin validation failed: {e}")
            return False


# Global plugin registry instance
plugin_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance"""
    return plugin_registry


def register_plugin(plugin: PluginInterface) -> None:
    """Convenience function to register a plugin with the global registry"""
    plugin_registry.register_plugin(plugin)


def get_plugin(app_id: str) -> Optional[PluginInterface]:
    """Convenience function to get a plugin from the global registry"""
    return plugin_registry.get_plugin(app_id)