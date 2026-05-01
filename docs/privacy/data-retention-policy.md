# Children's Thinking Tree System: Data Retention and Deletion Policy

**Document ID**: CTS-DRP-001
**Version**: 1.0
**Effective Date**: 2026-04-30
**Next Review Date**: 2027-04-30

---

## 1. Purpose

This policy establishes specific retention periods, automated deletion mechanisms, and audit procedures for all data collected by the Children's Thinking Tree System. This policy ensures compliance with:

- **COPPA**: "Personal information collected online from children may be retained only as long as is reasonably necessary to fulfill the purpose for which the information was collected" (16 CFR § 312.10)
- **GDPR-K**: Storage limitation principle (Article 5(1)(e))
- **PIPL**: Data retention limitations (Article 19)

---

## 2. Data Classification and Retention Periods

### 2.1 Data Retention Schedule

| Data Category | Classification | Retention Period | Trigger | Legal Basis |
|---------------|----------------|------------------|---------|-------------|
| Raw Audio Recordings | Sensitive PI | 24 hours maximum | After AI processing completes | COPPA §312.10, PIPL Art. 19 |
| Audio Processing Cache | Sensitive PI | 1 hour maximum | After processing completes | Data minimization |
| Speech Transcripts | Personal Information | 90 days | From activity date | Educational purpose |
| AI-Generated Summaries | Personal Information | 1 academic year | From activity date | Educational purpose |
| Activity Tree Data | Personal Information | 1 academic year | From activity date | Educational purpose |
| Teacher Review Records | Business Data | 2 academic years | From review date | Audit requirement |
| Consent Records | Compliance Data | 3 years | From consent revocation/expiration | Regulatory requirement |
| Audit Logs | Compliance Data | 3 years | From log creation | Regulatory requirement |
| Breach Records | Compliance Data | 5 years | From breach closure | Regulatory requirement |
| System Logs | Operational Data | 90 days | From log creation | Operations |
| User Account Data | Personal Information | Account active + 30 days | Account closure | Service provision |
| Backup Data | Varies | Same as source + 30 days | Source deletion | Recovery purpose |

### 2.2 Retention Period Justification

**Raw Audio Recordings (24 hours)**:
- Audio is collected solely for AI processing
- No educational value in retaining raw audio
- Minimizes risk of unauthorized access to children's voices
- Complies with data minimization principle

**Speech Transcripts (90 days)**:
- Needed for teacher review and activity continuity
- 90 days covers typical activity completion cycle
- Can be extended with parental consent for specific purposes

**Activity Tree Data (1 academic year)**:
- Educational value for progress tracking
- Aligns with academic calendar
- Enables year-end reporting and parent conferences

**Consent Records (3 years)**:
- Regulatory requirement for demonstrating compliance
- Covers typical statute of limitations
- Enables audit and investigation support

### 2.3 No Indefinite Retention

**This system does not retain any data indefinitely.** All data categories have specific, documented retention periods with automated deletion triggers.

```
STATEMENT OF COMPLIANCE:
The Children's Thinking Tree System does not practice indefinite retention
of any personal information. All data categories have defined retention
periods as documented in Section 2.1, with automated deletion mechanisms
as described in Section 3.
```

---

## 3. Automated Deletion Mechanisms

### 3.1 Deletion Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA DELETION ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Data         │     │ Retention    │     │ Deletion     │
│ Created      │────▶│ Timer        │────▶│ Trigger      │
│              │     │ Starts       │     │ Activated    │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Deletion     │     │ Data         │     │ Deletion     │
│ Confirmation │◀────│ Removed      │◀────│ Process      │
│ Logged       │     │ from System  │     │ Executed     │
└──────────────┘     └──────────────┘     └──────────────┘
        │
        ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Backup       │     │ Audit        │     │ Compliance   │
│ Deletion     │────▶│ Log          │────▶│ Report       │
│ Scheduled    │     │ Updated      │     │ Generated    │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 3.2 Deletion Triggers

**Trigger 1: Time-Based Automatic Deletion**

