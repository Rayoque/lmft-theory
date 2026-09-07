/* Renders index.html in a real DOM and clicks through it.
 *
 * The other harness tests pure functions -- queue order, mastery state -- and
 * every bug that reached Lauren lived outside that: a button label
 * contradicting the setting, a summary reporting 0% for a session that never
 * happened, a stats object missing a field on one code path. None of those are
 * reachable without something actually rendering and being clicked.
 *
 * jsdom is dev tooling. index.html still ships with no dependencies.
 *
 *   npm i jsdom --prefix %TEMP%
 *   node scripts/rendertest.js
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require(path.join(
  process.env.TEMP || "/tmp", "node_modules", "jsdom"));

const HTML = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");

let pass = 0, fail = 0;
const ok = (n, c, extra) => { c ? pass++ : fail++;
  console.log("  " + (c ? "PASS" : "FAIL") + "  " + n +
              (!c && extra ? "  <- " + extra : "")); };
const head = t => console.log("\n=== " + t + " ===");

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
  if (modal) modal.querySelector("#again2").click();       // dismiss welcome
  return { w, d };
}

/* Only the rendered regions. body.textContent would swallow the inline
   <script>, whose template literals trip every check for a dollar-brace. */
const txt = d => ["header", "#view", "footer"]
  .map(sel => (d.querySelector(sel) || {}).textContent || "")
  .join(" ").replace(/\s+/g, " ").trim();
const tab = (d, name) => [...d.querySelectorAll("nav button")]
  .find(b => b.textContent.trim().startsWith(name));

/* Answer the current question deterministically. The key is not in the DOM,
   so ask the app which option is correct through its own global scope.
   Picking index 0 and hoping made the miss assertions flaky, which is worse
   than having no assertion at all. */
function answer(w, d, right, knew){
  const opts = [...d.querySelectorAll("#opts button.opt")];
  if (!opts.length) return false;
  const correct = w.eval("Q[qi].options.findIndex(o => o.correct)");
  const pick = right ? correct : (correct === 0 ? opts.length - 1 : 0);
  opts[pick].click();
  if (right && !opts[pick].classList.contains("correct")) throw new Error("expected a hit");
  if (!right && !opts[pick].classList.contains("wrong")) throw new Error("expected a miss");
  const conf = d.querySelector('footer [data-k="' + (knew ? 1 : 0) + '"]');
  if (conf) conf.click();
  return true;
}

/* ------------------------------------------------------------------ */
head("renders at all Learn sizes");
for (const size of [3, 5, 10]){
  const { w, d } = boot();
  tab(d, "Learn").click();
  const szBtn = [...d.querySelectorAll("[data-n]")].find(b => b.dataset.n == size);
  ok("size chip " + size + " exists", !!szBtn);
  szBtn.click();
  const chip = [...d.querySelectorAll("[data-n]")].find(b => b.dataset.n == size);
  ok("size " + size + " shows selected", chip.classList.contains("on"));

  d.querySelector('[data-m="bowen"]').click();
  const start = d.querySelector("#start");
  ok("brief button says " + size, start.textContent.includes(String(size)),
     start.textContent.trim());

  start.click();
  ok('counter reads "1 of ' + size + '"',
     d.querySelector(".note").textContent.includes("1 of " + size),
     d.querySelector(".note").textContent);

  // answer them all, missing the first, and confirm the total never moves
  const totals = new Set();
  let n = 0;
  while (d.querySelector("#opts") && n < size + 5){
    totals.add(d.querySelector(".note").textContent.split(" of ")[1]);
    answer(w, d, n !== 0, false);
    n++;
  }
  ok("session stayed " + size + " long", totals.size === 1 && n === size,
     "totals " + [...totals] + " over " + n + " questions");
  ok("summary appeared", txt(d).includes("Session done"));
  ok("retry offered after a miss", !!d.querySelector("#retry"));
  if (d.querySelector("#retry")){
    d.querySelector("#retry").click();
    ok("retry starts a queue", !!d.querySelector("#opts"));
  }
}

