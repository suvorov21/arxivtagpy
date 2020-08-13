if (loadData) {
  var DATA = [];
}

var showNov = [
  true,
  true,
  true
];

var sortMethod = "tag-as";

var showCats = {};

var loadAbs = true;

function alertLocalError(jqXHR) {
  $("#loadPapers").css("display", "None");
  var error = "</br></br>Flask server request processed with problems</br>";
  error += "Status: " + jqXHR.status + "</br></br>";

  error += "404 - Flask server is not running.</br>";
  error += "500 - Flask is up. arXiv API is not responding.</br>";
  error += "501 - Flask is up, arXiv is up, but response with no paper. Potentialy bad request to arXiv API.</br>";

  error += "</br>Troubleshooting:</br>";
  error += "404 Check if Flask app is running</br>";
  error += "500 Check if arXiv API is alive. Check request in a browser address bar</br>";
  error += "501 Check a logged request adress with a browser address bar</br>";
  $("#paper-list-content").html(error);
}

// toggle abstract visibility
$("#paper-list").on('click', function(e) {
  if (!$(e.target).hasClass("btn-abs")) {
    return true;
  }
  var num = $(e.target).attr("id").split("-")[2];
  var name =  "#abs-" + num;

  if (typeof $(name).html() === "undefined") {
    // create the div, parse TeX, then show
    var abs = document.createElement("div");
    abs.setAttribute("class", "paper-abs");
    abs.setAttribute("id", name.slice(1));
    abs.textContent = DATA.papers[parseInt(num, 10)].abstract;
    $("#paper-"+num).append(abs);
    if (parseTex) {
      MathJax.typeset();
    }
  }

  if ($(name).css("display") === "none") {
    $(name).css("display", "block");
  } else {
    $(name).css("display", "none");
  }
});

$(".item-nov").click(function() {
  var name =  "#check-nov-" + $(this).attr("id").split("-")[1];
  $(name).click();
});

$(".item-cat").click(function() {
  var name =  "#check-cat-" + $(this).attr("id").split("-")[2];
  $(name).click();
});

// Toggle visibility with checkboxes
function toggleVis() {
  $("#no-paper").css("display", "none");

  var passed = 0;
  var paperId = 0;
  for (paperId = 0; paperId < DATA.papers.length; paperId++) {
    var paper = DATA.papers[parseInt(paperId, 10)];
    var show = false;
    // 1st check by category
    for(var cat in showCats) {
      if (!showCats[cat]) {
        continue;
      }

      if (!showNov[1] && cat !== paper.cats[0]){
        continue;
      }

      var catId = 0;
      for (catId = 0; catId < paper.cats.length; catId++) {
        if (paper.cats[parseInt(catId, 10)] === cat && showCats[cat]) {
          show = true;
          break;
        }

      } // loop over all cats
      if (show) {
        break;
      }
    } // loop over paper cats

    if (!show) {
      $("#paper-"+paperId).css("display", "None");
      continue;
    }

    // 2nd check by novelty
    if (showNov[1] && paper["cross"] ||
        showNov[2] && paper["up"] ||
        showNov[0] && !paper["cross"] & !paper["up"]) {
      // BA DUM TSSS
      // don't want to invert logic, too lazy
    } else {
      show = false;
    }

    if (!show) {
      $("#paper-"+paperId).css("display", "None");
      continue;
    }

    // 3rd check by tag
    // TODO

    passed += 1;
    var title = $("#paper-title-"+paperId).html();
    var n = title.indexOf(".");
    $("#paper-title-"+paperId).html(passed + title.slice(n));
    $("#paper-"+paperId).css("display", "block");

  } // paper loop

  if (passed === 0) {
    $("#sort-block").css("display", "none");
    $("#no-paper").css("display", "block");
  } else {
    $("#no-paper").css("display", "none");
    $("#sort-block").css("display", "block");
    $("#passed").html(passed);
  }
}

// Toggle visibility with categories checks click
$(".check-cat").click(function() {
  var number = $(this).attr("id").split("-")[2];
  var cat = $("#cat-label-"+number).html();
  showCats[cat] = $("#check-cat-"+number).is(":checked");
  setTimeout(function () {
    toggleVis();
  }, 0);
});

