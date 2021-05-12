/*global allCatsArray, CATS, TAGS, PREF, LISTS, parseTex, MathJax, raiseAlert, cssVar*/
/*exported fillCatForm, fillTagForm, fillSetForm, changePasw, delAcc, fillListForm, */
/*eslint no-undef: "error"*/

var dragTarget;
var tagEdited = false;
var tableFilled = false;

var loadingTags = false;

// API call for settings modifications
const submitSetting = (url, set) => {
  if (set.length === 0) {
    set = ["null"];
  }
  $.post(url, JSON.stringify(set))
  .done(function() {
    reloadSettings();
    $(".btn-save").addClass("disabled");
    if ($("#btn-del").length > 0) {
      $("#btn-del").addClass("disabled");
    }
    tagEdited = false;
    raiseAlert("Settings are saved", "success");
    return false;
  }).fail(function() {
    raiseAlert("Settings are not saved. Please try later", "danger");
    return false;
  });
  return false;
};

// *****************************************************************************
// ************************  RENDERS *******************************************
// *****************************************************************************
// *****************************************************************************

// ************************ Categories *****************************************

const dropElement = (event, arrayToSwap) => {
  event.preventDefault();
  let moved = parseInt(event.dataTransfer.getData("Text"), 10);
  // insert transfered element at new place
  arrayToSwap.splice(dragTarget, 0, arrayToSwap[parseInt(moved, 10)]);

  if (moved > dragTarget) {
    moved += 1;
  }

  // delete transfered element at old place
  arrayToSwap.splice(moved, 1);

  $(".btn").removeClass("disabled");
  reloadSettings();
};

const delCatClick = (event) => {
  let name = event.target.getAttribute("id").split("_")[1];
  $("#par-cat-" + name).removeClass("d-flex");
  $("#par-cat-" + name).fadeOut();
  $(".btn").removeClass("disabled");
  const catId = CATS.indexOf(name.replace("111", "."));
  if (catId > -1) {
    CATS.splice(catId, 1);
  }
};

function addCat(cat) {
  // Dots replace with 111 to be a legal
  // name for JS elements
  // TODO proper escape dot with \\.
  let parent = document.createElement("div");
  parent.className = "d-flex cat-parent";
  parent.id = "par-cat-"+cat.replaceAll(".", "111");
  parent.draggable = true;

  parent.ondragstart = function(event) {
    let moved = event.target.getAttribute("id").split("-").slice(2);
    moved = moved.join("-").replaceAll("111", ".");
    moved = CATS.indexOf(moved);
    event.dataTransfer.setData("Text", moved);
  };

  parent.ondragover = function(event) {
    let target = event.target.getAttribute("id").split("-").slice(2);
    target = target.join("-").replaceAll("111", ".");
    dragTarget = CATS.indexOf(target);
  };

  let close = document.createElement("button");
  close.id = "close_" + cat.replaceAll(".", "111");
  close.className = "close close-btn";
  close.innerHTML = "&times";

  close.addEventListener("click", delCatClick);

  let catElement = document.createElement("div");
  catElement.className = "pl-2";
  catElement.id = "cat-name-" + cat.replaceAll(".", "111");
  catElement.textContent = allCatsArray[`${cat}`];

  document.getElementById("cats-list").appendChild(parent);
  parent.appendChild(close);
  parent.appendChild(catElement);
}

const dropCat = (event) => {
  dropElement(event, CATS);
};

function renderCats() {
  $("#cats-list").empty();
  CATS.forEach((cat) => {
    addCat(cat);
  });

  document.getElementById("cats-list").ondragover = function(event) {
    event.preventDefault();
  };
  document.getElementById("cats-list").removeEventListener("drop", dropCat);
  document.getElementById("cats-list").addEventListener("drop", dropCat);
}

// ************************ Tags ***********************************************

const findTagId = (param, paramName) => {
  for (let tagId = 0; tagId < TAGS.length; tagId++) {
    if (String(TAGS[parseInt(tagId, 10)][paramName]) === String(param)) {
      return tagId;
    }
  }
  return -1;
};

