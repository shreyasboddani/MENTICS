// The Arena fighter is drawn as one inline SVG on a fixed 200x300 viewBox.
//
// It used to be ~30 absolutely positioned <div>s shaped with border-radius and
// clip-path. That could not survive being scaled: the lobby renders the figure
// at full size, the duel at 72%, and the scoreboard at 48%, and every one of
// those transforms re-snapped pixel-tuned offsets, so limbs separated from the
// torso and every clip-path edge aliased into a jagged blob. One viewBox scales
// exactly, and vector joints stay welded at any size.
//
// Everything is authored in viewBox units around a real skeleton -- cranium,
// jaw, neck, shoulder line, waist, hip, knee, ankle. Keeping those landmarks
// consistent is what makes the parts read as one person instead of a stack of
// shapes, and it is what lets 20 independent cosmetic fields combine without
// any particular pairing falling apart.

import { memo, useMemo, useState } from 'react'
import { Check, Dices, RotateCcw, Sparkles, X } from 'lucide-react'

// A single dark ink colour on every silhouette is what separates drawn
// character art from a pile of flat coloured shapes. Limbs are stroked paths,
// so they get their outline by being drawn twice: thick in ink, then thinner in
// their own colour on top.
// One light, from the upper left, for every part of the figure. Shading only
// reads as form when it agrees with itself: a highlight on the left of the head
// and a highlight on the right of the arm cancel each other out and the result
// looks flat no matter how many gradients are involved.
const LIGHT_SHIFT = 'translate(-1.4 -1)'

const INK = '#161a33'
const INK_WEIGHT = 2.6
const LIMB_INK = 3.4

// --- Cosmetic catalog ------------------------------------------------------
// One source of truth: the renderer, the customizer UI, and the server-side
// allow-list in app.py all describe the same fields and values.

export const ARENA_AVATAR_PALETTES = {
  nova: ['#8b5cf6', '#4f46e5', '#f1eaff'],
  solar: ['#ffb340', '#e95d43', '#fff1c7'],
  glacier: ['#48d8ff', '#3974e8', '#e2fbff'],
  volt: ['#b5f33d', '#31a878', '#efffc6'],
  rose: ['#ff6fae', '#ad3f83', '#ffe0ef'],
  midnight: ['#5468ff', '#161c5a', '#b9c4ff'],
  ember: ['#ff7a45', '#8c2020', '#ffd9c2'],
  forest: ['#4fbf7d', '#1c5b3f', '#d6f7e2'],
  mono: ['#9aa3c4', '#3a4064', '#e9ecf8'],
  tide: ['#2fd3c0', '#1a5f8c', '#d3fbf6'],
  crimson: ['#ff5c72', '#7a1230', '#ffd6dd'],
  jade: ['#3ee08f', '#0f6b52', '#ccfbe6'],
  royal: ['#7b8cff', '#2c2a8f', '#dfe3ff'],
  dune: ['#e8c37a', '#9c6a2f', '#fff2d6'],
  orchid: ['#c77dff', '#5b1e91', '#f3e2ff'],
  steel: ['#7d93b8', '#2b3552', '#e6edf8'],
}

// [base, shadow, highlight] per tone, colour-matched so the shading on a face
// reads as the same skin rather than a grey wash laid over it.
export const ARENA_AVATAR_SKINS = {
  porcelain: ['#f7d7c4', '#d9a184', '#fff1e6'],
  light: ['#eec3a3', '#c9906d', '#fbe0cb'],
  sand: ['#e6bd94', '#bc8659', '#f7dcbd'],
  warm: ['#e0a578', '#b3754c', '#f4c9a4'],
  amber: ['#d69a63', '#a56a3c', '#eec096'],
  medium: ['#c98f68', '#9a6242', '#e3b591'],
  olive: ['#ac7b52', '#7d5334', '#c99c74'],
  bronze: ['#a06f45', '#6f4728', '#c1935f'],
  deep: ['#8d5b3d', '#5f3826', '#ab7a58'],
  mocha: ['#7a4f36', '#4e2e20', '#996b4e'],
  umber: ['#6b452f', '#43281c', '#8a6047'],
  ebony: ['#4c3227', '#2b1a15', '#6c4a3b'],
}

export const ARENA_AVATAR_HAIR = {
  onyx: '#1b1a26', espresso: '#3a241e', chestnut: '#713f2b', copper: '#b95732',
  gold: '#e5b956', silver: '#c8d0df', white: '#f2f4fb', violet: '#6f4ad8',
  blue: '#2769bd', teal: '#22a89b', emerald: '#2f9455', crimson: '#b32744',
  pink: '#ef78bb', sunset: '#f2803f', ash: '#8b8fa6', sage: '#7fa87c',
  ember: '#e2542a', ice: '#a9dcf5', plum: '#7a3f78', honey: '#d9a441',
}

export const ARENA_AVATAR_ACCENTS = {
  crystal: '#a8edff', gold: '#ffd66d', rose: '#ff9cc8', teal: '#67f0cf',
  white: '#f8fbff', graphite: '#5b638a', violet: '#c3a2ff', lime: '#d2fb63',
  copper: '#ff9f68', obsidian: '#2a2e4a', ice: '#cfeeff', ember: '#ff7d4d',
  jade: '#6ff0a8', blush: '#ffc2d6', chrome: '#dfe6f5', bronze: '#c78a4e',
}

export const ARENA_AVATAR_EYES = {
  brown: '#5a3620', hazel: '#8a6a2f', green: '#2f7a52', blue: '#2f6bab',
  amber: '#b57a1e', violet: '#7248b8', grey: '#5d6780', crimson: '#9c2b3d',
  gold: '#c9962a', teal: '#22867f', silver: '#8d9bb5', rose: '#b8536e',
}

// Every customizable field, in the order the locker presents it. `swatch` names
// the palette a value's colour chip is drawn from, when it has one.
export const ARENA_CUSTOMIZER_SECTIONS = [
  ['body', 'Body', [
    ['frame', 'Silhouette', [['masculine', 'Masculine'], ['feminine', 'Feminine'], ['androgynous', 'Androgynous'], ['athletic', 'Athletic']]],
    ['body', 'Build', [['striker', 'Striker'], ['sentinel', 'Sentinel'], ['scout', 'Scout'], ['titan', 'Titan'], ['lithe', 'Lithe'], ['compact', 'Compact']]],
    ['height', 'Height', [['short', 'Short'], ['average', 'Average'], ['tall', 'Tall']]],
    ['skin', 'Skin tone', [['porcelain', 'Porcelain'], ['light', 'Light'], ['sand', 'Sand'], ['warm', 'Warm'], ['amber', 'Amber'], ['medium', 'Medium'], ['olive', 'Olive'], ['bronze', 'Bronze'], ['deep', 'Deep'], ['mocha', 'Mocha'], ['umber', 'Umber'], ['ebony', 'Ebony']], 'skin'],
    ['pose', 'Stance', [['ready', 'Ready'], ['guard', 'Guard'], ['confident', 'Confident'], ['relaxed', 'Relaxed']]],
  ]],
  ['face', 'Face', [
    ['eyes', 'Eye color', [['brown', 'Brown'], ['hazel', 'Hazel'], ['green', 'Green'], ['blue', 'Blue'], ['amber', 'Amber'], ['violet', 'Violet'], ['grey', 'Grey'], ['crimson', 'Crimson'], ['gold', 'Gold'], ['teal', 'Teal'], ['silver', 'Silver'], ['rose', 'Rose']], 'eyes'],
    ['brows', 'Eyebrows', [['soft', 'Soft'], ['bold', 'Bold'], ['arched', 'Arched'], ['sharp', 'Sharp']]],
    ['expression', 'Expression', [['calm', 'Calm'], ['focused', 'Focused'], ['fierce', 'Fierce'], ['grin', 'Grin']]],
    ['face', 'Face detail', [['natural', 'None'], ['freckles', 'Freckles'], ['liner', 'Liner'], ['warpaint', 'War paint'], ['blush', 'Blush'], ['scar', 'Scar'], ['cyber', 'Cyber lines'], ['tattoo', 'Tattoo']]],
    ['facial_hair', 'Facial hair', [['none', 'None'], ['stubble', 'Stubble'], ['mustache', 'Mustache'], ['goatee', 'Goatee'], ['full', 'Full beard']]],
  ]],
  ['hair', 'Hair', [
    ['hair', 'Style', [['crop', 'Crop'], ['fade', 'Fade'], ['buzz', 'Buzz'], ['wave', 'Wave'], ['spike', 'Spike'], ['mohawk', 'Mohawk'], ['undercut', 'Undercut'], ['pixie', 'Pixie'], ['bob', 'Bob'], ['ponytail', 'Ponytail'], ['twin_tails', 'Twin tails'], ['curls', 'Curls'], ['afro', 'Afro'], ['locs', 'Locs'], ['braids', 'Braids'], ['long', 'Long'], ['flow', 'Flow'], ['bun', 'Bun']]],
    ['hair_color', 'Color', [['onyx', 'Onyx'], ['espresso', 'Espresso'], ['chestnut', 'Chestnut'], ['copper', 'Copper'], ['gold', 'Gold'], ['silver', 'Silver'], ['white', 'White'], ['violet', 'Violet'], ['blue', 'Blue'], ['teal', 'Teal'], ['emerald', 'Emerald'], ['crimson', 'Crimson'], ['pink', 'Pink'], ['sunset', 'Sunset'], ['ash', 'Ash'], ['sage', 'Sage'], ['ember', 'Ember'], ['ice', 'Ice'], ['plum', 'Plum'], ['honey', 'Honey']], 'hair'],
  ]],
  ['outfit', 'Outfit', [
    ['outfit', 'Top / armor', [['combat', 'Combat'], ['academy', 'Academy'], ['varsity', 'Varsity'], ['techwear', 'Techwear'], ['street', 'Street'], ['champion', 'Champion'], ['hoodie', 'Hoodie'], ['jersey', 'Jersey'], ['flight', 'Flight suit'], ['scholar', 'Scholar robe']]],
    ['palette', 'Main color', [['nova', 'Nova'], ['solar', 'Solar'], ['glacier', 'Glacier'], ['volt', 'Volt'], ['rose', 'Rose'], ['midnight', 'Midnight'], ['ember', 'Ember'], ['forest', 'Forest'], ['mono', 'Mono'], ['tide', 'Tide'], ['crimson', 'Crimson'], ['jade', 'Jade'], ['royal', 'Royal'], ['dune', 'Dune'], ['orchid', 'Orchid'], ['steel', 'Steel']], 'palette'],
    ['accent', 'Trim color', [['crystal', 'Crystal'], ['gold', 'Gold'], ['rose', 'Rose'], ['teal', 'Teal'], ['white', 'White'], ['graphite', 'Graphite'], ['violet', 'Violet'], ['lime', 'Lime'], ['copper', 'Copper'], ['obsidian', 'Obsidian'], ['ice', 'Ice'], ['ember', 'Ember'], ['jade', 'Jade'], ['blush', 'Blush'], ['chrome', 'Chrome'], ['bronze', 'Bronze']], 'accent'],
    ['marking', 'Suit pattern', [['none', 'None'], ['stripes', 'Racing stripes'], ['circuit', 'Circuitry'], ['chevron', 'Chevrons'], ['stars', 'Stars'], ['scales', 'Scales']]],
    ['bottom', 'Bottom', [['tactical', 'Tactical'], ['fitted', 'Fitted'], ['cargo', 'Cargo'], ['battle_skirt', 'Battle skirt'], ['shorts', 'Shorts'], ['pleated', 'Pleated'], ['joggers', 'Joggers']]],
    ['gloves', 'Hands', [['tech', 'Tech gloves'], ['fingerless', 'Fingerless'], ['gauntlets', 'Gauntlets'], ['wraps', 'Wraps'], ['claws', 'Claws'], ['none', 'Bare']]],
    ['footwear', 'Footwear', [['boots', 'Combat boots'], ['high_tops', 'High-tops'], ['runners', 'Runners'], ['armored', 'Armored'], ['low_tops', 'Low-tops'], ['greaves', 'Greaves'], ['barefoot', 'Barefoot']]],
  ]],
  ['gear', 'Gear', [
    ['shoulder', 'Shoulders', [['none', 'None'], ['pauldrons', 'Pauldrons'], ['epaulettes', 'Epaulettes'], ['spikes', 'Spikes'], ['sash', 'Sash']]],
    ['waist', 'Waist gear', [['none', 'None'], ['pouch', 'Pouch'], ['wrap', 'Hip wrap'], ['chain', 'Chain'], ['holsters', 'Holsters']]],
    ['gear', 'Head gear', [['visor', 'Visor'], ['comms', 'Comms'], ['crown', 'Crown'], ['glasses', 'Glasses'], ['shades', 'Shades'], ['headband', 'Headband'], ['earrings', 'Earrings'], ['mask', 'Mask'], ['cap', 'Cap'], ['helmet', 'Helmet'], ['none', 'None']]],
    ['back', 'Back gear', [['none', 'None'], ['cape', 'Cape'], ['half_cape', 'Half cape'], ['energy_pack', 'Energy pack'], ['banner', 'Rank banner'], ['wings', 'Wings'], ['quiver', 'Quiver'], ['jetpack', 'Jetpack']]],
    ['emblem', 'Chest emblem', [['bolt', 'Bolt'], ['mind', 'Mind'], ['target', 'Target'], ['shield', 'Shield'], ['star', 'Star'], ['flame', 'Flame'], ['crown', 'Crown'], ['atom', 'Atom'], ['book', 'Book'], ['wave', 'Wave']]],
    ['aura', 'Power aura', [['pulse', 'Pulse'], ['flare', 'Flare'], ['orbit', 'Orbit'], ['spark', 'Spark'], ['halo', 'Halo'], ['embers', 'Embers'], ['frost', 'Frost'], ['storm', 'Storm'], ['none', 'None']]],
  ]],
]

