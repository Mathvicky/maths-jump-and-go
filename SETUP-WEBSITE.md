# Website estimate and lead setup

The existing domain remains `mathsjumpandgo.co.uk`. The implementation is local and has not been deployed.

## Customer flow

1. The initial form asks only for postcode, vehicle type and call-out time.
2. `POST /api/quotes/estimate` accepts a valid UK postcode, converts it into coordinates and a place name, calculates actual driving distance from `HP12 3GH` with Amazon Location (or the existing OSRM fallback), and applies the distance-based price.
3. The backend returns the calculated estimate immediately and sends a minimal lead to Google Apps Script as a background task. The private Sheet receives exactly: postcode, vehicle type, call-out time, estimated price, timestamp and estimate ID. The script emails the same estimate to the configured business address.
4. The customer sees an animated estimate modal containing the price, normalized postcode, location, driving miles, CALL NOW and WhatsApp actions. There is no customer-details form.

Local car prices are £45 up to 5 miles, £55 up to 10 miles and £60 up to 15 miles. Above 15 miles, each 15-mile band costs another £60: over 15 to 30 miles is £120, over 30 to 45 is £180, and the same pattern continues without a cap. The night rate doubles the final distance-band price once.

The estimate ID is generated once in the browser and checked as a UUID by the API. The Google script uses it to avoid duplicate Sheet rows if the same estimate request is retried.

## Public website configuration

Edit `app/config.js`:

- `apiBaseUrl`: the backend HTTPS origin, or `same-origin` if FastAPI serves the site.
- `phone`: the number used by the CALL NOW link.
- `whatsapp`: the WhatsApp number in international digits, such as `447700900000`.
- `vehicleAdjustments.van12v`: adjustment added to the distance price before the night multiplier (default `0`).
- `vehicleAdjustments.vanLarge24v`: adjustment added to the distance price before the night multiplier (default `30`).

Never place the Google webhook secret, AWS credentials, private base postcode or business notification email in this public file.

After editing frontend files, run `python scripts/sync_frontend.py`. It copies the canonical `app/` frontend to `docs/` for GitHub Pages and preserves `docs/CNAME`.

## Google Sheet and email delivery

1. Create a Google Sheet owned by the business account.
2. Create a standalone Google Apps Script project and copy in `google-apps-script/Code.gs` and `appsscript.json`.
3. In **Project Settings → Script properties**, add:
   - `SPREADSHEET_ID`: the ID from the Sheet URL.
   - `BUSINESS_EMAIL`: the recipient of estimate notifications.
   - `WEBHOOK_SECRET`: a long, randomly generated secret used only by the backend and Apps Script.
   - `RETENTION_DAYS`: `30`, or the documented period chosen for the business.
4. Run `setupRetentionTrigger` once and approve the requested Google permissions. This creates the header row and a daily deletion trigger. Confirm the trigger exists before launch.
5. Deploy the script as a web app, executing as the business account. Record the `/exec` URL. Access must permit backend requests; the shared secret rejects unauthorised payloads.
6. Test a staging estimate and verify both the six-column Sheet row and the business email. Also test that a repeated request with the same estimate ID does not create another row.

Google Apps Script email delivery uses the Google account's MailApp quota. Monitor the quota and backend error logs. Lead delivery runs after the estimate response so a slow Google request never delays the customer's price; a process failure during that short background task can lose a lead. Use a durable queue such as Amazon SQS before production if guaranteed delivery is required. The webhook deliberately returns no personal or configuration data and does not log request bodies in application code.

## Backend configuration

Copy `backend/.env.example` to the ignored `backend/.env`, then set:

- `SERVICE_BASE_POSTCODE`: the service origin postcode (`HP12 3GH`).
- `NIGHT_RATE_START_HOUR`: start of the night-rate window in local 24-hour time (default `22`).
- `NIGHT_RATE_END_HOUR`: end of the night-rate window in local 24-hour time (default `7`).
- `VEHICLE_12V_ADJUSTMENT`: flat amount added to a 12V van estimate (default `0`).
- `VEHICLE_24V_ADJUSTMENT`: flat amount added to a 24V van/large-vehicle estimate (default `0`).
- `GOOGLE_LEADS_WEBHOOK_URL`: the deployed Apps Script `/exec` URL.
- `GOOGLE_LEADS_WEBHOOK_SECRET`: the same secret as the script property.
- `ALLOWED_ORIGINS`: the exact live website origins.

The ECS task definition exposes matching parameters. Secrets are marked `NoEcho`, but production should resolve them from AWS Secrets Manager rather than storing them in deployment history.

## UK GDPR launch checklist

- Verify the Sheet is private to the people who handle enquiries and enable account MFA.
- Select and document the lawful basis. A quote request will normally use steps requested before entering a contract; obtain professional advice for the business's circumstances.
- Complete the privacy text with the business/controller identity, contact route, lawful basis, recipients, retention period, individual rights and ICO complaint route before going live.
- Set mailbox retention for notification emails. The script deletes Sheet rows after the configured period but cannot delete messages from the business mailbox.
- Sign or review applicable Google and AWS processor terms and international-transfer safeguards.
- Do not add analytics, advertising identifiers, full addresses or other fields to the initial estimate without reviewing necessity and updating the notice.
- Establish a process for access/deletion requests using the estimate ID and postcode.

## Verification

Run:

```text
python -m pytest backend/tests -q
node --test tests/frontend.test.cjs
```

For a local preview:

```text
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

Open `http://127.0.0.1:8001/website`. Without the private Google and AWS settings, the page loads but the estimate button correctly reports that online estimates are unavailable.

Before publishing, finish the HTTPS API/load-balancer configuration, restrict the ECS task security group to the load balancer, add request rate limiting, test all price bands on mobile, and confirm real Sheet and email delivery in staging.