/* ------------------------------------------------------------------ */
head("every view renders clean");
{
  const { d } = boot();
  const BAD = ["undefined", "NaN", "[object Object]", "${", "null,"];
  for (const name of ["Learn", "Drill", "Grid", "Progress"]){
    tab(d, name).click();
    const t = txt(d);
    ok(name + " renders", t.length > 40, "only " + t.length + " chars");
    const hit = BAD.find(b => t.includes(b));
    ok(name + " has no template leakage", !hit, hit);
  }

  tab(d, "Grid").click();
  const rows = d.querySelectorAll("table.grid tbody tr");
  ok("grid has 14 rows", rows.length === 14, String(rows.length));
  ok("grid has 7 columns", d.querySelectorAll("table.grid thead th").length === 7);
  ok("grid lists many interventions, not one",
     rows[0].children[3].textContent.includes("·"),
     rows[0].children[3].textContent.slice(0, 60));
  ok("client-centered shows the gap honestly",
     [...rows].find(r => r.textContent.includes("Client Centered"))
       .textContent.includes("not in packet"));
}

/* ------------------------------------------------------------------ */
head("reveal shows what it should");
{
  const { d } = boot();
  tab(d, "Drill").click();
  d.querySelector("#opts button.opt").click();
  const rev = d.querySelector("#reveal").textContent;
  ok("no 'Correct.' banner", !rev.includes("Correct."));
  ok("no 'Not this one'", !rev.includes("Not this one"));
  ok("packet quote shown", rev.includes("verbatim from your packet"));
  ok("flag link present", !!d.querySelector("#flag"));
  ok("options stay selectable",
     ![...d.querySelectorAll("#opts button.opt")].some(b => b.disabled));
  ok("confidence prompt removed",
     !d.querySelector("footer").textContent.includes("Did you know it"));
  ok("both confidence buttons", d.querySelectorAll("footer [data-k]").length === 2);
}

/* ------------------------------------------------------------------ */
head("theme and feedback");
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
head("promises match the pool");
{
  const { w, d } = boot();
  tab(d, "Learn").click();
  [...d.querySelectorAll("[data-n]")].find(b => b.dataset.n == "10").click();
  d.querySelector('[data-m="client-centered"]').click();
  const label = d.querySelector("#start").textContent;
  ok("Client Centered offers 3, not 10",
     label.includes("3") && !label.includes("10"), label.trim());
  d.querySelector("#start").click();
  ok("and delivers 1 of 3",
     d.querySelector(".note").textContent.includes("1 of 3"),
     d.querySelector(".note").textContent);
  ok("vignette session clamps to 17",
     w.eval('sessionN("vignette", null)') === 17,
     String(w.eval('sessionN("vignette", null)')));
  ok("drill session is 20", w.eval('sessionN("drill", null)') === 20);
}

/* ------------------------------------------------------------------ */
head("state is recorded when she answers");
{
  const { w, d } = boot();
  tab(d, "Drill").click();
  const id = JSON.stringify(w.eval("Q[qi].id"));
  d.querySelector("#opts button.opt").click();
  // deliberately do NOT tap a confidence button; she taps a nav tab instead
  ok("answer persists without the confidence tap", w.eval("!!S.concepts[" + id + "]"));
  ok("seen counted exactly once", w.eval("S.concepts[" + id + "].seen") === 1);

  const n = new Date(), pad = x => String(x).padStart(2, "0");
  const local = n.getFullYear() + "-" + pad(n.getMonth() + 1) + "-" + pad(n.getDate());
  ok("today() is local, not UTC", w.eval("today()") === local, w.eval("today()"));
}

/* ------------------------------------------------------------------ */
head("tags read as words");
{
  const { w, d } = boot();
  const seen = new Set();
  tab(d, "Drill").click();
  for (let i = 0; i < 40 && d.querySelector("#opts"); i++){
    seen.add(d.querySelector(".tag").textContent.trim());
    answer(w, d, true, false);
  }
  ok("no squished tag like examtip",
     ![...seen].some(t => /examtip/i.test(t)), [...seen].join(", "));
}

/* ------------------------------------------------------------------ */
console.log("\n" + pass + " passed, " + fail + " failed\n");
process.exit(fail ? 1 : 0);