export const ARENA_AVATAR_FIELDS = ARENA_CUSTOMIZER_SECTIONS.flatMap(([, , groups]) => groups)

export const ARENA_AVATAR_OPTIONS = Object.fromEntries(
  ARENA_AVATAR_FIELDS.map(([key, , choices]) => [key, choices.map(([value]) => value)]))

export const ARENA_AVATAR_DEFAULT = {
  frame: 'masculine', body: 'striker', height: 'average', skin: 'medium', pose: 'ready',
  eyes: 'brown', brows: 'soft', expression: 'calm', face: 'natural', facial_hair: 'none',
  hair: 'crop', hair_color: 'onyx',
  outfit: 'combat', palette: 'nova', accent: 'crystal', marking: 'none', bottom: 'tactical',
  gloves: 'tech', footwear: 'boots',
  shoulder: 'none', waist: 'none', gear: 'visor', back: 'none', emblem: 'bolt', aura: 'pulse',
}

const SWATCH_SOURCES = {
  palette: value => ARENA_AVATAR_PALETTES[value]?.[0],
  skin: value => ARENA_AVATAR_SKINS[value]?.[0],
  hair: value => ARENA_AVATAR_HAIR[value],
  accent: value => ARENA_AVATAR_ACCENTS[value],
  eyes: value => ARENA_AVATAR_EYES[value],
}

export function normalizeArenaAvatar(avatar) {
  const source = avatar && typeof avatar === 'object' ? avatar : {}
  return Object.fromEntries(Object.entries(ARENA_AVATAR_DEFAULT).map(([key, fallback]) =>
    [key, ARENA_AVATAR_OPTIONS[key].includes(source[key]) ? source[key] : fallback]))
}

export function randomArenaAvatar() {
  const pick = list => list[Math.floor(Math.random() * list.length)]
  return Object.fromEntries(Object.keys(ARENA_AVATAR_DEFAULT).map(key => [key, pick(ARENA_AVATAR_OPTIONS[key])]))
}

// --- Anatomy ---------------------------------------------------------------

// Half-widths at each landmark plus limb thickness, so "Titan" reads as a
// heavier person and "Lithe" as a lighter one rather than the same body with a
// wider rectangle pasted on.
const BUILDS = {
  striker: { shoulder: 34, chest: 31, waist: 23, hip: 26, arm: 10.5, thigh: 15, calf: 11.5, neck: 8.5 },
  sentinel: { shoulder: 41, chest: 38, waist: 29, hip: 31, arm: 13.5, thigh: 18, calf: 13.5, neck: 10.5 },
  scout: { shoulder: 28, chest: 26, waist: 19, hip: 22, arm: 8.5, thigh: 12.5, calf: 9.5, neck: 7.4 },
  titan: { shoulder: 46, chest: 43, waist: 35, hip: 36, arm: 16, thigh: 21, calf: 15.5, neck: 12 },
  lithe: { shoulder: 26, chest: 24, waist: 18, hip: 21, arm: 8, thigh: 11.5, calf: 9, neck: 7 },
  compact: { shoulder: 36, chest: 34, waist: 28, hip: 29, arm: 12, thigh: 17, calf: 13, neck: 9.5 },
}

// Silhouette shaping layered on top of the build: torso taper, head shape, jaw.
const FRAMES = {
  masculine: { shoulder: 1.07, waist: 1.06, hip: 0.92, headW: 1, jaw: 1.06, chinY: 0 },
  feminine: { shoulder: 0.88, waist: 0.82, hip: 1.08, headW: 0.95, jaw: 0.87, chinY: -1 },
  androgynous: { shoulder: 0.98, waist: 0.94, hip: 1, headW: 0.98, jaw: 0.97, chinY: 0 },
  athletic: { shoulder: 1.14, waist: 0.86, hip: 0.97, headW: 0.96, jaw: 1.01, chinY: 0 },
}

// Stance moves the elbow out and the wrist in or down. Keeping it to two
// numbers means every build, outfit and glove keeps working in every pose.
const POSES = {
  ready: { elbow: 0.62, wrist: 0.98, drop: 20 },
  guard: { elbow: 1.15, wrist: 0.74, drop: 2 },
  confident: { elbow: 1.35, wrist: 0.58, drop: 10 },
  relaxed: { elbow: 0.34, wrist: 1.06, drop: 26 },
}

const HEIGHTS = {
  short: { leg: 0.87, head: 1.09 },
  average: { leg: 1, head: 1 },
  tall: { leg: 1.13, head: 0.93 },
}

/** Landmarks for one height, always standing on the same ground line. */
function buildSkeleton(height) {
  const h = HEIGHTS[height] || HEIGHTS.average
  const hip = 138
  const ankle = hip + 112 * h.leg
  const shift = 268 - (ankle + 8)
  return {
    headTop: 20 + shift, chin: 66 + shift, neck: 72 + shift, shoulder: 82 + shift,
    chest: 100 + shift, waist: 124 + shift, hip: hip + shift,
    knee: hip + 58 * h.leg + shift, ankle: ankle + shift, ground: 268,
    centerX: 100, headScale: h.head,
  }
}

const EMBLEM_PATHS = {
  bolt: { d: 'M1.6 -6.4 L-3.6 0.4 L-0.5 0.4 L-1.7 6.4 L3.6 -0.7 L0.5 -0.7 Z', fill: true },
  mind: { d: 'M-4.6 -2.6 A3.1 3.1 0 0 1 0 -5.6 A3.1 3.1 0 0 1 4.6 -2.6 A3.2 3.2 0 0 1 4.2 3 A3.5 3.5 0 0 1 0 5.7 A3.5 3.5 0 0 1 -4.2 3 A3.2 3.2 0 0 1 -4.6 -2.6 Z M0 -5.6 L0 5.7 M-3 -1 L3 -1 M-2.6 2.3 L2.6 2.3' },
  target: { d: 'M0 -6.2 A6.2 6.2 0 1 1 -0.1 -6.2 Z M0 -2.7 A2.7 2.7 0 1 1 -0.1 -2.7 Z' },
  shield: { d: 'M0 -6.4 L5.5 -3.9 L5.5 1 Q5.5 4.7 0 6.5 Q-5.5 4.7 -5.5 1 L-5.5 -3.9 Z', fill: true },
  star: { d: 'M0 -6.6 L1.9 -2 L6.6 -1.8 L2.9 1.3 L4.1 6 L0 3.3 L-4.1 6 L-2.9 1.3 L-6.6 -1.8 L-1.9 -2 Z', fill: true },
  flame: { d: 'M0 -6.8 Q3 -2.8 2.7 -0.4 Q2.5 1.5 1 1.7 Q1.9 -0.8 0 -2.9 Q-1 -0.6 -2.5 0.6 Q-3.5 2.7 -1.8 4.7 Q-0.6 6.1 0 6.6 Q3.7 5.3 4.1 1.6 Q4.5 -2 0 -6.8 Z', fill: true },
  crown: { d: 'M-6.2 3.9 L-6.2 -4.6 L-3.1 -0.6 L0 -5.6 L3.1 -0.6 L6.2 -4.6 L6.2 3.9 Z', fill: true },
  atom: { d: 'M-1.8 0 A1.8 1.8 0 1 1 1.8 0 A1.8 1.8 0 1 1 -1.8 0 '
    + 'M-6.4 0 A6.4 2.6 0 1 1 6.4 0 A6.4 2.6 0 1 1 -6.4 0 '
    + 'M-3.2 -5.54 A6.4 2.6 60 1 1 3.2 5.54 A6.4 2.6 60 1 1 -3.2 -5.54 '
    + 'M-3.2 5.54 A6.4 2.6 -60 1 1 3.2 -5.54 A6.4 2.6 -60 1 1 -3.2 5.54' },
  book: { d: 'M-5.8 -4.6 Q-2.8 -6 0 -4.4 Q2.8 -6 5.8 -4.6 L5.8 4.6 Q2.8 3.2 0 4.8 Q-2.8 3.2 -5.8 4.6 Z M0 -4.4 L0 4.8' },
  wave: { d: 'M-6.2 1.4 Q-4.2 -2.2 -2.1 1.4 Q0 5 2.1 1.4 Q4.2 -2.2 6.2 1.4 M-6.2 -3.2 Q-4.2 -6.8 -2.1 -3.2 Q0 0.4 2.1 -3.2 Q4.2 -6.8 6.2 -3.2' },
}

// --- Hair ------------------------------------------------------------------

// Hair sits on a real skull, so every style is measured from the same three
// landmarks rather than from numbers guessed per style:
//
//   the crown  ~ head.top - h*0.04   (the cranium arc peaks just above `top`)
//   the temple ~ head.top + h*0.34   (the widest point of the head)
//   the brow   ~ head.top + h*0.40
//
// The hairline must land between the crown and the brow. Earlier versions put
// it at h*0.15, which is above the forehead entirely, so almost every short
// style rendered as a thin cap floating over a bald head.
const HAIRLINE = 0.27
const TEMPLE = 0.52

/** A skull-hugging cap. `grow` puffs it out, `line` moves the fringe down. */
function hairCap(head, { grow = 0, line = HAIRLINE, temple = TEMPLE } = {}) {
  const { cx, top, w, h } = head
  const l = cx - w - grow
  const r = cx + w + grow
  const crown = top - h * 0.06 - grow
  return `M${l} ${top + h * temple}
          C${l} ${crown} ${cx - w * 0.55} ${crown - 2} ${cx} ${crown - 2}
          C${cx + w * 0.55} ${crown - 2} ${r} ${crown} ${r} ${top + h * temple}
          C${cx + w * 0.72} ${top + h * (line + 0.06)} ${cx + w * 0.34} ${top + h * line} ${cx} ${top + h * line}
          C${cx - w * 0.34} ${top + h * line} ${cx - w * 0.72} ${top + h * (line + 0.06)} ${l} ${top + h * temple} Z`
}

