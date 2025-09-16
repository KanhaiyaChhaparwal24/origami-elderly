# Origami Elderly Care Framework

A comprehensive Python skeleton framework for elderly healthcare monitoring with protobuf-based data serialization and family communication capabilities.

## Overview

This framework provides a complete solution for monitoring elderly patients' health and wellbeing, including sensor data monitoring, medication management, emergency contact systems, care summarization, and data persistence using efficient protobuf-based storage.

## Use Cases Supported

### 1. **Fall Detection & Emergency Response**
Real-time fall detection from wearable sensors with immediate alerts to emergency contacts and automated emergency service notifications for severe incidents.

### 2. **Vital Signs Monitoring**
Continuous monitoring of heart rate, SpO2, blood pressure, and temperature with anomaly detection, configurable thresholds, and trend analysis.

### 3. **Medication Adherence Tracking**
Scheduled medication reminders, missed dose detection and alerts, and family notifications for medication non-compliance.

### 4. **Family Communication & Notifications**
Emergency contact management with relationship tracking, multi-channel communication (SMS, Email, Voice calls), automated family updates, wellness check scheduling, and failed communication detection with backup contact activation.

### 5. **Daily Wellness Reporting**
Comprehensive care summaries, alert aggregation and prioritization, and family-friendly status updates.

## Key Features

### Family Communication Features
- **Emergency Contact Management**: Store and manage family members, caregivers, and healthcare providers
- **Multi-Channel Notifications**: Support for SMS, email, and voice call notifications
- **Alert-Triggered Communications**: Automatic family notifications based on alert severity
- **Communication Tracking**: Log all family interactions with success/failure status
- **Backup Contact System**: Escalation to secondary contacts for failed communications
- **Daily Updates**: Scheduled wellness reports to family members

### Data Models (Protobuf)

#### Core Entities
- `ElderlyRecord`: Complete patient profile with medical and contact information
- `SensorReading`: Real-time health monitoring data
- `MedicationEvent`: Medication schedules and adherence tracking
- `EmergencyContact`: Family and caregiver contact information
- `FamilyCommunication`: Communication logs and tracking

#### Application Layer
- `Alert`: Healthcare alerts with severity scoring
- `FamilyNotification`: Family communication notifications
- `CareSummary`: Comprehensive care reports

## Data Flow

1. **Data Ingestion**: Sensor readings and medication events are captured
2. **Alert Generation**: Raw data is analyzed for anomalies and alerts are created
3. **Family Notification**: High-priority alerts trigger automatic family communications
4. **Data Persistence**: All data is serialized to protobuf format and stored
5. **Care Summarization**: Comprehensive reports are generated for healthcare providers

## Testing

The framework includes comprehensive tests covering data serialization/deserialization roundtrips, alert generation and scoring, family communication scenarios, emergency contact management, and care summary generation.

## Dependencies

- `protobuf>=4.21.0`: Protocol buffer serialization
- `pytest>=7.0`: Testing framework
- `boto3>=1.26.0`: Optional AWS integration

---
