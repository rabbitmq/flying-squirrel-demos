function scroll() {
    $("body").scrollTop($("body").height() + 10000);
}

function write(msg) {
    $("#box").append( msg + '\n');
    scroll();
}

$(function () {
      // Focus on page load.
      $("#input").focus();

      // On click, anywhere, focus input box.
      $("html").click(function(){
                          scroll();
                          $("#input").focus();
                          return false;
                      });
});

$(function () {
      var opts = {debug: true};
      var conn = new flyingsquirrel.Connection(transport_url, ticket, opts);

      var to = null;
      var ping = function() {
          conn.publish('pipe', "\x00");
          to = setTimeout(ping, 5000);
      };

      conn.on_connect = function() {
          conn.egress_buffer = [];
          to = setTimeout(ping, 5000);
          conn.publish('pipe', 'hello');
          //write("Connected.");
      };
      conn.on_disconnect = function() {
          clearTimeout(to);
          to = null;
          write("Disconnected.");
      };

      // When user presses enter.
      $("#form").submit(function() {
                            var val = $("#input").val();
                            $("#input").val('');
                            conn.publish('pipe', val);
                            scroll();
                            clearTimeout(to);
                            to = setTimeout(ping, 5000);
                            return false;
                        });

      conn.subscribe('pipe', function(msg) {
                         if (msg != "\x00") {
                             write(msg);
                         }
                     });
      conn.connect();
  });

