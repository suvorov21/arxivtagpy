var catNew = [];

// ************************  RENDERS *******************************************
function addCat(cat) {
  // Dots replace with 111 to be a legal
  // name for JS elements
  // TODO proper escape dot with \\.
  let parent = document.createElement("div");
  parent.setAttribute("class", "d-flex");
  parent.setAttribute("id", "par-cat-"+cat.replaceAll(".", "111"))

  let close = document.createElement("button");
  close.setAttribute("id", "close_"+cat.replaceAll(".", "111"));
  close.setAttribute("class", "close close-btn");
  close.innerHTML = "&times"

  close.onclick = function(event) {
    let name = event.target.getAttribute("id").split("_")[1]
    $("#par-cat-" + name).removeClass("d-flex");
    $("#par-cat-" + name).fadeOut();
    $(".btn").removeClass("disabled");
    const catId = catNew.indexOf(name.replace("111", "."));
    if (catId > -1) {
      catNew.splice(catId, 1);
    }
  }

  let catElement = document.createElement("div");
  catElement.setAttribute("class", "pl-2");
  catElement.textContent = allCatsArray[cat];

  document.getElementById("cats-list").appendChild(parent);
  parent.appendChild(close);
  parent.appendChild(catElement);
}

function renderCats() {
  $("#cats-list").empty();
  catNew = [];
  CATS.forEach((cat, num) => {
    // TODO consider moving function inline?
    addCat(cat);
    catNew.push(cat);
  });
}

function renderTags() {
  $("#tag-list").empty();
  TAGS.forEach((tag, num) => {
    let tagElement = document.createElement("div");
    tagElement.setAttribute("class", "tag-label");
    tagElement.setAttribute("id", "tag-label-"+num);
    tagElement.setAttribute("style", "background-color: " + tag.color);
    tagElement.textContent = tag.name;
    document.getElementById("tag-list").appendChild(tagElement);
  });
  if (parseTex) {
    MathJax.typesetPromise();
  }
  // new tag button
  let tagElement = document.createElement("div");
  tagElement.setAttribute("class", "add-set tag-label");
  tagElement.setAttribute("id", "add-tag");
  tagElement.textContent = "New";

  document.getElementById("tag-list").appendChild(tagElement);
}

function renderPref() {
 return;
}

function reloadSettings() {
  if (CATS !== catNew) {
    renderCats();
  }
  renderTags();
  document.forms["add-tag"]["tag_name"].value = "";
  document.forms["add-tag"]["tag_rule"].value = "";
  document.forms["add-tag"]["tag_color"].value = "";
  document.forms["add-tag"]["tag_order"].value = "";

  renderPref();
}

window.onload = function(event) {
  $.each(allCatsArray, function(val, text) {
    $("#catsDataList").append($("<option>").attr("value", val).text(text));
  });

  reloadSettings()
}

// ******************** CATEGORIES *********************************************
function fillCatForm() {
  if ($(".btn-cancel").hasClass("disabled")) {
    return false;
  }
  let hiddenText = document.createElement("input");
  hiddenText.setAttribute("type", "text");
  hiddenText.setAttribute("name", "catNew");
  hiddenText.setAttribute("style", "display: none;");
  hiddenText.value = catNew.toString();

  document.forms["mod-cat"].appendChild(hiddenText);
  return true;
}

$("#add-cat-btn").click((event) => {
  cat = document.forms["add-cat"]["cat_name"].value;
  // check if already there
  if (catNew.includes(cat)) {
    alert("Catagory already added!");
    return;
  }
  // check if legal category
  if (allCatsArray[cat] === undefined) {
    alert("Unknown category");
    return;
  }
  $(".btn-save").removeClass("disabled");
  addCat(document.forms["add-cat"]["cat_name"].value);
  document.forms["add-cat"]["cat_name"].value = "";
  // add to array
  catNew.push(cat);
});

$(".btn-cancel").click((event) => {
  if (!$(".btn-cancel").hasClass("disabled")) {
    location.reload();
  }
});

// ****************** TAGS *****************************************************
$("#show-rules").click((event) => {
  if ($("#tag-help").css("display") === "block") {
    $("#tag-help").css("display", "none");
  } else {
    $("#tag-help").css("display", "block");
  }
});

var newTag = true;
var editTagId = -1;

