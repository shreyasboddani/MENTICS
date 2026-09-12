import { a as ARENA_AVATAR_PALETTES, i as ARENA_AVATAR_HAIR, n as ARENA_AVATAR_ACCENTS, o as ARENA_AVATAR_SKINS, r as ARENA_AVATAR_EYES, s as normalizeArenaAvatar } from "./arena-page-OnUfJ9b0.js";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
//#region frontend/src/arena-avatar-hair.js
var HEAD_PROFILE = [
	[0, -.34],
	[.11, -.32],
	[.21, -.25],
	[.26, -.14],
	[.29, 0],
	[.29, .13],
	[.24, .25],
	[.14, .32],
	[0, .35]
];
var DEPTH = .91;
var TAU = Math.PI * 2;
var ease = (t) => t * t * (3 - 2 * t);
var clamp = (v, a, b) => v < a ? a : v > b ? b : v;
var mix = (a, b, t) => a + (b - a) * t;
var SKULL = (() => {
	const source = [...HEAD_PROFILE].reverse(), points = [source[0]];
	for (let i = 1; i < source.length; i++) for (let k = 1; k <= 6; k++) {
		const t = k / 6, [x0, y0] = source[i - 1], [x1, y1] = source[i];
		points.push([mix(x0, x1, t), mix(y0, y1, t)]);
	}
	return points.map(([r, y], i) => {
		const a = points[Math.max(0, i - 1)], b = points[Math.min(points.length - 1, i + 1)];
		const dx = b[0] - a[0], dy = b[1] - a[1], length = Math.hypot(dx, dy) || 1;
		return {
			r,
			y,
			nr: -dy / length,
			ny: dx / length
		};
	});
})();
var at = (t) => {
	const i = clamp(Math.floor(t), 0, SKULL.length - 2), f = t - i, a = SKULL[i], b = SKULL[i + 1];
	return {
		r: mix(a.r, b.r, f),
		y: mix(a.y, b.y, f),
		nr: mix(a.nr, b.nr, f),
		ny: mix(a.ny, b.ny, f)
	};
};
var indexAt = (y) => {
	for (let i = 1; i < SKULL.length; i++) if (SKULL[i].y <= y) return i - 1 + (SKULL[i - 1].y - y) / (SKULL[i - 1].y - SKULL[i].y || 1);
	return SKULL.length - 1;
};
var radiusAt = (y) => at(indexAt(y)).r;
var STYLES = {
	buzz: {
		thick: .015,
		line: [
			.203,
			-.005,
			-.25
		],
		grain: 1.8,
		grainN: 44
	},
	fade: {
		thick: .062,
		line: [
			.212,
			.085,
			-.2
		],
		taper: .95,
		fringe: "crop",
		grain: 1.4
	},
	crop: {
		thick: .072,
		line: [
			.198,
			.03,
			-.218
		],
		fringe: "crop",
		grain: 1.5
	},
	wave: {
		thick: .088,
		line: [
			.205,
			.025,
			-.218
		],
		fringe: "swept",
		part: .9,
		sweep: .5,
		grain: 1.8
	},
	spike: {
		thick: .05,
		line: [
			.205,
			.04,
			-.205
		],
		fringe: "spike",
		spikes: 15
	},
	mohawk: {
		thick: .017,
		line: [
			.198,
			.125,
			-.205
		],
		crest: true,
		taper: .55,
		grain: 1.6,
		grainN: 40
	},
	undercut: {
		thick: .1,
		line: [
			.205,
			.145,
			-.12
		],
		taper: 1,
		sweep: .3,
		part: .5,
		grain: 1.4,
		quiff: .5
	},
	pixie: {
		thick: .066,
		line: [
			.198,
			-.005,
			-.215
		],
		fringe: "wisp",
		part: .5,
		grain: 1.3,
		points: .05
	},
	bob: {
		thick: .072,
		line: [
			.2,
			-.01,
			-.225
		],
		fringe: "blunt",
		part: .35,
		curtain: {
			end: -.44,
			back: -.58,
			flare: .13,
			spread: 1.95,
			gain: .16,
			curl: 1
		}
	},
	long: {
		thick: .078,
		line: [
			.205,
			-.02,
			-.235
		],
		fringe: "curtain",
		part: .7,
		frame: .82,
		curtain: {
			end: -1.02,
			back: -1.24,
			flare: .18,
			spread: 2,
			gain: .05
		}
	},
	flow: {
		thick: .098,
		line: [
			.208,
			.015,
			-.222
		],
		fringe: "curtain",
		sweep: .28,
		quiff: .35,
		frame: .62,
		curtain: {
			end: -.8,
			back: -.96,
			flare: .24,
			spread: 1.98,
			gain: .1,
			wave: 1
		}
	},
	curls: {
		thick: .072,
		line: [
			.203,
			.015,
			-.212
		],
		curl: 1,
		clusters: 36,
		coil: .04
	},
	afro: {
		thick: .135,
		line: [
			.198,
			.015,
			-.212
		],
		volume: .4,
		curl: 1.25,
		clusters: 58,
		coil: .045
	},
	locs: {
		thick: .042,
		line: [
			.203,
			.005,
			-.218
		],
		strands: "locs"
	},
	braids: {
		thick: .038,
		line: [
			.198,
			.025,
			-.218
		],
		strands: "braids",
		fringe: "blunt"
	},
	ponytail: {
		thick: .058,
		line: [
			.205,
			.015,
			-.212
		],
		pull: 1,
		grain: 1.8,
		tails: [0]
	},
	twin_tails: {
		thick: .058,
		line: [
			.203,
			.02,
			-.212
		],
		pull: .8,
		grain: 1.8,
		tails: [-1, 1],
		fringe: "blunt"
	},
	bun: {
		thick: .056,
		line: [
			.205,
			.02,
			-.212
		],
		pull: 1,
		grain: 1.8,
		bun: true,
		fringe: "wisp"
	}
};
function buildAvatarHair(head, style, hair, band) {
	const cfg = STYLES[style] || STYLES.crop;
	const [lineFront, lineSide, lineNape] = cfg.line;
	const attach = (geometry, material = hair) => {
		const mesh = new THREE.Mesh(geometry, material);
		mesh.userData.ownedGeometry = true;
		head.add(mesh);
		return mesh;
	};
	const finish = (vertices, indices, material) => {
		const geometry = new THREE.BufferGeometry();
		geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
		geometry.setIndex(indices);
		geometry.computeVertexNormals();
		return attach(geometry, material);
	};
	const hairline = (phi) => {
		const front = Math.cos(phi), corner = .03 * Math.max(0, front) * Math.pow(Math.sin(2 * phi), 2);
		return (front >= 0 ? mix(lineSide, lineFront, ease(front)) : mix(lineSide, lineNape, ease(-front))) + corner;
	};
	const point = (phi, index, lift = 0) => {
		const p = at(index), r = p.r + p.nr * lift;
		return new THREE.Vector3(r * Math.sin(phi), p.y + p.ny * lift, r * DEPTH * Math.cos(phi));
	};
	const liftAt = (phi, t) => {
		const dome = Math.sin(Math.PI * t);
		let lift = cfg.thick * (1 - .96 * ease(clamp((t - .6) / .4, 0, 1)));
		if (cfg.taper) lift *= 1 - cfg.taper * .92 * ease(clamp((t - .25) / .55, 0, 1)) * Math.pow(Math.abs(Math.sin(phi)), 1.4);
		if (cfg.volume) lift *= 1 + cfg.volume * dome;
		if (cfg.quiff) lift *= 1 + cfg.quiff * Math.max(0, Math.cos(phi)) * dome * dome;
		if (cfg.pull) lift *= 1 - .22 * cfg.pull * dome * Math.max(0, Math.cos(phi));
		return lift;
	};
	const capPoint = (phi, t) => point(phi, indexAt(hairline(phi)) * t, liftAt(phi, t));
	const spread = (i, count, reach) => [i * 2.3999 % TAU, Math.sqrt((i + .5) / count) * reach];
	const shell = (columns, rows, fn, thick, material = hair) => {
		const points = [], normals = [], vertices = [], indices = [];
		const index = (i, j) => i * (columns + 1) + j;
		for (let i = 0; i <= rows; i++) for (let j = 0; j <= columns; j++) points.push(fn(j / columns, i / rows));
		for (let i = 0; i <= rows; i++) for (let j = 0; j <= columns; j++) {
			const u = points[index(i, Math.min(columns, j + 1))].clone().sub(points[index(i, Math.max(0, j - 1))]);
			const normal = points[index(Math.min(rows, i + 1), j)].clone().sub(points[index(Math.max(0, i - 1), j)]).cross(u);
			normals.push(normal.lengthSq() ? normal.normalize() : new THREE.Vector3(0, 0, 1));
		}
		const count = points.length;
		for (let side = 0; side < 2; side++) for (let k = 0; k < count; k++) {
			const depth = typeof thick === "function" ? thick(k % (columns + 1) / columns, Math.floor(k / (columns + 1)) / rows) : thick;
			const v = points[k].clone().addScaledVector(normals[k], (side ? -.5 : .5) * depth);
			vertices.push(v.x, v.y, v.z);
		}
		for (let i = 0; i < rows; i++) for (let j = 0; j < columns; j++) {
			const a = index(i, j), b = a + 1, c = a + columns + 1, d = c + 1;
			indices.push(a, c, b, b, c, d, count + a, count + b, count + c, count + b, count + d, count + c);
		}
		const border = [];
		for (let j = 0; j <= columns; j++) border.push(index(0, j));
		for (let i = 1; i <= rows; i++) border.push(index(i, columns));
		for (let j = columns - 1; j >= 0; j--) border.push(index(rows, j));
		for (let i = rows - 1; i >= 1; i--) border.push(index(i, 0));
		for (let k = 0; k < border.length; k++) {
			const a = border[k], b = border[(k + 1) % border.length];
			indices.push(a, b, count + b, a, count + b, count + a);
		}
		return finish(vertices, indices, material);
	};
	const locks = {
		vertices: [],
		indices: []
	};
	const coils = {
		vertices: [],
		indices: []
	};
	const coil = (centre, radius, squash = .9) => {
		const rings = 7, segments = 10, base = coils.vertices.length / 3;
		for (let i = 0; i <= rings; i++) for (let j = 0; j <= segments; j++) {
			const theta = i / rings * Math.PI, phi = j / segments * TAU;
			coils.vertices.push(centre.x + radius * Math.sin(theta) * Math.sin(phi), centre.y + radius * squash * Math.cos(theta), centre.z + radius * Math.sin(theta) * Math.cos(phi));
			if (i < rings && j < segments) {
				const n = base + i * 11 + j;
				coils.indices.push(n, n + segments + 1, n + 1, n + 1, n + segments + 1, n + segments + 2);
			}
		}
	};
	const strand = (path, width, { taper = .3, rib = 0, blunt = 0, segments = 18, sides = 7 } = {}) => {
		const curve = new THREE.CatmullRomCurve3(path.map((p) => new THREE.Vector3(...p)));
		const frames = curve.computeFrenetFrames(segments, false);
		const vertices = locks.vertices, indices = locks.indices, base = vertices.length / 3;
		for (let i = 0; i <= segments; i++) {
			const t = i / segments, position = curve.getPointAt(t);
			const body = Math.pow(Math.sin(Math.PI * (.24 + .76 * t)), .5);
			const radius = width * (1 - taper * t) * Math.max(blunt * (1 - Math.pow(t, 8)), body) * (1 - rib + rib * Math.abs(Math.cos(t * Math.PI * 7)));
			for (let j = 0; j <= sides; j++) {
				const a = j / sides * TAU;
				const v = position.clone().addScaledVector(frames.normals[i], Math.cos(a) * radius).addScaledVector(frames.binormals[i], Math.sin(a) * radius);
				vertices.push(v.x, v.y, v.z);
				if (i < segments && j < sides) {
					const n = base + i * (sides + 1) + j;
					indices.push(n, n + 1, n + sides + 1, n + 1, n + sides + 2, n + sides + 1);
				}
			}
		}
	};
	const rows = 26, columns = 72, vertices = [], indices = [];
	const partPhi = -.55;
	for (let i = 0; i <= 27; i++) for (let j = 0; j < columns; j++) {
		const phi = j / columns * TAU, rim = i > rows, t = Math.min(i, rows) / rows;
		const p = at(indexAt(hairline(phi)) * t);
		const dome = Math.pow(Math.sin(Math.PI * t), 1.6);
		const grain = (cfg.grain || 0) * .006 * Math.sin(phi * (cfg.grainN || 26) + t * 5) * dome;
		const curl = (cfg.curl || 0) * .022 * Math.sin(phi * 13 + t * 4) * Math.sin(t * 16 + phi * 2) * dome;
		const part = (cfg.part || 0) * -.034 * Math.exp(-Math.pow(Math.sin((phi - partPhi) / 2) / .12, 2)) * (1 - ease(clamp((t - .45) / .5, 0, 1)));
		const lift = rim ? .001 : liftAt(phi, t) + grain + curl + part;
		const radius = p.r + p.nr * lift;
		vertices.push(radius * Math.sin(phi) + (cfg.sweep || 0) * .05 * dome, p.y + p.ny * lift, radius * DEPTH * Math.cos(phi));
		if (i <= rows) {
			const n = i * columns + j, right = i * columns + (j + 1) % columns;
			indices.push(n, n + columns, right, right, n + columns, right + columns);
		}
	}
	finish(vertices, indices);
	const bangs = (kind, span) => {
		const shape = (u) => {
			const x = u * 2 - 1;
			if (kind === "blunt") return .118 + .018 * x * x;
			if (kind === "crop") return .148 + .02 * Math.abs(Math.sin(u * Math.PI * 5));
			if (kind === "spike") return .142 + .034 * Math.pow(Math.abs(Math.sin(u * Math.PI * 5.5)), .7);
			if (kind === "swept") return mix(.104, .198, ease(clamp(u * 1.2, 0, 1)));
			return mix(.198, .052, ease(Math.abs(x)));
		};
		shell(36, 9, (u, v) => {
			const skew = kind === "swept" ? .34 : kind === "curtain" ? .16 * Math.sign(u * 2 - 1) : 0;
			const phi = (u * 2 - 1) * span + skew * v * v;
			const top = hairline(phi) + .025;
			const y = mix(top, Math.min(shape(u), top - .03), Math.pow(v, .85));
			const stand = .009 + (kind === "curtain" ? .034 : .026) * v * (1 - .3 * v);
			const radius = Math.max(radiusAt(y), radiusAt(top)) + stand;
			return new THREE.Vector3(radius * Math.sin(phi), y, radius * DEPTH * Math.cos(phi));
		}, (u, v) => .046 * (1 - .9 * v * v) * (1 - .45 * Math.pow(Math.abs(u * 2 - 1), 3)));
	};
	if (cfg.fringe === "wisp") for (let i = 0; i < 6; i++) {
		const phi = -1.05 + i * .42, top = hairline(phi) + .03, r = radiusAt(top);
		const drop = .112 + .026 * (i * 3 % 4) / 3, tip = phi + .3;
		strand([
			[
				r * Math.sin(phi),
				top,
				r * DEPTH * Math.cos(phi)
			],
			[
				(r + .012) * Math.sin(phi + .1),
				mix(top, drop, .5),
				(r + .012) * DEPTH * Math.cos(phi + .1)
			],
			[
				(r + .026) * Math.sin(tip),
				drop,
				(r + .026) * DEPTH * Math.cos(tip)
			]
		], .026, { taper: .55 });
	}
	else if (cfg.fringe) bangs(cfg.fringe, cfg.fringe === "curtain" ? 1.32 : 1.24);
	if (cfg.clusters) for (let i = 0; i < cfg.clusters; i++) {
		const [phi, t] = spread(i, cfg.clusters, .96);
		const size = cfg.coil * (.78 + .44 * (i * 7 % 5) / 4);
		coil(capPoint(phi, t).multiplyScalar(1 + size * .3), size);
	}
	if (cfg.spikes) for (let i = 0; i < cfg.spikes; i++) {
		const [phi, t] = spread(i, cfg.spikes, .86);
		const base = capPoint(phi, t);
		const tip = base.clone().multiplyScalar(1.04);
		tip.y += .085 + .045 * (i * 5 % 3) / 2;
		tip.x += .035 * Math.sin(phi * 3);
		tip.z += .02;
		strand([
			base.toArray(),
			base.clone().lerp(tip, .5).toArray(),
			tip.toArray()
		], .03, {
			taper: .6,
			segments: 10
		});
	}
	if (cfg.crest) shell(38, 6, (u, v) => {
		const forward = u < .5, t = forward ? 1 - u * 2 : u * 2 - 1;
		const phi = forward ? 0 : Math.PI, along = forward ? .5 - t * .5 : .5 + t * .5;
		const p = at(indexAt(hairline(phi)) * t);
		const height = .175 * Math.pow(Math.sin(Math.PI * along), .65) * (1 - .24 * Math.abs(Math.sin(along * Math.PI * 7)));
		const radius = p.r + p.nr * cfg.thick + height * v * p.nr * .18;
		return new THREE.Vector3(0, p.y + p.ny * cfg.thick + height * v, radius * DEPTH * Math.cos(phi));
	}, (u, v) => .075 * (1 - .8 * v * v) * (1 - .55 * Math.pow(Math.abs(u * 2 - 1), 2)));
	if (cfg.curtain) {
		const { end, back, flare, spread: arc, gain, wave = 0, curl = 0 } = cfg.curtain;
		shell(52, 16, (u, v) => {
			const edge = Math.abs(u * 2 - 1), fall = ease(v);
			const phi = Math.PI + (u * 2 - 1) * (arc + gain * fall);
			const root = point(phi, indexAt(hairline(phi)) * mix(.82, .42, Math.max(0, -Math.cos(phi))), cfg.thick * .5);
			const hem = mix(back, end, ease(edge)) + (end - back) * .35 * Math.pow(edge, 4);
			const y = mix(root.y, hem, fall);
			const widen = 1 + flare * fall * fall * (1 - .5 * edge * edge) + wave * .04 * Math.sin(v * 7 + u * 5);
			const radius = Math.max(Math.hypot(root.x, root.z / DEPTH), radiusAt(y) + .028) * widen;
			const tuck = curl * .09 * Math.pow(fall, 3) * Math.max(0, -Math.cos(phi));
			return new THREE.Vector3(radius * Math.sin(phi), y, radius * DEPTH * Math.cos(phi) - tuck);
		}, (u, v) => (.018 + .075 * Math.sin(Math.PI * Math.pow(v, .65))) * (1 - .3 * Math.pow(Math.abs(u * 2 - 1), 4)));
	}
	if (cfg.frame) for (const side of [-1, 1]) {
		const phi = side * 1.18, y = hairline(phi), r = radiusAt(y);
		strand([
			[
				r * Math.sin(phi),
				y,
				r * DEPTH * Math.cos(phi)
			],
			[
				r * 1.06 * Math.sin(phi),
				y - .34,
				r * .92 * DEPTH * Math.cos(phi)
			],
			[
				r * 1.14 * Math.sin(phi),
				y - .78 * cfg.frame,
				r * .62 * DEPTH * Math.cos(phi)
			]
		], .045, { taper: .55 });
	}
	if (cfg.strands) {
		const braids = cfg.strands === "braids", count = braids ? 13 : 17;
		for (let i = 0; i < count; i++) {
			const phi = Math.PI + (i / (count - 1) * 2 - 1) * (braids ? 1.9 : 2.2);
			const line = indexAt(hairline(phi));
			const start = point(phi, line * .5, cfg.thick);
			const mid = point(phi, line, cfg.thick * 1.4);
			const reach = braids ? .62 : .5, drift = (i % 3 - 1) * .02;
			strand([
				start.toArray(),
				mid.toArray(),
				[
					mid.x * 1.06 + drift,
					mid.y - reach * .45,
					mid.z * 1.02
				],
				[
					mid.x * 1.1 + drift,
					mid.y - reach,
					mid.z * .92
				]
			], braids ? .03 : .036, {
				taper: .35,
				blunt: .85,
				rib: braids ? .3 : .08
			});
		}
	}
	if (cfg.tails) {
		const twin = cfg.tails.length > 1;
		for (const side of cfg.tails) {
			const root = twin ? new THREE.Vector3(side * .25, .14, -.1) : new THREE.Vector3(0, .06, -.29);
			for (let j = 0; j < 4; j++) {
				const offset = (j - 1.5) * .036;
				strand([
					root.toArray(),
					[
						root.x + (twin ? side * .09 : offset),
						root.y - .18,
						root.z - (twin ? .04 : -.02)
					],
					[
						root.x + (twin ? side * .15 : offset * 1.2),
						root.y - .46,
						root.z - (twin ? .07 : -.01)
					],
					[
						root.x + (twin ? side * .16 : offset * 1.1),
						root.y - .76 - .04 * (j % 2),
						root.z - (twin ? .06 : .05)
					]
				], .052, { taper: .45 });
			}
			const tie = attach(new THREE.TorusGeometry(.062, .017, 8, 22), band);
			tie.position.copy(root);
			tie.rotation.set(twin ? 0 : -.6, twin ? Math.PI / 2 : 0, 0);
		}
	}
	if (cfg.bun) {
		const centre = point(Math.PI, indexAt(.17), cfg.thick + .1);
		const knot = attach(new THREE.TorusGeometry(.1, .052, 12, 26));
		knot.position.copy(centre);
		knot.rotation.set(Math.PI / 2 - .3, 0, 0);
		knot.scale.set(1, 1, .82);
		for (let i = 0; i < 3; i++) {
			const a = i / 3 * TAU;
			strand([
				[
					centre.x + Math.cos(a) * .105,
					centre.y + Math.sin(a) * .095,
					centre.z
				],
				[
					centre.x + Math.cos(a + 2) * .085,
					centre.y + Math.sin(a + 2) * .08,
					centre.z - .07
				],
				[
					centre.x + Math.cos(a + 4) * .105,
					centre.y + Math.sin(a + 4) * .095,
					centre.z
				]
			], .02, {
				taper: .1,
				blunt: .9
			});
		}
		const tie = attach(new THREE.TorusGeometry(.072, .016, 8, 22), band);
		tie.position.set(centre.x, centre.y - .02, centre.z + .07);
		tie.rotation.set(Math.PI / 2 - .3, 0, 0);
	}
	if (coils.indices.length) finish(coils.vertices, coils.indices);
	if (cfg.points) for (const side of [-1, 1]) {
		const phi = side * 1.62, y = hairline(phi), r = radiusAt(y);
		strand([
			[
				r * Math.sin(phi),
				y + .03,
				r * DEPTH * Math.cos(phi)
			],
			[
				r * .99 * Math.sin(phi),
				y - .06,
				r * .95 * DEPTH * Math.cos(phi) + .012
			],
			[
				r * .93 * Math.sin(phi),
				y - .14 - cfg.points,
				r * .84 * DEPTH * Math.cos(phi) + .025
			]
		], .026, { taper: .5 });
	}
	if (locks.indices.length) finish(locks.vertices, locks.indices);
}
//#endregion
//#region frontend/src/arena-avatar-scene.js
function createAvatarScene(host, initial, onFailure) {
	const renderer = new THREE.WebGLRenderer({
		alpha: true,
		antialias: true,
		powerPreference: "low-power"
	});
	renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
	renderer.outputColorSpace = THREE.SRGBColorSpace;
	renderer.toneMapping = THREE.ACESFilmicToneMapping;
	renderer.toneMappingExposure = 1.05;
	renderer.shadowMap.enabled = true;
	renderer.shadowMap.type = THREE.PCFShadowMap;
	host.appendChild(renderer.domElement);
	const scene = new THREE.Scene();
	const camera = new THREE.PerspectiveCamera(32, 1, .1, 30);
	camera.position.set(0, 1.85, 5.3);
	camera.lookAt(0, 1.46, 0);
	scene.add(new THREE.HemisphereLight("#d7e2ff", "#2c3050", 1.35));
	for (const [color, power, x, y, z] of [[
		"#fff2df",
		3.8,
		-3,
		5,
		4
	], [
		"#d3c9ef",
		2.5,
		3,
		3,
		-2
	]]) {
		const light = new THREE.DirectionalLight(color, power);
		light.position.set(x, y, z);
		if (z > 0) {
			light.castShadow = true;
			light.shadow.mapSize.set(1024, 1024);
			Object.assign(light.shadow.camera, {
				left: -2,
				right: 2,
				top: 4,
				bottom: -1,
				near: .1,
				far: 12
			});
			light.shadow.bias = -.001;
			light.shadow.normalBias = .025;
		}
		scene.add(light);
	}
	const shapes = {
		ball: new THREE.SphereGeometry(1, 24, 16),
		box: new THREE.BoxGeometry(1, 1, 1),
		rounded: new RoundedBoxGeometry(1, 1, 1, 3, .16),
		capsule: new THREE.CapsuleGeometry(1, 2, 6, 16),
		cone: new THREE.ConeGeometry(1, 1, 12),
		cylinder: new THREE.CylinderGeometry(1, 1, 1, 24),
		ring: new THREE.TorusGeometry(1, .07, 8, 40)
	};
	const pedestalMaterial = new THREE.MeshStandardMaterial({
		color: "#20232f",
		roughness: .8,
		metalness: .15
	});
	const pedestal = new THREE.Mesh(shapes.cylinder, pedestalMaterial);
	pedestal.scale.set(1.02, .035, .78);
	pedestal.position.y = .045;
	pedestal.receiveShadow = true;
	scene.add(pedestal);
	const shadowMaterials = [];
	const shadowGeometry = new THREE.CircleGeometry(1, 48);
	for (let i = 0; i < 5; i++) {
		const mat = new THREE.MeshBasicMaterial({
			color: "#080918",
			transparent: true,
			opacity: .075,
			depthWrite: false
		});
		shadowMaterials.push(mat);
		const mesh = new THREE.Mesh(shadowGeometry, mat);
		mesh.rotation.x = -Math.PI / 2;
		mesh.scale.set(.34 + i * .055, .26 + i * .03, 1);
		mesh.position.set(0, .062 + i * 1e-4, 0);
		scene.add(mesh);
	}
	let fighter, materials = [], disposed = false, frame = 0, visible = true, paused = false, last = 0;
	let targetAngle = -.2, angle = -.2, drag = null, view = "full";
	const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
	function setAvatar(value) {
		const a = normalizeArenaAvatar(value);
		if (fighter) scene.remove(fighter);
		materials.forEach((m) => m.dispose());
		materials = [];
		fighter = new THREE.Group();
		scene.add(fighter);
		const [primary, dark] = ARENA_AVATAR_PALETTES[a.palette];
		const material = (color, metalness = 0) => {
			const m = new THREE.MeshStandardMaterial({
				color,
				roughness: metalness ? .36 : .7,
				metalness
			});
			materials.push(m);
			return m;
		};
		const skin = material(ARENA_AVATAR_SKINS[a.skin][0]);
		const cloth = material(new THREE.Color(primary).lerp(new THREE.Color("#77768a"), .24));
		const pants = material(new THREE.Color(dark).lerp(new THREE.Color("#161c28"), .94));
		const trim = material(ARENA_AVATAR_ACCENTS[a.accent], .25), hair = material(ARENA_AVATAR_HAIR[a.hair_color]);
		Object.assign(hair, {
			roughness: .52,
			side: THREE.DoubleSide
		});
		const white = material("#f4f4fb"), ink = material("#171724"), eye = material(ARENA_AVATAR_EYES[a.eyes]);
		function part(shape, mat, pos, scale, parent = fighter, rotation = 0) {
			const mesh = new THREE.Mesh(shapes[shape], mat);
			mesh.castShadow = true;
			mesh.position.set(...pos);
			mesh.scale.set(...scale);
			mesh.rotation.z = rotation;
			parent.add(mesh);
			return mesh;
		}
		const ball = (mat, pos, scale, parent, rotation) => part("ball", mat, pos, scale, parent, rotation);
		const box = (mat, pos, scale, parent, rotation) => part("box", mat, pos, scale, parent, rotation);
		const capsule = (mat, pos, scale, parent, rotation) => part("capsule", mat, pos, scale, parent, rotation);
		function sculpt(mat, profile, position, scale, parent = fighter) {
			const geometry = new THREE.LatheGeometry(profile.map(([x, y]) => new THREE.Vector2(x, y)), 32);
			const mesh = new THREE.Mesh(geometry, mat);
			mesh.castShadow = true;
			mesh.userData.ownedGeometry = true;
			mesh.position.set(...position);
			mesh.scale.set(...scale);
			parent.add(mesh);
			return mesh;
		}
		const build = {
			striker: 1,
			sentinel: 1.13,
			scout: .86,
			titan: 1.23,
			lithe: .82,
			compact: 1.07
		}[a.body];
		const width = build * {
			masculine: 1,
			feminine: .89,
			androgynous: .95,
			athletic: 1.08
		}[a.frame];
		fighter.scale.y = {
			short: .92,
			average: 1,
			tall: 1.07
		}[a.height];
		const torso = new THREE.Group();
		torso.position.y = 1.37;
		fighter.add(torso);
		const soft = [
			"hoodie",
			"street",
			"varsity",
			"scholar"
		].includes(a.outfit);
		sculpt(cloth, [
			[0, -.04],
			[.22, -.04],
			[.26, 0],
			[.265, .1],
			[.28, .25],
			[.32, .43],
			[.34, .6],
			[.31, .68],
			[.23, .74],
			[.13, .78],
			[0, .78]
		], [
			0,
			0,
			0
		], [
			width,
			1,
			.68
		], torso);
		sculpt(pants, [
			[0, -.14],
			[.21, -.14],
			[.27, -.07],
			[.27, .07],
			[.23, .12],
			[0, .12]
		], [
			0,
			-.035,
			0
		], [
			width,
			1,
			.69
		], torso);
		if ([
			"combat",
			"champion",
			"techwear"
		].includes(a.outfit)) {
			box(pants, [
				0,
				.41,
				.232
			], [
				.014,
				.43,
				.012
			], torso);
			box(trim, [
				0,
				.56,
				.243
			], [
				.024,
				.05,
				.012
			], torso);
		} else if (["academy", "scholar"].includes(a.outfit)) {
			for (const side of [-1, 1]) box(white, [
				side * .08,
				.65,
				.17
			], [
				.09,
				.2,
				.035
			], torso, side * -.4);
			box(trim, [
				0,
				.52,
				.23
			], [
				.045,
				.2,
				.025
			], torso);
		} else if (a.outfit === "jersey") box(white, [
			0,
			.43,
			.225
		], [
			.11,
			.2,
			.02
		], torso);
		else if (a.outfit === "flight") box(trim, [
			.18,
			.44,
			.22
		], [
			.1,
			.11,
			.025
		], torso);
		if (soft) {
			ball(cloth, [
				0,
				.77,
				-.03
			], [
				.26,
				.13,
				.24
			], torso);
			for (const side of [-1, 1]) box(trim, [
				side * .07,
				.58,
				.23
			], [
				.018,
				.18,
				.018
			], torso);
		}
		const crest = {
			bolt: "box",
			mind: "ball",
			target: "ring",
			shield: "cone",
			star: "cone",
			flame: "ball",
			crown: "box",
			atom: "ring",
			book: "box",
			wave: "ring"
		}[a.emblem];
		part(crest, trim, [
			-.12 * width,
			.56,
			.235
		], [
			.055,
			.055,
			.02
		], torso, a.emblem === "bolt" ? -.45 : 0);
		if (a.marking !== "none") {
			const count = {
				stripes: 2,
				circuit: 3,
				chevron: 2,
				stars: 3,
				scales: 4
			}[a.marking];
			for (let i = 0; i < count; i++) box(trim, [
				.16,
				.35 - i * .075,
				.22
			], [
				.1,
				.018,
				.025
			], torso, a.marking === "chevron" ? .5 : 0);
		}
		const robe = a.outfit === "scholar";
		const skirted = robe || ["battle_skirt", "pleated"].includes(a.bottom);
		for (const side of [-1, 1]) {
			const legX = side * .16 * width;
			if (a.bottom === "shorts") {
				sculpt(pants, [
					[0, 0],
					[.1, 0],
					[.105, .1],
					[.12, .26],
					[.135, .43],
					[.145, .55],
					[.12, .61],
					[0, .62]
				], [
					legX,
					.73,
					0
				], [
					build,
					1,
					1.02
				]);
				sculpt(skin, [
					[0, 0],
					[.08, 0],
					[.085, .13],
					[.11, .29],
					[.115, .42],
					[.1, .53],
					[0, .54]
				], [
					legX + side * .015,
					.25,
					.01
				], [
					build,
					1,
					1.02
				]);
			} else sculpt(pants, [
				[0, 0],
				[.085, 0],
				[.09, .12],
				[.115, .3],
				[.108, .48],
				[.12, .65],
				[.14, .9],
				[.14, 1.04],
				[.1, 1.1],
				[0, 1.12]
			], [
				legX,
				.25,
				0
			], [
				build,
				1,
				1.02
			]);
			if (!skirted && (a.bottom === "cargo" || a.bottom === "tactical")) part("rounded", pants, [
				legX + side * .09,
				1.04,
				.105
			], [
				.1,
				.19,
				.075
			]);
			if (a.bottom === "joggers") ball(cloth, [
				legX + side * .025,
				.34,
				.02
			], [
				.11 * build,
				.06,
				.12
			]);
			const foot = a.footwear === "barefoot" ? skin : pants;
			const tallBoot = [
				"boots",
				"armored",
				"greaves"
			].includes(a.footwear);
			ball(foot, [
				legX + side * .025,
				.17,
				.1
			], [
				.14 * build,
				.11,
				.24
			]);
			if (a.footwear !== "barefoot") {
				part("rounded", white, [
					legX + side * .025,
					.095,
					.105
				], [
					.265 * build,
					.045,
					.44
				]);
				capsule(foot, [
					legX + side * .025,
					tallBoot ? .27 : .23,
					.02
				], [
					.105 * build,
					tallBoot ? .07 : .03,
					.105
				]);
				for (let j = 0; j < 3; j++) box(trim, [
					legX + side * .025,
					.245,
					.15 + j * .045
				], [
					.14,
					.012,
					.02
				]);
			}
			const arm = new THREE.Group();
			arm.position.set(side * .35 * width, 2.02, 0);
			arm.rotation.z = side * (a.pose === "confident" ? .31 : a.pose === "relaxed" ? .08 : .18);
			if (a.pose === "guard") arm.rotation.x = -.45;
			fighter.add(arm);
			sculpt(a.outfit === "jersey" ? skin : cloth, [
				[0, -.37],
				[.085, -.37],
				[.095, -.29],
				[.125, -.13],
				[.14, -.01],
				[.1, .07],
				[0, .1]
			], [
				side * .025,
				0,
				0
			], [
				build,
				1,
				1
			], arm);
			sculpt(a.outfit === "jersey" ? skin : cloth, [
				[0, -.66],
				[.072, -.66],
				[.08, -.58],
				[.1, -.43],
				[.09, -.33],
				[0, -.31]
			], [
				side * .03,
				0,
				.015
			], [
				build,
				1,
				1
			], arm);
			ball(a.gloves === "none" ? skin : pants, [
				side * .04,
				-.7,
				.045
			], [
				.105 * build,
				.13,
				.1
			], arm);
			if (a.gloves !== "none") {
				ball(trim, [
					side * .04,
					-.61,
					.05
				], [
					.107 * build,
					a.gloves === "gauntlets" ? .13 : .04,
					.105
				], arm);
				if (a.gloves === "fingerless") ball(skin, [
					side * .04,
					-.77,
					.075
				], [
					.08,
					.045,
					.08
				], arm);
				if (a.gloves === "claws") for (let j = 0; j < 3; j++) part("cone", trim, [
					side * .04 + (j - 1) * .04,
					-.84,
					.1
				], [
					.015,
					.12,
					.015
				], arm, Math.PI);
			}
			if ([
				"pauldrons",
				"epaulettes",
				"spikes"
			].includes(a.shoulder)) {
				ball(trim, [
					0,
					-.04,
					0
				], [
					.17 * build,
					.11,
					.17
				], arm);
				if (a.shoulder === "spikes") for (let j = 0; j < 3; j++) part("cone", trim, [
					(j - 1) * .1,
					.09,
					0
				], [
					.035,
					.18,
					.035
				], arm);
			}
		}
		function drape(mat, shape, from = 0, to = 1, swell = 0) {
			const { top, hem, waist, flare, folds, amp, depth, sharp } = shape;
			const rows = 14, columns = folds > 10 ? 120 : 72, rings = 30;
			const vertices = [], indices = [];
			for (let i = 0; i < rings; i++) {
				const outer = i <= rows;
				const v = from + (to - from) * ((outer ? i : 29 - i) / rows);
				const radius = waist + flare * Math.pow(v, 1.55);
				for (let j = 0; j <= columns; j++) {
					const phi = j / columns * Math.PI * 2;
					const r = radius * (1 + amp * (sharp ? Math.abs(phi / (Math.PI * 2) * folds % 1 * 2 - 1) * 2 - 1 : Math.cos(phi * folds)) * (.25 + .75 * v)) + swell - (outer ? 0 : .022);
					vertices.push(r * Math.sin(phi), top + (hem - top) * v, r * depth * Math.cos(phi));
				}
			}
			for (let i = 0; i < rings; i++) {
				const a = i * (columns + 1), b = (i + 1) % rings * (columns + 1);
				for (let j = 0; j < columns; j++) indices.push(a + j, b + j, a + j + 1, a + j + 1, b + j, b + j + 1);
			}
			const geometry = new THREE.BufferGeometry();
			geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
			geometry.setIndex(indices);
			geometry.computeVertexNormals();
			const mesh = new THREE.Mesh(geometry, mat);
			mesh.castShadow = true;
			mesh.userData.ownedGeometry = true;
			fighter.add(mesh);
			return mesh;
		}
		if (skirted) {
			const pleated = !robe && a.bottom === "pleated";
			const shape = robe ? {
				top: 1.35,
				hem: .4,
				waist: .3 * width,
				flare: .17 * width,
				folds: 7,
				amp: .035,
				depth: .84
			} : pleated ? {
				top: 1.345,
				hem: .845,
				waist: .275 * width,
				flare: .2 * width,
				folds: 20,
				amp: .055,
				depth: .8,
				sharp: true
			} : {
				top: 1.35,
				hem: .875,
				waist: .285 * width,
				flare: .175 * width,
				folds: 8,
				amp: .03,
				depth: .82
			};
			drape(cloth, shape);
			if (!robe) {
				drape(trim, shape, pleated ? .93 : .9, 1, .008);
				if (!pleated) drape(trim, shape, 0, .07, .01);
			}
		}
		if (a.shoulder === "sash") box(trim, [
			0,
			.42,
			.25
		], [
			.07,
			.73,
			.02
		], torso, -.55);
		if (a.waist !== "none") {
			if (a.waist === "wrap") ball(trim, [
				0,
				1.3,
				0
			], [
				.32 * width,
				.15,
				.23
			]);
			else if (a.waist === "chain") {
				const ring = part("ring", trim, [
					0,
					1.34,
					.1
				], [
					.3 * width,
					.1,
					.2
				]);
				ring.rotation.x = Math.PI / 2;
			} else for (const side of a.waist === "holsters" ? [-1, 1] : [1]) box(pants, [
				side * .3 * width,
				1.27,
				.1
			], [
				.14,
				.22,
				.14
			]);
		}
		ball(skin, [
			0,
			2.15,
			0
		], [
			.12,
			.17,
			.12
		]);
		const head = new THREE.Group();
		head.position.y = 2.43;
		head.scale.set(.88, .94, .92);
		fighter.add(head);
		sculpt(skin, HEAD_PROFILE, [
			0,
			0,
			0
		], [
			1,
			1,
			.91
		], head);
		for (const side of [-1, 1]) {
			ball(skin, [
				side * .29,
				-.02,
				0
			], [
				.055,
				.1,
				.06
			], head);
			ball(white, [
				side * .105,
				.015,
				.242
			], [
				.057,
				.032,
				.022
			], head);
			ball(eye, [
				side * .105,
				.015,
				.262
			], [
				.024,
				.026,
				.009
			], head);
			ball(ink, [
				side * .105,
				.015,
				.271
			], [
				.012,
				.018,
				.006
			], head);
			ball(white, [
				side * .098,
				.025,
				.277
			], [
				.006,
				.007,
				.004
			], head);
			box(hair, [
				side * .11,
				.09,
				.247
			], [
				.12,
				a.brows === "bold" ? .035 : .022,
				.025
			], head, side * {
				soft: 0,
				bold: -.1,
				arched: .2,
				sharp: -.25
			}[a.brows]);
		}
		ball(skin, [
			0,
			-.055,
			.275
		], [
			.034,
			.045,
			.032
		], head);
		const lip = material(ARENA_AVATAR_SKINS[a.skin][1]);
		ball(a.expression === "grin" ? white : lip, [
			0,
			-.16,
			.23
		], [
			a.expression === "grin" ? .1 : .075,
			a.expression === "grin" ? .026 : .012,
			.012
		], head);
		if (a.face !== "natural") for (const side of [-1, 1]) if (a.face === "freckles") for (let i = 0; i < 3; i++) ball(lip, [
			side * (.12 + i * .025),
			-.07 + i % 2 * .02,
			.238
		], [
			.008,
			.008,
			.005
		], head);
		else box([
			"cyber",
			"warpaint",
			"tattoo"
		].includes(a.face) ? trim : lip, [
			side * .17,
			-.065,
			.23
		], [
			a.face === "blush" ? .06 : .017,
			a.face === "blush" ? .025 : .1,
			.015
		], head, side * -.4);
		if (a.facial_hair !== "none") {
			if ([
				"full",
				"stubble",
				"goatee"
			].includes(a.facial_hair)) ball(hair, [
				0,
				-.25,
				.17
			], [
				a.facial_hair === "goatee" ? .065 : .2,
				a.facial_hair === "full" ? .13 : .07,
				.095
			], head);
			if (["full", "mustache"].includes(a.facial_hair)) ball(hair, [
				0,
				-.12,
				.267
			], [
				.11,
				.023,
				.023
			], head);
		}
		if (!["helmet", "cap"].includes(a.gear)) buildAvatarHair(head, a.hair, hair, trim);
		switch (a.gear) {
			case "visor":
			case "shades":
			case "glasses":
				for (const side of [-1, 1]) {
					ball(a.gear === "glasses" ? trim : ink, [
						side * .115,
						.035,
						.277
					], [
						.095,
						.06,
						.034
					], head);
					if (a.gear === "glasses") ball(white, [
						side * .115,
						.035,
						.306
					], [
						.069,
						.041,
						.007
					], head);
					box(trim, [
						side * .235,
						.045,
						.13
					], [
						.03,
						.025,
						.3
					], head);
				}
				box(trim, [
					0,
					.035,
					.3
				], [
					.055,
					.025,
					.02
				], head);
				break;
			case "helmet":
				ball(pants, [
					0,
					.19,
					-.04
				], [
					.34,
					.25,
					.29
				], head);
				for (const side of [-1, 1]) ball(cloth, [
					side * .3,
					-.015,
					-.01
				], [
					.075,
					.23,
					.24
				], head);
				box(trim, [
					0,
					.19,
					.25
				], [
					.42,
					.04,
					.055
				], head);
				break;
			case "cap":
				ball(cloth, [
					0,
					.26,
					-.02
				], [
					.32,
					.14,
					.28
				], head);
				ball(pants, [
					0,
					.18,
					.27
				], [
					.33,
					.025,
					.22
				], head);
				break;
			case "crown":
				for (let i = -2; i <= 2; i++) part("cone", trim, [
					i * .11,
					.4,
					.09
				], [
					.07,
					.2,
					.07
				], head);
				box(trim, [
					0,
					.31,
					.16
				], [
					.5,
					.06,
					.09
				], head);
				break;
			case "comms":
				ball(pants, [
					-.32,
					0,
					0
				], [
					.065,
					.12,
					.1
				], head);
				box(trim, [
					-.23,
					-.12,
					.16
				], [
					.2,
					.025,
					.03
				], head, -.3);
				break;
			case "headband":
				box(trim, [
					0,
					.17,
					.243
				], [
					.46,
					.055,
					.045
				], head);
				break;
			case "earrings":
				for (const side of [-1, 1]) part("ring", trim, [
					side * .3,
					-.12,
					.025
				], [
					.045,
					.06,
					.045
				], head);
				break;
			case "mask": ball(pants, [
				0,
				-.135,
				.24
			], [
				.2,
				.095,
				.06
			], head);
		}
		if (a.back !== "none") {
			if ([
				"cape",
				"half_cape",
				"banner"
			].includes(a.back)) {
				box(pants, [
					a.back === "half_cape" ? -.16 : 0,
					1.47,
					-.29
				], [
					a.back === "half_cape" ? .32 : .64,
					a.back === "banner" ? 1.15 : 1.05,
					.06
				], fighter, -.06);
				box(trim, [
					0,
					1.6,
					-.33
				], [
					.1,
					.5,
					.018
				]);
			} else if (a.back === "wings") for (const side of [-1, 1]) for (let i = 0; i < 4; i++) ball(trim, [
				side * (.4 + i * .13),
				1.9 + i * .12,
				-.22
			], [
				.1,
				.43 - i * .05,
				.055
			], fighter, side * -.65);
			else {
				box(pants, [
					0,
					1.77,
					-.28
				], [
					.4,
					.5,
					.22
				]);
				for (const side of [-1, 1]) ball(a.back === "quiver" ? pants : trim, [
					side * .16,
					1.8,
					-.38
				], [
					.075,
					a.back === "quiver" ? .4 : .24,
					.09
				]);
			}
		}
		if (a.aura !== "none") {
			const ring = part("ring", trim, [
				0,
				a.aura === "halo" ? 2.98 : .1,
				0
			], [
				a.aura === "halo" ? .4 : .71,
				a.aura === "halo" ? .4 : .6,
				.3
			]);
			ring.rotation.x = Math.PI / 2;
			if ([
				"spark",
				"embers",
				"frost",
				"storm"
			].includes(a.aura)) for (let i = 0; i < 5; i++) part("ball", trim, [
				Math.cos(i * 2.4) * .65,
				.3 + i * .32,
				-.25
			], [
				.025,
				.035,
				.025
			]);
		}
		updateCamera();
		invalidate();
	}
	function updateCamera() {
		const portrait = view === "portrait";
		const height = fighter?.scale.y || 1;
		camera.position.set(0, portrait ? 2.42 * height : 1.85, portrait ? 2.5 : 5.3);
		camera.lookAt(0, portrait ? 2.29 * height : 1.46, 0);
	}
	function render(time = 0) {
		frame = 0;
		if (disposed || !visible || document.hidden || paused) return;
		if (time - last >= 32 || reduced.matches) {
			last = time;
			angle += (targetAngle - angle) * (reduced.matches ? 1 : .2);
			fighter.rotation.y = angle;
			fighter.position.y = reduced.matches ? 0 : Math.sin(time * .0013) * .008;
			renderer.render(scene, camera);
		}
		if (!reduced.matches || Math.abs(targetAngle - angle) > .001) frame = requestAnimationFrame(render);
	}
	function invalidate() {
		if (!frame && !disposed) frame = requestAnimationFrame(render);
	}
	const resize = new ResizeObserver(() => {
		const { width, height } = host.getBoundingClientRect();
		if (!width || !height) return;
		renderer.setSize(width, height, false);
		camera.aspect = width / height;
		camera.updateProjectionMatrix();
		invalidate();
	});
	const intersection = new IntersectionObserver((entries) => {
		visible = entries[0].isIntersecting;
		invalidate();
	});
	const resume = () => invalidate();
	const down = (e) => {
		if (e.button !== 0) return;
		drag = {
			id: e.pointerId,
			x: e.clientX
		};
		host.setPointerCapture(e.pointerId);
	};
	const move = (e) => {
		if (!drag || drag.id !== e.pointerId) return;
		targetAngle += (e.clientX - drag.x) * .012;
		drag.x = e.clientX;
		invalidate();
	};
	const up = () => {
		drag = null;
	};
	const lost = (e) => {
		e.preventDefault();
		paused = true;
		onFailure();
	};
	resize.observe(host);
	intersection.observe(host);
	document.addEventListener("visibilitychange", resume);
	reduced.addEventListener("change", resume);
	host.addEventListener("pointerdown", down);
	host.addEventListener("pointermove", move);
	host.addEventListener("pointerup", up);
	host.addEventListener("pointercancel", up);
	renderer.domElement.addEventListener("webglcontextlost", lost);
	setAvatar(initial);
	function disposeOwned(group) {
		group?.traverse((obj) => {
			if (obj.userData.ownedGeometry) obj.geometry.dispose();
		});
	}
	return {
		setAvatar(value) {
			disposeOwned(fighter);
			setAvatar(value);
		},
		turn(amount) {
			targetAngle += amount;
			invalidate();
		},
		setView(value) {
			view = value;
			updateCamera();
			invalidate();
		},
		setPaused(value) {
			paused = value;
			invalidate();
		},
		dispose() {
			disposed = true;
			cancelAnimationFrame(frame);
			resize.disconnect();
			intersection.disconnect();
			document.removeEventListener("visibilitychange", resume);
			reduced.removeEventListener("change", resume);
			host.removeEventListener("pointerdown", down);
			host.removeEventListener("pointermove", move);
			host.removeEventListener("pointerup", up);
			host.removeEventListener("pointercancel", up);
			renderer.domElement.removeEventListener("webglcontextlost", lost);
			disposeOwned(fighter);
			Object.values(shapes).forEach((g) => g.dispose());
			shadowGeometry.dispose();
			materials.forEach((m) => m.dispose());
			shadowMaterials.forEach((m) => m.dispose());
			pedestalMaterial.dispose();
			renderer.dispose();
			renderer.forceContextLoss();
			renderer.domElement.remove();
		}
	};
}
//#endregion
export { createAvatarScene };
