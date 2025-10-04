# ORIGAMI-GENERIC-BACKEND

A comprehensive, application-agnostic Python framework supporting multiple domains through a plugin-based architecture with universal data format support (JSON, XML, CSV, YAML, Protocol Buffers, and more).

## Overview

This framework provides a generic backend that supports multiple applications and domains through a plugin system. Originally built for elderly healthcare monitoring, it has been refactored into a universal platform supporting:

- **Elderly Care**: Health monitoring, family communications, and emergency response
- **Agriculture**: Crop monitoring, farming activities, and agricultural alerts  
- **Security**: Surveillance, access control, and security incident management
- **Extensible**: Easy to add new domains via the plugin architecture

## Architecture

### Core Components
- **Plugin Registry**: Manages application-specific plugins
- **Generic Data Processing**: Application-agnostic data ingestion and processing
- **Multi-Domain Alerts**: Unified alert system across all applications
- **Cross-Application Analytics**: System-wide monitoring and statistics

### Application Plugins
- **Elderly Care Plugin**: Family communication, health monitoring, emergency alerts
- **Agriculture Plugin**: Crop monitoring, weather alerts, farm management
- **Security Plugin**: (Framework ready for implementation)

## Supported Applications

### 1. **Elderly Care** (`app_id: elderly_care`)
- Fall detection and emergency response
- Vital signs monitoring with anomaly detection
- Medication adherence tracking
- Family communication and notifications
- Daily wellness reporting

### 2. **Agriculture** (`app_id: agriculture`)
- Crop sensor monitoring (soil, weather conditions)
- Drought and frost warnings
- Nutrient deficiency detection
- Farm team notifications
- Agricultural reporting

### 3. **Security** (`app_id: security`)
- Framework ready for security monitoring
- Intrusion detection capabilities
- Access control event tracking
- Security team notifications

## Key Features

### Universal Data Format Support
- **JSON**: Native support for JSON data input and processing
- **XML**: Full XML parsing and data extraction capabilities  
- **CSV**: Batch processing of CSV data files
- **YAML**: Configuration and structured data in YAML format
- **Protocol Buffers**: High-performance binary serialization (legacy support)
- **Plain Text**: Unstructured text data processing
- **Binary**: Raw binary data handling for specialized applications

### Multi-Application Support
- **Plugin Architecture**: Each domain is implemented as a plugin
- **Generic Data Models**: Core protobuf schemas work across all applications
- **Unified Processing**: Single framework handles multiple domains simultaneously
- **Cross-Application Analytics**: System-wide monitoring and reporting

### Data Models (Protobuf)

#### Core Generic Models (`core.proto`)
- `Application`: Application metadata and capabilities
- `DataPacket`: Generic container for all application data
- `Alert`: Universal alert system with severity levels
- `Notification`: Multi-channel notification system
- `Contact`: Universal contact management
- `ApplicationSummary`: Cross-application reporting

#### Application-Specific Models
- `elderly.proto`: Healthcare-specific data structures
- `agriculture.proto`: Farming and crop monitoring structures
- `security.proto`: Security and surveillance data models

## Usage Examples

### Multi-Application Demo
```python
from app.main import demo_multi_application

# Run demonstration across all applications
demo_multi_application()
```

### Application-Specific Processing
```python
from app.registry import get_registry
from app.plugins.elderly_service import ElderlyServicePlugin

# Register plugins
registry = get_registry()
registry.register_plugin(ElderlyServicePlugin())

# Process data for specific application
alerts = registry.generate_alerts(data_packet)
notifications = registry.process_alert(alert)
```

### CLI Usage
```bash
# List all registered applications
python cli.py apps

# Run demo for specific application
python cli.py demo --app-id elderly_care
python cli.py demo --app-id agriculture

# Show application contacts
python cli.py contacts --app-id elderly_care --entity-id patient123

# System overview
python cli.py overview

# Application statistics
python cli.py stats --app-id agriculture
```

## Data Format Examples

