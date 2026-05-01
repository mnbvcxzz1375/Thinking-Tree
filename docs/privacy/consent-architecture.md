# Children's Thinking Tree System: Two-Tier Consent Architecture

**Document ID**: CTS-CONSENT-001
**Version**: 1.0
**Effective Date**: 2026-04-30
**Next Review Date**: 2027-04-30

---

## 1. Overview

The Children's Thinking Tree System implements a two-tier consent architecture to comply with COPPA, GDPR-K, and PIPL requirements for processing children's audio recordings in educational settings.

### 1.1 Consent Tiers

| Tier | Consent Holder | Scope | Legal Basis |
|------|----------------|-------|-------------|
| Tier 1 | School (as Agent) | Educational use only | COPPA "school consent" exception |
| Tier 2 | Parent/Guardian | Any non-educational use | Verifiable parental consent |

### 1.2 Key Principle

**School consent under COPPA is LIMITED to educational purposes.** Any use beyond the educational context requires separate, verifiable parental consent.

---

## 2. Tier 1: School-as-Agent Consent

### 2.1 Legal Basis

Under COPPA's "school consent" exception (16 CFR § 312.5(c)(4)), schools may consent on behalf of parents when:
- The operator collects personal information solely for the use and benefit of the school
- The operator does not use or disclose the information for any other purpose
- The school has authorized the collection

### 2.2 Scope of School Consent

**PERMITTED under School Consent**:

```
✓ Audio collection during classroom activities
✓ AI processing of audio for educational purposes
✓ Storage of activity results (tree nodes, summaries)
✓ Teacher access to activity data
✓ Educational reporting and progress tracking
✓ Export for parent-teacher conferences
```

**NOT PERMITTED under School Consent**:

```
✗ Use of audio for AI model training
✗ Sharing audio with third parties for non-educational purposes
✗ Behavioral advertising or profiling
✗ Commercial use of child data
✗ Retention beyond educational need
✗ Cross-border transfer without additional safeguards
```

### 2.3 School Consent Requirements

**Before System Deployment**, the school must:

1. **Authorize Collection**
   - Designate authorized personnel (teachers, administrators)
   - Specify approved educational activities
   - Define data retention period aligned with academic calendar

2. **Provide Notice to Parents**
   - Distribute privacy notice to all parents/guardians
   - Describe data collection practices
   - Explain the school's role in consenting
   - Provide contact information for questions

3. **Maintain Records**
   - Document authorization date
   - List authorized personnel
   - Record approved activities
   - Track parent notification completion

### 2.4 School Consent Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SCHOOL CONSENT FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ School Signs │     │ School       │     │ School       │
│ Agreement    │────▶│ Designates   │────▶│ Notifies     │
│              │     │ Personnel    │     │ Parents      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ System       │     │ Teacher      │     │ Parent       │
│ Activated    │◀────│ Verified     │◀────│ Notice       │
│ for School   │     │              │     │ Period       │
└──────────────┘     └──────────────┘     └──────────────┘
        │
        ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Teacher      │     │ Audio        │     │ AI Process   │
│ Creates      │────▶│ Collected    │────▶│ for          │
│ Activity     │     │ (Encrypted)  │     │ Education    │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
                                          ┌──────────────┐
                                          │ Results      │
                                          │ Stored       │
                                          │ (No Audio)   │
                                          └──────────────┘