```python
# Automated Deletion Job (runs every hour)

class AutomatedDeletionJob:
    """
    Scheduled job that deletes data exceeding retention periods.
    Runs every hour to ensure timely deletion.
    """
    
    def run(self):
        # 1. Delete expired audio recordings (24-hour retention)
        self.delete_expired_audio()
        
        # 2. Delete expired transcripts (90-day retention)
        self.delete_expired_transcripts()
        
        # 3. Delete expired activity data (1-year retention)
        self.delete_expired_activities()
        
        # 4. Schedule backup deletion (30 days after primary)
        self.schedule_backup_deletion()
    
    def delete_expired_audio(self):
        """
        Delete audio recordings older than 24 hours.
        CRITICAL: This is the most time-sensitive deletion.
        """
        expiration_time = datetime.utcnow() - timedelta(hours=24)
        
        expired_records = AudioRecord.query.filter(
            AudioRecord.created_at < expiration_time,
            AudioRecord.deletion_status != 'deleted'
        ).all()
        
        for record in expired_records:
            # Verify no active processing
            if not self.is_actively_processing(record.id):
                # Securely delete audio file
                self.secure_delete_file(record.audio_url)
                
                # Update record status
                record.deletion_status = 'deleted'
                record.deleted_at = datetime.utcnow()
                
                # Log deletion
                self.log_deletion(
                    record_id=record.id,
                    data_type='audio_recording',
                    deletion_method='automated_time_based',
                    retention_period='24_hours'
                )
        
        db.session.commit()
```

**Trigger 2: Consent Revocation Deletion**

```python
def process_consent_revocation(self, consent_id: str):
    """
    Delete all data associated with a revoked consent.
    Must complete within 30 days of revocation.
    """
    consent = Consent.query.get(consent_id)
    child_id = consent.child_id
    
    # Identify all data for this child
    data_inventory = self.inventory_child_data(child_id)
    
    # Delete each data category
    for data_type, records in data_inventory.items():
        for record in records:
            # Check if retention required for legal/compliance
            if not self.requires_retention(record):
                self.delete_record(record, reason='consent_revocation')
            else:
                # Mark for deletion when retention period expires
                record.pending_deletion = True
                record.deletion_reason = 'consent_revocation'
                record.deletion_deadline = self.calculate_retention_end(record)
    
    # Log revocation processing
    self.log_revocation_processing(
        consent_id=consent_id,
        child_id=child_id,
        data_deleted=len(data_inventory),
        processing_date=datetime.utcnow()
    )
```

**Trigger 3: Account Closure Deletion**

```python
def process_account_closure(self, account_id: str):
    """
    Delete personal data when account is closed.
    Retains compliance data as required.
    """
    # Stop all data collection
    self.disable_data_collection(account_id)
    
    # Delete personal data (not compliance data)
    personal_data = self.get_personal_data(account_id)
    for data in personal_data:
        if not self.is_compliance_data(data):
            self.delete_record(data, reason='account_closure')
    
    # Schedule compliance data deletion per retention schedule
    compliance_data = self.get_compliance_data(account_id)
    for data in compliance_data:
        data.scheduled_deletion = self.calculate_retention_end(data)
```

### 3.3 Deletion Verification

```python
class DeletionVerifier:
    """
    Verifies that data has been completely and securely deleted.
    """
    
    def verify_deletion(self, record_id: str, data_type: str) -> bool:
        """
        Verify that a record has been completely deleted.
        
        Returns True only if ALL of the following are confirmed:
        1. Primary storage deleted
        2. Backup storage scheduled for deletion
        3. Cache cleared
        4. Index entries removed
        5. Audit log entry created
        """
        checks = [
            self.check_primary_storage(record_id, data_type),
            self.check_backup_schedule(record_id, data_type),
            self.check_cache_cleared(record_id, data_type),
            self.check_index_removed(record_id, data_type),
            self.check_audit_logged(record_id, data_type)
        ]
        
        return all(checks)
    
    def check_primary_storage(self, record_id: str, data_type: str) -> bool:
        """Verify primary storage deletion."""
        if data_type == 'audio_recording':
            # Check file system
            record = AudioRecord.query.get(record_id)
            if record and record.deletion_status == 'deleted':
                # Verify file doesn't exist
                if not os.path.exists(record.audio_url):
                    return True
        return False
    
    def check_backup_schedule(self, record_id: str, data_type: str) -> bool:
        """Verify backup deletion is scheduled."""
        backup_record = BackupDeletionSchedule.query.filter_by(
            source_record_id=record_id
        ).first()
        return backup_record is not None
```

---

## 4. Proof of No Indefinite Retention

### 4.1 Automated Compliance Monitoring

