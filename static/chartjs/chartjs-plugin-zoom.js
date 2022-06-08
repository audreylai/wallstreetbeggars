/*!
 * chartjs-plugin-zoom v1.2.1
 * undefined
 * (c) 2016-2022 chartjs-plugin-zoom Contributors
 * Released under the MIT License
 */
! function(e, n) {
    "object" == typeof exports && "undefined" != typeof module ? module.exports = n(require("chart.js"), require("hammerjs"), require("chart.js/helpers")) : "function" == typeof define && define.amd ? define(["chart.js", "hammerjs", "chart.js/helpers"], n) : (e = "undefined" != typeof globalThis ? globalThis : e || self).ChartZoom = n(e.Chart, e.Hammer, e.Chart.helpers)
}(this, (function(e, n, t) {
    "use strict";

    function o(e) {
        return e && "object" == typeof e && "default" in e ? e : {
            default: e
        }
    }
    var a = o(n);
    const i = e => e && e.enabled && e.modifierKey,
        c = (e, n) => e && n[e + "Key"],
        r = (e, n) => e && !n[e + "Key"];

    function l(e, n, t) {
        return void 0 === e || ("string" == typeof e ? -1 !== e.indexOf(n) : "function" == typeof e && -1 !== e({
            chart: t
        }).indexOf(n))
    }

    function s(e, n, o) {
        const a = function({
            x: e,
            y: n
        }, t) {
            const o = t.scales,
                a = Object.keys(o);
            for (let t = 0; t < a.length; t++) {
                const i = o[a[t]];
                if (n >= i.top && n <= i.bottom && e >= i.left && e <= i.right) return i
            }
            return null
        }(n, o);
        if (a && l(e, a.axis, o)) return [a];
        const i = [];
        return t.each(o.scales, (function(n) {
            l(e, n.axis, o) || i.push(n)
        })), i
    }
    const m = new WeakMap;

    function u(e) {
        let n = m.get(e);
        return n || (n = {
            originalScaleLimits: {},
            updatedScaleLimits: {},
            handlers: {},
            panDelta: {}
        }, m.set(e, n)), n
    }

    function d(e, n, t) {
        const o = e.max - e.min,
            a = o * (n - 1),
            i = e.isHorizontal() ? t.x : t.y,
            c = Math.max(0, Math.min(1, (e.getValueForPixel(i) - e.min) / o || 0));
        return {
            min: a * c,
            max: a * (1 - c)
        }
    }

    function f(e, n, o, a, i) {
        let c = o[a];
        if ("original" === c) {
            const o = e.originalScaleLimits[n.id][a];
            c = t.valueOrDefault(o.options, o.scale)
        }
        return t.valueOrDefault(c, i)
    }

    function h(e, {
        min: n,
        max: t
    }, o, a = !1) {
        const i = u(e.chart),
            {
                id: c,
                axis: r,
                options: l
            } = e,
            s = o && (o[c] || o[r]) || {},
            {
                minRange: m = 0
            } = s,
            d = f(i, e, s, "min", -1 / 0),
            h = f(i, e, s, "max", 1 / 0),
            p = Math.max(n, d),
            x = Math.min(t, h),
            g = a ? Math.max(x - p, m) : e.max - e.min;
        if (x - p !== g)
            if (d > x - g) n = p, t = p + g;
            else if (h < p + g) t = x, n = x - g;
        else {
            const e = (g - x + p) / 2;
            n = p - e, t = x + e
        } else n = p, t = x;
        return l.min = n, l.max = t, i.updatedScaleLimits[e.id] = {
            min: n,
            max: t
        }, e.parse(n) !== e.min || e.parse(t) !== e.max
    }
    const p = e => 0 === e || isNaN(e) ? 0 : e < 0 ? Math.min(Math.round(e), -1) : Math.max(Math.round(e), 1);
    const x = {
        second: 500,
        minute: 3e4,
        hour: 18e5,
        day: 432e5,
        week: 3024e5,
        month: 1296e6,
        quarter: 5184e6,
        year: 157248e5
    };

    function g(e, n, t, o = !1) {
        const {
            min: a,
            max: i,
            options: c
        } = e, r = c.time && c.time.round, l = x[r] || 0, s = e.getValueForPixel(e.getPixelForValue(a + l) - n), m = e.getValueForPixel(e.getPixelForValue(i + l) - n), {
            min: u = -1 / 0,
            max: d = 1 / 0
        } = o && t && t[e.axis] || {};
        return !!(isNaN(s) || isNaN(m) || s < u || m > d) || h(e, {
            min: s,
            max: m
        }, t, o)
    }

    function b(e, n, t) {
        return g(e, n, t, !0)
    }
    const y = {
            category: function(e, n, t, o) {
                const a = d(e, n, t);
                return e.min === e.max && n < 1 && function(e) {
                    const n = e.getLabels().length - 1;
                    e.min > 0 && (e.min -= 1), e.max < n && (e.max += 1)
                }(e), h(e, {
                    min: e.min + p(a.min),
                    max: e.max - p(a.max)
                }, o, !0)
            },
            default: function(e, n, t, o) {
                const a = d(e, n, t);
                return h(e, {
                    min: e.min + a.min,
                    max: e.max - a.max
                }, o, !0)
            }
        },
        v = {
            category: function(e, n, t) {
                const o = e.getLabels().length - 1;
                let {
                    min: a,
                    max: i
                } = e;
                const c = Math.max(i - a, 1),
                    r = Math.round(function(e) {
                        return e.isHorizontal() ? e.width : e.height
                    }(e) / Math.max(c, 10)),
                    l = Math.round(Math.abs(n / r));
                let s;
                return n < -r ? (i = Math.min(i + l, o), a = 1 === c ? i : i - c, s = i === o) : n > r && (a = Math.max(0, a - l), i = 1 === c ? a : a + c, s = 0 === a), h(e, {
                    min: a,
                    max: i
                }, t) || s
            },
            default: g,
            logarithmic: b,
            timeseries: b
        };

    function z(e, n) {
        t.each(e, ((t, o) => {
            n[o] || delete e[o]
        }))
    }

    function M(e, n) {
        const {
            scales: o
        } = e, {
            originalScaleLimits: a,
            updatedScaleLimits: i
        } = n;
        return t.each(o, (function(e) {
            (function(e, n, t) {
                const {
                    id: o,
                    options: {
                        min: a,
                        max: i
                    }
                } = e;
                if (!n[o] || !t[o]) return !0;
                const c = t[o];
                return c.min !== a || c.max !== i
            })(e, a, i) && (a[e.id] = {
                min: {
                    scale: e.min,
                    options: e.options.min
                },
                max: {
                    scale: e.max,
                    options: e.options.max
                }
            })
        })), z(a, o), z(i, o), a
    }

    function k(e, n, o, a) {
        const i = y[e.type] || y.default;
        t.callback(i, [e, n, o, a])
    }

    function w(e) {
        const n = e.chartArea;
        return {
            x: (n.left + n.right) / 2,
            y: (n.top + n.bottom) / 2
        }
    }

    function S(e, n, o = "none") {
        const {
            x: a = 1,
            y: i = 1,
            focalPoint: c = w(e)
        } = "number" == typeof n ? {
            x: n,
            y: n
        } : n, r = u(e), {
            options: {
                limits: m,
                zoom: d
            }
        } = r, {
            mode: f = "xy",
            overScaleMode: h
        } = d || {};
        M(e, r);
        const p = 1 !== a && l(f, "x", e),
            x = 1 !== i && l(f, "y", e),
            g = h && s(h, c, e);
        t.each(g || e.scales, (function(e) {
            e.isHorizontal() && p ? k(e, a, c, m) : !e.isHorizontal() && x && k(e, i, c, m)
        })), e.update(o), t.callback(d.onZoom, [{
            chart: e
        }])
    }

    function P(e, n, t) {
        const o = e.getValueForPixel(n),
            a = e.getValueForPixel(t);
        return {
            min: Math.min(o, a),
            max: Math.max(o, a)
        }
    }

    function C(e) {
        const n = u(e);
        let o = 1,
            a = 1;
        return t.each(e.scales, (function(e) {
            const i = function(e, n) {
                const o = e.originalScaleLimits[n];
                if (!o) return;
                const {
                    min: a,
                    max: i
                } = o;
                return t.valueOrDefault(i.options, i.scale) - t.valueOrDefault(a.options, a.scale)
            }(n, e.id);
            if (i) {
                const n = Math.round(i / (e.max - e.min) * 100) / 100;
                o = Math.min(o, n), a = Math.max(a, n)
            }
        })), o < 1 ? o : a
    }

    function j(e, n, o, a) {
        const {
            panDelta: i
        } = a, c = i[e.id] || 0;
        t.sign(c) === t.sign(n) && (n += c);
        const r = v[e.type] || v.default;
        t.callback(r, [e, n, o]) ? i[e.id] = 0 : i[e.id] = n
    }

    function Z(e, n, o, a = "none") {
        const {
            x: i = 0,
            y: c = 0
        } = "number" == typeof n ? {
            x: n,
            y: n
        } : n, r = u(e), {
            options: {
                pan: s,
                limits: m
            }
        } = r, {
            mode: d = "xy",
            onPan: f
        } = s || {};
        M(e, r);
        const h = 0 !== i && l(d, "x", e),
            p = 0 !== c && l(d, "y", e);
        t.each(o || e.scales, (function(e) {
            e.isHorizontal() && h ? j(e, i, m, r) : !e.isHorizontal() && p && j(e, c, m, r)
        })), e.update(a), t.callback(f, [{
            chart: e
        }])
    }

    function L(e) {
        const n = u(e),
            t = {};
        for (const o of Object.keys(e.scales)) {
            const {
                min: e,
                max: a
            } = n.originalScaleLimits[o] || {
                min: {},
                max: {}
            };
            t[o] = {
                min: e.scale,
                max: a.scale
            }
        }
        return t
    }

    function R(e, n) {
        const {
            handlers: t
        } = u(e), o = t[n];
        o && o.target && (o.target.removeEventListener(n, o), delete t[n])
    }

    function Y(e, n, t, o) {
        const {
            handlers: a,
            options: i
        } = u(e), c = a[t];
        c && c.target === n || (R(e, t), a[t] = n => o(e, n, i), a[t].target = n, n.addEventListener(t, a[t]))
    }

    function O(e, n) {
        const t = u(e);
        t.dragStart && (t.dragging = !0, t.dragEnd = n, e.update("none"))
    }

    function T(e, n, o) {
        const {
            onZoomStart: a,
            onZoomRejected: i
        } = o;
        if (a) {
            const {
                left: o,
                top: c
            } = n.target.getBoundingClientRect(), r = {
                x: n.clientX - o,
                y: n.clientY - c
            };
            if (!1 === t.callback(a, [{
                    chart: e,
                    event: n,
                    point: r
                }])) return t.callback(i, [{
                chart: e,
                event: n
            }]), !1
        }
    }

    function X(e, n) {
        const o = u(e),
            {
                pan: a,
                zoom: l = {}
            } = o.options;
        if (c(i(a), n) || r(i(l.drag), n)) return t.callback(l.onZoomRejected, [{
            chart: e,
            event: n
        }]);
        !1 !== T(e, n, l) && (o.dragStart = n, Y(e, e.canvas, "mousemove", O))
    }

    function D(e, n, t, o) {
        const {
            left: a,
            top: i
        } = t.target.getBoundingClientRect(), c = l(n, "x", e), r = l(n, "y", e);
        let {
            top: s,
            left: m,
            right: u,
            bottom: d,
            width: f,
            height: h
        } = e.chartArea;
        c && (m = Math.min(t.clientX, o.clientX) - a, u = Math.max(t.clientX, o.clientX) - a), r && (s = Math.min(t.clientY, o.clientY) - i, d = Math.max(t.clientY, o.clientY) - i);
        const p = u - m,
            x = d - s;
        return {
            left: m,
            top: s,
            right: u,
            bottom: d,
            width: p,
            height: x,
            zoomX: c && p ? 1 + (f - p) / f : 1,
            zoomY: r && x ? 1 + (h - x) / h : 1
        }
    }

    function E(e, n) {
        const o = u(e);
        if (!o.dragStart) return;
        R(e, "mousemove");
        const {
            mode: a,
            onZoomComplete: i,
            drag: {
                threshold: c = 0
            }
        } = o.options.zoom, r = D(e, a, o.dragStart, n), s = l(a, "x", e) ? r.width : 0, m = l(a, "y", e) ? r.height : 0, d = Math.sqrt(s * s + m * m);
        if (o.dragStart = o.dragEnd = null, d <= c) return o.dragging = !1, void e.update("none");
        ! function(e, n, o, a = "none") {
            const i = u(e),
                {
                    options: {
                        limits: c,
                        zoom: r
                    }
                } = i,
                {
                    mode: s = "xy"
                } = r;
            M(e, i);
            const m = l(s, "x", e),
                d = l(s, "y", e);
            t.each(e.scales, (function(e) {
                e.isHorizontal() && m ? h(e, P(e, n.x, o.x), c, !0) : !e.isHorizontal() && d && h(e, P(e, n.y, o.y), c, !0)
            })), e.update(a), t.callback(r.onZoom, [{
                chart: e
            }])
        }(e, {
            x: r.left,
            y: r.top
        }, {
            x: r.right,
            y: r.bottom
        }, "zoom"), setTimeout((() => o.dragging = !1), 500), t.callback(i, [{
            chart: e
        }])
    }

    function F(e, n) {
        const {
            handlers: {
                onZoomComplete: o
            },
            options: {
                zoom: a
            }
        } = u(e);
        if (! function(e, n, o) {
                if (r(i(o.wheel), n)) t.callback(o.onZoomRejected, [{
                    chart: e,
                    event: n
                }]);
                else if (!1 !== T(e, n, o) && (n.cancelable && n.preventDefault(), void 0 !== n.deltaY)) return !0
            }(e, n, a)) return;
        const c = n.target.getBoundingClientRect(),
            l = 1 + (n.deltaY >= 0 ? -a.wheel.speed : a.wheel.speed);
        S(e, {
            x: l,
            y: l,
            focalPoint: {
                x: n.clientX - c.left,
                y: n.clientY - c.top
            }
        }), o && o()
    }

    function H(e, n, o, a) {
        o && (u(e).handlers[n] = function(e, n) {
            let t;
            return function() {
                return clearTimeout(t), t = setTimeout(e, n), n
            }
        }((() => t.callback(o, [{
            chart: e
        }])), a))
    }

    function V(e, n) {
        return function(o, a) {
            const {
                pan: l,
                zoom: s = {}
            } = n.options;
            if (!l || !l.enabled) return !1;
            const m = a && a.srcEvent;
            return !m || (!(!n.panning && "mouse" === a.pointerType && (r(i(l), m) || c(i(s.drag), m))) || (t.callback(l.onPanRejected, [{
                chart: e,
                event: a
            }]), !1))
        }
    }

    function B(e, n, t) {
        if (n.scale) {
            const {
                center: o,
                pointers: a
            } = t, i = 1 / n.scale * t.scale, c = t.target.getBoundingClientRect(), r = function(e, n) {
                const t = Math.abs(e.clientX - n.clientX),
                    o = Math.abs(e.clientY - n.clientY),
                    a = t / o;
                let i, c;
                return a > .3 && a < 1.7 ? i = c = !0 : t > o ? i = !0 : c = !0, {
                    x: i,
                    y: c
                }
            }(a[0], a[1]), s = n.options.zoom.mode;
            S(e, {
                x: r.x && l(s, "x", e) ? i : 1,
                y: r.y && l(s, "y", e) ? i : 1,
                focalPoint: {
                    x: o.x - c.left,
                    y: o.y - c.top
                }
            }), n.scale = t.scale
        }
    }

    function K(e, n, t) {
        const o = n.delta;
        o && (n.panning = !0, Z(e, {
            x: t.deltaX - o.x,
            y: t.deltaY - o.y
        }, n.panScales), n.delta = {
            x: t.deltaX,
            y: t.deltaY
        })
    }
    const N = new WeakMap;

    function q(e, n) {
        const o = u(e),
            i = e.canvas,
            {
                pan: c,
                zoom: r
            } = n,
            l = new a.default.Manager(i);
        r && r.pinch.enabled && (l.add(new a.default.Pinch), l.on("pinchstart", (() => function(e, n) {
            n.options.zoom.pinch.enabled && (n.scale = 1)
        }(0, o))), l.on("pinch", (n => B(e, o, n))), l.on("pinchend", (n => function(e, n, o) {
            n.scale && (B(e, n, o), n.scale = null, t.callback(n.options.zoom.onZoomComplete, [{
                chart: e
            }]))
        }(e, o, n)))), c && c.enabled && (l.add(new a.default.Pan({
            threshold: c.threshold,
            enable: V(e, o)
        })), l.on("panstart", (n => function(e, n, o) {
            const {
                enabled: a,
                overScaleMode: i,
                onPanStart: c,
                onPanRejected: r
            } = n.options.pan;
            if (!a) return;
            const l = o.target.getBoundingClientRect(),
                m = {
                    x: o.center.x - l.left,
                    y: o.center.y - l.top
                };
            if (!1 === t.callback(c, [{
                    chart: e,
                    event: o,
                    point: m
                }])) return t.callback(r, [{
                chart: e,
                event: o
            }]);
            n.panScales = i && s(i, m, e), n.delta = {
                x: 0,
                y: 0
            }, clearTimeout(n.panEndTimeout), K(e, n, o)
        }(e, o, n))), l.on("panmove", (n => K(e, o, n))), l.on("panend", (() => function(e, n) {
            n.delta = null, n.panning && (n.panEndTimeout = setTimeout((() => n.panning = !1), 500), t.callback(n.options.pan.onPanComplete, [{
                chart: e
            }]))
        }(e, o)))), N.set(e, l)
    }
    var W = {
        id: "zoom",
        version: "1.2.1",
        defaults: {
            pan: {
                enabled: !1,
                mode: "xy",
                threshold: 10,
                modifierKey: null
            },
            zoom: {
                wheel: {
                    enabled: !1,
                    speed: .1,
                    modifierKey: null
                },
                drag: {
                    enabled: !1,
                    modifierKey: null
                },
                pinch: {
                    enabled: !1
                },
                mode: "xy"
            }
        },
        start: function(e, n, o) {
            u(e).options = o, Object.prototype.hasOwnProperty.call(o.zoom, "enabled") && console.warn("The option `zoom.enabled` is no longer supported. Please use `zoom.wheel.enabled`, `zoom.drag.enabled`, or `zoom.pinch.enabled`."), a.default && q(e, o), e.pan = (n, t, o) => Z(e, n, t, o), e.zoom = (n, t) => S(e, n, t), e.zoomScale = (n, t, o) => function(e, n, t, o = "none") {
                M(e, u(e)), h(e.scales[n], t, void 0, !0), e.update(o)
            }(e, n, t, o), e.resetZoom = n => function(e, n = "default") {
                const o = u(e),
                    a = M(e, o);
                t.each(e.scales, (function(e) {
                    const n = e.options;
                    a[e.id] ? (n.min = a[e.id].min.options, n.max = a[e.id].max.options) : (delete n.min, delete n.max)
                })), e.update(n), t.callback(o.options.zoom.onZoomComplete, [{
                    chart: e
                }])
            }(e, n), e.getZoomLevel = () => C(e), e.getInitialScaleBounds = () => L(e), e.isZoomedOrPanned = () => function(e) {
                const n = L(e);
                for (const t of Object.keys(e.scales)) {
                    const {
                        min: o,
                        max: a
                    } = n[t];
                    if (void 0 !== o && e.scales[t].min !== o) return !0;
                    if (void 0 !== a && e.scales[t].max !== a) return !0
                }
                return !1
            }(e)
        },
        beforeEvent(e) {
            const n = u(e);
            if (n.panning || n.dragging) return !1
        },
        beforeUpdate: function(e, n, t) {
            u(e).options = t,
                function(e, n) {
                    const t = e.canvas,
                        {
                            wheel: o,
                            drag: a,
                            onZoomComplete: i
                        } = n.zoom;
                    o.enabled ? (Y(e, t, "wheel", F), H(e, "onZoomComplete", i, 250)) : R(e, "wheel"), a.enabled ? (Y(e, t, "mousedown", X), Y(e, t.ownerDocument, "mouseup", E)) : (R(e, "mousedown"), R(e, "mousemove"), R(e, "mouseup"))
                }(e, t)
        },
        beforeDatasetsDraw: function(e, n, t) {
            const {
                dragStart: o,
                dragEnd: a
            } = u(e);
            if (a) {
                const {
                    left: n,
                    top: i,
                    width: c,
                    height: r
                } = D(e, t.zoom.mode, o, a), l = t.zoom.drag, s = e.ctx;
                s.save(), s.beginPath(), s.fillStyle = l.backgroundColor || "rgba(225,225,225,0.3)", s.fillRect(n, i, c, r), l.borderWidth > 0 && (s.lineWidth = l.borderWidth, s.strokeStyle = l.borderColor || "rgba(225,225,225)", s.strokeRect(n, i, c, r)), s.restore()
            }
        },
        stop: function(e) {
            ! function(e) {
                R(e, "mousedown"), R(e, "mousemove"), R(e, "mouseup"), R(e, "wheel"), R(e, "click")
            }(e), a.default && function(e) {
                    const n = N.get(e);
                    n && (n.remove("pinchstart"), n.remove("pinch"), n.remove("pinchend"), n.remove("panstart"), n.remove("pan"), n.remove("panend"), n.destroy(), N.delete(e))
                }(e),
                function(e) {
                    m.delete(e)
                }(e)
        },
        panFunctions: v,
        zoomFunctions: y
    };
    return e.Chart.register(W), W
}));