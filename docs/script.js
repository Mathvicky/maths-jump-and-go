"use strict";

const config = window.SITE_CONFIG || {};
const estimateForm = document.querySelector("#estimate-form");
const estimateFields = document.querySelector("#estimate-fields");
const estimateButton = document.querySelector("#estimate-button");
const estimateModal = document.querySelector("#estimate-modal");
const estimatePrice = document.querySelector("#estimated-price");
const estimateTitle = document.querySelector("#estimate-title");
const estimateRateNotice = document.querySelector("#estimate-rate-notice");
const estimateVehicle = document.querySelector("#estimate-vehicle");
const estimateCompatibility = document.querySelector("#estimate-compatibility");
const estimateMessage = document.querySelector("#estimate-message");
const estimateLocation = document.querySelector("#estimate-location");
const estimateDistance = document.querySelector("#estimate-distance");
const estimateReference = document.querySelector("#estimate-reference");
const estimateClose = document.querySelector("#estimate-close");
const formMessage = document.querySelector("#form-message");
const callButton = document.querySelector("#call-now");
const whatsappButton = document.querySelector("#whatsapp-now");
const heroCallButton = document.querySelector("#hero-call-now");
const heroWhatsappButton = document.querySelector("#hero-whatsapp-now");
const get = (id) => document.getElementById(id);
const fallbackOrigin = Object.freeze({ latitude: 51.636098, longitude: -0.778677 });
const metresPerMile = 1609.344;
const normalisePostcodeForComparison = (postcode) => String(postcode || "")
  .trim()
  .toUpperCase()
  .replace(/[^A-Z0-9]/g, "");
const vehicleLabels = Object.freeze({
  car: "Car",
  suv_4x4: "SUV / 4x4",
  van_12v: "Van - 12V",
  van_large_24v: "Van / Large Vehicle - 24V",
  other_specialist: "Other / Specialist Vehicle",
});
const configuredAdjustments = config.vehicleAdjustments || {};
const vehicleAdjustments = Object.freeze({
  van_12v: Math.max(0, Number(configuredAdjustments.van12v) || 0),
  van_large_24v: Math.max(0, Number(configuredAdjustments.vanLarge24v) || 0),
});

const revealItems = document.querySelectorAll
  ? Array.from(document.querySelectorAll("[data-reveal]"))
  : [];
const reduceMotion = typeof matchMedia === "function"
  && matchMedia("(prefers-reduced-motion: reduce)").matches;

if (revealItems.length && typeof IntersectionObserver === "function" && !reduceMotion) {
  document.documentElement.classList.add("reveal-ready");
  const revealObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add("is-visible");
      revealObserver.unobserve(entry.target);
    }
  }, { threshold: 0.14, rootMargin: "0px 0px -6%" });
  revealItems.forEach((item) => revealObserver.observe(item));
}

let apiBase = config.apiBaseUrl === "same-origin" ? location.origin : config.apiBaseUrl;
if (!apiBase && ["localhost", "127.0.0.1"].includes(location.hostname)) apiBase = location.origin;
if (apiBase) {
  try {
    const url = new URL(apiBase);
    const isLocal = url.protocol === "http:" && ["localhost", "127.0.0.1"].includes(url.hostname);
    if (url.protocol !== "https:" && !isLocal) throw new Error("Unsafe API URL");
    apiBase = url.href.replace(/\/$/, "");
  } catch {
    apiBase = "";
  }
}

const phone = (config.phone || "").trim();
const whatsapp = (config.whatsapp || "").replace(/\D/g, "");
if (phone) {
  const phoneHref = `tel:${phone.replace(/[^+0-9]/g, "")}`;
  for (const button of [callButton, heroCallButton]) {
    button.href = phoneHref;
    button.hidden = false;
  }
}
if (whatsapp) {
  const whatsappHref = `https://wa.me/${whatsapp}`;
  for (const button of [whatsappButton, heroWhatsappButton]) {
    button.href = whatsappHref;
    button.hidden = false;
  }
}
get("contact-setup-note").hidden = Boolean(phone || whatsapp);

