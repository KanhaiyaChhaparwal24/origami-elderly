from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime
from typing import Any, List, Dict, Union, Optional
import uuid
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom
import csv
import io
import hashlib
import yaml

import generated.origami.core_pb2 as core_pb
import generated.origami.elderly_pb2 as elderly_pb
import generated.origami.agriculture_pb2 as agriculture_pb
import generated.origami.security_pb2 as security_pb


def to_timestamp(dt: datetime) -> Timestamp:
    """Convert Python datetime to Protobuf Timestamp"""
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


# ============================================================================
# GENERIC DATA FORMAT HANDLING
# ============================================================================

class DataFormatHandler:
    """Handles conversion between different data formats"""
    
    @staticmethod
    def create_generic_data(data: Union[str, bytes, dict, list], 
                          data_format: core_pb.DataFormat, 
                          content_type: str = "",
                          metadata: Dict[str, str] = None) -> core_pb.GenericData:
        """Create GenericData message with automatic format handling"""
        generic_data = core_pb.GenericData()
        generic_data.format = data_format
        
        # Convert data to bytes based on format
        if data_format == core_pb.DataFormat.JSON:
            if isinstance(data, (dict, list)):
                raw_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif isinstance(data, str):
                raw_data = data.encode('utf-8')
            else:
                raw_data = data
            generic_data.content_type = content_type or "application/json"
            
        elif data_format == core_pb.DataFormat.XML:
            if isinstance(data, str):
                raw_data = data.encode('utf-8')
            elif isinstance(data, dict):
                raw_data = DataFormatHandler._dict_to_xml(data).encode('utf-8')
            else:
                raw_data = data
            generic_data.content_type = content_type or "application/xml"
            
        elif data_format == core_pb.DataFormat.CSV:
            if isinstance(data, (list, dict)):
                raw_data = DataFormatHandler._to_csv(data).encode('utf-8')
            else:
                raw_data = data if isinstance(data, bytes) else str(data).encode('utf-8')
            generic_data.content_type = content_type or "text/csv"
            
        elif data_format == core_pb.DataFormat.YAML:
            if isinstance(data, (dict, list)):
                raw_data = yaml.dump(data, default_flow_style=False).encode('utf-8')
            else:
                raw_data = data if isinstance(data, bytes) else str(data).encode('utf-8')
            generic_data.content_type = content_type or "application/x-yaml"
            
        elif data_format == core_pb.DataFormat.TEXT:
            raw_data = data if isinstance(data, bytes) else str(data).encode('utf-8')
            generic_data.content_type = content_type or "text/plain"
            
        else:  # BINARY, PROTOBUF, or others
            raw_data = data if isinstance(data, bytes) else str(data).encode('utf-8')
            generic_data.content_type = content_type or "application/octet-stream"
        
        generic_data.raw_data = raw_data
        generic_data.size_bytes = len(raw_data)
        generic_data.checksum = hashlib.sha256(raw_data).hexdigest()
        
        # Add format metadata
        if metadata:
            for key, value in metadata.items():
                generic_data.format_metadata[key] = value
        
        # Add encoding info
        if data_format in [core_pb.DataFormat.JSON, core_pb.DataFormat.XML, 
                          core_pb.DataFormat.CSV, core_pb.DataFormat.YAML, 
                          core_pb.DataFormat.TEXT]:
            generic_data.format_metadata["encoding"] = "utf-8"
        
        return generic_data
    
    @staticmethod
    def extract_data(generic_data: core_pb.GenericData, 
                    return_type: str = "auto") -> Union[str, bytes, dict, list]:
        """Extract data from GenericData message"""
        raw_data = generic_data.raw_data
        data_format = generic_data.format
        
        if return_type == "bytes":
            return raw_data
        
        # Auto-detect return type based on format
        if data_format == core_pb.DataFormat.JSON:
            try:
                return json.loads(raw_data.decode('utf-8'))
            except:
                return raw_data.decode('utf-8')
                
        elif data_format == core_pb.DataFormat.XML:
            if return_type == "dict":
                return DataFormatHandler._xml_to_dict(raw_data.decode('utf-8'))
            return raw_data.decode('utf-8')
            
        elif data_format == core_pb.DataFormat.CSV:
            if return_type == "list":
                return DataFormatHandler._csv_to_list(raw_data.decode('utf-8'))
            return raw_data.decode('utf-8')
            
        elif data_format == core_pb.DataFormat.YAML:
            try:
                return yaml.safe_load(raw_data.decode('utf-8'))
            except:
                return raw_data.decode('utf-8')
                
        elif data_format == core_pb.DataFormat.TEXT:
            return raw_data.decode('utf-8')
            
        else:  # BINARY, PROTOBUF, or others
            return raw_data
    
    @staticmethod
    def _dict_to_xml(data: dict, root_name: str = "data") -> str:
        """Convert dictionary to XML string"""
        root = ET.Element(root_name)
        DataFormatHandler._dict_to_xml_element(data, root)
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = xml.dom.minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    @staticmethod
    def _dict_to_xml_element(data: dict, parent: ET.Element):
        """Helper to convert dict to XML elements"""
        for key, value in data.items():
            child = ET.SubElement(parent, str(key))
            if isinstance(value, dict):
                DataFormatHandler._dict_to_xml_element(value, child)
            elif isinstance(value, list):
                for item in value:
                    item_elem = ET.SubElement(child, "item")
                    if isinstance(item, dict):
                        DataFormatHandler._dict_to_xml_element(item, item_elem)
                    else:
                        item_elem.text = str(item)
            else:
                child.text = str(value)
    
    @staticmethod
    def _xml_to_dict(xml_string: str) -> dict:
        """Convert XML string to dictionary"""
        root = ET.fromstring(xml_string)
        return DataFormatHandler._xml_element_to_dict(root)
    
    @staticmethod
    def _xml_element_to_dict(element: ET.Element) -> dict:
        """Helper to convert XML element to dict"""
        result = {}
        if element.text and element.text.strip():
            result = element.text.strip()
        
        for child in element:
            child_data = DataFormatHandler._xml_element_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    @staticmethod
    def _to_csv(data: Union[list, dict]) -> str:
        """Convert data to CSV string"""
        output = io.StringIO()
        
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        elif isinstance(data, dict):
            # Single dictionary
            writer = csv.writer(output)
            for key, value in data.items():
                writer.writerow([key, value])
        else:
            # Fallback
            writer = csv.writer(output)
            if isinstance(data, list):
                for item in data:
                    writer.writerow([item] if not isinstance(item, list) else item)
            else:
                writer.writerow([data])
        
        return output.getvalue()
    
    @staticmethod
    def _csv_to_list(csv_string: str) -> list:
        """Convert CSV string to list of dictionaries"""
        input_stream = io.StringIO(csv_string)
        reader = csv.DictReader(input_stream)
        return list(reader)


