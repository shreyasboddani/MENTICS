import { useEffect } from 'react'
import { createContentReveal } from './AnimatedContent'

const contentTargets = [
  '.landing-facts > div', '.section-heading', '.process-grid article',
  '.signal-story-intro', '.signal-story-beats article', '.journey-showcase-copy',
  '.platform-copy', '.feature-stack > div', '.battle-landing-copy',
  '.suite-heading', '.suite-grid article', '.week-heading', '.week-flow article',
  '.faq details', '.closing > div',
  '.app-main > :not(.chat-panel):not(.modal-wrap):not(.floating-chat):not(.roadmap)',
  '.onboarding-page main > form > section.active'
].join(',')

export function useFluidExperience(page) {
  useEffect(() => {
    const disposers = [...document.querySelectorAll(contentTargets)].map((element, index) =>
      createContentReveal(element, { delay: Math.min(index % 3, 2) * .045 })
    )
    // Animate existing form rows without adding wrappers or changing form semantics.
    const authTargets = document.querySelectorAll('.auth-panel > *, .auth-panel form > label, .auth-panel form > button')
    authTargets.forEach((element, index) => {
      // The form itself stays stationary while its fields enter individually.
      if (element.tagName !== 'FORM') disposers.push(createContentReveal(element, {
        trigger: 'mount', distance: 12, duration: .48, delay: Math.min(index, 7) * .035
      }))
    })
    const onboarding = document.querySelector('.onboarding-page main > form')
    const stepObserver = onboarding ? new MutationObserver(records => {
      for (const record of records) {
        const element = record.target
        if (element.matches('section.active')) disposers.push(createContentReveal(element, {
          trigger: 'mount', duration: .4, distance: 10
        }))
      }
    }) : null
    if (onboarding) stepObserver.observe(onboarding, { subtree: true, attributes: true, attributeFilter: ['class'] })
    return () => { stepObserver?.disconnect(); disposers.forEach(dispose => dispose()) }
  }, [page])
}