estimateFields.disabled = false;
if (!apiBase) {
  get("estimate-data-note").firstChild.textContent = "Your details are processed only to calculate this estimate and are not saved by the website. ";
  get("quote-data-use").textContent = "When you select Get Instant Estimate, your postcode, vehicle type and call-out time are processed only to calculate and display the price. The website does not save or email these details. To request a call-out, contact us by phone or WhatsApp.";
}

let estimateId = crypto.randomUUID();
let busy = false;

function quoteDetails() {
  return {
    postcode: get("postcode").value.trim().toUpperCase(),
    vehicle_type: get("vehicle-type").value,
    callout_time: get("callout-time").value,
    estimate_id: estimateId,
  };
}

async function post(path, payload) {
  if (!apiBase) return estimateInBrowser(payload);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${apiBase}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(typeof data.detail === "string" ? data.detail : "Please check your details and try again.");
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError" || error instanceof TypeError) {
      throw new Error("Connection interrupted. Please call or WhatsApp us for urgent help.");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function isNightTime(calloutTime) {
  const [hour, minute] = calloutTime.split(":").map(Number);
  const time = hour * 60 + minute;
  return time >= 22 * 60 || time < 7 * 60;
}

function calculateBrowserPrice(drivingMiles, nightRate, vehicleType) {
  let price;
  if (drivingMiles <= 5) price = 45;
  else if (drivingMiles <= 10) price = 55;
  else if (drivingMiles <= 15) price = 60;
  else price = Math.ceil(drivingMiles / 15) * 60;
  const vehiclePrice = price + (vehicleAdjustments[vehicleType] || 0);
  return nightRate ? vehiclePrice * 2 : vehiclePrice;
}

async function getJson(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) throw new Error("The route service is temporarily unavailable.");
    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
}

async function estimateInBrowser(payload) {
  const basePostcode = String(config.serviceBasePostcode || "").trim().toUpperCase();
  const isBasePostcode = Boolean(basePostcode)
    && normalisePostcodeForComparison(payload.postcode)
      === normalisePostcodeForComparison(basePostcode);
  if (isBasePostcode) {
    const drivingMiles = 0;
    const nightRate = isNightTime(payload.callout_time);
    let pricingStatus = "estimated";
    let estimatedPrice = calculateBrowserPrice(drivingMiles, nightRate, payload.vehicle_type);
    let estimateLabel = "Your estimate is ready";
    let message = "Estimated price only. Final price, vehicle compatibility and availability will be confirmed before dispatch.";
    if (payload.vehicle_type === "other_specialist") {
      pricingStatus = "manual_quote";
      estimatedPrice = null;
      estimateLabel = "Manual quote required";
      message = "Other or specialist vehicles require a manual quote. Call or WhatsApp us now.";
    }
    return {
      pricing_status: pricingStatus,
      estimated_price: estimatedPrice,
      currency: "GBP",
      message,
      estimate_label: estimateLabel,
      rate_notice: pricingStatus === "estimated" && nightRate ? "Night call-out rate applies." : null,
      estimate_id: payload.estimate_id,
      postcode: basePostcode,
      location: basePostcode,
      driving_miles: drivingMiles,
    };
  }

  const postcodeData = await getJson(
    `https://api.postcodes.io/postcodes/${encodeURIComponent(payload.postcode)}`,
  );
  if (!postcodeData.result) throw new Error("Postcode could not be found.");

  const destination = postcodeData.result;
  const coordinates = [
    `${fallbackOrigin.longitude},${fallbackOrigin.latitude}`,
    `${destination.longitude},${destination.latitude}`,
  ].join(";");
  const routeData = await getJson(
    `https://router.project-osrm.org/route/v1/driving/${coordinates}?overview=false&alternatives=false&steps=false`,
  );
  if (routeData.code !== "Ok" || !routeData.routes?.[0]?.distance) {
    throw new Error("A driving route could not be calculated for this postcode.");
  }

  const drivingMiles = routeData.routes[0].distance / metresPerMile;
  const nightRate = isNightTime(payload.callout_time);
  const outOfArea = drivingMiles > 15;
  const placeParts = [destination.parish, destination.admin_district, destination.region]
    .filter((value, index, values) => value
      && !value.toLowerCase().includes("unparished")
      && values.indexOf(value) === index);

  let pricingStatus = "estimated";
  let estimatedPrice = calculateBrowserPrice(drivingMiles, nightRate, payload.vehicle_type);
  let estimateLabel = outOfArea ? "Out-of-area estimate" : "Your estimate is ready";
  let message = "Estimated price only. Final price, vehicle compatibility and availability will be confirmed before dispatch.";
  if (payload.vehicle_type === "other_specialist") {
    pricingStatus = "manual_quote";
    estimatedPrice = null;
    estimateLabel = "Manual quote required";
    message = "Other or specialist vehicles require a manual quote. Call or WhatsApp us now.";
  }

  let rateNotice = null;
  if (pricingStatus === "estimated") {
    if (nightRate && outOfArea) rateNotice = "Night/out-of-area rate applies.";
    else if (nightRate) rateNotice = "Night call-out rate applies.";
    else if (outOfArea) rateNotice = "Out-of-area rate applies.";
  }

  return {
    pricing_status: pricingStatus,
    estimated_price: estimatedPrice,
    currency: "GBP",
    message,
    estimate_label: estimateLabel,
    rate_notice: rateNotice,
    estimate_id: payload.estimate_id,
    postcode: destination.postcode,
    location: placeParts.join(", ") || destination.postcode,
    driving_miles: drivingMiles,
  };
}

