/**
 * Shared JavaScript utilities for the Scoring Engine application
 */

// Common validation functions for editable fields
var ScoringEngineUtils = (function() {
    'use strict';

    /**
     * Validates text field input for editable fields
     * Checks for empty values, leading/trailing spaces, and invalid characters
     * @param {string} value - The value to validate
     * @returns {string|undefined} - Error message if validation fails, undefined if valid
     */
    function validateTextField(value) {
        if ($.trim(value) == '') {
            return 'This field is required';
        }
        if (value.startsWith(" ") || value.endsWith(" ")) {
            return "Input cannot start or end with a space";
        }
        if (/^[A-Za-z0-9\.,@=:\/\-\|\(\)\^$; !]+$/.test(value) == false) {
            return "Invalid characters detected in input. Allowed characters are AlphaNumeric and any of . , @ = : / - | ( ) ^ $ ; space !";
        }
    }

    /**
     * Validates dropdown/select field input
     * Checks for empty values
     * @param {string} value - The value to validate
     * @returns {string|undefined} - Error message if validation fails, undefined if valid
     */
    function validateDropdownField(value) {
        if ($.trim(value) == '') {
            return 'This field is required';
        }
    }

    /**
     * Standard success handler for editable field updates
     * @param {Object} response - The response from the server
     * @returns {string|undefined} - Error message if response contains error, undefined otherwise
     */
    function editableSuccessHandler(response) {
        if (response.error) {
            return "Unable to update value due to error: " + response.error;
        }
    }

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
        validateTextField: validateTextField,
        validateDropdownField: validateDropdownField,
        editableSuccessHandler: editableSuccessHandler,
        sanitizeSelector: sanitizeSelector
    };
})();