/** Front hair: the cap on the skull plus the style's own silhouette. */
function hairFront(style, head) {
  const { cx, top, w, h } = head
  const l = cx - w
  const r = cx + w
  switch (style) {
    case 'buzz':
      return hairCap(head, { grow: -1.5, line: 0.2, temple: 0.4 })
    case 'fade':
      return hairCap(head, { grow: -1, line: 0.24, temple: 0.42 })
    case 'undercut':
      return hairCap(head, { grow: 1.5, line: 0.24, temple: 0.3 })
    case 'wave':
      return `M${l - 2} ${top + h * 0.56} C${l - 3} ${top - h * 0.14} ${cx - w * 0.5} ${top - h * 0.16} ${cx} ${top - h * 0.16}
              C${cx + w * 0.6} ${top - h * 0.16} ${r + 3} ${top - h * 0.12} ${r + 2} ${top + h * 0.5}
              C${cx + w * 0.7} ${top + h * 0.2} ${cx + w * 0.3} ${top + h * 0.34} ${cx - w * 0.06} ${top + h * 0.26}
              C${cx - w * 0.4} ${top + h * 0.2} ${cx - w * 0.7} ${top + h * 0.34} ${l - 2} ${top + h * 0.56} Z`
    case 'spike':
      return `M${l - 2} ${top + h * 0.5} L${l - 1} ${top - h * 0.18} L${cx - w * 0.46} ${top + h * 0.06}
              L${cx - w * 0.22} ${top - h * 0.3} L${cx + w * 0.02} ${top + h * 0.04}
              L${cx + w * 0.26} ${top - h * 0.32} L${cx + w * 0.5} ${top + h * 0.05}
              L${r + 1} ${top - h * 0.16} L${r + 2} ${top + h * 0.5}
              C${cx + w * 0.7} ${top + h * 0.22} ${cx - w * 0.7} ${top + h * 0.22} ${l - 2} ${top + h * 0.5} Z`
    case 'mohawk':
      return `M${cx - w * 0.34} ${top + h * 0.42} L${cx - w * 0.3} ${top - h * 0.34}
              C${cx - w * 0.1} ${top - h * 0.46} ${cx + w * 0.16} ${top - h * 0.44} ${cx + w * 0.32} ${top - h * 0.26}
              L${cx + w * 0.34} ${top + h * 0.42}
              C${cx + w * 0.1} ${top + h * 0.3} ${cx - w * 0.1} ${top + h * 0.3} ${cx - w * 0.34} ${top + h * 0.42} Z`
    case 'pixie':
      return `M${l - 3} ${top + h * 0.5} C${l - 4} ${top - h * 0.12} ${cx - w * 0.5} ${top - h * 0.14} ${cx} ${top - h * 0.14}
              C${cx + w * 0.6} ${top - h * 0.14} ${r + 4} ${top - h * 0.1} ${r + 3} ${top + h * 0.34}
              L${r + 6} ${top + h * 0.6} C${cx + w * 0.8} ${top + h * 0.3} ${cx + w * 0.3} ${top + h * 0.3} ${cx} ${top + h * 0.24}
              C${cx - w * 0.5} ${top + h * 0.18} ${l - 1} ${top + h * 0.3} ${l - 3} ${top + h * 0.5} Z`
    case 'bob':
      return `M${l - 5} ${top + h * 1.02} C${l - 6} ${top - h * 0.12} ${cx - w * 0.5} ${top - h * 0.14} ${cx} ${top - h * 0.14}
              C${cx + w * 0.6} ${top - h * 0.14} ${r + 6} ${top - h * 0.1} ${r + 5} ${top + h * 1.02}
              C${r + 2} ${top + h * 0.5} ${cx + w * 0.86} ${top + h * 0.3} ${cx + w * 0.2} ${top + h * 0.28}
              C${cx - w * 0.4} ${top + h * 0.26} ${l + 1} ${top + h * 0.32} ${l - 5} ${top + h * 1.02} Z`
    case 'curls':
      return hairCap(head, { grow: 5, line: 0.27, temple: 0.62 })
    case 'afro':
      return hairCap(head, { grow: 2, line: 0.27, temple: 0.5 })
    case 'locs':
      return hairCap(head, { grow: 2, line: 0.26, temple: 0.5 })
    case 'braids':
      return hairCap(head, { grow: 0.5, line: 0.25, temple: 0.48 })
    case 'long':
    case 'flow':
      return `M${l - 4} ${top + h * 0.72} C${l - 5} ${top - h * 0.13} ${cx - w * 0.5} ${top - h * 0.15} ${cx} ${top - h * 0.15}
              C${cx + w * 0.6} ${top - h * 0.15} ${r + 5} ${top - h * 0.11} ${r + 4} ${top + h * 0.68}
              C${r + 1} ${top + h * 0.36} ${cx + w * 0.7} ${top + h * 0.26} ${cx + w * 0.18} ${top + h * 0.3}
              C${cx - w * 0.3} ${top + h * 0.34} ${cx - w * 0.55} ${top + h * 0.2} ${cx - w * 0.75} ${top + h * 0.3}
              C${cx - w * 0.95} ${top + h * 0.4} ${l - 2} ${top + h * 0.44} ${l - 4} ${top + h * 0.72} Z`
    case 'ponytail':
    case 'twin_tails':
    case 'bun':
      return hairCap(head, { grow: 1, line: 0.26, temple: 0.5 })
    default: // crop
      return hairCap(head)
  }
}

/** Back hair: everything falling behind the head and shoulders. */
function hairBack(style, head, shoulderY) {
  const { cx, top, w, h } = head
  const bottom = top + h
  switch (style) {
    case 'bob':
      return [`M${cx - w - 6} ${top + h * 0.3} Q${cx - w - 8} ${bottom + 12} ${cx - w + 1} ${bottom + 14}
               L${cx + w - 1} ${bottom + 14} Q${cx + w + 8} ${bottom + 12} ${cx + w + 6} ${top + h * 0.3} Z`]
    case 'pixie':
      return [`M${cx - w - 3} ${top + h * 0.36} Q${cx - w - 5} ${bottom + 4} ${cx - w + 2} ${bottom + 6}
               L${cx + w - 2} ${bottom + 6} Q${cx + w + 5} ${bottom + 4} ${cx + w + 3} ${top + h * 0.36} Z`]
    case 'long':
      return [`M${cx - w - 5} ${top + h * 0.25} Q${cx - w - 12} ${shoulderY + 44} ${cx - w - 4} ${shoulderY + 58}
               Q${cx} ${shoulderY + 52} ${cx + w + 4} ${shoulderY + 58}
               Q${cx + w + 12} ${shoulderY + 44} ${cx + w + 5} ${top + h * 0.25} Z`]
    case 'flow':
      return [`M${cx - w - 6} ${top + h * 0.24} Q${cx - w - 20} ${shoulderY + 30} ${cx - w - 10} ${shoulderY + 50}
               Q${cx - w - 2} ${shoulderY + 38} ${cx} ${shoulderY + 44}
               Q${cx + w + 2} ${shoulderY + 38} ${cx + w + 10} ${shoulderY + 50}
               Q${cx + w + 20} ${shoulderY + 30} ${cx + w + 6} ${top + h * 0.24} Z`]
    case 'ponytail':
      return [`M${cx + w - 2} ${top + h * 0.22} Q${cx + w + 17} ${top + h * 0.5} ${cx + w + 14} ${bottom + 28}
               Q${cx + w + 10} ${bottom + 38} ${cx + w + 2} ${bottom + 31}
               Q${cx + w + 9} ${bottom + 6} ${cx + w - 4} ${top + h * 0.6} Z`]
    case 'twin_tails':
      return [
        `M${cx - w + 1} ${top + h * 0.28} Q${cx - w - 17} ${top + h * 0.6} ${cx - w - 13} ${bottom + 22}
         Q${cx - w - 8} ${bottom + 30} ${cx - w - 2} ${bottom + 22} Q${cx - w - 6} ${bottom} ${cx - w + 4} ${top + h * 0.62} Z`,
        `M${cx + w - 1} ${top + h * 0.28} Q${cx + w + 17} ${top + h * 0.6} ${cx + w + 13} ${bottom + 22}
         Q${cx + w + 8} ${bottom + 30} ${cx + w + 2} ${bottom + 22} Q${cx + w + 6} ${bottom} ${cx + w - 4} ${top + h * 0.62} Z`,
      ]
    case 'bun':
      return [`M${cx} ${top - h * 0.2} m-11 0 a11 11 0 1 0 22 0 a11 11 0 1 0 -22 0 Z`]
    case 'curls': {
      // A scalloped underside, walked right to left so the bumps close cleanly.
      const reach = w + 9
      const bumps = 5
      const step = (reach * 2) / bumps
      let edge = ''
      for (let i = 0; i < bumps; i += 1) edge += ` q${-step * 0.5} 11 ${-step} 0`
      return [`M${cx - reach} ${bottom + 2} L${cx - reach} ${top + h * 0.3}`
        + ` a${reach} ${reach * 0.86} 0 0 1 ${reach * 2} 0`
        + ` L${cx + reach} ${bottom + 2}${edge} Z`]
    }
    case 'afro': {
      const reach = w * 1.32
      const cy = top + h * 0.12
      return [`M${cx - reach} ${cy} a${reach} ${reach} 0 1 0 ${reach * 2} 0`
        + ` a${reach} ${reach} 0 1 0 ${-reach * 2} 0 Z`]
    }
    case 'locs':
      return [-2, -1, 0, 1, 2].map(i => {
        const x = cx + i * (w * 0.46)
        const foot = bottom + 24 + Math.abs(i) * -4
        return `M${x - 5.5} ${top + h * 0.3} L${x + 5.5} ${top + h * 0.3} L${x + 5.5} ${foot}`
          + ` a5.5 5.5 0 0 1 -11 0 Z`
      })
    case 'braids':
      return [
        `M${cx - w - 1} ${top + h * 0.5} Q${cx - w - 9} ${bottom + 18} ${cx - w - 5} ${bottom + 36}
         L${cx - w + 4} ${bottom + 35} Q${cx - w + 1} ${bottom + 14} ${cx - w + 6} ${top + h * 0.56} Z`,
        `M${cx + w + 1} ${top + h * 0.5} Q${cx + w + 9} ${bottom + 18} ${cx + w + 5} ${bottom + 36}
         L${cx + w - 4} ${bottom + 35} Q${cx + w - 1} ${bottom + 14} ${cx + w - 6} ${top + h * 0.56} Z`,
      ]
    default:
      return []
  }
}

// --- Face ------------------------------------------------------------------

const BROW_SHAPES = {
  soft: (x, y, s) => `M${x - 5 * s} ${y + 0.4} Q${x} ${y - 2.6} ${x + 5 * s} ${y - 0.2}`,
  bold: (x, y, s) => `M${x - 5.4 * s} ${y + 0.6} Q${x} ${y - 3} ${x + 5.4 * s} ${y}`,
  arched: (x, y, s) => `M${x - 5 * s} ${y + 1.6} Q${x - 0.6 * s} ${y - 4.4} ${x + 5 * s} ${y - 0.4}`,
  sharp: (x, y, s) => `M${x - 5.2 * s} ${y + 2} L${x + 1 * s} ${y - 2.8} L${x + 5.2 * s} ${y - 1.4}`,
}