for (const id of ["postcode", "vehicle-type", "callout-time"]) {
  get(id).addEventListener("input", () => {
    estimateId = crypto.randomUUID();
    if (estimateModal.open) estimateModal.close();
    formMessage.textContent = "";
  });
}

estimateClose.addEventListener("click", () => estimateModal.close());
estimateModal.addEventListener("click", (event) => {
  if (event.target === estimateModal) estimateModal.close();
});

estimateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || !estimateForm.reportValidity()) return;
  busy = true;
  estimateButton.disabled = true;
  estimateButton.textContent = "Getting estimate…";
  formMessage.textContent = "Calculating your route securely…";
  if (estimateModal.open) estimateModal.close();
  try {
    const details = quoteDetails();
    const result = await post("/api/quotes/estimate", details);
    estimatePrice.textContent = result.pricing_status === "estimated"
      ? new Intl.NumberFormat("en-GB", {
          style: "currency",
          currency: result.currency,
          maximumFractionDigits: 0,
        }).format(result.estimated_price)
      : "Contact us for a price";
    estimateMessage.textContent = result.message;
    estimateTitle.textContent = result.estimate_label;
    estimateRateNotice.textContent = result.rate_notice || "";
    estimateRateNotice.hidden = !result.rate_notice;
    estimateVehicle.textContent = `Vehicle: ${vehicleLabels[details.vehicle_type] || details.vehicle_type}`;
    estimateCompatibility.hidden = details.vehicle_type !== "van_large_24v";
    estimateLocation.textContent = result.location === result.postcode
      ? result.postcode
      : `${result.postcode} — ${result.location}`;
    estimateDistance.textContent = `Driving distance: ${result.driving_miles.toFixed(1)} miles`;
    estimateReference.textContent = `Estimate reference: ${result.estimate_id}`;
    formMessage.textContent = "Your estimate is ready.";
    estimateModal.showModal();
  } catch (error) {
    formMessage.textContent = error.message;
  } finally {
    estimateButton.disabled = false;
    estimateButton.textContent = "GET INSTANT ESTIMATE";
    busy = false;
  }
});
