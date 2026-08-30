const quoteForm = document.querySelector("#quote-form");
const vehicleType = document.querySelector("#vehicle-type");
const calloutTime = document.querySelector("#callout-time");
const estimatedPrice = document.querySelector("#estimated-price");
const formMessage = document.querySelector("#form-message");

function updateEstimate() {
  const selectedVehicle = vehicleType.value;
  const selectedTime = Number(calloutTime.value || 0);

  if (!selectedVehicle) {
    estimatedPrice.textContent = "Enter postcode and vehicle type";
    return;
  }

  if (selectedVehicle === "van") {
    estimatedPrice.textContent = "Van price requires confirmation";
    return;
  }

  if (selectedVehicle === "large") {
    estimatedPrice.textContent = "Manual quote required";
    return;
  }

  if (selectedVehicle === "car") {
    const exampleBasePrice = 45;
    const total = exampleBasePrice + selectedTime;

    estimatedPrice.textContent =
      `From £${total}, subject to postcode coverage`;
  }
}

vehicleType.addEventListener("change", updateEstimate);
calloutTime.addEventListener("change", updateEstimate);

quoteForm.addEventListener("submit", (event) => {
  event.preventDefault();

  if (!quoteForm.checkValidity()) {
    quoteForm.reportValidity();
    formMessage.textContent =
      "Please complete all required fields.";
    return;
  }

  formMessage.textContent =
    "Quote details checked. No information has been sent or stored.";
});