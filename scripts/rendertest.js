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
    totals.add((d.querySelector(".note").textContent.match(/of (\d+)/) || [])[1]);
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

head("keyboard navigation");
{
  const { w, d } = boot();
  const key = k => d.dispatchEvent(new w.KeyboardEvent("keydown", {key:k, bubbles:true}));
  tab(d, "Drill").click();
  const opts = () => [...d.querySelectorAll("#opts button.opt")];

  key("ArrowDown");
  ok("first arrow focuses first option", d.activeElement === opts()[0]);
  key("ArrowDown");
  ok("arrow down advances", d.activeElement === opts()[1]);
  key("ArrowUp");
  ok("arrow up goes back", d.activeElement === opts()[0]);
  key("ArrowUp");
  ok("arrow up wraps to last", d.activeElement === opts()[opts().length - 1]);

  d.activeElement.click();
  const conf = [...d.querySelectorAll("footer [data-k]")];
  key("ArrowDown");
  ok("after answering, arrows move to confidence",
     conf.includes(d.activeElement), String(d.activeElement && d.activeElement.className));
  key("ArrowRight");
  ok("left/right work on confidence too", conf.includes(d.activeElement));
  ok("options carry a hover hint",
     (opts()[0].getAttribute("title") || "").includes("space"));
}

/* ------------------------------------------------------------------ */

head("no same-day repeats");
{
  const { w, d } = boot();
  tab(d, "Learn").click();
  [...d.querySelectorAll("[data-n]")].find(b => b.dataset.n == "5").click();
  d.querySelector('[data-m="bowen"]').click();
  d.querySelector("#start").click();

  const seen = [];
  for (let round = 0; round < 3; round++){
    while (d.querySelector("#opts")){
      seen.push(w.eval("Q[qi].id"));
      answer(w, d, true, false);           // always correct
    }
    const again = d.querySelector("#again");
    if (!again) break;
    again.click();
  }
  ok("no item served twice in a day", new Set(seen).size === seen.length,
     (seen.length - new Set(seen).size) + " repeats across " + seen.length);
  ok("weight drops to 0 once correct today",
     w.eval("weight(" + JSON.stringify(seen[0]) + ")") === 0);
  ok("unseen items outrank seen ones", w.eval("weight('nope_not_an_id')") === 3);
}

head("exhausted states differ");
{
  const { w, d } = boot();
  tab(d, "Learn").click();
  d.querySelector('[data-m="client-centered"]').click();
  d.querySelector("#start").click();
  while (d.querySelector("#opts")) answer(w, d, true, false);
  const again = d.querySelector("#again");
  if (again) again.click();
  const t = txt(d);
  ok("says done for today, not locked in",
     t.includes("Done here for today") && !t.includes("Nothing left here"),
     t.slice(0, 90));
}


head("undo and space-to-confirm");
{
  const { w, d } = boot();
  tab(d, "Drill").click();
  const firstId = w.eval("Q[qi].id");
  ok("no Back on the first question", !d.getElementById("back"));

  answer(w, d, true, true);                       // right, tapped Knew it
  ok("Back appears after answering", !!d.getElementById("back"));
  ok("moved to question 2", w.eval("qi") === 1);
  ok("first answer recorded",
     w.eval("S.concepts[" + JSON.stringify(firstId) + "].seen") === 1);

  d.getElementById("back").click();
  ok("Back returns to question 1", w.eval("qi") === 0);
  ok("Back un-reveals it", !d.querySelector("#opts button.opt.done"));
  ok("Back undoes the record",
     w.eval("!S.concepts[" + JSON.stringify(firstId) + "]"));
  ok("Back undoes the tally", w.eval("stats.right") === 0);

  // a correct answer parks focus on Knew it so a second space confirms
  answer(w, d, true, false);
  d.querySelector("#opts button.opt").click();     // no-op, already answered
  const { w: w2, d: d2 } = boot();
  tab(d2, "Drill").click();
  const correct = w2.eval("Q[qi].options.findIndex(o => o.correct)");
  [...d2.querySelectorAll("#opts button.opt")][correct].click();
  ok("right answer focuses Knew it",
     d2.activeElement === d2.querySelector('footer [data-k="1"]'));

  const { w: w3, d: d3 } = boot();
  tab(d3, "Drill").click();
  const c3 = w3.eval("Q[qi].options.findIndex(o => o.correct)");
  const opts3 = [...d3.querySelectorAll("#opts button.opt")];
  opts3[c3 === 0 ? opts3.length - 1 : 0].click();  // wrong on purpose
  ok("wrong answer does NOT preselect Knew it",
     d3.activeElement !== d3.querySelector('footer [data-k="1"]'));
}


