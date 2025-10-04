"""
Agriculture Plugin for Origami Framework
Handles crop monitoring, farming activities, and agricultural alerts
"""

from typing import List, Optional, Any
from datetime import datetime
import uuid
import random

import generated.origami.core_pb2 as core_pb
import generated.origami.agriculture_pb2 as agriculture_pb
from app.registry import PluginInterface
from google.protobuf.timestamp_pb2 import Timestamp


def to_timestamp(dt: datetime) -> Timestamp:
    """Convert Python datetime to Protobuf Timestamp"""
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


class AgricultureServicePlugin(PluginInterface):
    """Plugin for agricultural monitoring and farm management"""
    
    @property
    def app_id(self) -> str:
        return "agriculture"
    
    @property
    def app_name(self) -> str:
        return "Smart Agriculture Monitoring"
    
    @property
    def supported_data_types(self) -> List[str]:
        return ["crop_sensor_reading", "farming_event", "farm_contact"]
    
    def parse_data_packet(self, data_packet: core_pb.DataPacket) -> Any:
        """Parse DataPacket payload into agriculture-specific protobuf objects"""
        try:
            if data_packet.data_type == "crop_sensor_reading":
                sensor_reading = agriculture_pb.CropSensorReading()
                sensor_reading.ParseFromString(data_packet.payload)
                return sensor_reading
                
            elif data_packet.data_type == "farming_event":
                farming_event = agriculture_pb.FarmingEvent()
                farming_event.ParseFromString(data_packet.payload)
                return farming_event
                
            elif data_packet.data_type == "farm_contact":
                farm_contact = agriculture_pb.FarmContact()
                farm_contact.ParseFromString(data_packet.payload)
                return farm_contact
                
            else:
                raise ValueError(f"Unsupported data type: {data_packet.data_type}")
                
        except Exception as e:
            print(f"Error parsing agriculture data packet: {e}")
            return None
    
    def generate_alerts(self, parsed_data: Any, app_config: Optional[core_pb.ApplicationConfig] = None) -> List[core_pb.Alert]:
        """Generate agricultural alerts from farm monitoring data"""
        alerts = []
        
        # Get thresholds from config or use defaults
        drought_threshold = 20.0  # soil moisture %
        frost_threshold = 2.0     # temperature °C
        
        if app_config and app_config.thresholds:
            drought_threshold = app_config.thresholds.get("drought_threshold", 20.0)
            frost_threshold = app_config.thresholds.get("frost_threshold", 2.0)
        
        if isinstance(parsed_data, agriculture_pb.CropSensorReading):
            # Drought alert
            if parsed_data.soil.moisture_level < drought_threshold:
                alert = core_pb.Alert()
                alert.alert_id = str(uuid.uuid4())
                alert.app_id = self.app_id
                alert.timestamp.CopyFrom(parsed_data.timestamp)
                alert.type = "DROUGHT_WARNING"
                alert.severity = "critical" if parsed_data.soil.moisture_level < 10 else "warning"
                alert.message = f"Low soil moisture detected: {parsed_data.soil.moisture_level}%"
                alert.score = 0.9 if alert.severity == "critical" else 0.7
                alert.context["moisture_level"] = str(parsed_data.soil.moisture_level)
                alert.context["field_id"] = parsed_data.field_id
                alert.context["crop_type"] = parsed_data.crop_type
                alert.affected_entities.append(parsed_data.field_id)
                alerts.append(alert)
            
            # Frost alert
            if parsed_data.weather.temperature < frost_threshold:
                alert = core_pb.Alert()
                alert.alert_id = str(uuid.uuid4())
                alert.app_id = self.app_id
                alert.timestamp.CopyFrom(parsed_data.timestamp)
                alert.type = "FROST_WARNING"
                alert.severity = "critical"
                alert.message = f"Frost conditions detected: {parsed_data.weather.temperature}°C"
                alert.score = 0.95
                alert.context["temperature"] = str(parsed_data.weather.temperature)
                alert.context["field_id"] = parsed_data.field_id
                alert.context["crop_type"] = parsed_data.crop_type
                alert.affected_entities.append(parsed_data.field_id)
                alerts.append(alert)
            
            # Nutrient deficiency alert
            soil = parsed_data.soil
            if soil.nitrogen_level < 20 or soil.phosphorus_level < 15 or soil.potassium_level < 25:
                alert = core_pb.Alert()
                alert.alert_id = str(uuid.uuid4())
                alert.app_id = self.app_id
                alert.timestamp.CopyFrom(parsed_data.timestamp)
                alert.type = "NUTRIENT_DEFICIENCY"
                alert.severity = "warning"
                alert.message = f"Nutrient levels low - N:{soil.nitrogen_level}, P:{soil.phosphorus_level}, K:{soil.potassium_level}"
                alert.score = 0.6
                alert.context["nitrogen"] = str(soil.nitrogen_level)
                alert.context["phosphorus"] = str(soil.phosphorus_level)
                alert.context["potassium"] = str(soil.potassium_level)
                alert.context["field_id"] = parsed_data.field_id
                alert.affected_entities.append(parsed_data.field_id)
                alerts.append(alert)
        
        return alerts
    
    def get_contacts(self, entity_id: str) -> List[core_pb.Contact]:
        """Get farm contacts for a field"""
        contacts = []
        
        # Primary farmer contact
        contact = core_pb.Contact()
        contact.contact_id = "farmer_001"
        contact.app_id = self.app_id
        contact.name = "Sarah Thompson (Farm Owner)"
        contact.role = "farmer"
        contact.phone = "+1-555-0456"
        contact.email = "sarah.thompson@farm.com"
        contact.is_primary = True
        contact.entity_ids.append(entity_id)
        contact.preferences["preferred_method"] = "sms"
        contacts.append(contact)
        
        # Agronomist contact
        contact = core_pb.Contact()
        contact.contact_id = "agronomist_001"
        contact.app_id = self.app_id
        contact.name = "Dr. Michael Green"
        contact.role = "agronomist"
        contact.phone = "+1-555-0789"
        contact.email = "dr.green@agri-consult.com"
        contact.is_primary = False
        contact.entity_ids.append(entity_id)
        contact.preferences["preferred_method"] = "email"
        contacts.append(contact)
        
        return contacts
    
    def process_alert(self, alert: core_pb.Alert) -> List[core_pb.Notification]:
        """Process agricultural alerts and send farmer notifications"""
        notifications = []
        
        for entity_id in alert.affected_entities:
            contacts = self.get_contacts(entity_id)
            
            for contact in contacts:
                channel = self._get_notification_channel(alert, contact)
                
                notification = core_pb.Notification()
                notification.notification_id = str(uuid.uuid4())
                notification.app_id = self.app_id
                notification.timestamp.CopyFrom(alert.timestamp)
                notification.type = self._get_notification_type(alert)
                notification.channel = channel
                notification.recipient_id = contact.contact_id
                notification.message = self._create_notification_message(alert, contact)
                notification.sent_successfully = self._simulate_send_notification(channel)
                notification.alert_id = alert.alert_id
                
                notifications.append(notification)
        
        return notifications
    
    def generate_summary(self, entity_id: str, period: str, alerts: List[core_pb.Alert], 
                        notifications: List[core_pb.Notification]) -> core_pb.ApplicationSummary:
        """Generate agricultural summary report"""
        summary = core_pb.ApplicationSummary()
        summary.summary_id = str(uuid.uuid4())
        summary.app_id = self.app_id
        summary.timestamp.CopyFrom(to_timestamp(datetime.utcnow()))
        summary.period = period
        summary.alerts.extend(alerts)
        summary.notifications.extend(notifications)
        summary.entity_ids.append(entity_id)
        
        # Calculate metrics
        summary.metrics["total_alerts"] = len(alerts)
        summary.metrics["drought_alerts"] = len([a for a in alerts if a.type == "DROUGHT_WARNING"])
        summary.metrics["frost_alerts"] = len([a for a in alerts if a.type == "FROST_WARNING"])
        summary.metrics["nutrient_alerts"] = len([a for a in alerts if a.type == "NUTRIENT_DEFICIENCY"])
        summary.metrics["notifications_sent"] = len(notifications)
        
        # Generate summary text
        total_alerts = len(alerts)
        drought_count = summary.metrics["drought_alerts"]
        frost_count = summary.metrics["frost_alerts"]
        
        if total_alerts == 0:
            summary.summary_text = f"Field {entity_id}: No alerts during {period}. Crop conditions normal."
        else:
            summary.summary_text = (f"Field {entity_id}: {total_alerts} alerts during {period}. "
                                  f"Drought warnings: {drought_count}, Frost warnings: {frost_count}. "
                                  f"{len(notifications)} notifications sent to farm team.")
        
        return summary
    
    def _get_notification_channel(self, alert: core_pb.Alert, contact: core_pb.Contact) -> str:
        """Determine notification channel based on alert and contact"""
        if alert.severity == "critical":
            return "SMS"  # Critical agricultural alerts via SMS
        else:
            return contact.preferences.get("preferred_method", "EMAIL").upper()
    
    def _get_notification_type(self, alert: core_pb.Alert) -> str:
        """Map alert types to notification types"""
        if alert.severity == "critical":
            return "URGENT_FARM_ALERT"
        else:
            return "FARM_UPDATE"
    
    def _create_notification_message(self, alert: core_pb.Alert, contact: core_pb.Contact) -> str:
        """Create agricultural notification message"""
        field_id = alert.affected_entities[0] if alert.affected_entities else "Unknown"
        
        if alert.type == "DROUGHT_WARNING":
            return f"DROUGHT ALERT: Field {field_id} needs irrigation. {alert.message}"
        elif alert.type == "FROST_WARNING":
            return f"FROST WARNING: Protect crops in Field {field_id}. {alert.message}"
        elif alert.type == "NUTRIENT_DEFICIENCY":
            return f"FERTILIZER NEEDED: Field {field_id} has nutrient deficiency. {alert.message}"
        else:
            return f"FARM ALERT: {alert.message}"
    
    def _simulate_send_notification(self, channel: str) -> bool:
        """Simulate sending notification"""
        success_rates = {"SMS": 0.95, "EMAIL": 0.98, "CALL": 0.85}
        return random.random() < success_rates.get(channel, 0.9)