```

### 2.5 School Consent Record Template

```json
{
  "school_consent_id": "SC-YYYY-NNNNN",
  "school_name": "[School Name]",
  "school_district": "[District Name]",
  "authorized_date": "YYYY-MM-DD",
  "authorized_by": {
    "name": "[Administrator Name]",
    "title": "[Title]",
    "email": "[Email]"
  },
  "authorized_activities": [
    "classroom_thinking_tree",
    "group_discussion_analysis",
    "individual_expression_recording"
  ],
  "authorized_personnel": [
    {
      "teacher_id": "T-001",
      "name": "[Teacher Name]",
      "classroom": "[Classroom]"
    }
  ],
  "parent_notice_date": "YYYY-MM-DD",
  "parent_notice_method": "email_and_paper",
  "parent_opt_out_count": 0,
  "data_retention_end_date": "YYYY-MM-DD",
  "renewal_required_date": "YYYY-MM-DD"
}
```

---

## 3. Tier 2: Parental Consent

### 3.1 When Parental Consent is Required

Separate parental consent is required for ANY use beyond educational purposes:

| Use Case | School Consent Sufficient? | Parental Consent Required? |
|----------|---------------------------|---------------------------|
| Classroom activity processing | Yes | No |
| Educational progress reports | Yes | No |
| Parent-teacher conference materials | Yes | No |
| AI model improvement/training | No | **Yes** |
| Sharing with research partners | No | **Yes** |
| Long-term retention beyond semester | No | **Yes** |
| Use in marketing or publications | No | **Yes** |
| Cross-border transfer for non-educational purposes | No | **Yes** |

### 3.2 Verifiable Parental Consent Methods

Per COPPA requirements, we implement the following consent methods:

**Method 1: Signed Consent Form (Preferred)**
- Paper or electronic form with parent signature
- Must include specific description of data use
- Retained for duration of data use + 3 years

**Method 2: Credit Card Verification**
- Small charge ($0.50) with immediate refund
- Provides verification of adult identity
- Transaction record retained

**Method 3: Video Conference Verification**
- Live video call with parent
- Identity verified against government ID
- Call recording retained for 90 days

**Method 4: Government ID Verification**
- Upload of government-verified ID
- ID number partially redacted after verification
- Verification record retained

### 3.3 Parental Consent Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PARENTAL CONSENT FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Non-         │     │ System       │     │ Parent       │
│ Educational  │────▶│ Generates    │────▶│ Receives     │
│ Use Requested│     │ Consent Form │     │ Request      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Consent      │     │ Parent       │     │ Identity     │
│ Form Sent    │────▶│ Reviews      │────▶│ Verification │
│ (Digital)    │     │ Details      │     │ Required     │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          ▼                        ▼                        ▼
                   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
                   │ Signed Form  │     │ Credit Card  │     │ Video Call   │
                   │ (Preferred)  │     │ Verification │     │ Verification │
                   └──────────────┘     └──────────────┘     └──────────────┘
                          │                        │                        │
                          └────────────────────────┼────────────────────────┘
                                                   ▼
                                          ┌──────────────┐
                                          │ Consent      │
                                          │ Verified     │
                                          └──────────────┘
                                                   │
                          ┌────────────────────────┼────────────────────────┐
                          ▼                        ▼                        ▼
                   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
                   │ Consent      │     │ Consent      │     │ Consent      │
                   │ Granted      │     │ Denied       │     │ Expired      │
                   └──────────────┘     └──────────────┘     └──────────────┘
                          │                        │                        │
                          ▼                        ▼                        ▼
                   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
                   │ Non-         │     │ Non-         │     │ Data         │
                   │ Educational  │     │ Educational  │     │ Deleted      │
                   │ Use Enabled  │     │ Use Blocked  │     │              │
                   └──────────────┘     └──────────────┘     └──────────────┘
```

### 3.4 Parental Consent Form Template

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PARENTAL CONSENT FORM                                    │
│                 Children's Thinking Tree System                             │
└─────────────────────────────────────────────────────────────────────────────┘

PARENT/GUARDIAN INFORMATION
──────────────────────────────────────────────────────────────────────────────
Parent/Guardian Name: ____________________________________________________
Relationship to Child: __________________________________________________
Email Address: __________________________________________________________
Phone Number: __________________________________________________________

CHILD INFORMATION
──────────────────────────────────────────────────────────────────────────────
Child's Name: __________________________________________________________
Child's School: _________________________________________________________
Child's Classroom/Grade: ________________________________________________

PURPOSE OF CONSENT
──────────────────────────────────────────────────────────────────────────────
I understand that the Children's Thinking Tree System collects and processes
my child's voice recordings for the following NON-EDUCATIONAL purposes:

[ ] AI model improvement and training
[ ] Research and development
[ ] Publication in anonymized case studies
[ ] Other: _____________________________________________________________

DATA COLLECTED
──────────────────────────────────────────────────────────────────────────────
The following data will be collected:
- Voice recordings of my child's verbal responses
- Transcripts of my child's speech
- AI-generated summaries of my child's expressions
- Activity participation records

DATA USE
──────────────────────────────────────────────────────────────────────────────
The data will be used for:
- Processing by AI models (Qwen/MiMo) for speech analysis
- Storage for the purposes described above
- Retention for: [Specify duration: ____ months/years]

DATA SHARING
──────────────────────────────────────────────────────────────────────────────
The data may be shared with:
- [ ] AI model providers (Alibaba Cloud, Xiaomi) for processing
- [ ] Research partners (list: ________________________________________)
- [ ] Other: ___________________________________________________________