$("#tag-list").click((event) => {
  // consider only tag labels click
  if (!$(event.target).attr("class").includes("tag-label")) {
    return;
  }
  // make delete possible
  $("#btn-del").removeClass("disabled");
  // check if settings were modified
  if (!$(".btn-cancel").hasClass("disabled")) {
    if (confirm("Settings will not be saved. Continue?")) {
      $(".btn-save").addClass("disabled");
      event.preventDefault();
    } else {
      event.preventDefault();
      return;
    }
  }
  // highlight the editting tag
  let tagCol = document.getElementsByClassName("tag-label");
  for (let id = 0; id < tagCol.length; id++) {
    $("#tag-label-"+parseInt(id, 10)).css("border-color", "transparent");
    if ($(tagCol[parseInt(id, 10)]).attr("id") === "add-tag") {
      $("#add-tag").css("border-style", "dashed");
      $("#add-tag").css("border-width", "2px");
    }
  }

  if ($(event.target).attr("id") === "add-tag") {
    // WARNING
    newTag = true;

    $("#btn-reset").click();
    $("#add-tag").css("border-style", "solid");
    $("#add-tag").css("border-width", "4px");
    document.forms["add-tag"]["tag_name"].value = "";
    document.forms["add-tag"]["tag_rule"].value = "";
    document.forms["add-tag"]["tag_color"].value = "";
    document.forms["add-tag"]["tag_order"].value = "";
  } else {
    // WARNING
    newTag = false;

    editTagId = $(event.target).attr("id").split("-")[2];
    let tag = TAGS[parseInt(editTagId, 10)];

    $(event.target).css("border-color", "#000");

    $("#tag-fields").prop("disabled", false);
    document.forms["add-tag"]["tag_name"].value = tag.name;
    document.forms["add-tag"]["tag_rule"].value = tag.rule;
    document.forms["add-tag"]["tag_color"].value = tag.color;
    document.forms["add-tag"]["tag_order"].value = editTagId;
    $("#tag-color").css("background-color", $("#tag-color").val());
  }
  $("#tag-fields").prop("disabled", false);
});

$(".tag-field").on("input", function(event) {
  $(".btn-save").removeClass("disabled");
});

$("#tag-color").on("change", function(event) {
  $("#tag-color").css("background-color", $("#tag-color").val());
  $(".btn-save").removeClass("disabled");
});

function fillTagForm() {
  if ($(".btn-cancel").hasClass("disabled")) {
    return false;
  }
  return checkTag();
}

function submitTag() {
  let url = "mod_tag";
  $.post(url, JSON.stringify(TAGS))
  .done(function(data) {
    reloadSettings();
    $(".btn-save").addClass("disabled");
    $("#btn-del").addClass("disabled");
  }).fail(function(jqXHR){
    alert(jqXHR);
  });
}

function checkTag() {
  $(".cat-alert").html("");

  // check all fields are filled
  if (document.forms["add-tag"]["tag_name"].value === "" ||
      document.forms["add-tag"]["tag_rule"].value === "" ||
      document.forms["add-tag"]["tag_color"].value === "" ||
      document.forms["add-tag"]["tag_order"].value === "") {
    $(".cat-alert").html("Fill all the fields in the form!");
    return false;
  }

  // check rule
  let rule = document.forms["add-tag"]["tag_rule"].value;
  if (!/^(ti|au|abs){.*?}((\||\&)(\(|)((ti|au|abs){.*?})(\)|))*$/i.test(rule)) {
    $(".cat-alert").html("Check the rule syntax!");
    return false;
  }

  // check color
  if (!/^#[0-9A-F]{6}$/i.test(document.forms["add-tag"]["tag_color"].value)) {
    $(".cat-alert").html("Color should be in hex format: e.g. #aaaaaa");
    return false;
  }

  // check order
  if (!/^[0-9]/i.test(document.forms["add-tag"]["tag_order"].value)) {
    $(".cat-alert").html("Order should be an integer");
    return false;
  }

  // tag rules are checked
  let TagDict = {"name": document.forms["add-tag"]["tag_name"].value,
                 "rule": document.forms["add-tag"]["tag_rule"].value,
                 "color": document.forms["add-tag"]["tag_color"].value
               };
  let order = parseInt(document.forms["add-tag"]["tag_order"].value, 10);
  if (!newTag) {
    TAGS.splice(editTagId, 1);
  }
  TAGS.splice(order, 0, TagDict);

  submitTag();
}

$("#btn-del").click((event) => {
  if (confirm("Are you sure you want to delete " + TAGS[editTagId].name + "?")) {
    TAGS.splice(editTagId, 1);
    submitTag();
    event.preventDefault();
  } else {
    event.preventDefault();
    return;
  }
});


// ************** NAVIGATION ***************************************************
$(".nav-link").click((event) => {
  if (!$(".btn-cancel").hasClass("disabled")) {
    if (confirm("Settings will not be saved. Continue?")) {
      $(".btn-save").addClass("disabled");
      reloadSettings();
      event.preventDefault();
    } else {
      event.preventDefault();
      return;
    }
  }
  $("#cats-set").css("display", "none");
  $("#tags-set").css("display", "none");
  $("#pref-set").css("display", "none");

  $("#cats-link").removeClass("active");
  $("#tags-link").removeClass("active");
  $("#pref-link").removeClass("active");

  $("#" + event.target.getAttribute("id").split("-")[0]
                                    + "-set").css("display", "block");
  $(event.target).addClass("active");
});