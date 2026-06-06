class MaiClimateCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      const card = document.createElement("ha-card");
      card.header = this.config.title || "M.A.I Climate Fan";
      this.content = document.createElement("div");
      this.content.style.padding = "0 16px 16px";
      this.content.style.display = "flex";
      this.content.style.flexDirection = "column";
      this.content.style.gap = "10px";
      card.appendChild(this.content);
      this.appendChild(card);
    }
    
    this.render();
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("You need to define a fan entity");
    }
    this.config = config;
  }

  render() {
    if (!this._hass || !this.config) return;
    
    const entityId = this.config.entity;
    const stateObj = this._hass.states[entityId];
    if (!stateObj) {
      this.content.innerHTML = `Entity not found: ${entityId}`;
      return;
    }

    const percentage = stateObj.attributes.percentage || 0;
    const isOn = stateObj.state === "on";

    this.content.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <ha-icon icon="mdi:fan" style="color: ${isOn ? 'var(--state-fan-active-color, #2196f3)' : 'var(--state-icon-color)'}; animation: ${isOn ? 'spin ' + (3 - percentage/50) + 's linear infinite' : 'none'};"></ha-icon>
          <span style="font-size: 1.2em; font-weight: bold;">${stateObj.attributes.friendly_name || entityId}</span>
        </div>
        <ha-switch .checked="${isOn}" id="toggle-switch"></ha-switch>
      </div>
      
      <div style="margin-top: 10px;">
        <label>Tốc độ: ${percentage}%</label>
        <input type="range" min="0" max="100" value="${percentage}" id="speed-slider" style="width: 100%;">
      </div>
      
      <style>
        @keyframes spin { 100% { transform: rotate(360deg); } }
      </style>
    `;

    // Add event listeners
    const toggleSwitch = this.content.querySelector("#toggle-switch");
    toggleSwitch.addEventListener("change", () => {
      this._hass.callService("fan", isOn ? "turn_off" : "turn_on", {
        entity_id: entityId
      });
    });

    const speedSlider = this.content.querySelector("#speed-slider");
    speedSlider.addEventListener("change", (e) => {
      const val = parseInt(e.target.value);
      this._hass.callService("fan", "set_percentage", {
        entity_id: entityId,
        percentage: val
      });
    });
  }

  getCardSize() {
    return 3;
  }
}

customElements.define("mai-climate-card", MaiClimateCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "mai-climate-card",
  name: "M.A.I Climate Fan Card",
  preview: true,
  description: "Thẻ điều khiển quạt thông minh M.A.I Climate",
});
