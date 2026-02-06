/**
 * Shared JavaScript utilities for the Scoring Engine application
 */

var ScoringEngineUtils = (function() {
    'use strict';

    /**
     * Sanitize string for use in jQuery selectors
     * Escapes special characters that have meaning in CSS selectors
     * @param {string} str - The string to sanitize
     * @returns {string} - Sanitized string safe for use in selectors
     */
    function sanitizeSelector(str) {
        return str.replace(/[!"#$%&'()*+,.\/:;<=>?@[\\\]^`{|}~]/g, '\\$&');
    }

    /**
     * Animate a numeric counter from previous value to target value.
     * Skips animation if the value hasn't changed.
     * @param {HTMLElement} el - The element to animate
     * @param {number} target - The target number
     * @param {number} duration - Animation duration in ms (default 800)
     */
    function animateCounter(el, target, duration) {
        duration = duration || 800;
        target = parseInt(target) || 0;
        var prev = el._counterPrev;
        if (prev !== undefined && prev === target) return;
        var from = (prev !== undefined) ? prev : 0;
        el._counterPrev = target;
        var startTime = null;
        function step(ts) {
            if (!startTime) startTime = ts;
            var p = Math.min((ts - startTime) / duration, 1);
            el.textContent = Math.floor(from + (target - from) * p).toLocaleString();
            if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    /**
     * Set text content only if the value has changed.
     * @param {HTMLElement} el - The element to update
     * @param {string} text - The new text content
     */
    function setText(el, text) {
        if (el.textContent !== text) el.textContent = text;
    }

    // Public API
    return {
        sanitizeSelector: sanitizeSelector,
        animateCounter: animateCounter,
        setText: setText
    };
})();
