# Summit Health Payments — Platform Data Handling Notes (Internal)

Author: Platform Engineering. Status: working notes, not yet reviewed by security.
Scope: the production system that processes card payments, stores patient billing records
for partner clinics, and feeds financial reporting for a listed parent company. These notes
describe how things actually work today, ahead of a security review we know is overdue.

## 1. Cardholder data environment (CDE)

- We store the primary account number (PAN) encrypted with AES in the `billing.cards`
  table so we can run recurring charges. We do not keep the CVV after authorization.
- The encryption key for the card table is stored on the same application servers that read
  the data, in a config file readable by the application service account.
- Card data is sent to our fraud-analytics vendor over plain HTTP because the vendor's TLS
  endpoint "was flaky," and this was never switched back.
- The back-office support tool shows the full, unmasked PAN to any agent who opens a
  customer record.
- Vulnerability scanning is not performed on the CDE, and several servers are months behind
  on security patches.

## 2. Protected health information (PHI)

- Patient diagnosis codes, treatment notes, and insurance IDs are encrypted at rest, but
  every authenticated employee can query the full patient database; there is no
  role-based or need-to-know restriction.
- Patient statements with diagnosis details are emailed in plaintext to our outsourced
  billing partner, and there is no signed business associate agreement with them.
- Access to patient records is not logged, so we cannot tell who has viewed what.
- We have not performed a HIPAA risk analysis.

## 3. Personal data and privacy (EU customers)

- EU customer personal data is continuously replicated to a US-hosted analytics warehouse,
  and we do not have Standard Contractual Clauses or any other transfer safeguard in place.
- We retain all customer personal data indefinitely, including for closed accounts.
- Marketing uses the full customer list; marketing consent was never collected separately
  and is bundled into the general terms.
- We do not have a working process for data subject access or erasure requests; such emails
  are usually left unanswered.
- We have not appointed a data protection officer despite large-scale processing of
  special-category health data.

## 4. Financial reporting controls (SOX)

- Audit logging on the general-ledger database was turned off to save storage and has not
  been re-enabled.
- The same finance engineer can create, approve, and post journal entries; there is no
  segregation of duties for manual adjustments.
- Management has not completed a formal assessment of internal control over financial
  reporting this year.
- Emergency changes to financial systems are pushed straight to production without approval
  and are reconciled later, if at all.

## 5. Access management and authentication

- Multi-factor authentication is enabled for the customer-facing application.
- The production database console is accessed through a shared `ops` account whose password
  is kept in a team wiki, and MFA is not enabled for it.
- Offboarding is handled whenever someone remembers; several former contractors still have
  active accounts.
- Service-account credentials are static and have never been rotated.

## 6. Logging, monitoring, and resilience

- Application logs are kept for thirty days; security-relevant events are not separated out
  and there is no alerting on suspicious activity such as bulk data exports.
- Backups run nightly but have not been restore-tested in over a year, and there is no
  disaster-recovery runbook.

## 7. Vendor and third-party management

- Teams adopt third-party tools without a security review, and several receive customer
  personal data.
- We do not maintain any inventory of which third parties hold which categories of customer
  or patient data, and most vendor contracts lack data-protection terms.

## 8. Retention and disposal

- There is no enforced retention schedule; data is kept indefinitely by default.
- Decommissioned drives are reused or discarded without any secure-wipe procedure.

## 9. Incident response and breach notification

- There is no documented incident response plan.
- There is no breach-notification procedure and no defined timeline for notifying
  regulators or affected individuals; a previous suspected incident was never reported.

## 10. Governance and training

- New joiners receive a short security briefing, but there is no recurring security or
  data-protection training for existing staff.
- Compliance policies are informal, unowned, and have not been reviewed in years.
