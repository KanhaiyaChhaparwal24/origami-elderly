"""
Generic Adapter for Origami Framework
Routes data processing through plugin system for application-agnostic handling
"""

from typing import List, Optional, Any
from datetime import datetime
import uuid

import generated.origami.core_pb2 as core_pb
import generated.origami.elderly_app_pb2 as elderly_app_pb  # Legacy support
from app.registry import get_registry
from google.protobuf.timestamp_pb2 import Timestamp


def to_timestamp(dt: datetime) -> Timestamp:
    """Convert Python datetime to Protobuf Timestamp"""
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


def process_data_packet(data_packet: core_pb.DataPacket, app_config: Optional[core_pb.ApplicationConfig] = None) -> List[core_pb.Alert]:
    """Process a data packet using the appropriate plugin to generate alerts"""
    registry = get_registry()
    return registry.generate_alerts(data_packet, app_config)


def process_alert(alert: core_pb.Alert) -> List[core_pb.Notification]:
    """Process an alert using the appropriate plugin to generate notifications"""
    registry = get_registry()
    return registry.process_alert(alert)


def generate_application_summary(app_id: str, entity_id: str, period: str, 
                                alerts: List[core_pb.Alert], notifications: List[core_pb.Notification]) -> Optional[core_pb.ApplicationSummary]:
    """Generate an application summary using the appropriate plugin"""
    registry = get_registry()
    plugin = registry.get_plugin(app_id)
    
    if not plugin:
        print(f"No plugin found for app_id: {app_id}")
        return None
    
    # Filter alerts and notifications for this application and entity
    entity_alerts = [alert for alert in alerts if alert.app_id == app_id and entity_id in alert.affected_entities]
    entity_notifications = [notif for notif in notifications if notif.app_id == app_id]
    
    return plugin.generate_summary(entity_id, period, entity_alerts, entity_notifications)


def check_alert_severity(alerts: List[core_pb.Alert]) -> dict:
    """Analyze alert severity distribution"""
    severity_counts = {"info": 0, "warning": 0, "critical": 0, "emergency": 0}
    
    for alert in alerts:
        severity = alert.severity.lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    return severity_counts


def get_application_statistics(app_id: str, alerts: List[core_pb.Alert], notifications: List[core_pb.Notification]) -> dict:
    """Get statistics for a specific application"""
    app_alerts = [alert for alert in alerts if alert.app_id == app_id]
    app_notifications = [notif for notif in notifications if notif.app_id == app_id]
    
    stats = {
        "app_id": app_id,
        "total_alerts": len(app_alerts),
        "total_notifications": len(app_notifications),
        "successful_notifications": len([n for n in app_notifications if n.sent_successfully]),
        "severity_distribution": check_alert_severity(app_alerts),
        "alert_types": {},
        "notification_channels": {}
    }
    
    # Count alert types
    for alert in app_alerts:
        alert_type = alert.type
        stats["alert_types"][alert_type] = stats["alert_types"].get(alert_type, 0) + 1
    
    # Count notification channels
    for notification in app_notifications:
        channel = notification.channel
        stats["notification_channels"][channel] = stats["notification_channels"].get(channel, 0) + 1
    
    return stats


def get_system_overview(alerts: List[core_pb.Alert], notifications: List[core_pb.Notification]) -> dict:
    """Get system-wide overview across all applications"""
    overview = {
        "total_alerts": len(alerts),
        "total_notifications": len(notifications),
        "applications": {},
        "overall_severity": check_alert_severity(alerts)
    }
    
    # Group by application
    app_ids = set(alert.app_id for alert in alerts)
    
    for app_id in app_ids:
        overview["applications"][app_id] = get_application_statistics(app_id, alerts, notifications)
    
    return overview