function ArenaFace({ loadout, head, skin, accent, hairColor, eyeColor }) {
  const { cx, top, h, w } = head
  const hidden = ['visor', 'helmet'].includes(loadout.gear)
  const eyeY = top + h * 0.54
  // Every beard shape is measured off the jaw, not off the eye line.
  const jaw = top + h * 0.98
  const eyeDx = w * 0.44
  const browY = eyeY - h * 0.14
  const browWeight = loadout.brows === 'bold' ? 2.9 : loadout.brows === 'sharp' ? 2.2 : 2
  const fierce = loadout.expression === 'fierce'
  const focused = loadout.expression === 'focused'
  const grin = loadout.expression === 'grin'
  const lidDrop = fierce ? 1.5 : focused ? 1 : 0
  const mouth = grin
    ? `M${cx - 6} ${eyeY + 13.6} Q${cx} ${eyeY + 19.4} ${cx + 6} ${eyeY + 13.6} Q${cx} ${eyeY + 15.6} ${cx - 6} ${eyeY + 13.6} Z`
    : fierce
      ? `M${cx - 5.4} ${eyeY + 16} Q${cx} ${eyeY + 13} ${cx + 5.4} ${eyeY + 16}`
      : focused
        ? `M${cx - 4.6} ${eyeY + 14.8} L${cx + 4.6} ${eyeY + 14.8}`
        : `M${cx - 5.2} ${eyeY + 14.2} Q${cx} ${eyeY + 17.4} ${cx + 5.2} ${eyeY + 14.2}`

  return <g className="arena-fighter-face">
    {/* Ears sit on the skull line so head gear has something to rest against. */}
    <ellipse cx={cx - w} cy={eyeY + 2} rx={w * 0.13} ry={h * 0.13} fill={skin[1]} />
    <ellipse cx={cx + w} cy={eyeY + 2} rx={w * 0.13} ry={h * 0.13} fill={skin[1]} />
    {!hidden && <>
      {[-1, 1].map(side =>
        <path key={`brow${side}`}
          d={BROW_SHAPES[loadout.brows] ? BROW_SHAPES[loadout.brows](cx + side * eyeDx, browY + (fierce ? 1.6 : 0), side) : ''}
          stroke={hairColor} strokeWidth={browWeight} strokeLinecap="round" strokeLinejoin="round"
          fill="none" opacity=".92" />)}
      {[-1, 1].map(side => <g key={`eye${side}`}>
        {/* Almond eye, iris, pupil, catchlight -- the four parts that stop a
            face reading as two punched-out dots. */}
        <path d={`M${cx + side * eyeDx - 4.8} ${eyeY} Q${cx + side * eyeDx} ${eyeY - 3.5 + lidDrop} ${cx + side * eyeDx + 4.8} ${eyeY}
                  Q${cx + side * eyeDx} ${eyeY + 3.3} ${cx + side * eyeDx - 4.8} ${eyeY} Z`}
          fill="#fdfaff" stroke="#2a2036" strokeWidth=".7" />
        <circle cx={cx + side * eyeDx + side * 0.4} cy={eyeY + 0.2} r="2.2" fill={eyeColor} />
        <circle cx={cx + side * eyeDx + side * 0.4} cy={eyeY + 0.2} r="1" fill="#150f21" />
        <circle cx={cx + side * eyeDx + side * 0.4 - 0.9} cy={eyeY - 0.8} r=".6" fill="#fff" opacity=".95" />
      </g>)}
      <path d={`M${cx - 1.6} ${eyeY + 5} Q${cx - 2.5} ${eyeY + 9.6} ${cx + 1.4} ${eyeY + 9.8}`}
        stroke={skin[1]} strokeWidth="1.6" strokeLinecap="round" fill="none" />
    </>}

    {/* Facial hair hugs the jaw and stops below the cheekbone. The old shape
        began at eye level and ran the full width of the head, so with any long
        style the hair and the beard met at the temples and framed the face in
        solid black -- a balaclava, not a beard. It also sits under the mouth
        rather than over it, which is why the mouth is drawn after this. */}
    {loadout.facial_hair !== 'none' && !hidden && <g fill={hairColor}>
      {loadout.facial_hair === 'full' &&
        <path d={`M${cx - w * 0.84} ${eyeY + 7}
                  C${cx - w * 0.86} ${jaw - 6} ${cx - w * 0.5} ${jaw + 3} ${cx} ${jaw + 4}
                  C${cx + w * 0.5} ${jaw + 3} ${cx + w * 0.86} ${jaw - 6} ${cx + w * 0.84} ${eyeY + 7}
                  C${cx + w * 0.5} ${eyeY + 13} ${cx + w * 0.2} ${eyeY + 11} ${cx} ${eyeY + 11}
                  C${cx - w * 0.2} ${eyeY + 11} ${cx - w * 0.5} ${eyeY + 13} ${cx - w * 0.84} ${eyeY + 7} Z`} />}
      {loadout.facial_hair === 'goatee' &&
        <path d={`M${cx - w * 0.34} ${eyeY + 12.5}
                  C${cx - w * 0.36} ${jaw - 5} ${cx - w * 0.22} ${jaw + 2} ${cx} ${jaw + 2.5}
                  C${cx + w * 0.22} ${jaw + 2} ${cx + w * 0.36} ${jaw - 5} ${cx + w * 0.34} ${eyeY + 12.5}
                  C${cx + w * 0.16} ${eyeY + 15} ${cx - w * 0.16} ${eyeY + 15} ${cx - w * 0.34} ${eyeY + 12.5} Z`} />}
      {loadout.facial_hair === 'stubble' &&
        <path d={`M${cx - w * 0.82} ${eyeY + 8}
                  C${cx - w * 0.84} ${jaw - 6} ${cx - w * 0.5} ${jaw + 2} ${cx} ${jaw + 3}
                  C${cx + w * 0.5} ${jaw + 2} ${cx + w * 0.84} ${jaw - 6} ${cx + w * 0.82} ${eyeY + 8}
                  C${cx + w * 0.5} ${eyeY + 14} ${cx - w * 0.5} ${eyeY + 14} ${cx - w * 0.82} ${eyeY + 8} Z`}
          opacity=".26" />}
      {['mustache', 'goatee', 'full'].includes(loadout.facial_hair) &&
        <path d={`M${cx - w * 0.36} ${eyeY + 11.6} C${cx - w * 0.2} ${eyeY + 8.2} ${cx + w * 0.2} ${eyeY + 8.2} ${cx + w * 0.36} ${eyeY + 11.6}
                  C${cx + w * 0.18} ${eyeY + 12.8} ${cx - w * 0.18} ${eyeY + 12.8} ${cx - w * 0.36} ${eyeY + 11.6} Z`} />}
    </g>}
    {/* Painted last, so a beard can never swallow the mouth. */}
    {!hidden && <path d={mouth} stroke="#8d4d54" strokeWidth={grin ? 1 : 1.8} strokeLinecap="round"
      fill={grin ? '#8d4d54' : 'none'} />}

    {loadout.face === 'freckles' && !hidden && [-1, 1].flatMap(side => [0, 1, 2].map(i =>
      <circle key={`f${side}-${i}`} cx={cx + side * (eyeDx + 1) + (i - 1) * 2.6} cy={eyeY + 6.4 + (i % 2) * 1.8}
        r=".7" fill={skin[1]} opacity=".8" />))}
    {loadout.face === 'liner' && !hidden && [-1, 1].map(side =>
      <path key={`l${side}`} d={`M${cx + side * (eyeDx + 4.8)} ${eyeY - 0.4} l${side * 3.6} ${-2.4}`}
        stroke="#241a33" strokeWidth="1.5" strokeLinecap="round" fill="none" />)}
    {loadout.face === 'warpaint' && [-1, 1].map(side =>
      <path key={`w${side}`} d={`M${cx + side * (w - 1)} ${eyeY - 1} L${cx + side * w * 0.2} ${eyeY - 2.6}
                                 L${cx + side * w * 0.2} ${eyeY + 3.8} L${cx + side * (w - 1)} ${eyeY + 4.6} Z`}
        fill={accent} opacity=".75" />)}
    {loadout.face === 'blush' && !hidden && [-1, 1].map(side =>
      <ellipse key={`b${side}`} cx={cx + side * (eyeDx + 3)} cy={eyeY + 6.6} rx="4.4" ry="2.6"
        fill="#f0748c" opacity=".3" />)}
    {loadout.face === 'scar' &&
      <path d={`M${cx + eyeDx + 1} ${eyeY - 8} L${cx + eyeDx - 2} ${eyeY + 7}`}
        stroke={skin[1]} strokeWidth="1.5" strokeLinecap="round" fill="none" opacity=".9" />}
    {loadout.face === 'cyber' && <g stroke={accent} strokeWidth="1.2" fill="none" opacity=".9">
      <path d={`M${cx + eyeDx + 5} ${eyeY - 5} L${cx + w - 1} ${eyeY - 5} L${cx + w - 1} ${eyeY + 4}`} />
      <circle cx={cx + eyeDx + 5} cy={eyeY - 5} r="1.4" fill={accent} stroke="none" />
      <path d={`M${cx - eyeDx - 5} ${eyeY + 7} L${cx - w + 1} ${eyeY + 7}`} />
    </g>}
    {loadout.face === 'tattoo' &&
      <path d={`M${cx - eyeDx - 3} ${eyeY - 7} q-4 5 0 10 q4 5 0 9`}
        stroke={accent} strokeWidth="1.6" strokeLinecap="round" fill="none" opacity=".85" />}
  </g>
}

// --- Gear ------------------------------------------------------------------

function ArenaHeadGear({ gear, head, colors, accent }) {
  const { cx, top, w, h } = head
  const eyeY = top + h * 0.54
  switch (gear) {
    case 'visor':
      return <g>
        <path d={`M${cx - w - 1} ${eyeY - 5} Q${cx} ${eyeY - 8.6} ${cx + w + 1} ${eyeY - 5}
                  L${cx + w + 1} ${eyeY + 3.6} Q${cx} ${eyeY + 7.8} ${cx - w - 1} ${eyeY + 3.6} Z`}
          fill={colors[1]} stroke={accent} strokeWidth="1.6" opacity=".95" />
        <path d={`M${cx - w + 2} ${eyeY - 3.4} Q${cx - w * 0.3} ${eyeY - 5} ${cx - w * 0.1} ${eyeY + 2.6}`}
          stroke="#ffffff" strokeWidth="1.8" strokeLinecap="round" fill="none" opacity=".45" />
      </g>
    case 'shades':
      return <g>
        <path d={`M${cx - w - 1} ${eyeY - 4.6} L${cx - 1.4} ${eyeY - 4.6} L${cx - 2.4} ${eyeY + 4.4}
                  Q${cx - w * 0.6} ${eyeY + 7.4} ${cx - w - 1} ${eyeY + 1.4} Z`} fill="#1d2033" />
        <path d={`M${cx + w + 1} ${eyeY - 4.6} L${cx + 1.4} ${eyeY - 4.6} L${cx + 2.4} ${eyeY + 4.4}
                  Q${cx + w * 0.6} ${eyeY + 7.4} ${cx + w + 1} ${eyeY + 1.4} Z`} fill="#1d2033" />
        <path d={`M${cx - 2} ${eyeY - 4} L${cx + 2} ${eyeY - 4}`} stroke={accent} strokeWidth="2" strokeLinecap="round" />
      </g>
    case 'comms':
      return <g fill="none" stroke={accent} strokeWidth="2.4" strokeLinecap="round">
        <path d={`M${cx - w - 2} ${eyeY - 1} a${w + 2} ${h * 0.5} 0 0 1 ${2 * w + 4} 0`} />
        <rect x={cx - w - 5} y={eyeY - 2} width="6" height="10" rx="3" fill={colors[0]} stroke={accent} />
        <rect x={cx + w - 1} y={eyeY - 2} width="6" height="10" rx="3" fill={colors[0]} stroke={accent} />
        <path d={`M${cx + w + 2} ${eyeY + 8} q-3 7 -9 8`} strokeWidth="1.6" />
      </g>
    case 'crown':
      return <g>
        <path d={`M${cx - w + 1} ${top + 2} L${cx - w + 1} ${top - 12} L${cx - w * 0.45} ${top - 3}
                  L${cx} ${top - 16} L${cx + w * 0.45} ${top - 3} L${cx + w - 1} ${top - 12}
                  L${cx + w - 1} ${top + 2} Z`}
          fill="#ffd45e" stroke="#c98a12" strokeWidth="1.4" strokeLinejoin="round" />
        <circle cx={cx} cy={top - 6.6} r="2.1" fill={accent} stroke="#c98a12" strokeWidth=".8" />
      </g>
    case 'glasses':
      return <g fill="none" stroke={accent} strokeWidth="1.8">
        <rect x={cx - w * 0.94} y={eyeY - 4.6} width={w * 0.74} height="9.4" rx="3.4" fill="#dff4ff" fillOpacity=".26" />
        <rect x={cx + w * 0.2} y={eyeY - 4.6} width={w * 0.74} height="9.4" rx="3.4" fill="#dff4ff" fillOpacity=".26" />
        <path d={`M${cx - w * 0.2} ${eyeY} L${cx + w * 0.2} ${eyeY}`} />
        <path d={`M${cx - w * 0.94} ${eyeY - 1.6} L${cx - w - 2} ${eyeY - 0.6}`} />
        <path d={`M${cx + w * 0.94} ${eyeY - 1.6} L${cx + w + 2} ${eyeY - 0.6}`} />
      </g>
    case 'headband':
      return <g>
        <path d={`M${cx - w - 1.5} ${top + h * 0.3} Q${cx} ${top + h * 0.18} ${cx + w + 1.5} ${top + h * 0.3}
                  L${cx + w + 1.5} ${top + h * 0.44} Q${cx} ${top + h * 0.32} ${cx - w - 1.5} ${top + h * 0.44} Z`}
          fill={accent} stroke="rgba(255,255,255,.45)" strokeWidth=".9" />
        <path d={`M${cx + w} ${top + h * 0.36} q10 4 12 15 q-6 -5 -8 -3 q3 5 1 9 q-4 -8 -7 -14 Z`} fill={accent} opacity=".9" />
      </g>
    case 'earrings':
      return <g fill="none" stroke={accent} strokeWidth="1.8">
        <circle cx={cx - w - 0.5} cy={eyeY + 8.6} r="3" />
        <circle cx={cx + w + 0.5} cy={eyeY + 8.6} r="3" />
      </g>
    case 'mask':
      return <g>
        <path d={`M${cx - w * 0.96} ${eyeY + 4} Q${cx} ${eyeY + 2} ${cx + w * 0.96} ${eyeY + 4}
                  Q${cx + w * 0.8} ${top + h + 5} ${cx} ${top + h + 7}
                  Q${cx - w * 0.8} ${top + h + 5} ${cx - w * 0.96} ${eyeY + 4} Z`}
          fill={colors[1]} stroke={accent} strokeWidth="1.4" />
        <path d={`M${cx - w * 0.5} ${eyeY + 10} L${cx + w * 0.5} ${eyeY + 10}`}
          stroke={accent} strokeWidth="1.2" opacity=".6" />
      </g>
    case 'cap':
      return <g>
        <path d={`M${cx - w - 1} ${top + h * 0.34} Q${cx - w - 1} ${top - 6} ${cx} ${top - 7}
                  Q${cx + w + 1} ${top - 6} ${cx + w + 1} ${top + h * 0.34} Z`}
          fill={colors[0]} stroke={colors[1]} strokeWidth="1.2" />
        <path d={`M${cx - 2} ${top + h * 0.3} L${cx + w + 16} ${top + h * 0.26} Q${cx + w + 19} ${top + h * 0.4} ${cx + w + 14} ${top + h * 0.46}
                  L${cx - 2} ${top + h * 0.44} Z`} fill={colors[1]} />
        <circle cx={cx} cy={top - 6} r="2.4" fill={accent} />
      </g>
    case 'helmet':
      return <g>
        <path d={`M${cx - w - 3} ${top + h * 0.72} Q${cx - w - 4} ${top - 7} ${cx} ${top - 8}
                  Q${cx + w + 4} ${top - 7} ${cx + w + 3} ${top + h * 0.72}
                  L${cx + w - 2} ${top + h * 0.72} L${cx + w - 2} ${eyeY - 5}
                  L${cx - w + 2} ${eyeY - 5} L${cx - w + 2} ${top + h * 0.72} Z`}
          fill={colors[0]} stroke={accent} strokeWidth="1.6" strokeLinejoin="round" />
        <path d={`M${cx - w + 2} ${eyeY - 5} L${cx + w - 2} ${eyeY - 5} L${cx + w - 2} ${eyeY + 4.6}
                  Q${cx} ${eyeY + 8} ${cx - w + 2} ${eyeY + 4.6} Z`} fill="#161a33" opacity=".92" />
        <path d={`M${cx} ${top - 8} L${cx} ${top + h * 0.3}`} stroke={accent} strokeWidth="2.4" />
        <path d={`M${cx - w + 4} ${eyeY} L${cx + w - 4} ${eyeY}`} stroke={accent} strokeWidth="1.4" opacity=".55" />
      </g>
    default:
      return null
  }
}