# Utility functions for creating agriculture data packets
def create_crop_sensor_data_packet(sensor_reading: agriculture_pb.CropSensorReading) -> core_pb.DataPacket:
    """Create a DataPacket from a CropSensorReading"""
    packet = core_pb.DataPacket()
    packet.packet_id = str(uuid.uuid4())
    packet.app_id = "agriculture"
    packet.timestamp.CopyFrom(sensor_reading.timestamp)
    packet.data_type = "crop_sensor_reading"
    packet.source_id = sensor_reading.sensor_id
    packet.payload = sensor_reading.SerializeToString()
    packet.metadata["field_id"] = sensor_reading.field_id
    packet.metadata["crop_type"] = sensor_reading.crop_type
    return packet


def create_farming_event_data_packet(farming_event: agriculture_pb.FarmingEvent) -> core_pb.DataPacket:
    """Create a DataPacket from a FarmingEvent"""
    packet = core_pb.DataPacket()
    packet.packet_id = str(uuid.uuid4())
    packet.app_id = "agriculture"
    packet.timestamp.CopyFrom(farming_event.timestamp)
    packet.data_type = "farming_event"
    packet.source_id = farming_event.operator_id
    packet.payload = farming_event.SerializeToString()
    packet.metadata["field_id"] = farming_event.field_id
    packet.metadata["activity_type"] = farming_event.activity_type
    return packet