import * as THREE from 'three'

// The head is lathed from this profile, so hair is built as an offset surface of
// the same curve: every style sits on the skull instead of hovering over it, and
// a hairline is simply the height where the hair stops.
export const HEAD_PROFILE = [[0,-.34],[.11,-.32],[.21,-.25],[.26,-.14],[.29,0],[.29,.13],[.24,.25],[.14,.32],[0,.35]]
const DEPTH = .91
const TAU = Math.PI * 2
const ease = t => t * t * (3 - 2 * t)
const clamp = (v, a, b) => v < a ? a : v > b ? b : v
const mix = (a, b, t) => a + (b - a) * t

// Dense crown-to-jaw polyline with outward normals, so a shell can be offset and
// cut at any height without re-deriving the skull.
const SKULL = (() => {
  const source = [...HEAD_PROFILE].reverse(), points = [source[0]]
  for (let i = 1; i < source.length; i++)
    for (let k = 1; k <= 6; k++) {
      const t = k / 6, [x0, y0] = source[i - 1], [x1, y1] = source[i]
      points.push([mix(x0, x1, t), mix(y0, y1, t)])
    }
  return points.map(([r, y], i) => {
    const a = points[Math.max(0, i - 1)], b = points[Math.min(points.length - 1, i + 1)]
    const dx = b[0] - a[0], dy = b[1] - a[1], length = Math.hypot(dx, dy) || 1
    return { r, y, nr: -dy / length, ny: dx / length }
  })
})()
const at = t => {
  const i = clamp(Math.floor(t), 0, SKULL.length - 2), f = t - i, a = SKULL[i], b = SKULL[i + 1]
  return { r: mix(a.r, b.r, f), y: mix(a.y, b.y, f), nr: mix(a.nr, b.nr, f), ny: mix(a.ny, b.ny, f) }
}
// Fractional index where the skull passes through a height, and the radius there.
const indexAt = y => {
  for (let i = 1; i < SKULL.length; i++)
    if (SKULL[i].y <= y) return i - 1 + (SKULL[i - 1].y - y) / (SKULL[i - 1].y - SKULL[i].y || 1)
  return SKULL.length - 1
}
const radiusAt = y => at(indexAt(y)).r

// thick: cap depth. line: [forehead, temple, nape] hairline heights. taper fades
// the sides toward the skin; grain, curl and part texture the surface; the rest
// name the masses a style adds. Silhouettes differ before colour does.
const STYLES = {
  buzz: { thick: .015, line: [.203, -.005, -.25], grain: 1.8, grainN: 44 },
  fade: { thick: .062, line: [.212, .085, -.20], taper: .95, fringe: 'crop', grain: 1.4 },
  crop: { thick: .072, line: [.198, .030, -.218], fringe: 'crop', grain: 1.5 },
  wave: { thick: .088, line: [.205, .025, -.218], fringe: 'swept', part: .9, sweep: .5, grain: 1.8 },
  spike: { thick: .050, line: [.205, .040, -.205], fringe: 'spike', spikes: 15 },
  mohawk: { thick: .017, line: [.198, .125, -.205], crest: true, taper: .55, grain: 1.6, grainN: 40 },
  undercut: { thick: .10, line: [.205, .145, -.12], taper: 1, sweep: .30, part: .5, grain: 1.4, quiff: .5 },
  pixie: { thick: .066, line: [.198, -.005, -.215], fringe: 'wisp', part: .5, grain: 1.3, points: .05 },
  bob: { thick: .072, line: [.20, -.01, -.225], fringe: 'blunt', part: .35, curtain: { end: -.44, back: -.58, flare: .13, spread: 1.95, gain: .16, curl: 1 } },
  long: { thick: .078, line: [.205, -.02, -.235], fringe: 'curtain', part: .7, frame: .82, curtain: { end: -1.02, back: -1.24, flare: .18, spread: 2.0, gain: .05 } },
  flow: { thick: .098, line: [.208, .015, -.222], fringe: 'curtain', sweep: .28, quiff: .35, frame: .62, curtain: { end: -.80, back: -.96, flare: .24, spread: 1.98, gain: .10, wave: 1 } },
  curls: { thick: .072, line: [.203, .015, -.212], curl: 1, clusters: 36, coil: .040 },
  afro: { thick: .135, line: [.198, .015, -.212], volume: .40, curl: 1.25, clusters: 58, coil: .045 },
  locs: { thick: .042, line: [.203, .005, -.218], strands: 'locs' },
  braids: { thick: .038, line: [.198, .025, -.218], strands: 'braids', fringe: 'blunt' },
  ponytail: { thick: .058, line: [.205, .015, -.212], pull: 1, grain: 1.8, tails: [0] },
  twin_tails: { thick: .058, line: [.203, .02, -.212], pull: .8, grain: 1.8, tails: [-1, 1], fringe: 'blunt' },
  bun: { thick: .056, line: [.205, .02, -.212], pull: 1, grain: 1.8, bun: true, fringe: 'wisp' },
}