# ============================================================================
# ENHANCED GENERIC DATA PACKET FUNCTIONS
# ============================================================================

def create_data_packet_generic(app_id: str, data_type: str, source_id: str, 
                             data: Union[str, bytes, dict, list],
                             data_format: core_pb.DataFormat = core_pb.DataFormat.JSON,
                             metadata: dict = None, timestamp: datetime = None,
                             schema_version: str = "1.0") -> core_pb.DataPacket:
    """Create a generic DataPacket with flexible data format support"""
    packet = core_pb.DataPacket()
    packet.packet_id = str(uuid.uuid4())
    packet.app_id = app_id
    packet.data_type = data_type
    packet.source_id = source_id
    packet.schema_version = schema_version
    
    # Handle different data formats
    if data_format == core_pb.DataFormat.JSON:
        if isinstance(data, str):
            packet.json_data = data
        else:
            packet.json_data = json.dumps(data, ensure_ascii=False)
    elif data_format == core_pb.DataFormat.XML:
        packet.xml_data = data if isinstance(data, str) else str(data)
    elif data_format == core_pb.DataFormat.TEXT:
        packet.text_data = data if isinstance(data, str) else str(data)
    else:
        # Use GenericData for other formats
        packet.generic_data.CopyFrom(
            DataFormatHandler.create_generic_data(data, data_format)
        )
    
    if timestamp:
        packet.timestamp.CopyFrom(to_timestamp(timestamp))
    else:
        packet.timestamp.CopyFrom(to_timestamp(datetime.utcnow()))
    
    if metadata:
        for key, value in metadata.items():
            packet.metadata[key] = str(value)
    
    return packet


