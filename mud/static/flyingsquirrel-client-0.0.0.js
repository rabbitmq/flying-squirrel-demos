/* Requires socket.io:

 <script type="text/javascript"
         src="http://cdn.socket.io/stable/socket.io.js"></script>

 * Basic usage:

    var protocol_url = "{{ protocol_url }}";
    var ticket = "{{ ticket }}";
    var connection = new flyingsquirrel.Connection(protocol_url, ticket);

    connection.on_connect = function () {};

    connection.subscribe('channel', function (msg) {});
    connection.publish('channel', value),

    connection.connect();

 */
/*
 * Socket.io reconnection strategy is completely crazy, we will
 * implement our own, with exponential backoff.
 */

var flyingsquirrel;
if (this.flyingsquirrel === undefined) {
    flyingsquirrel = this.flyingsquirrel = {};
}
flyingsquirrel.client_version = '0.0.1';

if (!'io' in this) {
    if ('console' in window) {console.error('socket.io is missing');}
}
if (!'JSON' in this) {
    if ('console' in window) {console.error('JSON is missing');}
}


(function() {
     var getLocation = function(href) {
         var l = document.createElement("a");
         l.href = href;
         return l;
     };

     var fix_socket_opts = function (options, loc) {
         var socket_opts = (options && options.socket_opts) || {};
         socket_opts.secure = (loc.protocol === "https:");
         socket_opts.port = (loc.port || undefined);
         socket_opts.resource = loc.pathname.replace( /^\//g, '');
         socket_opts.reconnect = false;
         socket_opts.timeout = null;
         socket_opts.maxReconnectionAttempts = 0;
         socket_opts.rememberTransport = false;
         socket_opts.tryTransportsOnConnectTimeout = false;
         if (socket_opts.transports === undefined) {
             socket_opts.transports = ['websocket', 'xhr-polling'];
         }
         return socket_opts;
     };

     var flyingsquirrel = this.flyingsquirrel;

     flyingsquirrel.Connection = function (protocol_url, ticket, options) {
	 var that = this;
         this.uid = (''+Math.random()).substr(2, 8);
         this.state = 'disconnected';
         this.reconnect_timeout = undefined;
         this.ticket = ticket;

         if (options && options.debug && 'console' in window) {
             this.debug = function (l) {
                 console.log(that.uid + '/' + that.state + ':\t' + l);
             };
         } else {
             this.debug = function (l) {};
         }

         var loc = getLocation(protocol_url);
         var socket_opts = fix_socket_opts(options, loc);

         this.debug('new io.Socket("' + loc.hostname + '", ' +
                     JSON.stringify(socket_opts) + ');');
	 this.socket = new io.Socket(loc.hostname, socket_opts);
         // if (options && options.debug && 'console' in window) {
	 //     this.socket.on('connect', function() {
         //                        console.log("Socket.io: on_connect");
         //                    });
	 //     this.socket.on('disconnect', function() {
         //                        console.log("Socket.io: on_disconnect");
         //                    });
	 //     this.socket.on('messsage', function() {
         //                        console.log("Socket.io: on_message");
         //                    });
         // }
         this._reset_callbacks();
         this.socket.on('connect', function() {that._on_connect();});
         this.socket.on('disconnect', function() {that._on_disconnect();});
         this.socket.on('message', function(msg) {that._on_message(msg);});

         this.socket.on('connecting', function() {
                            that.debug('Socket.io: connecting');
                        });
         this.socket.on('connect_fail', function() {
                            that.debug('Socket.io: connect_fail');
                        });
         this.socket.on('reconnect', function() {
                            that.debug('Socket.io: reconnect');
                        });
         this.socket.on('reconnecting', function() {
                            that.debug('Socket.io: reconnecting');
                        });
         this.socket.on('reconnecting_failed', function() {
                            that.debug('Socket.io: reconnecting_failed');
                        });

	 this.egress_buffer = [];
	 this.channels = {};
     };

     flyingsquirrel.Connection.prototype = {
         // **** public api ****
	 'publish': function(channel, body) {
	     var raw_message = JSON.stringify({channel:channel, body:body});
             this._send(raw_message);
	 },
	 'subscribe': function(channel, callback) {
	     this.channels[channel] = callback;
	 },
         'request': function(channel, question, callback) {
             var self = this;
             var waiting = true;
             self.subscribe(channel, function(answer, channel, msgobj) {
                 if (waiting) {
                     waiting = false;
                     callback(answer, channel, msgobj);
                 }
                 else {
                     self._error_and_close('unexpected reply');
                 }
             });
             this.publish(channel, question);
         },
         'serve': function(channel, callback) {
             var self = this;
             self.subscribe(channel, function(msg, channel, msgobj) {
                 var replyto = msgobj['reply-to'];
                 callback(msg, channel, msgobj, function(answer) {
                     self._send(JSON.stringify(
                         {'channel': channel, 'reply-to': replyto, 'body': answer}));
                 });
             });
         },
	 'connect': function() {
             if (this.state === 'disconnected') {
                 this.debug('connect()');
                 this.reconnect_delay = 100;
                 this._next('_state_connecting', 'user');
                 return true;
             } else {
                 return false;
             }
         },
	 'disconnect': function() {
             this.debug('disconnect()');
             if (this.reconnect_timeout) {
                 window.clearTimeout(this.reconnect_timeout);
                 this.reconnect_timeout = undefined;
             }
             this._reset_callbacks();
             // TODO: this may actually not work correctly
             this.debug("socket.disconnect()");
             this.socket.disconnect();
             this._next('_state_disconnected', 'user');
             return true;
	 },

         // **** private stuff (message) ****
	 '_deliver_message': function(msg) {
	     if (msg.channel in this.channels) {
		 this.channels[msg.channel](msg.body, msg.channel, msg);
	     } else {
                 if (msg['error-code']) {
                     this._error_and_close(msg['error-code']);
                 }
                 this.debug("Undelivered: " + JSON.stringify(msg));
             }
	 },
         '_send': function(raw) {
	     this.egress_buffer.push(raw);
             if (this.state === 'connected') {
	         this._flush_egress();
             }
         },

	 '_flush_egress': function() {
	     while (this.egress_buffer.length > 0) {
                 var raw_msg = this.egress_buffer.shift();
		 this.socket.send(raw_msg);
	     }
	 },

         '_error_and_close': function(error) {
             this.debug("Error: " + error);
             this.debug("socket.disconnect()");
             this.socket.disconnect();
             this._next('_state_disconnected', 'error', error);
         },

         // **** private stuff (state) ****
         '_reset_callbacks': function () {
             var that = this;
             this._on_message = function (raw_msg) {
                 that.debug("Invalid on_message");
             };
             this._on_connect = function () {
                 that.debug("Invalid on_connect");
             };
             this._on_disconnect = function () {
                 that.debug("Invalid on_disconnect");
             };
         },
         '_next': function (state, reason, descr) {
             this.debug(" -> " + state + '('+reason+')');
             this.state = state;
             this._reset_callbacks();
             this[state](reason, descr);
         },

	 '_state_disconnected': function (reason, message) {
             this.state = 'disconnected';
             if (this.on_disconnect) {
                 this.on_disconnect(this, reason, message);
             }
	 },

         '_state_connecting': function (reason) {
             var that = this;
             this._on_connect = function () {
                 that._next('_state_handshake', reason);
	     };
             this._on_disconnect = function () {
                 that._next('_state_retry');
             };
             this.debug("socket.connect()");
	     this.socket.connect();
         },
         '_state_handshake': function (reason) {
             var that = this;
             this._on_message = function (raw_message) {
                 var msg = JSON.parse(raw_message);
                 if (msg.connect === 'ok') {
                     that._next('_state_connected', reason);
                 } else {
                     this.debug("socket.disconnect()");
                     that.socket.disconnect();
                     that._next('_state_disconnected', 'refused',
                                msg['error-code']);
                 }
             };
             this._on_disconnect = function () {
                 // Server crashed during handshake.
                 that.socket.disconnect();
                 that._next('_state_disconnected', 'refused');
             };
             this.socket.send(JSON.stringify({connect:this.ticket}));
         },
         '_state_connected': function (reason) {
             var that = this;
             this._on_message = function (raw_message) {
                 var msg = JSON.parse(raw_message);
	         that._deliver_message(msg);
             };
             this._on_disconnect = function (raw_message) {
                 that._next('_state_retry');
             };

             this.state = 'connected';
             if (this.on_connect && reason === 'user') {
                 // Not for reconnects.
                 this.on_connect(this, 'success');
             }
             that.reconnect_delay = 100;
             this._flush_egress();
         },
         '_state_retry': function () {
             var that = this;
             this.socket.disconnect();
	     if (this.reconnect_delay > 10000) {
                 this._next('_state_disconnected', 'timeout');
             } else {
                 this.debug("Reconnecting in " + that.reconnect_delay);
                 this.reconnect_timeout =
                     window.setTimeout(function () {
                                           that.reconnect_timeout = undefined;
                                           that._next('_state_connecting', 'reconnect');
                                       },
				       that.reconnect_delay);
                 this.reconnect_delay *= 2;
             }
         }
     };
 })();