# Legacy support functions for backward compatibility
def sensor_to_alert(sensor, score=1.0):
    """Legacy function - convert sensor reading to alert (elderly care specific)"""
    from app.plugins.elderly_service import ElderlyServicePlugin
    
    plugin = ElderlyServicePlugin()
    alerts = plugin.generate_alerts(sensor)
    
    if alerts:
        alert = alerts[0]  # Return first alert for compatibility
        # Convert to legacy format
        legacy_alert = elderly_app_pb.Alert()
        legacy_alert.patient_id = alert.affected_entities[0] if alert.affected_entities else ""
        legacy_alert.timestamp.CopyFrom(alert.timestamp)
        legacy_alert.alert_type = alert.type
        legacy_alert.message = alert.message
        legacy_alert.score = alert.score
        legacy_alert.alert_id = alert.alert_id
        return legacy_alert
    
    return None


def medication_to_alert(med_event):
    """Legacy function - convert medication event to alert (elderly care specific)"""
    from app.plugins.elderly_service import ElderlyServicePlugin
    
    plugin = ElderlyServicePlugin()
    alerts = plugin.generate_alerts(med_event)
    
    if alerts:
        alert = alerts[0]  # Return first alert for compatibility
        # Convert to legacy format
        legacy_alert = elderly_app_pb.Alert()
        legacy_alert.patient_id = alert.affected_entities[0] if alert.affected_entities else ""
        legacy_alert.timestamp.CopyFrom(alert.timestamp)
        legacy_alert.alert_type = alert.type
        legacy_alert.message = alert.message
        legacy_alert.score = alert.score
        legacy_alert.alert_id = alert.alert_id
        return legacy_alert
    
    return None


def family_communication_to_notification(comm):
    """Legacy function - convert family communication to notification"""
    notification = elderly_app_pb.FamilyNotification()
    notification.patient_id = comm.patient_id
    notification.contact_id = comm.contact_id
    notification.timestamp.CopyFrom(comm.timestamp)
    
    # Map communication type to notification type
    if comm.communication_type in ["CALL", "SMS"]:
        notification.notification_type = "EMERGENCY_ALERT" if comm.alert_id else "WELLNESS_CHECK"
        notification.delivery_method = comm.communication_type
    else:
        notification.notification_type = "DAILY_UPDATE"
        notification.delivery_method = comm.communication_type
    
    notification.message = comm.message
    notification.sent_successfully = comm.successful
    return notification


def check_family_contact_status(elderly_record):
    """Legacy function - generate alerts if family communication has failed"""
    alerts = []
    failed_communications = [comm for comm in elderly_record.family_communications if not comm.successful]
    
    for failed_comm in failed_communications:
        alert = elderly_app_pb.Alert()
        alert.patient_id = failed_comm.patient_id
        alert.timestamp.CopyFrom(failed_comm.timestamp)
        alert.alert_type = "FAMILY_CONTACT_FAILED"
        alert.message = f"Failed to contact family via {failed_comm.communication_type}"
        alert.score = 0.8
        alert.alert_id = str(uuid.uuid4())
        alerts.append(alert)
    
    return alerts


def should_notify_emergency_contacts(alert):
    """Legacy function - determine if emergency contacts should be notified"""
    high_priority_alerts = ["FALL", "VITALS_ANOMALY"]
    return alert.alert_type in high_priority_alerts and alert.score >= 0.7


def build_care_summary(patient_id, alerts, family_notifications=None):
    """Legacy function - build care summary (elderly care specific)"""
    cs = elderly_app_pb.CareSummary()
    cs.patient_id = patient_id
    cs.alerts.extend([a for a in alerts if a])
    
    # Include family notifications if provided
    if family_notifications:
        cs.family_notifications.extend(family_notifications)
    
    # Generate summary text based on alerts and notifications
    alert_count = len([a for a in alerts if a])
    notification_count = len(family_notifications) if family_notifications else 0
    
    cs.summary_text = f"Care Summary: {alert_count} alerts generated, {notification_count} family notifications sent"
    return cs