const dropTag = (event) => {
  dropElement(event, TAGS);
};

function renderTags() {
  $("#tag-list").empty();
  TAGS.forEach((tag) => {
    let tagElement = document.createElement("div");
    tagElement.className = "tag-label";
    tagElement.id = "tag-label-" + tag.id;
    tagElement.setAttribute("style", "background-color: " + tag.color);
    tagElement.draggable = true;
    tagElement.textContent = tag.name;
    document.getElementById("tag-list").appendChild(tagElement);

    tagElement.ondragstart = function(event) {
      if (tagEdited) {
        event.preventDefault();
        return;
      }
      let moved = event.target.getAttribute("id").split("-")[2];
      moved = findTagId(moved, "id");
      event.dataTransfer.setData("Text", moved);
    };

    tagElement.ondragover = function(event) {
      let target = event.target.getAttribute("id").split("-")[2];
      dragTarget = findTagId(target, "id");
    };
  });

  document.getElementById("tag-list").ondragover = function(event) {
    event.preventDefault();
  };

  // tag reordering
  document.getElementById("tag-list").removeEventListener("drop", dropTag);
  document.getElementById("tag-list").addEventListener("drop", dropTag);

  if (parseTex) {
    MathJax.typesetPromise();
  }
  // new tag button
  let tagElement = document.createElement("div");
  tagElement.setAttribute("class", "add-set tag-label");
  tagElement.setAttribute("id", "add-tag");
  tagElement.textContent = "+New";

  document.getElementById("tag-list").appendChild(tagElement);
}

// ************************  BOOKMARKS *****************************************

function fillListForm() {
  if ($(".btn-cancel").hasClass("disabled")) {
    return false;
  }
  let url = "mod_lists";
  submitSetting(url, LISTS);
  return false;
}

const findListNumById = (id) => {
  for (let listId = 0; listId < LISTS.length; listId++) {
    if (LISTS[parseInt(listId, 10)]["id"] === parseInt(id, 10)) {
      return listId;
    }
  }
  return -1;
};

function delListClick(event) {
  let name = event.target.getAttribute("id").split("_")[1];
  $("#par-list-" + name).removeClass("d-flex");
  $("#par-list-" + name).fadeOut();
  $(".btn").removeClass("disabled");
  const listId = findListNumById(name);
  if (listId > -1) {
    LISTS.splice(listId, 1);
  }
}

const dropList = (event) => {
  dropElement(event, LISTS);
};

function renderBookshelf() {
  $("#book-list").empty();
  LISTS.forEach((list) => {
    let listName = list.name;
    let parent = document.createElement("div");
    parent.className = "d-flex cat-parent";
    parent.id = "par-list-" + list.id;
    parent.draggable = true;

    parent.ondragstart = function(event) {
      let moved = event.target.getAttribute("id").split("-")[2];
      moved = findListNumById(moved);
      event.dataTransfer.setData("Text", moved);
    };

    parent.ondragover = function(event) {
      let target = event.target.getAttribute("id").split("-")[2];
      dragTarget = findListNumById(target);
    };

    let close = document.createElement("button");
    close.id = "close_" + list.id;
    close.className = "close close-btn";
    close.innerHTML = "&times";

    close.addEventListener("click", delListClick);

    let listElement = document.createElement("div");
    listElement.className = "pl-2";
    listElement.id = "list-name-" + list.id;
    listElement.textContent = listName;

    document.getElementById("book-list").appendChild(parent);
    parent.appendChild(close);
    parent.appendChild(listElement);
  });
  document.getElementById("book-list").ondragover = function(event) {
    event.preventDefault();
  };
  document.getElementById("book-list").removeEventListener("drop", dropList);
  document.getElementById("book-list").addEventListener("drop", dropList);
  if (parseTex) {
    MathJax.typesetPromise();
  }
}

// *******************  Preferences ********************************************

function renderPref() {
  if (PREF["tex"]) {
    document.getElementById("tex-check").checked = true;
  }

  if (PREF["theme"] === "dark") {
    document.getElementById("radio-dark").checked = true;
  } else {
    document.getElementById("radio-light").checked = true;
  }
  return;
}

