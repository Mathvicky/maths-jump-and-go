const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function setup(api = "https://api.example.test") {
  const ids = [
    "estimate-form", "estimate-fields", "estimate-button", "estimate-modal",
    "estimated-price", "estimate-message", "estimate-location", "estimate-distance",
    "estimate-title", "estimate-rate-notice", "estimate-vehicle", "estimate-compatibility", "estimate-reference", "estimate-close", "form-message", "call-now", "whatsapp-now",
    "contact-setup-note", "estimate-data-note", "quote-data-use", "postcode", "vehicle-type", "callout-time",
  ];
  const nodes = Object.fromEntries(ids.map((id) => [id, {
    value: "", checked: true, hidden: true, disabled: false, open: false, textContent: "",
    handlers: {},
    firstChild: { textContent: "" },
    addEventListener(name, fn) { this.handlers[name] = fn; },
    reportValidity() { return true; },
    scrollIntoView() {}, focus() {}, reset() {},
    showModal() { this.open = true; },
    close() { this.open = false; },
  }]));
  const calls = [];
  let estimateResponse = {
    pricing_status: "estimated", estimated_price: 55, currency: "GBP",
    message: "Final price is confirmed before dispatch.",
    estimate_label: "Your estimate is ready", rate_notice: null,
    estimate_id: "82c77659-19e0-4b81-81ef-eed4a84c61b1",
    postcode: "HP11 2AA", location: "High Wycombe, Buckinghamshire",
    driving_miles: 6.4, base_postcode: "HP12 3GH",
  };
  const context = {
    window: { SITE_CONFIG: {
      apiBaseUrl: api, phone: "01494 000000", whatsapp: "447700900000",
      serviceBasePostcode: "HP12 3GH",
      vehicleAdjustments: { van12v: 0, vanLarge24v: 30 },
    } },
    location: { origin: "https://example.test", hostname: "example.test" },
    document: {
      querySelector: (selector) => nodes[selector.slice(1)],
      getElementById: (id) => nodes[id],
    },
    URL, Intl, AbortController, setTimeout, clearTimeout, Error, TypeError,
    crypto: { randomUUID: () => "82c77659-19e0-4b81-81ef-eed4a84c61b1" },
    fetch: async (url, options = {}) => {
      calls.push({ url, body: options.body ? JSON.parse(options.body) : null });
      if (url.startsWith("https://api.postcodes.io/")) return {
        ok: true,
        json: async () => ({ result: {
          postcode: "HP11 2AA", latitude: 51.6, longitude: -0.7,
          parish: "Chepping Wycombe", admin_district: "Buckinghamshire", region: "South East",
        } }),
      };
      if (url.startsWith("https://router.project-osrm.org/")) return {
        ok: true,
        json: async () => ({ code: "Ok", routes: [{ distance: 10300 }] }),
      };
      return { ok: true, json: async () => estimateResponse };
    },
  };
  vm.runInNewContext(fs.readFileSync("app/script.js", "utf8"), context);
  return { nodes, calls, respond: (value) => { estimateResponse = value; } };
}

test("unconfigured site calculates an estimate in the browser", async () => {
  const { nodes, calls } = setup("");
  nodes.postcode.value = "HP11 2AA";
  nodes["vehicle-type"].value = "car";
  nodes["callout-time"].value = "12:00";
  assert.equal(nodes["estimate-fields"].disabled, false);
  await nodes["estimate-form"].handlers.submit({ preventDefault() {} });
  assert.equal(calls.length, 2);
  assert.match(nodes["estimated-price"].textContent, /£55/);
  assert.equal(nodes["estimate-modal"].open, true);
  assert.match(nodes["estimate-data-note"].firstChild.textContent, /not saved/);
});

test("base postcode returns a zero-mile estimate without external calls", async () => {
  const { nodes, calls } = setup("");
  nodes.postcode.value = " hp12-3gh ";
  nodes["vehicle-type"].value = "car";
  nodes["callout-time"].value = "12:00";
  await nodes["estimate-form"].handlers.submit({ preventDefault() {} });
  assert.equal(calls.length, 0);
  assert.equal(nodes["estimate-distance"].textContent, "Driving distance: 0.0 miles");
  assert.match(nodes["estimated-price"].textContent, /£45/);
  assert.equal(nodes["estimate-modal"].open, true);
});

