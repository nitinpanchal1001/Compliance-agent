# Northwind Health & Finance — Q2 Compliance Self-Assessment (Internal)

Prepared by: Risk & Engineering. Status: working draft for the upcoming external audit.
Scope: the production platform that processes card payments, stores patient billing
records, and manages investor reporting for a publicly listed entity. This self-assessment
records current practice honestly, including known gaps, so they can be remediated before
the audit.

## 1. Cardholder data environment (CDE)

- The full card number (PAN), expiry date, and the card verification value (CVV) are
  stored together in plaintext in the `billing.cards` table so that recurring charges can
  run without re-collecting card details. This has been in place since the original build.
- The internal back-office tool prints the complete, unmasked PAN on the customer detail
  screen for every support agent, regardless of role.
- Card data is pushed to a fraud-analytics vendor over an unencrypted HTTP endpoint.
- We do encrypt PAN in our data warehouse, but the AES key is checked into the same Git
  repository as the application code and is readable by the whole engineering team.
- The cardholder password policy requires a minimum of eight characters but does not
  enforce complexity or block previously breached passwords.
- Audit logs in the CDE are retained for six months; the standard expectation is twelve.

## 2. Protected health information (PHI)

- Diagnosis codes, treatment notes, and insurance member IDs are stored unencrypted in the
  shared `patients` database, which is also used by analytics and marketing.
- Every authenticated employee can query patient records; there is no need-to-know or
  role-based restriction.
- Patient statements containing diagnosis details are emailed to an outsourced billing
  partner. We have a business associate agreement with our main partner, but two smaller
  partners that receive the same data have no signed agreement.
- Access to patient records is logged, but the logs are never reviewed and no one is
  assigned to monitor them.
- Our notice of privacy practices exists and is published, but it was last updated three
  years ago and does not reflect the marketing analytics processing we added since.

## 3. Personal data and privacy (EU customers)

- We retain all customer personal data indefinitely, including for accounts that were
  closed years ago, "in case the customer returns."
- The marketing team uses the full customer list, including EU residents, for email
  campaigns. Consent at sign-up was bundled into the general terms and not collected
  separately for marketing.
- EU customer data is continuously replicated to a US-hosted analytics warehouse. We do
  not have Standard Contractual Clauses or any other transfer mechanism in place.
- We maintain a record of processing activities, but it covers only the core product and
  omits several internal tools and the analytics pipeline.
- We respond to data subject access and deletion requests manually over email; there is a
  process and we usually answer, but responses routinely take three to four months.
- Our cookie banner sets analytics and advertising cookies before the user makes any
  choice; the "reject" option only takes effect on the next page load.

## 4. Financial reporting controls (SOX)

- Audit logging on the general-ledger database was disabled last quarter to reduce storage
  costs and has not been re-enabled.
- The same finance engineer can create, approve, and post journal entries; there is no
  segregation of duties for manual adjustments.
- Quarter-end adjustments are occasionally entered with a backdated timestamp so they fall
  into the prior reporting period.
- Management performs an annual assessment of internal control over financial reporting,
  but several remediation items from last year remain open and untracked.
- The change-management process for financial systems exists but allows developers to push
  emergency fixes to production without a documented approval, and these are reconciled
  "later" — sometimes weeks afterward.

## 5. Access management and authentication

- Multi-factor authentication is enforced for the customer-facing application and the VPN.
- However, the production database console is reached through a shared `ops` account whose
  password is stored in a team wiki page, and MFA is not enabled for it.
- Offboarding is handled by a quarterly access review rather than at the time of
  termination, so departed employees can retain access for up to three months.
- Service accounts use long-lived static credentials that have never been rotated.

## 6. Logging, monitoring, and resilience

- Application and security logs are centralized and retained for ninety days.
- Database backups run nightly and are restored-tested once a year; the disaster-recovery
  runbook, however, is more than a year out of date and references decommissioned systems.
- There is alerting for infrastructure availability, but no alerting on security-relevant
  events such as repeated failed logins or bulk data exports.

## 7. Vendor and third-party management

- Major vendors are reviewed at onboarding, and contracts include security terms.
- Smaller SaaS tools are adopted by individual teams without a security review, and at
  least one such tool receives customer email addresses.
- We do not maintain a current inventory of which third parties hold which categories of
  customer or patient data.

## 8. Retention and disposal

- We have a published data-retention schedule, but it is not enforced technically and most
  data is simply kept.
- Decommissioned laptops and drives are returned to a storage cupboard; there is no
  documented secure-wipe or destruction procedure before reuse or disposal.

## 9. Incident response and breach notification

- We do not have a documented incident response plan; response depends on whoever is
  on-call at the time.
- There is no defined breach-notification procedure or timeline for regulators or affected
  individuals.
- We have never run a tabletop exercise or breach simulation.

## 10. Governance and training

- Security and data-protection training is delivered to new joiners at onboarding but is
  not repeated annually for existing staff.
- We have not designated a data protection officer, despite large-scale processing of
  special-category (health) data.
- Compliance policies exist in a shared drive but have no owner and no scheduled review
  cycle, and several are over two years old.