// *****************************************************************************
// ************************  INTERACTIONS **************************************
// *****************************************************************************
// *****************************************************************************

// ******************** CATEGORIES *********************************************

function fillCatForm() {
  if ($(".btn-cancel").hasClass("disabled")) {
    return false;
  }
  submitSetting("mod_cat", CATS);
  return false;
}

$("#add-cat-btn").click(() => {
  let cat = document.forms["add-cat"]["cat_name"].value;
  // check if already there
  if (CATS.includes(cat)) {
    raiseAlert("Catagory already added!", "danger");
    return;
  }
  // check if legal category
  if (typeof(allCatsArray[cat]) === "undefined") {
    raiseAlert("Unknown category", "danger");
    return;
  }
  $(".btn-save").removeClass("disabled");
  addCat(document.forms["add-cat"]["cat_name"].value);
  document.forms["add-cat"]["cat_name"].value = "";
  // add to array
  CATS.push(cat);
});

$(".btn-cancel").click(() => {
  if (!$(".btn-cancel").hasClass("disabled")) {
    location.reload();
  }
});

// ****************** TAGS *****************************************************

const clearTagField = () => {
  document.forms["add-tag"]["tag_name"].value = "";
  document.forms["add-tag"]["tag_rule"].value = "";
  document.forms["add-tag"]["tag_color"].value = "";
  document.forms["add-tag"]["book-check"].checked = false;
  document.forms["add-tag"]["email-check"].checked = false;
  document.forms["add-tag"]["public-check"].checked = false;
  $("#tag-color").css("background-color", $("#tag-color").val());
};

$("#show-rules").click(() => {
  if ($("#tag-help").css("display") === "block") {
    $("#tag-help").css("display", "none");
    $("#show-rules").text("Show rules hints");
  } else {
    $("#tag-help").css("display", "block");
    $("#show-rules").text("Hide rules hints");
  }
});

var editTagId = -2;

const makeTagEdited = () => {
  $(".btn-save").removeClass("disabled");
  tagEdited = true;
  var doms = document.getElementsByClassName("tag-label");
  for(let i = 0; i < doms.length; i++) {
    doms[parseInt(i, 10)].style.cursor = "not-allowed";
  }
};

const tableRowClick = (event) => {
  // do nothing if tag is not eddited
  let message = "Use this name and rule?";
  let newTag = false;
  if ($(".btn-save").hasClass("disabled") && editTagId < -1) {
    message = "Use this rule for a new tag?";
    newTag = true;
  }
  if (confirm(message)) {
    // assume click is done on a cell, thus the row is a parent element
    let row = event.target.parentElement;
    for (let childId = 0; childId < row.childNodes.length; childId++) {
      if (newTag) {
        $("#add-tag").click();
      }
      if (!row.childNodes[parseInt(childId, 10)].className) {
        continue;
      }
      if (row.childNodes[parseInt(childId, 10)].className.includes("name")) {
        document.forms["add-tag"]["tag_name"].value = row.childNodes[parseInt(childId, 10)].textContent;
      }
      if (row.childNodes[parseInt(childId, 10)].className.includes("rule")) {
        document.forms["add-tag"]["tag_rule"].value = row.childNodes[parseInt(childId, 10)].textContent;
      }
    }
  }
  makeTagEdited();
};

