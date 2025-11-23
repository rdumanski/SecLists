# FedWatch WhatsApp notifier

This helper script polls the CME FedWatch Tool JSON feed and alerts you over WhatsApp whenever the Ease probability changes.

## Setup
1. Install dependencies (Twilio SDK only):
   ```bash
   pip install twilio
   ```
2. Export the required credentials and WhatsApp numbers (Twilio sandbox or WhatsApp-enabled number):
   ```bash
   export TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   export TWILIO_AUTH_TOKEN=your_auth_token
   export TWILIO_WHATSAPP_FROM=whatsapp:+12345678900
   export TWILIO_WHATSAPP_TO=whatsapp:+10987654321
   ```

## Running the monitor
Run the script directly; it polls every 15 minutes by default and only sends a message when the Ease probability changes (use `--notify-on-start` to send the first value immediately).
```bash
python tools/fedwatch_notifier.py \
  --url https://www.cmegroup.com/CmeWS/mvc/InterestRates/FedWatchToolData \
  --poll-seconds 900 \
  --notify-on-start
```

Use `--run-once` if you only want a single fetch (useful for smoke tests or cron-driven runs).

## How it works
- Fetches JSON from the FedWatch feed with a lightweight urllib client.
- Recursively searches for the first field labeled "ease" and interprets its value as a percentage.
- Sends a WhatsApp message via Twilio when the value differs from the last observed reading.