```python
class RetentionComplianceMonitor:
    """
    Continuously monitors for any data that might be retained indefinitely.
    Runs every 15 minutes.
    """
    
    ALERT_THRESHOLDS = {
        'audio_recording': timedelta(hours=24),
        'transcript': timedelta(days=90),
        'activity_data': timedelta(days=365),
        'consent_record': timedelta(days=1095),  # 3 years
        'audit_log': timedelta(days=1095),  # 3 years
    }
    
    def monitor(self):
        """
        Check all data categories for retention compliance.
        Alert if any data exceeds retention period.
        """
        alerts = []
        
        for data_type, threshold in self.ALERT_THRESHOLDS.items():
            # Find records exceeding retention
            expired = self.find_expired_records(data_type, threshold)
            
            if expired:
                # CRITICAL ALERT: Data retained beyond policy
                alert = self.create_critical_alert(
                    data_type=data_type,
                    count=len(expired),
                    oldest_record=min(r.created_at for r in expired),
                    threshold=threshold
                )
                alerts.append(alert)
                
                # Attempt immediate remediation
                self.attempt_remediation(expired)
        
        if alerts:
            self.notify_compliance_team(alerts)
            self.log_compliance_violation(alerts)
        
        return alerts
    
    def find_expired_records(self, data_type: str, threshold: timedelta):
        """Find all records of this type that exceed retention period."""
        cutoff = datetime.utcnow() - threshold
        
        if data_type == 'audio_recording':
            return AudioRecord.query.filter(
                AudioRecord.created_at < cutoff,
                AudioRecord.deletion_status != 'deleted'
            ).all()
        # ... other data types
```

### 4.2 Daily Compliance Report

```python
def generate_daily_compliance_report() -> dict:
    """
    Generate daily report proving no indefinite retention.
    Report is automatically generated and archived.
    """
    report = {
        'report_date': datetime.utcnow().isoformat(),
        'report_type': 'retention_compliance',
        
        'audio_recordings': {
            'total_records': AudioRecord.query.count(),
            'oldest_record_age_hours': self.get_oldest_record_age('audio'),
            'records_within_policy': self.count_within_policy('audio'),
            'records_exceeding_policy': self.count_exceeding_policy('audio'),
            'deletions_today': self.count_deletions_today('audio'),
            'compliance_status': 'COMPLIANT' if self.count_exceeding_policy('audio') == 0 else 'NON_COMPLIANT'
        },
        
        'transcripts': {
            'total_records': Transcript.query.count(),
            'oldest_record_age_days': self.get_oldest_record_age('transcript'),
            'records_within_policy': self.count_within_policy('transcript'),
            'records_exceeding_policy': self.count_exceeding_policy('transcript'),
            'deletions_today': self.count_deletions_today('transcript'),
            'compliance_status': 'COMPLIANT' if self.count_exceeding_policy('transcript') == 0 else 'NON_COMPLIANT'
        },
        
        # ... other data types
        
        'overall_status': self.calculate_overall_status(),
        'next_scheduled_deletions': self.get_upcoming_deletions(),
        'pending_revocations': self.get_pending_revocations()
    }
    
    # Archive report
    self.archive_report(report)
    
    # Alert if non-compliant
    if report['overall_status'] != 'COMPLIANT':
        self.send_compliance_alert(report)
    
    return report
```

### 4.3 Compliance Verification Queries

```sql
-- Query 1: Verify no audio exists beyond 24-hour retention
-- Expected result: 0 records
SELECT COUNT(*) as violating_records
FROM audio_records
WHERE created_at < NOW() - INTERVAL '24 hours'
  AND deletion_status != 'deleted';

-- Query 2: Verify no transcripts exist beyond 90-day retention
-- Expected result: 0 records
SELECT COUNT(*) as violating_records
FROM transcripts
WHERE created_at < NOW() - INTERVAL '90 days'
  AND deletion_status != 'deleted';

-- Query 3: Verify no activity data exists beyond 1-year retention
-- Expected result: 0 records
SELECT COUNT(*) as violating_records
FROM activity_data
WHERE created_at < NOW() - INTERVAL '1 year'
  AND deletion_status != 'deleted';

-- Query 4: List all pending deletions with deadlines
SELECT 
    data_type,
    record_id,
    created_at,
    scheduled_deletion_date,
    deletion_status
FROM deletion_schedule
WHERE deletion_status = 'pending'
ORDER BY scheduled_deletion_date ASC;
```

---

## 5. Deletion Audit Logging

### 5.1 Audit Log Structure

