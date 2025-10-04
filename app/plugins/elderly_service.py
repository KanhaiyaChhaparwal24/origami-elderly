"""
Elderly Care Plugin for Origami Framework
Handles elderly patient monitoring, family communications, and healthcare alerts
Enhanced with multi-format data support (JSON, XML, protobuf, etc.)
"""

from typing import List, Optional, Any, Union, Dict
from datetime import datetime
import uuid
import random
import json

import generated.origami.core_pb2 as core_pb
import generated.origami.elderly_pb2 as elderly_pb
from app.registry import PluginInterface
from app.serializer import DataFormatHandler, extract_packet_data, create_alert_with_data, create_notification_with_content
from google.protobuf.timestamp_pb2 import Timestamp


def to_timestamp(dt: datetime) -> Timestamp:
    """Convert Python datetime to Protobuf Timestamp"""
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


class ElderlyServicePlugin(PluginInterface):
    """Plugin for elderly care monitoring and family communication"""
    
    @property
    def app_id(self) -> str:
        return "elderly_care"
    
    @property
    def app_name(self) -> str:
        return "Elderly Care Monitoring"
    
    @property
    def supported_data_types(self) -> List[str]:
        return ["sensor_reading", "medication_event", "emergency_contact", "family_communication", 
                "vitals_json", "patient_data_xml", "sensor_csv"]  # Added multi-format support
    
    def parse_data_packet(self, data_packet: core_pb.DataPacket) -> Any:
        """Parse DataPacket payload supporting multiple data formats"""
        try:
            # Handle new generic data formats
            if data_packet.data_type in ["vitals_json", "patient_data_xml", "sensor_csv"]:
                # Extract data in appropriate format
                extracted_data = extract_packet_data(data_packet, return_format="auto")
                
                if data_packet.data_type == "vitals_json":
                    return self._parse_vitals_json(extracted_data)
                elif data_packet.data_type == "patient_data_xml":
                    return self._parse_patient_xml(extracted_data)
                elif data_packet.data_type == "sensor_csv":
                    return self._parse_sensor_csv(extracted_data)
            
            # Handle legacy protobuf formats
            elif data_packet.HasField("payload"):
                if data_packet.data_type == "sensor_reading":
                    sensor_reading = elderly_pb.SensorReading()
                    sensor_reading.ParseFromString(data_packet.payload)
                    return sensor_reading
                    
                elif data_packet.data_type == "medication_event":
                    medication_event = elderly_pb.MedicationEvent()
                    medication_event.ParseFromString(data_packet.payload)
                    return medication_event
                    
                elif data_packet.data_type == "emergency_contact":
                    emergency_contact = elderly_pb.EmergencyContact()
                    emergency_contact.ParseFromString(data_packet.payload)
                    return emergency_contact
                    
                elif data_packet.data_type == "family_communication":
                    family_comm = elderly_pb.FamilyCommunication()
                    family_comm.ParseFromString(data_packet.payload)
                    return family_comm
            
            # Handle direct JSON/XML/text data
            elif data_packet.HasField("json_data"):
                return json.loads(data_packet.json_data)
            elif data_packet.HasField("xml_data"):
                return DataFormatHandler._xml_to_dict(data_packet.xml_data)
            elif data_packet.HasField("text_data"):
                return {"text_content": data_packet.text_data, "data_type": data_packet.data_type}
            else:
                raise ValueError(f"No data content found in packet")
                
        except Exception as e:
            print(f"Error parsing elderly data packet: {e}")
            return None
    
    def _parse_vitals_json(self, data: Dict) -> Dict:
        """Parse JSON vitals data"""
        return {
            "type": "vitals_json",
            "patient_id": data.get("patient_id", "unknown"),
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
            "heart_rate": data.get("heart_rate", 0),
            "spo2": data.get("spo2", 0),
            "temperature": data.get("temperature", 0),
            "blood_pressure": data.get("blood_pressure", {}),
            "device_info": data.get("device_info", {}),
            "raw_data": data
        }
    
    def _parse_patient_xml(self, data: Union[str, Dict]) -> Dict:
        """Parse XML patient data"""
        if isinstance(data, str):
            data = DataFormatHandler._xml_to_dict(data)
        
        return {
            "type": "patient_xml",
            "patient_id": data.get("patient_id", "unknown"),
            "patient_info": data.get("patient_info", {}),
            "medical_history": data.get("medical_history", {}),
            "current_medications": data.get("medications", []),
            "raw_data": data
        }
    
    def _parse_sensor_csv(self, data: Union[str, List]) -> Dict:
        """Parse CSV sensor data"""
        if isinstance(data, str):
            data = DataFormatHandler._csv_to_list(data)
        
        return {
            "type": "sensor_csv",
            "readings": data,
            "count": len(data) if isinstance(data, list) else 1,
            "raw_data": data
        }
    
    def generate_alerts(self, parsed_data: Any, app_config: Optional[core_pb.ApplicationConfig] = None) -> List[core_pb.Alert]:
        """Generate healthcare alerts from elderly monitoring data (multi-format support)"""
        alerts = []
        
        # Get thresholds from config or use defaults
        heart_rate_threshold = 120
        spo2_threshold = 90
        
        if app_config and app_config.thresholds:
            heart_rate_threshold = app_config.thresholds.get("heart_rate_high", 120)
            spo2_threshold = app_config.thresholds.get("spo2_low", 90)
        
        # Handle protobuf sensor readings (legacy)
        if isinstance(parsed_data, elderly_pb.SensorReading):
            alerts.extend(self._process_protobuf_sensor_data(parsed_data, heart_rate_threshold, spo2_threshold))
        
        # Handle protobuf medication events (legacy)
        elif isinstance(parsed_data, elderly_pb.MedicationEvent):
            alerts.extend(self._process_protobuf_medication_data(parsed_data))
        
        # Handle JSON vitals data
        elif isinstance(parsed_data, dict) and parsed_data.get("type") == "vitals_json":
            alerts.extend(self._process_json_vitals_data(parsed_data, heart_rate_threshold, spo2_threshold))
        
        # Handle XML patient data
        elif isinstance(parsed_data, dict) and parsed_data.get("type") == "patient_xml":
            alerts.extend(self._process_xml_patient_data(parsed_data))
        
        # Handle CSV sensor data
        elif isinstance(parsed_data, dict) and parsed_data.get("type") == "sensor_csv":
            alerts.extend(self._process_csv_sensor_data(parsed_data, heart_rate_threshold, spo2_threshold))
        
        # Handle generic JSON data
        elif isinstance(parsed_data, dict):
            alerts.extend(self._process_generic_json_data(parsed_data, heart_rate_threshold, spo2_threshold))
        
        return alerts
    
    def _process_protobuf_sensor_data(self, sensor_data: elderly_pb.SensorReading, 
                                    hr_threshold: float, spo2_threshold: float) -> List[core_pb.Alert]:
        """Process legacy protobuf sensor data"""
        alerts = []
        
        # Fall detection alert
        if sensor_data.fall_detected:
            alert = create_alert_with_data(
                app_id=self.app_id,
                alert_type="FALL_DETECTED",
                severity="emergency",
                message=f"Fall detected for patient {sensor_data.patient_id}",
                score=1.0,
                context={"device_id": sensor_data.device_id},
                affected_entities=[sensor_data.patient_id],
                alert_data={"device_id": sensor_data.device_id, "timestamp": sensor_data.timestamp.ToDatetime().isoformat()},
                data_format=core_pb.DataFormat.JSON
            )
            alerts.append(alert)
        
        # Vital signs anomaly alerts
        vitals = sensor_data.vitals
        if vitals.heart_rate > hr_threshold or vitals.spo2 < spo2_threshold:
            severity = "critical" if vitals.heart_rate > 150 or vitals.spo2 < 85 else "warning"
            alert = create_alert_with_data(
                app_id=self.app_id,
                alert_type="VITALS_ANOMALY",
                severity=severity,
                message=f"Abnormal vitals: HR={vitals.heart_rate}, SpO2={vitals.spo2}%",
                score=0.9 if severity == "critical" else 0.7,
                context={"heart_rate": str(vitals.heart_rate), "spo2": str(vitals.spo2)},
                affected_entities=[sensor_data.patient_id],
                alert_data={"vitals": {"heart_rate": vitals.heart_rate, "spo2": vitals.spo2, "temperature": vitals.body_temp}},
                data_format=core_pb.DataFormat.JSON
            )
            alerts.append(alert)
        
        return alerts
    
    def _process_protobuf_medication_data(self, med_data: elderly_pb.MedicationEvent) -> List[core_pb.Alert]:
        """Process legacy protobuf medication data"""
        alerts = []
        
        if not med_data.taken:
            alert = create_alert_with_data(
                app_id=self.app_id,
                alert_type="MEDICATION_MISSED",
                severity="warning",
                message=f"Missed medication: {med_data.medication_name}",
                score=0.8,
                context={"medication_name": med_data.medication_name},
                affected_entities=[med_data.patient_id],
                alert_data={"medication": med_data.medication_name, "scheduled_time": med_data.scheduled_time.ToDatetime().isoformat()},
                data_format=core_pb.DataFormat.JSON
            )
            alerts.append(alert)
        
        return alerts
    
    def _process_json_vitals_data(self, vitals_data: Dict, hr_threshold: float, spo2_threshold: float) -> List[core_pb.Alert]:
        """Process JSON format vitals data"""
        alerts = []
        
        heart_rate = vitals_data.get("heart_rate", 0)
        spo2 = vitals_data.get("spo2", 0)
        patient_id = vitals_data.get("patient_id", "unknown")
        
        if heart_rate > hr_threshold or spo2 < spo2_threshold:
            severity = "critical" if heart_rate > 150 or spo2 < 85 else "warning"
            alert = create_alert_with_data(
                app_id=self.app_id,
                alert_type="VITALS_ANOMALY_JSON",
                severity=severity,
                message=f"Abnormal vitals from JSON data: HR={heart_rate}, SpO2={spo2}%",
                score=0.9 if severity == "critical" else 0.7,
                context={"source_format": "JSON", "heart_rate": str(heart_rate), "spo2": str(spo2)},
                affected_entities=[patient_id],
                alert_data=vitals_data.get("raw_data", vitals_data),
                data_format=core_pb.DataFormat.JSON
            )
            alerts.append(alert)
        
        return alerts
    
    def _process_xml_patient_data(self, patient_data: Dict) -> List[core_pb.Alert]:
        """Process XML format patient data"""
        alerts = []
        
        patient_id = patient_data.get("patient_id", "unknown")
        medical_history = patient_data.get("medical_history", {})
        
        # Check for high-risk conditions in medical history
        if "diabetes" in str(medical_history).lower() or "heart_disease" in str(medical_history).lower():
            alert = create_alert_with_data(
                app_id=self.app_id,
                alert_type="HIGH_RISK_PATIENT",
                severity="info",
                message=f"High-risk patient profile detected from XML data",
                score=0.6,
                context={"source_format": "XML", "risk_factors": str(medical_history)},
                affected_entities=[patient_id],
                alert_data=patient_data.get("raw_data", patient_data),
                data_format=core_pb.DataFormat.JSON
            )
            alerts.append(alert)
        
        return alerts
    
    def _process_csv_sensor_data(self, csv_data: Dict, hr_threshold: float, spo2_threshold: float) -> List[core_pb.Alert]:
        """Process CSV format sensor data"""
        alerts = []
        
        readings = csv_data.get("readings", [])
        if not readings:
            return alerts
        
        # Analyze readings for patterns
        high_hr_count = sum(1 for reading in readings if float(reading.get("heart_rate", 0)) > hr_threshold)
        low_spo2_count = sum(1 for reading in readings if float(reading.get("spo2", 100)) < spo2_threshold)
        
        if high_hr_count > len(readings) * 0.5:  # More than 50% of readings show high HR
            alert = create_alert_with_data(
                app_id=self.app_id,
                alert_type="PATTERN_ANOMALY_CSV",
                severity="warning",
                message=f"Pattern anomaly detected in CSV data: {high_hr_count}/{len(readings)} readings show elevated heart rate",
                score=0.8,
                context={"source_format": "CSV", "readings_count": str(len(readings)), "anomaly_count": str(high_hr_count)},
                affected_entities=["csv_patient"],
                alert_data={"summary": f"High HR in {high_hr_count}/{len(readings)} readings", "sample_data": readings[:3]},
                data_format=core_pb.DataFormat.JSON
            )
            alerts.append(alert)
        
        return alerts
    
    def _process_generic_json_data(self, json_data: Dict, hr_threshold: float, spo2_threshold: float) -> List[core_pb.Alert]:
        """Process generic JSON data"""
        alerts = []
        
        # Look for common health-related fields
        if "emergency" in str(json_data).lower() or "urgent" in str(json_data).lower():
            alert = create_alert_with_data(
                app_id=self.app_id,
                alert_type="EMERGENCY_KEYWORD_DETECTED",
                severity="warning",
                message="Emergency keywords detected in JSON data",
                score=0.7,
                context={"source_format": "JSON", "keywords_found": "emergency/urgent"},
                affected_entities=["generic_patient"],
                alert_data=json_data,
                data_format=core_pb.DataFormat.JSON
            )
            alerts.append(alert)
        
        return alerts
    
    def get_contacts(self, entity_id: str) -> List[core_pb.Contact]:
        """Get emergency contacts for a patient"""
        # In a real implementation, this would query a database
        # For now, return sample contacts
        contacts = []
        
        # Primary family contact
        contact = core_pb.Contact()
        contact.contact_id = "contact_001"
        contact.app_id = self.app_id
        contact.name = "John Smith (Son)"
        contact.role = "family"
        contact.phone = "+1-555-0123"
        contact.email = "john.smith@email.com"
        contact.is_primary = True
        contact.entity_ids.append(entity_id)
        contact.preferences["preferred_method"] = "phone"
        contacts.append(contact)
        
        # Doctor contact
        contact = core_pb.Contact()
        contact.contact_id = "contact_002"
        contact.app_id = self.app_id
        contact.name = "Dr. Sarah Johnson"
        contact.role = "doctor"
        contact.phone = "+1-555-0199"
        contact.email = "dr.johnson@hospital.com"
        contact.is_primary = False
        contact.entity_ids.append(entity_id)
        contact.preferences["preferred_method"] = "email"
        contacts.append(contact)
        
        return contacts
    
    def process_alert(self, alert: core_pb.Alert) -> List[core_pb.Notification]:
        """Process healthcare alerts and send family notifications"""
        notifications = []
        
        # Get affected entity (patient) contacts
        for entity_id in alert.affected_entities:
            contacts = self.get_contacts(entity_id)
            
            for contact in contacts:
                # Determine notification channel based on alert severity and contact preferences
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
        """Generate elderly care summary report"""
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
        summary.metrics["critical_alerts"] = len([a for a in alerts if a.severity == "critical"])
        summary.metrics["emergency_alerts"] = len([a for a in alerts if a.severity == "emergency"])
        summary.metrics["notifications_sent"] = len(notifications)
        summary.metrics["successful_notifications"] = len([n for n in notifications if n.sent_successfully])
        
        # Generate summary text
        total_alerts = len(alerts)
        critical_count = summary.metrics["critical_alerts"]
        emergency_count = summary.metrics["emergency_alerts"]
        
        if total_alerts == 0:
            summary.summary_text = f"Patient {entity_id}: No health alerts during {period}. All systems normal."
        else:
            summary.summary_text = (f"Patient {entity_id}: {total_alerts} health alerts during {period}. "
                                  f"Emergency: {emergency_count}, Critical: {critical_count}. "
                                  f"{len(notifications)} family notifications sent.")
        
        return summary
    
    def _get_notification_channel(self, alert: core_pb.Alert, contact: core_pb.Contact) -> str:
        """Determine the best notification channel based on alert severity and contact preferences"""
        if alert.severity == "emergency":
            return "CALL"  # Emergency situations need immediate phone contact
        elif alert.severity == "critical":
            return "SMS"   # Critical alerts via SMS for quick delivery
        else:
            # Use contact's preferred method or default to email
            return contact.preferences.get("preferred_method", "EMAIL").upper()
    
    def _get_notification_type(self, alert: core_pb.Alert) -> str:
        """Map alert types to notification types"""
        if alert.severity in ["emergency", "critical"]:
            return "EMERGENCY_ALERT"
        else:
            return "HEALTH_UPDATE"
    
    def _create_notification_message(self, alert: core_pb.Alert, contact: core_pb.Contact) -> str:
        """Create personalized notification message"""
        patient_id = alert.affected_entities[0] if alert.affected_entities else "Unknown"
        
        if alert.type == "FALL_DETECTED":
            return f"EMERGENCY: {patient_id} has fallen. Please check on them immediately."
        elif alert.type == "VITALS_ANOMALY":
            return f"HEALTH ALERT: {patient_id} has abnormal vital signs. {alert.message}"
        elif alert.type == "MEDICATION_MISSED":
            return f"MEDICATION REMINDER: {patient_id} missed their medication. {alert.message}"
        else:
            return f"HEALTH UPDATE: {alert.message}"
    
    def _simulate_send_notification(self, channel: str) -> bool:
        """Simulate sending notification (in real implementation, would use actual services)"""
        # Simulate different success rates for different channels
        success_rates = {
            "CALL": 0.85,
            "SMS": 0.95,
            "EMAIL": 0.98,
            "PUSH": 0.90
        }
        return random.random() < success_rates.get(channel, 0.9)


