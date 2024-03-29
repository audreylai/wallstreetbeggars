/*!
 * chartjs-chart-treemap v2.0.2
 * https://chartjs-chart-treemap.pages.dev/
 * (c) 2021 Jukka Kurkela
 * Released under the MIT license
 */
! function(t, e) {
	"object" == typeof exports && "undefined" != typeof module ? e(exports, require("chart.js"), require("chart.js/helpers")) : "function" == typeof define && define.amd ? define(["exports", "chart.js", "chart.js/helpers"], e) : e((t = "undefined" != typeof globalThis ? globalThis : t || self)["chartjs-chart-treemap"] = {}, t.Chart, t.Chart.helpers)
}(this, (function(t, e, n) {
	"use strict";

	function i(t) {
			const e = [...t],
					n = [];
			for (; e.length;) {
					const t = e.pop();
					Array.isArray(t) ? e.push(...t) : n.push(t)
			}
			return n.reverse()
	}

	function r(t, e, n, i, r) {
			const o = Object.create(null),
					s = Object.create(null),
					a = [];
			let l, h, u, c;
			for (h = 0, u = t.length; h < u; ++h) c = t[h], i && c[i] !== r || (l = c[e] || "", l in o || (o[l] = 0, s[l] = []), o[l] += +c[n], s[l].push(c));
			return Object.keys(o).forEach((t => {
					c = {
							children: s[t]
					}, c[n] = +o[t], c[e] = t, i && (c[i] = r), a.push(c)
			})), a
	}

	function o(t) {
			const e = typeof t;
			return "function" === e || "object" === e && !!t
	}

	function s(t, e) {
			let n, i = t.length;
			if (!i) return e;
			const r = o(t[0]);
			for (e = r ? e : "v", n = 0, i = t.length; n < i; ++n) r ? t[n]._idx = n : t[n] = {
					v: t[n],
					_idx: n
			};
			return e
	}

	function a(t, e) {
			e ? t.sort(((t, n) => +n[e] - +t[e])) : t.sort(((t, e) => +e - +t))
	}

	function l(t, e) {
			let n, i, r;
			for (n = 0, i = 0, r = t.length; i < r; ++i) n += e ? +t[i][e] : +t[i];
			return n
	}

	function h(t, e) {
			const n = e.split(".");
			if (!t.split(".").reduce(((t, e, i) => t && e <= n[i]), !0)) throw new Error(`Chart.js v${e} is not supported. v${t} or newer is required.`)
	}

	function u(t, e) {
			return +(Math.round(t + "e+" + e) + "e-" + e) || 0
	}

	function c(t, e, n, i) {
			const r = t._normalized,
					o = e * r / n,
					s = Math.sqrt(r * o),
					a = r / s;
			return {
					d1: s,
					d2: a,
					w: "_ix" === i ? s : a,
					h: "_ix" === i ? a : s
			}
	}
	const d = (t, e) => u(t.rtl ? t.x + t.w - t._ix - e : t.x + t._ix, 4);

	function p(t, e, n, i) {
			const r = {
					x: d(t, n.w),
					y: u(t.y + t._iy, 4),
					w: u(n.w, 4),
					h: u(n.h, 4),
					a: u(e._normalized, 4),
					v: e.value,
					s: i,
					_data: e._data
			};
			return e.group && (r.g = e.group, r.l = e.level, r.gs = e.groupSum), r
	}
	class g {
			constructor(t) {
					const e = this;
					t = t || {
							w: 1,
							h: 1
					}, e.rtl = !!t.rtl, e.x = t.x || t.left || 0, e.y = t.y || t.top || 0, e._ix = 0, e._iy = 0, e.w = t.w || t.width || t.right - t.left, e.h = t.h || t.height || t.bottom - t.top
			}
			get area() {
					return this.w * this.h
			}
			get iw() {
					return this.w - this._ix
			}
			get ih() {
					return this.h - this._iy
			}
			get dir() {
					const t = this.ih;
					return t <= this.iw && t > 0 ? "y" : "x"
			}
			get side() {
					return "x" === this.dir ? this.iw : this.ih
			}
			map(t) {
					const e = this,
							n = [],
							i = t.nsum,
							r = t.get(),
							o = e.dir,
							s = e.side,
							a = s * s,
							l = "x" === o ? "_ix" : "_iy",
							h = i * i;
					let u = 0,
							d = 0;
					for (const i of r) {
							const r = c(i, a, h, l);
							d += r.d1, u = Math.max(u, r.d2), n.push(p(e, i, r, t.sum)), e[l] += r.d1
					}
					return e["y" === o ? "_ix" : "_iy"] += u, e[l] -= d, n
			}
	}
	const f = Math.min,
			m = Math.max;

	function y(t, e) {
			const n = +e[t.key],
					i = n * t.ratio;
			return e._normalized = i, {
					min: f(t.min, n),
					max: m(t.max, n),
					sum: t.sum + n,
					nmin: f(t.nmin, i),
					nmax: m(t.nmax, i),
					nsum: t.nsum + i
			}
	}

	function x(t, e, n) {
			t._arr.push(e),
					function(t, e) {
							Object.assign(t, e)
					}(t, n)
	}
	class v {
			constructor(t, e) {
					const n = this;
					n.key = t, n.ratio = e, n.reset()
			}
			get length() {
					return this._arr.length
			}
			reset() {
					const t = this;
					t._arr = [], t._hist = [], t.sum = 0, t.nsum = 0, t.min = 1 / 0, t.max = -1 / 0, t.nmin = 1 / 0, t.nmax = -1 / 0
			}
			push(t) {
					x(this, t, y(this, t))
			}
			pushIf(t, e, ...n) {
					const i = y(this, t);
					if (!e((r = this, {
									min: r.min,
									max: r.max,
									sum: r.sum,
									nmin: r.nmin,
									nmax: r.nmax,
									nsum: r.nsum
							}), i, n)) return t;
					var r;
					x(this, t, i)
			}
			get() {
					return this._arr
			}
	}

	function w(t, e, n) {
			if (0 === t.sum) return !0;
			const [i] = n, r = t.nsum * t.nsum, o = e.nsum * e.nsum, s = i * i, a = Math.max(s * t.nmax / r, r / (s * t.nmin));
			return Math.max(s * e.nmax / o, o / (s * e.nmin)) <= a
	}

	function b(t, e, n, r, o, h) {
			t = t || [];
			const u = [],
					c = new g(e),
					d = new v("value", c.area / l(t, n));
			let p = c.side;
			const f = t.length;
			let m, y;
			if (!f) return u;
			const x = t.slice();
			n = s(x, n), a(x, n);
			const b = t => r && x[t][r];
			for (m = 0; m < f; ++m) y = {
					value: (_ = m, n ? +x[_][n] : +x[_]),
					groupSum: h,
					_data: t[x[m]._idx],
					level: void 0,
					group: void 0
			}, r && (y.level = o, y.group = b(m)), y = d.pushIf(y, w, p), y && (u.push(c.map(d)), p = c.side, d.reset(), d.push(y));
			var _;
			return d.length && u.push(c.map(d)), i(u)
	}

	function _(t, e) {
			if (!e) return !1;
			const n = t.width || t.w,
					i = t.height || t.h,
					r = 2 * e.lineHeight;
			return n > r && i > r
	}

	function O(t, e, i, r, o) {
			t.save(), t.beginPath(), t.rect(e.x, e.y, e.width, e.height), t.clip(), "l" in i && i.l !== o ? r.captions && r.captions.display && function(t, e, i) {
					const r = i.options,
							o = r.captions || {},
							s = r.borderWidth || 0,
							a = n.valueOrDefault(r.spacing, 0) + s,
							l = (i.active ? o.hoverColor : o.color) || o.color,
							h = o.padding,
							u = o.align || (r.rtl ? "right" : "left"),
							c = (i.active ? o.hoverFont : o.font) || o.font,
							d = n.toFont(c),
							p = D(i, u, h, s);
					t.fillStyle = l, t.font = d.string, t.textAlign = u, t.textBaseline = "middle", t.fillText(o.formatter || e.g, p, i.y + h + a + d.lineHeight / 2)
			}(t, i, e) : function(t, e, i) {
					const r = i.options,
							o = r.labels;
					if (!o || !o.display) return;
					const s = (i.active ? o.hoverColor : o.color) || o.color,
							a = (i.active ? o.hoverFont : o.font) || o.font,
							l = n.toFont(a),
							h = l.lineHeight,
							u = o.formatter;
					if (u) {
							const e = n.isArray(u) ? u : [u],
									a = function(t, e, n, i) {
											const r = t.labels,
													o = t.borderWidth || 0,
													{
															align: s,
															position: a,
															padding: l
													} = r;
											let h, u;
											h = D(e, s, l, o), u = "top" === a ? e.y + l + o : "bottom" === a ? e.y + e.height - l - o - (n.length - 1) * i : e.y + e.height / 2 - n.length * i / 4;
											return {
													x: h,
													y: u
											}
									}(r, i, e, h);
							t.font = l.string, t.textAlign = o.align, t.textBaseline = o.position, t.fillStyle = s, e.forEach(((e, n) => t.fillText(e, a.x, a.y + n * h)))
					}
			}(t, 0, e), t.restore()
	}

	function C(t, e) {
			const n = e.options.dividers || {},
					i = e.width || e.w,
					r = e.height || e.h;
			if (t.save(), t.strokeStyle = n.lineColor || "black", t.lineCap = n.lineCapStyle, t.setLineDash(n.lineDash || []), t.lineDashOffset = n.lineDashOffset, t.lineWidth = n.lineWidth, t.beginPath(), i > r) {
					const n = i / 2;
					t.moveTo(e.x + n, e.y), t.lineTo(e.x + n, e.y + r)
			} else {
					const n = r / 2;
					t.moveTo(e.x, e.y + n), t.lineTo(e.x + i, e.y + n)
			}
			t.stroke(), t.restore()
	}

	function D(t, e, n, i) {
			return "left" === e ? t.x + n + i : "right" === e ? t.x + t.width - n - i : t.x + t.width / 2
	}
	class k extends e.DatasetController {
			constructor(t, e) {
					super(t, e), this._rect = void 0, this._key = void 0, this._groups = void 0
			}
			initialize() {
					this.enableOptionSharing = !0, super.initialize()
			}
			update(t) {
					const e = this,
							i = e.getMeta(),
							o = e.getDataset(),
							s = o.groups || (o.groups = []),
							a = o.captions ? o.captions : {},
							l = e.chart.chartArea,
							h = o.key || "",
							u = !!o.rtl,
							c = {
									x: l.left,
									y: l.top,
									w: l.right - l.left,
									h: l.bottom - l.top,
									rtl: u
							};
					var d, p;
					"reset" !== t && (d = e._rect, p = c, d && p && d.x === p.x && d.y === p.y && d.w === p.w && d.h === p.h) && e._key === h && ! function(t, e) {
							let n, i;
							if (t.lenght !== e.length) return !0;
							for (n = 0, i = t.length; n < i; ++n)
									if (t[n] !== e[n]) return !0;
							return !1
					}(e._groups, s) || (e._rect = c, e._groups = s.slice(), e._key = h, o.data = function(t, e, i) {
							const o = t.key || "";
							let s = t.tree || [];
							const a = t.groups || [],
									l = a.length,
									h = n.valueOrDefault(t.spacing, 0) + n.valueOrDefault(t.borderWidth, 0),
									u = i.font || {},
									c = n.toFont(u),
									d = n.valueOrDefault(i.padding, 3);
							return !s.length && t.data.length && (s = t.tree = t.data), l ? function t(e, u, p, g) {
									const f = a[e],
											m = e > 0 && a[e - 1],
											y = b(r(s, f, o, m, p), u, o, f, e, g),
											x = y.slice();
									let v;
									return e < l - 1 && y.forEach((r => {
											v = {
													x: r.x + h,
													y: r.y + h,
													w: r.w - 2 * h,
													h: r.h - 2 * h
											}, n.valueOrDefault(i.display, !0) && _(r, c) && (v.y += c.lineHeight + 2 * d, v.h -= c.lineHeight + 2 * d), x.push(...t(e + 1, v, r.g, r.s))
									})), x
							}(0, e) : b(s, e, o)
					}(o, c, a), e._dataCheck(), e._resyncElements()), e.updateElements(i.data, 0, i.data.length, t)
			}
			resolveDataElementOptions(t, e) {
					const i = super.resolveDataElementOptions(t, e),
							r = Object.isFrozen(i) ? Object.assign({}, i) : i;
					return r.font = n.toFont(i.captions.font), r
			}
			updateElements(t, e, n, i) {
					const r = this,
							o = "reset" === i,
							s = r.getDataset(),
							a = r._rect.options = r.resolveDataElementOptions(e, i),
							l = r.getSharedOptions(a),
							h = r.includeOptions(i, l);
					for (let a = e; a < e + n; a++) {
							const e = s.data[a],
									n = l || r.resolveDataElementOptions(a, i),
									u = n.spacing,
									c = 2 * u,
									d = {
											x: e.x + u,
											y: e.y + u,
											width: o ? 0 : e.w - c,
											height: o ? 0 : e.h - c,
											hidden: c > e.w || c > e.h
									};
							h && (d.options = n), r.updateElement(t[a], a, d, i)
					}
					r.updateSharedOptions(l, i, a)
			}
			_drawDividers(t, e, n) {
					for (let i = 0, r = n.length; i < r; ++i) {
							const r = n[i],
									o = e[i];
							(r.options.dividers || {}).display && o._data.children.length > 1 && C(t, r)
					}
			}
			_drawRects(t, e, n, i) {
					for (let r = 0, o = n.length; r < o; ++r) {
							const o = n[r],
									s = e[r];
							if (!o.hidden) {
									o.draw(t);
									const e = o.options;
									_(o, e.captions.font) && O(t, o, s, e, i)
							}
					}
			}
			draw() {
					const t = this,
							e = t.chart.ctx,
							n = t.getMeta().data || [],
							i = t.getDataset(),
							r = (i.groups || []).length - 1,
							o = i.data || [];
					t._drawRects(e, o, n, r), t._drawDividers(e, o, n)
			}
	}

	function j(t, e) {
			const {
					x: n,
					y: i,
					width: r,
					height: o
			} = t.getProps(["x", "y", "width", "height"], e);
			return {
					left: n,
					top: i,
					right: n + r,
					bottom: i + o
			}
	}

	function E(t, e, n) {
			return Math.max(Math.min(t, n), e)
	}

	function S(t) {
			const e = j(t),
					n = e.right - e.left,
					i = e.bottom - e.top,
					r = function(t, e, n) {
							let i, r, s, a;
							return o(t) ? (i = +t.top || 0, r = +t.right || 0, s = +t.bottom || 0, a = +t.left || 0) : i = r = s = a = +t || 0, {
									t: E(i, 0, n),
									r: E(r, 0, e),
									b: E(s, 0, n),
									l: E(a, 0, e)
							}
					}(t.options.borderWidth, n / 2, i / 2);
			return {
					outer: {
							x: e.left,
							y: e.top,
							w: n,
							h: i
					},
					inner: {
							x: e.left + r.l,
							y: e.top + r.t,
							w: n - r.l - r.r,
							h: i - r.t - r.b
					}
			}
	}

	function M(t, e, n, i) {
			const r = null === e,
					o = null === n,
					s = !(!t || r && o) && j(t, i);
			return s && (r || e >= s.left && e <= s.right) && (o || n >= s.top && n <= s.bottom)
	}
	k.id = "treemap", k.version = "2.0.2", k.defaults = {
			dataElementType: "treemap",
			animations: {
					numbers: {
							type: "number",
							properties: ["x", "y", "width", "height"]
					}
			},
			borderWidth: 0,
			spacing: .5,
			dividers: {
					display: !1,
					lineWidth: 1
			}
	}, k.descriptors = {
			_scriptable: !0,
			_indexable: !1
	}, k.overrides = {
			interaction: {
					mode: "point",
					intersect: !0
			},
			hover: {},
			plugins: {
					tooltip: {
							position: "treemap",
							intersect: !0,
							callbacks: {
									title(t) {
											if (t.length) {
													return t[0].dataset.key || ""
											}
											return ""
									},
									label(t) {
											const e = t.dataset,
													n = e.data[t.dataIndex],
													i = n.g || e.label;
											return (i ? i + ": " : "") + n.v
									}
							}
					}
			},
			scales: {
					x: {
							type: "linear",
							display: !1
					},
					y: {
							type: "linear",
							display: !1
					}
			}
	}, k.beforeRegister = function() {
			h("3.6", e.Chart.version)
	}, k.afterRegister = function() {
			const t = e.registry.plugins.get("tooltip");
			t && (t.positioners.treemap = function(t) {
					if (!t.length) return !1;
					return t[t.length - 1].element.tooltipPosition()
			})
	}, k.afterUnregister = function() {
			const t = e.registry.plugins.get("tooltip");
			t && delete t.positioners.treemap
	};
	class P extends e.Element {
			constructor(t) {
					super(), this.options = void 0, this.width = void 0, this.height = void 0, t && Object.assign(this, t)
			}
			draw(t) {
					const e = this.options,
							{
									inner: n,
									outer: i
							} = S(this);
					t.save(), i.w !== n.w || i.h !== n.h ? (t.beginPath(), t.rect(i.x, i.y, i.w, i.h), t.clip(), t.rect(n.x, n.y, n.w, n.h), t.fillStyle = e.backgroundColor, t.fill(), t.fillStyle = e.borderColor, t.fill("evenodd")) : (t.fillStyle = e.backgroundColor, t.fillRect(n.x, n.y, n.w, n.h)), t.restore()
			}
			inRange(t, e, n) {
					return M(this, t, e, n)
			}
			inXRange(t, e) {
					return M(this, t, null, e)
			}
			inYRange(t, e) {
					return M(this, null, t, e)
			}
			getCenterPoint(t) {
					const {
							x: e,
							y: n,
							width: i,
							height: r
					} = this.getProps(["x", "y", "width", "height"], t);
					return {
							x: e + i / 2,
							y: n + r / 2
					}
			}
			tooltipPosition() {
					return this.getCenterPoint()
			}
			getRange(t) {
					return "x" === t ? this.width / 2 : this.height / 2
			}
	}
	P.id = "treemap", P.defaults = {
			borderWidth: void 0,
			spacing: void 0,
			label: void 0,
			rtl: void 0,
			dividers: {
					display: !1,
					lineCapStyle: "butt",
					lineColor: "black",
					lineDash: void 0,
					lineDashOffset: 0,
					lineWidth: 0
			},
			captions: {
					align: void 0,
					color: void 0,
					display: !0,
					formatter: t => t.raw.g || "",
					font: {},
					padding: 3
			},
			labels: {
					align: "center",
					color: void 0,
					display: !1,
					formatter: t => t.raw.g ? [t.raw.g, t.raw.v] : t.raw.v,
					font: {},
					position: "middle",
					padding: 3
			}
	}, P.descriptors = {
			_scriptable: !0,
			_indexable: !1
	}, P.defaultRoutes = {
			backgroundColor: "backgroundColor",
			borderColor: "borderColor"
	}, e.Chart.register(k, P), t.flatten = i, t.group = r, t.index = s, t.isObject = o, t.requireVersion = h, t.sort = a, t.sum = l, Object.defineProperty(t, "__esModule", {
			value: !0
	})
}));