$("#show-pubtags").click(() => {
  if (loadingTags) {
    event.preventDefault();
    return;
  }
  loadingTags = true;
  if ($("#table-wrapper").css("display") === "block") {
    $("#table-wrapper").css("display", "none");
    $("#loading-tags").css("display", "none");
    $("#show-pubtags").text("Show users rules examples");
  } else {
    $("#table-wrapper").css("display", "block");
    $("#show-pubtags").text("Hide users rules examples");
  }
  if (tableFilled) {
    event.preventDefault();
    return;
  }

  $("#loading-tags").css("display", "block");
   $.ajax({
    url: "/public_tags",
    type: "get",
    success(data) {
      data.forEach((tag, num) => {
        let row = document.createElement("tr");
        let inner = document.createElement("th");
        inner.scope = "row";
        inner.textContent = num + 1;
        row.addEventListener("click", tableRowClick);

        let name = document.createElement("td");
        name.className = "name";
        name.textContent = tag.name;

        let rule = document.createElement("td");
        rule.className = "rule";
        rule.style.letterSpacing = "2px";
        rule.textContent = tag.rule;

        document.getElementById("table-body").appendChild(row);
        row.appendChild(inner);
        row.appendChild(name);
        row.appendChild(rule);
      });
      tableFilled = true;
      $("#loading-tags").css("display", "none");
    }
  });
});

// click on tag label
$("#tag-list").click((event) => {
  // consider only tag labels click
  if (typeof($(event.target).attr("class")) === "undefined" ||
      !$(event.target).attr("class").includes("tag-label")) {
    return;
  }

  // check if settings were modified
  if (tagEdited) {
    event.preventDefault();
    return;
  }

  // reset the highlignt of all other tags
  let tagCol = document.getElementsByClassName("tag-label");
  for (let id = 0; id < tagCol.length; id++) {
    // new tag box
    if ($(tagCol[parseInt(id, 10)]).attr("id") === "add-tag") {
      $("#add-tag").css("border-style", "dashed");
      $("#add-tag").css("border-width", "2px");
    } else {
      // existing tags
      tagCol.item(id).style.borderColor =  "transparent";
    }
  }

  // highlight the editable tag
  $(event.target).css("border-color", cssVar("--tag_border_color"));

  if ($(event.target).attr("id") === "add-tag") {
    // -1 corresponds to new tag
    editTagId = -1;

    $("#btn-reset").click();
    $("#add-tag").css("border-style", "solid");
    $("#add-tag").css("border-width", "4px");
    clearTagField();
    // make delete NOT possible
    $("#btn-del").addClass("disabled");
  } else {
    let editTagName = $(event.target).attr("id").split("-")[2];
    editTagName = parseInt(editTagName, 10);
    editTagId = findTagId(editTagName, "id");
    let tag = TAGS[parseInt(editTagId, 10)];


    $("#tag-fields").prop("disabled", false);
    document.forms["add-tag"]["tag_name"].value = tag.name;
    document.forms["add-tag"]["tag_rule"].value = tag.rule;
    document.forms["add-tag"]["tag_color"].value = tag.color;
    document.forms["add-tag"]["book-check"].checked = tag.bookmark;
    document.forms["add-tag"]["email-check"].checked = tag.email;
    document.forms["add-tag"]["public-check"].checked = tag.public;
    $("#tag-color").css("background-color", $("#tag-color").val());

    // make delete possible
    $("#btn-del").removeClass("disabled");
  }
  $("#tag-fields").prop("disabled", false);
});

$(".tag-field").on("input", function() {
  makeTagEdited();
});

// TODO should I delete oninput listener?!
$(".tag-field").on("change", function() {
  makeTagEdited();
});

$("#tag-color").on("change", function() {
  $("#tag-color").css("background-color", $("#tag-color").val());
  $(".btn-save").removeClass("disabled");
});