# Utility functions for creating elderly data packets
def create_sensor_data_packet(sensor_reading: elderly_pb.SensorReading) -> core_pb.DataPacket:
    """Create a DataPacket from a SensorReading"""
    packet = core_pb.DataPacket()
    packet.packet_id = str(uuid.uuid4())
    packet.app_id = "elderly_care"
    packet.timestamp.CopyFrom(sensor_reading.timestamp)
    packet.data_type = "sensor_reading"
    packet.source_id = sensor_reading.device_id
    packet.payload = sensor_reading.SerializeToString()
    packet.metadata["patient_id"] = sensor_reading.patient_id
    packet.metadata["device_id"] = sensor_reading.device_id
    return packet


def create_medication_data_packet(medication_event: elderly_pb.MedicationEvent) -> core_pb.DataPacket:
    """Create a DataPacket from a MedicationEvent"""
    packet = core_pb.DataPacket()
    packet.packet_id = str(uuid.uuid4())
    packet.app_id = "elderly_care"
    packet.timestamp.CopyFrom(medication_event.scheduled_time)
    packet.data_type = "medication_event"
    packet.source_id = medication_event.patient_id
    packet.payload = medication_event.SerializeToString()
    packet.metadata["patient_id"] = medication_event.patient_id
    packet.metadata["medication_name"] = medication_event.medication_name
    return packet