---
name: finance-products
description: Troubleshoot financial products including payment terminals, card readers, POS systems, and banking apps
---

# Skill: Financial Products Support

**Description:** This skill provides troubleshooting guidance for financial hardware devices and banking applications. Use this skill whenever a user asks about payment terminals, card readers, POS systems, or banking app issues.

## When to Use This Skill

Activate this skill when the user's query relates to:
- Hardware devices used for payment processing (terminals, card readers, POS systems)
- Banking or finance application issues (login, transactions, syncing)
- Error codes from any of the products listed below
- Security questions about payment processing or PCI compliance

## How to Use This Skill

1. Identify which product category the user is asking about.
2. Match their issue to the relevant troubleshooting section.
3. Walk them through the numbered steps in order. Do not skip steps.
4. If an error code is mentioned, reference the error code table for that product.
5. Always close the interaction with the relevant security reminder from the Security Best Practices section.

---

## SECURITY REMINDER

Before providing any troubleshooting guidance, remind the user:

> We will never ask you for your PIN, full card number, CVV, or login password. Do not share these with anyone, including support staff. If you are on a call and someone requests this information, end the call immediately.

---

## Product 1: Payment Terminals

### Common Issues and Troubleshooting

**Connection Refused Errors (ERR-PT-001)**

1. Verify the terminal is powered on and the network cable is securely connected (or Wi-Fi is enabled).
2. Restart the terminal by holding the power button for 10 seconds, then powering back on.
3. Check that the terminal's IP configuration matches your network settings (DHCP or static).
4. Confirm your firewall or router is not blocking the terminal's outbound port (typically 443 or 8443).
5. If the issue persists, perform a network diagnostic from the terminal menu: Settings > Network > Diagnostics.

**Timeout Errors (ERR-PT-002)**

1. Check your internet connection speed; payment terminals require a minimum of 1 Mbps upload.
2. Reduce network congestion by disconnecting unnecessary devices from the same network.
3. Switch from Wi-Fi to a wired Ethernet connection if available.
4. Contact your payment processor to confirm there are no server-side outages.

**Chip Reader Failures (ERR-PT-003)**

1. Inspect the chip slot for debris or damage; clean gently with compressed air.
2. Ask the customer to reinsert the card slowly and firmly until the terminal acknowledges it.
3. Try a different chip card to determine if the issue is with the card or the reader.
4. Restart the terminal and retry the transaction.
5. If the chip reader is unresponsive after restart, escalate for hardware replacement.

**Contactless Not Working (ERR-PT-004)**

1. Confirm contactless payments are enabled in the terminal settings: Settings > Payment Methods > NFC.
2. Ensure the customer is holding their card or device within 4 cm of the reader.
3. Restart the NFC module from the terminal menu.
4. Test with a different contactless card or mobile wallet to isolate the issue.

**Printer Issues (ERR-PT-005)**

1. Open the printer compartment and verify the paper roll is loaded correctly (thermal side facing out).
2. Check for paper jams and clear any obstructions.
3. Run a test print from the terminal menu: Settings > Printer > Test Print.
4. If the printout is blank, replace the thermal paper roll with a new one.

---

## Product 2: Card Readers

### Common Issues and Troubleshooting

**Bluetooth Pairing (ERR-CR-001)**

1. Ensure the card reader is in pairing mode (hold the Bluetooth button for 3 seconds until the LED flashes blue).
2. On your device, go to Bluetooth settings and remove any previous pairings for the reader.
3. Search for new devices and select the card reader model from the list.
4. Enter the pairing code displayed on the reader screen (default: 0000 if none is shown).
5. Confirm the connection is established by processing a test transaction.

**Firmware Updates (ERR-CR-002)**

1. Connect the card reader to a stable Wi-Fi network or pair it with a device that has internet access.
2. Open the reader management app and navigate to Settings > Firmware > Check for Updates.
3. If an update is available, ensure the battery is above 50% before proceeding.
4. Do not power off or disconnect the reader during the update process.

**Battery Issues (ERR-CR-003)**

1. Charge the reader for at least 2 hours using the supplied cable and adapter.
2. Check the charging port for lint or debris that may prevent proper contact.
3. If the reader does not power on after charging, perform a hard reset by holding power and volume-down for 15 seconds.
4. Replace the battery if the device is older than 18 months and holds less than 2 hours of charge.

**Magnetic Stripe vs Chip vs Tap**