RIGHTS
──────────────────────────────────────────────────────────────────────────────
I understand that I have the right to:
- Revoke this consent at any time
- Request deletion of my child's data
- Access my child's data
- Obtain a copy of my child's data
- File a complaint with relevant authorities

CONSENT STATEMENT
──────────────────────────────────────────────────────────────────────────────
I have read and understand this consent form. I voluntarily consent to the
collection, use, and sharing of my child's data as described above.

□ I GRANT consent for the purposes described above.
□ I DO NOT GRANT consent.

Signature: _______________________________________ Date: _________________

Parent/Guardian Name (Print): ___________________________________________

VERIFICATION METHOD
──────────────────────────────────────────────────────────────────────────────
□ Signed form submitted electronically
□ Credit card verification completed
□ Video conference verification completed
□ Government ID verification completed

Verification ID: ________________________________________________________
Verification Date: ______________________________________________________
```

---

## 4. Consent Management System

### 4.1 Consent Record Structure

```json
{
  "consent_id": "CONSENT-YYYY-NNNNN",
  "child_id": "CHILD-YYYY-NNNNN",
  "consent_type": "parental|school_agent",
  "consent_status": "active|revoked|expired|pending",
  "consent_granted_date": "YYYY-MM-DDTHH:MM:SSZ",
  "consent_expiration_date": "YYYY-MM-DDTHH:MM:SSZ",
  "verification_method": "signed_form|credit_card|video_call|government_id",
  "verification_id": "VER-YYYY-NNNNN",
  "permitted_purposes": [
    "educational_processing",
    "ai_model_training",
    "research_use"
  ],
  "data_sharing_consents": [
    {
      "recipient": "alibaba_cloud_qwen",
      "purpose": "ai_processing",
      "consented": true
    },
    {
      "recipient": "xiaomi_mimo",
      "purpose": "ai_processing",
      "consented": true
    }
  ],
  "parent_contact": {
    "name": "[Parent Name]",
    "email": "[parent@email.com]",
    "phone": "[Phone Number]"
  },
  "school_context": {
    "school_id": "SCHOOL-YYYY-NNNNN",
    "teacher_id": "TEACHER-YYYY-NNNNN",
    "activity_id": "ACT-YYYY-NNNNN"
  },
  "audit_trail": [
    {
      "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
      "action": "consent_granted",
      "actor": "parent",
      "details": "Consent form signed electronically"
    }
  ]
}
```

### 4.2 Consent Verification Logic

```python
class ConsentManager:
    def can_process_audio(self, child_id: str, purpose: str) -> bool:
        """
        Determine if audio can be processed for the given purpose.
        
        Args:
            child_id: Unique identifier for the child
            purpose: 'educational' or 'non_educational'
            
        Returns:
            True if processing is permitted, False otherwise
        """
        # Get school consent for this child's school
        school_consent = self.get_school_consent(child_id)
        
        if purpose == 'educational':
            # Educational purposes can use school consent
            if school_consent and school_consent.is_active():
                return True
            return False
        
        elif purpose == 'non_educational':
            # Non-educational purposes require parental consent
            parental_consent = self.get_parental_consent(child_id)
            
            if parental_consent and parental_consent.is_active():
                # Check if the specific purpose is consented
                if purpose in parental_consent.permitted_purposes:
                    return True
            
            return False
        
        return False
    
    def get_consent_status(self, child_id: str) -> dict:
        """
        Get complete consent status for a child.
        
        Returns dict with:
        - school_consent: School consent details
        - parental_consent: Parental consent details (if any)
        - can_process_educational: Boolean
        - can_process_non_educational: Boolean
        """
        school_consent = self.get_school_consent(child_id)
        parental_consent = self.get_parental_consent(child_id)
        
        return {
            "child_id": child_id,
            "school_consent": school_consent.to_dict() if school_consent else None,
            "parental_consent": parental_consent.to_dict() if parental_consent else None,
            "can_process_educational": (
                school_consent is not None and school_consent.is_active()
            ),
            "can_process_non_educational": (
                parental_consent is not None and parental_consent.is_active()
            )
        }
