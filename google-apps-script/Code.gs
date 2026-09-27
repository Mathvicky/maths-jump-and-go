const LEAD_HEADERS = [
  "postcode",
  "vehicle_type",
  "callout_time",
  "estimated_price",
  "timestamp",
  "estimate_id",
];

function jsonResponse(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

function requireProperty(name) {
  const value = PropertiesService.getScriptProperties().getProperty(name);
  if (!value) throw new Error(`Missing script property: ${name}`);
  return value;
}

function doPost(event) {
  try {
    const payload = JSON.parse(event.postData.contents);
    if (payload.secret !== requireProperty("WEBHOOK_SECRET")) {
      return jsonResponse({ ok: false, error: "unauthorised" });
    }
    if (payload.lead) return recordEstimate(payload.lead);
    return jsonResponse({ ok: false, error: "unsupported request" });
  } catch (error) {
    return jsonResponse({ ok: false, error: "request failed" });
  }
}

function recordEstimate(lead) {
  validateExactKeys(lead, LEAD_HEADERS);
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const sheet = getLeadSheet();
    if (!estimateExists(sheet, lead.estimate_id)) {
      MailApp.sendEmail({
        to: requireProperty("BUSINESS_EMAIL"),
        subject: `New website estimate ${lead.estimate_id}`,
        body: [
          "A customer requested an estimate.",
          `Postcode: ${lead.postcode}`,
          `Vehicle: ${lead.vehicle_type}`,
          `Call-out time: ${lead.callout_time}`,
          `Estimated price: ${lead.estimated_price === null ? "Manual quote" : "£" + lead.estimated_price}`,
          `Timestamp: ${lead.timestamp}`,
          `Estimate ID: ${lead.estimate_id}`,
        ].join("\n"),
      });
      sheet.appendRow(LEAD_HEADERS.map((key) => lead[key] === null ? "" : lead[key]));
    }
    return jsonResponse({ ok: true });
  } finally {
    lock.releaseLock();
  }
}

function validateExactKeys(value, allowed) {
  const keys = Object.keys(value).sort();
  const expected = allowed.slice().sort();
  if (JSON.stringify(keys) !== JSON.stringify(expected)) {
    throw new Error("Unexpected data fields");
  }
  if (!/^[0-9a-f-]{36}$/i.test(value.estimate_id)) throw new Error("Invalid estimate ID");
}

function getLeadSheet() {
  const spreadsheet = SpreadsheetApp.openById(requireProperty("SPREADSHEET_ID"));
  let sheet = spreadsheet.getSheetByName("Estimate leads");
  if (!sheet) sheet = spreadsheet.insertSheet("Estimate leads");
  if (sheet.getLastRow() === 0) sheet.appendRow(LEAD_HEADERS);
  return sheet;
}

function estimateExists(sheet, estimateId) {
  const rowCount = sheet.getLastRow();
  if (rowCount < 2) return false;
  return sheet.getRange(2, 6, rowCount - 1, 1)
    .getValues()
    .some((row) => row[0] === estimateId);
}

function deleteExpiredLeads() {
  const retentionDays = Number(requireProperty("RETENTION_DAYS"));
  const cutoff = Date.now() - retentionDays * 24 * 60 * 60 * 1000;
  const sheet = getLeadSheet();
  for (let row = sheet.getLastRow(); row >= 2; row -= 1) {
    const timestamp = new Date(sheet.getRange(row, 5).getValue()).getTime();
    if (Number.isFinite(timestamp) && timestamp < cutoff) sheet.deleteRow(row);
  }
}

function setupRetentionTrigger() {
  ScriptApp.getProjectTriggers()
    .filter((trigger) => trigger.getHandlerFunction() === "deleteExpiredLeads")
    .forEach((trigger) => ScriptApp.deleteTrigger(trigger));
  ScriptApp.newTrigger("deleteExpiredLeads").timeBased().everyDays(1).create();
  getLeadSheet();
}