1. Always prefer chip or contactless (tap) over magnetic stripe for improved security.
2. If chip fails after two attempts, the terminal may prompt for a magnetic stripe fallback; follow the on-screen instructions.
3. For tap payments, ensure the transaction amount is below your contactless limit (typically $250).

---

## Product 3: POS Systems

### Common Issues and Troubleshooting

**Transaction Reconciliation (ERR-POS-001)**

1. Run the reconciliation report from Reports > Daily Reconciliation in the POS menu.
2. Compare the POS totals against your payment processor's dashboard figures.
3. Identify discrepancies by filtering transactions by payment method (cash, card, mobile).
4. For missing transactions, check the "Pending" queue; network interruptions can delay settlement.
5. Export the report as CSV for your records and escalate unresolved variances to your processor.

**End-of-Day Settlement (ERR-POS-002)**

1. Initiate settlement from the POS menu: Transactions > Batch Settlement > Settle Now.
2. Ensure all pending transactions have been completed or voided before settling.
3. Wait for the settlement confirmation receipt; do not power off the system during this process.
4. If settlement fails, verify your internet connection and retry after 5 minutes.

**Voiding and Refunding Transactions (ERR-POS-003)**

1. To void: locate the transaction in the current batch under Transactions > Today, select it, and choose "Void."
2. Voids are only available before the batch is settled; after settlement, use a refund instead.
3. To refund: go to Transactions > Search, find the original transaction, and select "Refund."
4. Enter the refund amount (full or partial) and confirm with a manager authorization code.
5. Provide the customer with a refund receipt showing the expected processing time (3-5 business days).

**Receipt Printing (ERR-POS-004)**

1. Verify the printer is online and connected to the POS system (check the status indicator light).
2. Open the printer cover and reload paper if the roll is empty or low.
3. Print a test page from Settings > Printer > Test Print.
4. If the printer is network-connected, confirm it is on the same subnet as the POS terminal.

---

## Product 4: Banking Apps

### Common Issues and Troubleshooting

**Login Issues - 2FA and Biometric (ERR-APP-001)**

1. Confirm the app is updated to the latest version from your device's app store.
2. For 2FA failures, check that your device clock is set to automatic; time drift causes code mismatches.
3. If biometric login fails, remove and re-enroll your fingerprint or face ID in your device settings.
4. Clear the app cache: Device Settings > Apps > [Banking App] > Clear Cache.
5. If locked out, use the "Forgot Password" flow and verify identity through the registered email or phone.

**Transaction Failures (ERR-APP-002)**

1. Check your account balance and daily transaction limits before retrying.
2. Verify the recipient details (account number, routing number) are correct.
3. Ensure you have a stable internet connection; switch between Wi-Fi and mobile data to test.
4. If the error mentions "declined," contact your bank to check for fraud holds on your account.

**Account Sync Delays (ERR-APP-003)**

1. Pull down to refresh the account overview screen.
2. Log out and log back in to force a full sync with the server.
3. Check the app's status page or social media channels for known outages.
4. If transactions are missing for more than 24 hours, contact support with the transaction reference number.

**Notification Setup (ERR-APP-004)**

1. Open the banking app and go to Settings > Notifications > Manage Alerts.
2. Enable the desired alert types: transaction alerts, balance thresholds, login notifications.
3. Ensure your device allows notifications from the app: Device Settings > Notifications > [Banking App] > Allow.
4. For SMS alerts, verify your phone number is correct and that you have not blocked the bank's short code.

---

## Security Best Practices

This section must be referenced at the end of every support interaction regardless of product category.

### PCI Compliance Basics

- Never store full card numbers, CVVs, or PINs on any device, paper, or system.
- Ensure all payment data is transmitted over encrypted connections (TLS 1.2 or higher).
- Limit access to payment systems to authorized personnel only.

### Never Share Credentials

- Do not share login passwords, API keys, or merchant IDs with anyone outside your organization.
- Rotate passwords every 90 days and use a password manager.
- Enable multi-factor authentication on all payment and banking accounts.

### Secure Network Requirements

- Payment devices must operate on a dedicated, segmented network separate from guest Wi-Fi.
- Use WPA3 encryption for wireless connections wherever supported.
- Disable remote access to payment terminals unless required, and use VPN when enabled.

### Regular Firmware Updates

- Check for firmware updates on all payment hardware at least once per month.
- Subscribe to your device manufacturer's security bulletin mailing list.
- Apply critical security patches within 48 hours of release.
- Document all firmware versions and update dates for audit purposes.
