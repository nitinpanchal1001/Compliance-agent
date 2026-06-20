---
regulation: PCI-DSS
title: Payment Card Industry Data Security Standard
jurisdiction: Global
source: PCI DSS v4.0.1 (paraphrased; © PCI SSC)
---

## Req. 1.2 — Network security controls configuration
Network security controls must be configured and maintained to restrict traffic between the cardholder data environment and untrusted networks, with a documented configuration standard and ruleset reviews. Flat networks that expose card systems to untrusted traffic violate this requirement.

## Req. 1.3 — Restrict access to and from the cardholder data environment
Inbound and outbound traffic to the cardholder data environment must be restricted to only that which is necessary, and access from untrusted networks must be denied by default. Permitting unnecessary or any-any access into the card environment is a violation.

## Req. 1.4 — Network connections between trusted and untrusted networks are controlled
Connections between trusted and untrusted networks must be controlled, and private IP addresses and routing information for the cardholder data environment must not be disclosed to untrusted networks. Exposing internal card-environment addressing is a violation.

## Req. 2.2 — Secure configuration standards for system components
System components must be configured securely using hardening standards that address known vulnerabilities, with default passwords and unnecessary services removed or disabled before deployment. Deploying systems with vendor default credentials is a violation.

## Req. 2.3 — Secure configuration of wireless environments
Wireless environments connected to or affecting the cardholder data environment must change vendor defaults and use strong encryption for authentication and transmission. Running wireless with default keys or weak encryption is a violation.

## Req. 3.2 — Do not store sensitive authentication data after authorization
Sensitive authentication data — full track data, card verification codes, and PINs/PIN blocks — must not be stored after authorization, even if encrypted. Retaining CVV or full magnetic-stripe data after a transaction is a violation.

## Req. 3.3 — Mask PAN when displayed
The primary account number (PAN) must be masked when displayed so that only personnel with a legitimate business need can see more than the first six and last four digits. Displaying full card numbers to unauthorized users is a violation.

## Req. 3.4 — Render PAN unreadable anywhere it is stored
PAN must be rendered unreadable anywhere it is stored, using strong one-way hashing of the entire PAN, truncation, tokenization, or strong cryptography. Storing card numbers in plaintext is prohibited.

## Req. 3.5 — Protect cryptographic keys used to secure stored account data
Cryptographic keys used to protect stored account data must be protected against disclosure and misuse, with access restricted to the fewest custodians necessary and keys stored securely. Storing encryption keys alongside the data they protect is a violation.

## Req. 4.2 — Protect PAN with strong cryptography during transmission
Strong cryptography and security protocols must safeguard PAN during transmission over open, public networks, and PAN must never be sent unprotected by end-user messaging technologies. Transmitting cardholder data unencrypted over the internet, email, or chat is prohibited.

## Req. 5.2 — Protect systems against malicious software
An anti-malware solution must be deployed on all system components commonly affected by malicious software, kept current, and actively running. Systems in the card environment without active, updated anti-malware are a violation.

## Req. 5.3 — Anti-malware mechanisms are active and monitored
Anti-malware mechanisms must be kept active, perform periodic and on-access scans, generate audit logs, and not be disabled or altered by users unless explicitly authorized. Allowing users to disable endpoint protection is a violation.

## Req. 6.2 — Develop software securely
Bespoke and custom software must be developed securely, based on industry standards and secure coding practices, with review for vulnerabilities before release. Shipping code without secure development and review controls is a violation.

## Req. 6.3 — Identify and address security vulnerabilities
Security vulnerabilities must be identified, risk-ranked, and addressed, and applicable vendor security patches must be installed in a timely manner — critical patches promptly. Leaving known critical vulnerabilities unpatched is a violation.

## Req. 6.4 — Protect public-facing web applications against attacks
Public-facing web applications must be protected against attacks, either through automated technical solutions such as a web application firewall or through regular reviews. Exposing web applications without such protection is a violation.

## Req. 7.2 — Restrict access to system components and cardholder data by need to know
Access to system components and cardholder data must be limited to only the individuals whose jobs require it, based on least privilege and defined roles. Granting broad or default access to cardholder data violates least-privilege requirements.

## Req. 7.3 — Manage access via an access control system
Access must be managed through an access control system that enforces privileges based on job classification and denies access by default. Manual or default-allow access management is a violation.

## Req. 8.2 — Establish and manage user identification
Each user must be assigned a unique identifier before access to system components is granted, and shared, group, or generic accounts must not be used unless specifically managed and justified. Shared or generic accounts for accessing cardholder data are prohibited.

## Req. 8.3 — Establish strong authentication for users and administrators
User authentication must be strong, protecting credentials in storage and transmission and enforcing password or passphrase strength and change requirements. Weak, unprotected, or default credentials violate this requirement.

## Req. 8.4 — Multi-factor authentication
Multi-factor authentication must be implemented for all access into the cardholder data environment and for all remote and administrative access. Single-factor access into the card environment is a violation.

## Req. 9.4 — Restrict physical access to cardholder data
Physical access to systems, media, and facilities in the cardholder data environment must be controlled and monitored, and media containing cardholder data must be secured, inventoried, and destroyed when no longer needed. Unmonitored physical access or improper media disposal is a violation.

## Req. 10.2 — Log all access to system components and cardholder data
Audit logs must be implemented to record all individual access to system components and cardholder data, including privileged actions, access to logs, and authentication events. Missing audit trails for access to card data violate this requirement.

## Req. 10.4 — Review audit logs to identify anomalies
Audit logs must be reviewed — including through automated mechanisms — to identify anomalies or suspicious activity, with critical logs reviewed at least daily. Collecting logs but never reviewing them is a violation.

## Req. 10.5 — Retain audit log history
Audit log history must be retained for at least twelve months, with at least the most recent three months immediately available for analysis. Short or absent log retention violates this requirement.

## Req. 11.3 — Address vulnerabilities through scanning
Internal and external vulnerability scans must be performed regularly and after significant changes, and identified vulnerabilities must be remediated, with external scans by an approved scanning vendor. Skipping required vulnerability scans is a violation.

## Req. 11.4 — Penetration testing
External and internal penetration testing must be performed at least annually and after significant infrastructure or application changes, with exploitable findings corrected and retested. Never performing penetration tests is a violation.

## Req. 12.1 — Establish and maintain an information security policy
A comprehensive information security policy must be established, published, maintained, and disseminated to all relevant personnel, and reviewed at least annually. Operating without a maintained information security policy is a violation.

## Req. 12.6 — Security awareness education
A formal security awareness program must be in place to make personnel aware of the cardholder data security policy and their responsibilities, with training upon hire and at least annually. An untrained workforce handling card data is a compliance gap.

## Req. 12.8 — Manage risk associated with third-party service providers
Risk from third-party service providers with access to cardholder data must be managed through due diligence, written agreements acknowledging their security responsibilities, and monitoring of their compliance status. Using service providers without such agreements is a violation.

## Req. 12.10 — Respond to security incidents
An incident response plan must be implemented and maintained to detect, respond to, and recover from security incidents affecting the cardholder data environment, and tested at least annually. Lacking a tested incident response plan is a violation.