```json
{
  "audit_id": "AUDIT-YYYY-NNNNN",
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "event_type": "data_deletion",
  "event_subtype": "automated|manual|revocation|account_closure",
  "data_details": {
    "data_type": "audio_recording|transcript|activity|consent|audit_log",
    "record_id": "UUID",
    "record_created_at": "YYYY-MM-DDTHH:MM:SSZ",
    "retention_period": "24_hours|90_days|1_year|3_years|5_years",
    "retention_expiration": "YYYY-MM-DDTHH:MM:SSZ"
  },
  "deletion_details": {
    "deletion_method": "secure_overwrite|cryptographic_erasure|file_deletion",
    "deletion_confirmed": true,
    "confirmation_method": "file_system_check|database_verification",
    "deletion_duration_ms": 150
  },
  "verification_details": {
    "primary_storage_cleared": true,
    "backup_deletion_scheduled": true,
    "backup_deletion_date": "YYYY-MM-DDTHH:MM:SSZ",
    "cache_cleared": true,
    "index_entries_removed": true
  },
  "compliance_context": {
    "trigger": "time_based|consent_revocation|account_closure|manual_request",
    "legal_basis": "COPPA §312.10|GDPR Art.5(1)(e)|PIPL Art.19",
    "policy_reference": "CTS-DRP-001 Section 2.1"
  },
  "actor": {
    "type": "system|user",
    "id": "system_automated|user_id",
    "ip_address": "if_applicable"
  }
}
```

### 5.2 Audit Log Examples

**Example 1: Automated Audio Deletion**

```json
{
  "audit_id": "AUDIT-2026-00001",
  "timestamp": "2026-04-30T12:00:00Z",
  "event_type": "data_deletion",
  "event_subtype": "automated",
  "data_details": {
    "data_type": "audio_recording",
    "record_id": "AUDIO-2026-00001",
    "record_created_at": "2026-04-29T11:55:00Z",
    "retention_period": "24_hours",
    "retention_expiration": "2026-04-30T11:55:00Z"
  },
  "deletion_details": {
    "deletion_method": "secure_overwrite",
    "deletion_confirmed": true,
    "confirmation_method": "file_system_check",
    "deletion_duration_ms": 145
  },
  "verification_details": {
    "primary_storage_cleared": true,
    "backup_deletion_scheduled": true,
    "backup_deletion_date": "2026-05-30T12:00:00Z",
    "cache_cleared": true,
    "index_entries_removed": true
  },
  "compliance_context": {
    "trigger": "time_based",
    "legal_basis": "COPPA §312.10",
    "policy_reference": "CTS-DRP-001 Section 2.1"
  },
  "actor": {
    "type": "system",
    "id": "system_automated"
  }
}
```

**Example 2: Consent Revocation Deletion**

```json
{
  "audit_id": "AUDIT-2026-00002",
  "timestamp": "2026-04-30T14:30:00Z",
  "event_type": "data_deletion",
  "event_subtype": "revocation",
  "data_details": {
    "data_type": "transcript",
    "record_id": "TRANSCRIPT-2026-00001",
    "record_created_at": "2026-04-15T10:00:00Z",
    "retention_period": "90_days",
    "retention_expiration": "2026-07-14T10:00:00Z"
  },
  "deletion_details": {
    "deletion_method": "database_deletion",
    "deletion_confirmed": true,
    "confirmation_method": "database_verification",
    "deletion_duration_ms": 52
  },
  "verification_details": {
    "primary_storage_cleared": true,
    "backup_deletion_scheduled": true,
    "backup_deletion_date": "2026-05-30T14:30:00Z",
    "cache_cleared": true,
    "index_entries_removed": true
  },
  "compliance_context": {
    "trigger": "consent_revocation",
    "legal_basis": "GDPR Art.17",
    "policy_reference": "CTS-DRP-001 Section 3.2",
    "consent_id": "CONSENT-2026-00001"
  },
  "actor": {
    "type": "user",
    "id": "privacy_officer_001"
  }
}
```

### 5.3 Audit Log Query Examples

