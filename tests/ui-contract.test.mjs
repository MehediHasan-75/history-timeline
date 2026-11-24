import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import { relative } from "node:path";
import { test } from "node:test";
import { displayYear, signedYear } from "../assets/js/date-utils.mjs";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

const templateRoot = new URL("../templates/", import.meta.url);

const templateFiles = async (directory = templateRoot) => {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map((entry) => {
    const path = new URL(entry.name + (entry.isDirectory() ? "/" : ""), directory);
    return entry.isDirectory() ? templateFiles(path) : [path];
  }));
  return nested.flat().filter((path) => path.pathname.endsWith(".html"));
};

test("event form uses integer date controls instead of native date inputs", async () => {
  const template = await read("templates/events/_event_form.html");
  assert.match(template, /start_year_abs/);
  assert.match(template, /start_era/);
  assert.match(template, /end_year_abs/);
  assert.doesNotMatch(template, /type=["']date["']/);
});

test("Tailwind scans templates and frontend JavaScript", async () => {
  const config = await read("tailwind.config.js");
  assert.match(config, /templates\/\*\*\/\*\.html/);
  assert.match(config, /assets\/js\/\*\*\/\*\.js/);
});

test("base template loads versioned compiled assets", async () => {
  const template = await read("templates/base.html");
  assert.match(template, /app\.v1\.css/);
  assert.match(template, /timeline\.v3\.9\.13\.css/);
  assert.match(template, /app\.v1\.js/);
  assert.match(template, /favicon\.svg/);
});

test("timeline pages use shared full-width filter toolbar", async () => {
  const [filters, publicTimeline, dashboard] = await Promise.all([
    read("templates/components/filters.html"),
    read("templates/core/public_timeline.html"),
    read("templates/core/dashboard.html"),
  ]);
  assert.match(filters, /data-filter-search/);
  assert.match(filters, /data-filter-advanced-drawer/);
  assert.match(filters, /data-filter-mobile-open/);
  assert.match(filters, /data-filter-clear/);
  assert.match(filters, /data-result-count/);
  assert.doesNotMatch(filters, /Apply filters/);
  assert.doesNotMatch(publicTimeline, /lg:grid-cols-\[19rem/);
  assert.doesNotMatch(dashboard, /lg:grid-cols-\[19rem/);
});

test("timeline filtering debounces search and cancels obsolete requests", async () => {
  const script = await read("assets/js/app.js");
  assert.match(script, /new AbortController\(\)/);
  assert.match(script, /window\.setTimeout\(render, 300\)/);
  assert.match(script, /data\.events\.length/);
  assert.match(script, /count === 1 \? "event" : "events"/);
});

test("TimelineJS vendor font referenced by its stylesheet is packaged", async () => {
  const font = await read("static/css/icons/tl-icons.woff2");
  assert.ok(font.length > 0);
});

test("BCE and CE years convert without a year zero", () => {
  assert.equal(signedYear("44", "BCE"), -44);
  assert.equal(signedYear("1", "BCE"), -1);
  assert.equal(signedYear("1", "CE"), 1);
  assert.equal(signedYear("0", "CE"), null);
  assert.equal(displayYear(-44), "44 BCE");
  assert.equal(displayYear(1), "1 CE");
  assert.equal(displayYear(0), null);
});

test("Django template delimiters and referenced templates are complete", async () => {
  const files = await templateFiles();
  const known = new Set(files.map((file) => relative(templateRoot.pathname, file.pathname)));
  for (const file of files) {
    const source = await readFile(file, "utf8");
    assert.equal(source.match(/\{%/g)?.length ?? 0, source.match(/%\}/g)?.length ?? 0, `${file.pathname} has an unclosed block tag`);
    assert.equal(source.match(/\{\{/g)?.length ?? 0, source.match(/\}\}/g)?.length ?? 0, `${file.pathname} has an unclosed variable tag`);
    for (const match of source.matchAll(/\{%\s*(?:extends|include)\s+"([^"]+)"/g)) {
      assert.ok(known.has(match[1]), `${file.pathname} references missing template ${match[1]}`);
    }
  }
});
