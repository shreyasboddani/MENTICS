// Server-provided bootstrap data.
//
// On the client this comes from the inline __MENTICS__ script Flask writes into
// the page. During prerendering there is no window, so the server entry calls
// setBoot() to supply the page being rendered. Components read `boot.page` and
// `boot.data` at render time rather than destructuring at module scope, so both
// paths see the right values.
const initial =
  typeof window !== 'undefined' && window.__MENTICS__
    ? window.__MENTICS__
    : { page: 'landing', data: {} }

export const boot = {
  page: initial.page || 'landing',
  data: initial.data || {}
}

export function setBoot(next) {
  boot.page = (next && next.page) || 'landing'
  boot.data = (next && next.data) || {}
}