// Toggle visibility with novelty checks click
$(".check-nov").click(function() {
  var number = $(this).attr("id").split("-")[2];
  showNov[parseInt(number, 10)] = $("#check-nov-"+number).is(":checked");
  setTimeout(function () {
    toggleVis();
  }, 0);
});

// read the category list
function readCats() {
  var result = $("#cats").find(".item-cat");
  if (result.length === 0) {
    return false;
  }

  var catId = 0;
  for (catId = 0; catId < result.length; catId++) {
    var key = result[parseInt(catId, 10)].innerHTML;
    showCats[key] = true;
  }
}

function displayCounters() {

  // setup caunters
  $("#nov-count-0").html(DATA.n_new);
  $("#nov-count-1").html(DATA.n_cross);
  $("#nov-count-2").html(DATA.n_up);

  DATA.n_tag.forEach(function(cat, num) {
    $("#tag-count-"+num).html(cat);
  });

  DATA.n_cat.forEach(function(cat, num) {
    $("#cat-count-"+num).html(cat);
  });
}

function sortPapers() {
  // tag increase
  if (sortMethod === "tag-as") {
    DATA.papers.sort(function(a, b) {
      if (b.tags.length === 0) {
        return -1;
      }
      if (a.tags.length === 0) {
        return 1;
      }
      return a.tags[0] - b.tags[0];
    });
  }
  // tag deacrease
  if (sortMethod === "tag-des") {
    DATA.papers.sort(function(a, b) {
      if (b.tags.length === 0) {
        return 1;
      }
      if (a.tags.length === 0) {
        return -1;
      }
      return b.tags[0] - a.tags[0];
    })
  }
  // date from most old
  if (sortMethod === "date-des") {
    DATA.papers.sort(function(a, b) {
      var aDate = new Date(a.date_up);
      var bDate = new Date(b.date_up);
      return aDate - bDate;
    })
  }
  // date from most recent
  if (sortMethod === "date-as") {
    DATA.papers.sort(function(a, b) {
      var aDate = new Date(a.date_up);
      var bDate = new Date(b.date_up);
      return bDate - aDate;
    })
  }
}

function displayPapers() {
  // parse papers
  $("#paper-list-content").html("");
  var content = "";
  DATA.papers.forEach(function(content, i) {
    var paper = document.createElement("div");
    paper.setAttribute("class", "paper");
    paper.setAttribute("id", "paper-"+i);

    var title = document.createElement("div");
    title.setAttribute("class", "paper-title");
    title.setAttribute("id", "paper-title-"+i);
    var str = (i+1) + ". " + content.title;
    title.textContent = str;

    var tagPanel = document.createElement("div");
    tagPanel.setAttribute("class", "tag-panel");
    var tags = [];
    content.tags.forEach(function(tag, tagId) {
      var tagDiv = document.createElement("div");
      tagDiv.setAttribute("class", "tag-panel-item");
      tagDiv.setAttribute("style", "background-color:" + DATA.tags[tag].color);
      tagDiv.textContent = DATA.tags[tag].name;
      tags.push(tagDiv);
    })

    var au = document.createElement("div");
    au.setAttribute("class", "paper-au");
    au.textContent += content.author.join(", ");

    var cat = document.createElement("div");
    cat.setAttribute("class", "paper-cat");
    cat.innerHTML = "[<strong>" + content.cats[0] + "</strong>";
    if (content.cats.length > 1) {
      cat.innerHTML += ", ";
    }
    cat.innerHTML += content.cats.slice(1).join(", ");
    cat.innerHTML += "]";

    var btnPanel = document.createElement("div");
    btnPanel.setAttribute("class", "btn-panel");

    var btnAbs = document.createElement("button");
    btnAbs.setAttribute("class", "btn btn-primary btn-abs");
    btnAbs.setAttribute("id", "btn-abs-"+i);
    btnAbs.textContent = "Abstract";

    var btnPdf = document.createElement("a");
    btnPdf.setAttribute("class", "btn btn-primary");
    btnPdf.setAttribute("id", "btn-pdf-"+i);
    btnPdf.setAttribute("href", content.pdf);
    btnPdf.setAttribute("target", "_blank");
    btnPdf.textContent = "PDF";

    var btnArxiv = document.createElement("a");
    btnArxiv.setAttribute("class", "btn btn-primary");
    btnArxiv.setAttribute("id", "btn-arxiv-"+i);
    btnArxiv.setAttribute("href", content.abs);
    btnArxiv.setAttribute("target", "_blank");
    btnArxiv.textContent = "arXiv";

    if (loadAbs) {
      var abs = document.createElement("div");
      abs.setAttribute("class", "paper-abs");
      abs.setAttribute("id", "abs-"+i);
      abs.textContent = content.abstract;
    }

    $("#paper-list-content").append(paper);
    paper.append(title);
    paper.append(tagPanel);
    tags.forEach(function(tag, i){
      tagPanel.append(tag);
    });
    if (tags.length === 0) {
      tagPanel.setAttribute("style", "display: none");
    }
    paper.append(au);
    paper.append(cat);
    paper.append(btnPanel);
    btnPanel.append(btnAbs);
    btnPanel.append(btnPdf);
    btnPanel.append(btnArxiv);
    if (loadAbs) {
      paper.append(abs);
    }
  })
  toggleVis();
  // parse LaTeX
  if (parseTex) {
    // WARNING
    // usually typeset() is working. It processes laTeX in ыумукфд threads --> fast
    // If there are dependencies (e.g. \newcommand{}) consequent typesetPromise() should be used.
    // MathJax.typeset();
    MathJax.typesetPromise();
  }
}