function ArenaBackGear({ back, colors, accent, build, S, uid }) {
  const { shoulder, hip } = build
  const { shoulder: sy, hip: hy, centerX: cx, knee, chest } = S
  switch (back) {
    case 'cape':
      return <path d={`M${cx - shoulder - 1} ${sy - 4} Q${cx - shoulder - 16} ${knee - 10} ${cx - hip - 12} ${knee + 8}
                       Q${cx - 8} ${knee - 2} ${cx} ${knee + 6} Q${cx + 8} ${knee - 2} ${cx + hip + 12} ${knee + 8}
                       Q${cx + shoulder + 16} ${knee - 10} ${cx + shoulder + 1} ${sy - 4} Z`}
        fill={`url(#${uid}-suit)`} stroke={accent} strokeWidth="1.2" strokeOpacity=".5" />
    case 'half_cape':
      return <path d={`M${cx + shoulder - 2} ${sy - 6} Q${cx + shoulder + 22} ${hy + 24} ${cx + hip + 16} ${knee - 4}
                       Q${cx + hip * 0.4} ${knee - 16} ${cx - 4} ${hy + 4} Z`}
        fill={`url(#${uid}-suit)`} stroke={accent} strokeWidth="1.3" strokeOpacity=".7" />
    case 'energy_pack':
      return <g>
        <rect x={cx - shoulder - 4} y={sy - 14} width={shoulder * 2 + 8} height="46" rx="12"
          fill={colors[1]} stroke={accent} strokeWidth="2.2" />
        <rect x={cx - 12} y={sy - 8} width="24" height="18" rx="6" fill={accent} opacity=".7" />
        <path d={`M${cx - shoulder - 12} ${sy + 4} l8 0 M${cx + shoulder + 4} ${sy + 4} l8 0`}
          stroke={accent} strokeWidth="4" strokeLinecap="round" />
      </g>
    case 'jetpack':
      return <g>
        {[-1, 1].map(side => <g key={side}>
          <rect x={cx + side * (shoulder + 2) - 9} y={sy - 12} width="18" height="46" rx="9"
            fill={colors[1]} stroke={accent} strokeWidth="1.8" />
          <path d={`M${cx + side * (shoulder + 2)} ${sy + 36} q-6 10 0 19 q6 -9 0 -19 Z`} fill={accent} opacity=".8" />
        </g>)}
      </g>
    case 'wings':
      return <g fill={`url(#${uid}-suit)`} stroke={accent} strokeWidth="1.3" strokeLinejoin="round" opacity=".92">
        {[-1, 1].map(side =>
          <path key={side} d={`M${cx + side * (shoulder - 4)} ${sy - 2}
                               Q${cx + side * (shoulder + 40)} ${sy - 28} ${cx + side * (shoulder + 48)} ${chest + 6}
                               Q${cx + side * (shoulder + 34)} ${chest + 2} ${cx + side * (shoulder + 32)} ${chest + 20}
                               Q${cx + side * (shoulder + 20)} ${chest + 10} ${cx + side * (shoulder + 16)} ${chest + 28}
                               Q${cx + side * (shoulder + 6)} ${chest + 12} ${cx + side * (shoulder - 4)} ${sy - 2} Z`} />)}
      </g>
    case 'quiver':
      return <g>
        <rect x={cx + shoulder - 2} y={sy - 8} width="16" height="52" rx="7"
          transform={`rotate(15 ${cx + shoulder + 6} ${sy + 18})`}
          fill={colors[1]} stroke={accent} strokeWidth="1.8" />
        {[-4, 0, 4].map(dx => <path key={dx}
          d={`M${cx + shoulder + 6 + dx} ${sy - 24} l2 15`} stroke={accent} strokeWidth="2" strokeLinecap="round" />)}
      </g>
    case 'banner':
      return <g>
        <rect x={cx + shoulder - 2} y={sy - 26} width="3.4" height={hy + 34 - sy + 26} rx="1.7" fill={accent} />
        <path d={`M${cx + shoulder + 1.4} ${sy - 22} L${cx + shoulder + 34} ${sy - 17} L${cx + shoulder + 30} ${sy + 20}
                  L${cx + shoulder + 16} ${sy + 13} L${cx + shoulder + 1.4} ${sy + 19} Z`}
          fill={`url(#${uid}-suit)`} stroke={accent} strokeWidth="1.2" />
        <text x={cx + shoulder + 16} y={sy - 1} textAnchor="middle" fontSize="15" fontWeight="900"
          fill={colors[2]} fontFamily="inherit">M</text>
      </g>
    default:
      return null
  }
}

/** Outfit detailing, drawn inside the torso silhouette via a clip path. */
function ArenaOutfitDetail({ outfit, colors, accent, build, S }) {
  const { shoulder, waist, chest: chestW } = build
  const { shoulder: sy, chest, waist: wy, centerX: cx } = S
  switch (outfit) {
    case 'academy':
      return <g>
        <path d={`M${cx - shoulder + 4} ${sy - 2} L${cx} ${chest + 14} L${cx - waist - 3} ${wy + 4} Z`} fill={colors[1]} opacity=".8" />
        <path d={`M${cx + shoulder - 4} ${sy - 2} L${cx} ${chest + 14} L${cx + waist + 3} ${wy + 4} Z`} fill={colors[1]} opacity=".8" />
        <path d={`M${cx - shoulder + 4} ${sy - 2} L${cx} ${chest + 14} L${cx + shoulder - 4} ${sy - 2}`} fill="none" stroke={accent} strokeWidth="2" />
        <path d={`M${cx - 3.4} ${chest + 14} L${cx + 3.4} ${chest + 14} L${cx + 1.6} ${chest + 27} L${cx - 1.6} ${chest + 27} Z`} fill={accent} />
      </g>
    case 'varsity':
      return <g>
        <path d={`M${cx - shoulder} ${sy + 8} L${cx + shoulder} ${sy + 8}`} stroke={colors[2]} strokeWidth="7" opacity=".85" />
        <path d={`M${cx - waist - 6} ${wy - 6} L${cx + waist + 6} ${wy - 6}`} stroke={colors[2]} strokeWidth="6" opacity=".85" />
        <path d={`M${cx - waist - 6} ${wy - 6} L${cx + waist + 6} ${wy - 6}`} stroke={accent} strokeWidth="2" />
      </g>
    case 'techwear':
      return <g>
        <path d={`M${cx - shoulder} ${sy} L${cx + 8} ${sy + 4} L${cx - 2} ${wy + 6} L${cx - shoulder} ${wy}`} fill={colors[1]} opacity=".72" />
        <path d={`M${cx + 8} ${sy + 4} L${cx - 2} ${wy + 6}`} stroke={accent} strokeWidth="2.4" />
        <rect x={cx + 14} y={chest + 12} width="13" height="7" rx="2.6" fill="none" stroke={accent} strokeWidth="1.6" />
        <rect x={cx + 14} y={chest + 22} width="9" height="6" rx="2.4" fill="none" stroke={accent} strokeWidth="1.4" />
      </g>
    case 'street':
      return <g>
        <path d={`M${cx - shoulder} ${sy + 4} Q${cx} ${sy + 14} ${cx + shoulder} ${sy + 4}`} fill="none" stroke={accent} strokeWidth="3.4" />
        <rect x={cx - waist + 2} y={wy - 22} width={waist * 2 - 4} height="18" rx="5" fill="none" stroke="rgba(255,255,255,.3)" strokeWidth="2.2" />
      </g>
    case 'champion':
      return <g>
        <path d={`M${cx - shoulder + 1} ${sy + 2} Q${cx} ${sy + 15} ${cx + shoulder - 1} ${sy + 2}`} fill="none" stroke={accent} strokeWidth="5.4" strokeLinecap="round" />
        <path d={`M${cx - waist - 2} ${wy - 4} L${cx + waist + 2} ${wy - 4}`} stroke={accent} strokeWidth="3.4" strokeLinecap="round" opacity=".95" />
        <path d={`M${cx - shoulder + 6} ${chest + 2} L${cx - waist} ${wy - 10}`} stroke={accent} strokeWidth="1.6" opacity=".7" />
        <path d={`M${cx + shoulder - 6} ${chest + 2} L${cx + waist} ${wy - 10}`} stroke={accent} strokeWidth="1.6" opacity=".7" />
      </g>
    case 'hoodie':
      return <g>
        <path d={`M${cx - shoulder - 2} ${sy - 8} Q${cx} ${sy + 22} ${cx + shoulder + 2} ${sy - 8}`} fill={colors[1]} opacity=".9" />
        <path d={`M${cx - 5} ${sy + 10} L${cx - 4} ${chest + 12} M${cx + 5} ${sy + 10} L${cx + 4} ${chest + 12}`}
          stroke={accent} strokeWidth="2" strokeLinecap="round" />
        <path d={`M${cx - waist + 4} ${wy - 16} L${cx + waist - 4} ${wy - 16}`} stroke="rgba(255,255,255,.2)" strokeWidth="12" />
      </g>
    case 'jersey':
      return <g>
        <path d={`M${cx - shoulder} ${sy - 4} Q${cx} ${sy + 12} ${cx + shoulder} ${sy - 4}`} fill="none" stroke={accent} strokeWidth="3" />
        <text x={cx} y={wy - 4} textAnchor="middle" fontSize="17" fontWeight="900" fill={colors[2]} opacity=".85" fontFamily="inherit">01</text>
      </g>
    case 'flight':
      return <g>
        <path d={`M${cx - chestW} ${chest - 4} L${cx + chestW} ${chest - 8}`} stroke={colors[1]} strokeWidth="8" opacity=".8" />
        <path d={`M${cx - chestW} ${chest - 4} L${cx + chestW} ${chest - 8}`} stroke={accent} strokeWidth="1.6" />
        <path d={`M${cx - shoulder + 4} ${sy + 2} L${cx - shoulder + 4} ${wy}`} stroke={accent} strokeWidth="1.6" opacity=".7" />
        <path d={`M${cx + shoulder - 4} ${sy + 2} L${cx + shoulder - 4} ${wy}`} stroke={accent} strokeWidth="1.6" opacity=".7" />
        <rect x={cx - waist * 0.6} y={wy - 22} width="12" height="9" rx="2.4" fill="none" stroke={accent} strokeWidth="1.4" />
      </g>
    case 'scholar':
      return <g>
        <path d={`M${cx - 9} ${sy - 6} L${cx - 6} ${wy + 12} L${cx + 6} ${wy + 12} L${cx + 9} ${sy - 6} Z`} fill={accent} opacity=".8" />
        <path d={`M${cx - shoulder} ${sy + 2} Q${cx} ${sy + 18} ${cx + shoulder} ${sy + 2}`} fill="none" stroke={colors[1]} strokeWidth="6" />
      </g>
    default: // combat
      return <g>
        <path d={`M${cx - shoulder + 3} ${sy + 6} Q${cx} ${sy + 13} ${cx + shoulder - 3} ${sy + 6}`} fill="none" stroke="rgba(255,255,255,.24)" strokeWidth="3" />
        <path d={`M${cx - waist + 3} ${chest + 6} L${cx + waist - 3} ${chest + 2}`} stroke="rgba(255,255,255,.16)" strokeWidth="4" strokeLinecap="round" />
        <path d={`M${cx - shoulder + 4} ${chest - 6} L${cx - waist + 1} ${wy - 4}`}
          stroke={INK} strokeWidth="2" opacity=".22" />
        <path d={`M${cx + shoulder - 4} ${chest - 6} L${cx + waist - 1} ${wy - 4}`}
          stroke={INK} strokeWidth="2" opacity=".22" />
      </g>
  }
}

