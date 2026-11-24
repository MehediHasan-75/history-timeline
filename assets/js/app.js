import { Timeline } from "@knight-lab/timelinejs";
import { signedYear } from "./date-utils.mjs";

const normalizeDigits = (value) => String(value || "").replace(/[০-৯]/g, (digit) => "০১২৩৪৫৬৭৮৯".indexOf(digit));
const bengaliMonths = ["বৈশাখ", "জ্যৈষ্ঠ", "আষাঢ়", "শ্রাবণ", "ভাদ্র", "আশ্বিন", "কার্তিক", "অগ্রহায়ণ", "পৌষ", "মাঘ", "ফাল্গুন", "চৈত্র"];
const gregorianMonths = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

const focusableSelector = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])"
].join(",");

const setupToggle = (button) => {
  const target = document.getElementById(button.getAttribute("aria-controls"));
  if (!target) return;
  button.addEventListener("click", () => {
    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!expanded));
    target.hidden = expanded;
  });
};

const setupDialog = (dialog) => {
  const id = dialog.id;
  let returnFocus = null;

  const close = () => {
    dialog.close();
    document.body.classList.remove("overflow-hidden");
    returnFocus?.focus();
  };

  document.querySelectorAll(`[data-dialog-open="${id}"]`).forEach((button) => {
    button.addEventListener("click", () => {
      returnFocus = button;
      dialog.showModal();
      document.body.classList.add("overflow-hidden");
      dialog.querySelector(focusableSelector)?.focus();
    });
  });

  dialog.querySelectorAll("[data-dialog-close]").forEach((button) => button.addEventListener("click", close));
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    close();
  });
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) close();
  });
  dialog.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;
    const focusable = [...dialog.querySelectorAll(focusableSelector)];
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });
};

const setupDrawer = (button) => {
  const drawer = document.getElementById(button.getAttribute("aria-controls"));
  if (!drawer) return;
  const closeButton = drawer.querySelector("[data-drawer-close]");
  const close = () => {
    drawer.classList.add("hidden");
    button.setAttribute("aria-expanded", "false");
    document.body.classList.remove("overflow-hidden");
    button.focus();
  };
  const open = () => {
    drawer.classList.remove("hidden");
    button.setAttribute("aria-expanded", "true");
    document.body.classList.add("overflow-hidden");
    closeButton?.focus();
  };
  button.addEventListener("click", open);
  closeButton?.addEventListener("click", close);
  drawer.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && window.innerWidth < 1024) close();
  });
};

const setupEndDate = (root = document) => {
  root.querySelectorAll("[data-end-date-toggle]").forEach((toggle) => {
    const panel = document.getElementById(toggle.getAttribute("aria-controls"));
    if (!panel) return;
    const sync = () => {
      panel.hidden = !toggle.checked;
      panel.querySelectorAll("input, select").forEach((field) => {
        field.disabled = !toggle.checked;
      });
    };
    toggle.addEventListener("change", sync);
    sync();
  });
};

const validateHistoricalForm = (form) => {
  form.addEventListener("submit", (event) => {
    let valid = true;
    form.querySelectorAll("[data-date-group]").forEach((group) => {
      const year = group.querySelector("[data-date-year]");
      const month = group.querySelector("[data-date-month]");
      const day = group.querySelector("[data-date-day]");
      if (year && !year.disabled && year.value && Number(normalizeDigits(year.value)) < 1) {
        year.setCustomValidity("Year must be 1 or greater. Historical calendars have no year zero.");
        valid = false;
      } else {
        year?.setCustomValidity("");
      }
      if (day && !day.disabled && day.value && !month?.value) {
        day.setCustomValidity("Choose a month before entering a day.");
        valid = false;
      } else {
        day?.setCustomValidity("");
      }
    });
    if (!valid) {
      event.preventDefault();
      form.reportValidity();
    }
  });
};

const setupCalendarGroups = (root = document) => {
  root.querySelectorAll("[data-date-group]").forEach((group) => {
    const calendar = group.querySelector("[data-date-calendar]");
    const era = group.querySelector("[data-era-group]");
    const month = group.querySelector("[data-date-month]");
    if (!calendar) return;
    const sync = () => {
      const bengali = calendar.value === "BENGALI_BD";
      era.hidden = bengali;
      era.querySelectorAll("input").forEach((input) => { input.disabled = bengali; });
      [...month.options].slice(1).forEach((option, index) => { option.textContent = (bengali ? bengaliMonths : gregorianMonths)[index]; });
    };
    calendar.addEventListener("change", sync);
    sync();
  });
  root.querySelectorAll("[data-filter-calendar]").forEach((calendar) => {
    const era = calendar.form?.querySelector("[data-filter-era]");
    const sync = () => {
      if (!era) return;
      const bengali = calendar.value === "BENGALI_BD";
      era.hidden = bengali;
      era.querySelectorAll("input").forEach((input) => { input.disabled = bengali; });
    };
    calendar.addEventListener("change", sync);
    sync();
  });
};

