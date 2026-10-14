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
No npm dependencies are added.

Local adaptations update settings after commit, respond to live reduced-motion
preferences, disable click bursts for reduced motion, ignore touch magnet and
spotlight movement, and allow SpotlightCard's root
element to be selected with `as` (defaulting to `article`). Mentics keeps ownership
of the existing styling. CSS adds press feedback and progressive native page
transitions without delaying links or intercepting pointer events.
