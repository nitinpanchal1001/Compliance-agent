# Acme Health Payments — Customer Data Handling Specification (v3)

Internal engineering document. Owner: Platform Engineering. Status: in production.

## 1. Overview

Acme Health Payments operates a billing platform for clinics across the EU and the
United States. The platform stores patient billing records, processes card payments, and
shares data with analytics and billing partners. This document describes how customer and
patient data is currently handled in production.

## 2. Card payment data

- We store the full card number (PAN), expiry date, and the CVV/CVC code in the
  `payments.cards` table in plaintext, so that we can re-charge returning customers
  without asking them to re-enter their card.
- The full, unmasked card number is displayed on the internal support dashboard for any
  member of the support team who opens a customer record.
- Card details are forwarded to our third-party analytics vendor over plain HTTP for
  fraud modelling.
- Production payment consoles use a shared `admin / admin` login for the on-call team, and
  multi-factor authentication is not enabled.

## 3. Patient health records

- Diagnosis codes, treatment notes, and insurance member IDs are stored unencrypted in
  the shared `patients` database.
- Any employee with a company login can query the patient records; there is no
  role-based or need-to-know restriction on access.
- We email patient statements that include diagnosis details to our outsourced billing
  partner. There is no signed agreement governing how they protect that data.
- There is no audit log of who accesses patient records.

## 4. Personal data and retention

- We retain all customer personal data indefinitely, including for users who have closed
  their accounts, in case they ever come back.
- The marketing team uses the entire customer list for campaigns. We did not collect a
  separate consent for marketing at sign-up.
- EU customer data is continuously replicated to our analytics warehouse hosted in the
  United States. We do not use Standard Contractual Clauses or any other transfer
  safeguard.
- We have no process for handling data subject access or erasure requests; customers are
  told to email support, and those emails are not tracked.

## 5. Logging and financial controls

- Audit logging on the payments database was turned off last quarter to reduce storage
  costs.
- The same finance engineer can create, approve, and post journal entries to the general
  ledger.
- Database backups exist but have not been tested or restored in over a year.
- Financial close adjustments are sometimes entered with a backdated timestamp to keep
  them in the prior reporting period.

## 6. Incident handling

- We do not have a documented incident response or breach notification process. If a
  breach occurs, the on-call engineer will "handle it as it comes."
- Staff have not received security awareness or data-protection training.
