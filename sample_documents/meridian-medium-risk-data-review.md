# Meridian Care & Capital — Data Protection Review (Internal)

Prepared by: Information Security & Compliance. Status: annual review, with open items.
Scope: the production platform that processes tokenized card payments, stores patient
billing records for partner clinics, and supports financial reporting for a listed entity.
This review records current practice and the partial gaps identified this cycle. The
fundamentals are in place; the findings below are improvements needed to reach full
maturity, not critical exposures.

## 1. Cardholder data environment (CDE)

- Cards are tokenized at capture by our payment processor; we do not store the full PAN and
  we never store sensitive authentication data such as CVV or track data.
- The last four digits are shown in the back office and the rest is masked.
- All cardholder traffic uses TLS; plaintext transmission is not permitted.
- Access to the CDE requires multi-factor authentication.
- Gap: CDE audit logs are retained for six months rather than the twelve months expected,
  because of storage limits we have not yet addressed.
- Gap: vulnerability scans are run quarterly, but remediation of medium-rated findings
  routinely slips past the target window and is not formally tracked to closure.

## 2. Protected health information (PHI)

- PHI is encrypted at rest and in transit; encryption is enabled across the patient data
  stores.
- Access to patient records is role-based for clinical and billing staff.
- Gap: encryption keys are managed by the platform team but the key-rotation schedule has
  lapsed and keys have not been rotated in over eighteen months.
- Gap: access to patient records is logged, but the logs are reviewed only on an ad-hoc
  basis rather than on a defined cadence, and no one formally owns the review.
- Gap: we have business associate agreements with our primary partners, but a recently
  added analytics sub-processor that receives de-identified-but-re-identifiable data is not
  yet covered by a signed agreement.
- Our notice of privacy practices is published but was last updated fourteen months ago.

## 3. Personal data and privacy (EU customers)

- We process personal data on a documented lawful basis and provide privacy notices at
  collection.
- Marketing consent is collected, but the sign-up flow bundles product and marketing
  consent into a single checkbox rather than separating them.
- Transfers of EU personal data to US sub-processors are covered by Standard Contractual
  Clauses; however, the supporting transfer impact assessment has not been completed.
- Gap: our record of processing activities exists but omits several internal tools and is
  more than a year out of date.
- Gap: data subject access and erasure requests are handled through a shared mailbox; we do
  respond, but turnaround averages six to eight weeks against the one-month deadline.
- Gap: retention periods are defined in policy but enforced manually, so some closed-account
  data persists beyond its stated period.
- The cookie banner offers accept and reject, but non-essential analytics cookies load a
  moment before the choice is registered.

## 4. Financial reporting controls (SOX)

- Audit logging on financial systems is enabled and retained.
- Duties are generally segregated, and journal entries require approval.
- Gap: a small number of "break-glass" finance admin accounts can both approve and post
  entries; their use is permitted for month-end but is not independently reviewed
  afterward.
- Gap: management performs the annual ICFR assessment, but remediation items from prior
  years are tracked informally in a spreadsheet and several remain open without owners.
- Change management for financial systems exists and is followed for planned changes, but
  emergency changes are documented retrospectively, sometimes several days later.

## 5. Access management and authentication

- Multi-factor authentication is enforced for employee application and VPN access, and the
  production console.
- Gap: offboarding relies on a monthly access-review sweep rather than immediate
  termination, so access can persist for a few weeks after departure.
- Gap: some service accounts use static credentials that are rotated only annually rather
  than automatically.

## 6. Logging, monitoring, and resilience

- Application and security logs are centralized and retained for ninety days.
- Backups run nightly and are encrypted.
- Gap: backup restoration is tested only once a year, and the last disaster-recovery
  exercise surfaced issues that have not all been resolved.
- Gap: alerting covers availability but not security events such as bulk data exports.

## 7. Vendor and third-party management

- Major vendors are security-reviewed at onboarding with contractual security terms.
- Gap: smaller SaaS tools are sometimes adopted by teams without a formal review, and our
  third-party data inventory is incomplete.

## 8. Retention and disposal

- A retention schedule is published and broadly followed.
- Gap: technical enforcement of deletion is partial; some datasets are deleted on a manual
  quarterly job that has occasionally been skipped.
- Decommissioned media is wiped, but certificates of destruction are not consistently
  retained.

## 9. Incident response and breach notification

- We maintain an incident response plan with defined roles.
- Gap: the breach-notification procedure references the 72-hour regulatory timeline but the
  internal escalation steps to meet it have not been tested in a tabletop exercise.

## 10. Governance and training

- Security and data-protection training is delivered at onboarding and annually.
- Gap: completion of annual refresher training is around 80% and is not actively chased.
- A data protection officer is appointed.
- Gap: several compliance policies are past their scheduled review date and are queued for
  update this cycle.
