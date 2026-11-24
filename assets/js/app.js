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

const trapFocus = (container, event) => {
  if (event.key !== "Tab") return;
  const focusable = [...container.querySelectorAll(focusableSelector)].filter((element) => element.offsetParent !== null);
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
};

const setupFilterPanels = (form) => {
  const mobileOpen = document.querySelector(`[data-filter-mobile-open][aria-controls="${form.id}"]`);
  const mobileClose = form.querySelector("[data-filter-mobile-close]");
  const advancedOpen = form.querySelector("[data-filter-advanced-open]");
  const advancedDrawer = form.querySelector("[data-filter-advanced-drawer]");
  const advancedClose = form.querySelector("[data-filter-advanced-close]");
  const advancedBackdrop = form.querySelector("[data-filter-advanced-backdrop]");
  const desktop = window.matchMedia("(min-width: 1024px)");
  let returnFocus = null;

  const unlockPage = () => document.body.classList.remove("overflow-hidden");
  const closeAdvanced = ({ restoreFocus = true } = {}) => {
    advancedDrawer?.classList.remove("is-open");
    advancedBackdrop?.classList.remove("is-open");
    form.classList.remove("filter-panel-open");
    advancedOpen?.setAttribute("aria-expanded", "false");
    advancedDrawer?.removeAttribute("role");
    advancedDrawer?.removeAttribute("aria-modal");
    unlockPage();
    if (restoreFocus) advancedOpen?.focus();
  };
  const closeMobile = ({ restoreFocus = true } = {}) => {
    form.classList.add("hidden");
    mobileOpen?.setAttribute("aria-expanded", "false");
    form.removeAttribute("role");
    form.removeAttribute("aria-modal");
    form.removeAttribute("aria-labelledby");
    unlockPage();
    if (restoreFocus) mobileOpen?.focus();
  };

  mobileOpen?.addEventListener("click", () => {
    returnFocus = mobileOpen;
    form.classList.remove("hidden");
    form.setAttribute("role", "dialog");
    form.setAttribute("aria-modal", "true");
    form.setAttribute("aria-labelledby", "mobile-filter-title");
    mobileOpen.setAttribute("aria-expanded", "true");
    document.body.classList.add("overflow-hidden");
    mobileClose?.focus();
  });
  mobileClose?.addEventListener("click", () => closeMobile());
  advancedOpen?.addEventListener("click", () => {
    returnFocus = advancedOpen;
    advancedDrawer?.classList.add("is-open");
    advancedDrawer?.setAttribute("role", "dialog");
    advancedDrawer?.setAttribute("aria-modal", "true");
    advancedBackdrop?.classList.add("is-open");
    form.classList.add("filter-panel-open");
    advancedOpen.setAttribute("aria-expanded", "true");
    document.body.classList.add("overflow-hidden");
    advancedClose?.focus();
  });
  advancedClose?.addEventListener("click", () => closeAdvanced());
  advancedBackdrop?.addEventListener("click", () => closeAdvanced());
  form.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      if (desktop.matches && advancedDrawer?.classList.contains("is-open")) closeAdvanced();
      else if (!desktop.matches && mobileOpen?.getAttribute("aria-expanded") === "true") closeMobile();
      return;
    }
    const activePanel = desktop.matches ? advancedDrawer : form;
    if ((desktop.matches && advancedDrawer?.classList.contains("is-open")) || (!desktop.matches && mobileOpen?.getAttribute("aria-expanded") === "true")) {
      trapFocus(activePanel, event);
    }
  });
  desktop.addEventListener("change", () => {
    closeAdvanced({ restoreFocus: false });
    closeMobile({ restoreFocus: false });
    returnFocus = null;
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
    const sync = () => syncFilterCalendar(calendar.form);
    calendar.addEventListener("change", sync);
    sync();
  });
};

const syncFilterCalendar = (form) => {
  const calendar = form?.querySelector("[data-filter-calendar]");
  const era = form?.querySelector("[data-filter-era]");
  if (!calendar || !era) return;
  const bengali = calendar.value === "BENGALI_BD";
  if (bengali) {
    const allEras = era.querySelector('input[name="era"][value=""]');
    if (allEras) allEras.checked = true;
  }
  era.hidden = bengali;
  era.querySelectorAll("input").forEach((input) => { input.disabled = bengali; });
};

