var prefs = {

  data: {},

  load(name="prefs") {
    let cookieDecoded = decodeURIComponent(document.cookie).split(";");
    let cname = name + "=";
    for (let i = 0; i < cookieDecoded.length; i++) {
      let cook = cookieDecoded[parseInt(i, 10)];
      while (cook[0] === " ") {
        cook = cook.slice(1);
      }
      if (cook.indexOf(cname) === 0) {
        this.data = JSON.parse(cook.substring(cname.length, cook.length));
      }
    }

    return this.data;
  },

  save(expires, path) {
    var d = expires || new Date(2100, 2, 2);
    var p = path || "/";
    document.cookie = "prefs=" + encodeURIComponent(JSON.stringify(this.data))
              + ";expires=" + d.toUTCString()
              + ";path=" + p;
  }
};

prefs.load();

if (!prefs.data.hasOwnProperty("catsArr")) {
  prefs.data.catsArr = {};
}

if (!prefs.data.hasOwnProperty("showNov")) {
  prefs.data.showNov = [true, true, true];
}

prefs.save();

// ************************** UTILS ********************************************
function raiseAlert(text="Text", type="alert") {
  let parent = document.createElement("div");
  parent.setAttribute("class", "alert alert-dismissible fade show alert-" + type);
  parent.setAttribute("role", "alert");

  let content = document.createElement("span");
  content.textContent = text;

  let close = document.createElement("button");
  close.setAttribute("class", "close");
  close.setAttribute("data-dismiss", "alert");
  close.setAttribute("aria-label", "Close");

  let time = document.createElement("span");
  time.innerHTML = "&times;";

  document.getElementById("inner-message").appendChild(parent);
  parent.appendChild(content);
  parent.appendChild(close);
  close.appendChild(time);

  setTimeout(function() {
    $(".alert").alert("close");
  } , 3000);
}

$(function() {
  $("#feedback-tab").click(function() {
    $("#feedback-form").toggle("slide");
  });

  $("#feedback-form form").on("submit", function(event) {
    var $form = $(this);
    $.ajax({
      type: $form.attr("method"),
      url: $form.attr("action"),
      data: $form.serialize(),
      success: function() {
        $("#feedback-form").toggle("slide").find("textarea").val("");
        raiseAlert("Thank you for your feedback!", "success");
      }
    });
    event.preventDefault();
  });
});
