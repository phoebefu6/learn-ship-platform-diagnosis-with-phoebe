/* lookback-live.js - the window widget for learn-ship-platform-diagnosis-with-phoebe.
   Real monthly numbers (assets/diagnosis-data.js, exported by notebooks/a2) drawn through a
   lookback window the reader controls. Nothing is modelled: the series are the course dataset.
   Markup contract:
     <div class="lb" data-series="S07" data-asof="2024-08"></div>
   Self-theming from the :root palette. Vanilla, no deps. */
(function () {
  "use strict";
  if (typeof document === "undefined" || !window.DIAG_SERIES) return;
  var css = getComputedStyle(document.documentElement);
  var theme = function (v, fb) { var x = css.getPropertyValue(v).trim(); return x || fb; };
  var C = { navy: theme("--indigo", "#163E6A"), soft: theme("--indigo-soft", "#A9C1DE"), amber: theme("--amber", "#E39B0E"),
            ink: theme("--ink", "#14202E"), muted: theme("--muted", "#5B6B7E"), faint: theme("--faint", "#C3CEDB"), hair: theme("--hairline", "#E3E9F1") };
  var WINDOWS = [3, 6, 12, 24, 60];
  var METRICS = [["margin", "margin %"], ["revenue", "revenue"], ["profit", "profit"], ["orders", "orders"]];

  function el(tag, cls, txt) { var n = document.createElement(tag); if (cls) n.className = cls; if (txt != null) n.textContent = txt; return n; }
  function fmt(v, metric) { return metric === "margin" ? v.toFixed(1) + "%" : (v >= 1000 ? (v / 1000).toFixed(v >= 10000 ? 0 : 1) + "k" : String(v)); }

  document.querySelectorAll(".lb").forEach(function (box) {
    var sid = box.dataset.series || "S07";
    var S = window.DIAG_SERIES[sid];
    if (!S) return;
    var state = { win: 3, metric: "margin", asof: S.months.indexOf(box.dataset.asof || S.months[S.months.length - 1]) };
    if (state.asof < 0) state.asof = S.months.length - 1;

    var head = el("div", "lb-head");
    head.appendChild(el("b", null, "Lookback window on " + sid + (sid === "platform" ? " (all servers)" : "")));
    head.appendChild(el("span", "lb-hint", "Real monthly numbers from the course dataset. Drag the window, change the metric, move the as-of month."));
    box.appendChild(head);

    var ctl = el("div", "lb-ctl");
    var winRow = el("div", "lb-row"); winRow.appendChild(el("span", "lb-lbl", "window"));
    var winBtns = {};
    WINDOWS.forEach(function (w) {
      var b = el("button", "lb-btn", w === 60 ? "all" : w + " mo"); b.type = "button";
      b.addEventListener("click", function () { state.win = w; draw(); });
      winBtns[w] = b; winRow.appendChild(b);
    });
    ctl.appendChild(winRow);
    var metRow = el("div", "lb-row"); metRow.appendChild(el("span", "lb-lbl", "metric"));
    var metBtns = {};
    METRICS.forEach(function (m) {
      var b = el("button", "lb-btn", m[1]); b.type = "button";
      b.addEventListener("click", function () { state.metric = m[0]; draw(); });
      metBtns[m[0]] = b; metRow.appendChild(b);
    });
    ctl.appendChild(metRow);
    var asRow = el("div", "lb-row"); asRow.appendChild(el("span", "lb-lbl", "as of"));
    var slider = el("input", "lb-slider"); slider.type = "range"; slider.min = 12; slider.max = S.months.length - 1; slider.value = state.asof;
    slider.setAttribute("aria-label", "as-of month");
    var asLbl = el("span", "lb-asof", S.months[state.asof]);
    slider.addEventListener("input", function () { state.asof = parseInt(slider.value, 10); draw(); });
    asRow.appendChild(slider); asRow.appendChild(asLbl);
    ctl.appendChild(asRow);
    box.appendChild(ctl);

    var svgNS = "http://www.w3.org/2000/svg";
    var W = 880, H = 300, P = { l: 56, r: 18, t: 18, b: 40 };
    var svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("viewBox", "0 0 " + W + " " + H); svg.setAttribute("class", "lb-svg"); svg.setAttribute("role", "img");
    box.appendChild(svg);
    var read = el("p", "lb-read");
    box.appendChild(read);

    function draw() {
      Object.keys(winBtns).forEach(function (w) { winBtns[w].classList.toggle("on", parseInt(w, 10) === state.win); });
      Object.keys(metBtns).forEach(function (m) { metBtns[m].classList.toggle("on", m === state.metric); });
      asLbl.textContent = S.months[state.asof];
      var end = state.asof, start = Math.max(0, end - state.win + 1);
      var vals = S[state.metric].slice(start, end + 1), months = S.months.slice(start, end + 1);
      var full = S[state.metric].slice(0, end + 1);
      var lo = Math.min.apply(null, full), hi = Math.max.apply(null, full);
      if (state.metric === "margin") { lo = Math.min(lo, 20); hi = Math.max(hi, 50); } else { lo = 0; hi = hi * 1.08; }
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      var x = function (i) { return P.l + (vals.length === 1 ? 0 : i * (W - P.l - P.r) / (vals.length - 1)); };
      var y = function (v) { return P.t + (H - P.t - P.b) * (1 - (v - lo) / (hi - lo || 1)); };
      for (var g = 0; g <= 4; g++) {
        var gy = P.t + g * (H - P.t - P.b) / 4, gv = hi - g * (hi - lo) / 4;
        var line = document.createElementNS(svgNS, "line");
        line.setAttribute("x1", P.l); line.setAttribute("x2", W - P.r); line.setAttribute("y1", gy); line.setAttribute("y2", gy);
        line.setAttribute("stroke", C.hair); svg.appendChild(line);
        var t = document.createElementNS(svgNS, "text"); t.setAttribute("x", P.l - 8); t.setAttribute("y", gy + 4);
        t.setAttribute("text-anchor", "end"); t.setAttribute("font-size", "11"); t.setAttribute("fill", C.muted); t.textContent = fmt(gv, state.metric); svg.appendChild(t);
      }
      var step = Math.max(1, Math.ceil(vals.length / 8));
      months.forEach(function (m, i) {
        var isLast = i === months.length - 1;
        if (!isLast && (i % step !== 0 || months.length - 1 - i < step / 2)) return;  /* skip a tick that would crowd the last label */
        var t = document.createElementNS(svgNS, "text"); t.setAttribute("x", x(i)); t.setAttribute("y", H - 14);
        t.setAttribute("text-anchor", i === 0 ? "start" : (i === months.length - 1 ? "end" : "middle"));  /* edge labels hug the edge, never cross the viewBox */
        t.setAttribute("font-size", "11"); t.setAttribute("fill", C.muted); t.textContent = m; svg.appendChild(t);
      });
      var mark = S.months.indexOf("2024-03");
      if (mark >= start && mark <= end && sid !== "platform") {
        var vl = document.createElementNS(svgNS, "line"); var mx = x(mark - start);
        vl.setAttribute("x1", mx); vl.setAttribute("x2", mx); vl.setAttribute("y1", P.t); vl.setAttribute("y2", H - P.b);
        vl.setAttribute("stroke", C.faint); vl.setAttribute("stroke-dasharray", "4 4"); svg.appendChild(vl);
      }
      var d = vals.map(function (v, i) { return (i ? "L" : "M") + x(i).toFixed(1) + " " + y(v).toFixed(1); }).join(" ");
      var path = document.createElementNS(svgNS, "path"); path.setAttribute("d", d); path.setAttribute("fill", "none");
      path.setAttribute("stroke", sid === "S07" || sid === "S08" ? C.amber : C.navy); path.setAttribute("stroke-width", "2.5"); svg.appendChild(path);
      if (vals.length <= 12) vals.forEach(function (v, i) {
        var c = document.createElementNS(svgNS, "circle"); c.setAttribute("cx", x(i)); c.setAttribute("cy", y(v)); c.setAttribute("r", "3.5");
        c.setAttribute("fill", sid === "S07" || sid === "S08" ? C.amber : C.navy); svg.appendChild(c);
      });
      var first = vals[0], last = vals[vals.length - 1];
      var range = Math.max.apply(null, vals) - Math.min.apply(null, vals);
      var verdict;
      if (state.metric === "margin") {
        verdict = range < 4 ? "Inside this window the margin moves " + range.toFixed(1) + " points - reads as noise."
          : "Inside this window the margin spans " + range.toFixed(1) + " points, from " + fmt(Math.max.apply(null, vals), "margin") + " to " + fmt(Math.min.apply(null, vals), "margin") + " - a step, not a wobble.";
      } else {
        var chg = first ? ((last - first) / first * 100) : 0;
        verdict = state.metric.charAt(0).toUpperCase() + state.metric.slice(1) + " changes " + (chg >= 0 ? "+" : "") + chg.toFixed(0) + "% across this window" + (state.metric !== "margin" && sid !== "platform" ? " - volume and revenue are the numbers that stayed calm while margin broke." : ".");
      }
      read.textContent = state.win + "-month window ending " + S.months[end] + ". " + verdict;
    }
    draw();
  });
})();
