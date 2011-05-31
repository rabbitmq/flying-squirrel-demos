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

      conn.on_connect = function() {
          //write("Connected.");
      };
      conn.on_disconnect = function() {
          write("Disconnected.");
      };

      // When user presses enter.
      $("#form").submit(function() {
                            var val = $("#input").val();
                            $("#input").val('');
                            conn.publish('pipe', val);
                            scroll();
                            return false;
                        });

      conn.publish('pipe', 'aaa');
      conn.subscribe('pipe', function(msg) {
                         write(msg);
                     });
      conn.connect();
  });