const paramsFromFilters = (form) => {
  const params = new URLSearchParams();
  const data = new FormData(form);
  for (const [name, value] of data.entries()) {
    if (!value || name.endsWith("_year_abs") || name.endsWith("_era")) continue;
    params.append(name, value);
  }
  [["year_from", "year_from_abs", "year_from_era"], ["year_to", "year_to_abs", "year_to_era"]]
    .forEach(([output, yearName, eraName]) => {
      const rawYear = normalizeDigits(data.get(yearName));
      const value = data.get("calendar") === "BENGALI_BD" ? (rawYear ? Number(rawYear) : null) : signedYear(rawYear, data.get(eraName));
      if (value !== null) params.set(output, String(value));
    });
  return params;
};

const updateChips = (form, root) => {
  if (!root) return;
  root.replaceChildren();
  [...new FormData(form).entries()].forEach(([name, value]) => {
    if (!value || name.endsWith("_era") || name === "csrfmiddlewaretoken") return;
    const field = form.elements.namedItem(name);
    const label = field instanceof RadioNodeList ? value : field?.selectedOptions?.[0]?.text || value;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chip";
    button.dataset.filterRemove = name;
    button.dataset.filterValue = value;
    const labelNode = document.createElement("span");
    labelNode.textContent = String(label);
    const icon = document.createElement("span");
    icon.ariaHidden = "true";
    icon.textContent = "×";
    const accessibleLabel = document.createElement("span");
    accessibleLabel.className = "sr-only";
    accessibleLabel.textContent = "Remove filter";
    button.append(labelNode, icon, accessibleLabel);
    root.append(button);
  });
};

const setupTimeline = (root) => {
  const feedUrl = root.dataset.feedUrl;
  const filterForm = document.querySelector(root.dataset.filterForm || "[data-filter-form]");
  const status = root.querySelector("[data-timeline-status]");
  const chips = document.querySelector("[data-active-filters]");
  let activeEventId = null;
  let requestController = null;

  const setStatus = (kind, message) => {
    status.hidden = kind === "ready";
    status.dataset.state = kind;
    status.querySelector("[data-status-message]").textContent = message;
    status.querySelector("[data-status-retry]").hidden = kind !== "error";
  };

  const render = async () => {
    requestController?.abort();
    requestController = new AbortController();
    setStatus("loading", "Loading historical events…");
    const params = filterForm ? paramsFromFilters(filterForm) : new URLSearchParams();
    if (filterForm) updateChips(filterForm, chips);
    try {
      const response = await fetch(`${feedUrl}?${params}`, {
        headers: { Accept: "application/json" },
        signal: requestController.signal
      });
      if (!response.ok) throw new Error(`Timeline request failed with ${response.status}`);
      const data = await response.json();
      if (!data || !Array.isArray(data.events)) throw new Error("Timeline response has an invalid shape");
      if (!data.events.length) {
        setStatus("empty", "No events match these filters.");
        return;
      }
      const container = document.createElement("div");
      container.className = "h-full w-full";
      container.id = `timeline-${Math.random().toString(36).slice(2)}`;
      root.querySelector("[data-timeline-canvas]").replaceChildren(container);
      const startIndex = Math.max(0, data.events.findIndex((event) => event.unique_id === activeEventId));
      const timeline = new Timeline(container, data, {
        start_at_slide: startIndex,
        hash_bookmark: false,
        timenav_position: "bottom",
        timenav_height_percentage: 28,
        timenav_mobile_height_percentage: 38,
        language: root.dataset.languageUrl || "en"
      });
      timeline.on?.("change", (event) => {
        activeEventId = event?.unique_id || activeEventId;
      });
      setStatus("ready", "Timeline loaded.");
    } catch (error) {
      if (error.name === "AbortError") return;
      setStatus("error", "Timeline could not load. Check your connection and try again.");
    }
  };

  filterForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    render();
  });
  filterForm?.addEventListener("change", render);
  filterForm?.addEventListener("reset", () => window.setTimeout(render, 0));
  chips?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter-remove]");
    if (!button || !filterForm) return;
    const fields = [...filterForm.querySelectorAll(`[name="${CSS.escape(button.dataset.filterRemove)}"]`)];
    fields.forEach((field) => {
      if ((field.type === "checkbox" || field.type === "radio") && field.value === button.dataset.filterValue) field.checked = false;
      else if (field.value === button.dataset.filterValue) field.value = "";
    });
    render();
  });
  status.querySelector("[data-status-retry]")?.addEventListener("click", render);
  render();
};

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-toggle]").forEach(setupToggle);
  document.querySelectorAll("[data-drawer-open]").forEach(setupDrawer);
  document.querySelectorAll("dialog[data-dialog]").forEach(setupDialog);
  document.querySelectorAll("form[data-historical-form]").forEach(validateHistoricalForm);
  document.querySelectorAll("[data-timeline]").forEach(setupTimeline);
  setupEndDate();
  setupCalendarGroups();
});

export { paramsFromFilters };