// check if tag info is filled properly
// if yes, do API call
function checkTag() {
  $(".cat-alert").empty();
  // in case of simple replacement no check required
  if (!tagEdited) {
    submitSetting("mod_tag", TAGS);
    return true;
  }

  // check all fields are filled
  if (document.forms["add-tag"]["tag_name"].value === "" ||
      document.forms["add-tag"]["tag_rule"].value === "" ||
      document.forms["add-tag"]["tag_color"].value === "") {
    $(".cat-alert").html("Fill all the fields in the form!");
    return false;
  }

  let tagWithSameNameId = findTagId(document.forms["add-tag"]["tag_name"].value,
                                    "name"
                                    );
  if (tagWithSameNameId !== -1 && tagWithSameNameId !== editTagId) {
    $(".cat-alert").html("Tag with this name already exists. Consider a unique name!");
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

  // tag rules are checked
  let TagDict = {"name": document.forms["add-tag"]["tag_name"].value,
                 "rule": document.forms["add-tag"]["tag_rule"].value,
                 "color": document.forms["add-tag"]["tag_color"].value,
                 "bookmark": document.forms["add-tag"]["book-check"].checked,
                 "email": document.forms["add-tag"]["email-check"].checked,
                 "public": document.forms["add-tag"]["public-check"].checked
                 };
  if (editTagId > -1) {
    TAGS[parseInt(editTagId, 10)]["name"] = TagDict["name"];
    TAGS[parseInt(editTagId, 10)]["rule"] = TagDict["rule"];
    TAGS[parseInt(editTagId, 10)]["color"] = TagDict["color"];
    TAGS[parseInt(editTagId, 10)]["bookmark"] = TagDict["bookmark"];
    TAGS[parseInt(editTagId, 10)]["email"] = TagDict["email"];
    TAGS[parseInt(editTagId, 10)]["public"] = TagDict["public"];
  } else {
    // new tag no id
    TagDict["id"] = -1;
    TAGS.push(TagDict);
  }

  submitSetting("mod_tag", TAGS);
}

function fillTagForm() {
  if ($(".btn-cancel").hasClass("disabled")) {
    return false;
  }
  checkTag();
  return false;
}

// delete tag
$("#btn-del").click((event) => {
  if (editTagId < 0 || $("#btn-del").hasClass("disabled")) {
    event.preventDefault();
    return;
  }
  $("#tag-label-" + TAGS[parseInt(editTagId, 10)]["id"]).fadeOut();
  TAGS.splice(editTagId, 1);
  $(".btn-save").removeClass("disabled");
  event.preventDefault();
});

// ***************** PREFERENCES ***********************************************

$(".form-check-input").change(() => {
  $(".btn-save").removeClass("disabled");
});

function fillSetForm() {
  if ($(".btn-cancel").hasClass("disabled")) {
    return false;
  }
  let url = "mod_pref";
  let themeName = "light";
  if (document.getElementById("radio-dark").checked) {
    themeName = "dark";
  }
  let dataSet = {"tex": document.getElementById("tex-check").checked,
                 "theme": themeName
                 };
  $.post(url, JSON.stringify(dataSet))
  .done(function() {
    reloadSettings();
    $(".btn-save").addClass("disabled");
    raiseAlert("Settings are saved", "success");
    // update the stylesheets. Just in case theme was changed
    var links = document.getElementsByTagName("link");
    for (var i = 0; i < links.length; i++) {
      var link = links[parseInt(i, 10)];
      if (link.rel === "stylesheet") {
        link.href += "?";
      }}
    localStorage.clear();
    window.location.reload(true);
    return false;
  }).fail(function(){
    raiseAlert("Settings are not saved. Please try later", "danger");
    return false;
  });

  return false;
}

function delAcc() {
  if (confirm("Do you want to delete account completely? This action could not be undone!")) {
    return true;
  } else {
    return false;
  }
}

// ************** NAVIGATION ***************************************************
$(".nav-link").click((event) => {
  if ($(".btn-cancel").length && !$(".btn-cancel").hasClass("disabled")) {
    if (confirm("Settings will not be saved. Continue?")) {
      return;
    } else {
      event.preventDefault();
      return;
    }
  }
});

// reload settings information
const reloadSettings = () => {
  if ($("#cats-link").hasClass("active")) {
    renderCats();
  }
  else if ($("#tags-link").hasClass("active")) {
    renderTags();
    editTagId = -2;
    $("#tag-fields").prop("disabled", true);
    clearTagField();
  } else if ($("#bookshelf-link").hasClass("active")) {
    renderBookshelf();
  } else if ($("#pref-link").hasClass("active")) {
    renderPref();
  }
};

// on page load
window.onload = function() {
  $.each(allCatsArray, function(val, text) {
    $("#catsDataList").append($("<option>").attr("value", val).text(text));
  });

  reloadSettings();
};
