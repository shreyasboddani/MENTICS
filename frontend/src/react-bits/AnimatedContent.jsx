// Adapted from React Bits AnimatedContent by David Haz. See LICENSE.md.
// IntersectionObserver keeps the GSAP reveal lightweight and content visible in SSR.
import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'

export function createContentReveal(element, {
  distance = 16, direction = 'vertical', reverse = false,
  duration = .55, ease = 'power3.out', initialOpacity = .3,
  delay = 0, threshold = .08, trigger = 'scroll'
} = {}) {
  let observer
  let played = false
  let context
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)')
  const play = () => {
    if (played || motion.matches) return
    played = true
    observer?.disconnect()
    const axis = direction === 'horizontal' ? 'x' : 'y'
    context = gsap.context(() => {
      gsap.fromTo(element,
        { [axis]: reverse ? -distance : distance, opacity: initialOpacity },
        { [axis]: 0, opacity: 1, duration, ease, delay, onComplete: () => context?.revert() }
      )
    })
  }
  const preferenceChanged = () => {
    if (motion.matches) { observer?.disconnect(); context?.revert() }
    else if (trigger === 'mount') play()
    else observer?.observe(element)
  }
  if (trigger === 'mount') play()
  else {
    observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) play()
    }, { threshold, rootMargin: '0px 0px -20px 0px' })
    if (!motion.matches) observer.observe(element)
  }
  motion.addEventListener('change', preferenceChanged)
  return () => {
    observer?.disconnect()
    context?.revert()
    motion.removeEventListener('change', preferenceChanged)
  }
}

export default function AnimatedContent({
  as: Component = 'div', children, distance = 16, direction = 'vertical',
  reverse = false, duration = .55, ease = 'power3.out', initialOpacity = .3,
  delay = 0, threshold = .08, trigger = 'scroll', ...props
}) {
  const ref = useRef(null)
  useEffect(() => createContentReveal(ref.current, {
    distance, direction, reverse, duration, ease, initialOpacity, delay, threshold, trigger
  }), [distance, direction, reverse, duration, ease, initialOpacity, delay, threshold, trigger])
  return <Component ref={ref} {...props}>{children}</Component>
}
