"""
Test suite for generic data format handling in the Origami platform
Tests JSON, XML, CSV, YAML, and other data formats across all applications
"""

import pytest
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List

# Import our modules
import generated.origami.core_pb2 as core_pb
from app.serializer import (
    DataFormatHandler, 
    create_data_packet_generic, 
    extract_packet_data,
    create_alert_with_data,
    create_notification_with_content
)
from app.plugins.elderly_service import ElderlyServicePlugin
from app.plugins.agriculture_service import AgricultureServicePlugin
from app.registry import PluginRegistry


class TestDataFormatHandler:
    """Test the generic data format handler"""
    
    def test_json_format_handling(self):
        """Test JSON data format creation and extraction"""
        test_data = {
            "patient_id": "patient123",
            "heart_rate": 85,
            "blood_pressure": {"systolic": 120, "diastolic": 80},
            "timestamp": "2025-10-01T10:30:00Z"
        }
        
        # Create GenericData with JSON format
        generic_data = DataFormatHandler.create_generic_data(
            test_data, 
            core_pb.DataFormat.JSON
        )
        
        assert generic_data.format == core_pb.DataFormat.JSON
        assert generic_data.content_type == "application/json"
        assert generic_data.size_bytes > 0
        assert len(generic_data.checksum) == 64  # SHA256 hash length
        
        # Extract and verify data
        extracted_data = DataFormatHandler.extract_data(generic_data)
        assert extracted_data == test_data
        assert extracted_data["patient_id"] == "patient123"
        assert extracted_data["heart_rate"] == 85
    
    def test_xml_format_handling(self):
        """Test XML data format creation and extraction"""
        test_data = {
            "patient": {
                "id": "patient456",
                "vitals": {
                    "heart_rate": 92,
                    "temperature": 98.6
                }
            }
        }
        
        # Create GenericData with XML format
        generic_data = DataFormatHandler.create_generic_data(
            test_data,
            core_pb.DataFormat.XML
        )
        
        assert generic_data.format == core_pb.DataFormat.XML
        assert generic_data.content_type == "application/xml"
        
        # Extract as string and verify it's valid XML
        xml_string = DataFormatHandler.extract_data(generic_data, return_type="string")
        assert "<patient>" in xml_string
        assert "<id>patient456</id>" in xml_string
        
        # Extract as dict and verify structure
        extracted_dict = DataFormatHandler.extract_data(generic_data, return_type="dict")
        assert "patient" in extracted_dict
    
    def test_csv_format_handling(self):
        """Test CSV data format creation and extraction"""
        test_data = [
            {"patient_id": "p1", "heart_rate": 75, "timestamp": "2025-10-01T09:00:00Z"},
            {"patient_id": "p2", "heart_rate": 82, "timestamp": "2025-10-01T09:05:00Z"},
            {"patient_id": "p3", "heart_rate": 78, "timestamp": "2025-10-01T09:10:00Z"}
        ]
        
        # Create GenericData with CSV format
        generic_data = DataFormatHandler.create_generic_data(
            test_data,
            core_pb.DataFormat.CSV
        )
        
        assert generic_data.format == core_pb.DataFormat.CSV
        assert generic_data.content_type == "text/csv"
        
        # Extract and verify data
        csv_string = DataFormatHandler.extract_data(generic_data, return_type="string")
        assert "patient_id,heart_rate,timestamp" in csv_string
        assert "p1,75," in csv_string
        
        # Extract as list and verify structure
        extracted_list = DataFormatHandler.extract_data(generic_data, return_type="list")
        assert len(extracted_list) == 3
        assert extracted_list[0]["patient_id"] == "p1"
    
    def test_yaml_format_handling(self):
        """Test YAML data format creation and extraction"""
        test_data = {
            "config": {
                "thresholds": {
                    "heart_rate_max": 120,
                    "spo2_min": 90
                },
                "alerts": ["fall_detection", "vitals_anomaly"]
            }
        }
        
        # Create GenericData with YAML format
        generic_data = DataFormatHandler.create_generic_data(
            test_data,
            core_pb.DataFormat.YAML
        )
        
        assert generic_data.format == core_pb.DataFormat.YAML
        assert generic_data.content_type == "application/x-yaml"
        
        # Extract and verify data
        extracted_data = DataFormatHandler.extract_data(generic_data)
        assert extracted_data["config"]["thresholds"]["heart_rate_max"] == 120
        assert "fall_detection" in extracted_data["config"]["alerts"]


