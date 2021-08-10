/*global MathJax, parseTex, DATA, prefs, CATS, TAGS, raiseAlert, renderPapersBase*/
/*exported novChange */
/*eslint no-undef: "error"*/

let TO_RENDER = 20;
let START = 0;
let DONE = false;
var VISIBLE = 0;
var titleRendered = false;

var TAGSSHOW = [];

function formateDate(date) {
  let dateArray = date.toString().split(" ");
  return dateArray[2] + " " + dateArray[1] + " " + dateArray[3];
}

function paperVisibility(vis, pId) {
  // do not show too much papers
  if (pId >= START + TO_RENDER) {
    return;
  }

  if (vis) {
    // show paper with aproproate number
    document.getElementById("paper-" + pId).style["display"] = "block";
    let number = document.getElementById("paper-num-" + pId);
    VISIBLE += 1;
    number.textContent = String(VISIBLE);
  } else {
    // hide paper
    document.getElementById("paper-" + pId).style["display"] = "none";
  }
}

// toggle the visibility of rendered papers
function toggleVis(start=0) {
  let passed = 0;
  if (start === 0) {
    VISIBLE = 0;
  }

  // create a list of categories that are visible based on checkbox selection
  let catsShow = [];
  for (let key in prefs.data.catsArr) {
    if (prefs.data.catsArr[`${key}`]) {
      catsShow.push(key);
    }
  }

  let allVisible = TAGSSHOW.every(x=>x);

  for(let pId = start; pId < DATA.papers.length; pId++) {
    let paper = DATA.papers[parseInt(pId, 10)];
    // Logic: if check-box is off --> cut all the affected papers
    if ((prefs.data.showNov[0] === true || !(paper.nov & 1)) &&
        (prefs.data.showNov[1] === true || !(paper.nov & 2)) &&
        (prefs.data.showNov[2] === true || !(paper.nov & 4)) &&
        // filter on categories check boxes
        catsShow.filter((value) => paper.cats.includes(value)).length > 0 &&
        // filter on tags
        (allVisible || TAGSSHOW.filter((value, index) => value && paper.tags.includes(index)).length > 0)
        ) {
      passed += 1;
      paperVisibility(true, pId);
    } else {
      paperVisibility(false, pId);
    }
  }

  if (start === 0) {
    $("#passed").text(passed);
  }

  if (!DONE) {
    scrollIfNeeded();
  }
}

function checkCat(event) {
  let number = event.target.getAttribute("id").split("-")[2];
  let cat = document.getElementById("cat-label-" + number).textContent;
  prefs.data.catsArr[`${cat}`] = document.getElementById("check-cat-" + number).checked;
  // save the cookies
  prefs.save();
  setTimeout(function () {
    toggleVis();
  }, 0);
}

function renderCats() {
  // TODO check if there are old cats in cookies
  CATS.forEach((cat, num) => {
    // if category not in cookies visibility dictionary --> add it
    // TODO remove excessive categories from cookies
    if (!(cat in prefs.data.catsArr)) {
      prefs.data.catsArr[`${cat}`] = true;
    }

    let parent = document.createElement("div");
    parent.className = "d-flex menu-item";

    let form = document.createElement("div");
    form.className = "form-check";

    var check = document.createElement("input");
    check.setAttribute("type", "checkbox");
    check.id = "check-cat-"+num;
    check.className = "form-check-input check-cat";
    // read visibility from cookies
    check.checked = prefs.data.catsArr[`${cat}`];
    check.addEventListener("click", checkCat);

    // category name
    let catElement = document.createElement("label");
    catElement.className = "form-check-label";
    catElement.id = "cat-label-"+num;
    catElement.setAttribute("for", "check-cat-"+num);
    catElement.textContent = cat;

    // number of papers of given category
    let counter = document.createElement("div");
    counter.className = "ml-auto counter";
    counter.id = "cat-count-"+num;
    counter.textContent = "0";

    document.getElementById("cats").appendChild(parent);
    parent.appendChild(form);
    form.appendChild(check);
    form.appendChild(catElement);
    parent.appendChild(counter);
  });
}

const tagBorder = (num, border) => {
  TAGSSHOW[parseInt(num, 10)] = border;

  $("#tag-label-" + num).css("border-color",
                             border ? cssVar("--tag_border_color") : "transparent"
                             );
};