test("browser estimates include 12V and 24V adjustments", async () => {
  const twelveVolt = setup("");
  twelveVolt.nodes.postcode.value = "HP11 2AA";
  twelveVolt.nodes["vehicle-type"].value = "van_12v";
  twelveVolt.nodes["callout-time"].value = "12:00";
  await twelveVolt.nodes["estimate-form"].handlers.submit({ preventDefault() {} });
  assert.match(twelveVolt.nodes["estimated-price"].textContent, /£55/);
  assert.equal(twelveVolt.nodes["estimate-vehicle"].textContent, "Vehicle: Van - 12V");
  assert.equal(twelveVolt.nodes["estimate-compatibility"].hidden, true);

  const twentyFourVolt = setup("");
  twentyFourVolt.nodes.postcode.value = "HP11 2AA";
  twentyFourVolt.nodes["vehicle-type"].value = "van_large_24v";
  twentyFourVolt.nodes["callout-time"].value = "12:00";
  await twentyFourVolt.nodes["estimate-form"].handlers.submit({ preventDefault() {} });
  assert.match(twentyFourVolt.nodes["estimated-price"].textContent, /£85/);
  assert.equal(twentyFourVolt.nodes["estimate-vehicle"].textContent, "Vehicle: Van / Large Vehicle - 24V");
  assert.equal(twentyFourVolt.nodes["estimate-compatibility"].hidden, false);

  const twentyFourVoltNight = setup("");
  twentyFourVoltNight.nodes.postcode.value = "HP11 2AA";
  twentyFourVoltNight.nodes["vehicle-type"].value = "van_large_24v";
  twentyFourVoltNight.nodes["callout-time"].value = "23:00";
  await twentyFourVoltNight.nodes["estimate-form"].handlers.submit({ preventDefault() {} });
  assert.match(twentyFourVoltNight.nodes["estimated-price"].textContent, /£170/);
  assert.equal(twentyFourVoltNight.nodes["estimate-rate-notice"].textContent, "Night call-out rate applies.");
});

test("Get Instant Estimate sends only the four calculation inputs", async () => {
  const { nodes, calls } = setup();
  nodes.postcode.value = " hp11 2aa ";
  nodes["vehicle-type"].value = "car";
  nodes["callout-time"].value = "23:00";
  await nodes["estimate-form"].handlers.submit({ preventDefault() {} });
  assert.deepEqual(calls[0].body, {
    postcode: "HP11 2AA",
    vehicle_type: "car",
    callout_time: "23:00",
    estimate_id: "82c77659-19e0-4b81-81ef-eed4a84c61b1",
  });
  assert.match(nodes["estimated-price"].textContent, /£55/);
  assert.equal(nodes["estimate-modal"].open, true);
  assert.equal(nodes["estimate-vehicle"].textContent, "Vehicle: Car");
  assert.equal(nodes["estimate-location"].textContent, "HP11 2AA — High Wycombe, Buckinghamshire");
  assert.equal(nodes["estimate-distance"].textContent, "Driving distance: 6.4 miles");
  assert.equal(nodes["call-now"].href, "tel:01494000000");
  assert.equal(nodes["whatsapp-now"].href, "https://wa.me/447700900000");
  assert.equal(nodes["call-now"].hidden, false);
  assert.equal(nodes["whatsapp-now"].hidden, false);
});

test("rate labels are shown clearly", async () => {
  const { nodes, respond } = setup();
  respond({
    pricing_status: "estimated", estimated_price: 360, currency: "GBP",
    message: "Estimated call-out price.", estimate_label: "Out-of-area estimate",
    rate_notice: "Night/out-of-area rate applies.",
    estimate_id: "82c77659-19e0-4b81-81ef-eed4a84c61b1",
    postcode: "SW1A 1AA", location: "Westminster, London",
    driving_miles: 34.5, base_postcode: "HP12 3GH",
  });
  await nodes["estimate-form"].handlers.submit({ preventDefault() {} });
  assert.equal(nodes["estimate-title"].textContent, "Out-of-area estimate");
  assert.equal(nodes["estimate-rate-notice"].textContent, "Night/out-of-area rate applies.");
  assert.equal(nodes["estimate-rate-notice"].hidden, false);
  assert.match(nodes["estimated-price"].textContent, /£360/);
  assert.equal(nodes["estimate-distance"].textContent, "Driving distance: 34.5 miles");
});

test("changing an estimate input hides the old result", async () => {
  const { nodes } = setup();
  await nodes["estimate-form"].handlers.submit({ preventDefault() {} });
  nodes.postcode.handlers.input();
  assert.equal(nodes["estimate-modal"].open, false);
});

test("close button dismisses the price modal", async () => {
  const { nodes } = setup();
  await nodes["estimate-form"].handlers.submit({ preventDefault() {} });
  nodes["estimate-close"].handlers.click();
  assert.equal(nodes["estimate-modal"].open, false);
});

test("GitHub Pages files match canonical source and domain is preserved", () => {
  for (const name of ["index.html", "styles.css", "script.js", "config.js"]) {
    assert.equal(fs.readFileSync(`app/${name}`, "utf8"), fs.readFileSync(`docs/${name}`, "utf8"));
  }
  assert.equal(fs.readFileSync("docs/CNAME", "utf8").trim(), "mathsjumpandgo.co.uk");
});