# Legacy DataPacket function (for backward compatibility)
def create_data_packet(app_id: str, data_type: str, source_id: str, payload: bytes, 
                      metadata: dict = None, timestamp: datetime = None) -> core_pb.DataPacket:
    """Create a generic DataPacket (legacy protobuf payload)"""
    packet = core_pb.DataPacket()
    packet.packet_id = str(uuid.uuid4())
    packet.app_id = app_id
    packet.data_type = data_type
    packet.source_id = source_id
    packet.payload = payload
    
    if timestamp:
        packet.timestamp.CopyFrom(to_timestamp(timestamp))
    else:
        packet.timestamp.CopyFrom(to_timestamp(datetime.utcnow()))
    
    if metadata:
        for key, value in metadata.items():
            packet.metadata[key] = str(value)
    
    return packet


def extract_packet_data(packet: core_pb.DataPacket, 
                       return_format: str = "auto") -> Union[str, bytes, dict, list]:
    """Extract data from DataPacket regardless of format"""
    # Check which data field is set
    if packet.HasField("json_data"):
        if return_format == "dict":
            return json.loads(packet.json_data)
        return packet.json_data
    elif packet.HasField("xml_data"):
        if return_format == "dict":
            return DataFormatHandler._xml_to_dict(packet.xml_data)
        return packet.xml_data
    elif packet.HasField("text_data"):
        return packet.text_data
    elif packet.HasField("generic_data"):
        return DataFormatHandler.extract_data(packet.generic_data, return_format)
    elif packet.HasField("payload"):
        return packet.payload
    else:
        return None


def create_alert_with_data(app_id: str, alert_type: str, severity: str, message: str,
                          score: float = 0.0, context: dict = None,
                          alert_data: Union[str, dict, list] = None,
                          data_format: core_pb.DataFormat = core_pb.DataFormat.JSON,
                          affected_entities: List[str] = None,
                          source_packet_id: str = "") -> core_pb.Alert:
    """Create an Alert with structured data support"""
    alert = core_pb.Alert()
    alert.alert_id = str(uuid.uuid4())
    alert.app_id = app_id
    alert.timestamp.CopyFrom(to_timestamp(datetime.utcnow()))
    alert.type = alert_type
    alert.severity = severity
    alert.message = message
    alert.score = score
    alert.source_packet_id = source_packet_id
    
    if context:
        for key, value in context.items():
            alert.context[key] = str(value)
    
    if affected_entities:
        alert.affected_entities.extend(affected_entities)
    
    # Add structured alert data
    if alert_data:
        if data_format == core_pb.DataFormat.JSON:
            if isinstance(alert_data, str):
                alert.json_details = alert_data
            else:
                alert.json_details = json.dumps(alert_data, ensure_ascii=False)
        else:
            alert.generic_alert_data.CopyFrom(
                DataFormatHandler.create_generic_data(alert_data, data_format)
            )
    
    return alert


def create_notification_with_content(app_id: str, notification_type: str, channel: str,
                                   recipient_id: str, content: Union[str, dict],
                                   content_format: str = "text",
                                   alert_id: str = "",
                                   template_id: str = "") -> core_pb.Notification:
    """Create a Notification with rich content support"""
    notification = core_pb.Notification()
    notification.notification_id = str(uuid.uuid4())
    notification.app_id = app_id
    notification.timestamp.CopyFrom(to_timestamp(datetime.utcnow()))
    notification.type = notification_type
    notification.channel = channel
    notification.recipient_id = recipient_id
    notification.alert_id = alert_id
    notification.template_id = template_id
    notification.sent_successfully = False  # Set to True after successful delivery
    
    # Handle different content formats
    if content_format == "html":
        notification.html_content = content if isinstance(content, str) else str(content)
        notification.message = notification.html_content  # Fallback
    elif content_format == "rich" and isinstance(content, dict):
        notification.rich_content.CopyFrom(
            DataFormatHandler.create_generic_data(content, core_pb.DataFormat.JSON)
        )
        notification.message = json.dumps(content)  # Fallback
    else:
        notification.text_content = content if isinstance(content, str) else str(content)
        notification.message = notification.text_content  # Fallback
    
    return notification


def serialize_data_packet(data_packet: core_pb.DataPacket) -> bytes:
    """Serialize a DataPacket to binary format"""
    return data_packet.SerializeToString()


def deserialize_data_packet(data: bytes) -> core_pb.DataPacket:
    """Deserialize binary data to DataPacket"""
    packet = core_pb.DataPacket()
    packet.ParseFromString(data)
    return packet