```

---

## 5. Consent Revocation Process

### 5.1 Revocation Rights

Parents and guardians have the right to revoke consent at any time. Revocation applies to:

- Future data collection
- Existing data processing
- Data sharing with third parties
- Data retention

**Note**: Revocation does not affect the lawfulness of processing prior to revocation.

### 5.2 Revocation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONSENT REVOCATION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Parent       │     │ System       │     │ Revocation   │
│ Requests     │────▶│ Verifies     │────▶│ Request      │
│ Revocation   │     │ Identity     │     │ Logged       │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Confirmation │     │ School       │     │ CPSO         │
│ Sent to      │◀────│ Notified     │◀────│ Notified     │
│ Parent       │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
        │
        ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Future       │     │ Existing     │     │ Third-Party  │
│ Collection   │────▶│ Data         │────▶│ Sharing      │
│ Stopped      │     │ Assessment   │     │ Stopped      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
                                          ┌──────────────┐
                                          │ Deletion     │
                                          │ Initiated    │
                                          │ (if required)│
                                          └──────────────┘
```

### 5.3 Revocation Timeline

| Action | Timeline | Responsible Party |
|--------|----------|-------------------|
| Acknowledge revocation request | Within 24 hours | System automated |
| Stop future data collection | Immediately | System automated |
| Notify school administrator | Within 24 hours | System automated |
| Assess existing data | Within 72 hours | Privacy Operations |
| Stop third-party sharing | Within 48 hours | Privacy Operations |
| Delete data (if required) | Within 30 days | Privacy Operations |
| Confirm deletion to parent | Within 35 days | Privacy Operations |

### 5.4 Revocation Methods

Parents can revoke consent through:

1. **Online Portal**
   - Login to parent account
   - Navigate to Consent Management
   - Click "Revoke Consent"
   - Confirm identity via email verification

2. **Email Request**
   - Send email to privacy@thinkingtree.example.com
   - Include child's name, school, and classroom
   - System sends confirmation email
   - Revocation processed after identity verification

3. **Written Request**
   - Send letter to organization address
   - Include child's information and parent signature
   - Revocation processed within 5 business days of receipt

4. **Phone Request**
   - Call privacy hotline
   - Identity verified via security questions
   - Revocation processed during call
   - Confirmation sent via email

### 5.5 Revocation Record Template

```json
{
  "revocation_id": "REV-YYYY-NNNNN",
  "consent_id": "CONSENT-YYYY-NNNNN",
  "child_id": "CHILD-YYYY-NNNNN",
  "revocation_date": "YYYY-MM-DDTHH:MM:SSZ",
  "revocation_method": "online_portal|email|written|phone",
  "revocation_reason": "optional_parent_provided_reason",
  "identity_verification": {
    "method": "email_verification|security_questions|signature_match",
    "verified": true,
    "verified_by": "system|operator_name",
    "verified_at": "YYYY-MM-DDTHH:MM:SSZ"
  },
  "actions_taken": {
    "future_collection_stopped": {
      "status": "completed",
      "timestamp": "YYYY-MM-DDTHH:MM:SSZ"
    },
    "school_notified": {
      "status": "completed",
      "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
      "notified_contact": "teacher@school.edu"
    },
    "third_party_sharing_stopped": {
      "status": "completed",
      "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
      "vendors_notified": ["alibaba_cloud", "xiaomi"]
    },
    "data_assessment": {
      "status": "in_progress",
      "data_found": true,
      "data_types": ["audio_recordings", "transcripts", "activity_records"],
      "deletion_initiated": true,
      "deletion_deadline": "YYYY-MM-DDTHH:MM:SSZ"
    }
  },
  "confirmation_sent": {
    "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
    "method": "email",
    "recipient": "parent@email.com"
  }
}
```

---

## 6. Consent for Different Jurisdictions

### 6.1 COPPA (United States)

**Age Threshold**: Under 13
**Consent Requirement**: Verifiable parental consent
**School Exception**: Allowed for educational purposes only
**Enforcement**: FTC

### 6.2 GDPR-K (European Union)

**Age Threshold**: Under 16 (member states may lower to 13)
**Consent Requirement**: Parental consent for information society services
**School Exception**: Not explicitly provided; legitimate interest may apply
**Enforcement**: National DPAs

### 6.3 PIPL (China)

**Age Threshold**: Under 14
**Consent Requirement**: Parental consent with separate consent for sensitive data
**School Exception**: Not explicitly provided; consent required
**Enforcement**: CAC

### 6.4 Jurisdiction-Specific Consent Matrix

| Requirement | COPPA | GDPR-K | PIPL |
|-------------|-------|--------|------|
| Age Threshold | <13 | <16 (varies) | <14 |
| Parental Consent | Verifiable | Explicit | Separate consent |
| School Exception | Yes (limited) | No explicit | No explicit |
| Consent Renewal | Not required | Not required | Not specified |
| Right to Revoke | Yes | Yes | Yes |
| Data Portability | No | Yes | Yes |

