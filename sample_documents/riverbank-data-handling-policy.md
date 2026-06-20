# Riverbank Financial — Data Handling & Security Policy (v6)

Owner: Chief Information Security Officer. Review cycle: annual. Status: approved, in force.
Scope: the production platform that processes card payments, stores limited patient billing
records for partner clinics, and supports financial reporting for a listed entity. This
policy describes controls as they are implemented and verified in production.

## 1. Cardholder data environment (CDE)

- We do not store the primary account number (PAN) or any sensitive authentication data.
  Cards are tokenized at capture by our PCI-DSS Level 1 payment processor, and only the
  token and last four digits are retained.
- Sensitive authentication data (CVV, full track data, PINs) is never written to disk or
  logs at any stage of authorization.
- Where the last four digits are shown, the rest of the number is masked; no interface
  displays a full card number.
- All cardholder-adjacent traffic uses TLS 1.2+ with strong cipher suites; plaintext
  transmission is blocked at the gateway.
- Access to the CDE requires multi-factor authentication and is restricted by role on a
  documented need-to-know basis.
- CDE audit logs are centralized and retained for thirteen months, with the most recent
  three months immediately available.

## 2. Protected health information (PHI)

- PHI is encrypted at rest with AES-256 and in transit with TLS; encryption keys are held
  in a managed key-management service, separate from the data, with restricted custodianship.
- Access to patient records is role-based and limited to the minimum necessary; access is
  logged and the logs are reviewed weekly by the security team.
- Every partner that receives PHI is covered by a signed business associate agreement, and
  we maintain a current register of those agreements.
- Our notice of privacy practices is published and accurately reflects current processing.
- Workforce members complete HIPAA security and privacy training at onboarding and annually.

## 3. Personal data and privacy (EU customers)

- We process personal data on a documented lawful basis, and marketing consent is collected
  separately, is unbundled, and can be withdrawn at any time with one click.
- We retain personal data only for defined periods set out in our retention schedule, and
  closed-account data is deleted or anonymized after the stated period.
- Transfers of EU personal data to our US sub-processors are covered by Standard
  Contractual Clauses, supported by a transfer impact assessment.
- We maintain a complete record of processing activities covering the product and all
  internal tools, reviewed each year.
- Data subject access and erasure requests are handled through a tracked workflow and
  fulfilled within the one-month statutory deadline.
- Our cookie banner sets only strictly necessary cookies by default; analytics and
  advertising cookies load only after explicit opt-in.
- A data protection officer is appointed, is involved in privacy decisions, and reports to
  the board.

## 4. Financial reporting controls (SOX)

- Audit logging on financial systems, including the general ledger, is always enabled and
  monitored; logs are immutable and retained per policy.
- Duties are segregated so that no single person can create, approve, and post a journal
  entry; manual adjustments require independent approval.
- Period-end entries are dated to the actual transaction date; backdating is prohibited and
  detected by control reports.
- Management assesses internal control over financial reporting annually, and remediation
  items are tracked to closure in a central register.
- Changes to financial systems follow a documented change-management process with approval,
  testing, and segregation between development and production.

## 5. Access management and authentication

- Multi-factor authentication is enforced for all employee and administrative access,
  including the production database console; there are no shared accounts.
- Access is provisioned by role and de-provisioned automatically at termination through HR
  integration, typically within the hour.
- Service accounts use short-lived, automatically rotated credentials issued by our secrets
  manager.

## 6. Logging, monitoring, and resilience

- Application and security logs are centralized and retained for thirteen months, with
  alerting on security-relevant events such as repeated failed logins and bulk exports.
- Backups run nightly, are encrypted, and are restore-tested quarterly.
- The disaster-recovery runbook is reviewed every six months; the last review was four
  months ago. (Minor: the next scheduled review is due in two months.)

## 7. Vendor and third-party management

- All third parties undergo a security review before onboarding, with contractual security
  and data-protection terms.
- We maintain a current inventory mapping each third party to the categories of customer
  and patient data it holds.

## 8. Retention and disposal

- The retention schedule is enforced technically through automated deletion jobs.
- Decommissioned media is cryptographically wiped or physically destroyed under a
  documented procedure with certificates of destruction retained.

## 9. Incident response and breach notification

- We maintain a documented incident response plan with defined roles and escalation paths.
- Our breach-notification procedure commits to notifying the supervisory authority within
  72 hours and affected individuals without undue delay where required.
- We run a breach tabletop exercise twice a year.

## 10. Governance and training

- Security and data-protection training is delivered at onboarding and annually to all staff.
- Compliance policies have named owners and a scheduled annual review cycle.
- Minor housekeeping item: two low-impact internal runbooks are thirteen months past their
  twelve-month review target and are queued for refresh this quarter.