```sql
-- Query: All deletions in the last 30 days
SELECT 
    audit_id,
    timestamp,
    event_subtype,
    data_type,
    record_id,
    deletion_method,
    deletion_confirmed,
    trigger
FROM deletion_audit_log
WHERE timestamp > NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC;

-- Query: Deletion verification status
SELECT 
    data_type,
    COUNT(*) as total_deletions,
    SUM(CASE WHEN deletion_confirmed THEN 1 ELSE 0 END) as confirmed,
    SUM(CASE WHEN NOT deletion_confirmed THEN 1 ELSE 0 END) as unconfirmed,
    AVG(deletion_duration_ms) as avg_duration_ms
FROM deletion_audit_log
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY data_type;

-- Query: Backup deletion compliance
SELECT 
    data_type,
    COUNT(*) as total_scheduled,
    SUM(CASE WHEN backup_deletion_date < NOW() THEN 1 ELSE 0 END) as overdue,
    MIN(backup_deletion_date) as next_due
FROM deletion_audit_log
WHERE backup_deletion_scheduled = true
GROUP BY data_type;
```

---

## 6. Special Retention Scenarios

### 6.1 Legal Hold

In the event of litigation or regulatory investigation:

```python
class LegalHoldManager:
    """
    Manages data retention during legal proceedings.
    Overrides normal retention periods when required.
    """
    
    def place_legal_hold(self, hold_request: LegalHoldRequest):
        """
        Place a legal hold on specified data.
        Prevents automatic deletion until hold is released.
        """
        # Identify affected records
        records = self.identify_hold_records(hold_request)
        
        for record in records:
            record.legal_hold = True
            record.legal_hold_id = hold_request.id
            record.legal_hold_reason = hold_request.reason
            record.legal_hold_date = datetime.utcnow()
            
            # Cancel any scheduled deletions
            self.cancel_scheduled_deletion(record.id)
        
        # Log legal hold
        self.log_legal_hold(
            hold_id=hold_request.id,
            records_affected=len(records),
            reason=hold_request.reason
        )
        
        # Notify CPSO
        self.notify_cpso(hold_request)
    
    def release_legal_hold(self, hold_id: str):
        """
        Release legal hold and resume normal retention.
        """
        hold = LegalHold.query.get(hold_id)
        records = self.get_hold_records(hold_id)
        
        for record in records:
            record.legal_hold = False
            record.legal_hold_id = None
            
            # Reschedule deletion per normal retention
            self.schedule_deletion(record)
        
        # Log hold release
        self.log_hold_release(
            hold_id=hold_id,
            records_released=len(records)
        )
```

### 6.2 Backup Retention

Backups follow a staggered deletion schedule:

| Backup Type | Retention After Primary Deletion | Purpose |
|-------------|----------------------------------|---------|
| Real-time Replication | 24 hours | Immediate recovery |
| Daily Backup | 7 days | Short-term recovery |
| Weekly Backup | 30 days | Medium-term recovery |
| Monthly Backup | 90 days | Long-term recovery |

**Critical**: When primary data is deleted, backup deletion is automatically scheduled.

### 6.3 Cross-Border Data Residency

For data subject to cross-border transfer restrictions:

```python
def handle_cross_border_retention(self, data: dict, jurisdiction: str):
    """
    Apply jurisdiction-specific retention rules.
    """
    if jurisdiction == 'china':
        # PIPL: Data must be stored in China
        # Apply Chinese retention rules
        retention_period = self.get_china_retention_period(data['type'])
        storage_location = 'china_mainland'
    elif jurisdiction == 'eu':
        # GDPR: Data must stay in EEA or have adequate protection
        retention_period = self.get_eu_retention_period(data['type'])
        storage_location = 'eu_region'
    else:
        # Default: Apply strictest retention
        retention_period = self.get_minimum_retention_period(data['type'])
        storage_location = 'default_region'
    
    return {
        'retention_period': retention_period,
        'storage_location': storage_location,
        'deletion_schedule': self.calculate_deletion_schedule(data, retention_period)
    }
```

---

## 7. Emergency Deletion Procedures

### 7.1 Emergency Deletion Triggers

Emergency deletion is initiated when:

1. **Data Breach**: Unauthorized access to children's data
2. **Consent Fraud**: Consent obtained through deception
3. **Regulatory Order**: Direct order from FTC, DPA, or CAC
4. **Security Vulnerability**: Critical vulnerability exposing data
5. **Vendor Compromise**: Third-party vendor security incident

### 7.2 Emergency Deletion Process