const clickTag = (event) => {
  let number = event.target.getAttribute("id").split("-")[2];
  let thisVisible = TAGSSHOW[parseInt(number, 10)];
  let allVisible = TAGSSHOW.every(x=>x);

  // if this tag is selected
  if (thisVisible) {
    if (allVisible) {
      // select only this tag
      // make all others invisible
      TAGSSHOW = TAGSSHOW.map(x => false);

      // but this one visible
      tagBorder(number, true);
    } else {
      // hide this tag
      TAGSSHOW[parseInt(number, 10)] = false;
      // if this was the only left tag
      if (TAGSSHOW.filter((value) => value).length === 0) {
        // make all tags visible
        TAGSSHOW = TAGSSHOW.map(x => true);
      }
      // remove border
      $("#tag-label-" + number).css("border-color", "transparent");
    }
  // if this tag is UNselected
  } else {
    // make this tag selected
    tagBorder(number, true);
  }

  setTimeout(function () {
    toggleVis();
  }, 0);
};

function renderTags() {
  TAGS.forEach((tag, num) => {
    // store tag in settings for visibility control
    // do NOT store this values in cookies
    // keep it just for the current session
    TAGSSHOW.push(true);

    let parent = document.createElement("div");
    parent.className = "d-flex justify-content-between align-items-center";

    let tagElement = document.createElement("div");
    tagElement.className = "tag-label";
    tagElement.id = "tag-label-"+num;
    tagElement.style = "background-color: " + tag.color;
    tagElement.textContent = tag.name;

    tagElement.addEventListener("click", clickTag);

    let counter = document.createElement("div");
    counter.className = "counter";
    counter.id = "tag-count-"+num;
    counter.textContent = "0";

    document.getElementById("tags").appendChild(parent);
    parent.appendChild(tagElement);
    parent.appendChild(counter);
  });

  if (parseTex) {
    MathJax.typesetPromise();
  }
}

function renderNov() {
  prefs.data.showNov.forEach((show, num) => {
    document.getElementById("check-nov-" + num).checked = show;
  });
}

function renderCounters() {
  let nCats = CATS.length;
  if (typeof(DATA.ncat) === "undefined") {
    return;
  }
  for(let catId = 0; catId < nCats; catId++) {
    document.getElementById("cat-count-"+catId).textContent = DATA.ncat[parseInt(catId, 10)];
  }

  for(let novId = 0; novId < 3; novId++) {
    document.getElementById("nov-count-"+novId).textContent = DATA.nnov[parseInt(novId, 10)];
  }

 let nTags = TAGS.length;
 for(let tagId = 0; tagId < nTags; tagId++) {
    document.getElementById("tag-count-"+tagId).textContent = DATA.ntag[parseInt(tagId, 10)];
  }
  return;
}

function addBookmark(event) {
  // WARNING
  // UB addBookmark listener is added to all the buttons, not the bookmark only one
  // prevent the bookmark adding for other buttons
  if (!event.target.id.includes("btn-book") &&
      !event.target.id.includes("a-icon")) {
    return;
  }
  let url = "add_bm";
  let num = event.target.getAttribute("id").split("-")[2];
  let paper = DATA.papers[parseInt(num, 10)];
  // we take paper id w/o version --> do not overload paper DB
  $.post(url, {"paper_id": paper.id.split("v")[0]})
  .done(function(data, textStatus, jqXHR) {
    let status = jqXHR.status;
    if (status === 200) {
      raiseAlert("Paper has been already saved", "success");
    }
    if (status === 201) {
      raiseAlert("Paper has been added", "success");
    }
  }).fail(function(){
    raiseAlert("Paper is not saved due to server error", "danger");
  });
}

function renderPapers() {
  if (!titleRendered) {
    $("#paper-list-title").text($("#paper-list-title").text() + DATA.title);
    titleRendered = true;
  }

  for (let pId = START; pId < Math.min(START + TO_RENDER, DATA.papers.length); pId++) {

    let content = DATA.papers[parseInt(pId, 10)];
    let paperBase = renderPapersBase(content, pId);
    let btnPanel = paperBase[1];

    // add bookmark button
    let btnBook = document.createElement("button");
    btnBook.className = "btn btn-primary";
    btnBook.id = "btn-book-"+pId;
    btnBook.innerHTML = "<i class='fa fa-bookmark' aria-hidden='true' id='a-icon-" + pId + "'></i>";
    btnBook.onclick = addEventListener("click", addBookmark);

    let btnGroup4 = document.createElement("div");
    btnGroup4.className = "btn-group mr-2";
    btnGroup4.role = "group";
    btnPanel.appendChild(btnGroup4);
    btnGroup4.appendChild(btnBook);
  }

  // check papers compatibility with visibility settings with checkboxes
  toggleVis(START);

  if (parseTex) {
    MathJax.typesetPromise();
  }
  if (!DONE) {
    scrollIfNeeded();
  }
}

