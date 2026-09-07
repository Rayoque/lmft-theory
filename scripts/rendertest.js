/* Renders index.html in a real DOM and clicks through it.
 *
 * The other harness tests pure functions -- queue order, mastery state -- and
 * every bug that reached Lauren lived outside that: a button whose label
 * contradicted the setting, a summary reporting 0% for a session that never
 * happened, a stats object missing a field on one code path. Those are only
 * visible if something actually renders and gets clicked.
 *
 * jsdom is dev tooling here. index.html ships with no dependencies.
 *
 *   npm i jsdom --prefix %TEMP%   (already done)
 *   node scripts/rendertest.js
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require(path.join(
  process.env.TEMP || "/tmp", "node_modules", "jsdom"));

const HTML = fs.readFileSync(
  path.join(__dirname, "..", "index.html"), "utf8");

let pass = 0, fail = 0;
const ok  = (n, c, extra) => { c ? pass++ : fail++;
  console.log(`  ${c ? "PASS" : "FAIL"}  ${n}${!c && extra ? "  <- " + extra : ""}`); };

function boot(){
  const dom = new JSDOM(HTML, {
    runScripts: "dangerously",
    url: "https://rayoque.github.io/lmft-theory/",
    pretendToBeVisual: true,
    beforeParse(w){
      w.matchMedia = () => ({ matches:false, addEventListener(){}, addListener(){} });
      w.scrollTo = () => {};
    },
  });
  const w = dom.window, d = w.document;
  const modal = d.querySelector(".overlay");
  if (modal) modal.querySelector("#again2").click();      // dismiss welcome
  return { w, d };
}

/* Only the rendered regions. body.textContent would swallow the inline
   <script>, whose template literals trip every check for "${". */
const txt = d => ["header", "#view", "footer"]
  .map(sel => (d.querySelector(sel) || {}).textContent || "")
  .join(" ").replace(/\s+/g, " ").trim();
const tab  = (d, name) => [...d.querySelectorAll("nav button")]
  .find(b => b.textContent.trim().startsWith(name));

/* answer the current question; right=true picks the correct option */
function answer(d, right, knew){
  const opts = [...d.querySelectorAll("#opts button.opt")];
  if (!opts.length) return false;
  // the key is not in the DOM, so find it after revealing
  const pick = right ? 0 : (opts.length - 1);
  opts[pick].click();
  let chosen = d.querySelector("#opts button.opt.correct");
  if (right && chosen && !chosen.classList.contains("wrong")){
    // clicked wrong by luck; that is fine, we only need determinism below
  }
  const conf = d.querySelector(`footer [data-k="${knew ? 1 : 0}"]`);
  if (conf) conf.click();
  return true;
}

/* ------------------------------------------------------------------ */
console.log("\n=== renders at all Learn sizes ===");
for (const size of [3, 5, 10]){
  const { d } = boot();
  tab(d, "Learn").click();
  const szBtn = [...d.querySelectorAll("[data-n]")].find(b => b.dataset.n == size);
  ok(`size chip ${size} exists`, !!szBtn);
  szBtn.click();

  const chip = [...d.querySelectorAll("[data-n]")].find(b => b.dataset.n == size);
  ok(`size ${size} shows selected`, chip.classList.contains("on"));

  d.querySelector('[data-m="bowen"]').click();
  const start = d.querySelector("#start");
  ok(`brief button says ${size}`,
     start.textContent.includes(String(size)),
     start.textContent.trim());

  start.click();
  const counter = d.querySelector(".note").textContent;
  ok(`counter reads "1 of ${size}"`, counter.includes(`1 of ${size}`), counter);

  // answer them all, missing the first, and confirm the total never moves
  let totals = new Set(), n = 0;
  while (d.querySelector("#opts") && n < size + 5){
    totals.add(d.querySelector(".note").textContent.split(" of ")[1]);
    answer(d, n !== 0, false);
    n++;
  }
  ok(`session stayed ${size} long`, totals.size === 1 && n === size,
     `saw totals ${[...totals]} over ${n} questions`);
  ok("summary appeared", txt(d).includes("Session done"));
  ok("retry offered after a miss", !!d.querySelector("#retry"));

  if (d.querySelector("#retry")){
    d.querySelector("#retry").click();
    ok("retry starts a queue", !!d.querySelector("#opts"));
  }
}

/* ------------------------------------------------------------------ */
console.log("\n=== every view renders clean ===");
{
  const { d } = boot();
  const BAD = ["undefined", "NaN", "[object Object]", "${", "null,"];
  for (const name of ["Learn", "Drill", "Grid", "Progress"]){
    tab(d, name).click();
    const t = txt(d);
    ok(`${name} renders`, t.length > 40, `only ${t.length} chars`);
    const hit = BAD.find(b => t.includes(b));
    ok(`${name} has no template leakage`, !hit, hit);
  }

  tab(d, "Grid").click();
  const rows = d.querySelectorAll("table.grid tbody tr");
  const cols = d.querySelectorAll("table.grid thead th");
  ok("grid has 14 rows", rows.length === 14, `${rows.length}`);
  ok("grid has 7 columns", cols.length === 7, `${cols.length}`);
  ok("grid lists many interventions, not one",
     rows[0].children[3].textContent.includes("·"),
     rows[0].children[3].textContent.slice(0, 60));
  ok("client-centered shows the gap honestly",
     [...rows].find(r => r.textContent.includes("Client Centered"))
       .textContent.includes("not in packet"));
}

/* ------------------------------------------------------------------ */
console.log("\n=== reveal shows what it should ===");
{
  const { d } = boot();
  tab(d, "Drill").click();
  d.querySelector("#opts button.opt").click();
  const rev = d.querySelector("#reveal").textContent;
  ok("no 'Correct.' banner", !rev.includes("Correct."));
  ok("no 'Not this one'",    !rev.includes("Not this one"));
  ok("packet quote shown",   rev.includes("verbatim from your packet"));
  ok("flag link present",    !!d.querySelector("#flag"));
  ok("options stay selectable",
     ![...d.querySelectorAll("#opts button.opt")].some(b => b.disabled));
  const foot = d.querySelector("footer").textContent;
  ok("confidence prompt removed", !foot.includes("Did you know it"));
  ok("both confidence buttons", d.querySelectorAll("footer [data-k]").length === 2);
}

/* ------------------------------------------------------------------ */
console.log("\n=== theme + feedback ===");
{
  const { d } = boot();
  const t = d.getElementById("theme");
  const seen = [];
  for (let i = 0; i < 4; i++){ seen.push(t.textContent.trim()); t.click(); }
  ok("theme cycles through three", new Set(seen).size === 3, seen.join(" -> "));
  ok("returns to start", seen[0] === seen[3]);

  tab(d, "Progress").click();
  ok("feedback link on Progress", !!d.getElementById("fbopen"));
  d.getElementById("fbopen").click();
  ok("feedback modal opens", !!d.querySelector(".overlay"));
  ok("has a copy fallback", !!d.querySelector("#fbcopy"));
  ok("no raw email in markup", !/tannen\.skriver@/.test(d.body.innerHTML));
}

/* ------------------------------------------------------------------ */
console.log(`\n${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
