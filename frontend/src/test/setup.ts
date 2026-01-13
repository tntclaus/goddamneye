/**
 * Vitest test setup file.
 *
 * This file runs before each test file and sets up:
 * - jest-dom matchers for DOM assertions
 * - Common mocks for browser APIs
 */

import '@testing-library/jest-dom'

// Mock window.matchMedia for Ant Design components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Mock ResizeObserver for Ant Design components
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock scrollTo
window.scrollTo = () => {}

// Mock getComputedStyle for Ant Design animations
const originalGetComputedStyle = window.getComputedStyle
window.getComputedStyle = (elt: Element, pseudoElt?: string | null) => {
  const style = originalGetComputedStyle(elt, pseudoElt)
  // Return a proxy that handles missing properties
  return new Proxy(style, {
    get(target, prop) {
      if (prop === 'getPropertyValue') {
        return (name: string) => target.getPropertyValue(name) || ''
      }
      return target[prop as keyof CSSStyleDeclaration] || ''
    },
  })
}
