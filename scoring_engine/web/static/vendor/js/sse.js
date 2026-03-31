/**
 * ScoringEngineSSE — EventSource client with polling fallback.
 *
 * Usage:
 *   ScoringEngineSSE.on('round_complete', function(data) { refreshScoreboard(); });
 *   ScoringEngineSSE.connect();
 *
 * The client fetches a short-lived token from /api/events/token, then opens
 * an EventSource to /api/events?token=xxx. If the connection fails after
 * MAX_RETRIES, it falls back to firing all registered handlers every 30s.
 */
var ScoringEngineSSE = (function () {
  'use strict';

  var _source = null;
  var _handlers = {};
  var _fallbackInterval = null;
  var _connected = false;
  var _retryCount = 0;
  var MAX_RETRIES = 5;
  var POLL_INTERVAL = 30000;

  function connect() {
    $.getJSON('/api/events/token')
      .done(function (resp) {
        _openStream(resp.token);
      })
      .fail(function () {
        // Token endpoint unavailable — fall back to polling
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
      _retryCount = 0;
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
      _source.close();
      _source = null;
      _retryCount++;

      if (_retryCount <= MAX_RETRIES) {
        // Exponential backoff: 1s, 2s, 4s, 8s, 16s
        var delay = Math.pow(2, _retryCount - 1) * 1000;
        setTimeout(connect, delay);
      } else {
        _startPolling();
      }
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