function ArenaMarking({ marking, accent, build, S }) {
  const { shoulder, waist } = build
  const { shoulder: sy, chest, waist: wy, centerX: cx } = S
  switch (marking) {
    case 'stripes':
      return <g stroke={accent} strokeWidth="4" opacity=".55" strokeLinecap="round">
        <path d={`M${cx - shoulder * 0.5} ${sy - 10} L${cx - waist * 0.5} ${wy + 14}`} />
        <path d={`M${cx - shoulder * 0.2} ${sy - 10} L${cx - waist * 0.2} ${wy + 14}`} />
      </g>
    case 'circuit':
      return <g stroke={accent} strokeWidth="1.8" fill="none" opacity=".7">
        <path d={`M${cx - shoulder + 6} ${chest - 8} h${shoulder * 0.5} v10 h${shoulder * 0.4}`} />
        <path d={`M${cx + shoulder - 6} ${chest + 14} h${-shoulder * 0.45} v-12 h${-shoulder * 0.3}`} />
        <circle cx={cx - shoulder + 6} cy={chest - 8} r="2.4" fill={accent} stroke="none" />
        <circle cx={cx + shoulder - 6} cy={chest + 14} r="2.4" fill={accent} stroke="none" />
      </g>
    case 'chevron':
      return <g stroke={accent} strokeWidth="3.4" fill="none" opacity=".6" strokeLinejoin="round">
        {[0, 1, 2].map(i => <path key={i}
          d={`M${cx - waist} ${wy - 26 + i * 11} L${cx} ${wy - 32 + i * 11} L${cx + waist} ${wy - 26 + i * 11}`} />)}
      </g>
    case 'stars':
      return <g fill={accent} opacity=".7">
        {[[-0.5, -14], [0.35, 4], [-0.2, 20], [0.6, -24]].map(([fx, dy], i) => {
          const x = cx + fx * shoulder
          const y = chest + dy
          return <path key={i} d={`M${x} ${y - 5} L${x + 1.4} ${y - 1.5} L${x + 5} ${y - 1.4}
                                   L${x + 2.2} ${y + 1} L${x + 3.1} ${y + 4.6} L${x} ${y + 2.5}
                                   L${x - 3.1} ${y + 4.6} L${x - 2.2} ${y + 1} L${x - 5} ${y - 1.4}
                                   L${x - 1.4} ${y - 1.5} Z`} />
        })}
      </g>
    case 'scales':
      return <g fill="none" stroke={accent} strokeWidth="1.5" opacity=".45">
        {[0, 1, 2, 3].map(row => [-2, -1, 0, 1, 2].map(col =>
          <path key={`${row}-${col}`}
            d={`M${cx + col * 13 + (row % 2 ? 6.5 : 0) - 6.5} ${sy + 4 + row * 11}
                a6.5 6 0 0 0 13 0`} />))}
      </g>
    default:
      return null
  }
}

function ArenaShoulders({ shoulder, accent, build, S }) {
  const { shoulder: half } = build
  const { shoulder: sy, chest, centerX: cx } = S
  if (shoulder === 'none') return null
  if (shoulder === 'sash') {
    return <path d={`M${cx - half - 1} ${sy + 4} L${cx - half + 13} ${sy - 6}
                     L${cx + half * 0.5} ${chest + 26} L${cx + half * 0.5 - 13} ${chest + 30} Z`}
      fill={accent} stroke={INK} strokeWidth={INK_WEIGHT} strokeLinejoin="round" />
  }
  return <g>{[-1, 1].map(side => {
    const x = cx + side * half
    if (shoulder === 'pauldrons') {
      return <path key={side} d={`M${x - side * 15} ${sy + 13} a16 14 0 0 1 ${side * 28} 0
                                  l${-side * 3} 15 a14 11 0 0 0 ${-side * 22} 0 Z`}
        fill={`url(#${S.uid}-limb)`} stroke={INK} strokeWidth={INK_WEIGHT} strokeLinejoin="round" />
    }
    if (shoulder === 'epaulettes') {
      return <rect key={side} x={x - 14} y={sy + 7} width="27" height="12" rx="4.5"
        fill={accent} stroke={INK} strokeWidth={INK_WEIGHT} />
    }
    return <path key={side} d={`M${x - 13} ${sy + 20} L${x - 7} ${sy + 2} L${x - 1} ${sy + 18}
                                L${x + 5} ${sy} L${x + 12} ${sy + 20} Z`}
      fill={accent} stroke={INK} strokeWidth="2" strokeLinejoin="round" />
  })}</g>
}

function ArenaWaistGear({ waist, colors, accent, build, S }) {
  const { waist: half, hip } = build
  const { waist: wy, hip: hy, centerX: cx } = S
  switch (waist) {
    case 'pouch':
      return <rect x={cx + half - 6} y={wy + 6} width="16" height="15" rx="4"
        fill={colors[1]} stroke={INK} strokeWidth={INK_WEIGHT} />
    case 'wrap':
      return <path d={`M${cx - hip - 3} ${wy + 6} L${cx + hip + 3} ${wy + 6}
                       L${cx + hip - 2} ${hy + 30} L${cx - hip + 2} ${hy + 26} Z`}
        fill={accent} opacity=".85" stroke={INK} strokeWidth={INK_WEIGHT} strokeLinejoin="round" />
    case 'chain':
      return <g fill="none" stroke={accent} strokeWidth="2.4">
        <path d={`M${cx - half} ${wy + 7} q${half * 0.6} 16 ${half * 1.2} 2`} />
        <circle cx={cx - half * 0.4} cy={wy + 15} r="2.2" fill={accent} />
      </g>
    case 'holsters':
      return <g>{[-1, 1].map(side =>
        <rect key={side} x={cx + side * (hip - 2) - 7} y={wy + 8} width="14" height="20" rx="4"
          fill={colors[1]} stroke={INK} strokeWidth={INK_WEIGHT} />)}
      </g>
    default:
      return null
  }
}

function ArenaAura({ aura, colors, accent, uid, S, head }) {
  // Every aura is positioned from the skeleton rather than from fixed viewBox
  // numbers. The old hardcoded coordinates were tuned for one build, so a short
  // or tall fighter wore their halo through their forehead.
  const cx = S.centerX
  const mid = (S.shoulder + S.hip) / 2
  switch (aura) {
    case 'none': return null
    case 'halo':
      return <g className="arena-fighter-aura">
        <ellipse cx={cx} cy={head.top - 12} rx={head.w * 1.25} ry={head.w * 0.34}
          fill="none" stroke={accent} strokeWidth="4" opacity=".35" />
        {/* The front arc is drawn brighter so the ring reads as a tilted disc
            rather than a flat circle stuck to the character's head. */}
        <path d={`M${cx - head.w * 1.25} ${head.top - 12} a${head.w * 1.25} ${head.w * 0.34} 0 0 0 ${head.w * 2.5} 0`}
          fill="none" stroke={accent} strokeWidth="4" strokeLinecap="round" />
      </g>
    case 'spark':
      return <g className="arena-fighter-aura" fill={accent}>
        {[[-1, S.chest - 18], [1, S.chest - 4], [-1, S.hip + 8], [1, S.hip - 6],
          [-1, S.knee + 16], [1, S.knee + 4]].map(([side, y], i) => {
          const x = cx + side * (52 + (i % 3) * 7)
          const r = 5 + (i % 2) * 1.6
          return <path key={i} d={`M${x} ${y - r} L${x + r * 0.32} ${y - r * 0.32} L${x + r} ${y}
                                   L${x + r * 0.32} ${y + r * 0.32} L${x} ${y + r}
                                   L${x - r * 0.32} ${y + r * 0.32} L${x - r} ${y}
                                   L${x - r * 0.32} ${y - r * 0.32} Z`} />
        })}
      </g>
    case 'orbit':
      return <ellipse className="arena-fighter-aura" cx={cx} cy={mid} rx="66"
        ry={(S.ground - head.top) * 0.56} fill="none" stroke={colors[2]} strokeWidth="2"
        strokeDasharray="9 11" opacity=".7" />
    case 'flare':
      return <ellipse className="arena-fighter-aura" cx={cx} cy={S.hip} rx="78"
        ry={(S.ground - head.top) * 0.62} fill={`url(#${uid}-glow)`} opacity=".85" />
    case 'embers':
      return <g className="arena-fighter-aura" fill={accent}>
        {[[-1, S.knee + 10, 3], [-1, S.chest + 6, 2.2], [1, S.hip + 22, 2.8],
          [1, S.chest - 12, 2], [-1, S.shoulder + 4, 1.8], [1, S.knee + 30, 2.4]].map(([side, y, r], i) =>
            <circle key={i} cx={cx + side * (48 + (i % 3) * 9)} cy={y} r={r} opacity={.55 + (i % 3) * .15} />)}
      </g>
    case 'frost':
      return <g className="arena-fighter-aura" stroke={accent} strokeWidth="1.6" fill="none" opacity=".8">
        {[[-1, S.chest], [1, S.chest + 16], [-1, S.knee], [1, S.knee - 12]].map(([side, y], i) => {
          const x = cx + side * (52 + (i % 2) * 6)
          return <path key={i} d={`M${x} ${y - 7} L${x} ${y + 7} M${x - 6} ${y - 3.5} L${x + 6} ${y + 3.5}
                                   M${x - 6} ${y + 3.5} L${x + 6} ${y - 3.5}`} />
        })}
      </g>
    case 'storm':
      return <g className="arena-fighter-aura" stroke={colors[2]} strokeWidth="2.2" fill="none"
        strokeLinecap="round" opacity=".85">
        <path d={`M${cx - 58} ${S.chest - 8} l10 22 l-7 3 l11 20`} />
        <path d={`M${cx + 58} ${S.chest + 8} l-10 22 l7 3 l-11 20`} />
      </g>
    default: // pulse -- a soft ground-up glow, not a ring drawn around the body
      return <ellipse className="arena-fighter-aura" cx={cx} cy={S.hip + 24} rx="62"
        ry={(S.ground - head.top) * 0.52} fill={`url(#${uid}-glow)`} opacity=".55" />
  }
}

// --- Fighter ---------------------------------------------------------------

