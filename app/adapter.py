import generated.origami.elderly_app_pb2 as app_pb
import uuid
from datetime import datetime

def sensor_to_alert(sensor, score=1.0):
    alert_id = str(uuid.uuid4())
    if sensor.fall_detected:
        alert = app_pb.Alert()
        alert.patient_id = sensor.patient_id
        alert.timestamp.CopyFrom(sensor.timestamp)
        alert.alert_type = "FALL"
        alert.message = "Fall detected!"
        alert.score = score
        alert.alert_id = alert_id
        return alert
    if sensor.vitals.heart_rate > 120 or sensor.vitals.spo2 < 90:
        alert = app_pb.Alert()
        alert.patient_id = sensor.patient_id
        alert.timestamp.CopyFrom(sensor.timestamp)
        alert.alert_type = "VITALS_ANOMALY"
        alert.message = f"Abnormal vitals HR={sensor.vitals.heart_rate}, SpO2={sensor.vitals.spo2}"
        alert.score = score
        alert.alert_id = alert_id
        return alert
    return None
 
def medication_to_alert(med_event):
    if not med_event.taken:
        alert = app_pb.Alert()
        alert.patient_id = med_event.patient_id
        alert.timestamp.CopyFrom(med_event.scheduled_time)
        alert.alert_type = "MED_MISSED"
        alert.message = f"Missed medication: {med_event.medication_name}"
        alert.score = 1.0
        alert.alert_id = str(uuid.uuid4())
        return alert
    return None

def family_communication_to_notification(comm):
    """Convert family communication to notification for care summary"""
    notification = app_pb.FamilyNotification()
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
    """Generate alerts if family communication has failed"""
    alerts = []
    failed_communications = [comm for comm in elderly_record.family_communications if not comm.successful]
    
    for failed_comm in failed_communications:
        alert = app_pb.Alert()
        alert.patient_id = failed_comm.patient_id
        alert.timestamp.CopyFrom(failed_comm.timestamp)
        alert.alert_type = "FAMILY_CONTACT_FAILED"
        alert.message = f"Failed to contact family via {failed_comm.communication_type}"
        alert.score = 0.8
        alert.alert_id = str(uuid.uuid4())
        alerts.append(alert)
    
    return alerts

def should_notify_emergency_contacts(alert):
    """Determine if emergency contacts should be notified for this alert"""
    high_priority_alerts = ["FALL", "VITALS_ANOMALY"]
    return alert.alert_type in high_priority_alerts and alert.score >= 0.7

def build_care_summary(patient_id, alerts, family_notifications=None):
    cs = app_pb.CareSummary()
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
