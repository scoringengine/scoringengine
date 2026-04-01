/**
 * ScoringEngineSSE — EventSource client with polling fallback.
 *
 * Usage:
 *   ScoringEngineSSE.on('round_complete', function(data) { refreshScoreboard(); });
 *   ScoringEngineSSE.connect();
 */
var ScoringEngineSSE = (function () {
  'use strict';

  var _source = null;
  var _handlers = {};
  var _fallbackInterval = null;
  var _connected = false;
  var _everConnected = false;
  var _errorCount = 0;
  var POLL_INTERVAL = 30000;
  var MAX_ERRORS_BEFORE_FALLBACK = 10;

  function connect() {
    $.getJSON('/api/events/token')
      .done(function (resp) {
        _openStream(resp.token);
      })
      .fail(function () {
        _startPolling();
      });
  }

  function _openStream(token) {
    if (_source) {
      _source.close();
    }

    _source = new EventSource('/api/events?token=' + encodeURIComponent(token));

    _source.onopen = function () {
      _connected = true;
      _everConnected = true;
      _errorCount = 0;
      _stopPolling();
    };

    _source.onmessage = function (e) {
      try {
        var event = JSON.parse(e.data);
        var callbacks = _handlers[event.type] || [];
        for (var i = 0; i < callbacks.length; i++) {
          callbacks[i](event.data);
        }
      } catch (err) {
        // Ignore malformed events
      }
    };

    _source.onerror = function () {
      _connected = false;
      _errorCount++;

      // EventSource auto-reconnects natively. Only intervene if it's
      // consistently failing (never connected, or too many errors in a row).
      if (!_everConnected && _errorCount >= 3) {
        _source.close();
        _source = null;
        _startPolling();
      } else if (_errorCount >= MAX_ERRORS_BEFORE_FALLBACK) {
        _source.close();
        _source = null;
        // Re-fetch token and reconnect (token may have expired)
        setTimeout(connect, 5000);
        _errorCount = 0;
      }
      // Otherwise: let the browser's native EventSource retry handle it
    };
  }

  function on(eventType, callback) {
    if (!_handlers[eventType]) {
      _handlers[eventType] = [];
    }
    _handlers[eventType].push(callback);
  }

  function _startPolling() {
    if (_fallbackInterval) return;
    _fallbackInterval = setInterval(function () {
      for (var type in _handlers) {
        var callbacks = _handlers[type];
        for (var i = 0; i < callbacks.length; i++) {
          callbacks[i]({});
        }
      }
    }, POLL_INTERVAL);
  }

  function _stopPolling() {
    if (_fallbackInterval) {
      clearInterval(_fallbackInterval);
      _fallbackInterval = null;
    }
  }

  function isConnected() {
    return _connected;
  }

  return {
    connect: connect,
    on: on,
    isConnected: isConnected,
  };
})();
