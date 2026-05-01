# Children's Thinking Tree System: Written Information Security Program

**Document ID**: CTS-WISP-001
**Version**: 1.0
**Effective Date**: 2026-04-30
**Next Review Date**: 2027-04-30
**Classification**: Internal - Confidential

---

## 1. Purpose and Scope

This Written Information Security Program ("WISP") establishes the administrative, technical, and physical safeguards for protecting children's personal information collected, processed, and stored by the Children's Thinking Tree System ("CTS System"). This program complies with:

- **COPPA** (Children's Online Privacy Protection Act, 15 U.S.C. §§ 6501-6506)
- **GDPR-K** (General Data Protection Regulation, Article 8 - child consent)
- **China PIPL** (Personal Information Protection Law, Article 28 - sensitive personal information of minors)

### 1.1 Scope of Protected Data

| Data Category | Classification | Examples |
|---------------|----------------|----------|
| Child Audio Recordings | Sensitive Personal Information | Raw voice recordings from classroom sessions |
| Child Voice Biometrics | Sensitive Personal Information | Voice patterns, speech characteristics |
| Speech Transcripts | Personal Information | rough_transcript, leaf_text derived from child speech |
| Activity Metadata | Personal Information | Activity participation records, timestamps |
| Child Identifiers | Personal Information | Student IDs, session identifiers |
| Teacher Account Data | Business Personal Information | Login credentials, activity history |

---

## 2. Designated Security Officer

### 2.1 Role Definition

**Title**: Chief Privacy and Security Officer (CPSO)
**Reports To**: Chief Executive Officer / Board of Directors
**Appointment Authority**: Board of Directors

### 2.2 Responsibilities

The CPSO shall:

1. **Program Oversight**
   - Maintain and update this WISP annually
   - Report security posture to executive leadership quarterly
   - Ensure compliance with COPPA, GDPR-K, and PIPL requirements

2. **Risk Management**
   - Conduct annual risk assessments for audio data collection
   - Approve all data processing activities involving children's data
   - Review and approve vendor security assessments

3. **Incident Response**
   - Serve as primary contact for data breach notifications
   - Maintain breach notification templates and contact lists
   - Coordinate with legal counsel on regulatory reporting

4. **Training and Awareness**
   - Develop annual privacy training for all staff
   - Ensure teachers understand consent requirements
   - Maintain training records for audit purposes

5. **Vendor Management**
   - Review Data Processing Agreements with all vendors
   - Conduct annual vendor security assessments
   - Maintain vendor inventory with risk classifications

### 2.3 Delegation

The CPSO may delegate specific tasks to:
- **Privacy Operations Manager**: Day-to-day privacy operations
- **Security Engineer**: Technical security implementation
- **Legal Counsel**: Regulatory interpretation and reporting

Delegation does not relieve the CPSO of ultimate accountability.

### 2.4 Contact Information

```
Chief Privacy and Security Officer
[Organization Name]
[Address]
Email: privacy@thinkingtree.example.com
Phone: [Emergency Phone Number]
```

---

## 3. Audio Collection Risk Assessment Methodology

### 3.1 Risk Assessment Framework

Risk assessments follow NIST SP 800-30 methodology, adapted for children's audio data:

```
Risk = Likelihood × Impact × Data Sensitivity Factor
```

**Data Sensitivity Factor for Children's Audio**: 3.0 (Maximum)

### 3.2 Threat Categories

| Threat ID | Threat Category | Description | Likelihood (1-5) | Impact (1-5) |
|-----------|-----------------|-------------|-------------------|---------------|
| T-AUD-01 | Unauthorized Audio Access | Access to raw audio recordings by unauthorized personnel | 3 | 5 |
| T-AUD-02 | Audio Data Breach | External breach exposing children's voice data | 2 | 5 |
| T-AUD-03 | Voice Profiling | Using audio for unintended biometric analysis | 2 | 5 |
| T-AUD-04 | Indefinite Retention | Failure to delete audio within policy timeframe | 3 | 4 |
| T-AUD-05 | Cross-border Transfer | Improper transfer of audio data across jurisdictions | 2 | 5 |
| T-AUD-06 | Vendor Data Misuse | Third-party vendor using audio for model training | 3 | 5 |
| T-AUD-07 | Insider Threat | Employee accessing audio without business need | 2 | 5 |
| T-AUD-08 | Technical Failure | System failure preventing timely audio deletion | 2 | 4 |

### 3.3 Risk Assessment Procedure

**Frequency**: Quarterly for audio-specific risks, annually for comprehensive assessment

**Steps**:

1. **Asset Inventory**
   - Identify all systems processing audio data
   - Map data flows from collection to deletion
   - Document storage locations and encryption status

2. **Threat Identification**
   - Review threat intelligence for audio processing systems
   - Analyze vendor security advisories
   - Consider regulatory enforcement actions

3. **Vulnerability Assessment**
   - Scan audio processing infrastructure quarterly
   - Review access logs for anomalies monthly
   - Test deletion mechanisms weekly

4. **Risk Calculation**
   ```
   Risk Score = Likelihood × Impact × Sensitivity Factor (3.0)
   Critical: Score ≥ 60
   High: Score 40-59
   Medium: Score 20-39
   Low: Score < 20
   ```

5. **Risk Treatment**
   - Critical/High risks: Immediate mitigation required (within 48 hours)
   - Medium risks: Mitigation plan within 30 days
   - Low risks: Document and accept with quarterly review

### 3.4 Audio-Specific Risk Controls

| Risk | Control | Verification |
|------|---------|--------------|
| T-AUD-01 | AES-256 encryption at rest, TLS 1.3 in transit | Monthly encryption audit |
| T-AUD-02 | Network segmentation, intrusion detection | Quarterly penetration test |
| T-AUD-03 | Prohibition on voice biometric extraction | Code review, API monitoring |
| T-AUD-04 | Automated deletion with 24-hour SLA | Daily deletion verification |
| T-AUD-05 | Geo-fencing, data residency controls | Monthly transfer log review |
| T-AUD-06 | DPA with training prohibition clause | Annual vendor audit |
| T-AUD-07 | Role-based access, audit logging | Weekly access review |
| T-AUD-08 | Redundant deletion triggers, monitoring | Weekly failure simulation |

---

## 4. Technical Safeguards

### 4.1 Encryption Standards

| Data State | Standard | Key Management |
|------------|----------|----------------|
| At Rest | AES-256-GCM | HSM-backed key storage, rotation every 90 days |
| In Transit | TLS 1.3 | Certificate pinning, HSTS enforcement |
| In Processing | Memory encryption | Secure enclaves where available |
| Backups | AES-256-GCM | Separate key from production |

### 4.2 Access Controls

**Principle of Least Privilege**

```
Role-Based Access Matrix:
┌─────────────────────┬────────────┬────────────┬────────────┬────────────┐
│ Role                │ Audio Data │ Transcript │ Activity   │ Admin      │
├─────────────────────┼────────────┼────────────┼────────────┼────────────┤
│ System Admin        │ No Access  │ No Access  │ Read       │ Full       │
│ Teacher             │ No Access  │ Read/Write │ Read/Write │ No Access  │
│ Privacy Officer     │ Audit Only │ Audit Only │ Audit      │ Limited    │
│ AI Service Account  │ Process    │ Write      │ Read       │ No Access  │
│ Support Staff       │ No Access  │ No Access  │ Read       │ No Access  │
└─────────────────────┴────────────┴────────────┴────────────┴────────────┘
```

**Authentication Requirements**:
- Multi-factor authentication for all administrative access
- Session timeout: 15 minutes inactivity
- Password policy: 12+ characters, complexity requirements
- Account lockout: 5 failed attempts, 30-minute lockout

### 4.3 Network Security

- **Segmentation**: Audio processing isolated in separate VLAN
- **Firewall Rules**: Default deny, explicit allow for required services
- **Intrusion Detection**: Real-time monitoring with automated alerting
- **DDoS Protection**: Cloud-based DDoS mitigation enabled

### 4.4 Application Security

- **Input Validation**: All audio data validated before processing
- **Output Encoding**: Prevent injection in transcript processing
- **API Security**: OAuth 2.0 with scoped tokens, rate limiting
- **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options

### 4.5 Audio Processing Security

```python
# Audio Processing Security Controls (Pseudocode)

class SecureAudioProcessor:
    def process_audio(self, audio_data: bytes, session_id: str):
        # 1. Validate session consent
        if not self.verify_consent(session_id):
            raise ConsentError("No valid consent for audio processing")
        
        # 2. Encrypt audio in memory
        encrypted_audio = self.encrypt_in_memory(audio_data)
        
        # 3. Process with AI model
        result = self.ai_model.analyze(encrypted_audio)
        
        # 4. Immediately purge audio from memory
        self.secure_wipe(audio_data)
        self.secure_wipe(encrypted_audio)
        
        # 5. Verify deletion
        if not self.verify_memory_cleared():
            raise SecurityError("Audio data not properly cleared from memory")
        
        # 6. Log processing event (no audio content)
        self.audit_log.record(
            session_id=session_id,
            action="audio_processed",
            timestamp=datetime.utcnow(),
            # NO audio content or transcript logged here
        )
        
        return result
```

---

## 5. Organizational Safeguards

### 5.1 Personnel Security

**Pre-Employment**:
- Background checks for all employees with data access
- Reference checks for positions handling children's data
- Signed confidentiality agreements

**During Employment**:
- Annual privacy and security training
- Acknowledgment of acceptable use policies
- Immediate revocation upon termination

**Training Schedule**:

| Training | Audience | Frequency | Duration |
|----------|----------|-----------|----------|
| COPPA/GDPR-K/PIPL Overview | All Staff | Annual | 2 hours |
| Audio Data Handling | Technical Staff | Semi-annual | 4 hours |
| Incident Response | CPSO Team | Quarterly | 2 hours |
| Teacher Consent Procedures | Teachers | Annual + onboarding | 1 hour |

### 5.2 Physical Security

- Data center access: Biometric + badge authentication
- Visitor logs maintained for 2 years
- Secure disposal of physical media
- Clean desk policy enforced

### 5.3 Operational Procedures

**Change Management**:
- All changes to audio processing systems require CPSO approval
- Security review before deployment
- Rollback procedures documented

**Incident Response**:
- Defined in breach-notification.md
- Tabletop exercises quarterly
- Post-incident reviews mandatory

---

## 6. Periodic Testing Schedule

### 6.1 Testing Calendar

| Test Type | Frequency | Responsible Party | Documentation |
|-----------|-----------|-------------------|---------------|
| Vulnerability Scan | Weekly | Security Engineer | Scan reports |
| Penetration Test | Quarterly | External Vendor | Pentest report |
| Audio Deletion Verification | Daily (Automated) | System Monitor | Deletion logs |
| Access Control Review | Monthly | Privacy Operations | Access audit report |
| Encryption Audit | Monthly | Security Engineer | Encryption status report |
| Backup Restoration Test | Quarterly | System Admin | Recovery test report |
| Incident Response Drill | Quarterly | CPSO Team | Exercise report |
| Compliance Assessment | Annual | External Auditor | Compliance report |

### 6.2 Testing Procedures

**Daily Automated Deletion Verification**:
```sql
-- Verify no audio exists beyond retention period
SELECT COUNT(*) as expired_audio_count
FROM audio_records
WHERE created_at < NOW() - INTERVAL '24 hours'
  AND deletion_status != 'confirmed_deleted';

-- Alert if any expired audio found
-- Expected result: 0 records
```

**Weekly Vulnerability Scan Checklist**:
- [ ] Audio processing servers scanned
- [ ] Database encryption verified
- [ ] API endpoints tested for injection
- [ ] Access logs reviewed for anomalies
- [ ] Certificate expiration checked

**Quarterly Penetration Test Scope**:
- Audio upload and processing pipeline
- Consent management system
- Deletion mechanism verification
- API security assessment
- Network segmentation validation

### 6.3 Testing Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Audio Deletion Success Rate | 100% | Daily verification |
| Vulnerability Remediation (Critical) | < 24 hours | Time to fix |
| Vulnerability Remediation (High) | < 7 days | Time to fix |
| Access Review Completion | 100% monthly | Review completion rate |
| Incident Response Time | < 1 hour | Time to containment |

---

## 7. Annual Evaluation Plan

### 7.1 Evaluation Scope

The annual evaluation shall assess:

1. **Regulatory Compliance**
   - COPPA compliance verification
   - GDPR-K compliance verification
   - PIPL compliance verification
   - Cross-border transfer compliance

2. **Technical Controls**
   - Encryption effectiveness
   - Access control effectiveness
   - Deletion mechanism reliability
   - Monitoring system accuracy

3. **Organizational Controls**
   - Training completion rates
   - Policy adherence
   - Incident response effectiveness
   - Vendor compliance

4. **Risk Management**
   - Risk assessment completeness
   - Risk treatment effectiveness
   - Emerging threat identification

### 7.2 Evaluation Timeline

| Quarter | Evaluation Activity |
|---------|---------------------|
| Q1 | Internal compliance audit, risk assessment update |
| Q2 | External penetration test, vendor security reviews |
| Q3 | Mid-year compliance review, training effectiveness assessment |
| Q4 | Annual comprehensive evaluation, report preparation |

### 7.3 Evaluation Methods

**Document Review**:
- Policy and procedure review
- Training record verification
- Incident log analysis
- Vendor DPA review

**Technical Testing**:
- Automated compliance scanning
- Manual security testing
- Deletion verification testing
- Performance and reliability testing

**Interviews and Surveys**:
- Staff privacy awareness survey
- Teacher consent process feedback
- Management security posture review

### 7.4 Annual Report Contents

The annual evaluation report shall include:

1. Executive Summary
2. Compliance Status by Regulation
3. Risk Assessment Results
4. Incident Summary and Trends
5. Training Completion Statistics
6. Vendor Compliance Status
7. Recommendations and Remediation Plan
8. Budget and Resource Requirements

### 7.5 Report Distribution

| Recipient | Report Version | Timing |
|-----------|----------------|--------|
| Board of Directors | Full Report | Within 30 days of completion |
| Executive Team | Executive Summary | Within 14 days of completion |
| CPSO Team | Full Report + Technical Details | Immediately upon completion |
| Regulatory Authorities | As required | Per regulatory requirements |

---

## 8. Vendor Due Diligence Process

### 8.1 Vendor Classification

| Vendor Type | Risk Level | Due Diligence Requirements |
|-------------|------------|---------------------------|
| AI Model Providers (Qwen, MiMo) | Critical | Full assessment, annual audit |
| Cloud Infrastructure | Critical | Full assessment, annual audit |
| Audio Processing Services | High | Standard assessment, bi-annual review |
| Development Tools | Medium | Basic assessment, annual review |
| Support Services | Low | Self-assessment questionnaire |

### 8.2 Due Diligence Procedure

**Step 1: Initial Assessment**

Before engaging any vendor that will process children's data:

1. Complete Vendor Security Questionnaire (VSQ)
2. Review vendor's SOC 2 Type II report (or equivalent)
3. Verify vendor's privacy policy compliance
4. Check vendor's regulatory certifications

**Step 2: Written Assurances**

Vendor must provide written assurances covering:

```
REQUIRED WRITTEN ASSURANCES CHECKLIST:

□ Data Processing Purpose Limitation
  - Audio data used only for providing the service
  - No use for model training or improvement
  - No sale or sharing with third parties

□ Data Security Measures
  - Encryption at rest and in transit
  - Access controls and authentication
  - Incident response procedures

□ Data Retention and Deletion
  - Immediate deletion after processing
  - Confirmation of deletion within 24 hours
  - No backup retention beyond 72 hours

□ Cross-Border Transfer Safeguards
  - Data residency commitments
  - Transfer impact assessments
  - Appropriate safeguards (SCCs, BCRs)

□ Regulatory Compliance
  - COPPA compliance acknowledgment
  - GDPR-K compliance commitment
  - PIPL compliance commitment

□ Audit Rights
  - Right to audit vendor's security practices
  - Annual compliance reports provided
  - Breach notification within 24 hours

□ Sub-processor Management
  - Prior written consent required
  - Same obligations flow down
  - Sub-processor list maintained
```

**Step 3: Technical Validation**

- API security testing
- Data flow verification
- Encryption validation
- Deletion mechanism testing

**Step 4: Contract Execution**

- Data Processing Agreement (see dpa-template.md)
- Service Level Agreement with security metrics
- Right to audit clause
- Termination for cause clause

### 8.3 Ongoing Vendor Monitoring

| Activity | Frequency | Documentation |
|----------|-----------|---------------|
| Security Questionnaire Review | Annual | Updated VSQ |
| Compliance Report Review | Annual | Vendor compliance report |
| Incident History Review | Quarterly | Incident log |
| Technical Security Assessment | Annual | Technical audit report |
| Contract Review | Annual | Updated DPA if needed |

### 8.4 Vendor Non-Compliance

If a vendor fails to meet requirements:

1. **Immediate**: Suspend data sharing
2. **Within 24 hours**: Notify CPSO
3. **Within 72 hours**: Issue remediation notice
4. **Within 30 days**: Verify remediation or terminate
5. **Within 90 days**: Complete transition to alternative vendor

### 8.5 Vendor Inventory

| Vendor | Service | Risk Level | DPA Status | Last Audit | Next Audit |
|--------|---------|------------|------------|------------|------------|
| Alibaba Cloud (Qwen) | AI Model Processing | Critical | Active | [Date] | [Date + 1 year] |
| Xiaomi (MiMo) | AI Model Processing | Critical | Active | [Date] | [Date + 1 year] |
| Cloud Storage Provider | Data Storage | Critical | Active | [Date] | [Date + 1 year] |
| [Additional Vendors] | [Service] | [Level] | [Status] | [Date] | [Date] |

---

## 9. Document Control

### 9.1 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-30 | CPSO | Initial release |

### 9.2 Review and Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Chief Privacy and Security Officer | [Name] | [Signature] | [Date] |
| Chief Executive Officer | [Name] | [Signature] | [Date] |
| Legal Counsel | [Name] | [Signature] | [Date] |

### 9.3 Distribution

This document is classified as **Internal - Confidential** and shall be distributed only to:
- Executive leadership
- Privacy and security team
- Legal counsel
- External auditors (under NDA)

---

## Appendices

### Appendix A: Regulatory Reference Matrix

| Requirement | COPPA | GDPR-K | PIPL | This Program Section |
|-------------|-------|--------|------|---------------------|
| Verifiable Parental Consent | §312.5 | Art. 8 | Art. 31 | consent-architecture.md |
| Data Minimization | §312.7 | Art. 5(1)(c) | Art. 6 | Section 4 |
| Purpose Limitation | §312.7 | Art. 5(1)(b) | Art. 6 | Section 4 |
| Data Security | §312.8 | Art. 32 | Art. 51 | Section 4, 5 |
| Data Retention Limits | §312.10 | Art. 5(1)(e) | Art. 19 | data-retention-policy.md |
| Breach Notification | N/A | Art. 33, 34 | Art. 57 | breach-notification.md |
| Data Protection Officer | N/A | Art. 37-39 | Art. 52 | Section 2 |

### Appendix B: Related Documents

- consent-architecture.md - Two-Tier Consent Architecture
- data-retention-policy.md - Data Retention and Deletion Policy
- dpa-template.md - Data Processing Agreement Template
- breach-notification.md - Breach Notification Pipeline
- annual-audit-plan.md - Annual Compliance Audit Plan

---

*This document shall be reviewed and updated annually, or more frequently if significant changes occur in the regulatory environment or system architecture.*
