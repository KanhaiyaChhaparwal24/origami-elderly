"""
Tests for the family communication functionality in the elderly care system
"""

import pytest
from datetime import datetime, timedelta
from app.ingest import simulate_patient_data, simulate_family_communication_scenario
from app.serializer import deserialize_record, serialize_record
from app.family_service import FamilyService, create_sample_emergency_contacts
from app.adapter import (
    sensor_to_alert, 
    medication_to_alert, 
    family_communication_to_notification,
    check_family_contact_status
)


def test_emergency_contacts_creation():
    """Test creation of emergency contacts"""
    contacts = create_sample_emergency_contacts()
    
    assert len(contacts) == 3
    
    # Check primary contact
    primary_contacts = [c for c in contacts if c.is_primary]
    assert len(primary_contacts) == 1
    assert primary_contacts[0].name == "Rajesh Sharma"
    assert primary_contacts[0].relationship == "FAMILY"
    
    # Check all contacts have required fields
    for contact in contacts:
        assert contact.contact_id
        assert contact.name
        assert contact.relationship
        assert contact.phone
        assert contact.notify_on_alert is True


def test_patient_record_with_emergency_contacts():
    """Test patient record includes emergency contacts"""
    record, blob = simulate_patient_data()
    
    # Verify emergency contacts are included
    assert len(record.emergency_contacts) == 3
    assert record.patient_id == "patient123"
    assert record.name == "Mrs. Sharma"
    
    # Test serialization roundtrip
    deserialized_record = deserialize_record(blob)
    assert len(deserialized_record.emergency_contacts) == len(record.emergency_contacts)
    assert deserialized_record.emergency_contacts[0].name == record.emergency_contacts[0].name


def test_family_service_initialization():
    """Test FamilyService initialization and basic methods"""
    family_service = FamilyService()
    assert family_service.communication_log == []
    
    # Test with sample data
    record, _ = simulate_patient_data()
    
    # Test get emergency contacts
    emergency_contacts = family_service.get_emergency_contacts(record)
    assert len(emergency_contacts) == 3  # All contacts notify on alert
    
    # Test get primary contact
    primary_contact = family_service.get_primary_contact(record)
    assert primary_contact is not None
    assert primary_contact.is_primary is True
    assert primary_contact.name == "Rajesh Sharma"


def test_alert_generation_with_ids():
    """Test that alerts are generated with unique IDs"""
    record, _ = simulate_patient_data()
    
    alerts = []
    for sr in record.sensor_readings:
        alert = sensor_to_alert(sr)
        if alert:
            alerts.append(alert)
    
    for med in record.medication_events:
        alert = medication_to_alert(med)
        if alert:
            alerts.append(alert)
    
    # Should have alerts (fall detection + missed medication)
    assert len(alerts) >= 2
    
    # All alerts should have unique IDs
    alert_ids = [alert.alert_id for alert in alerts]
    assert len(alert_ids) == len(set(alert_ids))  # All unique
    
    # Check alert types
    alert_types = [alert.alert_type for alert in alerts]
    assert "FALL" in alert_types
    assert "MED_MISSED" in alert_types


def test_family_communication_scenario():
    """Test the complete family communication scenario"""
    record, care_summary, family_service = simulate_family_communication_scenario()
    
    # Verify record has been updated with communications
    assert len(record.family_communications) > 0
    assert len(record.emergency_contacts) == 3
    
    # Verify care summary includes family notifications
    assert len(care_summary.alerts) > 0
    assert len(care_summary.family_notifications) > 0
    
    # Verify communication log in family service
    assert len(family_service.communication_log) > 0


def test_family_communication_to_notification():
    """Test conversion of family communication to notification"""
    from app.serializer import build_family_communication
    
    now = datetime.utcnow()
    communication = build_family_communication(
        patient_id="patient123",
        contact_id="contact_001",
        dt=now,
        comm_type="SMS",
        message="Emergency alert sent",
        successful=True,
        alert_id="alert_123"
    )
    
    notification = family_communication_to_notification(communication)
    
    assert notification.patient_id == "patient123"
    assert notification.contact_id == "contact_001"
    assert notification.notification_type == "EMERGENCY_ALERT"
    assert notification.delivery_method == "SMS"
    assert notification.sent_successfully is True