def serialize_alert(alert: core_pb.Alert) -> bytes:
    """Serialize an Alert to binary format"""
    return alert.SerializeToString()


def deserialize_alert(data: bytes) -> core_pb.Alert:
    """Deserialize binary data to Alert"""
    alert = core_pb.Alert()
    alert.ParseFromString(data)
    return alert


def serialize_application_summary(summary: core_pb.ApplicationSummary) -> bytes:
    """Serialize an ApplicationSummary to binary format"""
    return summary.SerializeToString()


def deserialize_application_summary(data: bytes) -> core_pb.ApplicationSummary:
    """Deserialize binary data to ApplicationSummary"""
    summary = core_pb.ApplicationSummary()
    summary.ParseFromString(data)
    return summary


# Legacy elderly care support functions (for backward compatibility)
def build_sensor_reading(device_id: str, patient_id: str, dt: datetime, vitals: dict, fall_detected: bool = False) -> elderly_pb.SensorReading:
    """Build elderly sensor reading (legacy support)"""
    r = elderly_pb.SensorReading()
    r.device_id = device_id
    r.patient_id = patient_id
    r.timestamp.CopyFrom(to_timestamp(dt))
    r.vitals.heart_rate = vitals.get("heart_rate", 0.0)
    r.vitals.spo2 = vitals.get("spo2", 0.0)
    r.vitals.body_temp = vitals.get("body_temp", 0.0)
    r.vitals.systolic = vitals.get("systolic", 0.0)
    r.vitals.diastolic = vitals.get("diastolic", 0.0)
    r.fall_detected = fall_detected
    return r


def build_medication_event(patient_id: str, med_id: str, med_name: str, scheduled: datetime, taken: datetime = None) -> elderly_pb.MedicationEvent:
    """Build medication event (legacy support)"""
    m = elderly_pb.MedicationEvent()
    m.patient_id = patient_id
    m.medication_id = med_id
    m.medication_name = med_name
    m.scheduled_time.CopyFrom(to_timestamp(scheduled))
    if taken:
        m.taken_time.CopyFrom(to_timestamp(taken))
        m.taken = True
    else:
        m.taken = False
    return m


def build_emergency_contact(contact_id: str, name: str, relationship: str, phone: str, email: str = "", 
                          is_primary: bool = False, notify_on_alert: bool = True) -> elderly_pb.EmergencyContact:
    """Build emergency contact (legacy support)"""
    contact = elderly_pb.EmergencyContact()
    contact.contact_id = contact_id
    contact.name = name
    contact.relationship = relationship
    contact.phone = phone
    contact.email = email
    contact.is_primary = is_primary
    contact.notify_on_alert = notify_on_alert
    return contact


def build_family_communication(patient_id: str, contact_id: str, dt: datetime, comm_type: str, 
                             message: str, successful: bool = True, alert_id: str = "") -> elderly_pb.FamilyCommunication:
    """Build family communication (legacy support)"""
    comm = elderly_pb.FamilyCommunication()
    comm.patient_id = patient_id
    comm.contact_id = contact_id
    comm.timestamp.CopyFrom(to_timestamp(dt))
    comm.communication_type = comm_type
    comm.message = message
    comm.successful = successful
    comm.alert_id = alert_id
    return comm


def build_elderly_record(patient_id: str, name: str, age: int, readings: List[elderly_pb.SensorReading], 
                        meds: List[elderly_pb.MedicationEvent], contacts: List[elderly_pb.EmergencyContact] = None, 
                        communications: List[elderly_pb.FamilyCommunication] = None) -> elderly_pb.ElderlyRecord:
    """Build elderly record (legacy support)"""
    rec = elderly_pb.ElderlyRecord()
    rec.patient_id = patient_id
    rec.name = name
    rec.age = age
    rec.sensor_readings.extend(readings)
    rec.medication_events.extend(meds)
    if contacts:
        rec.emergency_contacts.extend(contacts)
    if communications:
        rec.family_communications.extend(communications)
    return rec


def serialize_record(record: elderly_pb.ElderlyRecord) -> bytes:
    """Serialize elderly record (legacy support)"""
    return record.SerializeToString()


def deserialize_record(data: bytes) -> elderly_pb.ElderlyRecord:
    """Deserialize elderly record (legacy support)"""
    rec = elderly_pb.ElderlyRecord()
    rec.ParseFromString(data)
    return rec