function loadPapers() {
  var url = document.location.href;
  var n = url.lastIndexOf("/");
  url = url.slice(0, n+1) + "data" + url.slice(n+1, url.length);

  $.get(url)
  .done(function(data) {
    $("#load_papers").css("display", "None");
    DATA = data;
    displayCounters();
    sortPapers();
    displayPapers();
    $("#sort-block").css("display", "block");
  }).fail(function(jqXHR){
    alertLocalError(jqXHR);
  });
}

$(".latex-rad").click(function() {
  window.location.href = "/set_tex?tex=" + $("input[type='radio'][name='tex']:checked").val();
})

$("#sort-sel").on("change", function() {
  sortMethod = $("#sort-sel").val();
  $("#sorting-proc").css("display", "block");
  sortPapers();
  // WARNING
  // dirty fix to throw displayPapers() in the separate thread
  // and not frise the selector
  setTimeout(function () {
    displayPapers();
    $("#sorting-proc").css("display", "none");
  }, 0);
})

// submit add category popup
$("#add-cat").click(function() {
  $(".cat-alert").html("");
  $("#add-cat-pop").css("display", "block");
})

// show cat rm popup
$("#rm-cat").click(function() {
  $("#rm-cat-select").html("");
  for (var cat in showCats) {
    var item = document.createElement("option");
    item.setAttribute("value", cat);
    item.setAttribute("style", "font-size: 1.1rem");
    item.textContent = cat;
    $("#rm-cat-select").append(item);
  }
  $("#rm-cat-pop").css("display", "block");
})

$(".btn-cancel").click(function() {
  $("#add-cat-pop").css("display", "none");
  $("#rm-cat-pop").css("display", "none");
  $("#add-tag-pop").css("display", "none");
  $("#edit-tag-pop").css("display", "none");
})

// submit adding category
// go through few checks
$("#btn-add-cat").click(function() {
  $(".cat-alert").html("");
  var cat = $("#cat-name").val();
  if (cat === "") {
    $(".cat-alert").html("Empty category!");
    return false;
  }

  if (cat in showCats) {
    $(".cat-alert").html("Category already added!");
    return false;
  }

  var url = "http://export.arxiv.org/api/query?search_query=cat:"+cat;
  $.get(url)
  .done(function(data) {
    if ($(data).find("entry").length === 0) {
      $(".cat-alert").html("arXiv response with error for this category!");
    } else {
      window.location.href = "/add_cat?fcat="+cat;
    }
  }).fail(function(jqXHR) {
    alertLocalError(jqXHR);
  });
});