class TestGenericDataPackets:
    """Test generic data packet creation with multiple formats"""
    
    def test_json_data_packet(self):
        """Test creating DataPacket with JSON data"""
        vitals_data = {
            "patient_id": "patient789",
            "heart_rate": 95,
            "spo2": 98,
            "temperature": 99.1,
            "device_id": "monitor_001"
        }
        
        packet = create_data_packet_generic(
            app_id="elderly_care",
            data_type="vitals_json",
            source_id="json_monitor",
            data=vitals_data,
            data_format=core_pb.DataFormat.JSON,
            metadata={"location": "bedroom", "quality": "high"}
        )
        
        assert packet.app_id == "elderly_care"
        assert packet.data_type == "vitals_json"
        assert packet.HasField("json_data")
        
        # Extract and verify data
        extracted = extract_packet_data(packet, return_format="dict")
        assert extracted["patient_id"] == "patient789"
        assert extracted["heart_rate"] == 95
    
    def test_xml_data_packet(self):
        """Test creating DataPacket with XML data"""
        xml_data = """<?xml version="1.0"?>
        <patient_record>
            <patient_id>patient999</patient_id>
            <medical_history>
                <condition>diabetes</condition>
                <condition>hypertension</condition>
            </medical_history>
        </patient_record>"""
        
        packet = create_data_packet_generic(
            app_id="elderly_care",
            data_type="patient_data_xml",
            source_id="xml_system",
            data=xml_data,
            data_format=core_pb.DataFormat.XML
        )
        
        assert packet.app_id == "elderly_care"
        assert packet.data_type == "patient_data_xml"
        assert packet.HasField("xml_data")
        
        # Extract and verify data
        extracted = extract_packet_data(packet, return_format="string")
        assert "patient_id" in extracted
        assert "diabetes" in extracted
    
    def test_text_data_packet(self):
        """Test creating DataPacket with plain text data"""
        text_data = "Patient alert: Blood pressure reading 160/95 at 14:30 - requires immediate attention"
        
        packet = create_data_packet_generic(
            app_id="elderly_care",
            data_type="alert_text",
            source_id="text_monitor",
            data=text_data,
            data_format=core_pb.DataFormat.TEXT
        )
        
        assert packet.app_id == "elderly_care"
        assert packet.data_type == "alert_text"
        assert packet.HasField("text_data")
        
        # Extract and verify data
        extracted = extract_packet_data(packet)
        assert "Blood pressure reading 160/95" in extracted


class TestEnhancedAlerts:
    """Test enhanced alerts with structured data"""
    
    def test_alert_with_json_data(self):
        """Test creating alerts with JSON structured data"""
        alert_details = {
            "sensor_id": "temp_001",
            "location": "greenhouse_A",
            "temperature": 35.2,
            "humidity": 85,
            "threshold_exceeded": "temperature_high"
        }
        
        alert = create_alert_with_data(
            app_id="agriculture",
            alert_type="TEMPERATURE_HIGH",
            severity="warning",
            message="High temperature detected in greenhouse",
            score=0.8,
            alert_data=alert_details,
            data_format=core_pb.DataFormat.JSON,
            affected_entities=["greenhouse_A"]
        )
        
        assert alert.app_id == "agriculture"
        assert alert.type == "TEMPERATURE_HIGH"
        assert alert.severity == "warning"
        assert alert.HasField("json_details")
        
        # Verify JSON details
        json_data = json.loads(alert.json_details)
        assert json_data["temperature"] == 35.2
        assert json_data["location"] == "greenhouse_A"