### JSON Data Input
```json
{
  "patient_id": "patient123",
  "heart_rate": 95,
  "blood_pressure": {"systolic": 120, "diastolic": 80},
  "timestamp": "2025-10-01T10:30:00Z",
  "device_info": {"id": "monitor_001", "location": "bedroom"}
}
```

### XML Data Input
```xml
<?xml version="1.0"?>
<patient_record>
  <patient_id>patient456</patient_id>
  <medical_history>
    <condition>diabetes</condition>
    <condition>hypertension</condition>
  </medical_history>
  <current_vitals>
    <heart_rate>88</heart_rate>
    <temperature>98.6</temperature>
  </current_vitals>
</patient_record>
```

### CSV Data Input
```csv
patient_id,heart_rate,spo2,timestamp
p001,85,98,2025-10-01T09:00:00Z
p001,87,97,2025-10-01T09:05:00Z
p001,89,96,2025-10-01T09:10:00Z
```

### Python API Usage with Multiple Formats
```python
from app.serializer import create_data_packet_generic, DataFormatHandler
import generated.core_pb2 as core_pb

# Create JSON data packet
json_packet = create_data_packet_generic(
    app_id="elderly_care",
    data_type="vitals_json", 
    source_id="json_monitor",
    data={"patient_id": "p123", "heart_rate": 95},
    data_format=core_pb.DataFormat.JSON
)

# Create XML data packet  
xml_packet = create_data_packet_generic(
    app_id="elderly_care",
    data_type="patient_xml",
    source_id="xml_system", 
    data="<patient><id>p456</id><vitals><hr>88</hr></vitals></patient>",
    data_format=core_pb.DataFormat.XML
)

# Process through plugin system
alerts = registry.process_data("elderly_care", json_packet)
```

## Data Flow

1. **Multi-Source Ingestion**: Data from various applications (sensors, events, user actions)
2. **Plugin Routing**: DataPackets routed to appropriate application plugins
3. **Alert Generation**: Application-specific logic generates alerts
4. **Cross-Application Processing**: Unified notification and communication system
5. **Persistence**: All data stored in application-agnostic format
6. **Analytics**: System-wide and application-specific reporting

## Plugin Development

### Creating a New Application Plugin

```python
from app.registry import PluginInterface
import generated.origami.core_pb2 as core_pb

class MyApplicationPlugin(PluginInterface):
    @property
    def app_id(self) -> str:
        return "my_application"
    
    @property
    def app_name(self) -> str:
        return "My Application Name"
    
    @property 
    def supported_data_types(self) -> List[str]:
        return ["my_data_type"]
    
    def parse_data_packet(self, data_packet: core_pb.DataPacket):
        # Parse application-specific data
        pass
    
    def generate_alerts(self, parsed_data, app_config=None):
        # Generate application-specific alerts
        pass
    
    # ... implement other required methods
```

### Registering Plugins
```python
from app.registry import get_registry

registry = get_registry()
registry.register_plugin(MyApplicationPlugin())
```

## Testing

The framework includes comprehensive tests covering:
- Multi-application data processing
- Plugin system functionality  
- Cross-application alert generation
- Backward compatibility with original elderly care system

```bash
# Run all tests
python -m pytest

# Test specific application
python -m pytest tests/test_elderly_care.py

# Test plugin system
python -m pytest tests/test_plugin_registry.py
```

## Backward Compatibility

All original elderly care functionality is preserved:
- Legacy function calls continue to work
- Original data formats supported
- Existing CLI commands maintained
- Gradual migration path available

## Extension Points

1. **New Applications**: Add support for IoT, smart home, industrial monitoring
2. **Advanced Analytics**: Machine learning across applications
3. **Real-time Processing**: Stream processing for high-frequency data
4. **Cloud Integration**: Multi-tenant cloud deployment
5. **API Gateway**: RESTful API for external integrations

## Dependencies

- `protobuf>=4.21.0`: Protocol buffer serialization
- `pytest>=7.0`: Testing framework  
- `boto3>=1.26.0`: Optional cloud integration

---