// show add tag popup
$("#add-tag").click(function() {
  $(".cat-alert").html("");
  $("#add-tag-pop").css("display", "block");
})

$("#edit-tag").click(function() {
  $(".cat-alert").html("");
  $("#edit-tag-select").html("");
  DATA.tags.forEach(function(tag, id) {
    var item = document.createElement("option");
    item.setAttribute("value", id);
    item.setAttribute("style", "font-size: 1.1rem");
    item.textContent = tag.name;
    $("#edit-tag-select").append(item);
  })
  document.forms["edit-tag"]["tag_name"].value = DATA.tags[0].name;
  document.forms["edit-tag"]["tag_rule"].value = DATA.tags[0].rule;
  document.forms["edit-tag"]["tag_color"].value = DATA.tags[0].color;
  document.forms["edit-tag"]["tag_order"].value = 0;
  $("#edit-tag-pop").css("display", "block");
})

$("#edit-tag-select").change(function() {
  var tagId = $("#edit-tag-select").prop("selectedIndex");
  document.forms["edit-tag"]["tag_name"].value = DATA.tags[parseInt(tagId, 10)].name;
  document.forms["edit-tag"]["tag_rule"].value = DATA.tags[parseInt(tagId, 10)].rule;
  document.forms["edit-tag"]["tag_color"].value = DATA.tags[parseInt(tagId, 10)].color;
  document.forms["edit-tag"]["tag_order"].value = tagId;
})

function validateTagForm(str) {
  var formName = str + "-tag";
  $(".cat-alert").html("");

  // check all fields filled
  var tagId = $("#edit-tag-select").prop("selectedIndex");
  if (document.forms[formName]["tag_name"].value === "" ||
      document.forms[formName]["tag_rule"].value === "" ||
      document.forms[formName]["tag_color"].value === "" ||
      document.forms[formName]["tag_order"].value === "") {
    $(".cat-alert").html("Fill all the fields in the form!");
    return false;
  }

  // check if already exists
  var exists = false;
  DATA.tags.forEach(function(tag, id) {
    if (str === "add") {
      if (document.forms[formName]["tag_name"].value === tag["name"]) {
        exists = true;
      }
    } else {
      if (document.forms[formName]["tag_name"].value === tag["name"] && tagId !== id) {
        $(".cat-alert").html("Already exists");
        exists = true;
      }
    }
  })

  if (exists) {
    $(".cat-alert").html("Already exists");
    return false;
  }

  // check rule
  if (!/^(ti|au|abs){.*?}((\||\&)(\(|)((ti|au|abs){.*?})(\)|))*$/i.test(document.forms[formName]["tag_rule"].value)) {
    $(".cat-alert").html("Check the rule syntax!");
    return false;
  }

  // check color
  if (!/^#[0-9A-F]{6}$/i.test(document.forms[formName]["tag_color"].value)) {
    $(".cat-alert").html("Color should be in hex format: e.g. #aaaaaa");
    return false;
  }

  // check order
  if (!/[0-9]/i.test(document.forms[formName]["tag_order"].value)) {
    $(".cat-alert").html("Order should be an integer");
    return false;
  }

  // document.forms[formName]["tag_rule"].value = document.forms[formName]["tag_rule"].value.replace(/([^\\])\\([^\\])/i, "$1\\\\$2");

  $(".cat-alert").html("");
  return true;
}

$(document).ready(function() {
  $("input[type='radio'][value=" + (parseTex ? 'on' : 'off') + "]").prop('checked', true);
  readCats();
  if (loadData) {
    loadPapers()
  } else {
    $("#sort-block").css("display", "block");
    displayCounters();
    sortPapers();
    displayPapers();
  }
});

// safety check
// if (typeof jQuery === undefined) {
//   alert("jQuery load fail");
// }
// else {
//   console.log("jQuery Ok");
// }