class TestMultiFormatPluginProcessing:
    """Test that plugins can process multiple data formats"""
    
    def setup_method(self):
        """Set up test environment"""
        self.elderly_plugin = ElderlyServicePlugin()
        self.agriculture_plugin = AgricultureServicePlugin()
    
    def test_elderly_plugin_json_processing(self):
        """Test elderly plugin processing JSON vitals data"""
        # Create JSON vitals packet
        vitals_data = {
            "patient_id": "patient555",
            "heart_rate": 130,  # Above threshold
            "spo2": 95,
            "temperature": 98.6,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        packet = create_data_packet_generic(
            app_id="elderly_care",
            data_type="vitals_json",
            source_id="json_monitor",
            data=vitals_data,
            data_format=core_pb.DataFormat.JSON
        )
        
        # Process through plugin
        parsed_data = self.elderly_plugin.parse_data_packet(packet)
        assert parsed_data is not None
        assert parsed_data["type"] == "vitals_json"
        assert parsed_data["heart_rate"] == 130
        
        # Generate alerts
        alerts = self.elderly_plugin.generate_alerts(parsed_data)
        assert len(alerts) > 0
        
        # Check alert details
        vitals_alert = next((a for a in alerts if a.type == "VITALS_ANOMALY_JSON"), None)
        assert vitals_alert is not None
        assert vitals_alert.severity in ["warning", "critical"]
        assert "JSON" in vitals_alert.context["source_format"]
    
    def test_elderly_plugin_xml_processing(self):
        """Test elderly plugin processing XML patient data"""
        # Create XML patient data packet
        xml_data = """<?xml version="1.0"?>
        <patient_record>
            <patient_id>patient777</patient_id>
            <medical_history>
                <condition>diabetes</condition>
                <condition>heart_disease</condition>
            </medical_history>
        </patient_record>"""
        
        packet = create_data_packet_generic(
            app_id="elderly_care",
            data_type="patient_data_xml",
            source_id="xml_system",
            data=xml_data,
            data_format=core_pb.DataFormat.XML
        )
        
        # Process through plugin
        parsed_data = self.elderly_plugin.parse_data_packet(packet)
        assert parsed_data is not None
        assert parsed_data["type"] == "patient_xml"
        assert parsed_data["patient_id"] == "patient777"
        
        # Generate alerts
        alerts = self.elderly_plugin.generate_alerts(parsed_data)
        assert len(alerts) > 0
        
        # Check for high-risk patient alert
        risk_alert = next((a for a in alerts if a.type == "HIGH_RISK_PATIENT"), None)
        assert risk_alert is not None
        assert "XML" in risk_alert.context["source_format"]
    
    def test_elderly_plugin_csv_processing(self):
        """Test elderly plugin processing CSV sensor data"""
        # Create CSV sensor data
        csv_data = [
            {"patient_id": "p1", "heart_rate": "125", "spo2": "96", "timestamp": "2025-10-01T09:00:00Z"},
            {"patient_id": "p1", "heart_rate": "128", "spo2": "94", "timestamp": "2025-10-01T09:05:00Z"},
            {"patient_id": "p1", "heart_rate": "131", "spo2": "92", "timestamp": "2025-10-01T09:10:00Z"},
            {"patient_id": "p1", "heart_rate": "135", "spo2": "91", "timestamp": "2025-10-01T09:15:00Z"}
        ]
        
        packet = create_data_packet_generic(
            app_id="elderly_care",
            data_type="sensor_csv",
            source_id="csv_logger",
            data=csv_data,
            data_format=core_pb.DataFormat.CSV
        )
        
        # Process through plugin
        parsed_data = self.elderly_plugin.parse_data_packet(packet)
        assert parsed_data is not None
        assert parsed_data["type"] == "sensor_csv"
        assert parsed_data["count"] == 4
        
        # Generate alerts
        alerts = self.elderly_plugin.generate_alerts(parsed_data)
        
        # Should detect pattern anomaly (multiple high HR readings)
        pattern_alert = next((a for a in alerts if a.type == "PATTERN_ANOMALY_CSV"), None)
        assert pattern_alert is not None
        assert "CSV" in pattern_alert.context["source_format"]


class TestCrossFormatIntegration:
    """Test integration across multiple data formats"""
    
    def setup_method(self):
        """Set up test environment"""
        self.registry = PluginRegistry()
        self.registry.register("elderly_care", ElderlyServicePlugin())
        self.registry.register("agriculture", AgricultureServicePlugin())
    
    def test_multi_format_workflow(self):
        """Test complete workflow with multiple data formats"""
        # Process JSON data
        json_packet = create_data_packet_generic(
            app_id="elderly_care",
            data_type="vitals_json",
            source_id="json_monitor",
            data={"patient_id": "p1", "heart_rate": 140, "spo2": 89},
            data_format=core_pb.DataFormat.JSON
        )
        
        # Process XML data
        xml_packet = create_data_packet_generic(
            app_id="elderly_care",
            data_type="patient_data_xml",
            source_id="xml_system",
            data="""<patient><patient_id>p1</patient_id><medical_history><condition>diabetes</condition></medical_history></patient>""",
            data_format=core_pb.DataFormat.XML
        )
        
        # Process both packets
        json_alerts = self.registry.process_data("elderly_care", json_packet)
        xml_alerts = self.registry.process_data("elderly_care", xml_packet)
        
        # Verify alerts were generated
        assert len(json_alerts) > 0
        assert len(xml_alerts) > 0
        
        # Generate notifications
        all_alerts = json_alerts + xml_alerts
        notifications = self.registry.generate_notifications("elderly_care", all_alerts)
        
        assert len(notifications) > 0
        assert all(n.app_id == "elderly_care" for n in notifications)


if __name__ == "__main__":
    # Run specific tests to validate generic data handling
    print("Testing Generic Data Format Handling...")
    
    # Test basic format handlers
    handler_tests = TestDataFormatHandler()
    handler_tests.test_json_format_handling()
    handler_tests.test_xml_format_handling()
    handler_tests.test_csv_format_handling()
    print("✓ Basic format handlers working")
    
    # Test data packets
    packet_tests = TestGenericDataPackets()
    packet_tests.test_json_data_packet()
    packet_tests.test_xml_data_packet()
    packet_tests.test_text_data_packet()
    print("✓ Generic data packets working")
    
    # Test plugin processing
    plugin_tests = TestMultiFormatPluginProcessing()
    plugin_tests.setup_method()
    plugin_tests.test_elderly_plugin_json_processing()
    plugin_tests.test_elderly_plugin_xml_processing()
    plugin_tests.test_elderly_plugin_csv_processing()
    print("✓ Multi-format plugin processing working")
    
    print("\n🎉 All generic data format tests passed!")
    print("The system can now handle JSON, XML, CSV, YAML, and other data formats!")