head("picker marks a model finished for today");
{
  const { w, d } = boot();
  tab(d, "Learn").click();
  d.querySelector('[data-m="client-centered"]').click();
  d.querySelector("#start").click();
  while (d.querySelector("#opts")) answer(w, d, true, false);

  tab(d, "Learn").click();
  const tile = d.querySelector('[data-m="client-centered"]');
  ok("tile says done today", tile.textContent.includes("done today"), tile.textContent.trim());
  ok("tile gets its own colour", tile.classList.contains("s-today"), tile.className);
  const other = d.querySelector('[data-m="bowen"]');
  ok("untouched models unaffected", other.textContent.includes("not started"));
}


head("harbor theme");
{
  const { w, d } = boot();
  tab(d, "Drill").click();
  const chips = [...d.querySelectorAll("#opts button.opt .ch")].map(c => c.textContent);
  ok("options carry A-D chips", chips.join("") === "ABCD".slice(0, chips.length), chips.join(""));

  const key = k => d.dispatchEvent(new w.KeyboardEvent("keydown", {key:k, bubbles:true}));
  key("c");
  ok("pressing C answers the third option",
     d.querySelectorAll("#opts button.opt.done").length > 0);
  ok("result gets a mark, not just a colour",
     !!d.querySelector("#opts button.opt.correct .mk"),
     d.querySelector("#opts button.opt.correct").textContent.slice(-3));

  ok("favicon is inlined", /rel="icon" href="data:image\/svg/.test(d.head.innerHTML));
  ok("stem is serif",
     /Georgia/.test(d.querySelector("style, head").textContent || ""));
}


head("grid on a phone");
{
  const { d } = boot();
  tab(d, "Grid").click();
  const rows = d.querySelectorAll(".gnarrow details.mrow");
  ok("one collapsible per model", rows.length === 14, String(rows.length));
  ok("collapsed by default", ![...rows].some(r => r.hasAttribute("open")));
  ok("summary names the model",
     rows[0].querySelector("summary").textContent.includes("Bowen"),
     rows[0].querySelector("summary").textContent);
  const fields = rows[0].querySelectorAll(".mf");
  ok("six labelled fields inside", fields.length === 6, String(fields.length));
  ok("field carries its label",
     fields[0].querySelector("b").textContent.toLowerCase().includes("change"),
     fields[0].querySelector("b").textContent);
  ok("wide table still present for desktop",
     d.querySelectorAll(".gwide table.grid tbody tr").length === 14);
  const cc = [...rows].find(r => r.textContent.includes("Client Centered"));
  ok("gaps stay honest in the narrow layout",
     cc.textContent.includes("not in packet"));
  ok("narrow layout has no horizontal table",
     !d.querySelector(".gnarrow table"));
}


head("mobile answering flow");
{
  const { w, d } = boot();
  let scrolls = 0;
  w.scrollTo = () => { scrolls++; };
  tab(d, "Drill").click();
  const before = scrolls;

  ok("confidence bar hidden before answering", d.querySelector("footer").hidden);
  ok("no space reserved for it yet", !d.body.hasAttribute("data-foot"));

  d.querySelector("#opts button.opt").click();
  ok("bar appears after answering", !d.querySelector("footer").hidden);
  ok("space reserved while it is up", d.body.hasAttribute("data-foot"));
  ok("answering does not jump the page", scrolls === before);

  d.querySelector('footer [data-k="1"]').click();
  ok("bar hidden again on the next question", d.querySelector("footer").hidden);
  ok("reserved space released", !d.body.hasAttribute("data-foot"));
  ok("new question scrolls to top", scrolls === before + 1, String(scrolls - before));
}


head("no build-brief jargon on screen");
{
  const { w, d } = boot();
  const JARGON = ["marker", "collision", "distractor", "examtip", "T1_", "T2_", "V_"];
  const tags = new Set();
  tab(d, "Drill").click();
  let text = "";
  for (let i = 0; i < 60 && d.querySelector("#opts"); i++){
    tags.add(d.querySelector(".tag").textContent.trim());
    text += " " + d.querySelector(".card").textContent;
    answer(w, d, true, false);
  }
  const hit = JARGON.find(j => new RegExp(j, "i").test(text));
  ok("no jargon in questions or reveals", !hit, hit);
  ok("tags are plain words", ![...tags].some(t => /marker|collision|examtip/i.test(t)),
     [...tags].join(", "));
}

console.log("\n" + pass + " passed, " + fail + " failed\n");
process.exit(fail ? 1 : 0);