```python
class EmergencyDeletionProcedure:
    """
    Emergency deletion process for critical incidents.
    Target: Complete deletion within 4 hours.
    """
    
    def initiate_emergency_deletion(self, incident: Incident):
        """
        Initiate emergency deletion based on incident.
        """
        # Step 1: Stop all data collection (immediate)
        self.stop_all_collection()
        log("Collection stopped", timestamp=datetime.utcnow())
        
        # Step 2: Identify affected data (within 30 minutes)
        affected_data = self.identify_affected_data(incident)
        log("Data identified", count=len(affected_data), timestamp=datetime.utcnow())
        
        # Step 3: Execute deletion (within 2 hours)
        deletion_results = self.execute_emergency_deletion(affected_data)
        log("Deletion executed", results=deletion_results, timestamp=datetime.utcnow())
        
        # Step 4: Verify deletion (within 1 hour)
        verification = self.verify_emergency_deletion(affected_data)
        log("Deletion verified", verification=verification, timestamp=datetime.utcnow())
        
        # Step 5: Delete backups (within 4 hours)
        self.schedule_emergency_backup_deletion(affected_data)
        log("Backup deletion scheduled", timestamp=datetime.utcnow())
        
        # Step 6: Generate incident report
        report = self.generate_emergency_report(
            incident=incident,
            affected_data=affected_data,
            deletion_results=deletion_results,
            verification=verification
        )
        
        # Step 7: Notify authorities if required
        if self.requires_notification(incident):
            self.notify_authorities(report)
        
        return report
```

---

## 8. Compliance Reporting

### 8.1 Monthly Retention Compliance Report

```python
def generate_monthly_retention_report() -> dict:
    """
    Generate monthly compliance report on data retention.
    Submitted to CPSO and archived.
    """
    return {
        'report_period': 'YYYY-MM',
        'generated_at': datetime.utcnow().isoformat(),
        
        'retention_compliance': {
            'audio_recordings': {
                'records_processed': 1500,
                'records_deleted_on_time': 1500,
                'records_deleted_late': 0,
                'compliance_rate': '100%',
                'average_deletion_time_hours': 22.5
            },
            'transcripts': {
                'records_processed': 1200,
                'records_deleted_on_time': 1200,
                'records_deleted_late': 0,
                'compliance_rate': '100%'
            },
            'activity_data': {
                'records_processed': 800,
                'records_deleted_on_time': 800,
                'records_deleted_late': 0,
                'compliance_rate': '100%'
            }
        },
        
        'deletion_statistics': {
            'total_deletions': 3500,
            'automated_deletions': 3450,
            'manual_deletions': 50,
            'emergency_deletions': 0,
            'average_deletion_duration_ms': 125
        },
        
        'compliance_violations': {
            'total_violations': 0,
            'critical_violations': 0,
            'remediation_time_avg_hours': 0
        },
        
        'audit_log_summary': {
            'total_audit_entries': 3500,
            'verified_deletions': 3500,
            'unverified_deletions': 0
        },
        
        'recommendations': [],
        'next_review_date': 'YYYY-MM-DD'
    }
```

---

## 9. Policy Exceptions

### 9.1 Exception Process

Any exception to this retention policy requires:

1. Written request to CPSO
2. Legal review and approval
3. Documentation of justification
4. Defined exception period
5. Compensating controls
6. Regular review of exception

### 9.2 Exception Register

| Exception ID | Data Type | Justification | Approved By | Expiration | Status |
|--------------|-----------|---------------|-------------|------------|--------|
| EXC-001 | [Type] | [Reason] | [Name] | [Date] | Active/Expired |

---

## Appendices

### Appendix A: Retention Period Quick Reference

| Data Type | Retention Period | Auto-Delete Trigger |
|-----------|------------------|---------------------|
| Audio Recordings | 24 hours | After processing |
| Audio Cache | 1 hour | After processing |
| Transcripts | 90 days | Activity date |
| AI Summaries | 1 academic year | Activity date |
| Activity Trees | 1 academic year | Activity date |
| Teacher Reviews | 2 academic years | Review date |
| Consent Records | 3 years | Consent end |
| Audit Logs | 3 years | Log creation |
| Breach Records | 5 years | Breach closure |
| System Logs | 90 days | Log creation |
| Backups | Source + 30 days | Source deletion |

### Appendix B: Related Documents

- security-program.md - Written Information Security Program
- consent-architecture.md - Two-Tier Consent Architecture
- dpa-template.md - Data Processing Agreement Template
- breach-notification.md - Breach Notification Pipeline

---

*This policy shall be reviewed annually or when significant changes occur to retention requirements or deletion mechanisms.*
