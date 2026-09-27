"use strict";

const config = window.SITE_CONFIG || {};
const estimateForm = document.querySelector("#estimate-form");
const estimateFields = document.querySelector("#estimate-fields");
const estimateButton = document.querySelector("#estimate-button");
const estimateModal = document.querySelector("#estimate-modal");
const estimatePrice = document.querySelector("#estimated-price");
const estimateTitle = document.querySelector("#estimate-title");
const estimateRateNotice = document.querySelector("#estimate-rate-notice");
const estimateMessage = document.querySelector("#estimate-message");
const estimateLocation = document.querySelector("#estimate-location");
const estimateDistance = document.querySelector("#estimate-distance");
const estimateReference = document.querySelector("#estimate-reference");
const estimateClose = document.querySelector("#estimate-close");
const formMessage = document.querySelector("#form-message");
const callButton = document.querySelector("#call-now");
const whatsappButton = document.querySelector("#whatsapp-now");
const get = (id) => document.getElementById(id);

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
  callButton.href = `tel:${phone.replace(/[^+0-9]/g, "")}`;
  callButton.hidden = false;
}
if (whatsapp) {
  whatsappButton.href = `https://wa.me/${whatsapp}`;
  whatsappButton.hidden = false;
}
get("contact-setup-note").hidden = Boolean(phone || whatsapp);

estimateFields.disabled = !apiBase;
if (!apiBase) formMessage.textContent = "Online estimates are not available yet. Please call or WhatsApp us.";

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
  if (!apiBase || busy || !estimateForm.reportValidity()) return;
  busy = true;
  estimateButton.disabled = true;
  estimateButton.textContent = "Getting estimate…";
  formMessage.textContent = "Calculating your route securely…";
  if (estimateModal.open) estimateModal.close();
  try {
    const result = await post("/api/quotes/estimate", quoteDetails());
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
