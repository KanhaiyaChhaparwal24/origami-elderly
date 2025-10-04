from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import uuid

import generated.origami.core_pb2 as core_pb
import generated.origami.elderly_pb2 as elderly_pb
import generated.origami.agriculture_pb2 as agriculture_pb
from app.registry import get_registry
from app.plugins.elderly_service import ElderlyServicePlugin, create_sensor_data_packet, create_medication_data_packet
from app.plugins.agriculture_service import AgricultureServicePlugin, create_crop_sensor_data_packet
from google.protobuf.timestamp_pb2 import Timestamp


def to_timestamp(dt: datetime) -> Timestamp:
    """Convert Python datetime to Protobuf Timestamp"""
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


def simulate_elderly_data() -> List[core_pb.DataPacket]:
    """Generate sample elderly care data packets"""
    now = datetime.utcnow()
    packets = []
    
    # Normal vital signs sensor reading
    sensor_reading = elderly_pb.SensorReading()
    sensor_reading.device_id = "smartwatch_001"
    sensor_reading.patient_id = "patient123"
    sensor_reading.timestamp.CopyFrom(to_timestamp(now))
    sensor_reading.vitals.heart_rate = 85
    sensor_reading.vitals.spo2 = 98
    sensor_reading.fall_detected = False
    sensor_reading.location = "home"
    
    packets.append(create_sensor_data_packet(sensor_reading))
    
    # Emergency sensor reading - fall detected
    emergency_reading = elderly_pb.SensorReading()
    emergency_reading.device_id = "smartwatch_001"
    emergency_reading.patient_id = "patient123"
    emergency_reading.timestamp.CopyFrom(to_timestamp(now + timedelta(minutes=5)))
    emergency_reading.vitals.heart_rate = 130
    emergency_reading.vitals.spo2 = 88
    emergency_reading.fall_detected = True
    emergency_reading.location = "bathroom"
    
    packets.append(create_sensor_data_packet(emergency_reading))
    
    # Missed medication event
    medication_event = elderly_pb.MedicationEvent()
    medication_event.patient_id = "patient123"
    medication_event.medication_id = "med_001"
    medication_event.medication_name = "Aspirin"
    medication_event.scheduled_time.CopyFrom(to_timestamp(now.replace(hour=8, minute=0)))
    medication_event.taken = False
    medication_event.dosage = "81mg"
    
    packets.append(create_medication_data_packet(medication_event))
    
    return packets


def simulate_agriculture_data() -> List[core_pb.DataPacket]:
    """Generate sample agriculture data packets"""
    now = datetime.utcnow()
    packets = []
    
    # Normal crop sensor reading
    sensor_reading = agriculture_pb.CropSensorReading()
    sensor_reading.sensor_id = "field_sensor_001"
    sensor_reading.field_id = "field_north_40"
    sensor_reading.timestamp.CopyFrom(to_timestamp(now))
    sensor_reading.soil.moisture_level = 45.0
    sensor_reading.soil.ph_level = 6.8
    sensor_reading.soil.temperature = 18.5
    sensor_reading.weather.temperature = 22.0
    sensor_reading.weather.humidity = 65.0
    sensor_reading.crop_type = "corn"
    sensor_reading.growth_stage = "vegetative"
    
    packets.append(create_crop_sensor_data_packet(sensor_reading))
    
    # Drought warning - low moisture
    drought_reading = agriculture_pb.CropSensorReading()
    drought_reading.sensor_id = "field_sensor_002"
    drought_reading.field_id = "field_south_20"
    drought_reading.timestamp.CopyFrom(to_timestamp(now + timedelta(hours=1)))
    drought_reading.soil.moisture_level = 15.0  # Below drought threshold
    drought_reading.soil.ph_level = 7.2
    drought_reading.soil.temperature = 25.0
    drought_reading.weather.temperature = 28.0
    drought_reading.weather.humidity = 35.0
    drought_reading.crop_type = "wheat"
    drought_reading.growth_stage = "flowering"
    
    packets.append(create_crop_sensor_data_packet(drought_reading))
    
    return packets


def simulate_multi_application_scenario() -> Tuple[List[core_pb.DataPacket], List[core_pb.Alert], List[core_pb.Notification]]:
    """Simulate a complete multi-application monitoring scenario"""
    # Initialize plugin registry
    registry = get_registry()
    
    # Register plugins if not already registered
    if not registry.get_plugin("elderly_care"):
        registry.register_plugin(ElderlyServicePlugin())
    if not registry.get_plugin("agriculture"):
        registry.register_plugin(AgricultureServicePlugin())
    
    # Generate data from multiple applications
    all_packets = []
    all_packets.extend(simulate_elderly_data())
    all_packets.extend(simulate_agriculture_data())
    
    # Process all data packets to generate alerts
    all_alerts = []
    for packet in all_packets:
        alerts = registry.generate_alerts(packet)
        all_alerts.extend(alerts)
    
    # Process all alerts to generate notifications
    all_notifications = []
    for alert in all_alerts:
        notifications = registry.process_alert(alert)
        all_notifications.extend(notifications)
    
    return all_packets, all_alerts, all_notifications


def get_application_summary(app_id: str, entity_id: str, alerts: List[core_pb.Alert], 
                          notifications: List[core_pb.Notification]) -> Optional[core_pb.ApplicationSummary]:
    """Generate application-specific summary"""
    registry = get_registry()
    plugin = registry.get_plugin(app_id)
    
    if not plugin:
        print(f"No plugin found for app_id: {app_id}")
        return None
    
    # Filter alerts and notifications for this application
    app_alerts = [alert for alert in alerts if alert.app_id == app_id]
    app_notifications = [notif for notif in notifications if notif.app_id == app_id]
    
    return plugin.generate_summary(entity_id, "daily", app_alerts, app_notifications)


if __name__ == "__main__":
    print("Multi-Application Data Simulation")
    print("=" * 50)
    
    packets, alerts, notifications = simulate_multi_application_scenario()
    
    print(f"Generated {len(packets)} data packets across multiple applications")
    print(f"Generated {len(alerts)} alerts from data analysis")
    print(f"Sent {len(notifications)} notifications to stakeholders")
    
    print("\nBreakdown by Application:")
    print("-" * 30)
    
    # Group by application
    apps = {"elderly_care": [], "agriculture": []}
    for packet in packets:
        if packet.app_id in apps:
            apps[packet.app_id].append(packet)
    
    for app_id, app_packets in apps.items():
        app_alerts = [alert for alert in alerts if alert.app_id == app_id]
        app_notifications = [notif for notif in notifications if notif.app_id == app_id]
        
        print(f"\n{app_id.upper()}:")
        print(f"  Data packets: {len(app_packets)}")
        print(f"  Alerts: {len(app_alerts)}")
        print(f"  Notifications: {len(app_notifications)}")
        
        # Show alert details
        for alert in app_alerts:
            print(f"    - {alert.severity.upper()} {alert.type}: {alert.message}")