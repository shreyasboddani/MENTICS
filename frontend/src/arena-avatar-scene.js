import * as THREE from 'three'
import { buildAvatarHair, HEAD_PROFILE } from './arena-avatar-hair'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'
import { ARENA_AVATAR_PALETTES, ARENA_AVATAR_SKINS, ARENA_AVATAR_HAIR, ARENA_AVATAR_ACCENTS, ARENA_AVATAR_EYES, normalizeArenaAvatar } from './arena-fighter'

// Procedural, texture-free wardrobe. Shared geometry and a single, capped-DPR
// canvas keep loadouts small; every accessory is attached to anatomical anchors.
export function createAvatarScene(host, initial, onFailure) {
  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5))
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.05
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFShadowMap
  host.appendChild(renderer.domElement)
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(32, 1, .1, 30)
  camera.position.set(0, 1.85, 5.3)
  camera.lookAt(0, 1.46, 0)
  scene.add(new THREE.HemisphereLight('#d7e2ff', '#2c3050', 1.35))
  for (const [color, power, x, y, z] of [['#fff2df', 3.8, -3, 5, 4], ['#d3c9ef', 2.5, 3, 3, -2]]) {
    const light = new THREE.DirectionalLight(color, power)
    light.position.set(x, y, z)
    if (z > 0) {
      light.castShadow = true
      light.shadow.mapSize.set(1024, 1024)
      Object.assign(light.shadow.camera, { left: -2, right: 2, top: 4, bottom: -1, near: .1, far: 12 })
      light.shadow.bias = -.001
      light.shadow.normalBias = .025
    }
    scene.add(light)
  }
  const shapes = {
    ball: new THREE.SphereGeometry(1, 24, 16),
    box: new THREE.BoxGeometry(1, 1, 1),
    rounded: new RoundedBoxGeometry(1, 1, 1, 3, .16),
    capsule: new THREE.CapsuleGeometry(1, 2, 6, 16),
    cone: new THREE.ConeGeometry(1, 1, 12),
    cylinder: new THREE.CylinderGeometry(1, 1, 1, 24),
    ring: new THREE.TorusGeometry(1, .07, 8, 40),
  }
  const pedestalMaterial = new THREE.MeshStandardMaterial({ color: '#20232f', roughness: .8, metalness: .15 })
  const pedestal = new THREE.Mesh(shapes.cylinder, pedestalMaterial)
  pedestal.scale.set(1.02, .035, .78); pedestal.position.y = .045; pedestal.receiveShadow = true; scene.add(pedestal)
  // Layered translucent ellipses give a soft contact shadow without a shadow-map pass.
  const shadowMaterials = []
  const shadowGeometry = new THREE.CircleGeometry(1, 48)
  for (let i = 0; i < 5; i++) {
    const mat = new THREE.MeshBasicMaterial({ color: '#080918', transparent: true, opacity: .075, depthWrite: false })
    shadowMaterials.push(mat)
    const mesh = new THREE.Mesh(shadowGeometry, mat)
    mesh.rotation.x = -Math.PI / 2; mesh.scale.set(.34 + i * .055, .26 + i * .03, 1)
    mesh.position.set(0, .062 + i * .0001, 0); scene.add(mesh)
  }
  let fighter, materials = [], disposed = false, frame = 0, visible = true, paused = false, last = 0
  let targetAngle = -.20, angle = -.20, drag = null, view = 'full'
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)')
  function setAvatar(value) {
    const a = normalizeArenaAvatar(value)
    if (fighter) scene.remove(fighter)
    materials.forEach(m => m.dispose()); materials = []
    fighter = new THREE.Group(); scene.add(fighter)
    const [primary, dark] = ARENA_AVATAR_PALETTES[a.palette]
    const material = (color, metalness = 0) => {
      const m = new THREE.MeshStandardMaterial({ color, roughness: metalness ? .36 : .7, metalness })
      materials.push(m); return m
    }
    const skin = material(ARENA_AVATAR_SKINS[a.skin][0])
    const cloth = material(new THREE.Color(primary).lerp(new THREE.Color('#77768a'), .24))
    const pants = material(new THREE.Color(dark).lerp(new THREE.Color('#161c28'), .94))
    const trim = material(ARENA_AVATAR_ACCENTS[a.accent], .25), hair = material(ARENA_AVATAR_HAIR[a.hair_color])
    // Hair keeps a faint sheen, and its thin shells are lit from both faces.
    Object.assign(hair, { roughness: .52, side: THREE.DoubleSide })
    const white = material('#f4f4fb'), ink = material('#171724'), eye = material(ARENA_AVATAR_EYES[a.eyes])
    function part(shape, mat, pos, scale, parent = fighter, rotation = 0) {
      const mesh = new THREE.Mesh(shapes[shape], mat)
      mesh.castShadow = true
      mesh.position.set(...pos); mesh.scale.set(...scale); mesh.rotation.z = rotation
      parent.add(mesh); return mesh
    }
    const ball = (mat, pos, scale, parent, rotation) => part('ball', mat, pos, scale, parent, rotation)
    const box = (mat, pos, scale, parent, rotation) => part('box', mat, pos, scale, parent, rotation)
    const capsule = (mat, pos, scale, parent, rotation) => part('capsule', mat, pos, scale, parent, rotation)
    function sculpt(mat, profile, position, scale, parent = fighter) {
      const geometry = new THREE.LatheGeometry(profile.map(([x,y]) => new THREE.Vector2(x,y)), 32)
      const mesh = new THREE.Mesh(geometry, mat)
      mesh.castShadow = true
      mesh.userData.ownedGeometry = true
      mesh.position.set(...position); mesh.scale.set(...scale); parent.add(mesh)
      return mesh
    }
    const build = { striker: 1, sentinel: 1.13, scout: .86, titan: 1.23, lithe: .82, compact: 1.07 }[a.body]
    const width = build * ({ masculine: 1, feminine: .89, androgynous: .95, athletic: 1.08 }[a.frame])
    fighter.scale.y = { short: .92, average: 1, tall: 1.07 }[a.height]
    const torso = new THREE.Group(); torso.position.y = 1.37; fighter.add(torso)
    const soft = ['hoodie', 'street', 'varsity', 'scholar'].includes(a.outfit)
    sculpt(cloth, [[0,-.04],[.22,-.04],[.26,0],[.265,.10],[.28,.25],[.32,.43],[.34,.60],[.31,.68],[.23,.74],[.13,.78],[0,.78]], [0,0,0], [width,1,.68], torso)
    sculpt(pants, [[0,-.14],[.21,-.14],[.27,-.07],[.27,.07],[.23,.12],[0,.12]], [0,-.035,0], [width,1,.69], torso)
    if (['combat', 'champion', 'techwear'].includes(a.outfit)) {
      box(pants, [0, .41, .232], [.014, .43, .012], torso)
      box(trim, [0, .56, .243], [.024, .05, .012], torso)
    } else if (['academy', 'scholar'].includes(a.outfit)) {
      for (const side of [-1, 1]) box(white, [side * .08, .65, .17], [.09, .20, .035], torso, side * -.4)
      box(trim, [0, .52, .23], [.045, .2, .025], torso)
    } else if (a.outfit === 'jersey') {
      box(white, [0, .43, .225], [.11, .2, .02], torso)
    } else if (a.outfit === 'flight') {
      box(trim, [.18, .44, .22], [.1, .11, .025], torso)
    }
    if (soft) {
      ball(cloth, [0, .77, -.03], [.26, .13, .24], torso)
      for (const side of [-1, 1]) box(trim, [side * .07, .58, .23], [.018, .18, .018], torso)
    }
    // Distinct crest silhouettes, mounted flush to the upper chest.
    const crest = { bolt: 'box', mind: 'ball', target: 'ring', shield: 'cone', star: 'cone', flame: 'ball', crown: 'box', atom: 'ring', book: 'box', wave: 'ring' }[a.emblem]
    part(crest, trim, [-.12 * width, .56, .235], [.055, .055, .02], torso, a.emblem === 'bolt' ? -.45 : 0)
    if (a.marking !== 'none') {
      const count = { stripes: 2, circuit: 3, chevron: 2, stars: 3, scales: 4 }[a.marking]
      for (let i = 0; i < count; i++) box(trim, [.16, .35 - i * .075, .22], [.1, .018, .025], torso, a.marking === 'chevron' ? .5 : 0)
    }
    const robe = a.outfit === 'scholar'
    const skirted = robe || ['battle_skirt', 'pleated'].includes(a.bottom)
    for (const side of [-1, 1]) {
      const legX = side * .16 * width
      const shorts = a.bottom === 'shorts'
      if (shorts) {
        sculpt(pants, [[0,0],[.10,0],[.105,.10],[.12,.26],[.135,.43],[.145,.55],[.12,.61],[0,.62]], [legX,.73,0], [build,1,1.02])
        sculpt(skin, [[0,0],[.08,0],[.085,.13],[.11,.29],[.115,.42],[.10,.53],[0,.54]], [legX + side * .015,.25,.01], [build,1,1.02])
      } else {
        sculpt(pants, [[0,0],[.085,0],[.09,.12],[.115,.30],[.108,.48],[.12,.65],[.14,.9],[.14,1.04],[.10,1.10],[0,1.12]], [legX,.25,0], [build,1,1.02])
      }
      if (!skirted && (a.bottom === 'cargo' || a.bottom === 'tactical')) part('rounded', pants, [legX + side * .09, 1.04, .105], [.10, .19, .075])
      if (a.bottom === 'joggers') ball(cloth, [legX + side * .025, .34, .02], [.11 * build, .06, .12])
      const foot = a.footwear === 'barefoot' ? skin : pants
      const tallBoot = ['boots', 'armored', 'greaves'].includes(a.footwear)
      ball(foot, [legX + side * .025, .17, .10], [.14 * build, .11, .24])
      if (a.footwear !== 'barefoot') {
        part('rounded', white, [legX + side * .025, .095, .105], [.265 * build, .045, .44])
        capsule(foot, [legX + side * .025, tallBoot ? .27 : .23, .02], [.105 * build, tallBoot ? .07 : .03, .105])
        for (let j=0;j<3;j++) box(trim, [legX + side * .025,.245,.15+j*.045], [.14,.012,.02])
      }
      const arm = new THREE.Group(); arm.position.set(side * .35 * width, 2.02, 0)
      arm.rotation.z = side * (a.pose === 'confident' ? .31 : a.pose === 'relaxed' ? .08 : .18)
      if (a.pose === 'guard') arm.rotation.x = -.45
      fighter.add(arm)
      sculpt(a.outfit === 'jersey' ? skin : cloth, [[0,-.37],[.085,-.37],[.095,-.29],[.125,-.13],[.14,-.01],[.10,.07],[0,.10]], [side * .025,0,0], [build,1,1], arm)
      sculpt(a.outfit === 'jersey' ? skin : cloth, [[0,-.66],[.072,-.66],[.08,-.58],[.10,-.43],[.09,-.33],[0,-.31]], [side * .03,0,.015], [build,1,1], arm)
      ball(a.gloves === 'none' ? skin : pants, [side * .04, -.70, .045], [.105 * build, .13, .10], arm)
      if (a.gloves !== 'none') {
        ball(trim, [side * .04, -.61, .05], [.107 * build, a.gloves === 'gauntlets' ? .13 : .04, .105], arm)
        if (a.gloves === 'fingerless') ball(skin, [side * .04, -.77, .075], [.08, .045, .08], arm)
        if (a.gloves === 'claws') for (let j = 0; j < 3; j++) part('cone', trim, [side * .04 + (j - 1) * .04, -.84, .10], [.015, .12, .015], arm, Math.PI)
      }
      if (['pauldrons', 'epaulettes', 'spikes'].includes(a.shoulder)) {
        ball(trim, [0, -.04, 0], [.17 * build, .11, .17], arm)
        if (a.shoulder === 'spikes') for (let j = 0; j < 3; j++) part('cone', trim, [(j - 1) * .10, .09, 0], [.035, .18, .035], arm)
      }
    }
    // Skirts are closed volumes lathed from a hip-to-hem curve. A cone would
    // pinch to a point at the waist and leave the hips bare above it; folds are
    // modulated into the surface so trim rides the cloth instead of floating in
    // front of it, and the open hem is walled so legs pass through a garment
    // rather than a lid.
    function drape(mat, shape, from = 0, to = 1, swell = 0) {
      const { top, hem, waist, flare, folds, amp, depth, sharp } = shape
      const rows = 14, columns = folds > 10 ? 120 : 72, rings = rows * 2 + 2
      const vertices = [], indices = []
      for (let i = 0; i < rings; i++) {
        const outer = i <= rows
        const v = from + (to - from) * ((outer ? i : rings - 1 - i) / rows)
        const radius = waist + flare * Math.pow(v, 1.55)
        for (let j = 0; j <= columns; j++) {
          const phi = j / columns * Math.PI * 2
          const fold = sharp ? Math.abs((phi / (Math.PI * 2) * folds % 1) * 2 - 1) * 2 - 1 : Math.cos(phi * folds)
          const r = radius * (1 + amp * fold * (.25 + .75 * v)) + swell - (outer ? 0 : .022)
          vertices.push(r * Math.sin(phi), top + (hem - top) * v, r * depth * Math.cos(phi))
        }
      }
      for (let i = 0; i < rings; i++) {
        const a = i * (columns + 1), b = (i + 1) % rings * (columns + 1)
        for (let j = 0; j < columns; j++) indices.push(a + j, b + j, a + j + 1, a + j + 1, b + j, b + j + 1)
      }
      const geometry = new THREE.BufferGeometry()
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
      geometry.setIndex(indices); geometry.computeVertexNormals()
      const mesh = new THREE.Mesh(geometry, mat)
      mesh.castShadow = true; mesh.userData.ownedGeometry = true
      fighter.add(mesh); return mesh
    }
    if (skirted) {
      const pleated = !robe && a.bottom === 'pleated'
      const shape = robe ? { top: 1.35, hem: .40, waist: .30 * width, flare: .17 * width, folds: 7, amp: .035, depth: .84 }
        : pleated ? { top: 1.345, hem: .845, waist: .275 * width, flare: .20 * width, folds: 20, amp: .055, depth: .80, sharp: true }
          : { top: 1.35, hem: .875, waist: .285 * width, flare: .175 * width, folds: 8, amp: .030, depth: .82 }
      drape(cloth, shape)
      if (!robe) {
        drape(trim, shape, pleated ? .93 : .90, 1, .008)
        if (!pleated) drape(trim, shape, 0, .07, .010)
      }
    }
    if (a.shoulder === 'sash') box(trim, [0, .42, .25], [.07, .73, .02], torso, -.55)
    if (a.waist !== 'none') {
      if (a.waist === 'wrap') ball(trim, [0, 1.30, 0], [.32 * width, .15, .23])
      else if (a.waist === 'chain') { const ring = part('ring', trim, [0, 1.34, .1], [.30 * width, .1, .20]); ring.rotation.x = Math.PI / 2 }
      else for (const side of a.waist === 'holsters' ? [-1, 1] : [1]) box(pants, [side * .3 * width, 1.27, .1], [.14, .22, .14])
    }
    // Head and hair share an anchor; headwear bounds suppress only covered hair.
    ball(skin, [0, 2.15, 0], [.12, .17, .12])
    const head = new THREE.Group(); head.position.y = 2.43; head.scale.set(.88,.94,.92); fighter.add(head)
    sculpt(skin, HEAD_PROFILE, [0,0,0], [1,1,.91], head)
    for (const side of [-1, 1]) {
      ball(skin, [side * .29, -.02, 0], [.055, .10, .06], head)
      ball(white, [side * .105, .015, .242], [.057, .032, .022], head)
      ball(eye, [side * .105, .015, .262], [.024, .026, .009], head)
      ball(ink, [side * .105, .015, .271], [.012, .018, .006], head)
      ball(white, [side * .098, .025, .277], [.006, .007, .004], head)
      box(hair, [side * .11, .09, .247], [.12, a.brows === 'bold' ? .035 : .022, .025], head,
        side * ({ soft: 0, bold: -.1, arched: .2, sharp: -.25 }[a.brows]))
    }
    ball(skin, [0, -.055, .275], [.034, .045, .032], head)
    const lip = material(ARENA_AVATAR_SKINS[a.skin][1])
    ball(a.expression === 'grin' ? white : lip, [0, -.16, .230], [a.expression === 'grin' ? .10 : .075, a.expression === 'grin' ? .026 : .012, .012], head)
    if (a.face !== 'natural') {
      for (const side of [-1, 1]) {
        if (a.face === 'freckles') for (let i = 0; i < 3; i++) ball(lip, [side * (.12 + i * .025), -.07 + (i % 2) * .02, .238], [.008, .008, .005], head)
        else box(['cyber', 'warpaint', 'tattoo'].includes(a.face) ? trim : lip, [side * .17, -.065, .23], [a.face === 'blush' ? .06 : .017, a.face === 'blush' ? .025 : .10, .015], head, side * -.4)
      }
    }
    if (a.facial_hair !== 'none') {
      if (['full', 'stubble', 'goatee'].includes(a.facial_hair)) ball(hair, [0, -.25, .17], [a.facial_hair === 'goatee' ? .065 : .20, a.facial_hair === 'full' ? .13 : .07, .095], head)
      if (['full', 'mustache'].includes(a.facial_hair)) ball(hair, [0, -.12, .267], [.11, .023, .023], head)
    }
    const covered = ['helmet', 'cap'].includes(a.gear)
    if (!covered) buildAvatarHair(head, a.hair, hair, trim)
    switch (a.gear) {
      case 'visor': case 'shades': case 'glasses':
        for (const side of [-1, 1]) {
          ball(a.gear === 'glasses' ? trim : ink, [side * .115, .035, .277], [.095, .060, .034], head)
          if (a.gear === 'glasses') ball(white, [side * .115, .035, .306], [.069, .041, .007], head)
          box(trim, [side * .235, .045, .13], [.03, .025, .30], head)
        }
        box(trim, [0, .035, .30], [.055, .025, .02], head); break
      case 'helmet':
        ball(pants, [0, .19, -.04], [.34, .25, .29], head)
        for (const side of [-1, 1]) ball(cloth, [side * .30, -.015, -.01], [.075, .23, .24], head)
        box(trim, [0, .19, .25], [.42, .04, .055], head); break
      case 'cap':
        ball(cloth, [0, .26, -.02], [.32, .14, .28], head)
        ball(pants, [0, .18, .27], [.33, .025, .22], head); break
      case 'crown':
        for (let i = -2; i <= 2; i++) part('cone', trim, [i * .11, .40, .09], [.07, .20, .07], head)
        box(trim, [0, .31, .16], [.50, .06, .09], head); break
      case 'comms':
        ball(pants, [-.32, 0, 0], [.065, .12, .1], head)
        box(trim, [-.23, -.12, .16], [.20, .025, .03], head, -.3); break
      case 'headband': box(trim, [0, .17, .243], [.46, .055, .045], head); break
      case 'earrings':
        for (const side of [-1, 1]) part('ring', trim, [side * .30, -.12, .025], [.045, .06, .045], head); break
      case 'mask': ball(pants, [0, -.135, .24], [.20, .095, .06], head); break
    }
    if (a.back !== 'none') {
      if (['cape', 'half_cape', 'banner'].includes(a.back)) {
        box(pants, [a.back === 'half_cape' ? -.16 : 0, 1.47, -.29], [a.back === 'half_cape' ? .32 : .64, a.back === 'banner' ? 1.15 : 1.05, .06], fighter, -.06)
        box(trim, [0, 1.6, -.33], [.1, .5, .018])
      } else if (a.back === 'wings') {
        for (const side of [-1, 1]) for (let i = 0; i < 4; i++) ball(trim, [side * (.40 + i * .13), 1.9 + i * .12, -.22], [.10, .43 - i * .05, .055], fighter, side * -.65)
      } else {
        box(pants, [0, 1.77, -.28], [.40, .5, .22])
        for (const side of [-1, 1]) ball(a.back === 'quiver' ? pants : trim, [side * .16, 1.8, -.38], [.075, a.back === 'quiver' ? .4 : .24, .09])
      }
    }
    if (a.aura !== 'none') {
      const ring = part('ring', trim, [0, a.aura === 'halo' ? 2.98 : .10, 0], [a.aura === 'halo' ? .4 : .71, a.aura === 'halo' ? .4 : .6, .3])
      ring.rotation.x = Math.PI / 2
      if (['spark', 'embers', 'frost', 'storm'].includes(a.aura)) for (let i = 0; i < 5; i++) part('ball', trim, [Math.cos(i * 2.4) * .65, .3 + i * .32, -.25], [.025, .035, .025])
    }
    updateCamera()
    invalidate()
  }
  function updateCamera() {
    const portrait = view === 'portrait'
    const height = fighter?.scale.y || 1
    camera.position.set(0, portrait ? 2.42 * height : 1.85, portrait ? 2.5 : 5.3)
    camera.lookAt(0, portrait ? 2.29 * height : 1.46, 0)
  }
  function render(time = 0) {
    frame = 0
    if (disposed || !visible || document.hidden || paused) return
    if (time - last >= 32 || reduced.matches) {
      last = time
      angle += (targetAngle - angle) * (reduced.matches ? 1 : .2)
      fighter.rotation.y = angle
      fighter.position.y = reduced.matches ? 0 : Math.sin(time * .0013) * .008
      renderer.render(scene, camera)
    }
    if (!reduced.matches || Math.abs(targetAngle - angle) > .001) frame = requestAnimationFrame(render)
  }
  function invalidate() { if (!frame && !disposed) frame = requestAnimationFrame(render) }
  const resize = new ResizeObserver(() => {
    const { width, height } = host.getBoundingClientRect()
    if (!width || !height) return
    renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix(); invalidate()
  })
  const intersection = new IntersectionObserver(entries => { visible = entries[0].isIntersecting; invalidate() })
  const resume = () => invalidate()
  const down = e => { if (e.button !== 0) return; drag = { id: e.pointerId, x: e.clientX }; host.setPointerCapture(e.pointerId) }
  const move = e => { if (!drag || drag.id !== e.pointerId) return; targetAngle += (e.clientX - drag.x) * .012; drag.x = e.clientX; invalidate() }
  const up = () => { drag = null }
  const lost = e => { e.preventDefault(); paused = true; onFailure() }
  resize.observe(host); intersection.observe(host)
  document.addEventListener('visibilitychange', resume); reduced.addEventListener('change', resume)
  host.addEventListener('pointerdown', down); host.addEventListener('pointermove', move)
  host.addEventListener('pointerup', up); host.addEventListener('pointercancel', up)
  renderer.domElement.addEventListener('webglcontextlost', lost)
  setAvatar(initial)
  function disposeOwned(group) { group?.traverse(obj => { if (obj.userData.ownedGeometry) obj.geometry.dispose() }) }
  return {
    setAvatar(value) { disposeOwned(fighter); setAvatar(value) },
    turn(amount) { targetAngle += amount; invalidate() },
    setView(value) { view = value; updateCamera(); invalidate() },
    setPaused(value) { paused = value; invalidate() },
    dispose() {
      disposed = true; cancelAnimationFrame(frame); resize.disconnect(); intersection.disconnect()
      document.removeEventListener('visibilitychange', resume); reduced.removeEventListener('change', resume)
      host.removeEventListener('pointerdown', down); host.removeEventListener('pointermove', move)
      host.removeEventListener('pointerup', up); host.removeEventListener('pointercancel', up)
      renderer.domElement.removeEventListener('webglcontextlost', lost)
      disposeOwned(fighter); Object.values(shapes).forEach(g => g.dispose()); shadowGeometry.dispose()
      materials.forEach(m => m.dispose()); shadowMaterials.forEach(m => m.dispose()); pedestalMaterial.dispose()
      renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove()
    },
  }
}