const paramsFromFilters = (form) => {
  const params = new URLSearchParams();
  const data = new FormData(form);
  for (const [name, value] of data.entries()) {
    if (!value || ["year_from_abs", "year_from_era", "year_to_abs", "year_to_era"].includes(name)) continue;
    if (name === "calendar" && value === "GREGORIAN") continue;
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

const addChip = (root, label, name, value = "") => {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "chip";
  button.dataset.filterRemove = name;
  button.dataset.filterValue = value;
  const labelNode = document.createElement("span");
  labelNode.textContent = label;
  const icon = document.createElement("span");
  icon.ariaHidden = "true";
  icon.textContent = "×";
  const accessibleLabel = document.createElement("span");
  accessibleLabel.className = "sr-only";
  accessibleLabel.textContent = `Remove ${label} filter`;
  button.append(labelNode, icon, accessibleLabel);
  root.append(button);
};

const updateChips = (form, root) => {
  if (!root) return;
  const summary = root.closest("[data-filter-summary]");
  root.replaceChildren();
  const data = new FormData(form);
  const query = String(data.get("q") || "").trim();
  const category = form.elements.namedItem("category");
  const calendar = form.elements.namedItem("calendar");
  const era = data.get("era");
  if (query) addChip(root, query, "q", query);
  if (category?.value) addChip(root, category.selectedOptions[0].text, "category", category.value);
  if (calendar?.value === "BENGALI_BD") addChip(root, calendar.selectedOptions[0].text, "calendar", calendar.value);
  form.querySelectorAll('input[name="tag"]:checked').forEach((field) => {
    const label = field.closest("label")?.querySelector("span")?.textContent?.trim() || field.value;
    addChip(root, label, "tag", field.value);
  });
  if (era) addChip(root, era, "era", era);

  const from = normalizeDigits(data.get("year_from_abs"));
  const to = normalizeDigits(data.get("year_to_abs"));
  const calendarIsBengali = calendar?.value === "BENGALI_BD";
  const formatYear = (year, eraName) => year ? `${year}${calendarIsBengali ? "" : ` ${data.get(eraName)}`}` : "";
  if (from || to) {
    const fromLabel = formatYear(from, "year_from_era");
    const toLabel = formatYear(to, "year_to_era");
    const label = from && to ? `${fromLabel}–${toLabel}` : from ? `From ${fromLabel}` : `Up to ${toLabel}`;
    addChip(root, label, "year_range");
  }
  if (summary) summary.hidden = root.childElementCount === 0;
};

const clearFilter = (form, name, value = "") => {
  if (name === "year_range") {
    form.elements.namedItem("year_from_abs").value = "";
    form.elements.namedItem("year_to_abs").value = "";
    return;
  }
  if (name === "tag") {
    form.querySelectorAll('input[name="tag"]').forEach((field) => {
      if (field.value === value) field.checked = false;
    });
    return;
  }
  if (name === "era") {
    form.querySelector('input[name="era"][value=""]').checked = true;
    return;
  }
  const field = form.elements.namedItem(name);
  if (field) field.value = name === "calendar" ? "GREGORIAN" : "";
};

const clearAllFilters = (form) => {
  ["q", "category", "year_from_abs", "year_to_abs"].forEach((name) => { form.elements.namedItem(name).value = ""; });
  form.elements.namedItem("calendar").value = "GREGORIAN";
  form.elements.namedItem("year_from_era").value = "CE";
  form.elements.namedItem("year_to_era").value = "CE";
  form.querySelectorAll('input[name="tag"]').forEach((field) => { field.checked = false; });
  form.querySelector('input[name="era"][value=""]').checked = true;
  syncFilterCalendar(form);
};

const setupTimeline = (root) => {
  const feedUrl = root.dataset.feedUrl;
  const filterForm = document.querySelector(root.dataset.filterForm || "[data-filter-form]");
  const status = root.querySelector("[data-timeline-status]");
  const chips = document.querySelector("[data-active-filters]");
  const resultCounts = document.querySelectorAll("[data-result-count]");
  let activeEventId = null;
  let requestController = null;
  let searchTimer = null;

  const setStatus = (kind, message) => {
    status.hidden = kind === "ready";
    status.dataset.state = kind;
    status.querySelector("[data-status-message]").textContent = message;
    status.querySelector("[data-status-retry]").hidden = kind !== "error";
    resultCounts.forEach((count) => { count.hidden = kind === "loading" || kind === "error"; });
  };

  const setResultCount = (count) => {
    resultCounts.forEach((element) => {
      element.textContent = `${count} ${count === 1 ? "event" : "events"}`;
      element.hidden = false;
    });
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
      setResultCount(data.events.length);
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
    window.clearTimeout(searchTimer);
    render();
  });
  filterForm?.addEventListener("change", (event) => {
    if (event.target.matches("[data-filter-search]")) return;
    window.clearTimeout(searchTimer);
    render();
  });
  filterForm?.querySelector("[data-filter-search]")?.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    requestController?.abort();
    searchTimer = window.setTimeout(render, 300);
  });
  filterForm?.querySelector("[data-filter-clear]")?.addEventListener("click", () => {
    window.clearTimeout(searchTimer);
    clearAllFilters(filterForm);
    render();
  });
  chips?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter-remove]");
    if (!button || !filterForm) return;
    clearFilter(filterForm, button.dataset.filterRemove, button.dataset.filterValue);
    syncFilterCalendar(filterForm);
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
  document.querySelectorAll("form[data-filter-form]").forEach(setupFilterPanels);
  setupEndDate();
  setupCalendarGroups();
  document.querySelectorAll("[data-timeline]").forEach(setupTimeline);
});

export { clearAllFilters, paramsFromFilters, updateChips };
