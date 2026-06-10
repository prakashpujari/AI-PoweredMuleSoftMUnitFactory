/**
 * Capture UI screenshots using puppeteer-core + system Chrome.
 * Uses in-page React Router navigation to avoid SPA 404s.
 */
const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BASE_URL = "http://localhost:4173";
const OUT_DIR = path.join(__dirname, "..", "docs", "screenshots");

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function waitForContent(page, timeout = 5000) {
  await sleep(2800);
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-gpu",
      "--window-size=1440,900",
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1.5 });

  // ── Load root first (React app boots) ──────────────────────────────────
  console.log("🚀 Loading app...");
  await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 15000 });
  await waitForContent(page);

  // ── Screenshot 1: Dashboard ────────────────────────────────────────────
  console.log("📸 1/5 — Dashboard (above fold)");
  await page.screenshot({ path: path.join(OUT_DIR, "01-dashboard.png") });
  console.log("   ✅ 01-dashboard.png");

  // ── Screenshot 2: Dashboard scrolled (charts) ─────────────────────────
  await page.evaluate(() => window.scrollTo(0, 620));
  await sleep(400);
  console.log("📸 2/5 — Dashboard charts & recent runs");
  await page.screenshot({ path: path.join(OUT_DIR, "02-dashboard-charts.png") });
  console.log("   ✅ 02-dashboard-charts.png");

  // ── Navigate to Applications via sidebar link ─────────────────────────
  await page.evaluate(() => window.scrollTo(0, 0));
  console.log("📸 3/5 — Applications");
  await page.evaluate(() => {
    const a = document.querySelector('a[href="/applications"]');
    if (a) a.click();
  });
  await waitForContent(page);
  await page.screenshot({ path: path.join(OUT_DIR, "03-applications.png") });
  console.log("   ✅ 03-applications.png");

  // ── Navigate to Executive Report ──────────────────────────────────────
  console.log("📸 4/5 — Executive Report (above fold)");
  await page.evaluate(() => {
    const a = document.querySelector('a[href="/executive-report"]');
    if (a) a.click();
  });
  await waitForContent(page);
  await page.screenshot({ path: path.join(OUT_DIR, "04-executive-report.png") });
  console.log("   ✅ 04-executive-report.png");

  // ── Executive Report scrolled (score gauges + BU breakdown) ──────────
  console.log("📸 5/5 — Executive Report scorecards");
  await page.evaluate(() => window.scrollTo(0, 750));
  await sleep(400);
  await page.screenshot({ path: path.join(OUT_DIR, "05-executive-scorecards.png") });
  console.log("   ✅ 05-executive-scorecards.png");

  await browser.close();

  // Print summary
  const files = fs.readdirSync(OUT_DIR).filter(f => f.endsWith(".png"));
  console.log(`\n🎉 ${files.length} screenshots saved → docs/screenshots/`);
  files.forEach(f => {
    const size = (fs.statSync(path.join(OUT_DIR, f)).size / 1024).toFixed(0);
    console.log(`   📄 ${f}  (${size} KB)`);
  });
}

main().catch(err => {
  console.error("Screenshot error:", err.message);
  process.exit(1);
});
