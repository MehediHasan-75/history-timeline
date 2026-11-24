import { copyFile, mkdir, readdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(root, "node_modules/@knight-lab/timelinejs/dist/css/timeline.css");
const target = resolve(root, "static/dist/timeline.v3.9.13.css");
const mapSource = resolve(root, "node_modules/@knight-lab/timelinejs/dist/css/timeline.css.map");
const mapTarget = resolve(root, "static/dist/timeline.css.map");
const iconSource = resolve(root, "node_modules/@knight-lab/timelinejs/dist/css/icons");
const iconTarget = resolve(root, "static/css/icons");

await mkdir(dirname(target), { recursive: true });
await copyFile(source, target);
await copyFile(mapSource, mapTarget);
await mkdir(iconTarget, { recursive: true });
for (const filename of await readdir(iconSource)) {
  await copyFile(resolve(iconSource, filename), resolve(iconTarget, filename));
}