function ArenaFighterView({ avatar, label = 'Arena fighter', size = 'full', facing = 'right', state = 'idle' }) {
  const loadout = useMemo(() => normalizeArenaAvatar(avatar), [avatar])
  const colors = ARENA_AVATAR_PALETTES[loadout.palette]
  const skin = ARENA_AVATAR_SKINS[loadout.skin]
  const hairColor = ARENA_AVATAR_HAIR[loadout.hair_color]
  const accent = ARENA_AVATAR_ACCENTS[loadout.accent]
  const eyeColor = ARENA_AVATAR_EYES[loadout.eyes]
  const hairShadow = `color-mix(in srgb, ${hairColor} 72%, #000)`

  // Gradient ids must be unique per rendered fighter: two fighters share one
  // document, and duplicate ids would make the rival inherit the player's suit.
  const uid = useMemo(() =>
    `af${[loadout.palette, loadout.skin, loadout.body, loadout.frame, loadout.height, size, facing].join('-')}`,
  [loadout.palette, loadout.skin, loadout.body, loadout.frame, loadout.height, size, facing])

  const frame = FRAMES[loadout.frame]
  const base = BUILDS[loadout.body]
  const build = {
    shoulder: base.shoulder * frame.shoulder,
    chest: base.chest * frame.shoulder,
    waist: base.waist * frame.waist,
    hip: base.hip * frame.hip,
    arm: base.arm, thigh: base.thigh, calf: base.calf, neck: base.neck,
  }
  const S = buildSkeleton(loadout.height)
  const cx = S.centerX
  const headH = (S.chin - S.headTop) * S.headScale
  const head = { cx, top: S.chin - headH, h: headH, w: 22 * frame.headW * S.headScale }
  const headBottom = S.chin + frame.chinY

  const skirt = loadout.bottom === 'battle_skirt' || loadout.bottom === 'pleated'
  const shorts = loadout.bottom === 'shorts'
  const legWidth = loadout.bottom === 'fitted' ? build.thigh * 0.86
    : loadout.bottom === 'joggers' ? build.thigh * 1.16 : build.thigh
  const legSpread = build.hip * 0.5
  const pants = `url(#${uid}-pants)`

  // Trapezius slope into the shoulder, a taper through the ribs to the waist,
  // then a flare back out to the hips. The outline alone should read as a
  // torso; the outfit layers on top are detail, not the shape.
  const torso = `M${cx - build.shoulder} ${S.shoulder + 7}
    C${cx - build.shoulder} ${S.shoulder - 4} ${cx - build.shoulder * 0.5} ${S.shoulder - 8} ${cx} ${S.shoulder - 8}
    C${cx + build.shoulder * 0.5} ${S.shoulder - 8} ${cx + build.shoulder} ${S.shoulder - 4} ${cx + build.shoulder} ${S.shoulder + 7}
    C${cx + build.chest} ${S.chest} ${cx + build.waist + 3} ${S.waist - 10} ${cx + build.waist} ${S.waist}
    C${cx + build.hip} ${S.hip - 13} ${cx + build.hip} ${S.hip - 8} ${cx + build.hip - 3} ${S.hip - 2}
    L${cx - build.hip + 3} ${S.hip - 2}
    C${cx - build.hip} ${S.hip - 8} ${cx - build.hip} ${S.hip - 13} ${cx - build.waist} ${S.waist}
    C${cx - build.waist - 3} ${S.waist - 10} ${cx - build.chest} ${S.chest} ${cx - build.shoulder} ${S.shoulder + 7} Z`

  // The arm swings clear of the ribs before dropping, so the whole limb reads
  // against the background instead of a hand appearing beside a solid block.
  const pose = POSES[loadout.pose] || POSES.ready
  const arm = side => {
    const sx = cx + side * (build.shoulder * 0.84)
    const sy = S.shoulder + 2
    const ex = cx + side * (build.shoulder + build.arm * pose.elbow)
    const ey = S.waist + 2
    const wx = cx + side * (build.shoulder * pose.wrist)
    const wy = S.hip + pose.drop
    return {
      upper: `M${sx} ${sy} C${cx + side * (build.shoulder + build.arm * 0.5)} ${S.chest - 6} ${ex} ${S.chest + 8} ${ex} ${ey}`,
      fore: `M${ex} ${ey} C${ex} ${ey + 14} ${wx + side * 1} ${wy - 12} ${wx} ${wy}`,
      hand: [wx, wy + build.arm * 0.16],
    }
  }
  const leg = side => {
    const tx = cx + side * legSpread
    const kx = cx + side * (legSpread * 0.94)
    const ax = cx + side * (legSpread * 0.86)
    return {
      thigh: `M${tx} ${S.hip + 6} C${tx + side * 2} ${S.hip + 24} ${kx + side * 1.5} ${S.knee - 22} ${kx} ${S.knee}`,
      calf: `M${kx} ${S.knee} C${kx - side * 1} ${S.knee + 22} ${ax + side * 1.5} ${S.ankle - 20} ${ax} ${S.ankle}`,
      foot: [ax, S.ankle],
    }
  }
  // The hip piece bridges the top to the legs so the silhouette has a real
  // waist-to-crotch transition instead of one shape squared off at the bottom.
  const pelvis = `M${cx - build.hip} ${S.hip - 12} L${cx + build.hip} ${S.hip - 12}
    C${cx + build.hip} ${S.hip + 6} ${cx + build.hip * 0.82} ${S.hip + 15} ${cx + build.hip * 0.62} ${S.hip + 18}
    C${cx + build.hip * 0.32} ${S.hip + 13} ${cx} ${S.hip + 7} ${cx} ${S.hip + 13}
    C${cx} ${S.hip + 7} ${cx - build.hip * 0.32} ${S.hip + 13} ${cx - build.hip * 0.62} ${S.hip + 18}
    C${cx - build.hip * 0.82} ${S.hip + 15} ${cx - build.hip} ${S.hip + 6} ${cx - build.hip} ${S.hip - 12} Z`
  const arms = { left: arm(-1), right: arm(1) }
  const legs = { left: leg(-1), right: leg(1) }

  const gloveRadius = loadout.gloves === 'gauntlets' ? build.arm * 0.84 : build.arm * 0.68
  const gloveFill = loadout.gloves === 'none' ? skin[0]
    : loadout.gloves === 'gauntlets' ? `url(#${uid}-limb)`
      : loadout.gloves === 'wraps' ? colors[2] : colors[0]
  const emblem = EMBLEM_PATHS[loadout.emblem]

  const hand = (position, side) => <g key={`hand${side}`}>
    {loadout.gloves !== 'none' &&
      <rect x={position[0] - gloveRadius * 0.95} y={position[1] - gloveRadius * 1.5}
        width={gloveRadius * 1.9} height={gloveRadius * 0.9} rx={gloveRadius * 0.35}
        fill={accent} stroke={INK} strokeWidth="2" />}
    <ellipse cx={position[0]} cy={position[1]} rx={gloveRadius} ry={gloveRadius * 1.12} fill={gloveFill}
      stroke={INK} strokeWidth="2" />
    {loadout.gloves === 'wraps' && [0, 1, 2].map(i =>
      <path key={i} d={`M${position[0] - gloveRadius} ${position[1] - 3 + i * 3} L${position[0] + gloveRadius} ${position[1] - 4 + i * 3}`}
        stroke={colors[1]} strokeWidth="1.3" opacity=".8" />)}
    {loadout.gloves === 'claws' && [-1, 0, 1].map(i =>
      <path key={i} d={`M${position[0] + i * 3.4} ${position[1] + gloveRadius * 0.4}
                        l${i * 2} ${gloveRadius + 5}`}
        stroke={accent} strokeWidth="2" strokeLinecap="round" fill="none" />)}
  </g>

  const foot = ([x, y], side) => {
    if (loadout.footwear === 'barefoot') {
      return <ellipse key={side} cx={x + side * build.calf * 0.22} cy={y + 4} rx={build.calf * 0.72} ry="5.4"
        fill={skin[0]} stroke={INK} strokeWidth="2" />
    }
    const w = loadout.footwear === 'armored' ? build.calf * 1.5 : build.calf * 1.25
    const h = loadout.footwear === 'high_tops' ? 13 : loadout.footwear === 'armored' ? 15 : 12
    return <g key={side}>
      {loadout.footwear === 'high_tops' &&
        <rect x={x - build.calf * 0.62} y={y - 14} width={build.calf * 1.24} height="16" rx="4.5"
          fill={colors[2]} stroke={INK} strokeWidth="2" />}
      {loadout.footwear === 'greaves' &&
        <path d={`M${x - build.calf * 0.7} ${y - 30} L${x + build.calf * 0.7} ${y - 30}
                  L${x + build.calf * 0.6} ${y - 2} L${x - build.calf * 0.6} ${y - 2} Z`}
          fill={`url(#${uid}-limb)`} stroke={INK} strokeWidth="2" strokeLinejoin="round" />}
      <g transform={side < 0 ? `translate(${2 * x} 0) scale(-1 1)` : undefined}>
        {/* Heel, instep, toe: a shoe profile rather than a wedge. */}
        <path d={`M${x - w * 0.46} ${y - h + 3} Q${x - w * 0.52} ${y + h - 6} ${x - w * 0.38} ${y + h - 3}
                  L${x + w * 0.66} ${y + h - 3} Q${x + w * 0.84} ${y + h - 4} ${x + w * 0.78} ${y + h - 9}
                  Q${x + w * 0.42} ${y - h + 5} ${x + w * 0.16} ${y - h + 3} Z`}
          fill={loadout.footwear === 'runners' || loadout.footwear === 'low_tops' ? colors[2] : `url(#${uid}-limb)`}
          stroke={INK} strokeWidth="2.2" strokeLinejoin="round" />
        <path d={`M${x - w * 0.36} ${y + h - 3.4} L${x + w * 0.64} ${y + h - 3.4}`}
          stroke={accent} strokeWidth="1.4" strokeLinecap="round" opacity=".32" />
        {loadout.footwear === 'runners' &&
          <path d={`M${x - w * 0.3} ${y + 2} L${x + w * 0.5} ${y}`} stroke={accent} strokeWidth="1.6" strokeLinecap="round" opacity=".7" />}
        {loadout.footwear === 'armored' &&
          <path d={`M${x - w * 0.34} ${y - 3} L${x + w * 0.6} ${y - 5}`} stroke="rgba(255,255,255,.35)" strokeWidth="2.4" strokeLinecap="round" />}
      </g>
    </g>
  }

  return <div
    className={`arena-fighter arena-fighter--${loadout.body} arena-fighter--${size} arena-fighter--${state}`}
    data-facing={facing}
    data-frame={loadout.frame}
    data-height={loadout.height}
    data-gear={loadout.gear}
    data-hair={loadout.hair}
    data-face={loadout.face}
    data-outfit={loadout.outfit}
    data-bottom={loadout.bottom}
    data-gloves={loadout.gloves}
    data-footwear={loadout.footwear}
    data-back={loadout.back}
    data-aura={loadout.aura}
    role="img"
    aria-label={label}
  >
    <svg className="arena-fighter-svg" viewBox="0 0 200 300" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
{/* Highlight, base, core shadow -- all running the same way as the light. */}
        <linearGradient id={`${uid}-suit`} x1="0.1" y1="0" x2="0.75" y2="1">
          <stop offset="0%" stopColor={`color-mix(in srgb, ${colors[0]} 76%, #ffffff)`} />
          <stop offset="42%" stopColor={colors[0]} />
          <stop offset="100%" stopColor={colors[1]} />
        </linearGradient>
        <linearGradient id={`${uid}-limb`} x1="0" y1="0" x2="1" y2="0.35">
          <stop offset="0%" stopColor={`color-mix(in srgb, ${colors[0]} 82%, #ffffff)`} />
          <stop offset="46%" stopColor={colors[0]} />
          <stop offset="100%" stopColor={colors[1]} />
        </linearGradient>
        <linearGradient id={`${uid}-skin`} x1="0.2" y1="0" x2="0.9" y2="1">
          <stop offset="0%" stopColor={skin[2]} /><stop offset="52%" stopColor={skin[0]} /><stop offset="100%" stopColor={skin[1]} />
        </linearGradient>
        <linearGradient id={`${uid}-pants`} x1="0.1" y1="0" x2="0.8" y2="1">
          <stop offset="0%" stopColor={`color-mix(in srgb, ${colors[1]} 74%, #c9d6ff)`} />
          <stop offset="45%" stopColor={`color-mix(in srgb, ${colors[1]} 82%, #0b1030)`} />
          <stop offset="100%" stopColor={`color-mix(in srgb, ${colors[1]} 46%, #0b1030)`} />
        </linearGradient>
        <radialGradient id={`${uid}-glow`}>
          <stop offset="0%" stopColor={colors[2]} stopOpacity="0.5" />
          <stop offset="55%" stopColor={colors[0]} stopOpacity="0.26" />
          <stop offset="100%" stopColor={colors[0]} stopOpacity="0" />
        </radialGradient>
        <clipPath id={`${uid}-torso-clip`}><path d={torso} /></clipPath>
      </defs>

      <ArenaAura aura={loadout.aura} colors={colors} accent={accent} uid={uid} S={S} head={head} />
      <ellipse className="arena-fighter-shadow" cx={cx} cy={S.ground + 8} rx={build.hip + 22} ry="8" fill="rgba(6,8,40,.45)" />

      <g className="arena-fighter-rig">
        {/* Back to front: back gear, back hair, legs, torso, arms, head.
            Paint order does the layering -- no z-index guesswork. */}
        <ArenaBackGear back={loadout.back} colors={colors} accent={accent} build={build} S={S} uid={uid} />
        {hairBack(loadout.hair, head, S.shoulder).map((d, i) =>
          <path key={i} d={d} fill={hairShadow} stroke={INK} strokeWidth={INK_WEIGHT} strokeLinejoin="round" />)}

{['left', 'right'].map(side => {
          const bare = skirt || shorts
          const skinTone = side === 'left' ? skin[1] : skin[0]
          return <g key={side} className={`arena-fighter-leg arena-fighter-leg--${side}`}
            strokeLinecap="round" fill="none">
            <path d={legs[side].thigh} stroke={INK} strokeWidth={legWidth + LIMB_INK} />
            <path d={legs[side].calf} stroke={INK} strokeWidth={build.calf + LIMB_INK} />
            <path d={legs[side].thigh} stroke={bare ? skinTone : pants} strokeWidth={legWidth} />
            <path d={legs[side].calf} stroke={bare ? skinTone : pants} strokeWidth={build.calf} />
            {/* A thinner lit stroke offset toward the light turns a flat band
                into a cylinder -- the cheapest honest volume there is. */}
            <g transform={LIGHT_SHIFT} opacity={side === 'left' ? '.1' : '.3'}>
              <path d={legs[side].thigh} stroke="#fff" strokeWidth={legWidth * 0.4} />
              <path d={legs[side].calf} stroke="#fff" strokeWidth={build.calf * 0.4} />
            </g>

          </g>
        })}
        {foot(legs.left.foot, -1)}
        {foot(legs.right.foot, 1)}
        <path d={pelvis} fill={skirt || shorts ? `url(#${uid}-suit)` : pants}
          stroke={INK} strokeWidth={INK_WEIGHT} strokeLinejoin="round" />

        {loadout.bottom === 'cargo' && <g fill={colors[1]} stroke={accent} strokeWidth="1.4">
          <rect x={cx - legSpread - build.thigh * 0.62} y={S.hip + 26} width="13" height="15" rx="3.4" />
          <rect x={cx + legSpread - build.thigh * 0.38} y={S.hip + 26} width="13" height="15" rx="3.4" />
        </g>}
        {loadout.bottom === 'joggers' && [-1, 1].map(side =>
          <path key={side} d={`M${cx + side * legSpread - build.calf * 0.8} ${S.knee + 26}
                               L${cx + side * legSpread + build.calf * 0.8} ${S.knee + 26}`}
            stroke={accent} strokeWidth="3" strokeLinecap="round" />)}
        {shorts && <path d={`M${cx - build.hip - 2} ${S.hip + 2} L${cx + build.hip + 2} ${S.hip + 2}
                             L${cx + build.hip} ${S.hip + 30} L${cx + 3} ${S.hip + 26}
                             L${cx - 3} ${S.hip + 26} L${cx - build.hip} ${S.hip + 30} Z`}
          fill={`url(#${uid}-suit)`} stroke={accent} strokeWidth="1.4" strokeLinejoin="round" />}
        {skirt && <path d={loadout.bottom === 'pleated'
          ? `M${cx - build.hip - 3} ${S.hip + 2} L${cx + build.hip + 3} ${S.hip + 2}
             L${cx + build.hip + 12} ${S.hip + 38} L${cx + build.hip * 0.5} ${S.hip + 32}
             L${cx} ${S.hip + 38} L${cx - build.hip * 0.5} ${S.hip + 32} L${cx - build.hip - 12} ${S.hip + 38} Z`
          : `M${cx - build.hip - 4} ${S.hip + 2} L${cx + build.hip + 4} ${S.hip + 2}
             L${cx + build.hip + 13} ${S.hip + 40} L${cx + 6} ${S.hip + 32}
             L${cx - 6} ${S.hip + 38} L${cx - build.hip - 13} ${S.hip + 40} Z`}
          fill={`url(#${uid}-suit)`} stroke={accent} strokeWidth="1.6" strokeLinejoin="round" />}

        {/* Neck first, torso over it, so the jaw shades onto the collar. */}
        <path d={`M${cx - build.neck * 1.12} ${headBottom - 8} L${cx - build.neck * 0.98} ${S.shoulder - 2}
                  L${cx + build.neck * 0.98} ${S.shoulder - 2} L${cx + build.neck * 1.12} ${headBottom - 8} Z`}
          fill={skin[0]} stroke={INK} strokeWidth={INK_WEIGHT} strokeLinejoin="round" />
        {/* The jaw casts onto the neck, not onto its own chin. */}
        <path d={`M${cx - build.neck * 1.06} ${headBottom - 7} L${cx + build.neck * 1.06} ${headBottom - 7}
                  L${cx + build.neck * 0.98} ${headBottom + 2} L${cx - build.neck * 0.98} ${headBottom + 2} Z`}
          fill={skin[1]} opacity=".85" />

        <g className="arena-fighter-torso">
          <path d={torso} fill={`url(#${uid}-suit)`} stroke={INK} strokeWidth={INK_WEIGHT} strokeLinejoin="round" />
          <g clipPath={`url(#${uid}-torso-clip)`}>
            <ArenaOutfitDetail outfit={loadout.outfit} colors={colors} accent={accent} build={build} S={S} />
            <ArenaMarking marking={loadout.marking} accent={accent} build={build} S={S} />
            <path d={`M${cx - build.shoulder - 4} ${S.shoulder - 12} Q${cx - build.chest * 0.35} ${S.chest + 16} ${cx - build.waist - 6} ${S.waist + 22}`}
              stroke="rgba(255,255,255,.09)" strokeWidth="13" fill="none" />
          </g>
          {/* Belt: a real band across the waist, not a floating pill. */}
          <path d={`M${cx - build.waist - 1} ${S.waist + 3} L${cx + build.waist + 1} ${S.waist + 3}`}
            stroke="rgba(10,14,50,.55)" strokeWidth="9" />
          <rect x={cx - 6} y={S.waist - 2.5} width="12" height="11" rx="2.6" fill={colors[1]} stroke={accent} strokeWidth="1.6" />
          <g clipPath={`url(#${uid}-torso-clip)`}>
            {/* The head casts onto the chest, and the arm on the shadow side
                casts along the ribs. Contact shadows are what tell the eye
                which part is in front of which. */}
            <ellipse cx={cx} cy={S.shoulder - 6} rx={build.neck * 1.5} ry="11" fill={INK} opacity=".26" />
            <path d={`M${cx + build.chest * 0.5} ${S.shoulder - 12} Q${cx + build.chest} ${S.chest} ${cx + build.waist} ${S.waist + 8}
                      L${cx + build.hip + 6} ${S.hip} L${cx + build.hip + 6} ${S.shoulder - 12} Z`}
              fill={INK} opacity=".2" />
            <ellipse cx={cx} cy={S.hip + 2} rx={build.hip} ry="9" fill={INK} opacity=".16" />
            {/* Rim light down the lit edge. */}
            <path d={`M${cx - build.shoulder + 3} ${S.shoulder} Q${cx - build.chest - 1} ${S.chest} ${cx - build.waist - 1} ${S.waist + 4}`}
              fill="none" stroke="#fff" strokeWidth="3.4" opacity=".2" strokeLinecap="round" />
            {/* Two folds where cloth gathers at the waist. */}
            <path d={`M${cx - build.waist * 0.7} ${S.waist - 12} q${build.waist * 0.7} 6 ${build.waist * 1.4} -2`}
              fill="none" stroke={INK} strokeWidth="1.6" opacity=".16" />
            <path d={`M${cx - build.waist * 0.5} ${S.waist - 4} q${build.waist * 0.5} 5 ${build.waist} -1`}
              fill="none" stroke={INK} strokeWidth="1.4" opacity=".12" />
          </g>
          <ArenaWaistGear waist={loadout.waist} colors={colors} accent={accent} build={build} S={S} />
          <g transform={`translate(${cx} ${S.chest + 2})`}>
            <circle r="11" fill={accent} stroke={INK} strokeWidth="2" />
            <path d={emblem.d} fill={emblem.fill ? colors[1] : 'none'} stroke={colors[1]}
              strokeWidth={emblem.fill ? 0.6 : 1.5} strokeLinejoin="round" strokeLinecap="round" />
          </g>
        </g>

        {['left', 'right'].map(side =>
          <g key={side} className={`arena-fighter-arm arena-fighter-arm--${side}`} strokeLinecap="round" fill="none">
            <path d={arms[side].upper} stroke={INK} strokeWidth={build.arm + LIMB_INK} />
            <path d={arms[side].fore} stroke={INK} strokeWidth={build.arm * 0.86 + LIMB_INK} />
            <path d={arms[side].upper} stroke={`url(#${uid}-limb)`} strokeWidth={build.arm} />
            <path d={arms[side].fore} stroke={`url(#${uid}-limb)`} strokeWidth={build.arm * 0.86} />
            <g transform={LIGHT_SHIFT} opacity={side === 'left' ? '.1' : '.32'}>
              <path d={arms[side].upper} stroke="#fff" strokeWidth={build.arm * 0.36} />
              <path d={arms[side].fore} stroke="#fff" strokeWidth={build.arm * 0.32} />
            </g>

            {hand(arms[side].hand, side === 'left' ? -1 : 1)}
          </g>)}

        <ArenaShoulders shoulder={loadout.shoulder} accent={accent} build={build} S={S} />

        <g className="arena-fighter-head">
          {/* Cranium and jaw as one path: a rounded skull narrowing to a chin. */}
          <path d={`M${cx - head.w} ${head.top + head.h * 0.34}
                    A${head.w} ${head.h * 0.38} 0 0 1 ${cx + head.w} ${head.top + head.h * 0.34}
                    L${cx + head.w * frame.jaw * 0.94} ${head.top + head.h * 0.62}
                    Q${cx + head.w * frame.jaw * 0.82} ${headBottom - 2} ${cx} ${headBottom + 2}
                    Q${cx - head.w * frame.jaw * 0.82} ${headBottom - 2} ${cx - head.w * frame.jaw * 0.94} ${head.top + head.h * 0.62} Z`}
            fill={`url(#${uid}-skin)`} stroke={INK} strokeWidth={INK_WEIGHT} strokeLinejoin="round" />
          {/* The hair casts onto the forehead and the light side of the face
              stays open, which is what stops a face reading as a flat mask. */}
          <path d={`M${cx - head.w * 0.9} ${head.top + head.h * 0.3}
                    Q${cx} ${head.top + head.h * 0.42} ${cx + head.w * 0.9} ${head.top + head.h * 0.3}
                    L${cx + head.w * 0.9} ${head.top + head.h * 0.16}
                    L${cx - head.w * 0.9} ${head.top + head.h * 0.16} Z`}
            fill={skin[1]} opacity=".3" />
          <path d={`M${cx + head.w * 0.42} ${head.top + head.h * 0.22}
                    Q${cx + head.w * 1.02} ${head.top + head.h * 0.6} ${cx + head.w * 0.5} ${head.top + head.h * 0.94}
                    Q${cx + head.w * 0.95} ${head.top + head.h * 0.7} ${cx + head.w * 0.96} ${head.top + head.h * 0.3} Z`}
            fill={skin[1]} opacity=".35" />
          <ArenaFace loadout={loadout} head={head} skin={skin} accent={accent} hairColor={hairColor} eyeColor={eyeColor} />
          <path d={hairFront(loadout.hair, head)} fill={hairColor} stroke={INK}
            strokeWidth={INK_WEIGHT} strokeLinejoin="round" />
          {/* One highlight sweep gives the hair volume instead of a flat cap. */}
          <path d={`M${cx - head.w * 0.62} ${head.top + head.h * 0.16}
                    Q${cx - head.w * 0.1} ${head.top - 1} ${cx + head.w * 0.5} ${head.top + head.h * 0.1}`}
            fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" opacity=".18" />
          <ArenaHeadGear gear={loadout.gear} head={head} colors={colors} accent={accent} />
        </g>
      </g>
    </svg>
  </div>
}

