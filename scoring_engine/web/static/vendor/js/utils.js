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

    /**
     * Initialize inline editable fields (Bootstrap 5 native replacement for x-editable)
     * @param {string} selector - jQuery selector for editable elements
     * @param {Object} options - Configuration options
     */
    function initInlineEdit(selector, options) {
        options = options || {};

        $(document).on('click', selector, function(e) {
            e.preventDefault();
            var $el = $(this);

            // Don't re-initialize if already editing
            if ($el.data('editing')) return;

            var currentValue = $el.text().trim();
            var pk = $el.data('pk');
            var name = $el.data('name');
            var url = $el.data('url');
            var title = $el.data('title') || 'Edit';

            // Mark as editing
            $el.data('editing', true);

            // Create input
            var $input = $('<input type="text" class="form-control form-control-sm d-inline-block" style="width: auto; min-width: 150px;">');
            $input.val(currentValue);

            // Store original content
            var originalHtml = $el.html();

            // Replace content with input
            $el.html($input);
            $input.focus().select();

            // Handle save
            function save() {
                var newValue = $input.val().trim();

                // Validate
                if (options.validate) {
                    var error = options.validate(newValue);
                    if (error) {
                        alert(error);
                        $input.focus();
                        return;
                    }
                }

                // Default validation
                var defaultError = validateTextField(newValue);
                if (defaultError) {
                    alert(defaultError);
                    $input.focus();
                    return;
                }

                // Submit
                $.ajax({
                    url: url,
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        pk: pk,
                        name: name,
                        value: newValue
                    }),
                    success: function(response) {
                        if (response.error) {
                            alert('Error: ' + response.error);
                            $el.html(originalHtml);
                        } else {
                            $el.text(newValue);
                            // Mask password fields
                            if (name === 'password') {
                                $el.text('************');
                            }
                        }
                        $el.data('editing', false);
                    },
                    error: function(xhr) {
                        var msg = 'Error saving';
                        try {
                            msg = xhr.responseJSON.error || xhr.responseJSON.status || msg;
                        } catch(e) {}
                        alert(msg);
                        $el.html(originalHtml);
                        $el.data('editing', false);
                    }
                });
            }

            // Handle cancel
            function cancel() {
                $el.html(originalHtml);
                $el.data('editing', false);
            }

            // Bind events
            $input.on('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    save();
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    cancel();
                }
            });

            $input.on('blur', function() {
                // Small delay to allow click events to fire first
                setTimeout(function() {
                    if ($el.data('editing')) {
                        save();
                    }
                }, 150);
            });
        });
    }

    // Public API
    return {
        validateTextField: validateTextField,
        validateDropdownField: validateDropdownField,
        editableSuccessHandler: editableSuccessHandler,
        sanitizeSelector: sanitizeSelector,
        initInlineEdit: initInlineEdit
    };
})();
