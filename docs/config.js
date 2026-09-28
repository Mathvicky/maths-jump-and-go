// Public website settings. Add your business details here later.
// Never put AWS credentials, private base postcodes or secrets in this file.
window.SITE_CONFIG = Object.freeze({
  apiBaseUrl: "", // HTTPS backend URL, or "same-origin" when served by FastAPI.
  phone: "",
  whatsapp: "", // International digits, for example 447700900000.
  vehicleAdjustments: Object.freeze({
    van12v: 0,
    vanLarge24v: 0,
  }),
});
