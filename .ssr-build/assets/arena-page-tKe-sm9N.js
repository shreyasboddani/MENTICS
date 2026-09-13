import { i as boot, n as Starfield, r as api$1, t as AppShell } from "../entry-server.js";
import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { toast } from "sonner";
import { ArrowRight, Brain, Calculator, Check, ChevronRight, Clock3, Dices, Flame, GripHorizontal, Maximize2, Minimize2, RotateCcw, RotateCw, Sparkles, Swords, Target, Trophy, Volume2, VolumeX, X, Zap } from "lucide-react";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
//#region \0rolldown/runtime.js
var __defProp = Object.defineProperty;
var __exportAll = (all, no_symbols) => {
	let target = {};
	for (var name in all) __defProp(target, name, {
		get: all[name],
		enumerable: true
	});
	if (!no_symbols) __defProp(target, Symbol.toStringTag, { value: "Module" });
	return target;
};
//#endregion
//#region frontend/src/arena-avatar-preview.jsx
function ArenaAvatarPreview({ avatar, label = "Your fighter", paused = false, view = "full" }) {
	const host = useRef(null);
	const scene = useRef(null);
	const latest = useRef(avatar);
	const [ready, setReady] = useState(false);
	const [failed, setFailed] = useState(false);
	useEffect(() => {
		latest.current = avatar;
		scene.current?.setAvatar(avatar);
	}, [avatar]);
	useEffect(() => {
		let cancelled = false;
		const element = host.current;
		const observer = new IntersectionObserver((entries) => {
			if (!entries[0].isIntersecting) return;
			observer.disconnect();
			import("./arena-avatar-scene-DzW3HvU1.js").then(({ createAvatarScene }) => {
				if (cancelled) return;
				scene.current = createAvatarScene(element, latest.current, () => setFailed(true));
				setReady(true);
			}).catch(() => {
				if (!cancelled) setFailed(true);
			});
		});
		observer.observe(element);
		return () => {
			cancelled = true;
			observer.disconnect();
			scene.current?.dispose();
			scene.current = null;
		};
	}, []);
	useEffect(() => {
		scene.current?.setPaused(paused);
	}, [paused, ready]);
	useEffect(() => {
		scene.current?.setView(view);
	}, [view, ready]);
	return /* @__PURE__ */ jsxs("div", {
		className: "arena-avatar-preview",
		"data-ready": ready && !failed,
		children: [
			/* @__PURE__ */ jsx("div", {
				className: "arena-avatar-canvas",
				ref: host,
				role: "img",
				"aria-label": label,
				hidden: failed
			}),
			(!ready || failed) && /* @__PURE__ */ jsx("div", {
				className: "arena-avatar-fallback",
				children: /* @__PURE__ */ jsx(ArenaFighter, {
					avatar,
					label
				})
			}),
			!failed && /* @__PURE__ */ jsxs("div", {
				className: "arena-avatar-controls",
				"aria-label": "Character viewing controls",
				children: [
					/* @__PURE__ */ jsx("button", {
						type: "button",
						"aria-label": "Rotate fighter left",
						onClick: () => scene.current?.turn(-Math.PI / 4),
						children: /* @__PURE__ */ jsx(RotateCcw, {})
					}),
					/* @__PURE__ */ jsx("span", { children: ready ? "DRAG TO ROTATE" : "PREPARING FIGHTER" }),
					/* @__PURE__ */ jsx("button", {
						type: "button",
						"aria-label": "Rotate fighter right",
						onClick: () => scene.current?.turn(Math.PI / 4),
						children: /* @__PURE__ */ jsx(RotateCw, {})
					})
				]
			})
		]
	});
}
//#endregion
//#region frontend/src/arena-fighter.jsx
var LIGHT_SHIFT = "translate(-1.4 -1)";
var INK = "#161a33";
var INK_WEIGHT = 2.6;
var LIMB_INK = 3.4;
var ARENA_AVATAR_PALETTES = {
	nova: [
		"#8b5cf6",
		"#4f46e5",
		"#f1eaff"
	],
	solar: [
		"#ffb340",
		"#e95d43",
		"#fff1c7"
	],
	glacier: [
		"#48d8ff",
		"#3974e8",
		"#e2fbff"
	],
	volt: [
		"#b5f33d",
		"#31a878",
		"#efffc6"
	],
	rose: [
		"#ff6fae",
		"#ad3f83",
		"#ffe0ef"
	],
	midnight: [
		"#5468ff",
		"#161c5a",
		"#b9c4ff"
	],
	ember: [
		"#ff7a45",
		"#8c2020",
		"#ffd9c2"
	],
	forest: [
		"#4fbf7d",
		"#1c5b3f",
		"#d6f7e2"
	],
	mono: [
		"#9aa3c4",
		"#3a4064",
		"#e9ecf8"
	],
	tide: [
		"#2fd3c0",
		"#1a5f8c",
		"#d3fbf6"
	],
	crimson: [
		"#ff5c72",
		"#7a1230",
		"#ffd6dd"
	],
	jade: [
		"#3ee08f",
		"#0f6b52",
		"#ccfbe6"
	],
	royal: [
		"#7b8cff",
		"#2c2a8f",
		"#dfe3ff"
	],
	dune: [
		"#e8c37a",
		"#9c6a2f",
		"#fff2d6"
	],
	orchid: [
		"#c77dff",
		"#5b1e91",
		"#f3e2ff"
	],
	steel: [
		"#7d93b8",
		"#2b3552",
		"#e6edf8"
	]
};
var ARENA_AVATAR_SKINS = {
	porcelain: [
		"#f7d7c4",
		"#d9a184",
		"#fff1e6"
	],
	light: [
		"#eec3a3",
		"#c9906d",
		"#fbe0cb"
	],
	sand: [
		"#e6bd94",
		"#bc8659",
		"#f7dcbd"
	],
	warm: [
		"#e0a578",
		"#b3754c",
		"#f4c9a4"
	],
	amber: [
		"#d69a63",
		"#a56a3c",
		"#eec096"
	],
	medium: [
		"#c98f68",
		"#9a6242",
		"#e3b591"
	],
	olive: [
		"#ac7b52",
		"#7d5334",
		"#c99c74"
	],
	bronze: [
		"#a06f45",
		"#6f4728",
		"#c1935f"
	],
	deep: [
		"#8d5b3d",
		"#5f3826",
		"#ab7a58"
	],
	mocha: [
		"#7a4f36",
		"#4e2e20",
		"#996b4e"
	],
	umber: [
		"#6b452f",
		"#43281c",
		"#8a6047"
	],
	ebony: [
		"#4c3227",
		"#2b1a15",
		"#6c4a3b"
	]
};
var ARENA_AVATAR_HAIR = {
	onyx: "#1b1a26",
	espresso: "#3a241e",
	chestnut: "#713f2b",
	copper: "#b95732",
	gold: "#e5b956",
	silver: "#c8d0df",
	white: "#f2f4fb",
	violet: "#6f4ad8",
	blue: "#2769bd",
	teal: "#22a89b",
	emerald: "#2f9455",
	crimson: "#b32744",
	pink: "#ef78bb",
	sunset: "#f2803f",
	ash: "#8b8fa6",
	sage: "#7fa87c",
	ember: "#e2542a",
	ice: "#a9dcf5",
	plum: "#7a3f78",
	honey: "#d9a441"
};
var ARENA_AVATAR_ACCENTS = {
	crystal: "#a8edff",
	gold: "#ffd66d",
	rose: "#ff9cc8",
	teal: "#67f0cf",
	white: "#f8fbff",
	graphite: "#5b638a",
	violet: "#c3a2ff",
	lime: "#d2fb63",
	copper: "#ff9f68",
	obsidian: "#2a2e4a",
	ice: "#cfeeff",
	ember: "#ff7d4d",
	jade: "#6ff0a8",
	blush: "#ffc2d6",
	chrome: "#dfe6f5",
	bronze: "#c78a4e"
};
var ARENA_AVATAR_EYES = {
	brown: "#5a3620",
	hazel: "#8a6a2f",
	green: "#2f7a52",
	blue: "#2f6bab",
	amber: "#b57a1e",
	violet: "#7248b8",
	grey: "#5d6780",
	crimson: "#9c2b3d",
	gold: "#c9962a",
	teal: "#22867f",
	silver: "#8d9bb5",
	rose: "#b8536e"
};
var ARENA_CUSTOMIZER_SECTIONS = [
	[
		"body",
		"Body",
		[
			[
				"frame",
				"Silhouette",
				[
					["masculine", "Masculine"],
					["feminine", "Feminine"],
					["androgynous", "Androgynous"],
					["athletic", "Athletic"]
				]
			],
			[
				"body",
				"Build",
				[
					["striker", "Striker"],
					["sentinel", "Sentinel"],
					["scout", "Scout"],
					["titan", "Titan"],
					["lithe", "Lithe"],
					["compact", "Compact"]
				]
			],
			[
				"height",
				"Height",
				[
					["short", "Short"],
					["average", "Average"],
					["tall", "Tall"]
				]
			],
			[
				"skin",
				"Skin tone",
				[
					["porcelain", "Porcelain"],
					["light", "Light"],
					["sand", "Sand"],
					["warm", "Warm"],
					["amber", "Amber"],
					["medium", "Medium"],
					["olive", "Olive"],
					["bronze", "Bronze"],
					["deep", "Deep"],
					["mocha", "Mocha"],
					["umber", "Umber"],
					["ebony", "Ebony"]
				],
				"skin"
			],
			[
				"pose",
				"Stance",
				[
					["ready", "Ready"],
					["guard", "Guard"],
					["confident", "Confident"],
					["relaxed", "Relaxed"]
				]
			]
		]
	],
	[
		"face",
		"Face",
		[
			[
				"eyes",
				"Eye color",
				[
					["brown", "Brown"],
					["hazel", "Hazel"],
					["green", "Green"],
					["blue", "Blue"],
					["amber", "Amber"],
					["violet", "Violet"],
					["grey", "Grey"],
					["crimson", "Crimson"],
					["gold", "Gold"],
					["teal", "Teal"],
					["silver", "Silver"],
					["rose", "Rose"]
				],
				"eyes"
			],
			[
				"brows",
				"Eyebrows",
				[
					["soft", "Soft"],
					["bold", "Bold"],
					["arched", "Arched"],
					["sharp", "Sharp"]
				]
			],
			[
				"expression",
				"Expression",
				[
					["calm", "Calm"],
					["focused", "Focused"],
					["fierce", "Fierce"],
					["grin", "Grin"]
				]
			],
			[
				"face",
				"Face detail",
				[
					["natural", "None"],
					["freckles", "Freckles"],
					["liner", "Liner"],
					["warpaint", "War paint"],
					["blush", "Blush"],
					["scar", "Scar"],
					["cyber", "Cyber lines"],
					["tattoo", "Tattoo"]
				]
			],
			[
				"facial_hair",
				"Facial hair",
				[
					["none", "None"],
					["stubble", "Stubble"],
					["mustache", "Mustache"],
					["goatee", "Goatee"],
					["full", "Full beard"]
				]
			]
		]
	],
	[
		"hair",
		"Hair",
		[[
			"hair",
			"Style",
			[
				["crop", "Crop"],
				["fade", "Fade"],
				["buzz", "Buzz"],
				["wave", "Wave"],
				["spike", "Spike"],
				["mohawk", "Mohawk"],
				["undercut", "Undercut"],
				["pixie", "Pixie"],
				["bob", "Bob"],
				["ponytail", "Ponytail"],
				["twin_tails", "Twin tails"],
				["curls", "Curls"],
				["afro", "Afro"],
				["locs", "Locs"],
				["braids", "Braids"],
				["long", "Long"],
				["flow", "Flow"],
				["bun", "Bun"]
			]
		], [
			"hair_color",
			"Color",
			[
				["onyx", "Onyx"],
				["espresso", "Espresso"],
				["chestnut", "Chestnut"],
				["copper", "Copper"],
				["gold", "Gold"],
				["silver", "Silver"],
				["white", "White"],
				["violet", "Violet"],
				["blue", "Blue"],
				["teal", "Teal"],
				["emerald", "Emerald"],
				["crimson", "Crimson"],
				["pink", "Pink"],
				["sunset", "Sunset"],
				["ash", "Ash"],
				["sage", "Sage"],
				["ember", "Ember"],
				["ice", "Ice"],
				["plum", "Plum"],
				["honey", "Honey"]
			],
			"hair"
		]]
	],
	[
		"outfit",
		"Outfit",
		[
			[
				"outfit",
				"Top / armor",
				[
					["combat", "Combat"],
					["academy", "Academy"],
					["varsity", "Varsity"],
					["techwear", "Techwear"],
					["street", "Street"],
					["champion", "Champion"],
					["hoodie", "Hoodie"],
					["jersey", "Jersey"],
					["flight", "Flight suit"],
					["scholar", "Scholar robe"]
				]
			],
			[
				"palette",
				"Main color",
				[
					["nova", "Nova"],
					["solar", "Solar"],
					["glacier", "Glacier"],
					["volt", "Volt"],
					["rose", "Rose"],
					["midnight", "Midnight"],
					["ember", "Ember"],
					["forest", "Forest"],
					["mono", "Mono"],
					["tide", "Tide"],
					["crimson", "Crimson"],
					["jade", "Jade"],
					["royal", "Royal"],
					["dune", "Dune"],
					["orchid", "Orchid"],
					["steel", "Steel"]
				],
				"palette"
			],
			[
				"accent",
				"Trim color",
				[
					["crystal", "Crystal"],
					["gold", "Gold"],
					["rose", "Rose"],
					["teal", "Teal"],
					["white", "White"],
					["graphite", "Graphite"],
					["violet", "Violet"],
					["lime", "Lime"],
					["copper", "Copper"],
					["obsidian", "Obsidian"],
					["ice", "Ice"],
					["ember", "Ember"],
					["jade", "Jade"],
					["blush", "Blush"],
					["chrome", "Chrome"],
					["bronze", "Bronze"]
				],
				"accent"
			],
			[
				"marking",
				"Suit pattern",
				[
					["none", "None"],
					["stripes", "Racing stripes"],
					["circuit", "Circuitry"],
					["chevron", "Chevrons"],
					["stars", "Stars"],
					["scales", "Scales"]
				]
			],
			[
				"bottom",
				"Bottom",
				[
					["tactical", "Tactical"],
					["fitted", "Fitted"],
					["cargo", "Cargo"],
					["battle_skirt", "Battle skirt"],
					["shorts", "Shorts"],
					["pleated", "Pleated"],
					["joggers", "Joggers"]
				]
			],
			[
				"gloves",
				"Hands",
				[
					["tech", "Tech gloves"],
					["fingerless", "Fingerless"],
					["gauntlets", "Gauntlets"],
					["wraps", "Wraps"],
					["claws", "Claws"],
					["none", "Bare"]
				]
			],
			[
				"footwear",
				"Footwear",
				[
					["boots", "Combat boots"],
					["high_tops", "High-tops"],
					["runners", "Runners"],
					["armored", "Armored"],
					["low_tops", "Low-tops"],
					["greaves", "Greaves"],
					["barefoot", "Barefoot"]
				]
			]
		]
	],
	[
		"gear",
		"Gear",
		[
			[
				"shoulder",
				"Shoulders",
				[
					["none", "None"],
					["pauldrons", "Pauldrons"],
					["epaulettes", "Epaulettes"],
					["spikes", "Spikes"],
					["sash", "Sash"]
				]
			],
			[
				"waist",
				"Waist gear",
				[
					["none", "None"],
					["pouch", "Pouch"],
					["wrap", "Hip wrap"],
					["chain", "Chain"],
					["holsters", "Holsters"]
				]
			],
			[
				"gear",
				"Head gear",
				[
					["visor", "Visor"],
					["comms", "Comms"],
					["crown", "Crown"],
					["glasses", "Glasses"],
					["shades", "Shades"],
					["headband", "Headband"],
					["earrings", "Earrings"],
					["mask", "Mask"],
					["cap", "Cap"],
					["helmet", "Helmet"],
					["none", "None"]
				]
			],
			[
				"back",
				"Back gear",
				[
					["none", "None"],
					["cape", "Cape"],
					["half_cape", "Half cape"],
					["energy_pack", "Energy pack"],
					["banner", "Rank banner"],
					["wings", "Wings"],
					["quiver", "Quiver"],
					["jetpack", "Jetpack"]
				]
			],
			[
				"emblem",
				"Chest emblem",
				[
					["bolt", "Bolt"],
					["mind", "Mind"],
					["target", "Target"],
					["shield", "Shield"],
					["star", "Star"],
					["flame", "Flame"],
					["crown", "Crown"],
					["atom", "Atom"],
					["book", "Book"],
					["wave", "Wave"]
				]
			],
			[
				"aura",
				"Power aura",
				[
					["pulse", "Pulse"],
					["flare", "Flare"],
					["orbit", "Orbit"],
					["spark", "Spark"],
					["halo", "Halo"],
					["embers", "Embers"],
					["frost", "Frost"],
					["storm", "Storm"],
					["none", "None"]
				]
			]
		]
	]
];
var ARENA_AVATAR_FIELDS = ARENA_CUSTOMIZER_SECTIONS.flatMap(([, , groups]) => groups);
var ARENA_AVATAR_OPTIONS = Object.fromEntries(ARENA_AVATAR_FIELDS.map(([key, , choices]) => [key, choices.map(([value]) => value)]));
var ARENA_AVATAR_DEFAULT = {
	frame: "masculine",
	body: "striker",
	height: "average",
	skin: "medium",
	pose: "ready",
	eyes: "brown",
	brows: "soft",
	expression: "calm",
	face: "natural",
	facial_hair: "none",
	hair: "crop",
	hair_color: "onyx",
	outfit: "combat",
	palette: "nova",
	accent: "crystal",
	marking: "none",
	bottom: "tactical",
	gloves: "tech",
	footwear: "boots",
	shoulder: "none",
	waist: "none",
	gear: "visor",
	back: "none",
	emblem: "bolt",
	aura: "pulse"
};
var SWATCH_SOURCES = {
	palette: (value) => ARENA_AVATAR_PALETTES[value]?.[0],
	skin: (value) => ARENA_AVATAR_SKINS[value]?.[0],
	hair: (value) => ARENA_AVATAR_HAIR[value],
	accent: (value) => ARENA_AVATAR_ACCENTS[value],
	eyes: (value) => ARENA_AVATAR_EYES[value]
};
function normalizeArenaAvatar(avatar) {
	const source = avatar && typeof avatar === "object" ? avatar : {};
	return Object.fromEntries(Object.entries(ARENA_AVATAR_DEFAULT).map(([key, fallback]) => [key, ARENA_AVATAR_OPTIONS[key].includes(source[key]) ? source[key] : fallback]));
}
function randomArenaAvatar() {
	const pick = (list) => list[Math.floor(Math.random() * list.length)];
	return Object.fromEntries(Object.keys(ARENA_AVATAR_DEFAULT).map((key) => [key, pick(ARENA_AVATAR_OPTIONS[key])]));
}
var BUILDS = {
	striker: {
		shoulder: 34,
		chest: 31,
		waist: 23,
		hip: 26,
		arm: 10.5,
		thigh: 15,
		calf: 11.5,
		neck: 8.5
	},
	sentinel: {
		shoulder: 41,
		chest: 38,
		waist: 29,
		hip: 31,
		arm: 13.5,
		thigh: 18,
		calf: 13.5,
		neck: 10.5
	},
	scout: {
		shoulder: 28,
		chest: 26,
		waist: 19,
		hip: 22,
		arm: 8.5,
		thigh: 12.5,
		calf: 9.5,
		neck: 7.4
	},
	titan: {
		shoulder: 46,
		chest: 43,
		waist: 35,
		hip: 36,
		arm: 16,
		thigh: 21,
		calf: 15.5,
		neck: 12
	},
	lithe: {
		shoulder: 26,
		chest: 24,
		waist: 18,
		hip: 21,
		arm: 8,
		thigh: 11.5,
		calf: 9,
		neck: 7
	},
	compact: {
		shoulder: 36,
		chest: 34,
		waist: 28,
		hip: 29,
		arm: 12,
		thigh: 17,
		calf: 13,
		neck: 9.5
	}
};
var FRAMES = {
	masculine: {
		shoulder: 1.07,
		waist: 1.06,
		hip: .92,
		headW: 1,
		jaw: 1.06,
		chinY: 0
	},
	feminine: {
		shoulder: .88,
		waist: .82,
		hip: 1.08,
		headW: .95,
		jaw: .87,
		chinY: -1
	},
	androgynous: {
		shoulder: .98,
		waist: .94,
		hip: 1,
		headW: .98,
		jaw: .97,
		chinY: 0
	},
	athletic: {
		shoulder: 1.14,
		waist: .86,
		hip: .97,
		headW: .96,
		jaw: 1.01,
		chinY: 0
	}
};
var POSES = {
	ready: {
		elbow: .62,
		wrist: .98,
		drop: 20
	},
	guard: {
		elbow: 1.15,
		wrist: .74,
		drop: 2
	},
	confident: {
		elbow: 1.35,
		wrist: .58,
		drop: 10
	},
	relaxed: {
		elbow: .34,
		wrist: 1.06,
		drop: 26
	}
};
var HEIGHTS = {
	short: {
		leg: .87,
		head: 1.09
	},
	average: {
		leg: 1,
		head: 1
	},
	tall: {
		leg: 1.13,
		head: .93
	}
};
/** Landmarks for one height, always standing on the same ground line. */
function buildSkeleton(height) {
	const h = HEIGHTS[height] || HEIGHTS.average;
	const hip = 138;
	const ankle = hip + 112 * h.leg;
	const shift = 268 - (ankle + 8);
	return {
		headTop: 20 + shift,
		chin: 66 + shift,
		neck: 72 + shift,
		shoulder: 82 + shift,
		chest: 100 + shift,
		waist: 124 + shift,
		hip: hip + shift,
		knee: hip + 58 * h.leg + shift,
		ankle: ankle + shift,
		ground: 268,
		centerX: 100,
		headScale: h.head
	};
}
var EMBLEM_PATHS = {
	bolt: {
		d: "M1.6 -6.4 L-3.6 0.4 L-0.5 0.4 L-1.7 6.4 L3.6 -0.7 L0.5 -0.7 Z",
		fill: true
	},
	mind: { d: "M-4.6 -2.6 A3.1 3.1 0 0 1 0 -5.6 A3.1 3.1 0 0 1 4.6 -2.6 A3.2 3.2 0 0 1 4.2 3 A3.5 3.5 0 0 1 0 5.7 A3.5 3.5 0 0 1 -4.2 3 A3.2 3.2 0 0 1 -4.6 -2.6 Z M0 -5.6 L0 5.7 M-3 -1 L3 -1 M-2.6 2.3 L2.6 2.3" },
	target: { d: "M0 -6.2 A6.2 6.2 0 1 1 -0.1 -6.2 Z M0 -2.7 A2.7 2.7 0 1 1 -0.1 -2.7 Z" },
	shield: {
		d: "M0 -6.4 L5.5 -3.9 L5.5 1 Q5.5 4.7 0 6.5 Q-5.5 4.7 -5.5 1 L-5.5 -3.9 Z",
		fill: true
	},
	star: {
		d: "M0 -6.6 L1.9 -2 L6.6 -1.8 L2.9 1.3 L4.1 6 L0 3.3 L-4.1 6 L-2.9 1.3 L-6.6 -1.8 L-1.9 -2 Z",
		fill: true
	},
	flame: {
		d: "M0 -6.8 Q3 -2.8 2.7 -0.4 Q2.5 1.5 1 1.7 Q1.9 -0.8 0 -2.9 Q-1 -0.6 -2.5 0.6 Q-3.5 2.7 -1.8 4.7 Q-0.6 6.1 0 6.6 Q3.7 5.3 4.1 1.6 Q4.5 -2 0 -6.8 Z",
		fill: true
	},
	crown: {
		d: "M-6.2 3.9 L-6.2 -4.6 L-3.1 -0.6 L0 -5.6 L3.1 -0.6 L6.2 -4.6 L6.2 3.9 Z",
		fill: true
	},
	atom: { d: "M-1.8 0 A1.8 1.8 0 1 1 1.8 0 A1.8 1.8 0 1 1 -1.8 0 M-6.4 0 A6.4 2.6 0 1 1 6.4 0 A6.4 2.6 0 1 1 -6.4 0 M-3.2 -5.54 A6.4 2.6 60 1 1 3.2 5.54 A6.4 2.6 60 1 1 -3.2 -5.54 M-3.2 5.54 A6.4 2.6 -60 1 1 3.2 -5.54 A6.4 2.6 -60 1 1 -3.2 5.54" },
	book: { d: "M-5.8 -4.6 Q-2.8 -6 0 -4.4 Q2.8 -6 5.8 -4.6 L5.8 4.6 Q2.8 3.2 0 4.8 Q-2.8 3.2 -5.8 4.6 Z M0 -4.4 L0 4.8" },
	wave: { d: "M-6.2 1.4 Q-4.2 -2.2 -2.1 1.4 Q0 5 2.1 1.4 Q4.2 -2.2 6.2 1.4 M-6.2 -3.2 Q-4.2 -6.8 -2.1 -3.2 Q0 0.4 2.1 -3.2 Q4.2 -6.8 6.2 -3.2" }
};
var HAIRLINE = .27;
var TEMPLE = .52;
/** A skull-hugging cap. `grow` puffs it out, `line` moves the fringe down. */
function hairCap(head, { grow = 0, line = HAIRLINE, temple = TEMPLE } = {}) {
	const { cx, top, w, h } = head;
	const l = cx - w - grow;
	const r = cx + w + grow;
	const crown = top - h * .06 - grow;
	return `M${l} ${top + h * temple}
          C${l} ${crown} ${cx - w * .55} ${crown - 2} ${cx} ${crown - 2}
          C${cx + w * .55} ${crown - 2} ${r} ${crown} ${r} ${top + h * temple}
          C${cx + w * .72} ${top + h * (line + .06)} ${cx + w * .34} ${top + h * line} ${cx} ${top + h * line}
          C${cx - w * .34} ${top + h * line} ${cx - w * .72} ${top + h * (line + .06)} ${l} ${top + h * temple} Z`;
}
/** Front hair: the cap on the skull plus the style's own silhouette. */
function hairFront(style, head) {
	const { cx, top, w, h } = head;
	const l = cx - w;
	const r = cx + w;
	switch (style) {
		case "buzz": return hairCap(head, {
			grow: -1.5,
			line: .2,
			temple: .4
		});
		case "fade": return hairCap(head, {
			grow: -1,
			line: .24,
			temple: .42
		});
		case "undercut": return hairCap(head, {
			grow: 1.5,
			line: .24,
			temple: .3
		});
		case "wave": return `M${l - 2} ${top + h * .56} C${l - 3} ${top - h * .14} ${cx - w * .5} ${top - h * .16} ${cx} ${top - h * .16}
              C${cx + w * .6} ${top - h * .16} ${r + 3} ${top - h * .12} ${r + 2} ${top + h * .5}
              C${cx + w * .7} ${top + h * .2} ${cx + w * .3} ${top + h * .34} ${cx - w * .06} ${top + h * .26}
              C${cx - w * .4} ${top + h * .2} ${cx - w * .7} ${top + h * .34} ${l - 2} ${top + h * .56} Z`;
		case "spike": return `M${l - 2} ${top + h * .5} L${l - 1} ${top - h * .18} L${cx - w * .46} ${top + h * .06}
              L${cx - w * .22} ${top - h * .3} L${cx + w * .02} ${top + h * .04}
              L${cx + w * .26} ${top - h * .32} L${cx + w * .5} ${top + h * .05}
              L${r + 1} ${top - h * .16} L${r + 2} ${top + h * .5}
              C${cx + w * .7} ${top + h * .22} ${cx - w * .7} ${top + h * .22} ${l - 2} ${top + h * .5} Z`;
		case "mohawk": return `M${cx - w * .34} ${top + h * .42} L${cx - w * .3} ${top - h * .34}
              C${cx - w * .1} ${top - h * .46} ${cx + w * .16} ${top - h * .44} ${cx + w * .32} ${top - h * .26}
              L${cx + w * .34} ${top + h * .42}
              C${cx + w * .1} ${top + h * .3} ${cx - w * .1} ${top + h * .3} ${cx - w * .34} ${top + h * .42} Z`;
		case "pixie": return `M${l - 3} ${top + h * .5} C${l - 4} ${top - h * .12} ${cx - w * .5} ${top - h * .14} ${cx} ${top - h * .14}
              C${cx + w * .6} ${top - h * .14} ${r + 4} ${top - h * .1} ${r + 3} ${top + h * .34}
              L${r + 6} ${top + h * .6} C${cx + w * .8} ${top + h * .3} ${cx + w * .3} ${top + h * .3} ${cx} ${top + h * .24}
              C${cx - w * .5} ${top + h * .18} ${l - 1} ${top + h * .3} ${l - 3} ${top + h * .5} Z`;
		case "bob": return `M${l - 5} ${top + h * 1.02} C${l - 6} ${top - h * .12} ${cx - w * .5} ${top - h * .14} ${cx} ${top - h * .14}
              C${cx + w * .6} ${top - h * .14} ${r + 6} ${top - h * .1} ${r + 5} ${top + h * 1.02}
              C${r + 2} ${top + h * .5} ${cx + w * .86} ${top + h * .3} ${cx + w * .2} ${top + h * .28}
              C${cx - w * .4} ${top + h * .26} ${l + 1} ${top + h * .32} ${l - 5} ${top + h * 1.02} Z`;
		case "curls": return hairCap(head, {
			grow: 5,
			line: .27,
			temple: .62
		});
		case "afro": return hairCap(head, {
			grow: 2,
			line: .27,
			temple: .5
		});
		case "locs": return hairCap(head, {
			grow: 2,
			line: .26,
			temple: .5
		});
		case "braids": return hairCap(head, {
			grow: .5,
			line: .25,
			temple: .48
		});
		case "long":
		case "flow": return `M${l - 4} ${top + h * .72} C${l - 5} ${top - h * .13} ${cx - w * .5} ${top - h * .15} ${cx} ${top - h * .15}
              C${cx + w * .6} ${top - h * .15} ${r + 5} ${top - h * .11} ${r + 4} ${top + h * .68}
              C${r + 1} ${top + h * .36} ${cx + w * .7} ${top + h * .26} ${cx + w * .18} ${top + h * .3}
              C${cx - w * .3} ${top + h * .34} ${cx - w * .55} ${top + h * .2} ${cx - w * .75} ${top + h * .3}
              C${cx - w * .95} ${top + h * .4} ${l - 2} ${top + h * .44} ${l - 4} ${top + h * .72} Z`;
		case "ponytail":
		case "twin_tails":
		case "bun": return hairCap(head, {
			grow: 1,
			line: .26,
			temple: .5
		});
		default: return hairCap(head);
	}
}
/** Back hair: everything falling behind the head and shoulders. */
function hairBack(style, head, shoulderY) {
	const { cx, top, w, h } = head;
	const bottom = top + h;
	switch (style) {
		case "bob": return [`M${cx - w - 6} ${top + h * .3} Q${cx - w - 8} ${bottom + 12} ${cx - w + 1} ${bottom + 14}
               L${cx + w - 1} ${bottom + 14} Q${cx + w + 8} ${bottom + 12} ${cx + w + 6} ${top + h * .3} Z`];
		case "pixie": return [`M${cx - w - 3} ${top + h * .36} Q${cx - w - 5} ${bottom + 4} ${cx - w + 2} ${bottom + 6}
               L${cx + w - 2} ${bottom + 6} Q${cx + w + 5} ${bottom + 4} ${cx + w + 3} ${top + h * .36} Z`];
		case "long": return [`M${cx - w - 5} ${top + h * .25} Q${cx - w - 12} ${shoulderY + 44} ${cx - w - 4} ${shoulderY + 58}
               Q${cx} ${shoulderY + 52} ${cx + w + 4} ${shoulderY + 58}
               Q${cx + w + 12} ${shoulderY + 44} ${cx + w + 5} ${top + h * .25} Z`];
		case "flow": return [`M${cx - w - 6} ${top + h * .24} Q${cx - w - 20} ${shoulderY + 30} ${cx - w - 10} ${shoulderY + 50}
               Q${cx - w - 2} ${shoulderY + 38} ${cx} ${shoulderY + 44}
               Q${cx + w + 2} ${shoulderY + 38} ${cx + w + 10} ${shoulderY + 50}
               Q${cx + w + 20} ${shoulderY + 30} ${cx + w + 6} ${top + h * .24} Z`];
		case "ponytail": return [`M${cx + w - 2} ${top + h * .22} Q${cx + w + 17} ${top + h * .5} ${cx + w + 14} ${bottom + 28}
               Q${cx + w + 10} ${bottom + 38} ${cx + w + 2} ${bottom + 31}
               Q${cx + w + 9} ${bottom + 6} ${cx + w - 4} ${top + h * .6} Z`];
		case "twin_tails": return [`M${cx - w + 1} ${top + h * .28} Q${cx - w - 17} ${top + h * .6} ${cx - w - 13} ${bottom + 22}
         Q${cx - w - 8} ${bottom + 30} ${cx - w - 2} ${bottom + 22} Q${cx - w - 6} ${bottom} ${cx - w + 4} ${top + h * .62} Z`, `M${cx + w - 1} ${top + h * .28} Q${cx + w + 17} ${top + h * .6} ${cx + w + 13} ${bottom + 22}
         Q${cx + w + 8} ${bottom + 30} ${cx + w + 2} ${bottom + 22} Q${cx + w + 6} ${bottom} ${cx + w - 4} ${top + h * .62} Z`];
		case "bun": return [`M${cx} ${top - h * .2} m-11 0 a11 11 0 1 0 22 0 a11 11 0 1 0 -22 0 Z`];
		case "curls": {
			const reach = w + 9;
			const bumps = 5;
			const step = reach * 2 / bumps;
			let edge = "";
			for (let i = 0; i < bumps; i += 1) edge += ` q${-step * .5} 11 ${-step} 0`;
			return [`M${cx - reach} ${bottom + 2} L${cx - reach} ${top + h * .3} a${reach} ${reach * .86} 0 0 1 ${reach * 2} 0 L${cx + reach} ${bottom + 2}${edge} Z`];
		}
		case "afro": {
			const reach = w * 1.32;
			const cy = top + h * .12;
			return [`M${cx - reach} ${cy} a${reach} ${reach} 0 1 0 ${reach * 2} 0 a${reach} ${reach} 0 1 0 ${-reach * 2} 0 Z`];
		}
		case "locs": return [
			-2,
			-1,
			0,
			1,
			2
		].map((i) => {
			const x = cx + i * (w * .46);
			const foot = bottom + 24 + Math.abs(i) * -4;
			return `M${x - 5.5} ${top + h * .3} L${x + 5.5} ${top + h * .3} L${x + 5.5} ${foot} a5.5 5.5 0 0 1 -11 0 Z`;
		});
		case "braids": return [`M${cx - w - 1} ${top + h * .5} Q${cx - w - 9} ${bottom + 18} ${cx - w - 5} ${bottom + 36}
         L${cx - w + 4} ${bottom + 35} Q${cx - w + 1} ${bottom + 14} ${cx - w + 6} ${top + h * .56} Z`, `M${cx + w + 1} ${top + h * .5} Q${cx + w + 9} ${bottom + 18} ${cx + w + 5} ${bottom + 36}
         L${cx + w - 4} ${bottom + 35} Q${cx + w - 1} ${bottom + 14} ${cx + w - 6} ${top + h * .56} Z`];
		default: return [];
	}
}
var BROW_SHAPES = {
	soft: (x, y, s) => `M${x - 5 * s} ${y + .4} Q${x} ${y - 2.6} ${x + 5 * s} ${y - .2}`,
	bold: (x, y, s) => `M${x - 5.4 * s} ${y + .6} Q${x} ${y - 3} ${x + 5.4 * s} ${y}`,
	arched: (x, y, s) => `M${x - 5 * s} ${y + 1.6} Q${x - .6 * s} ${y - 4.4} ${x + 5 * s} ${y - .4}`,
	sharp: (x, y, s) => `M${x - 5.2 * s} ${y + 2} L${x + 1 * s} ${y - 2.8} L${x + 5.2 * s} ${y - 1.4}`
};
function ArenaFace({ loadout, head, skin, accent, hairColor, eyeColor }) {
	const { cx, top, h, w } = head;
	const hidden = ["visor", "helmet"].includes(loadout.gear);
	const eyeY = top + h * .54;
	const jaw = top + h * .98;
	const eyeDx = w * .44;
	const browY = eyeY - h * .14;
	const browWeight = loadout.brows === "bold" ? 2.9 : loadout.brows === "sharp" ? 2.2 : 2;
	const fierce = loadout.expression === "fierce";
	const focused = loadout.expression === "focused";
	const grin = loadout.expression === "grin";
	const lidDrop = fierce ? 1.5 : focused ? 1 : 0;
	const mouth = grin ? `M${cx - 6} ${eyeY + 13.6} Q${cx} ${eyeY + 19.4} ${cx + 6} ${eyeY + 13.6} Q${cx} ${eyeY + 15.6} ${cx - 6} ${eyeY + 13.6} Z` : fierce ? `M${cx - 5.4} ${eyeY + 16} Q${cx} ${eyeY + 13} ${cx + 5.4} ${eyeY + 16}` : focused ? `M${cx - 4.6} ${eyeY + 14.8} L${cx + 4.6} ${eyeY + 14.8}` : `M${cx - 5.2} ${eyeY + 14.2} Q${cx} ${eyeY + 17.4} ${cx + 5.2} ${eyeY + 14.2}`;
	return /* @__PURE__ */ jsxs("g", {
		className: "arena-fighter-face",
		children: [
			/* @__PURE__ */ jsx("ellipse", {
				cx: cx - w,
				cy: eyeY + 2,
				rx: w * .13,
				ry: h * .13,
				fill: skin[1]
			}),
			/* @__PURE__ */ jsx("ellipse", {
				cx: cx + w,
				cy: eyeY + 2,
				rx: w * .13,
				ry: h * .13,
				fill: skin[1]
			}),
			!hidden && /* @__PURE__ */ jsxs(Fragment, { children: [
				[-1, 1].map((side) => /* @__PURE__ */ jsx("path", {
					d: BROW_SHAPES[loadout.brows] ? BROW_SHAPES[loadout.brows](cx + side * eyeDx, browY + (fierce ? 1.6 : 0), side) : "",
					stroke: hairColor,
					strokeWidth: browWeight,
					strokeLinecap: "round",
					strokeLinejoin: "round",
					fill: "none",
					opacity: ".92"
				}, `brow${side}`)),
				[-1, 1].map((side) => /* @__PURE__ */ jsxs("g", { children: [
					/* @__PURE__ */ jsx("path", {
						d: `M${cx + side * eyeDx - 4.8} ${eyeY} Q${cx + side * eyeDx} ${eyeY - 3.5 + lidDrop} ${cx + side * eyeDx + 4.8} ${eyeY}
                  Q${cx + side * eyeDx} ${eyeY + 3.3} ${cx + side * eyeDx - 4.8} ${eyeY} Z`,
						fill: "#fdfaff",
						stroke: "#2a2036",
						strokeWidth: ".7"
					}),
					/* @__PURE__ */ jsx("circle", {
						cx: cx + side * eyeDx + side * .4,
						cy: eyeY + .2,
						r: "2.2",
						fill: eyeColor
					}),
					/* @__PURE__ */ jsx("circle", {
						cx: cx + side * eyeDx + side * .4,
						cy: eyeY + .2,
						r: "1",
						fill: "#150f21"
					}),
					/* @__PURE__ */ jsx("circle", {
						cx: cx + side * eyeDx + side * .4 - .9,
						cy: eyeY - .8,
						r: ".6",
						fill: "#fff",
						opacity: ".95"
					})
				] }, `eye${side}`)),
				/* @__PURE__ */ jsx("path", {
					d: `M${cx - 1.6} ${eyeY + 5} Q${cx - 2.5} ${eyeY + 9.6} ${cx + 1.4} ${eyeY + 9.8}`,
					stroke: skin[1],
					strokeWidth: "1.6",
					strokeLinecap: "round",
					fill: "none"
				})
			] }),
			loadout.facial_hair !== "none" && !hidden && /* @__PURE__ */ jsxs("g", {
				fill: hairColor,
				children: [
					loadout.facial_hair === "full" && /* @__PURE__ */ jsx("path", { d: `M${cx - w * .84} ${eyeY + 7}
                  C${cx - w * .86} ${jaw - 6} ${cx - w * .5} ${jaw + 3} ${cx} ${jaw + 4}
                  C${cx + w * .5} ${jaw + 3} ${cx + w * .86} ${jaw - 6} ${cx + w * .84} ${eyeY + 7}
                  C${cx + w * .5} ${eyeY + 13} ${cx + w * .2} ${eyeY + 11} ${cx} ${eyeY + 11}
                  C${cx - w * .2} ${eyeY + 11} ${cx - w * .5} ${eyeY + 13} ${cx - w * .84} ${eyeY + 7} Z` }),
					loadout.facial_hair === "goatee" && /* @__PURE__ */ jsx("path", { d: `M${cx - w * .34} ${eyeY + 12.5}
                  C${cx - w * .36} ${jaw - 5} ${cx - w * .22} ${jaw + 2} ${cx} ${jaw + 2.5}
                  C${cx + w * .22} ${jaw + 2} ${cx + w * .36} ${jaw - 5} ${cx + w * .34} ${eyeY + 12.5}
                  C${cx + w * .16} ${eyeY + 15} ${cx - w * .16} ${eyeY + 15} ${cx - w * .34} ${eyeY + 12.5} Z` }),
					loadout.facial_hair === "stubble" && /* @__PURE__ */ jsx("path", {
						d: `M${cx - w * .82} ${eyeY + 8}
                  C${cx - w * .84} ${jaw - 6} ${cx - w * .5} ${jaw + 2} ${cx} ${jaw + 3}
                  C${cx + w * .5} ${jaw + 2} ${cx + w * .84} ${jaw - 6} ${cx + w * .82} ${eyeY + 8}
                  C${cx + w * .5} ${eyeY + 14} ${cx - w * .5} ${eyeY + 14} ${cx - w * .82} ${eyeY + 8} Z`,
						opacity: ".26"
					}),
					[
						"mustache",
						"goatee",
						"full"
					].includes(loadout.facial_hair) && /* @__PURE__ */ jsx("path", { d: `M${cx - w * .36} ${eyeY + 11.6} C${cx - w * .2} ${eyeY + 8.2} ${cx + w * .2} ${eyeY + 8.2} ${cx + w * .36} ${eyeY + 11.6}
                  C${cx + w * .18} ${eyeY + 12.8} ${cx - w * .18} ${eyeY + 12.8} ${cx - w * .36} ${eyeY + 11.6} Z` })
				]
			}),
			!hidden && /* @__PURE__ */ jsx("path", {
				d: mouth,
				stroke: "#8d4d54",
				strokeWidth: grin ? 1 : 1.8,
				strokeLinecap: "round",
				fill: grin ? "#8d4d54" : "none"
			}),
			loadout.face === "freckles" && !hidden && [-1, 1].flatMap((side) => [
				0,
				1,
				2
			].map((i) => /* @__PURE__ */ jsx("circle", {
				cx: cx + side * (eyeDx + 1) + (i - 1) * 2.6,
				cy: eyeY + 6.4 + i % 2 * 1.8,
				r: ".7",
				fill: skin[1],
				opacity: ".8"
			}, `f${side}-${i}`))),
			loadout.face === "liner" && !hidden && [-1, 1].map((side) => /* @__PURE__ */ jsx("path", {
				d: `M${cx + side * (eyeDx + 4.8)} ${eyeY - .4} l${side * 3.6} -2.4`,
				stroke: "#241a33",
				strokeWidth: "1.5",
				strokeLinecap: "round",
				fill: "none"
			}, `l${side}`)),
			loadout.face === "warpaint" && [-1, 1].map((side) => /* @__PURE__ */ jsx("path", {
				d: `M${cx + side * (w - 1)} ${eyeY - 1} L${cx + side * w * .2} ${eyeY - 2.6}
                                 L${cx + side * w * .2} ${eyeY + 3.8} L${cx + side * (w - 1)} ${eyeY + 4.6} Z`,
				fill: accent,
				opacity: ".75"
			}, `w${side}`)),
			loadout.face === "blush" && !hidden && [-1, 1].map((side) => /* @__PURE__ */ jsx("ellipse", {
				cx: cx + side * (eyeDx + 3),
				cy: eyeY + 6.6,
				rx: "4.4",
				ry: "2.6",
				fill: "#f0748c",
				opacity: ".3"
			}, `b${side}`)),
			loadout.face === "scar" && /* @__PURE__ */ jsx("path", {
				d: `M${cx + eyeDx + 1} ${eyeY - 8} L${cx + eyeDx - 2} ${eyeY + 7}`,
				stroke: skin[1],
				strokeWidth: "1.5",
				strokeLinecap: "round",
				fill: "none",
				opacity: ".9"
			}),
			loadout.face === "cyber" && /* @__PURE__ */ jsxs("g", {
				stroke: accent,
				strokeWidth: "1.2",
				fill: "none",
				opacity: ".9",
				children: [
					/* @__PURE__ */ jsx("path", { d: `M${cx + eyeDx + 5} ${eyeY - 5} L${cx + w - 1} ${eyeY - 5} L${cx + w - 1} ${eyeY + 4}` }),
					/* @__PURE__ */ jsx("circle", {
						cx: cx + eyeDx + 5,
						cy: eyeY - 5,
						r: "1.4",
						fill: accent,
						stroke: "none"
					}),
					/* @__PURE__ */ jsx("path", { d: `M${cx - eyeDx - 5} ${eyeY + 7} L${cx - w + 1} ${eyeY + 7}` })
				]
			}),
			loadout.face === "tattoo" && /* @__PURE__ */ jsx("path", {
				d: `M${cx - eyeDx - 3} ${eyeY - 7} q-4 5 0 10 q4 5 0 9`,
				stroke: accent,
				strokeWidth: "1.6",
				strokeLinecap: "round",
				fill: "none",
				opacity: ".85"
			})
		]
	});
}
function ArenaHeadGear({ gear, head, colors, accent }) {
	const { cx, top, w, h } = head;
	const eyeY = top + h * .54;
	switch (gear) {
		case "visor": return /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("path", {
			d: `M${cx - w - 1} ${eyeY - 5} Q${cx} ${eyeY - 8.6} ${cx + w + 1} ${eyeY - 5}
                  L${cx + w + 1} ${eyeY + 3.6} Q${cx} ${eyeY + 7.8} ${cx - w - 1} ${eyeY + 3.6} Z`,
			fill: colors[1],
			stroke: accent,
			strokeWidth: "1.6",
			opacity: ".95"
		}), /* @__PURE__ */ jsx("path", {
			d: `M${cx - w + 2} ${eyeY - 3.4} Q${cx - w * .3} ${eyeY - 5} ${cx - w * .1} ${eyeY + 2.6}`,
			stroke: "#ffffff",
			strokeWidth: "1.8",
			strokeLinecap: "round",
			fill: "none",
			opacity: ".45"
		})] });
		case "shades": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - w - 1} ${eyeY - 4.6} L${cx - 1.4} ${eyeY - 4.6} L${cx - 2.4} ${eyeY + 4.4}
                  Q${cx - w * .6} ${eyeY + 7.4} ${cx - w - 1} ${eyeY + 1.4} Z`,
				fill: "#1d2033"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx + w + 1} ${eyeY - 4.6} L${cx + 1.4} ${eyeY - 4.6} L${cx + 2.4} ${eyeY + 4.4}
                  Q${cx + w * .6} ${eyeY + 7.4} ${cx + w + 1} ${eyeY + 1.4} Z`,
				fill: "#1d2033"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - 2} ${eyeY - 4} L${cx + 2} ${eyeY - 4}`,
				stroke: accent,
				strokeWidth: "2",
				strokeLinecap: "round"
			})
		] });
		case "comms": return /* @__PURE__ */ jsxs("g", {
			fill: "none",
			stroke: accent,
			strokeWidth: "2.4",
			strokeLinecap: "round",
			children: [
				/* @__PURE__ */ jsx("path", { d: `M${cx - w - 2} ${eyeY - 1} a${w + 2} ${h * .5} 0 0 1 ${2 * w + 4} 0` }),
				/* @__PURE__ */ jsx("rect", {
					x: cx - w - 5,
					y: eyeY - 2,
					width: "6",
					height: "10",
					rx: "3",
					fill: colors[0],
					stroke: accent
				}),
				/* @__PURE__ */ jsx("rect", {
					x: cx + w - 1,
					y: eyeY - 2,
					width: "6",
					height: "10",
					rx: "3",
					fill: colors[0],
					stroke: accent
				}),
				/* @__PURE__ */ jsx("path", {
					d: `M${cx + w + 2} ${eyeY + 8} q-3 7 -9 8`,
					strokeWidth: "1.6"
				})
			]
		});
		case "crown": return /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("path", {
			d: `M${cx - w + 1} ${top + 2} L${cx - w + 1} ${top - 12} L${cx - w * .45} ${top - 3}
                  L${cx} ${top - 16} L${cx + w * .45} ${top - 3} L${cx + w - 1} ${top - 12}
                  L${cx + w - 1} ${top + 2} Z`,
			fill: "#ffd45e",
			stroke: "#c98a12",
			strokeWidth: "1.4",
			strokeLinejoin: "round"
		}), /* @__PURE__ */ jsx("circle", {
			cx,
			cy: top - 6.6,
			r: "2.1",
			fill: accent,
			stroke: "#c98a12",
			strokeWidth: ".8"
		})] });
		case "glasses": return /* @__PURE__ */ jsxs("g", {
			fill: "none",
			stroke: accent,
			strokeWidth: "1.8",
			children: [
				/* @__PURE__ */ jsx("rect", {
					x: cx - w * .94,
					y: eyeY - 4.6,
					width: w * .74,
					height: "9.4",
					rx: "3.4",
					fill: "#dff4ff",
					fillOpacity: ".26"
				}),
				/* @__PURE__ */ jsx("rect", {
					x: cx + w * .2,
					y: eyeY - 4.6,
					width: w * .74,
					height: "9.4",
					rx: "3.4",
					fill: "#dff4ff",
					fillOpacity: ".26"
				}),
				/* @__PURE__ */ jsx("path", { d: `M${cx - w * .2} ${eyeY} L${cx + w * .2} ${eyeY}` }),
				/* @__PURE__ */ jsx("path", { d: `M${cx - w * .94} ${eyeY - 1.6} L${cx - w - 2} ${eyeY - .6}` }),
				/* @__PURE__ */ jsx("path", { d: `M${cx + w * .94} ${eyeY - 1.6} L${cx + w + 2} ${eyeY - .6}` })
			]
		});
		case "headband": return /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("path", {
			d: `M${cx - w - 1.5} ${top + h * .3} Q${cx} ${top + h * .18} ${cx + w + 1.5} ${top + h * .3}
                  L${cx + w + 1.5} ${top + h * .44} Q${cx} ${top + h * .32} ${cx - w - 1.5} ${top + h * .44} Z`,
			fill: accent,
			stroke: "rgba(255,255,255,.45)",
			strokeWidth: ".9"
		}), /* @__PURE__ */ jsx("path", {
			d: `M${cx + w} ${top + h * .36} q10 4 12 15 q-6 -5 -8 -3 q3 5 1 9 q-4 -8 -7 -14 Z`,
			fill: accent,
			opacity: ".9"
		})] });
		case "earrings": return /* @__PURE__ */ jsxs("g", {
			fill: "none",
			stroke: accent,
			strokeWidth: "1.8",
			children: [/* @__PURE__ */ jsx("circle", {
				cx: cx - w - .5,
				cy: eyeY + 8.6,
				r: "3"
			}), /* @__PURE__ */ jsx("circle", {
				cx: cx + w + .5,
				cy: eyeY + 8.6,
				r: "3"
			})]
		});
		case "mask": return /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("path", {
			d: `M${cx - w * .96} ${eyeY + 4} Q${cx} ${eyeY + 2} ${cx + w * .96} ${eyeY + 4}
                  Q${cx + w * .8} ${top + h + 5} ${cx} ${top + h + 7}
                  Q${cx - w * .8} ${top + h + 5} ${cx - w * .96} ${eyeY + 4} Z`,
			fill: colors[1],
			stroke: accent,
			strokeWidth: "1.4"
		}), /* @__PURE__ */ jsx("path", {
			d: `M${cx - w * .5} ${eyeY + 10} L${cx + w * .5} ${eyeY + 10}`,
			stroke: accent,
			strokeWidth: "1.2",
			opacity: ".6"
		})] });
		case "cap": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - w - 1} ${top + h * .34} Q${cx - w - 1} ${top - 6} ${cx} ${top - 7}
                  Q${cx + w + 1} ${top - 6} ${cx + w + 1} ${top + h * .34} Z`,
				fill: colors[0],
				stroke: colors[1],
				strokeWidth: "1.2"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - 2} ${top + h * .3} L${cx + w + 16} ${top + h * .26} Q${cx + w + 19} ${top + h * .4} ${cx + w + 14} ${top + h * .46}
                  L${cx - 2} ${top + h * .44} Z`,
				fill: colors[1]
			}),
			/* @__PURE__ */ jsx("circle", {
				cx,
				cy: top - 6,
				r: "2.4",
				fill: accent
			})
		] });
		case "helmet": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - w - 3} ${top + h * .72} Q${cx - w - 4} ${top - 7} ${cx} ${top - 8}
                  Q${cx + w + 4} ${top - 7} ${cx + w + 3} ${top + h * .72}
                  L${cx + w - 2} ${top + h * .72} L${cx + w - 2} ${eyeY - 5}
                  L${cx - w + 2} ${eyeY - 5} L${cx - w + 2} ${top + h * .72} Z`,
				fill: colors[0],
				stroke: accent,
				strokeWidth: "1.6",
				strokeLinejoin: "round"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - w + 2} ${eyeY - 5} L${cx + w - 2} ${eyeY - 5} L${cx + w - 2} ${eyeY + 4.6}
                  Q${cx} ${eyeY + 8} ${cx - w + 2} ${eyeY + 4.6} Z`,
				fill: "#161a33",
				opacity: ".92"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx} ${top - 8} L${cx} ${top + h * .3}`,
				stroke: accent,
				strokeWidth: "2.4"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - w + 4} ${eyeY} L${cx + w - 4} ${eyeY}`,
				stroke: accent,
				strokeWidth: "1.4",
				opacity: ".55"
			})
		] });
		default: return null;
	}
}
function ArenaBackGear({ back, colors, accent, build, S, uid }) {
	const { shoulder, hip } = build;
	const { shoulder: sy, hip: hy, centerX: cx, knee, chest } = S;
	switch (back) {
		case "cape": return /* @__PURE__ */ jsx("path", {
			d: `M${cx - shoulder - 1} ${sy - 4} Q${cx - shoulder - 16} ${knee - 10} ${cx - hip - 12} ${knee + 8}
                       Q${cx - 8} ${knee - 2} ${cx} ${knee + 6} Q${cx + 8} ${knee - 2} ${cx + hip + 12} ${knee + 8}
                       Q${cx + shoulder + 16} ${knee - 10} ${cx + shoulder + 1} ${sy - 4} Z`,
			fill: `url(#${uid}-suit)`,
			stroke: accent,
			strokeWidth: "1.2",
			strokeOpacity: ".5"
		});
		case "half_cape": return /* @__PURE__ */ jsx("path", {
			d: `M${cx + shoulder - 2} ${sy - 6} Q${cx + shoulder + 22} ${hy + 24} ${cx + hip + 16} ${knee - 4}
                       Q${cx + hip * .4} ${knee - 16} ${cx - 4} ${hy + 4} Z`,
			fill: `url(#${uid}-suit)`,
			stroke: accent,
			strokeWidth: "1.3",
			strokeOpacity: ".7"
		});
		case "energy_pack": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("rect", {
				x: cx - shoulder - 4,
				y: sy - 14,
				width: shoulder * 2 + 8,
				height: "46",
				rx: "12",
				fill: colors[1],
				stroke: accent,
				strokeWidth: "2.2"
			}),
			/* @__PURE__ */ jsx("rect", {
				x: cx - 12,
				y: sy - 8,
				width: "24",
				height: "18",
				rx: "6",
				fill: accent,
				opacity: ".7"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder - 12} ${sy + 4} l8 0 M${cx + shoulder + 4} ${sy + 4} l8 0`,
				stroke: accent,
				strokeWidth: "4",
				strokeLinecap: "round"
			})
		] });
		case "jetpack": return /* @__PURE__ */ jsx("g", { children: [-1, 1].map((side) => /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("rect", {
			x: cx + side * (shoulder + 2) - 9,
			y: sy - 12,
			width: "18",
			height: "46",
			rx: "9",
			fill: colors[1],
			stroke: accent,
			strokeWidth: "1.8"
		}), /* @__PURE__ */ jsx("path", {
			d: `M${cx + side * (shoulder + 2)} ${sy + 36} q-6 10 0 19 q6 -9 0 -19 Z`,
			fill: accent,
			opacity: ".8"
		})] }, side)) });
		case "wings": return /* @__PURE__ */ jsx("g", {
			fill: `url(#${uid}-suit)`,
			stroke: accent,
			strokeWidth: "1.3",
			strokeLinejoin: "round",
			opacity: ".92",
			children: [-1, 1].map((side) => /* @__PURE__ */ jsx("path", { d: `M${cx + side * (shoulder - 4)} ${sy - 2}
                               Q${cx + side * (shoulder + 40)} ${sy - 28} ${cx + side * (shoulder + 48)} ${chest + 6}
                               Q${cx + side * (shoulder + 34)} ${chest + 2} ${cx + side * (shoulder + 32)} ${chest + 20}
                               Q${cx + side * (shoulder + 20)} ${chest + 10} ${cx + side * (shoulder + 16)} ${chest + 28}
                               Q${cx + side * (shoulder + 6)} ${chest + 12} ${cx + side * (shoulder - 4)} ${sy - 2} Z` }, side))
		});
		case "quiver": return /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("rect", {
			x: cx + shoulder - 2,
			y: sy - 8,
			width: "16",
			height: "52",
			rx: "7",
			transform: `rotate(15 ${cx + shoulder + 6} ${sy + 18})`,
			fill: colors[1],
			stroke: accent,
			strokeWidth: "1.8"
		}), [
			-4,
			0,
			4
		].map((dx) => /* @__PURE__ */ jsx("path", {
			d: `M${cx + shoulder + 6 + dx} ${sy - 24} l2 15`,
			stroke: accent,
			strokeWidth: "2",
			strokeLinecap: "round"
		}, dx))] });
		case "banner": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("rect", {
				x: cx + shoulder - 2,
				y: sy - 26,
				width: "3.4",
				height: hy + 34 - sy + 26,
				rx: "1.7",
				fill: accent
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx + shoulder + 1.4} ${sy - 22} L${cx + shoulder + 34} ${sy - 17} L${cx + shoulder + 30} ${sy + 20}
                  L${cx + shoulder + 16} ${sy + 13} L${cx + shoulder + 1.4} ${sy + 19} Z`,
				fill: `url(#${uid}-suit)`,
				stroke: accent,
				strokeWidth: "1.2"
			}),
			/* @__PURE__ */ jsx("text", {
				x: cx + shoulder + 16,
				y: sy - 1,
				textAnchor: "middle",
				fontSize: "15",
				fontWeight: "900",
				fill: colors[2],
				fontFamily: "inherit",
				children: "M"
			})
		] });
		default: return null;
	}
}
/** Outfit detailing, drawn inside the torso silhouette via a clip path. */
function ArenaOutfitDetail({ outfit, colors, accent, build, S }) {
	const { shoulder, waist, chest: chestW } = build;
	const { shoulder: sy, chest, waist: wy, centerX: cx } = S;
	switch (outfit) {
		case "academy": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder + 4} ${sy - 2} L${cx} ${chest + 14} L${cx - waist - 3} ${wy + 4} Z`,
				fill: colors[1],
				opacity: ".8"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx + shoulder - 4} ${sy - 2} L${cx} ${chest + 14} L${cx + waist + 3} ${wy + 4} Z`,
				fill: colors[1],
				opacity: ".8"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder + 4} ${sy - 2} L${cx} ${chest + 14} L${cx + shoulder - 4} ${sy - 2}`,
				fill: "none",
				stroke: accent,
				strokeWidth: "2"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - 3.4} ${chest + 14} L${cx + 3.4} ${chest + 14} L${cx + 1.6} ${chest + 27} L${cx - 1.6} ${chest + 27} Z`,
				fill: accent
			})
		] });
		case "varsity": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder} ${sy + 8} L${cx + shoulder} ${sy + 8}`,
				stroke: colors[2],
				strokeWidth: "7",
				opacity: ".85"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - waist - 6} ${wy - 6} L${cx + waist + 6} ${wy - 6}`,
				stroke: colors[2],
				strokeWidth: "6",
				opacity: ".85"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - waist - 6} ${wy - 6} L${cx + waist + 6} ${wy - 6}`,
				stroke: accent,
				strokeWidth: "2"
			})
		] });
		case "techwear": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder} ${sy} L${cx + 8} ${sy + 4} L${cx - 2} ${wy + 6} L${cx - shoulder} ${wy}`,
				fill: colors[1],
				opacity: ".72"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx + 8} ${sy + 4} L${cx - 2} ${wy + 6}`,
				stroke: accent,
				strokeWidth: "2.4"
			}),
			/* @__PURE__ */ jsx("rect", {
				x: cx + 14,
				y: chest + 12,
				width: "13",
				height: "7",
				rx: "2.6",
				fill: "none",
				stroke: accent,
				strokeWidth: "1.6"
			}),
			/* @__PURE__ */ jsx("rect", {
				x: cx + 14,
				y: chest + 22,
				width: "9",
				height: "6",
				rx: "2.4",
				fill: "none",
				stroke: accent,
				strokeWidth: "1.4"
			})
		] });
		case "street": return /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("path", {
			d: `M${cx - shoulder} ${sy + 4} Q${cx} ${sy + 14} ${cx + shoulder} ${sy + 4}`,
			fill: "none",
			stroke: accent,
			strokeWidth: "3.4"
		}), /* @__PURE__ */ jsx("rect", {
			x: cx - waist + 2,
			y: wy - 22,
			width: waist * 2 - 4,
			height: "18",
			rx: "5",
			fill: "none",
			stroke: "rgba(255,255,255,.3)",
			strokeWidth: "2.2"
		})] });
		case "champion": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder + 1} ${sy + 2} Q${cx} ${sy + 15} ${cx + shoulder - 1} ${sy + 2}`,
				fill: "none",
				stroke: accent,
				strokeWidth: "5.4",
				strokeLinecap: "round"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - waist - 2} ${wy - 4} L${cx + waist + 2} ${wy - 4}`,
				stroke: accent,
				strokeWidth: "3.4",
				strokeLinecap: "round",
				opacity: ".95"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder + 6} ${chest + 2} L${cx - waist} ${wy - 10}`,
				stroke: accent,
				strokeWidth: "1.6",
				opacity: ".7"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx + shoulder - 6} ${chest + 2} L${cx + waist} ${wy - 10}`,
				stroke: accent,
				strokeWidth: "1.6",
				opacity: ".7"
			})
		] });
		case "hoodie": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder - 2} ${sy - 8} Q${cx} ${sy + 22} ${cx + shoulder + 2} ${sy - 8}`,
				fill: colors[1],
				opacity: ".9"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - 5} ${sy + 10} L${cx - 4} ${chest + 12} M${cx + 5} ${sy + 10} L${cx + 4} ${chest + 12}`,
				stroke: accent,
				strokeWidth: "2",
				strokeLinecap: "round"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - waist + 4} ${wy - 16} L${cx + waist - 4} ${wy - 16}`,
				stroke: "rgba(255,255,255,.2)",
				strokeWidth: "12"
			})
		] });
		case "jersey": return /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("path", {
			d: `M${cx - shoulder} ${sy - 4} Q${cx} ${sy + 12} ${cx + shoulder} ${sy - 4}`,
			fill: "none",
			stroke: accent,
			strokeWidth: "3"
		}), /* @__PURE__ */ jsx("text", {
			x: cx,
			y: wy - 4,
			textAnchor: "middle",
			fontSize: "17",
			fontWeight: "900",
			fill: colors[2],
			opacity: ".85",
			fontFamily: "inherit",
			children: "01"
		})] });
		case "flight": return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - chestW} ${chest - 4} L${cx + chestW} ${chest - 8}`,
				stroke: colors[1],
				strokeWidth: "8",
				opacity: ".8"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - chestW} ${chest - 4} L${cx + chestW} ${chest - 8}`,
				stroke: accent,
				strokeWidth: "1.6"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder + 4} ${sy + 2} L${cx - shoulder + 4} ${wy}`,
				stroke: accent,
				strokeWidth: "1.6",
				opacity: ".7"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx + shoulder - 4} ${sy + 2} L${cx + shoulder - 4} ${wy}`,
				stroke: accent,
				strokeWidth: "1.6",
				opacity: ".7"
			}),
			/* @__PURE__ */ jsx("rect", {
				x: cx - waist * .6,
				y: wy - 22,
				width: "12",
				height: "9",
				rx: "2.4",
				fill: "none",
				stroke: accent,
				strokeWidth: "1.4"
			})
		] });
		case "scholar": return /* @__PURE__ */ jsxs("g", { children: [/* @__PURE__ */ jsx("path", {
			d: `M${cx - 9} ${sy - 6} L${cx - 6} ${wy + 12} L${cx + 6} ${wy + 12} L${cx + 9} ${sy - 6} Z`,
			fill: accent,
			opacity: ".8"
		}), /* @__PURE__ */ jsx("path", {
			d: `M${cx - shoulder} ${sy + 2} Q${cx} ${sy + 18} ${cx + shoulder} ${sy + 2}`,
			fill: "none",
			stroke: colors[1],
			strokeWidth: "6"
		})] });
		default: return /* @__PURE__ */ jsxs("g", { children: [
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder + 3} ${sy + 6} Q${cx} ${sy + 13} ${cx + shoulder - 3} ${sy + 6}`,
				fill: "none",
				stroke: "rgba(255,255,255,.24)",
				strokeWidth: "3"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - waist + 3} ${chest + 6} L${cx + waist - 3} ${chest + 2}`,
				stroke: "rgba(255,255,255,.16)",
				strokeWidth: "4",
				strokeLinecap: "round"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx - shoulder + 4} ${chest - 6} L${cx - waist + 1} ${wy - 4}`,
				stroke: INK,
				strokeWidth: "2",
				opacity: ".22"
			}),
			/* @__PURE__ */ jsx("path", {
				d: `M${cx + shoulder - 4} ${chest - 6} L${cx + waist - 1} ${wy - 4}`,
				stroke: INK,
				strokeWidth: "2",
				opacity: ".22"
			})
		] });
	}
}
function ArenaMarking({ marking, accent, build, S }) {
	const { shoulder, waist } = build;
	const { shoulder: sy, chest, waist: wy, centerX: cx } = S;
	switch (marking) {
		case "stripes": return /* @__PURE__ */ jsxs("g", {
			stroke: accent,
			strokeWidth: "4",
			opacity: ".55",
			strokeLinecap: "round",
			children: [/* @__PURE__ */ jsx("path", { d: `M${cx - shoulder * .5} ${sy - 10} L${cx - waist * .5} ${wy + 14}` }), /* @__PURE__ */ jsx("path", { d: `M${cx - shoulder * .2} ${sy - 10} L${cx - waist * .2} ${wy + 14}` })]
		});
		case "circuit": return /* @__PURE__ */ jsxs("g", {
			stroke: accent,
			strokeWidth: "1.8",
			fill: "none",
			opacity: ".7",
			children: [
				/* @__PURE__ */ jsx("path", { d: `M${cx - shoulder + 6} ${chest - 8} h${shoulder * .5} v10 h${shoulder * .4}` }),
				/* @__PURE__ */ jsx("path", { d: `M${cx + shoulder - 6} ${chest + 14} h${-shoulder * .45} v-12 h${-shoulder * .3}` }),
				/* @__PURE__ */ jsx("circle", {
					cx: cx - shoulder + 6,
					cy: chest - 8,
					r: "2.4",
					fill: accent,
					stroke: "none"
				}),
				/* @__PURE__ */ jsx("circle", {
					cx: cx + shoulder - 6,
					cy: chest + 14,
					r: "2.4",
					fill: accent,
					stroke: "none"
				})
			]
		});
		case "chevron": return /* @__PURE__ */ jsx("g", {
			stroke: accent,
			strokeWidth: "3.4",
			fill: "none",
			opacity: ".6",
			strokeLinejoin: "round",
			children: [
				0,
				1,
				2
			].map((i) => /* @__PURE__ */ jsx("path", { d: `M${cx - waist} ${wy - 26 + i * 11} L${cx} ${wy - 32 + i * 11} L${cx + waist} ${wy - 26 + i * 11}` }, i))
		});
		case "stars": return /* @__PURE__ */ jsx("g", {
			fill: accent,
			opacity: ".7",
			children: [
				[-.5, -14],
				[.35, 4],
				[-.2, 20],
				[.6, -24]
			].map(([fx, dy], i) => {
				const x = cx + fx * shoulder;
				const y = chest + dy;
				return /* @__PURE__ */ jsx("path", { d: `M${x} ${y - 5} L${x + 1.4} ${y - 1.5} L${x + 5} ${y - 1.4}
                                   L${x + 2.2} ${y + 1} L${x + 3.1} ${y + 4.6} L${x} ${y + 2.5}
                                   L${x - 3.1} ${y + 4.6} L${x - 2.2} ${y + 1} L${x - 5} ${y - 1.4}
                                   L${x - 1.4} ${y - 1.5} Z` }, i);
			})
		});
		case "scales": return /* @__PURE__ */ jsx("g", {
			fill: "none",
			stroke: accent,
			strokeWidth: "1.5",
			opacity: ".45",
			children: [
				0,
				1,
				2,
				3
			].map((row) => [
				-2,
				-1,
				0,
				1,
				2
			].map((col) => /* @__PURE__ */ jsx("path", { d: `M${cx + col * 13 + (row % 2 ? 6.5 : 0) - 6.5} ${sy + 4 + row * 11}
                a6.5 6 0 0 0 13 0` }, `${row}-${col}`)))
		});
		default: return null;
	}
}
function ArenaShoulders({ shoulder, accent, build, S }) {
	const { shoulder: half } = build;
	const { shoulder: sy, chest, centerX: cx } = S;
	if (shoulder === "none") return null;
	if (shoulder === "sash") return /* @__PURE__ */ jsx("path", {
		d: `M${cx - half - 1} ${sy + 4} L${cx - half + 13} ${sy - 6}
                     L${cx + half * .5} ${chest + 26} L${cx + half * .5 - 13} ${chest + 30} Z`,
		fill: accent,
		stroke: INK,
		strokeWidth: INK_WEIGHT,
		strokeLinejoin: "round"
	});
	return /* @__PURE__ */ jsx("g", { children: [-1, 1].map((side) => {
		const x = cx + side * half;
		if (shoulder === "pauldrons") return /* @__PURE__ */ jsx("path", {
			d: `M${x - side * 15} ${sy + 13} a16 14 0 0 1 ${side * 28} 0
                                  l${-side * 3} 15 a14 11 0 0 0 ${-side * 22} 0 Z`,
			fill: `url(#${S.uid}-limb)`,
			stroke: INK,
			strokeWidth: INK_WEIGHT,
			strokeLinejoin: "round"
		}, side);
		if (shoulder === "epaulettes") return /* @__PURE__ */ jsx("rect", {
			x: x - 14,
			y: sy + 7,
			width: "27",
			height: "12",
			rx: "4.5",
			fill: accent,
			stroke: INK,
			strokeWidth: INK_WEIGHT
		}, side);
		return /* @__PURE__ */ jsx("path", {
			d: `M${x - 13} ${sy + 20} L${x - 7} ${sy + 2} L${x - 1} ${sy + 18}
                                L${x + 5} ${sy} L${x + 12} ${sy + 20} Z`,
			fill: accent,
			stroke: INK,
			strokeWidth: "2",
			strokeLinejoin: "round"
		}, side);
	}) });
}
function ArenaWaistGear({ waist, colors, accent, build, S }) {
	const { waist: half, hip } = build;
	const { waist: wy, hip: hy, centerX: cx } = S;
	switch (waist) {
		case "pouch": return /* @__PURE__ */ jsx("rect", {
			x: cx + half - 6,
			y: wy + 6,
			width: "16",
			height: "15",
			rx: "4",
			fill: colors[1],
			stroke: INK,
			strokeWidth: INK_WEIGHT
		});
		case "wrap": return /* @__PURE__ */ jsx("path", {
			d: `M${cx - hip - 3} ${wy + 6} L${cx + hip + 3} ${wy + 6}
                       L${cx + hip - 2} ${hy + 30} L${cx - hip + 2} ${hy + 26} Z`,
			fill: accent,
			opacity: ".85",
			stroke: INK,
			strokeWidth: INK_WEIGHT,
			strokeLinejoin: "round"
		});
		case "chain": return /* @__PURE__ */ jsxs("g", {
			fill: "none",
			stroke: accent,
			strokeWidth: "2.4",
			children: [/* @__PURE__ */ jsx("path", { d: `M${cx - half} ${wy + 7} q${half * .6} 16 ${half * 1.2} 2` }), /* @__PURE__ */ jsx("circle", {
				cx: cx - half * .4,
				cy: wy + 15,
				r: "2.2",
				fill: accent
			})]
		});
		case "holsters": return /* @__PURE__ */ jsx("g", { children: [-1, 1].map((side) => /* @__PURE__ */ jsx("rect", {
			x: cx + side * (hip - 2) - 7,
			y: wy + 8,
			width: "14",
			height: "20",
			rx: "4",
			fill: colors[1],
			stroke: INK,
			strokeWidth: INK_WEIGHT
		}, side)) });
		default: return null;
	}
}
function ArenaAura({ aura, colors, accent, uid, S, head }) {
	const cx = S.centerX;
	const mid = (S.shoulder + S.hip) / 2;
	switch (aura) {
		case "none": return null;
		case "halo": return /* @__PURE__ */ jsxs("g", {
			className: "arena-fighter-aura",
			children: [/* @__PURE__ */ jsx("ellipse", {
				cx,
				cy: head.top - 12,
				rx: head.w * 1.25,
				ry: head.w * .34,
				fill: "none",
				stroke: accent,
				strokeWidth: "4",
				opacity: ".35"
			}), /* @__PURE__ */ jsx("path", {
				d: `M${cx - head.w * 1.25} ${head.top - 12} a${head.w * 1.25} ${head.w * .34} 0 0 0 ${head.w * 2.5} 0`,
				fill: "none",
				stroke: accent,
				strokeWidth: "4",
				strokeLinecap: "round"
			})]
		});
		case "spark": return /* @__PURE__ */ jsx("g", {
			className: "arena-fighter-aura",
			fill: accent,
			children: [
				[-1, S.chest - 18],
				[1, S.chest - 4],
				[-1, S.hip + 8],
				[1, S.hip - 6],
				[-1, S.knee + 16],
				[1, S.knee + 4]
			].map(([side, y], i) => {
				const x = cx + side * (52 + i % 3 * 7);
				const r = 5 + i % 2 * 1.6;
				return /* @__PURE__ */ jsx("path", { d: `M${x} ${y - r} L${x + r * .32} ${y - r * .32} L${x + r} ${y}
                                   L${x + r * .32} ${y + r * .32} L${x} ${y + r}
                                   L${x - r * .32} ${y + r * .32} L${x - r} ${y}
                                   L${x - r * .32} ${y - r * .32} Z` }, i);
			})
		});
		case "orbit": return /* @__PURE__ */ jsx("ellipse", {
			className: "arena-fighter-aura",
			cx,
			cy: mid,
			rx: "66",
			ry: (S.ground - head.top) * .56,
			fill: "none",
			stroke: colors[2],
			strokeWidth: "2",
			strokeDasharray: "9 11",
			opacity: ".7"
		});
		case "flare": return /* @__PURE__ */ jsx("ellipse", {
			className: "arena-fighter-aura",
			cx,
			cy: S.hip,
			rx: "78",
			ry: (S.ground - head.top) * .62,
			fill: `url(#${uid}-glow)`,
			opacity: ".85"
		});
		case "embers": return /* @__PURE__ */ jsx("g", {
			className: "arena-fighter-aura",
			fill: accent,
			children: [
				[
					-1,
					S.knee + 10,
					3
				],
				[
					-1,
					S.chest + 6,
					2.2
				],
				[
					1,
					S.hip + 22,
					2.8
				],
				[
					1,
					S.chest - 12,
					2
				],
				[
					-1,
					S.shoulder + 4,
					1.8
				],
				[
					1,
					S.knee + 30,
					2.4
				]
			].map(([side, y, r], i) => /* @__PURE__ */ jsx("circle", {
				cx: cx + side * (48 + i % 3 * 9),
				cy: y,
				r,
				opacity: .55 + i % 3 * .15
			}, i))
		});
		case "frost": return /* @__PURE__ */ jsx("g", {
			className: "arena-fighter-aura",
			stroke: accent,
			strokeWidth: "1.6",
			fill: "none",
			opacity: ".8",
			children: [
				[-1, S.chest],
				[1, S.chest + 16],
				[-1, S.knee],
				[1, S.knee - 12]
			].map(([side, y], i) => {
				const x = cx + side * (52 + i % 2 * 6);
				return /* @__PURE__ */ jsx("path", { d: `M${x} ${y - 7} L${x} ${y + 7} M${x - 6} ${y - 3.5} L${x + 6} ${y + 3.5}
                                   M${x - 6} ${y + 3.5} L${x + 6} ${y - 3.5}` }, i);
			})
		});
		case "storm": return /* @__PURE__ */ jsxs("g", {
			className: "arena-fighter-aura",
			stroke: colors[2],
			strokeWidth: "2.2",
			fill: "none",
			strokeLinecap: "round",
			opacity: ".85",
			children: [/* @__PURE__ */ jsx("path", { d: `M${cx - 58} ${S.chest - 8} l10 22 l-7 3 l11 20` }), /* @__PURE__ */ jsx("path", { d: `M${cx + 58} ${S.chest + 8} l-10 22 l7 3 l-11 20` })]
		});
		default: return /* @__PURE__ */ jsx("ellipse", {
			className: "arena-fighter-aura",
			cx,
			cy: S.hip + 24,
			rx: "62",
			ry: (S.ground - head.top) * .52,
			fill: `url(#${uid}-glow)`,
			opacity: ".55"
		});
	}
}
function ArenaFighterView({ avatar, label = "Arena fighter", size = "full", facing = "right", state = "idle" }) {
	const loadout = useMemo(() => normalizeArenaAvatar(avatar), [avatar]);
	const colors = ARENA_AVATAR_PALETTES[loadout.palette];
	const skin = ARENA_AVATAR_SKINS[loadout.skin];
	const hairColor = ARENA_AVATAR_HAIR[loadout.hair_color];
	const accent = ARENA_AVATAR_ACCENTS[loadout.accent];
	const eyeColor = ARENA_AVATAR_EYES[loadout.eyes];
	const hairShadow = `color-mix(in srgb, ${hairColor} 72%, #000)`;
	const uid = useMemo(() => `af${[
		loadout.palette,
		loadout.skin,
		loadout.body,
		loadout.frame,
		loadout.height,
		size,
		facing
	].join("-")}`, [
		loadout.palette,
		loadout.skin,
		loadout.body,
		loadout.frame,
		loadout.height,
		size,
		facing
	]);
	const frame = FRAMES[loadout.frame];
	const base = BUILDS[loadout.body];
	const build = {
		shoulder: base.shoulder * frame.shoulder,
		chest: base.chest * frame.shoulder,
		waist: base.waist * frame.waist,
		hip: base.hip * frame.hip,
		arm: base.arm,
		thigh: base.thigh,
		calf: base.calf,
		neck: base.neck
	};
	const S = buildSkeleton(loadout.height);
	const cx = S.centerX;
	const headH = (S.chin - S.headTop) * S.headScale;
	const head = {
		cx,
		top: S.chin - headH,
		h: headH,
		w: 22 * frame.headW * S.headScale
	};
	const headBottom = S.chin + frame.chinY;
	const skirt = loadout.bottom === "battle_skirt" || loadout.bottom === "pleated";
	const shorts = loadout.bottom === "shorts";
	const legWidth = loadout.bottom === "fitted" ? build.thigh * .86 : loadout.bottom === "joggers" ? build.thigh * 1.16 : build.thigh;
	const legSpread = build.hip * .5;
	const pants = `url(#${uid}-pants)`;
	const torso = `M${cx - build.shoulder} ${S.shoulder + 7}
    C${cx - build.shoulder} ${S.shoulder - 4} ${cx - build.shoulder * .5} ${S.shoulder - 8} ${cx} ${S.shoulder - 8}
    C${cx + build.shoulder * .5} ${S.shoulder - 8} ${cx + build.shoulder} ${S.shoulder - 4} ${cx + build.shoulder} ${S.shoulder + 7}
    C${cx + build.chest} ${S.chest} ${cx + build.waist + 3} ${S.waist - 10} ${cx + build.waist} ${S.waist}
    C${cx + build.hip} ${S.hip - 13} ${cx + build.hip} ${S.hip - 8} ${cx + build.hip - 3} ${S.hip - 2}
    L${cx - build.hip + 3} ${S.hip - 2}
    C${cx - build.hip} ${S.hip - 8} ${cx - build.hip} ${S.hip - 13} ${cx - build.waist} ${S.waist}
    C${cx - build.waist - 3} ${S.waist - 10} ${cx - build.chest} ${S.chest} ${cx - build.shoulder} ${S.shoulder + 7} Z`;
	const pose = POSES[loadout.pose] || POSES.ready;
	const arm = (side) => {
		const sx = cx + side * (build.shoulder * .84);
		const sy = S.shoulder + 2;
		const ex = cx + side * (build.shoulder + build.arm * pose.elbow);
		const ey = S.waist + 2;
		const wx = cx + side * (build.shoulder * pose.wrist);
		const wy = S.hip + pose.drop;
		return {
			upper: `M${sx} ${sy} C${cx + side * (build.shoulder + build.arm * .5)} ${S.chest - 6} ${ex} ${S.chest + 8} ${ex} ${ey}`,
			fore: `M${ex} ${ey} C${ex} ${ey + 14} ${wx + side * 1} ${wy - 12} ${wx} ${wy}`,
			hand: [wx, wy + build.arm * .16]
		};
	};
	const leg = (side) => {
		const tx = cx + side * legSpread;
		const kx = cx + side * (legSpread * .94);
		const ax = cx + side * (legSpread * .86);
		return {
			thigh: `M${tx} ${S.hip + 6} C${tx + side * 2} ${S.hip + 24} ${kx + side * 1.5} ${S.knee - 22} ${kx} ${S.knee}`,
			calf: `M${kx} ${S.knee} C${kx - side * 1} ${S.knee + 22} ${ax + side * 1.5} ${S.ankle - 20} ${ax} ${S.ankle}`,
			foot: [ax, S.ankle]
		};
	};
	const pelvis = `M${cx - build.hip} ${S.hip - 12} L${cx + build.hip} ${S.hip - 12}
    C${cx + build.hip} ${S.hip + 6} ${cx + build.hip * .82} ${S.hip + 15} ${cx + build.hip * .62} ${S.hip + 18}
    C${cx + build.hip * .32} ${S.hip + 13} ${cx} ${S.hip + 7} ${cx} ${S.hip + 13}
    C${cx} ${S.hip + 7} ${cx - build.hip * .32} ${S.hip + 13} ${cx - build.hip * .62} ${S.hip + 18}
    C${cx - build.hip * .82} ${S.hip + 15} ${cx - build.hip} ${S.hip + 6} ${cx - build.hip} ${S.hip - 12} Z`;
	const arms = {
		left: arm(-1),
		right: arm(1)
	};
	const legs = {
		left: leg(-1),
		right: leg(1)
	};
	const gloveRadius = loadout.gloves === "gauntlets" ? build.arm * .84 : build.arm * .68;
	const gloveFill = loadout.gloves === "none" ? skin[0] : loadout.gloves === "gauntlets" ? `url(#${uid}-limb)` : loadout.gloves === "wraps" ? colors[2] : colors[0];
	const emblem = EMBLEM_PATHS[loadout.emblem];
	const hand = (position, side) => /* @__PURE__ */ jsxs("g", { children: [
		loadout.gloves !== "none" && /* @__PURE__ */ jsx("rect", {
			x: position[0] - gloveRadius * .95,
			y: position[1] - gloveRadius * 1.5,
			width: gloveRadius * 1.9,
			height: gloveRadius * .9,
			rx: gloveRadius * .35,
			fill: accent,
			stroke: INK,
			strokeWidth: "2"
		}),
		/* @__PURE__ */ jsx("ellipse", {
			cx: position[0],
			cy: position[1],
			rx: gloveRadius,
			ry: gloveRadius * 1.12,
			fill: gloveFill,
			stroke: INK,
			strokeWidth: "2"
		}),
		loadout.gloves === "wraps" && [
			0,
			1,
			2
		].map((i) => /* @__PURE__ */ jsx("path", {
			d: `M${position[0] - gloveRadius} ${position[1] - 3 + i * 3} L${position[0] + gloveRadius} ${position[1] - 4 + i * 3}`,
			stroke: colors[1],
			strokeWidth: "1.3",
			opacity: ".8"
		}, i)),
		loadout.gloves === "claws" && [
			-1,
			0,
			1
		].map((i) => /* @__PURE__ */ jsx("path", {
			d: `M${position[0] + i * 3.4} ${position[1] + gloveRadius * .4}
                        l${i * 2} ${gloveRadius + 5}`,
			stroke: accent,
			strokeWidth: "2",
			strokeLinecap: "round",
			fill: "none"
		}, i))
	] }, `hand${side}`);
	const foot = ([x, y], side) => {
		if (loadout.footwear === "barefoot") return /* @__PURE__ */ jsx("ellipse", {
			cx: x + side * build.calf * .22,
			cy: y + 4,
			rx: build.calf * .72,
			ry: "5.4",
			fill: skin[0],
			stroke: INK,
			strokeWidth: "2"
		}, side);
		const w = loadout.footwear === "armored" ? build.calf * 1.5 : build.calf * 1.25;
		const h = loadout.footwear === "high_tops" ? 13 : loadout.footwear === "armored" ? 15 : 12;
		return /* @__PURE__ */ jsxs("g", { children: [
			loadout.footwear === "high_tops" && /* @__PURE__ */ jsx("rect", {
				x: x - build.calf * .62,
				y: y - 14,
				width: build.calf * 1.24,
				height: "16",
				rx: "4.5",
				fill: colors[2],
				stroke: INK,
				strokeWidth: "2"
			}),
			loadout.footwear === "greaves" && /* @__PURE__ */ jsx("path", {
				d: `M${x - build.calf * .7} ${y - 30} L${x + build.calf * .7} ${y - 30}
                  L${x + build.calf * .6} ${y - 2} L${x - build.calf * .6} ${y - 2} Z`,
				fill: `url(#${uid}-limb)`,
				stroke: INK,
				strokeWidth: "2",
				strokeLinejoin: "round"
			}),
			/* @__PURE__ */ jsxs("g", {
				transform: side < 0 ? `translate(${2 * x} 0) scale(-1 1)` : void 0,
				children: [
					/* @__PURE__ */ jsx("path", {
						d: `M${x - w * .46} ${y - h + 3} Q${x - w * .52} ${y + h - 6} ${x - w * .38} ${y + h - 3}
                  L${x + w * .66} ${y + h - 3} Q${x + w * .84} ${y + h - 4} ${x + w * .78} ${y + h - 9}
                  Q${x + w * .42} ${y - h + 5} ${x + w * .16} ${y - h + 3} Z`,
						fill: loadout.footwear === "runners" || loadout.footwear === "low_tops" ? colors[2] : `url(#${uid}-limb)`,
						stroke: INK,
						strokeWidth: "2.2",
						strokeLinejoin: "round"
					}),
					/* @__PURE__ */ jsx("path", {
						d: `M${x - w * .36} ${y + h - 3.4} L${x + w * .64} ${y + h - 3.4}`,
						stroke: accent,
						strokeWidth: "1.4",
						strokeLinecap: "round",
						opacity: ".32"
					}),
					loadout.footwear === "runners" && /* @__PURE__ */ jsx("path", {
						d: `M${x - w * .3} ${y + 2} L${x + w * .5} ${y}`,
						stroke: accent,
						strokeWidth: "1.6",
						strokeLinecap: "round",
						opacity: ".7"
					}),
					loadout.footwear === "armored" && /* @__PURE__ */ jsx("path", {
						d: `M${x - w * .34} ${y - 3} L${x + w * .6} ${y - 5}`,
						stroke: "rgba(255,255,255,.35)",
						strokeWidth: "2.4",
						strokeLinecap: "round"
					})
				]
			})
		] }, side);
	};
	return /* @__PURE__ */ jsx("div", {
		className: `arena-fighter arena-fighter--${loadout.body} arena-fighter--${size} arena-fighter--${state}`,
		"data-facing": facing,
		"data-frame": loadout.frame,
		"data-height": loadout.height,
		"data-gear": loadout.gear,
		"data-hair": loadout.hair,
		"data-face": loadout.face,
		"data-outfit": loadout.outfit,
		"data-bottom": loadout.bottom,
		"data-gloves": loadout.gloves,
		"data-footwear": loadout.footwear,
		"data-back": loadout.back,
		"data-aura": loadout.aura,
		role: "img",
		"aria-label": label,
		children: /* @__PURE__ */ jsxs("svg", {
			className: "arena-fighter-svg",
			viewBox: "0 0 200 300",
			xmlns: "http://www.w3.org/2000/svg",
			"aria-hidden": "true",
			children: [
				/* @__PURE__ */ jsxs("defs", { children: [
					/* @__PURE__ */ jsxs("linearGradient", {
						id: `${uid}-suit`,
						x1: "0.1",
						y1: "0",
						x2: "0.75",
						y2: "1",
						children: [
							/* @__PURE__ */ jsx("stop", {
								offset: "0%",
								stopColor: `color-mix(in srgb, ${colors[0]} 76%, #ffffff)`
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "42%",
								stopColor: colors[0]
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "100%",
								stopColor: colors[1]
							})
						]
					}),
					/* @__PURE__ */ jsxs("linearGradient", {
						id: `${uid}-limb`,
						x1: "0",
						y1: "0",
						x2: "1",
						y2: "0.35",
						children: [
							/* @__PURE__ */ jsx("stop", {
								offset: "0%",
								stopColor: `color-mix(in srgb, ${colors[0]} 82%, #ffffff)`
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "46%",
								stopColor: colors[0]
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "100%",
								stopColor: colors[1]
							})
						]
					}),
					/* @__PURE__ */ jsxs("linearGradient", {
						id: `${uid}-skin`,
						x1: "0.2",
						y1: "0",
						x2: "0.9",
						y2: "1",
						children: [
							/* @__PURE__ */ jsx("stop", {
								offset: "0%",
								stopColor: skin[2]
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "52%",
								stopColor: skin[0]
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "100%",
								stopColor: skin[1]
							})
						]
					}),
					/* @__PURE__ */ jsxs("linearGradient", {
						id: `${uid}-pants`,
						x1: "0.1",
						y1: "0",
						x2: "0.8",
						y2: "1",
						children: [
							/* @__PURE__ */ jsx("stop", {
								offset: "0%",
								stopColor: `color-mix(in srgb, ${colors[1]} 74%, #c9d6ff)`
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "45%",
								stopColor: `color-mix(in srgb, ${colors[1]} 82%, #0b1030)`
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "100%",
								stopColor: `color-mix(in srgb, ${colors[1]} 46%, #0b1030)`
							})
						]
					}),
					/* @__PURE__ */ jsxs("radialGradient", {
						id: `${uid}-glow`,
						children: [
							/* @__PURE__ */ jsx("stop", {
								offset: "0%",
								stopColor: colors[2],
								stopOpacity: "0.5"
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "55%",
								stopColor: colors[0],
								stopOpacity: "0.26"
							}),
							/* @__PURE__ */ jsx("stop", {
								offset: "100%",
								stopColor: colors[0],
								stopOpacity: "0"
							})
						]
					}),
					/* @__PURE__ */ jsx("clipPath", {
						id: `${uid}-torso-clip`,
						children: /* @__PURE__ */ jsx("path", { d: torso })
					})
				] }),
				/* @__PURE__ */ jsx(ArenaAura, {
					aura: loadout.aura,
					colors,
					accent,
					uid,
					S,
					head
				}),
				/* @__PURE__ */ jsx("ellipse", {
					className: "arena-fighter-shadow",
					cx,
					cy: S.ground + 8,
					rx: build.hip + 22,
					ry: "8",
					fill: "rgba(6,8,40,.45)"
				}),
				/* @__PURE__ */ jsxs("g", {
					className: "arena-fighter-rig",
					children: [
						/* @__PURE__ */ jsx(ArenaBackGear, {
							back: loadout.back,
							colors,
							accent,
							build,
							S,
							uid
						}),
						hairBack(loadout.hair, head, S.shoulder).map((d, i) => /* @__PURE__ */ jsx("path", {
							d,
							fill: hairShadow,
							stroke: INK,
							strokeWidth: INK_WEIGHT,
							strokeLinejoin: "round"
						}, i)),
						["left", "right"].map((side) => {
							const bare = skirt || shorts;
							const skinTone = side === "left" ? skin[1] : skin[0];
							return /* @__PURE__ */ jsxs("g", {
								className: `arena-fighter-leg arena-fighter-leg--${side}`,
								strokeLinecap: "round",
								fill: "none",
								children: [
									/* @__PURE__ */ jsx("path", {
										d: legs[side].thigh,
										stroke: INK,
										strokeWidth: legWidth + LIMB_INK
									}),
									/* @__PURE__ */ jsx("path", {
										d: legs[side].calf,
										stroke: INK,
										strokeWidth: build.calf + LIMB_INK
									}),
									/* @__PURE__ */ jsx("path", {
										d: legs[side].thigh,
										stroke: bare ? skinTone : pants,
										strokeWidth: legWidth
									}),
									/* @__PURE__ */ jsx("path", {
										d: legs[side].calf,
										stroke: bare ? skinTone : pants,
										strokeWidth: build.calf
									}),
									/* @__PURE__ */ jsxs("g", {
										transform: LIGHT_SHIFT,
										opacity: side === "left" ? ".1" : ".3",
										children: [/* @__PURE__ */ jsx("path", {
											d: legs[side].thigh,
											stroke: "#fff",
											strokeWidth: legWidth * .4
										}), /* @__PURE__ */ jsx("path", {
											d: legs[side].calf,
											stroke: "#fff",
											strokeWidth: build.calf * .4
										})]
									})
								]
							}, side);
						}),
						foot(legs.left.foot, -1),
						foot(legs.right.foot, 1),
						/* @__PURE__ */ jsx("path", {
							d: pelvis,
							fill: skirt || shorts ? `url(#${uid}-suit)` : pants,
							stroke: INK,
							strokeWidth: INK_WEIGHT,
							strokeLinejoin: "round"
						}),
						loadout.bottom === "cargo" && /* @__PURE__ */ jsxs("g", {
							fill: colors[1],
							stroke: accent,
							strokeWidth: "1.4",
							children: [/* @__PURE__ */ jsx("rect", {
								x: cx - legSpread - build.thigh * .62,
								y: S.hip + 26,
								width: "13",
								height: "15",
								rx: "3.4"
							}), /* @__PURE__ */ jsx("rect", {
								x: cx + legSpread - build.thigh * .38,
								y: S.hip + 26,
								width: "13",
								height: "15",
								rx: "3.4"
							})]
						}),
						loadout.bottom === "joggers" && [-1, 1].map((side) => /* @__PURE__ */ jsx("path", {
							d: `M${cx + side * legSpread - build.calf * .8} ${S.knee + 26}
                               L${cx + side * legSpread + build.calf * .8} ${S.knee + 26}`,
							stroke: accent,
							strokeWidth: "3",
							strokeLinecap: "round"
						}, side)),
						shorts && /* @__PURE__ */ jsx("path", {
							d: `M${cx - build.hip - 2} ${S.hip + 2} L${cx + build.hip + 2} ${S.hip + 2}
                             L${cx + build.hip} ${S.hip + 30} L${cx + 3} ${S.hip + 26}
                             L${cx - 3} ${S.hip + 26} L${cx - build.hip} ${S.hip + 30} Z`,
							fill: `url(#${uid}-suit)`,
							stroke: accent,
							strokeWidth: "1.4",
							strokeLinejoin: "round"
						}),
						skirt && /* @__PURE__ */ jsx("path", {
							d: loadout.bottom === "pleated" ? `M${cx - build.hip - 3} ${S.hip + 2} L${cx + build.hip + 3} ${S.hip + 2}
             L${cx + build.hip + 12} ${S.hip + 38} L${cx + build.hip * .5} ${S.hip + 32}
             L${cx} ${S.hip + 38} L${cx - build.hip * .5} ${S.hip + 32} L${cx - build.hip - 12} ${S.hip + 38} Z` : `M${cx - build.hip - 4} ${S.hip + 2} L${cx + build.hip + 4} ${S.hip + 2}
             L${cx + build.hip + 13} ${S.hip + 40} L${cx + 6} ${S.hip + 32}
             L${cx - 6} ${S.hip + 38} L${cx - build.hip - 13} ${S.hip + 40} Z`,
							fill: `url(#${uid}-suit)`,
							stroke: accent,
							strokeWidth: "1.6",
							strokeLinejoin: "round"
						}),
						/* @__PURE__ */ jsx("path", {
							d: `M${cx - build.neck * 1.12} ${headBottom - 8} L${cx - build.neck * .98} ${S.shoulder - 2}
                  L${cx + build.neck * .98} ${S.shoulder - 2} L${cx + build.neck * 1.12} ${headBottom - 8} Z`,
							fill: skin[0],
							stroke: INK,
							strokeWidth: INK_WEIGHT,
							strokeLinejoin: "round"
						}),
						/* @__PURE__ */ jsx("path", {
							d: `M${cx - build.neck * 1.06} ${headBottom - 7} L${cx + build.neck * 1.06} ${headBottom - 7}
                  L${cx + build.neck * .98} ${headBottom + 2} L${cx - build.neck * .98} ${headBottom + 2} Z`,
							fill: skin[1],
							opacity: ".85"
						}),
						/* @__PURE__ */ jsxs("g", {
							className: "arena-fighter-torso",
							children: [
								/* @__PURE__ */ jsx("path", {
									d: torso,
									fill: `url(#${uid}-suit)`,
									stroke: INK,
									strokeWidth: INK_WEIGHT,
									strokeLinejoin: "round"
								}),
								/* @__PURE__ */ jsxs("g", {
									clipPath: `url(#${uid}-torso-clip)`,
									children: [
										/* @__PURE__ */ jsx(ArenaOutfitDetail, {
											outfit: loadout.outfit,
											colors,
											accent,
											build,
											S
										}),
										/* @__PURE__ */ jsx(ArenaMarking, {
											marking: loadout.marking,
											accent,
											build,
											S
										}),
										/* @__PURE__ */ jsx("path", {
											d: `M${cx - build.shoulder - 4} ${S.shoulder - 12} Q${cx - build.chest * .35} ${S.chest + 16} ${cx - build.waist - 6} ${S.waist + 22}`,
											stroke: "rgba(255,255,255,.09)",
											strokeWidth: "13",
											fill: "none"
										})
									]
								}),
								/* @__PURE__ */ jsx("path", {
									d: `M${cx - build.waist - 1} ${S.waist + 3} L${cx + build.waist + 1} ${S.waist + 3}`,
									stroke: "rgba(10,14,50,.55)",
									strokeWidth: "9"
								}),
								/* @__PURE__ */ jsx("rect", {
									x: cx - 6,
									y: S.waist - 2.5,
									width: "12",
									height: "11",
									rx: "2.6",
									fill: colors[1],
									stroke: accent,
									strokeWidth: "1.6"
								}),
								/* @__PURE__ */ jsxs("g", {
									clipPath: `url(#${uid}-torso-clip)`,
									children: [
										/* @__PURE__ */ jsx("ellipse", {
											cx,
											cy: S.shoulder - 6,
											rx: build.neck * 1.5,
											ry: "11",
											fill: INK,
											opacity: ".26"
										}),
										/* @__PURE__ */ jsx("path", {
											d: `M${cx + build.chest * .5} ${S.shoulder - 12} Q${cx + build.chest} ${S.chest} ${cx + build.waist} ${S.waist + 8}
                      L${cx + build.hip + 6} ${S.hip} L${cx + build.hip + 6} ${S.shoulder - 12} Z`,
											fill: INK,
											opacity: ".2"
										}),
										/* @__PURE__ */ jsx("ellipse", {
											cx,
											cy: S.hip + 2,
											rx: build.hip,
											ry: "9",
											fill: INK,
											opacity: ".16"
										}),
										/* @__PURE__ */ jsx("path", {
											d: `M${cx - build.shoulder + 3} ${S.shoulder} Q${cx - build.chest - 1} ${S.chest} ${cx - build.waist - 1} ${S.waist + 4}`,
											fill: "none",
											stroke: "#fff",
											strokeWidth: "3.4",
											opacity: ".2",
											strokeLinecap: "round"
										}),
										/* @__PURE__ */ jsx("path", {
											d: `M${cx - build.waist * .7} ${S.waist - 12} q${build.waist * .7} 6 ${build.waist * 1.4} -2`,
											fill: "none",
											stroke: INK,
											strokeWidth: "1.6",
											opacity: ".16"
										}),
										/* @__PURE__ */ jsx("path", {
											d: `M${cx - build.waist * .5} ${S.waist - 4} q${build.waist * .5} 5 ${build.waist} -1`,
											fill: "none",
											stroke: INK,
											strokeWidth: "1.4",
											opacity: ".12"
										})
									]
								}),
								/* @__PURE__ */ jsx(ArenaWaistGear, {
									waist: loadout.waist,
									colors,
									accent,
									build,
									S
								}),
								/* @__PURE__ */ jsxs("g", {
									transform: `translate(${cx} ${S.chest + 2})`,
									children: [/* @__PURE__ */ jsx("circle", {
										r: "11",
										fill: accent,
										stroke: INK,
										strokeWidth: "2"
									}), /* @__PURE__ */ jsx("path", {
										d: emblem.d,
										fill: emblem.fill ? colors[1] : "none",
										stroke: colors[1],
										strokeWidth: emblem.fill ? .6 : 1.5,
										strokeLinejoin: "round",
										strokeLinecap: "round"
									})]
								})
							]
						}),
						["left", "right"].map((side) => /* @__PURE__ */ jsxs("g", {
							className: `arena-fighter-arm arena-fighter-arm--${side}`,
							strokeLinecap: "round",
							fill: "none",
							children: [
								/* @__PURE__ */ jsx("path", {
									d: arms[side].upper,
									stroke: INK,
									strokeWidth: build.arm + LIMB_INK
								}),
								/* @__PURE__ */ jsx("path", {
									d: arms[side].fore,
									stroke: INK,
									strokeWidth: build.arm * .86 + LIMB_INK
								}),
								/* @__PURE__ */ jsx("path", {
									d: arms[side].upper,
									stroke: `url(#${uid}-limb)`,
									strokeWidth: build.arm
								}),
								/* @__PURE__ */ jsx("path", {
									d: arms[side].fore,
									stroke: `url(#${uid}-limb)`,
									strokeWidth: build.arm * .86
								}),
								/* @__PURE__ */ jsxs("g", {
									transform: LIGHT_SHIFT,
									opacity: side === "left" ? ".1" : ".32",
									children: [/* @__PURE__ */ jsx("path", {
										d: arms[side].upper,
										stroke: "#fff",
										strokeWidth: build.arm * .36
									}), /* @__PURE__ */ jsx("path", {
										d: arms[side].fore,
										stroke: "#fff",
										strokeWidth: build.arm * .32
									})]
								}),
								hand(arms[side].hand, side === "left" ? -1 : 1)
							]
						}, side)),
						/* @__PURE__ */ jsx(ArenaShoulders, {
							shoulder: loadout.shoulder,
							accent,
							build,
							S
						}),
						/* @__PURE__ */ jsxs("g", {
							className: "arena-fighter-head",
							children: [
								/* @__PURE__ */ jsx("path", {
									d: `M${cx - head.w} ${head.top + head.h * .34}
                    A${head.w} ${head.h * .38} 0 0 1 ${cx + head.w} ${head.top + head.h * .34}
                    L${cx + head.w * frame.jaw * .94} ${head.top + head.h * .62}
                    Q${cx + head.w * frame.jaw * .82} ${headBottom - 2} ${cx} ${headBottom + 2}
                    Q${cx - head.w * frame.jaw * .82} ${headBottom - 2} ${cx - head.w * frame.jaw * .94} ${head.top + head.h * .62} Z`,
									fill: `url(#${uid}-skin)`,
									stroke: INK,
									strokeWidth: INK_WEIGHT,
									strokeLinejoin: "round"
								}),
								/* @__PURE__ */ jsx("path", {
									d: `M${cx - head.w * .9} ${head.top + head.h * .3}
                    Q${cx} ${head.top + head.h * .42} ${cx + head.w * .9} ${head.top + head.h * .3}
                    L${cx + head.w * .9} ${head.top + head.h * .16}
                    L${cx - head.w * .9} ${head.top + head.h * .16} Z`,
									fill: skin[1],
									opacity: ".3"
								}),
								/* @__PURE__ */ jsx("path", {
									d: `M${cx + head.w * .42} ${head.top + head.h * .22}
                    Q${cx + head.w * 1.02} ${head.top + head.h * .6} ${cx + head.w * .5} ${head.top + head.h * .94}
                    Q${cx + head.w * .95} ${head.top + head.h * .7} ${cx + head.w * .96} ${head.top + head.h * .3} Z`,
									fill: skin[1],
									opacity: ".35"
								}),
								/* @__PURE__ */ jsx(ArenaFace, {
									loadout,
									head,
									skin,
									accent,
									hairColor,
									eyeColor
								}),
								/* @__PURE__ */ jsx("path", {
									d: hairFront(loadout.hair, head),
									fill: hairColor,
									stroke: INK,
									strokeWidth: INK_WEIGHT,
									strokeLinejoin: "round"
								}),
								/* @__PURE__ */ jsx("path", {
									d: `M${cx - head.w * .62} ${head.top + head.h * .16}
                    Q${cx - head.w * .1} ${head.top - 1} ${cx + head.w * .5} ${head.top + head.h * .1}`,
									fill: "none",
									stroke: "#fff",
									strokeWidth: "2.6",
									strokeLinecap: "round",
									opacity: ".18"
								}),
								/* @__PURE__ */ jsx(ArenaHeadGear, {
									gear: loadout.gear,
									head,
									colors,
									accent
								})
							]
						})
					]
				})
			]
		})
	});
}
/** True when two loadouts would draw the same fighter. */
function sameLoadout(a, b) {
	if (a === b) return true;
	const left = a || {};
	const right = b || {};
	return Object.keys(ARENA_AVATAR_DEFAULT).every((key) => left[key] === right[key]);
}
var ArenaFighter = memo(ArenaFighterView, (previous, next) => previous.size === next.size && previous.facing === next.facing && previous.state === next.state && previous.label === next.label && sameLoadout(previous.avatar, next.avatar));
ArenaFighter.displayName = "ArenaFighter";
function ArenaCustomizer({ avatar, onChange, onSave, onClose, saving }) {
	const [section, setSection] = useState("body");
	const dialog = useRef(null);
	useEffect(() => {
		const previous = document.activeElement;
		const element = dialog.current;
		element.querySelector("button")?.focus();
		const trap = (event) => {
			if (event.key === "Escape" && element.getAttribute("aria-busy") !== "true") {
				event.preventDefault();
				onClose();
				return;
			}
			if (event.key !== "Tab") return;
			const focusable = [...element.querySelectorAll("button:not(:disabled), input, [tabindex=\"0\"]")];
			const first = focusable[0], last = focusable.at(-1);
			if (event.shiftKey && document.activeElement === first) {
				event.preventDefault();
				last?.focus();
			} else if (!event.shiftKey && document.activeElement === last) {
				event.preventDefault();
				first?.focus();
			}
		};
		element.addEventListener("keydown", trap);
		return () => {
			element.removeEventListener("keydown", trap);
			if (previous?.isConnected) previous.focus();
		};
	}, [onClose]);
	const current = normalizeArenaAvatar(avatar);
	const groups = (ARENA_CUSTOMIZER_SECTIONS.find(([key]) => key === section) || ARENA_CUSTOMIZER_SECTIONS[0])[2];
	return /* @__PURE__ */ jsx("div", {
		className: "arena-customizer-backdrop",
		role: "presentation",
		onMouseDown: (event) => {
			if (event.target === event.currentTarget && !saving) onClose();
		},
		children: /* @__PURE__ */ jsxs("section", {
			ref: dialog,
			className: "arena-customizer",
			role: "dialog",
			"aria-modal": "true",
			"aria-labelledby": "arena-customizer-title",
			"aria-busy": saving,
			children: [
				/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("div", { children: [
					/* @__PURE__ */ jsx("small", { children: "FIGHTER LOCKER" }),
					/* @__PURE__ */ jsx("h2", {
						id: "arena-customizer-title",
						children: "Make the fighter yours."
					}),
					/* @__PURE__ */ jsx("p", { children: "Your look, your arena. Preview instantly, then equip to save." })
				] }), /* @__PURE__ */ jsx("button", {
					type: "button",
					onClick: onClose,
					disabled: saving,
					"aria-label": "Close fighter locker",
					children: /* @__PURE__ */ jsx(X, {})
				})] }),
				/* @__PURE__ */ jsxs("div", {
					className: "arena-customizer-body",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "arena-customizer-preview",
						children: [
							/* @__PURE__ */ jsx("i", { className: "arena-preview-light" }),
							/* @__PURE__ */ jsx(ArenaAvatarPreview, {
								avatar: section === "hair" ? {
									...current,
									gear: "none"
								} : current,
								view: ["hair", "face"].includes(section) ? "portrait" : "full",
								label: "Your customized Arena fighter"
							}),
							/* @__PURE__ */ jsx("strong", { children: "LIVE LOADOUT" }),
							/* @__PURE__ */ jsxs("span", { children: [
								current.frame,
								" · ",
								current.body,
								" · ",
								current.outfit
							] }),
							/* @__PURE__ */ jsxs("div", {
								className: "arena-preview-actions",
								children: [/* @__PURE__ */ jsxs("button", {
									type: "button",
									disabled: saving,
									onClick: () => onChange(randomArenaAvatar()),
									children: [/* @__PURE__ */ jsx(Dices, {}), " Randomize"]
								}), /* @__PURE__ */ jsxs("button", {
									type: "button",
									disabled: saving,
									onClick: () => onChange({ ...ARENA_AVATAR_DEFAULT }),
									children: [/* @__PURE__ */ jsx(RotateCcw, {}), " Reset"]
								})]
							})
						]
					}), /* @__PURE__ */ jsxs("div", {
						className: "arena-customizer-editor",
						children: [/* @__PURE__ */ jsx("nav", {
							className: "arena-customizer-tabs",
							"aria-label": "Fighter customization categories",
							children: ARENA_CUSTOMIZER_SECTIONS.map(([key, title]) => /* @__PURE__ */ jsx("button", {
								type: "button",
								className: section === key ? "selected" : "",
								"aria-pressed": section === key,
								onClick: () => setSection(key),
								children: title
							}, key))
						}), /* @__PURE__ */ jsxs("div", {
							className: "arena-customizer-options",
							"data-category": section,
							children: [section === "hair" && /* @__PURE__ */ jsxs("p", {
								className: "arena-hair-hint",
								children: ["A closer look. Rotate to see the cut from every angle.", current.gear !== "none" && " Headwear is hidden in this preview."]
							}), groups.map(([key, title, choices, swatchKey]) => /* @__PURE__ */ jsxs("fieldset", { children: [/* @__PURE__ */ jsx("legend", { children: title }), /* @__PURE__ */ jsx("div", { children: choices.map(([value, optionLabel]) => {
								const swatch = swatchKey ? SWATCH_SOURCES[swatchKey]?.(value) : null;
								return /* @__PURE__ */ jsxs("button", {
									type: "button",
									disabled: saving,
									className: current[key] === value ? "selected" : "",
									"aria-pressed": current[key] === value,
									onClick: () => onChange({
										...current,
										[key]: value
									}),
									children: [
										swatch && /* @__PURE__ */ jsx("i", { style: { background: swatch } }),
										/* @__PURE__ */ jsx("span", { children: optionLabel }),
										current[key] === value && /* @__PURE__ */ jsx(Check, {})
									]
								}, value);
							}) })] }, key))]
						})]
					})]
				}),
				/* @__PURE__ */ jsxs("footer", { children: [/* @__PURE__ */ jsx("span", { children: "Cosmetics are visual only. Your rank still controls question difficulty." }), /* @__PURE__ */ jsxs("button", {
					type: "button",
					className: "arena-save-loadout",
					onClick: onSave,
					disabled: saving,
					children: [
						saving ? "SAVING…" : "EQUIP LOADOUT",
						" ",
						/* @__PURE__ */ jsx(Sparkles, {})
					]
				})] })
			]
		})
	});
}
//#endregion
//#region frontend/src/arena-calculator.jsx
var DESMOS_EMBED = "https://www.desmos.com/calculator";
var DEFAULT_SIZE = {
	width: 680,
	height: 560
};
var MIN_SIZE = {
	width: 440,
	height: 320
};
var EDGE = 8;
function viewport() {
	if (typeof window === "undefined") return {
		width: 1280,
		height: 800
	};
	return {
		width: window.innerWidth,
		height: window.innerHeight
	};
}
function clampSize(size) {
	const view = viewport();
	return {
		width: Math.min(Math.max(size.width, MIN_SIZE.width), view.width - 16),
		height: Math.min(Math.max(size.height, MIN_SIZE.height), view.height - 16)
	};
}
/** Keep the panel on screen, after a drag, a resize, or a window resize. */
function clampPosition(position, size) {
	const view = viewport();
	return {
		x: Math.min(Math.max(position.x, EDGE), Math.max(EDGE, view.width - size.width - EDGE)),
		y: Math.min(Math.max(position.y, EDGE), Math.max(EDGE, view.height - size.height - EDGE))
	};
}
function defaultSize() {
	if (viewport().width <= 620) return DEFAULT_SIZE;
	try {
		const saved = JSON.parse(sessionStorage.getItem("mentics:calculator-size"));
		if (Number.isFinite(saved?.width) && Number.isFinite(saved?.height)) return clampSize(saved);
	} catch {}
	return clampSize(DEFAULT_SIZE);
}
function defaultPosition() {
	const size = defaultSize();
	const view = viewport();
	return clampPosition({
		x: view.width - size.width - 24,
		y: view.height - size.height - 24
	}, size);
}
function ArenaCalculator({ open, onClose }) {
	const [position, setPosition] = useState(defaultPosition);
	const [size, setSize] = useState(defaultSize);
	const [everOpened, setEverOpened] = useState(open);
	const [loaded, setLoaded] = useState(false);
	const [interacting, setInteracting] = useState(false);
	const [maximized, setMaximized] = useState(false);
	const gesture = useRef(null);
	const panelRef = useRef(null);
	if (open && !everOpened) setEverOpened(true);
	useEffect(() => {
		if (!open) return void 0;
		const previous = document.activeElement;
		panelRef.current?.querySelector("button")?.focus();
		return () => {
			if (previous?.isConnected) previous.focus();
		};
	}, [open]);
	useEffect(() => {
		if (interacting || viewport().width <= 620) return;
		try {
			sessionStorage.setItem("mentics:calculator-size", JSON.stringify(size));
		} catch {}
	}, [size, interacting]);
	useEffect(() => {
		if (!open) return void 0;
		const onKeyDown = (event) => {
			if (event.key === "Escape") onClose();
		};
		const onWindowResize = () => {
			if (viewport().width <= 620 || maximized) return;
			const bounds = panelRef.current?.getBoundingClientRect();
			if (!bounds) return;
			const next = clampSize({
				width: bounds.width,
				height: bounds.height
			});
			setSize(next);
			setPosition((current) => clampPosition(current, next));
		};
		window.addEventListener("keydown", onKeyDown);
		window.addEventListener("resize", onWindowResize);
		return () => {
			window.removeEventListener("keydown", onKeyDown);
			window.removeEventListener("resize", onWindowResize);
		};
	}, [
		open,
		onClose,
		maximized
	]);
	const beginGesture = (event, mode) => {
		if (event.button !== 0 || maximized) return;
		if (mode === "move" && event.target.closest("button")) return;
		const bounds = panelRef.current.getBoundingClientRect();
		gesture.current = {
			mode,
			pointerX: event.clientX,
			pointerY: event.clientY,
			offsetX: event.clientX - bounds.left,
			offsetY: event.clientY - bounds.top,
			width: bounds.width,
			height: bounds.height
		};
		setInteracting(true);
		event.currentTarget.setPointerCapture(event.pointerId);
		if (event.pointerType !== "mouse") event.preventDefault();
	};
	const onGestureMove = (event) => {
		const active = gesture.current;
		if (!active) return;
		if (active.mode === "move") {
			setPosition(clampPosition({
				x: event.clientX - active.offsetX,
				y: event.clientY - active.offsetY
			}, {
				width: active.width,
				height: active.height
			}));
			return;
		}
		const next = clampSize({
			width: active.width + (event.clientX - active.pointerX),
			height: active.height + (event.clientY - active.pointerY)
		});
		setSize(next);
		setPosition((current) => clampPosition(current, next));
	};
	const endGesture = () => {
		gesture.current = null;
		setInteracting(false);
	};
	const nudge = (event, mode) => {
		const step = event.shiftKey ? 48 : 12;
		const move = {
			ArrowLeft: [-step, 0],
			ArrowRight: [step, 0],
			ArrowUp: [0, -step],
			ArrowDown: [0, step]
		}[event.key];
		if (!move) return;
		event.preventDefault();
		if (mode === "move") {
			setPosition((current) => clampPosition({
				x: current.x + move[0],
				y: current.y + move[1]
			}, size));
			return;
		}
		const next = clampSize({
			width: size.width + move[0],
			height: size.height + move[1]
		});
		setSize(next);
		setPosition((current) => clampPosition(current, next));
	};
	if (!everOpened) return null;
	return createPortal(/* @__PURE__ */ jsxs("aside", {
		ref: panelRef,
		className: "arena-calculator",
		hidden: !open,
		role: "dialog",
		"aria-modal": "false",
		"data-maximized": maximized,
		"data-interacting": interacting ? "true" : void 0,
		style: {
			left: `${position.x}px`,
			top: `${position.y}px`,
			width: `${size.width}px`,
			height: `${size.height}px`
		},
		"aria-label": "Desmos graphing calculator",
		children: [
			/* @__PURE__ */ jsxs("header", {
				className: "arena-calculator-bar",
				onPointerDown: (event) => beginGesture(event, "move"),
				onPointerMove: onGestureMove,
				onPointerUp: endGesture,
				onPointerCancel: endGesture,
				children: [
					/* @__PURE__ */ jsx("span", {
						className: "arena-calculator-grip",
						tabIndex: 0,
						role: "button",
						"aria-label": "Move the calculator. Use the arrow keys to reposition it.",
						onKeyDown: (event) => nudge(event, "move"),
						children: /* @__PURE__ */ jsx(GripHorizontal, { "aria-hidden": "true" })
					}),
					/* @__PURE__ */ jsx("b", { children: "DESMOS" }),
					/* @__PURE__ */ jsx("button", {
						type: "button",
						onClick: () => setMaximized((value) => !value),
						"aria-label": maximized ? "Restore calculator size" : "Maximize calculator",
						children: maximized ? /* @__PURE__ */ jsx(Minimize2, {}) : /* @__PURE__ */ jsx(Maximize2, {})
					}),
					/* @__PURE__ */ jsx("button", {
						type: "button",
						onClick: onClose,
						"aria-label": "Close the calculator",
						children: /* @__PURE__ */ jsx(X, {})
					})
				]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "arena-calculator-frame",
				children: [!loaded && /* @__PURE__ */ jsx("p", {
					className: "arena-calculator-loading",
					role: "status",
					children: "Opening your graphing workspace…"
				}), /* @__PURE__ */ jsx("iframe", {
					src: DESMOS_EMBED,
					title: "Desmos graphing calculator",
					onLoad: () => setLoaded(true),
					referrerPolicy: "no-referrer",
					sandbox: "allow-scripts allow-same-origin allow-popups allow-forms"
				})]
			}),
			/* @__PURE__ */ jsx("span", {
				className: "arena-calculator-resize",
				onPointerDown: (event) => beginGesture(event, "resize"),
				onPointerMove: onGestureMove,
				onPointerUp: endGesture,
				onPointerCancel: endGesture,
				onKeyDown: (event) => nudge(event, "resize"),
				tabIndex: 0,
				role: "button",
				"aria-label": "Resize the calculator. Use the arrow keys to change its size."
			})
		]
	}), document.body);
}
function ArenaCalculatorToggle({ open, onToggle }) {
	return /* @__PURE__ */ jsxs("button", {
		type: "button",
		className: `arena-calculator-toggle ${open ? "selected" : ""}`,
		onClick: onToggle,
		"aria-pressed": open,
		children: [
			/* @__PURE__ */ jsx(Calculator, { "aria-hidden": "true" }),
			" ",
			open ? "Hide calculator" : "Calculator"
		]
	});
}
//#endregion
//#region frontend/src/arena-experience.jsx
function BattleLoadingScreen({ rank, matchmaking = false }) {
	const [elapsed, setElapsed] = useState(0);
	useEffect(() => {
		const started = Date.now();
		const timer = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1e3)), 1e3);
		return () => clearInterval(timer);
	}, []);
	return /* @__PURE__ */ jsxs("section", {
		className: "arena-loading",
		role: "status",
		"aria-live": "polite",
		"aria-atomic": "true",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "arena-loading-insignia",
				"aria-hidden": "true",
				children: [
					/* @__PURE__ */ jsx(Swords, {}),
					/* @__PURE__ */ jsx("i", {}),
					/* @__PURE__ */ jsx("i", {}),
					/* @__PURE__ */ jsx("i", {})
				]
			}),
			/* @__PURE__ */ jsx("small", { children: matchmaking ? "CONNECTING TO THE ARENA" : `${rank} TRAINING` }),
			/* @__PURE__ */ jsx("h2", { children: elapsed < 20 ? "Building your battle." : "Good questions take thought." }),
			/* @__PURE__ */ jsx("p", { children: matchmaking ? "Finding your match and preparing a shared question set." : "Creating original questions and checking the set for your chosen difficulty." }),
			/* @__PURE__ */ jsx("div", {
				className: "arena-loading-track",
				"aria-hidden": "true",
				children: /* @__PURE__ */ jsx("i", {})
			}),
			/* @__PURE__ */ jsxs("ul", {
				"aria-label": "Battle preparation",
				children: [
					/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx(Check, {}), " Loadout ready"] }),
					/* @__PURE__ */ jsxs("li", {
						className: "working",
						children: [
							/* @__PURE__ */ jsx("span", {}),
							" ",
							matchmaking ? "Connecting players" : "Preparing questions"
						]
					}),
					/* @__PURE__ */ jsxs("li", { children: [/* @__PURE__ */ jsx("span", {}), " Battle begins when ready"] })
				]
			}),
			/* @__PURE__ */ jsx("p", {
				className: "arena-loading-note",
				children: elapsed >= 35 ? "Still working. If this set cannot be prepared, you can retry from the lobby." : "Your round clock starts after the questions are ready."
			})
		]
	});
}
function BattleQuestionPanel({ question, index, selected, onSelect, calculatorOpen, onToggleCalculator, disabled }) {
	const root = useRef(null);
	const paragraphs = question.question_text.split(/\n\s*\n/).filter(Boolean);
	useEffect(() => {
		if (index === 0) return;
		root.current?.querySelector(".arena-question-copy")?.focus({ preventScroll: true });
		root.current?.scrollIntoView({
			block: "start",
			behavior: "instant"
		});
	}, [index]);
	useEffect(() => {
		const keydown = (event) => {
			if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || disabled) return;
			if (event.target.closest("input, textarea, select, [contenteditable=\"true\"], .arena-calculator, [role=\"dialog\"]")) return;
			const option = /^[1-4]$/.test(event.key) ? Number(event.key) - 1 : -1;
			if (option >= 0 && question.options[option] != null) {
				event.preventDefault();
				onSelect(index, option);
			}
		};
		document.addEventListener("keydown", keydown);
		return () => document.removeEventListener("keydown", keydown);
	}, [
		index,
		question.options,
		onSelect,
		disabled
	]);
	return /* @__PURE__ */ jsx("div", {
		className: "battle-questions",
		ref: root,
		children: /* @__PURE__ */ jsxs("article", {
			className: "battle-question battle-question--focus",
			"data-domain": question.domain,
			children: [
				/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("small", { children: [
					question.domain === "math" ? "MATH" : "READING & WRITING",
					" ",
					/* @__PURE__ */ jsx("span", { children: " / " }),
					" ",
					question.skill
				] }), question.domain === "math" && /* @__PURE__ */ jsx(ArenaCalculatorToggle, {
					open: calculatorOpen,
					onToggle: onToggleCalculator
				})] }),
				/* @__PURE__ */ jsxs("div", {
					className: "arena-question-copy",
					tabIndex: -1,
					id: `arena-question-${index}`,
					children: [/* @__PURE__ */ jsxs("span", {
						className: "arena-question-number",
						children: ["QUESTION ", String(index + 1).padStart(2, "0")]
					}), paragraphs.map((paragraph, i) => /* @__PURE__ */ jsx("p", { children: paragraph }, i))]
				}),
				/* @__PURE__ */ jsxs("fieldset", {
					className: "arena-answer-choices",
					"aria-describedby": `arena-question-${index}`,
					disabled,
					children: [/* @__PURE__ */ jsxs("legend", { children: ["Choose your answer ", /* @__PURE__ */ jsx("span", { children: "Keys 1–4" })] }), question.options.map((option, optionIndex) => /* @__PURE__ */ jsxs("label", {
						className: selected === optionIndex ? "selected" : "",
						children: [
							/* @__PURE__ */ jsx("input", {
								type: "radio",
								name: `question-${index}`,
								checked: selected === optionIndex,
								onChange: () => onSelect(index, optionIndex)
							}),
							/* @__PURE__ */ jsx("i", {
								"aria-hidden": "true",
								children: String.fromCharCode(65 + optionIndex)
							}),
							/* @__PURE__ */ jsx("span", { children: option }),
							selected === optionIndex && /* @__PURE__ */ jsx(Check, { "aria-hidden": "true" })
						]
					}, optionIndex))]
				})
			]
		})
	});
}
function BattleReview({ battle, answers }) {
	if (!battle.questionReview?.length) return null;
	const graded = Array.isArray(battle.answers) ? Object.fromEntries(battle.answers.map((answer) => [answer.question_index, answer.selected_option])) : answers;
	return /* @__PURE__ */ jsxs("section", {
		className: "arena-review",
		"aria-label": "Review your answers",
		children: [/* @__PURE__ */ jsxs("header", { children: [
			/* @__PURE__ */ jsx("small", { children: "THE NEXT ROUND STARTS HERE" }),
			/* @__PURE__ */ jsx("h2", { children: "Learn from every answer." }),
			/* @__PURE__ */ jsx("p", { children: "Review the reasoning, then take it into your next battle." })
		] }), battle.questionReview.map((review, i) => {
			const selected = graded[i];
			const correct = selected === battle.answerKey?.[i];
			return /* @__PURE__ */ jsxs("details", {
				className: correct ? "correct" : "incorrect",
				children: [/* @__PURE__ */ jsxs("summary", { children: [
					/* @__PURE__ */ jsx("i", { children: correct ? /* @__PURE__ */ jsx(Check, {}) : /* @__PURE__ */ jsx(X, {}) }),
					/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsxs("b", { children: ["Question ", i + 1] }), /* @__PURE__ */ jsx("small", { children: review.skill })] }),
					/* @__PURE__ */ jsx("em", { children: correct ? "Correct" : selected == null ? "Unanswered" : "Review" }),
					/* @__PURE__ */ jsx(ChevronRight, {})
				] }), /* @__PURE__ */ jsxs("div", { children: [
					/* @__PURE__ */ jsx("p", {
						className: "arena-review-stem",
						children: review.questionText
					}),
					!correct && selected != null && /* @__PURE__ */ jsxs("p", { children: ["Your answer: ", /* @__PURE__ */ jsx("strong", { children: battle.questions?.[i]?.options?.[selected] })] }),
					/* @__PURE__ */ jsxs("p", {
						className: "arena-review-key",
						children: ["Correct answer: ", /* @__PURE__ */ jsx("strong", { children: review.correctAnswer })]
					}),
					/* @__PURE__ */ jsx("p", { children: review.explanation })
				] })]
			}, i);
		})]
	});
}
//#endregion
//#region frontend/src/arena-page.jsx
var arena_page_exports = /* @__PURE__ */ __exportAll({
	default: () => BattleArena,
	winStreakTier: () => winStreakTier
});
async function api(url, options = {}) {
	const controller = new AbortController();
	const timeout = window.setTimeout(() => controller.abort(), 55e3);
	try {
		return await api$1(url, {
			...options,
			signal: controller.signal
		});
	} catch (error) {
		if (error.name === "AbortError") throw new Error("The Arena took too long to respond. Reload to recover any battle that has already started.", { cause: error });
		throw error;
	} finally {
		window.clearTimeout(timeout);
	}
}
var BATTLE_TRAINING_RANKS = [
	[
		"bronze",
		"Bronze",
		"SAT essentials"
	],
	[
		"silver",
		"Silver",
		"Connected skills"
	],
	[
		"gold",
		"Gold",
		"Timing traps"
	],
	[
		"platinum",
		"Platinum",
		"Dense reasoning"
	],
	[
		"diamond",
		"Diamond",
		"Advanced synthesis"
	],
	[
		"master",
		"Master",
		"Elite pace"
	],
	[
		"grandmaster",
		"Grandmaster",
		"Hardest SAT-style sets"
	]
];
var WIN_STREAK_TIERS = [
	{
		at: 1,
		key: "ember",
		label: "Ember",
		hot: "#ffb27a",
		cool: "#e0361f"
	},
	{
		at: 3,
		key: "blaze",
		label: "Blaze",
		hot: "#ffd08a",
		cool: "#ff6b1f"
	},
	{
		at: 5,
		key: "solar",
		label: "Solar",
		hot: "#fff0a8",
		cool: "#ffa722"
	},
	{
		at: 8,
		key: "whitehot",
		label: "White hot",
		hot: "#ffffff",
		cool: "#ffeeb0"
	},
	{
		at: 12,
		key: "azure",
		label: "Azure",
		hot: "#dff4ff",
		cool: "#2f8fff"
	},
	{
		at: 20,
		key: "void",
		label: "Void",
		hot: "#f0dcff",
		cool: "#8b3dff"
	}
];
function winStreakTier(streak) {
	let tier = null;
	for (const candidate of WIN_STREAK_TIERS) if (streak >= candidate.at) tier = candidate;
	return tier;
}
function WinStreakFlame({ streak = 0, best = 0, compact = false }) {
	const tier = winStreakTier(streak);
	if (!tier) {
		if (compact) return null;
		return /* @__PURE__ */ jsxs("div", {
			className: "win-streak win-streak--cold",
			children: [/* @__PURE__ */ jsx(Flame, { "aria-hidden": "true" }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "No win streak" }), /* @__PURE__ */ jsx("small", { children: best > 0 ? `Best run ${best}` : "Win a ranked round to light it" })] })]
		});
	}
	const id = `flame-${tier.key}`;
	return /* @__PURE__ */ jsxs("div", {
		className: `win-streak win-streak--${tier.key}`,
		"data-tier": tier.key,
		title: `${streak} win streak - ${tier.label}`,
		children: [/* @__PURE__ */ jsxs("svg", {
			viewBox: "0 0 24 30",
			"aria-hidden": "true",
			className: "win-streak-flame",
			children: [
				/* @__PURE__ */ jsx("defs", { children: /* @__PURE__ */ jsxs("linearGradient", {
					id,
					x1: "0",
					y1: "1",
					x2: "0",
					y2: "0",
					children: [
						/* @__PURE__ */ jsx("stop", {
							offset: "0%",
							stopColor: tier.cool
						}),
						/* @__PURE__ */ jsx("stop", {
							offset: "55%",
							stopColor: tier.cool
						}),
						/* @__PURE__ */ jsx("stop", {
							offset: "100%",
							stopColor: tier.hot
						})
					]
				}) }),
				/* @__PURE__ */ jsx("path", {
					d: "M12 1c4.2 5.1 6.4 8.6 6.4 11.7 0 2.3-1 3.9-2.6 4.6 1-3.1-.6-6-4-8.6-.9 2.8-2.6 4.4-4.6 6.4-2 2-2.7 4.4-1.6 6.9C3.2 20.6 2 18 2 15.1 2 9.6 6.6 6.2 12 1Z",
					fill: `url(#${id})`
				}),
				/* @__PURE__ */ jsx("path", {
					d: "M12 29c-3.6 0-6.4-2.3-6.4-5.6 0-2.6 1.7-4.4 3.5-6.3 1.5-1.6 2.8-3 3.3-5 2.9 2.3 4.2 4.7 3.5 7.2 1.2-.5 2-1.6 2.2-3.1 1.5 1.9 2.3 3.8 2.3 5.6 0 3.6-3 7.2-8.4 7.2Z",
					fill: `url(#${id})`,
					opacity: ".92"
				})
			]
		}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsxs("b", { children: [
			streak,
			" win",
			streak === 1 ? "" : "s"
		] }), /* @__PURE__ */ jsxs("small", { children: [tier.label, best > streak ? ` · best ${best}` : ""] })] })]
	});
}
function BattleRatingResult({ rank, previousRank, delta }) {
	if (delta == null || !rank) return null;
	const promoted = previousRank && previousRank.key !== rank.key;
	const climbed = delta > 0;
	const span = rank.nextAt ? rank.nextAt - rank.minimum : 0;
	const progress = span > 0 ? Math.min(100, Math.max(0, (rank.rating - rank.minimum) / span * 100)) : 100;
	return /* @__PURE__ */ jsxs("div", {
		className: `battle-rating-result ${climbed ? "is-up" : "is-down"}`,
		children: [/* @__PURE__ */ jsxs("div", {
			className: "battle-rating-swing",
			children: [/* @__PURE__ */ jsxs("b", { children: [climbed ? "+" : "−", Math.abs(delta)] }), /* @__PURE__ */ jsx("small", { children: "RP" })]
		}), /* @__PURE__ */ jsxs("div", {
			className: "battle-rating-standing",
			children: [
				promoted && /* @__PURE__ */ jsxs("em", {
					className: climbed ? "promoted" : "demoted",
					children: [
						climbed ? "RANKED UP" : "RANKED DOWN",
						" · ",
						previousRank.label,
						" → ",
						rank.label
					]
				}),
				/* @__PURE__ */ jsxs("strong", {
					className: `battle-result-rank--${rank.key}`,
					children: [
						rank.label,
						" · ",
						rank.rating,
						" RP"
					]
				}),
				/* @__PURE__ */ jsx("i", {
					className: "battle-rating-track",
					children: /* @__PURE__ */ jsx("b", { style: { width: `${progress}%` } })
				}),
				/* @__PURE__ */ jsx("span", { children: rank.nextAt ? `${Math.max(0, rank.nextAt - rank.rating)} RP to ${rank.nextLabel}` : "Top of the ladder." })
			]
		})]
	});
}
var clockText = (seconds) => `${Math.floor(seconds / 60)}:${String(Math.round(seconds) % 60).padStart(2, "0")}`;
function BattleClock({ startedAt, durationSeconds = 300 }) {
	const [secondsLeft, setSecondsLeft] = useState(null);
	useEffect(() => {
		if (!startedAt) return void 0;
		const tick = () => setSecondsLeft(Math.max(0, durationSeconds - Math.floor((Date.now() - Date.parse(startedAt)) / 1e3)));
		tick();
		const timer = window.setInterval(tick, 1e3);
		return () => window.clearInterval(timer);
	}, [startedAt, durationSeconds]);
	const clock = clockText(secondsLeft == null ? durationSeconds : secondsLeft);
	return /* @__PURE__ */ jsxs("strong", {
		className: secondsLeft != null && secondsLeft < 30 ? "urgent" : "",
		children: [
			/* @__PURE__ */ jsx(Clock3, {}),
			" ",
			clock
		]
	});
}
function ArenaGameLobby({ paused, name, rank, rankProgress, avatar, openCustomizer, mode, setMode, trainingRank, setTrainingRank, selectedTier, busy, join, train, winStreak, bestWinStreak, clocks }) {
	const ranked = mode === "ranked";
	const tierClock = clocks?.[ranked ? rank?.key : trainingRank] ?? clocks?.bronze ?? 300;
	return /* @__PURE__ */ jsxs("section", {
		className: "arena-game-shell",
		"data-mode": mode,
		"aria-label": "SAT Battle Arena game lobby",
		children: [
			/* @__PURE__ */ jsxs("div", {
				className: "arena-game-sky",
				"aria-hidden": "true",
				children: [
					/* @__PURE__ */ jsx("i", {}),
					/* @__PURE__ */ jsx("i", {}),
					/* @__PURE__ */ jsx("i", {}),
					/* @__PURE__ */ jsx("i", {})
				]
			}),
			/* @__PURE__ */ jsxs("header", {
				className: "arena-game-bar",
				children: [
					/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(Swords, {}), " SAT BATTLES"] }),
					/* @__PURE__ */ jsx("b", { children: "MENTICS / ARENA" }),
					/* @__PURE__ */ jsxs("em", { children: [/* @__PURE__ */ jsx("i", {}), " Online"] })
				]
			}),
			/* @__PURE__ */ jsxs("div", {
				className: "arena-game-grid",
				children: [
					/* @__PURE__ */ jsxs("nav", {
						className: "arena-mode-rail",
						"aria-label": "Choose game mode",
						children: [
							/* @__PURE__ */ jsx("small", { children: "CHOOSE YOUR MODE" }),
							/* @__PURE__ */ jsxs("button", {
								type: "button",
								className: ranked ? "selected" : "",
								onClick: () => setMode("ranked"),
								children: [/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx(Swords, {}) }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "Ranked duel" }), /* @__PURE__ */ jsx("small", { children: "Climb the ladder" })] })]
							}),
							/* @__PURE__ */ jsxs("button", {
								type: "button",
								className: !ranked ? "selected" : "",
								onClick: () => setMode("training"),
								children: [/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx(Brain, {}) }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "Training room" }), /* @__PURE__ */ jsx("small", { children: "Choose any tier" })] })]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "arena-season-card",
								children: [
									/* @__PURE__ */ jsx(Trophy, {}),
									/* @__PURE__ */ jsxs("span", { children: [
										/* @__PURE__ */ jsx("small", { children: "CURRENT RANK" }),
										/* @__PURE__ */ jsx("b", { children: rank?.label || "Bronze" }),
										/* @__PURE__ */ jsxs("em", { children: [rank?.rating || 1e3, " RP"] })
									] }),
									/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx("b", { style: { width: `${rankProgress}%` } }) })
								]
							}),
							/* @__PURE__ */ jsx(WinStreakFlame, {
								streak: winStreak,
								best: bestWinStreak
							})
						]
					}),
					/* @__PURE__ */ jsxs("section", {
						className: "arena-player-stage",
						children: [
							/* @__PURE__ */ jsxs("div", {
								className: "arena-stage-wordmark",
								"aria-hidden": "true",
								children: [
									"GAME",
									/* @__PURE__ */ jsx("br", {}),
									"ON."
								]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "arena-stage-caption",
								"aria-hidden": "true",
								children: [/* @__PURE__ */ jsx("span", { children: "YOUR NEXT LEVEL" }), /* @__PURE__ */ jsx("b", { children: "Starts here." })]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "arena-stage-rig",
								"aria-hidden": "true",
								children: [
									/* @__PURE__ */ jsx("i", {}),
									/* @__PURE__ */ jsx("i", {}),
									/* @__PURE__ */ jsx("i", {})
								]
							}),
							/* @__PURE__ */ jsx("div", {
								className: "arena-spotlight",
								"aria-hidden": "true"
							}),
							/* @__PURE__ */ jsx(ArenaAvatarPreview, {
								avatar,
								paused,
								label: `${name || "Your"} Arena fighter`
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "arena-stage-name",
								children: [
									/* @__PURE__ */ jsx("small", { children: "PLAYER / 01" }),
									/* @__PURE__ */ jsx("h1", { children: name || "Arena player" }),
									/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("i", {}), " Ready to play"] })
								]
							}),
							/* @__PURE__ */ jsxs("button", {
								type: "button",
								className: "arena-locker-button",
								onClick: openCustomizer,
								children: [/* @__PURE__ */ jsx(Sparkles, {}), " Edit loadout"]
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "arena-stage-platform",
								"aria-hidden": "true",
								children: [
									/* @__PURE__ */ jsx("i", {}),
									/* @__PURE__ */ jsx("b", { children: "MENTICS" }),
									/* @__PURE__ */ jsx("i", {})
								]
							})
						]
					}),
					/* @__PURE__ */ jsxs("aside", {
						className: "arena-match-console",
						children: [
							/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsx("small", { children: ranked ? "RANKED PLAY" : "TRAINING SIM" }), /* @__PURE__ */ jsx("span", { children: ranked ? /* @__PURE__ */ jsx(Swords, {}) : /* @__PURE__ */ jsx(Brain, {}) })] }),
							/* @__PURE__ */ jsx("h2", { children: ranked ? /* @__PURE__ */ jsxs(Fragment, { children: [
								"One rival.",
								/* @__PURE__ */ jsx("br", {}),
								"Your move."
							] }) : /* @__PURE__ */ jsxs(Fragment, { children: [
								"Practice.",
								/* @__PURE__ */ jsx("br", {}),
								"Level up."
							] }) }),
							/* @__PURE__ */ jsx("p", { children: ranked ? "Same questions. Same clock. Outthink your opponent and climb the ranks." : "Choose your challenge. Build your speed. Keep your rank." }),
							!ranked && /* @__PURE__ */ jsx("div", {
								className: "arena-rank-selector",
								role: "radiogroup",
								"aria-label": "Bot question rank",
								children: BATTLE_TRAINING_RANKS.map(([key, label]) => /* @__PURE__ */ jsxs("button", {
									type: "button",
									role: "radio",
									"aria-checked": trainingRank === key,
									className: trainingRank === key ? "selected" : "",
									onClick: () => setTrainingRank(key),
									children: [/* @__PURE__ */ jsx("i", { "data-rank": key }), /* @__PURE__ */ jsx("span", { children: label })]
								}, key))
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "arena-difficulty-callout",
								children: [/* @__PURE__ */ jsx(Target, {}), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("small", { children: "QUESTION TIER" }), /* @__PURE__ */ jsx("b", { children: ranked ? `${rank?.label || "Bronze"} matchmaking` : `${selectedTier[1]} simulation` })] })]
							}),
							/* @__PURE__ */ jsx("p", {
								className: "arena-scale-copy",
								children: "Every rank gets full-length, original SAT-style questions. Higher ranks add denser passages, tighter traps, multi-constraint math, and dramatically harder reasoning."
							}),
							/* @__PURE__ */ jsxs("button", {
								type: "button",
								className: "arena-deploy-button",
								onClick: ranked ? join : train,
								disabled: busy,
								children: [/* @__PURE__ */ jsx("span", { children: busy ? "INITIALIZING…" : ranked ? "FIND A MATCH" : "START TRAINING" }), /* @__PURE__ */ jsx("i", { children: ranked ? /* @__PURE__ */ jsx(Swords, {}) : /* @__PURE__ */ jsx(Zap, {}) })]
							}),
							/* @__PURE__ */ jsxs("footer", { children: [
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: "05" }), " QUESTIONS"] }),
								/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("b", { children: clockText(tierClock) }), " CLOCK"] }),
								/* @__PURE__ */ jsxs("span", { children: [
									/* @__PURE__ */ jsx("b", { children: ranked ? "RP" : "0 RP" }),
									" ",
									ranked ? "AT STAKE" : "RISK"
								] })
							] }),
							ranked && /* @__PURE__ */ jsx("p", {
								className: "arena-match-note",
								children: "An Arena bot joins if no player matches within 30 seconds."
							})
						]
					})
				]
			}),
			/* @__PURE__ */ jsxs("footer", {
				className: "arena-game-ticker",
				children: [
					/* @__PURE__ */ jsx("span", { children: "FIVE QUESTIONS. ONE SHARED CHALLENGE." }),
					/* @__PURE__ */ jsx("i", {}),
					/* @__PURE__ */ jsx("span", { children: "ACCURACY WINS · SPEED BREAKS THE TIE" }),
					/* @__PURE__ */ jsx("i", {}),
					/* @__PURE__ */ jsx("span", { children: "GRANDMASTER = MAXIMUM SAT DIFFICULTY" })
				]
			})
		]
	});
}
function BattleArena() {
	const d = boot.data;
	const [battle, setBattle] = useState(d.currentBattle);
	const [answers, setAnswers] = useState(() => {
		if (d.currentBattle?.answers?.length) return Object.fromEntries(d.currentBattle.answers.map((a) => [a.question_index, a.selected_option]));
		try {
			return JSON.parse(sessionStorage.getItem(`mentics:battle:${d.currentBattle?.id}`)) || {};
		} catch {
			return {};
		}
	});
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState("");
	const [activeQuestion, setActiveQuestion] = useState(0);
	const [calculatorOpen, setCalculatorOpen] = useState(false);
	const winStreak = battle?.winStreak ?? d.winStreak ?? 0;
	const bestWinStreak = battle?.bestWinStreak ?? d.bestWinStreak ?? 0;
	const [cinematic, setCinematic] = useState("");
	const [lobbyMode, setLobbyMode] = useState("ranked");
	const [trainingRank, setTrainingRank] = useState(d.battleRank?.key || "bronze");
	const [avatar, setAvatar] = useState(() => normalizeArenaAvatar(d.arenaAvatar || d.currentBattle?.playerAvatar));
	const savedAvatar = useRef(avatar);
	const [customizing, setCustomizing] = useState(false);
	const [savingAvatar, setSavingAvatar] = useState(false);
	const [musicEnabled, setMusicEnabled] = useState(false);
	const previousStatus = useRef(d.currentBattle?.status);
	const stageRef = useRef(null);
	const cinematicTimers = useRef([]);
	const arenaAudio = useRef(null);
	const active = battle?.status === "active";
	const waiting = battle?.status === "waiting";
	const complete = battle?.status === "complete";
	const idle = !battle || battle.status === "expired";
	const clearCinematic = useCallback(() => {
		cinematicTimers.current.forEach(window.clearTimeout);
		cinematicTimers.current = [];
	}, []);
	const stopArenaMusic = useCallback(() => {
		const audio = arenaAudio.current;
		if (!audio) return;
		arenaAudio.current = null;
		window.clearInterval(audio.timer);
		const now = audio.context.currentTime;
		audio.master.gain.cancelScheduledValues(now);
		audio.master.gain.setValueAtTime(Math.max(1e-4, audio.master.gain.value), now);
		audio.master.gain.exponentialRampToValueAtTime(1e-4, now + .12);
		window.setTimeout(() => {
			audio.oscillators.forEach((oscillator) => {
				try {
					oscillator.stop();
				} catch (error) {}
			});
			audio.oscillators.clear();
			audio.context.close().catch(() => void 0);
		}, 150);
	}, []);
	const startArenaMusic = useCallback((force = false) => {
		if (!musicEnabled && !force || arenaAudio.current || typeof window === "undefined") return;
		const AudioContext = window.AudioContext || window.webkitAudioContext;
		if (!AudioContext) return;
		const context = new AudioContext();
		const master = context.createGain();
		master.gain.setValueAtTime(1e-4, context.currentTime);
		master.gain.exponentialRampToValueAtTime(.035, context.currentTime + .2);
		master.connect(context.destination);
		const oscillators = /* @__PURE__ */ new Set();
		const pattern = [
			0,
			7,
			12,
			7,
			3,
			10,
			7,
			14,
			0,
			7,
			15,
			12,
			3,
			10,
			7,
			2
		];
		let step = 0;
		const playBeat = () => {
			const now = context.currentTime;
			const note = 220 * Math.pow(2, pattern[step % pattern.length] / 12);
			const lead = context.createOscillator();
			const leadGain = context.createGain();
			lead.type = step % 4 === 0 ? "square" : "triangle";
			lead.frequency.setValueAtTime(note, now);
			leadGain.gain.setValueAtTime(1e-4, now);
			leadGain.gain.exponentialRampToValueAtTime(.19, now + .018);
			leadGain.gain.exponentialRampToValueAtTime(1e-4, now + .22);
			lead.connect(leadGain).connect(master);
			lead.start(now);
			lead.stop(now + .24);
			oscillators.add(lead);
			lead.onended = () => {
				lead.disconnect();
				leadGain.disconnect();
				oscillators.delete(lead);
			};
			if (step % 4 === 0) {
				const bass = context.createOscillator();
				const bassGain = context.createGain();
				bass.type = "sine";
				bass.frequency.setValueAtTime(note / 2, now);
				bassGain.gain.setValueAtTime(1e-4, now);
				bassGain.gain.exponentialRampToValueAtTime(.28, now + .015);
				bassGain.gain.exponentialRampToValueAtTime(1e-4, now + .27);
				bass.connect(bassGain).connect(master);
				bass.start(now);
				bass.stop(now + .29);
				oscillators.add(bass);
				bass.onended = () => {
					bass.disconnect();
					bassGain.disconnect();
					oscillators.delete(bass);
				};
			}
			step += 1;
		};
		context.resume().catch(() => {});
		playBeat();
		arenaAudio.current = {
			context,
			master,
			oscillators,
			timer: window.setInterval(playBeat, 285)
		};
	}, [musicEnabled]);
	const toggleArenaMusic = () => {
		if (musicEnabled) {
			stopArenaMusic();
			setMusicEnabled(false);
		} else {
			setMusicEnabled(true);
			startArenaMusic(true);
		}
	};
	const launchCinematic = useCallback(() => {
		clearCinematic();
		if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
		setCinematic("fight");
		[["", 650]].forEach(([phase, delay]) => cinematicTimers.current.push(window.setTimeout(() => setCinematic(phase), delay)));
	}, [clearCinematic]);
	const requestVersion = useRef(0);
	const polling = useRef(false);
	const refresh = useCallback(async (id) => {
		if (polling.current) return;
		polling.current = true;
		const version = requestVersion.current;
		try {
			const next = await api(`/api/sat-battles/${id}`);
			if (version === requestVersion.current) {
				setBattle(next);
				setError("");
			}
		} catch {
			if (version === requestVersion.current) setError("Connection interrupted. Reconnecting automatically; your selections are kept.");
		} finally {
			polling.current = false;
		}
	}, []);
	useEffect(() => {
		if (!battle?.id || !["waiting", "active"].includes(battle.status)) return void 0;
		const poll = window.setInterval(() => {
			if (!document.hidden) refresh(battle.id);
		}, 1800);
		const onVisible = () => {
			if (!document.hidden) refresh(battle.id);
			if (document.hidden) arenaAudio.current?.context.suspend();
			else arenaAudio.current?.context.resume().catch(() => {});
		};
		document.addEventListener("visibilitychange", onVisible);
		return () => {
			window.clearInterval(poll);
			requestVersion.current += 1;
			document.removeEventListener("visibilitychange", onVisible);
		};
	}, [
		battle?.id,
		battle?.status,
		refresh
	]);
	useEffect(() => {
		if (!battle?.id) return;
		try {
			sessionStorage.setItem(`mentics:battle:${battle.id}`, JSON.stringify(answers));
		} catch {}
	}, [battle?.id, answers]);
	useEffect(() => {
		const previous = previousStatus.current;
		previousStatus.current = battle?.status;
		if (previous !== "waiting" || battle?.status !== "active") return void 0;
		launchCinematic();
	}, [battle?.status, launchCinematic]);
	useEffect(() => {
		return () => clearCinematic();
	}, [clearCinematic]);
	useEffect(() => {
		if (!waiting && !active) stopArenaMusic();
	}, [
		waiting,
		active,
		stopArenaMusic
	]);
	useEffect(() => {
		return () => stopArenaMusic();
	}, [stopArenaMusic]);
	useEffect(() => {
		if (!customizing) return void 0;
		const previousOverflow = document.body.style.overflow;
		document.body.style.overflow = "hidden";
		return () => {
			document.body.style.overflow = previousOverflow;
		};
	}, [customizing]);
	useEffect(() => {
		if (battle?.status !== "active") return void 0;
		const frame = window.requestAnimationFrame(() => stageRef.current?.scrollIntoView({
			block: "start",
			behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"
		}));
		return () => window.cancelAnimationFrame(frame);
	}, [battle?.id, battle?.status]);
	useEffect(() => {
		if (battle?.status !== "complete" || !battle.youWon || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return void 0;
		const burst = () => import("canvas-confetti").then(({ default: confetti }) => confetti({
			particleCount: 56,
			spread: 66,
			startVelocity: 29,
			origin: { y: .62 },
			colors: [
				"#6f45dc",
				"#a786ff",
				"#e2d6ff",
				"#ffd267"
			]
		}));
		burst();
		const timer = window.setTimeout(burst, 240);
		return () => window.clearTimeout(timer);
	}, [
		battle?.id,
		battle?.status,
		battle?.youWon
	]);
	useEffect(() => {
		if (battle?.status !== "complete") return;
		boot.data.battleRank = battle.rank;
		boot.data.winStreak = battle.winStreak;
		boot.data.bestWinStreak = battle.bestWinStreak;
		boot.data.currentBattle = null;
	}, [battle]);
	const startBattle = (nextBattle) => {
		requestVersion.current += 1;
		setCalculatorOpen(false);
		setAnswers({});
		setActiveQuestion(0);
		setBattle(nextBattle);
		if (nextBattle?.status === "active") launchCinematic();
	};
	const join = async () => {
		startArenaMusic();
		setBusy(true);
		setError("");
		try {
			startBattle(await api("/api/sat-battles/queue", { method: "POST" }));
		} catch (x) {
			stopArenaMusic();
			setError(x.message);
		} finally {
			setBusy(false);
		}
	};
	const train = async () => {
		startArenaMusic();
		setBusy(true);
		setError("");
		try {
			startBattle(await api("/api/sat-battles/train", {
				method: "POST",
				body: JSON.stringify({ rank: trainingRank })
			}));
		} catch (x) {
			stopArenaMusic();
			setError(x.message);
		} finally {
			setBusy(false);
		}
	};
	const cancelQueue = async () => {
		if (!battle) return;
		setBusy(true);
		setError("");
		try {
			requestVersion.current += 1;
			await api(`/api/sat-battles/${battle.id}/cancel`, { method: "POST" });
			stopArenaMusic();
			setBattle(null);
		} catch (x) {
			setError(x.message);
		} finally {
			setBusy(false);
		}
	};
	const saveAvatar = async () => {
		setSavingAvatar(true);
		setError("");
		try {
			const saved = await api("/api/sat-battles/avatar", {
				method: "POST",
				body: JSON.stringify(avatar)
			});
			setAvatar(saved.avatar);
			savedAvatar.current = saved.avatar;
			boot.data.arenaAvatar = saved.avatar;
			setCustomizing(false);
			toast.success("Fighter loadout equipped");
		} catch (x) {
			setAvatar(savedAvatar.current);
			setError(x.message);
			toast.error(x.message);
		} finally {
			setSavingAvatar(false);
		}
	};
	const closeCustomizer = useCallback(() => {
		setAvatar(savedAvatar.current);
		setCustomizing(false);
	}, []);
	const select = useCallback((questionIndex, selectedOption) => setAnswers((current) => ({
		...current,
		[questionIndex]: selectedOption
	})), []);
	const submit = async () => {
		if (!battle || Object.keys(answers).length !== battle.questions.length) return;
		setBusy(true);
		setError("");
		try {
			requestVersion.current += 1;
			setBattle(await api(`/api/sat-battles/${battle.id}/submit`, {
				method: "POST",
				body: JSON.stringify({ answers: Object.entries(answers).map(([question_index, selected_option]) => ({
					question_index: Number(question_index),
					selected_option
				})) })
			}));
		} catch (x) {
			setError(x.message);
		} finally {
			setBusy(false);
		}
	};
	const spotlight = d.spotlight;
	const rank = battle?.rank || d.battleRank;
	const battleDifficulty = String(battle?.difficulty || rank?.label || "Bronze").toUpperCase();
	const rankProgress = rank?.nextAt ? Math.max(0, Math.min(100, (rank.rating - rank.minimum) / (rank.nextAt - rank.minimum) * 100)) : 100;
	const questionCount = battle?.questions?.length || 0;
	const currentQuestionIndex = Math.min(activeQuestion, Math.max(0, questionCount - 1));
	const currentQuestion = battle?.questions?.[currentQuestionIndex];
	const answeredCount = Object.keys(answers).length;
	const remainingCount = questionCount - answeredCount;
	const selectedTrainingTier = BATTLE_TRAINING_RANKS.find(([key]) => key === trainingRank) || BATTLE_TRAINING_RANKS[0];
	const advanceQuestion = () => setActiveQuestion((index) => Math.min(index + 1, Math.max(0, questionCount - 1)));
	return /* @__PURE__ */ jsx(AppShell, {
		name: d.name,
		children: /* @__PURE__ */ jsxs("main", {
			className: `app-main battle-page ${active ? "battle-page--in-match" : waiting ? "battle-page--queue" : complete ? "battle-page--complete" : ""}`,
			children: [
				idle && !busy && /* @__PURE__ */ jsx(ArenaGameLobby, {
					paused: customizing,
					name: d.name,
					rank,
					rankProgress,
					avatar,
					openCustomizer: () => setCustomizing(true),
					mode: lobbyMode,
					setMode: setLobbyMode,
					trainingRank,
					setTrainingRank,
					selectedTier: selectedTrainingTier,
					clocks: d.battleClocks,
					busy,
					join,
					train,
					winStreak,
					bestWinStreak
				}),
				idle && busy && /* @__PURE__ */ jsx(BattleLoadingScreen, {
					rank: selectedTrainingTier[1],
					matchmaking: lobbyMode === "ranked"
				}),
				idle && customizing && typeof document !== "undefined" && createPortal(/* @__PURE__ */ jsx(ArenaCustomizer, {
					avatar,
					onChange: setAvatar,
					onSave: saveAvatar,
					onClose: closeCustomizer,
					saving: savingAvatar
				}), document.body),
				error && /* @__PURE__ */ jsxs("div", {
					className: "error-banner",
					role: "alert",
					children: [
						error,
						/* @__PURE__ */ jsx("button", {
							onClick: () => window.location.reload(),
							children: "Reload battle"
						}),
						/* @__PURE__ */ jsx("button", {
							onClick: () => setError(""),
							children: "Dismiss"
						})
					]
				}),
				waiting && /* @__PURE__ */ jsxs("section", {
					className: "battle-stage battle-stage--waiting arena-queue-stage",
					"aria-live": "polite",
					children: [
						/* @__PURE__ */ jsxs("div", {
							className: "arena-queue-world",
							children: [
								/* @__PURE__ */ jsxs("div", {
									className: "arena-queue-podium arena-queue-podium--you",
									children: [
										/* @__PURE__ */ jsx("div", { className: "arena-queue-light" }),
										/* @__PURE__ */ jsx(ArenaFighter, {
											avatar: battle.playerAvatar || avatar,
											label: `${d.name || "Your"} fighter waiting for a match`,
											size: "medium"
										}),
										/* @__PURE__ */ jsx("strong", { children: d.name || "YOU" }),
										/* @__PURE__ */ jsx("span", { children: "READY" })
									]
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "arena-queue-core",
									children: [
										/* @__PURE__ */ jsx("span", {
											className: "battle-search-orbit",
											children: /* @__PURE__ */ jsx(Swords, {})
										}),
										/* @__PURE__ */ jsx("small", { children: "MATCHMAKING" }),
										/* @__PURE__ */ jsx("h2", { children: battle.preparing ? "Building your battle" : "Searching the Arena" }),
										/* @__PURE__ */ jsx("p", { children: battle.preparing ? "Players connected. Preparing your shared questions." : "Scanning for a live challenger" }),
										/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx("b", {}) }),
										/* @__PURE__ */ jsx("em", { children: battle.preparing ? "YOUR CLOCK HAS NOT STARTED" : "BOT DROP-IN AT 0:30" })
									]
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "arena-queue-podium arena-queue-podium--rival",
									children: [
										/* @__PURE__ */ jsx("div", { className: "arena-queue-light" }),
										/* @__PURE__ */ jsx("div", {
											className: "arena-mystery-fighter",
											children: "?"
										}),
										/* @__PURE__ */ jsx("strong", { children: "CHALLENGER" }),
										/* @__PURE__ */ jsx("span", { children: "SEARCHING" })
									]
								})
							]
						}),
						/* @__PURE__ */ jsx("p", {
							className: "arena-queue-note",
							children: "Both players receive the same fresh SAT set. If nobody joins within 30 seconds, an Arena bot enters automatically."
						}),
						/* @__PURE__ */ jsxs("div", {
							className: "battle-wait-actions",
							children: [
								/* @__PURE__ */ jsxs("button", {
									className: "text-button",
									onClick: () => refresh(battle.id),
									children: ["Check status ", /* @__PURE__ */ jsx(RotateCcw, {})]
								}),
								/* @__PURE__ */ jsxs("button", {
									className: "text-button",
									onClick: toggleArenaMusic,
									children: [
										musicEnabled ? /* @__PURE__ */ jsx(Volume2, {}) : /* @__PURE__ */ jsx(VolumeX, {}),
										" Music ",
										musicEnabled ? "on" : "off"
									]
								}),
								/* @__PURE__ */ jsx("button", {
									className: "text-button",
									disabled: busy,
									onClick: cancelQueue,
									children: "Leave queue"
								})
							]
						})
					]
				}),
				active && /* @__PURE__ */ jsxs("section", {
					ref: stageRef,
					className: `battle-stage battle-stage--active ${answers[currentQuestionIndex] != null ? "is-striking" : ""}`,
					"aria-label": "Active SAT battle",
					children: [
						cinematic && /* @__PURE__ */ jsxs("div", {
							className: "arena-cinematic",
							"data-phase": cinematic,
							role: "status",
							"aria-live": "assertive",
							children: [
								/* @__PURE__ */ jsx(Starfield, {
									warp: true,
									tone: "violet"
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "arena-cinematic-fighters",
									"aria-hidden": "true",
									children: [
										/* @__PURE__ */ jsxs("div", {
											className: "arena-cinematic-fighter arena-cinematic-fighter--you",
											children: [/* @__PURE__ */ jsx(ArenaFighter, {
												avatar: battle.playerAvatar || avatar,
												size: "medium",
												state: "combat"
											}), /* @__PURE__ */ jsx("b", { children: d.name || "YOU" })]
										}),
										/* @__PURE__ */ jsx("i", { children: "VS" }),
										/* @__PURE__ */ jsxs("div", {
											className: "arena-cinematic-fighter arena-cinematic-fighter--rival",
											children: [/* @__PURE__ */ jsx(ArenaFighter, {
												avatar: battle.opponentAvatar,
												size: "medium",
												facing: "left",
												state: "combat"
											}), /* @__PURE__ */ jsx("b", { children: battle.opponentName || "RIVAL" })]
										})
									]
								}),
								/* @__PURE__ */ jsxs("div", {
									className: "arena-cinematic-count",
									children: [
										/* @__PURE__ */ jsx("small", { children: cinematic === "fight" ? "MENTICS ARENA" : "ARENA LINK ESTABLISHED" }),
										/* @__PURE__ */ jsx("strong", { children: cinematic === "fight" ? "FIGHT" : cinematic }),
										/* @__PURE__ */ jsx("span", { children: cinematic === "fight" ? "MAKE EVERY SECOND COUNT" : "PREPARE TO THINK FAST" })
									]
								}),
								cinematic !== "fight" && /* @__PURE__ */ jsx("button", {
									type: "button",
									onClick: () => {
										clearCinematic();
										setCinematic("");
									},
									children: "Skip intro"
								})
							]
						}),
						/* @__PURE__ */ jsxs("header", {
							className: "battle-status",
							children: [
								/* @__PURE__ */ jsxs("span", { children: [
									/* @__PURE__ */ jsx("i", {}),
									/* @__PURE__ */ jsx("b", { children: battle.mode === "training" ? "PRIVATE BOT DRILL" : `${battleDifficulty} SAT BATTLE` }),
									/* @__PURE__ */ jsxs("small", { children: [
										"vs ",
										battle.opponentName || "your challenger",
										battle.questionSource === "gemini" ? " · GEMINI LIVE SET" : ""
									] })
								] }),
								/* @__PURE__ */ jsxs("button", {
									className: "arena-audio-toggle",
									type: "button",
									onClick: toggleArenaMusic,
									"aria-label": musicEnabled ? "Mute arena music" : "Play arena music",
									children: [
										musicEnabled ? /* @__PURE__ */ jsx(Volume2, {}) : /* @__PURE__ */ jsx(VolumeX, {}),
										" ",
										/* @__PURE__ */ jsxs("span", { children: ["Music ", musicEnabled ? "on" : "off"] })
									]
								}),
								/* @__PURE__ */ jsx(BattleClock, {
									startedAt: battle.startedAt,
									durationSeconds: battle.durationSeconds
								})
							]
						}),
						battle.submitted ? /* @__PURE__ */ jsxs("div", {
							className: "battle-locked",
							children: [
								/* @__PURE__ */ jsx("span", {
									className: "battle-search-orbit",
									children: /* @__PURE__ */ jsx(Check, {})
								}),
								/* @__PURE__ */ jsx("h2", { children: "Answers locked." }),
								/* @__PURE__ */ jsx("p", { children: battle.mode === "training" ? "Mentics Arena Bot is scoring your round now." : `Waiting for ${battle.opponentName || "your challenger"} to finish. The arena will reveal the result automatically.` })
							]
						}) : /* @__PURE__ */ jsxs(Fragment, { children: [
							/* @__PURE__ */ jsxs("div", {
								className: "battle-combat-hud",
								"aria-label": `You versus ${battle.opponentName || "Arena bot"}`,
								children: [
									/* @__PURE__ */ jsxs("article", {
										className: "battle-combatant battle-combatant--you",
										children: [/* @__PURE__ */ jsx(ArenaFighter, {
											avatar: battle.playerAvatar || avatar,
											label: "Your fighter",
											size: "portrait",
											state: "combat"
										}), /* @__PURE__ */ jsxs("div", {
											className: "battle-combatant-stats",
											children: [
												/* @__PURE__ */ jsx("small", { children: "YOU" }),
												/* @__PURE__ */ jsx("b", { children: d.name || "Challenger" }),
												/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx("em", { style: { width: `${questionCount ? answeredCount / questionCount * 100 : 0}%` } }) }),
												/* @__PURE__ */ jsxs("strong", { children: [
													"FOCUS ",
													answeredCount,
													"/",
													questionCount
												] })
											]
										})]
									}),
									/* @__PURE__ */ jsxs("div", {
										className: "battle-clash",
										children: [
											/* @__PURE__ */ jsx("i", {}),
											/* @__PURE__ */ jsx("b", { children: "VS" }),
											/* @__PURE__ */ jsx("span", { children: currentQuestion?.skill || "SAT ARENA" })
										]
									}),
									/* @__PURE__ */ jsxs("article", {
										className: "battle-combatant battle-combatant--rival",
										children: [/* @__PURE__ */ jsxs("div", {
											className: "battle-combatant-stats",
											children: [
												/* @__PURE__ */ jsx("small", { children: "RIVAL" }),
												/* @__PURE__ */ jsx("b", { children: battle.opponentName || "Arena Bot" }),
												/* @__PURE__ */ jsx("i", { children: /* @__PURE__ */ jsx("em", {}) }),
												/* @__PURE__ */ jsx("strong", { children: battle.opponentSubmitted ? "ANSWERS LOCKED" : "IN THE ARENA" })
											]
										}), /* @__PURE__ */ jsx(ArenaFighter, {
											avatar: battle.opponentAvatar,
											label: `${battle.opponentName || "Rival"} fighter`,
											size: "portrait",
											facing: "left",
											state: "combat"
										})]
									})
								]
							}),
							/* @__PURE__ */ jsx("div", {
								className: "battle-question-progress",
								"aria-label": `Question ${currentQuestionIndex + 1} of ${questionCount}`,
								children: battle.questions.map((_, index) => /* @__PURE__ */ jsx("button", {
									type: "button",
									className: `${answers[index] != null ? "done" : ""} ${currentQuestionIndex === index ? "current" : ""}`,
									onClick: () => setActiveQuestion(index),
									"aria-label": `Go to question ${index + 1}${answers[index] != null ? ", answered" : ""}`,
									children: index + 1
								}, index))
							}),
							/* @__PURE__ */ jsxs("div", {
								className: "battle-round-heading",
								children: [/* @__PURE__ */ jsxs("span", { children: [
									"QUESTION ",
									currentQuestionIndex + 1,
									" OF ",
									questionCount
								] }), /* @__PURE__ */ jsxs("b", { children: [
									answeredCount,
									"/",
									questionCount,
									" SELECTED"
								] })]
							}),
							currentQuestion && /* @__PURE__ */ jsx(BattleQuestionPanel, {
								question: currentQuestion,
								index: currentQuestionIndex,
								selected: answers[currentQuestionIndex],
								onSelect: select,
								disabled: busy,
								calculatorOpen,
								onToggleCalculator: () => setCalculatorOpen((value) => !value)
							}, currentQuestionIndex),
							/* @__PURE__ */ jsxs("div", {
								className: "battle-round-actions",
								children: [/* @__PURE__ */ jsx("p", {
									role: "status",
									children: answers[currentQuestionIndex] != null ? "Selected. You can change this before submitting." : "Choose your answer. Use keys 1-4 or tap a choice."
								}), currentQuestionIndex < questionCount - 1 ? /* @__PURE__ */ jsxs("button", {
									type: "button",
									className: "button button--quiet",
									onClick: advanceQuestion,
									children: [
										answers[currentQuestionIndex] != null ? "Next question" : "Skip for now",
										" ",
										/* @__PURE__ */ jsx(ArrowRight, {})
									]
								}) : /* @__PURE__ */ jsxs("button", {
									type: "button",
									className: "button button--quiet",
									onClick: () => {
										const unanswered = battle.questions.findIndex((_, index) => answers[index] == null);
										if (unanswered >= 0) setActiveQuestion(unanswered);
										else submit();
									},
									children: [
										remainingCount ? `Answer ${remainingCount} remaining` : "Submit answers",
										" ",
										/* @__PURE__ */ jsx(ArrowRight, {})
									]
								})]
							}),
							/* @__PURE__ */ jsxs("button", {
								className: "button button--primary battle-lock",
								disabled: busy || answeredCount !== questionCount,
								onClick: submit,
								children: [
									busy ? "Locking answers…" : `Lock in ${answeredCount}/${questionCount} answers`,
									" ",
									/* @__PURE__ */ jsx(ArrowRight, {})
								]
							}),
							/* @__PURE__ */ jsx(ArenaCalculator, {
								open: calculatorOpen,
								onClose: () => setCalculatorOpen(false)
							})
						] })
					]
				}),
				complete && /* @__PURE__ */ jsxs("section", {
					className: `battle-result battle-result--fighters ${battle.youWon ? "won" : battle.draw ? "draw" : "lost"}`,
					children: [
						(battle.youWon || battle.draw) && /* @__PURE__ */ jsx("div", {
							className: "arena-confetti",
							"aria-hidden": "true",
							children: Array.from({ length: 12 }, (_, index) => /* @__PURE__ */ jsx("i", { style: { "--arena-index": index } }, index))
						}),
						/* @__PURE__ */ jsx("div", {
							className: "battle-result-mark",
							children: battle.youWon ? /* @__PURE__ */ jsx(Trophy, {}) : battle.draw ? /* @__PURE__ */ jsx(Target, {}) : /* @__PURE__ */ jsx(Swords, {})
						}),
						/* @__PURE__ */ jsx("small", { children: battle.mode === "training" ? "BOT DRILL COMPLETE" : battle.youWon ? "VICTORY" : battle.draw ? "DRAW" : "BATTLE COMPLETE" }),
						/* @__PURE__ */ jsx("h2", { children: battle.mode === "training" ? "A sharper round in the bank." : battle.youWon ? "You won the race." : battle.draw ? "A dead-even finish." : "A strong round. Run it back." }),
						/* @__PURE__ */ jsxs("div", {
							className: "arena-result-versus",
							children: [
								/* @__PURE__ */ jsxs("article", {
									className: battle.youWon ? "winner" : "",
									children: [
										/* @__PURE__ */ jsx(ArenaFighter, {
											avatar: battle.playerAvatar || avatar,
											label: "Your fighter",
											size: "medium",
											state: battle.youWon ? "victory" : "idle"
										}),
										/* @__PURE__ */ jsx("b", { children: d.name || "YOU" }),
										/* @__PURE__ */ jsx("strong", { children: battle.yourScore }),
										/* @__PURE__ */ jsx("span", { children: "CORRECT" })
									]
								}),
								/* @__PURE__ */ jsx("i", { children: "VS" }),
								/* @__PURE__ */ jsxs("article", {
									className: !battle.youWon && !battle.draw ? "winner" : "",
									children: [
										/* @__PURE__ */ jsx(ArenaFighter, {
											avatar: battle.opponentAvatar,
											label: `${battle.opponentName || "Rival"} fighter`,
											size: "medium",
											facing: "left",
											state: !battle.youWon && !battle.draw ? "victory" : "idle"
										}),
										/* @__PURE__ */ jsx("b", { children: battle.opponentName || "RIVAL" }),
										/* @__PURE__ */ jsx("strong", { children: battle.opponentScore }),
										/* @__PURE__ */ jsx("span", { children: "CORRECT" })
									]
								})
							]
						}),
						battle.mode === "training" ? /* @__PURE__ */ jsx("em", {
							className: "battle-training-note",
							children: "This private drill did not affect your rating."
						}) : battle.ratingDelta != null ? /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx(BattleRatingResult, {
							rank: battle.rank,
							previousRank: battle.previousRank,
							delta: battle.ratingDelta
						}), /* @__PURE__ */ jsx(WinStreakFlame, {
							streak: battle.winStreak || 0,
							best: battle.bestWinStreak || 0
						})] }) : /* @__PURE__ */ jsxs("em", {
							className: `battle-result-rank battle-result-rank--${battle.rank?.key}`,
							children: [
								battle.rank?.label,
								" · ",
								battle.rank?.rating,
								" RP"
							]
						}),
						/* @__PURE__ */ jsxs("button", {
							className: "button button--primary",
							onClick: () => {
								requestVersion.current += 1;
								setCalculatorOpen(false);
								setBattle(null);
								setAnswers({});
								setActiveQuestion(0);
							},
							children: [
								battle.mode === "training" ? "Train again" : "Find another battle",
								" ",
								/* @__PURE__ */ jsx(Swords, {})
							]
						})
					]
				}),
				complete && /* @__PURE__ */ jsx(BattleReview, {
					battle,
					answers
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "battle-lower",
					children: [/* @__PURE__ */ jsxs("div", {
						className: "battle-rules",
						children: [
							/* @__PURE__ */ jsx("small", { children: "HOW IT WORKS" }),
							/* @__PURE__ */ jsx("h2", { children: "One clean round. No fluff." }),
							/* @__PURE__ */ jsxs("div", { children: [
								/* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("b", { children: "01" }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("strong", { children: "Match" }), /* @__PURE__ */ jsx("p", { children: "We pair you with one student and serve the same question set." })] })] }),
								/* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("b", { children: "02" }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("strong", { children: "Race" }), /* @__PURE__ */ jsx("p", { children: "Answer all five before the clock runs out. It is sized to the tier, and it starts together." })] })] }),
								/* @__PURE__ */ jsxs("article", { children: [/* @__PURE__ */ jsx("b", { children: "03" }), /* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx("strong", { children: "Climb" }), /* @__PURE__ */ jsx("p", { children: "Accuracy takes it. Faster completion breaks a tied score." })] })] })
							] })
						]
					}), /* @__PURE__ */ jsxs("aside", {
						className: "battle-leaderboard",
						children: [/* @__PURE__ */ jsxs("header", { children: [/* @__PURE__ */ jsxs("span", { children: [/* @__PURE__ */ jsx(Trophy, {}), " BATTLE LEADERBOARD"] }), /* @__PURE__ */ jsx("a", {
							href: "#battle-rankings",
							children: "View rankings"
						})] }), d.leaderboard?.length ? d.leaderboard.slice(0, 5).map((row, index) => /* @__PURE__ */ jsxs("div", { children: [
							/* @__PURE__ */ jsx("i", { children: index + 1 }),
							/* @__PURE__ */ jsx("span", { children: String(row.user_name || "M").slice(0, 1) }),
							/* @__PURE__ */ jsxs("b", { children: [row.user_name, /* @__PURE__ */ jsx("small", {
								className: `battle-rank-label battle-rank-label--${row.rank.key}`,
								children: row.rank.label
							})] }),
							/* @__PURE__ */ jsx("strong", { children: row.rating })
						] }, row.user_id)) : /* @__PURE__ */ jsx("p", { children: "The first completed battle earns a place here." })]
					})]
				}),
				/* @__PURE__ */ jsxs("section", {
					className: "battle-spotlight",
					id: "battle-rankings",
					children: [/* @__PURE__ */ jsxs("div", { children: [
						/* @__PURE__ */ jsx("small", { children: "ARENA SPOTLIGHT" }),
						/* @__PURE__ */ jsx("h2", { children: spotlight ? `${spotlight.challenger_name} vs ${spotlight.opponent_name}` : "The next great battle starts with you." }),
						/* @__PURE__ */ jsx("p", { children: spotlight ? "The latest completed head-to-head round in the Mentics arena." : "Enter the arena to set the first battle on the board." })
					] }), /* @__PURE__ */ jsx("div", { children: spotlight ? /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx("strong", { children: spotlight.winner_id ? "WINNER DECIDED" : "DRAW" }), /* @__PURE__ */ jsx("span", { children: "Latest completed battle" })] }) : /* @__PURE__ */ jsxs(Fragment, { children: [/* @__PURE__ */ jsx("strong", { children: "OPEN" }), /* @__PURE__ */ jsx("span", { children: "Matchmaking is ready" })] }) })]
				})
			]
		})
	});
}
//#endregion
export { ARENA_AVATAR_PALETTES as a, BattleArena as default, ARENA_AVATAR_HAIR as i, ARENA_AVATAR_ACCENTS as n, ARENA_AVATAR_SKINS as o, ARENA_AVATAR_EYES as r, normalizeArenaAvatar as s, arena_page_exports as t, winStreakTier };
