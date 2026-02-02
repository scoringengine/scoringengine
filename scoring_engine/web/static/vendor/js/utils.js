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

    // Public API
    return {
        sanitizeSelector: sanitizeSelector
    };
})();
