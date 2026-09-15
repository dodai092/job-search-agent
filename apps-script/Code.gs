/**
 * Append-only Web App bound to the "Job Search Agent - Shortlist" Sheet.
 * Exists because the Drive MCP available to the daily agent has no
 * content-write call for existing files (create_file only makes new files;
 * update_file only changes title/parentId) — see SPEC.md Delivery.
 *
 * Deploy: Extensions > Apps Script > paste this in > Project Settings >
 * Script Properties > add SHARED_SECRET > Deploy > New deployment >
 * Web app > Execute as: Me > Who has access: Anyone. Authorization is via
 * the shared secret in the request body, not Google's access control.
 */

function doPost(e) {
  var props = PropertiesService.getScriptProperties();
  var secret = props.getProperty('SHARED_SECRET');

  var body;
  try {
    body = JSON.parse(e.postData.contents);
  } catch (err) {
    return jsonResponse({ ok: false, error: 'invalid JSON body' });
  }

  if (!secret || body.secret !== secret) {
    return jsonResponse({ ok: false, error: 'unauthorized' });
  }

  if (body.action !== 'append_rows') {
    return jsonResponse({ ok: false, error: 'unknown action: ' + body.action });
  }

  var rows = body.rows;
  if (!Array.isArray(rows) || rows.length === 0) {
    return jsonResponse({ ok: false, error: 'rows must be a non-empty array' });
  }

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  rows.forEach(function (row) {
    sheet.appendRow([
      row.title || '',
      row.company || '',
      row.location || '',
      row.source || '',
      row.link || '',
      row.fit_score != null ? row.fit_score : '',
      row.rationale || '',
      row.date_found || '',
      row.status || ''
    ]);
  });

  return jsonResponse({ ok: true, appended: rows.length });
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}