---

## 7. Technical Implementation

### 7.1 Consent Check API

```python
# API Endpoint: POST /api/consent/check

class ConsentCheckRequest(BaseModel):
    child_id: str
    purpose: str  # 'educational' or 'non_educational'
    data_types: List[str]  # ['audio', 'transcript', 'activity']

class ConsentCheckResponse(BaseModel):
    permitted: bool
    consent_type: str  # 'school_agent', 'parental', 'none'
    consent_id: Optional[str]
    restrictions: List[str]  # Any restrictions on use
    expiration: Optional[datetime]
    audit_id: str  # For tracking this check

@app.post("/api/consent/check")
async def check_consent(request: ConsentCheckRequest):
    """
    Verify consent before any data processing.
    Must be called before audio collection or processing.
    """
    # Get consent status
    consent_status = consent_manager.get_consent_status(request.child_id)
    
    # Check if processing is permitted
    if request.purpose == 'educational':
        permitted = consent_status['can_process_educational']
        consent_type = 'school_agent'
    else:
        permitted = consent_status['can_process_non_educational']
        consent_type = 'parental'
    
    # Log the consent check
    audit_id = audit_logger.log_consent_check(
        child_id=request.child_id,
        purpose=request.purpose,
        permitted=permitted,
        consent_type=consent_type
    )
    
    return ConsentCheckResponse(
        permitted=permitted,
        consent_type=consent_type,
        consent_id=consent_status.get('consent_id'),
        restrictions=consent_status.get('restrictions', []),
        expiration=consent_status.get('expiration'),
        audit_id=audit_id
    )
```

### 7.2 Consent Enforcement Middleware

```python
class ConsentEnforcementMiddleware:
    """
    Middleware that enforces consent checks on all audio-related endpoints.
    """
    
    AUDIO_ENDPOINTS = [
        '/api/activities/*/speech/analyze',
        '/api/audio/*',
    ]
    
    async def __call__(self, request, call_next):
        # Check if this is an audio-related endpoint
        if self._is_audio_endpoint(request.url.path):
            # Extract child_id from request
            child_id = self._extract_child_id(request)
            purpose = self._determine_purpose(request)
            
            # Check consent
            consent_check = await self._check_consent(child_id, purpose)
            
            if not consent_check.permitted:
                # Block processing and return appropriate error
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "consent_required",
                        "message": f"Consent not found for {purpose} processing",
                        "consent_type_required": consent_check.required_type,
                        "consent_form_url": "/consent/request"
                    }
                )
        
        # Proceed with request
        response = await call_next(request)
        return response
```

---

## 8. Audit and Compliance

### 8.1 Consent Audit Requirements

| Audit Type | Frequency | Scope |
|------------|-----------|-------|
| Consent Record Audit | Monthly | Verify all consent records are complete and current |
| Consent Enforcement Audit | Quarterly | Verify consent checks are enforced on all endpoints |
| Revocation Processing Audit | Quarterly | Verify revocations are processed within SLA |
| School Consent Renewal | Annual | Verify school consents are renewed |

### 8.2 Compliance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Consent check compliance | 100% | All audio endpoints checked |
| Revocation processing time | < 24 hours | Time from request to action |
| School consent renewal rate | 100% | Annual renewal completion |
| Parent notification rate | 100% | All parents notified |

---

## Appendices

### Appendix A: Consent Decision Tree

```
START: Audio Processing Request
│
├─ Is purpose educational?
│  │
│  ├─ YES
│  │  │
│  │  └─ Is school consent active?
│  │     │
│  │     ├─ YES → PERMITTED (School Agent Consent)
│  │     │
│  │     └─ NO → BLOCKED (Require school consent)
│  │
│  └─ NO
│     │
│     └─ Is parental consent active?
│        │
│        ├─ YES
│        │  │
│        │  └─ Is this specific purpose consented?
│        │     │
│        │     ├─ YES → PERMITTED (Parental Consent)
│        │     │
│        │     └─ NO → BLOCKED (Require specific consent)
│        │
│        └─ NO → BLOCKED (Require parental consent)
│
END
```

### Appendix B: Related Documents

- security-program.md - Written Information Security Program
- data-retention-policy.md - Data Retention and Deletion Policy
- dpa-template.md - Data Processing Agreement Template
- breach-notification.md - Breach Notification Pipeline

---

*This document shall be reviewed annually or when significant changes occur to the consent management system or regulatory requirements.*