// Hair is built around one scalp for every style. Broad connected surfaces set
// the silhouette; locks add direction. Owned geometry is disposed by the avatar
// renderer when the loadout changes.
export function buildAvatarHair(head, style, hair, band) {
  const cfg = STYLES[style] || STYLES.crop
  const [lineFront, lineSide, lineNape] = cfg.line
  const attach = (geometry, material = hair) => {
    const mesh = new THREE.Mesh(geometry, material)
    mesh.userData.ownedGeometry = true
    // Hair does not cast: a fringe standing a few millimetres off the brow threw
    // a hard black band across the face at this shadow-map resolution.
    head.add(mesh)
    return mesh
  }
  const finish = (vertices, indices, material) => {
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
    geometry.setIndex(indices)
    geometry.computeVertexNormals()
    return attach(geometry, material)
  }
  // Highest across the brow, lifted at the temple corners, falling to the ears
  // and the nape.
  const hairline = phi => {
    const front = Math.cos(phi), corner = .03 * Math.max(0, front) * Math.pow(Math.sin(2 * phi), 2)
    return (front >= 0 ? mix(lineSide, lineFront, ease(front)) : mix(lineSide, lineNape, ease(-front))) + corner
  }
  const point = (phi, index, lift = 0) => {
    const p = at(index), r = p.r + p.nr * lift
    return new THREE.Vector3(r * Math.sin(phi), p.y + p.ny * lift, r * DEPTH * Math.cos(phi))
  }
  // How far the cap stands off the skull, given a direction and a distance from
  // the crown. Shared by the scalp, the coils and the spikes, so nothing floats
  // above the surface it is meant to grow from.
  const liftAt = (phi, t) => {
    const dome = Math.sin(Math.PI * t)
    let lift = cfg.thick * (1 - .96 * ease(clamp((t - .6) / .4, 0, 1)))
    if (cfg.taper) lift *= 1 - cfg.taper * .92 * ease(clamp((t - .25) / .55, 0, 1)) * Math.pow(Math.abs(Math.sin(phi)), 1.4)
    if (cfg.volume) lift *= 1 + cfg.volume * dome
    if (cfg.quiff) lift *= 1 + cfg.quiff * Math.max(0, Math.cos(phi)) * dome * dome
    if (cfg.pull) lift *= 1 - .22 * cfg.pull * dome * Math.max(0, Math.cos(phi))
    return lift
  }
  const capPoint = (phi, t) => point(phi, indexAt(hairline(phi)) * t, liftAt(phi, t))
  // Sunflower placement keeps coils and spikes evenly spread over the cap
  // instead of ringing its edge.
  const spread = (i, count, reach) => [i * 2.3999 % TAU, Math.sqrt((i + .5) / count) * reach]
  // A two-sided surface with real thickness, used for every hanging mass.
  const shell = (columns, rows, fn, thick, material = hair) => {
    const points = [], normals = [], vertices = [], indices = []
    const index = (i, j) => i * (columns + 1) + j
    for (let i = 0; i <= rows; i++)
      for (let j = 0; j <= columns; j++) points.push(fn(j / columns, i / rows))
    for (let i = 0; i <= rows; i++)
      for (let j = 0; j <= columns; j++) {
        const u = points[index(i, Math.min(columns, j + 1))].clone().sub(points[index(i, Math.max(0, j - 1))])
        const v = points[index(Math.min(rows, i + 1), j)].clone().sub(points[index(Math.max(0, i - 1), j)])
        // v before u: the offset must run out of the head, not into it.
        const normal = v.cross(u)
        normals.push(normal.lengthSq() ? normal.normalize() : new THREE.Vector3(0, 0, 1))
      }
    const count = points.length
    for (let side = 0; side < 2; side++)
      for (let k = 0; k < count; k++) {
        const depth = typeof thick === 'function'
          ? thick((k % (columns + 1)) / columns, Math.floor(k / (columns + 1)) / rows) : thick
        const v = points[k].clone().addScaledVector(normals[k], (side ? -.5 : .5) * depth)
        vertices.push(v.x, v.y, v.z)
      }
    for (let i = 0; i < rows; i++)
      for (let j = 0; j < columns; j++) {
        const a = index(i, j), b = a + 1, c = a + columns + 1, d = c + 1
        indices.push(a, c, b, b, c, d, count + a, count + b, count + c, count + b, count + d, count + c)
      }
    const border = []
    for (let j = 0; j <= columns; j++) border.push(index(0, j))
    for (let i = 1; i <= rows; i++) border.push(index(i, columns))
    for (let j = columns - 1; j >= 0; j--) border.push(index(rows, j))
    for (let i = rows - 1; i >= 1; i--) border.push(index(i, 0))
    for (let k = 0; k < border.length; k++) {
      const a = border[k], b = border[(k + 1) % border.length]
      indices.push(a, b, count + b, a, count + b, count + a)
    }
    return finish(vertices, indices, material)
  }
  // Locks and coils accumulate into one buffer each: an afro was forty meshes.
  const locks = { vertices: [], indices: [] }
  const coils = { vertices: [], indices: [] }
  const coil = (centre, radius, squash = .9) => {
    const rings = 7, segments = 10, base = coils.vertices.length / 3
    for (let i = 0; i <= rings; i++)
      for (let j = 0; j <= segments; j++) {
        const theta = i / rings * Math.PI, phi = j / segments * TAU
        coils.vertices.push(centre.x + radius * Math.sin(theta) * Math.sin(phi),
          centre.y + radius * squash * Math.cos(theta), centre.z + radius * Math.sin(theta) * Math.cos(phi))
        if (i < rings && j < segments) {
          const n = base + i * (segments + 1) + j
          coils.indices.push(n, n + segments + 1, n + 1, n + 1, n + segments + 1, n + segments + 2)
        }
      }
  }
  // A tapered tube for locks, tails and spikes. Tips come to a point unless the
  // strand is a loc or a braid, which end blunt.
  const strand = (path, width, { taper = .3, rib = 0, blunt = 0, segments = 18, sides = 7 } = {}) => {
    const curve = new THREE.CatmullRomCurve3(path.map(p => new THREE.Vector3(...p)))
    const frames = curve.computeFrenetFrames(segments, false)
    const vertices = locks.vertices, indices = locks.indices, base = vertices.length / 3
    for (let i = 0; i <= segments; i++) {
      const t = i / segments, position = curve.getPointAt(t)
      const body = Math.pow(Math.sin(Math.PI * (.24 + .76 * t)), .5)
      const radius = width * (1 - taper * t) * Math.max(blunt * (1 - Math.pow(t, 8)), body)
        * (1 - rib + rib * Math.abs(Math.cos(t * Math.PI * 7)))
      for (let j = 0; j <= sides; j++) {
        const a = j / sides * TAU
        const v = position.clone().addScaledVector(frames.normals[i], Math.cos(a) * radius)
          .addScaledVector(frames.binormals[i], Math.sin(a) * radius)
        vertices.push(v.x, v.y, v.z)
        if (i < segments && j < sides) {
          const n = base + i * (sides + 1) + j
          indices.push(n, n + 1, n + sides + 1, n + 1, n + sides + 2, n + sides + 1)
        }
      }
    }
  }

  // --- Scalp -----------------------------------------------------------------
  // One closed cap, cut at the hairline and thinned into the skin there, so no
  // style ends in a shelf or a rim of shadow across the forehead.
  const rows = 26, columns = 72, vertices = [], indices = []
  const partPhi = -.55
  for (let i = 0; i <= rows + 1; i++)
    for (let j = 0; j < columns; j++) {
      const phi = j / columns * TAU, rim = i > rows, t = Math.min(i, rows) / rows
      const p = at(indexAt(hairline(phi)) * t)
      const dome = Math.pow(Math.sin(Math.PI * t), 1.6)
      const grain = (cfg.grain || 0) * .006 * Math.sin(phi * (cfg.grainN || 26) + t * 5) * dome
      const curl = (cfg.curl || 0) * .022 * Math.sin(phi * 13 + t * 4) * Math.sin(t * 16 + phi * 2) * dome
      const part = (cfg.part || 0) * -.034 * Math.exp(-Math.pow(Math.sin((phi - partPhi) / 2) / .12, 2))
        * (1 - ease(clamp((t - .45) / .5, 0, 1)))
      const lift = rim ? .001 : liftAt(phi, t) + grain + curl + part
      const radius = p.r + p.nr * lift
      vertices.push(radius * Math.sin(phi) + (cfg.sweep || 0) * .05 * dome, p.y + p.ny * lift, radius * DEPTH * Math.cos(phi))
      if (i <= rows) {
        const n = i * columns + j, right = i * columns + (j + 1) % columns
        indices.push(n, n + columns, right, right, n + columns, right + columns)
      }
    }
  finish(vertices, indices)

  // --- Fringe ----------------------------------------------------------------
  // Bangs are rooted under the cap and follow the forehead down, so they read as
  // their own mass without floating in front of the face or cutting the brows.
  const bangs = (kind, span) => {
    const shape = u => {
      const x = u * 2 - 1
      if (kind === 'blunt') return .118 + .018 * x * x
      if (kind === 'crop') return .148 + .020 * Math.abs(Math.sin(u * Math.PI * 5))
      if (kind === 'spike') return .142 + .034 * Math.pow(Math.abs(Math.sin(u * Math.PI * 5.5)), .7)
      if (kind === 'swept') return mix(.104, .198, ease(clamp(u * 1.2, 0, 1)))
      return mix(.198, .052, ease(Math.abs(x)))
    }
    shell(36, 9, (u, v) => {
      const skew = kind === 'swept' ? .34 : kind === 'curtain' ? .16 * Math.sign(u * 2 - 1) : 0
      const phi = (u * 2 - 1) * span + skew * v * v
      const top = hairline(phi) + .025
      const y = mix(top, Math.min(shape(u), top - .03), Math.pow(v, .85))
      const stand = .009 + (kind === 'curtain' ? .034 : .026) * v * (1 - .3 * v)
      const radius = Math.max(radiusAt(y), radiusAt(top)) + stand
      return new THREE.Vector3(radius * Math.sin(phi), y, radius * DEPTH * Math.cos(phi))
    }, (u, v) => .046 * (1 - .9 * v * v) * (1 - .45 * Math.pow(Math.abs(u * 2 - 1), 3)))
  }
  if (cfg.fringe === 'wisp') {
    for (let i = 0; i < 6; i++) {
      const phi = -1.05 + i * .42, top = hairline(phi) + .03, r = radiusAt(top)
      const drop = .112 + .026 * ((i * 3) % 4) / 3, tip = phi + .30
      strand([[r * Math.sin(phi), top, r * DEPTH * Math.cos(phi)],
        [(r + .012) * Math.sin(phi + .1), mix(top, drop, .5), (r + .012) * DEPTH * Math.cos(phi + .1)],
        [(r + .026) * Math.sin(tip), drop, (r + .026) * DEPTH * Math.cos(tip)]],
      .026, { taper: .55 })
    }
  } else if (cfg.fringe) bangs(cfg.fringe, cfg.fringe === 'curtain' ? 1.32 : 1.24)

  // --- Volume, texture and masses -------------------------------------------
  if (cfg.clusters) {
    // Coils sit on the cap surface and break its outline, so curls read as hair
    // rather than as a helmet with a bumpy finish.
    for (let i = 0; i < cfg.clusters; i++) {
      const [phi, t] = spread(i, cfg.clusters, .96)
      const size = cfg.coil * (.78 + .44 * ((i * 7) % 5) / 4)
      coil(capPoint(phi, t).multiplyScalar(1 + size * .3), size)
    }
  }
  if (cfg.spikes) {
    for (let i = 0; i < cfg.spikes; i++) {
      const [phi, t] = spread(i, cfg.spikes, .86)
      const base = capPoint(phi, t)
      const tip = base.clone().multiplyScalar(1.04)
      tip.y += .085 + .045 * ((i * 5) % 3) / 2
      tip.x += .035 * Math.sin(phi * 3)
      tip.z += .02
      strand([base.toArray(), base.clone().lerp(tip, .5).toArray(), tip.toArray()], .030, { taper: .6, segments: 10 })
    }
  }
  if (cfg.crest) {
    // A standing fin along the midline, with stubble shaved down both sides.
    shell(38, 6, (u, v) => {
      const forward = u < .5, t = forward ? 1 - u * 2 : u * 2 - 1
      const phi = forward ? 0 : Math.PI, along = forward ? .5 - t * .5 : .5 + t * .5
      const p = at(indexAt(hairline(phi)) * t)
      const height = .175 * Math.pow(Math.sin(Math.PI * along), .65) * (1 - .24 * Math.abs(Math.sin(along * Math.PI * 7)))
      const radius = p.r + p.nr * cfg.thick + height * v * p.nr * .18
      return new THREE.Vector3(0, p.y + p.ny * cfg.thick + height * v, radius * DEPTH * Math.cos(phi))
    }, (u, v) => .075 * (1 - .8 * v * v) * (1 - .55 * Math.pow(Math.abs(u * 2 - 1), 2)))
  }
  if (cfg.curtain) {
    // One connected curtain behind the head: separated strands would expose the
    // scalp from the side. It widens as it falls so the ends frame the jaw.
    const { end, back, flare, spread: arc, gain, wave = 0, curl = 0 } = cfg.curtain
    shell(52, 16, (u, v) => {
      const edge = Math.abs(u * 2 - 1), fall = ease(v)
      const phi = Math.PI + (u * 2 - 1) * (arc + gain * fall)
      // Rooted high and under the cap at the back, lower at the temples: a root
      // on the hairline left the crown sitting inside a collar of hair.
      const root = point(phi, indexAt(hairline(phi)) * mix(.82, .42, Math.max(0, -Math.cos(phi))), cfg.thick * .5)
      const hem = mix(back, end, ease(edge)) + (end - back) * .35 * Math.pow(edge, 4)
      const y = mix(root.y, hem, fall)
      const widen = 1 + flare * fall * fall * (1 - .5 * edge * edge) + wave * .04 * Math.sin(v * 7 + u * 5)
      // Never narrower than the skull it passes, so the head cannot push through.
      const radius = Math.max(Math.hypot(root.x, root.z / DEPTH), radiusAt(y) + .028) * widen
      const tuck = curl * .09 * Math.pow(fall, 3) * Math.max(0, -Math.cos(phi))
      return new THREE.Vector3(radius * Math.sin(phi), y, radius * DEPTH * Math.cos(phi) - tuck)
    }, (u, v) => (.018 + .075 * Math.sin(Math.PI * Math.pow(v, .65))) * (1 - .3 * Math.pow(Math.abs(u * 2 - 1), 4)))
  }
  if (cfg.frame) {
    for (const side of [-1, 1]) {
      const phi = side * 1.18, y = hairline(phi), r = radiusAt(y)
      strand([[r * Math.sin(phi), y, r * DEPTH * Math.cos(phi)],
        [r * 1.06 * Math.sin(phi), y - .34, r * .92 * DEPTH * Math.cos(phi)],
        [r * 1.14 * Math.sin(phi), y - .78 * cfg.frame, r * .62 * DEPTH * Math.cos(phi)]],
      .045, { taper: .55 })
    }
  }
  if (cfg.strands) {
    // Locs and braids hang from the crown backwards; the front arc stays clear
    // so nothing falls across the eyes.
    const braids = cfg.strands === 'braids', count = braids ? 13 : 17
    for (let i = 0; i < count; i++) {
      const phi = Math.PI + (i / (count - 1) * 2 - 1) * (braids ? 1.9 : 2.2)
      const line = indexAt(hairline(phi))
      const start = point(phi, line * .5, cfg.thick)
      const mid = point(phi, line, cfg.thick * 1.4)
      const reach = braids ? .62 : .5, drift = (i % 3 - 1) * .02
      strand([start.toArray(), mid.toArray(),
        [mid.x * 1.06 + drift, mid.y - reach * .45, mid.z * 1.02],
        [mid.x * 1.10 + drift, mid.y - reach, mid.z * .92]],
      braids ? .030 : .036, { taper: .35, blunt: .85, rib: braids ? .3 : .08 })
    }
  }
  if (cfg.tails) {
    const twin = cfg.tails.length > 1
    for (const side of cfg.tails) {
      const root = twin ? new THREE.Vector3(side * .25, .14, -.10) : new THREE.Vector3(0, .06, -.29)
      for (let j = 0; j < 4; j++) {
        const offset = (j - 1.5) * .036
        strand([root.toArray(),
          [root.x + (twin ? side * .09 : offset), root.y - .18, root.z - (twin ? .04 : -.02)],
          [root.x + (twin ? side * .15 : offset * 1.2), root.y - .46, root.z - (twin ? .07 : -.01)],
          [root.x + (twin ? side * .16 : offset * 1.1), root.y - .76 - .04 * (j % 2), root.z - (twin ? .06 : .05)]],
        .052, { taper: .45 })
      }
      const tie = attach(new THREE.TorusGeometry(.062, .017, 8, 22), band)
      tie.position.copy(root)
      tie.rotation.set(twin ? 0 : -.6, twin ? Math.PI / 2 : 0, 0)
    }
  }
  if (cfg.bun) {
    // A coiled rope, not a ball: the wrap is what makes it read as a bun.
    const centre = point(Math.PI, indexAt(.17), cfg.thick + .10)
    const knot = attach(new THREE.TorusGeometry(.10, .052, 12, 26))
    knot.position.copy(centre)
    knot.rotation.set(Math.PI / 2 - .3, 0, 0)
    knot.scale.set(1, 1, .82)
    for (let i = 0; i < 3; i++) {
      const a = i / 3 * TAU
      strand([[centre.x + Math.cos(a) * .105, centre.y + Math.sin(a) * .095, centre.z],
        [centre.x + Math.cos(a + 2) * .085, centre.y + Math.sin(a + 2) * .08, centre.z - .07],
        [centre.x + Math.cos(a + 4) * .105, centre.y + Math.sin(a + 4) * .095, centre.z]],
      .020, { taper: .1, blunt: .9 })
    }
    const tie = attach(new THREE.TorusGeometry(.072, .016, 8, 22), band)
    tie.position.set(centre.x, centre.y - .02, centre.z + .07)
    tie.rotation.set(Math.PI / 2 - .3, 0, 0)
  }
  if (coils.indices.length) finish(coils.vertices, coils.indices)
  if (cfg.points) {
    for (const side of [-1, 1]) {
      const phi = side * 1.62, y = hairline(phi), r = radiusAt(y)
      strand([[r * Math.sin(phi), y + .03, r * DEPTH * Math.cos(phi)],
        [r * .99 * Math.sin(phi), y - .06, r * .95 * DEPTH * Math.cos(phi) + .012],
        [r * .93 * Math.sin(phi), y - .14 - cfg.points, r * .84 * DEPTH * Math.cos(phi) + .025]],
      .026, { taper: .5 })
    }
  }
  if (locks.indices.length) finish(locks.vertices, locks.indices)
}