// --- Locker ----------------------------------------------------------------

/** True when two loadouts would draw the same fighter. */
function sameLoadout(a, b) {
  if (a === b) return true
  const left = a || {}
  const right = b || {}
  return Object.keys(ARENA_AVATAR_DEFAULT).every(key => left[key] === right[key])
}

// The battle stage ticks a countdown four times a second, and each tick used to
// re-run every fighter's path maths and rebuild its whole SVG subtree. The
// avatar object arrives fresh from each poll response, so identity comparison
// is not enough -- the loadout has to be compared by value.
export const ArenaFighter = memo(ArenaFighterView, (previous, next) =>
  previous.size === next.size
  && previous.facing === next.facing
  && previous.state === next.state
  && previous.label === next.label
  && sameLoadout(previous.avatar, next.avatar))
ArenaFighter.displayName = 'ArenaFighter'


export function ArenaCustomizer({ avatar, onChange, onSave, onClose, saving }) {
  const [section, setSection] = useState('body')
  const current = normalizeArenaAvatar(avatar)
  const groups = (ARENA_CUSTOMIZER_SECTIONS.find(([key]) => key === section) || ARENA_CUSTOMIZER_SECTIONS[0])[2]
  return <div className="arena-customizer-backdrop" role="presentation"
    onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}>
    <section className="arena-customizer" role="dialog" aria-modal="true" aria-labelledby="arena-customizer-title">
      <header>
        <div>
          <small>FIGHTER LOCKER</small>
          <h2 id="arena-customizer-title">Make the fighter yours.</h2>
          <p>Twenty-one slots, mixed freely — every build, face, hairstyle, outfit, and effect combines.</p>
        </div>
        <button type="button" onClick={onClose} aria-label="Close fighter locker" autoFocus><X /></button>
      </header>
      <div className="arena-customizer-body">
        <div className="arena-customizer-preview">
          <i className="arena-preview-light" />
          <ArenaFighter avatar={current} label="Your customized Arena fighter" />
          <strong>LIVE LOADOUT</strong>
          <span>{current.frame} · {current.body} · {current.outfit}</span>
          <div className="arena-preview-actions">
            <button type="button" onClick={() => onChange(randomArenaAvatar())}><Dices /> Randomize</button>
            <button type="button" onClick={() => onChange({ ...ARENA_AVATAR_DEFAULT })}><RotateCcw /> Reset</button>
          </div>
        </div>
        <div className="arena-customizer-editor">
          <nav className="arena-customizer-tabs" aria-label="Fighter customization categories">
            {ARENA_CUSTOMIZER_SECTIONS.map(([key, title]) =>
              <button type="button" key={key} className={section === key ? 'selected' : ''}
                aria-pressed={section === key} onClick={() => setSection(key)}>{title}</button>)}
          </nav>
          <div className="arena-customizer-options">
            {groups.map(([key, title, choices, swatchKey]) => <fieldset key={key}>
              <legend>{title}</legend>
              <div>{choices.map(([value, optionLabel]) => {
                const swatch = swatchKey ? SWATCH_SOURCES[swatchKey]?.(value) : null
                return <button type="button" key={value} className={current[key] === value ? 'selected' : ''}
                  aria-pressed={current[key] === value} onClick={() => onChange({ ...current, [key]: value })}>
                  {swatch && <i style={{ background: swatch }} />}
                  <span>{optionLabel}</span>
                  {current[key] === value && <Check />}
                </button>
              })}</div>
            </fieldset>)}
          </div>
        </div>
      </div>
      <footer>
        <span>Cosmetics are visual only. Your rank still controls question difficulty.</span>
        <button type="button" className="arena-save-loadout" onClick={onSave} disabled={saving}>
          {saving ? 'SAVING…' : 'EQUIP LOADOUT'} <Sparkles />
        </button>
      </footer>
    </section>
  </div>
}

export default ArenaFighter
