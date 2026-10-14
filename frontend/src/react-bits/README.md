# React Bits interactions

ClickSpark, Magnet, and SpotlightCard are vendored from the JavaScript/CSS
variants of [React Bits](https://github.com/DavidHDev/react-bits), retrieved
October 14, 2026. The upstream license is included in LICENSE.md.

ClickSpark provides a brief violet burst on pointer and keyboard activation
across every route, including portals. Its wrapper uses `display: contents`
and a fixed, non-interactive effect layer so existing layout stays intact.
Magnet adds a small spring movement to homepage actions and public/product
navigation anchors. SpotlightCard decorates the five existing suite articles.
Original copy, controls, routes, colors, and article semantics are preserved.
These three interactions do not add npm dependencies.

Local adaptations update settings after commit, respond to live reduced-motion
preferences, disable click bursts for reduced motion, ignore touch magnet and
spotlight movement, and allow SpotlightCard's root
element to be selected with `as` (defaulting to `article`). Mentics keeps ownership
of the existing styling. CSS adds press feedback and progressive native page
transitions without delaying links or intercepting pointer events.

AnimatedContent is adapted from `src/content/Animations/AnimatedContent/AnimatedContent.jsx`.
It uses GSAP for the original directional fade animation, with IntersectionObserver
in place of ScrollTrigger. It preserves visible server-rendered content and
existing inline styles, respects live reduced-motion changes, and supports an
`as` tag and mount trigger. `useFluidExperience` applies the same reveal to existing
page blocks and auth fields without inserting layout wrappers. The auth artwork
uses the component directly. AnimatedContent adds only the GSAP dependency.

The mobile menu keeps its backdrop mounted so both entrance and exit complete,
staggers existing links, morphs its toggle icon, and supports Escape with focus
return. Closed navigation remains hidden and non-interactive. CSS feedback for
forms, buttons, and icons uses the existing palette.

GlareHover is vendored from `src/content/Animations/GlareHover/GlareHover.jsx`
and `.css`; it provides directional light sweeps on homepage actions and login
buttons. Its root supports `as` and native anchor/button props. Mentics keeps
control of button geometry and backgrounds; overlays do not intercept clicks.
Live reduced-motion changes stop the sweep, and touch hover is ignored.

SplitText is vendored from `src/content/TextAnimations/SplitText/SplitText.jsx`.
It uses GSAP SplitText, ScrollTrigger, and the `@gsap/react` hook for word reveals
on the method heading, auth heading, and shared page introductions. Text remains
visible in server markup, semantic heading tags are kept, splitting waits for
fonts, and reduced-motion users receive ordinary text. The original text and
palette are preserved. `@gsap/react` is added alongside the existing GSAP dependency.

ShinyText is vendored from `src/content/TextAnimations/ShinyText/ShinyText.jsx`
and `.css`. It sweeps a lavender highlight over the existing white closing
heading once when it enters view, then restores the original white. Settings
are synchronized after commit and live reduced-motion changes cancel the shine.

CountUp, DecryptedText, and StarBorder are vendored from their corresponding
`src/content/TextAnimations` and `src/content/Animations` JavaScript variants.
CountUp animates saved points, streaks, and achievements; server markup contains
the actual final value. Academic scores and timers remain ordinary numbers.
DecryptedText adds a brief hover reveal to page-intro labels; assistive text stays
stable. Both use the official `motion` dependency and respect reduced motion.
StarBorder outlines the path launcher and closing action, preserving native
button/link semantics, geometry, and backgrounds. Its settings and reduced-motion
preference update live. Existing dashboard articles now use SpotlightCard too.