def test_family_contact_failure_detection():
    """Test detection of failed family communications"""
    record, _ = simulate_patient_data()
    
    # Manually add a failed communication
    from app.serializer import build_family_communication
    now = datetime.utcnow()
    failed_comm = build_family_communication(
        patient_id="patient123",
        contact_id="contact_001", 
        dt=now,
        comm_type="SMS",
        message="Failed to send",
        successful=False
    )
    
    # Update record with failed communication
    record.family_communications.append(failed_comm)
    
    # Check for communication failure alerts
    failure_alerts = check_family_contact_status(record)
    
    assert len(failure_alerts) == 1
    assert failure_alerts[0].alert_type == "FAMILY_CONTACT_FAILED"
    assert "Failed to contact family" in failure_alerts[0].message


def test_emergency_alert_prioritization():
    """Test that high-priority alerts trigger appropriate family notifications"""
    family_service = FamilyService()
    record, _ = simulate_patient_data()
    
    # Create a high-priority fall alert
    from app.serializer import build_sensor_reading
    now = datetime.utcnow()
    fall_sensor = build_sensor_reading(
        "deviceA", "patient123", now,
        {"heart_rate": 85, "spo2": 98}, 
        fall_detected=True
    )
    
    fall_alert = sensor_to_alert(fall_sensor)
    assert fall_alert.alert_type == "FALL"
    
    # Process alerts for family notification
    communications = family_service.process_alerts_for_family_notification(record, [fall_alert])
    
    # Should have sent notifications
    assert len(communications) > 0
    
    # Primary contact should be notified
    primary_contact = family_service.get_primary_contact(record)
    primary_communications = [c for c in communications if c.contact_id == primary_contact.contact_id]
    assert len(primary_communications) > 0


def test_care_summary_with_family_notifications():
    """Test care summary includes family notifications"""
    from app.adapter import build_care_summary
    from app.serializer import build_family_communication
    
    # Create sample alerts and notifications
    record, _ = simulate_patient_data()
    
    alerts = []
    for sr in record.sensor_readings:
        alert = sensor_to_alert(sr)
        if alert:
            alerts.append(alert)
    
    # Create family notifications
    now = datetime.utcnow()
    comm = build_family_communication(
        patient_id="patient123",
        contact_id="contact_001",
        dt=now,
        comm_type="SMS", 
        message="Test notification",
        successful=True
    )
    
    notification = family_communication_to_notification(comm)
    
    care_summary = build_care_summary("patient123", alerts, [notification])
    
    assert len(care_summary.alerts) > 0
    assert len(care_summary.family_notifications) == 1
    assert "family notifications sent" in care_summary.summary_text.lower()


def test_serialization_roundtrip_with_family_data():
    """Test complete serialization roundtrip with family communication data"""
    record, care_summary, family_service = simulate_family_communication_scenario()
    
    # Serialize the complete record
    blob = serialize_record(record)
    
    # Deserialize and verify
    deserialized_record = deserialize_record(blob)
    
    # Verify all data is preserved
    assert deserialized_record.patient_id == record.patient_id
    assert len(deserialized_record.emergency_contacts) == len(record.emergency_contacts)
    assert len(deserialized_record.family_communications) == len(record.family_communications)
    assert len(deserialized_record.sensor_readings) == len(record.sensor_readings)
    assert len(deserialized_record.medication_events) == len(record.medication_events)
    
    # Verify emergency contact details
    original_primary = next(c for c in record.emergency_contacts if c.is_primary)
    deserialized_primary = next(c for c in deserialized_record.emergency_contacts if c.is_primary)
    assert original_primary.name == deserialized_primary.name
    assert original_primary.phone == deserialized_primary.phone


if __name__ == "__main__":
    # Run some basic tests
    print("Running Family Communication Tests...")
    
    test_emergency_contacts_creation()
    print("✅ Emergency contacts creation test passed")
    
    test_patient_record_with_emergency_contacts()
    print("✅ Patient record with emergency contacts test passed")
    
    test_family_service_initialization()
    print("✅ Family service initialization test passed")
    
    test_alert_generation_with_ids()
    print("✅ Alert generation with IDs test passed")
    
    test_family_communication_scenario()
    print("✅ Family communication scenario test passed")
    
    print("\n🎉 All basic tests passed! Run 'python -m pytest tests/' for full test suite.")