function sortFunction(a, b, order=true) {
  return order? a - b : b - a;
}

function sortPapers() {
  $("#paper-list-content").empty();
  START = 0;
  let sortMethod = $("#sort-sel").val();
  // tags
  if (sortMethod.includes("tag")) {

    DATA.papers.sort((a, b) => {
      if (b.tags.length === 0 || a.tags.length === 0) {
        return -1;
      }
      return sortFunction(a.tags[0], b.tags[0],
                          sortMethod === "tag-as"? true : false);
    });
  }
  // dates
  if (sortMethod.includes("date-up")) {
    DATA.papers.sort((a, b) => {
      let aDate = new Date(a.date_up);
      let bDate = new Date(b.date_up);
      return sortFunction(aDate, bDate,
                          sortMethod === "date-up_des"? true : false);
    });
  }

  if (sortMethod.includes("date-sub")) {
    DATA.papers.sort((a, b) => {
      let aDate = new Date(a.date_sub);
      let bDate = new Date(b.date_sub);
      return sortFunction(aDate, bDate,
                          sortMethod === "date-sub_des"? true : false);
    });
  }

  // caregories
  if (sortMethod.includes("cat")) {
    DATA.papers.sort((a, b) => {
      let catA = "";
      let catB = "";
      for (let id = 0; id < a.cats.length; id++) {
        if (CATS.includes(a.cats[parseInt(id, 10)])) {
          catA = a.cats[parseInt(id, 10)];
          break;
        }
      }
      for (let id = 0; id < b.cats.length; id++) {
        if (CATS.includes(b.cats[parseInt(id, 10)])) {
          catB = b.cats[parseInt(id, 10)];
          break;
        }
      }
      return sortFunction(CATS.indexOf(catA), CATS.indexOf(catB),
                          sortMethod === "cat-as"? true : false);
    });
  }
}

// change sort selector
$("#sort-sel").change(() => {
  $("#sorting-proc").css("display", "block");
  sortPapers();
  // dirty fix to throw renderPapers() in the separate thread
  // and not freeze the selector
  setTimeout(function () {
    renderPapers();
    $("#sorting-proc").css("display", "none");
    // if (parseTex) {
    //   MathJax.typesetPromise();
    // }
  }, 0);
});

function scrollIfNeeded() {
  if (START > DATA.papers.length) {
    DONE = true;
    document.getElementById("loading-papers").style["display"] = "none";
    document.getElementById("done-papers").style["display"] = "block";
    return;
  }

  var scrollTop = window.scrollY;
  var windowHeight = window.innerHeight;
  var bodyHeight = document.body.clientHeight - windowHeight;
  var scrollPercentage = (scrollTop / bodyHeight);

  if(scrollPercentage > 0.9 || bodyHeight < 0) {
    START += TO_RENDER;
    document.getElementById("loading-papers").style["display"] = "block";
    renderPapers();
  }
}

document.getElementById("filter-button").onclick = function() {
  if (document.getElementById("menu-col").classList.contains("d-none")) {
    document.getElementById("menu-col").classList.remove("d-none");
    document.getElementById("menu-main").classList.remove("ml-auto");
  } else {
    document.getElementById("menu-col").classList.add("d-none");
    document.getElementById("menu-main").classList.add("ml-auto");
  }
};

function novChange(number) {
  prefs.data.showNov[parseInt(number, 10)] = document.getElementById("check-nov-"+number).checked;
  prefs.save();
  setTimeout(function () {
    toggleVis();
  }, 0);
}

window.onload = function() {
  var url = document.location.href;
  url = url.replace("papers", "data");

  // Get paper data from backend
  $.get(url)
  .done(function(data) {
    DATA = data;
    renderCounters();
    renderPapers();
    $("#sort-block").css("display", "block");
  }).fail(function(jqXHR){
    $("#loading-papers").text("Oooops, arxivtag experienced an internal error processing your papers. We are working on fixing that. Please, try later.");
  });
  renderNov();
  renderCats();
  renderTags();
};

window.onscroll = function() {
  if (!DONE) {
    scrollIfNeeded();
  }
};
