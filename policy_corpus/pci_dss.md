---
regulation: PCI-DSS
title: Payment Card Industry Data Security Standard
jurisdiction: Global
source: PCI DSS v4.0
---

## Req. 3.2 — Do not store sensitive authentication data after authorization
Sensitive authentication data (full track data, card verification codes, and PINs) must not be stored after authorization, even if encrypted. Retaining CVV or full magnetic stripe data after a transaction is a violation.

## Req. 3.4 — Render PAN unreadable wherever it is stored
The primary account number (PAN) must be rendered unreadable anywhere it is stored, using strong cryptography, truncation, or tokenization. Storing card numbers in plaintext is prohibited.

## Req. 3.3 — Mask PAN when displayed
PAN must be masked when displayed such that only personnel with a legitimate business need can see more than the first six and last four digits. Displaying full card numbers to unauthorized users is a violation.

## Req. 4.1 — Encrypt cardholder data across open networks
Strong cryptography and security protocols must be used to safeguard cardholder data during transmission over open, public networks. Transmitting cardholder data unencrypted over the internet is prohibited.

## Req. 7.1 — Restrict access by business need to know
Access to system components and cardholder data must be limited to only those individuals whose job requires such access. Granting broad or default access to cardholder data violates least-privilege requirements.

## Req. 8.2 — Identify and authenticate access
Each user must be assigned a unique identifier before access to system components or cardholder data is granted, and authentication must be enforced. Shared or generic accounts for accessing cardholder data are prohibited.

## Req. 9.1 — Restrict physical access to cardholder data
Appropriate facility entry controls must be in place to limit and monitor physical access to systems in the cardholder data environment. Unmonitored physical access to card data systems is a violation.

## Req. 10.1 — Log and monitor all access to cardholder data
Audit logs must record all individual access to cardholder data and system components, and logs must be retained for at least one year, with three months immediately available. Missing or short-retained audit trails violate this requirement.
