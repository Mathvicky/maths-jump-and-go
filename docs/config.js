// Public website settings.
// Never put AWS credentials or secrets in this file.
window.SITE_CONFIG = Object.freeze({
  apiBaseUrl: "", // HTTPS backend URL, or "same-origin" when served by FastAPI.
  serviceBasePostcode: "HP12 3GH",
  phone: "+447508779214",
  whatsapp: "447508779214",
  vehicleAdjustments: Object.freeze({
    van12v: 0,
    vanLarge24v: 30,
  }),
});
