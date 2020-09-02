/*global MathJax*/
/*eslint no-undef: "error"*/

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
  prefs.data.catsArr = [];
}

if (!prefs.data.hasOwnProperty("catsShowArr")) {
  prefs.data.catsShowArr = [];
}

if (!prefs.data.hasOwnProperty("showNov")) {
  prefs.data.showNov = [true, true, true];
}

prefs.save();
