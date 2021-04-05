/*global MathJax, parseTex, DATA, prefs, CATS, TAGS, raiseAlert, renderPapersBase*/
/*eslint no-undef: "error"*/

let PAPERS_TO_RENDER = 20;
let START = 0;
let DONE = false;
var VISIBLE = 0;

function formateDate(date) {
  let dateArray = date.toString().split(" ");
  return dateArray[2] + " " + dateArray[1] + " " + dateArray[3];
}

// toggle the visibility of rendered papers
function toggleVis(start=0) {
  if (start === 0) {
    VISIBLE = 0;
  }
  for(let pId = start; pId < START + PAPERS_TO_RENDER; pId ++) {
    if (pId >= DATA.papers.length) {
      break;
    }
    let paper = DATA.papers[parseInt(pId, 10)];
    let display = false;
    if (prefs.data.showNov[0] === true && paper.nov === 1 ||
        prefs.data.showNov[1] === true && paper.nov === 2 ||
        prefs.data.showNov[2] === true && paper.nov === 4) {
      display = true;
    } else {
      display = false;
    }
    if (display) {
      for (let catId = 0; catId < prefs.data.catsArr.length; catId++) {
        let cat = prefs.data.catsArr[parseInt(catId, 10)];
        if (prefs.data.catsShowArr[parseInt(catId, 10)] && paper.cats.includes(cat)) {
          display = true;
          break;
        } else {
          display = false;
        }
      }
    }

    if (display) {
      document.getElementById("paper-" + pId).style["display"] = "block";
      let number = document.getElementById("paper-num-" + pId);
      VISIBLE += 1;
      number.textContent = String(VISIBLE);
    } else {
      document.getElementById("paper-" + pId).style["display"] = "none";
    }
  }

  if (!DONE) {
    scrollIfNeeded();
  }
}

function renderTitle() {
  let title = document.getElementById("paper-list-title");
  let date = new Date();
  let dateNew = new Date();
  if (title.textContent.includes("today")) {
    title.textContent += ": " + formateDate(date);
  } else if (title.textContent.includes("week")) {
    let start = new Date(date.setDate(date.getDate() - date.getDay() + 1));
    let end = new Date(dateNew.setDate(dateNew.getDate() + 7 - dateNew.getDay()));
    // Sunday (Burn in hell JS!!!)
    if ((new Date()).getDay() === 0) {
      start = new Date(start.setDate(start.getDate() - 7));
      end = new Date(dateNew.setDate(end.getDate() - 7));
    }
    title.textContent += ": " + formateDate(start) + " - " + formateDate(end);
  } else if (title.textContent.includes("month")) {
    let end = new Date;
    let start = new Date(date.setDate(date.getDate() - date.getDate() + 1));

    // TODO it's a dirty fix. Need proper treatment
    if (dateNew.getDate() === 1) {
      start = new Date(dateNew.setDate(dateNew.getDate() - 1));
    }
    title.textContent += ": " +formateDate(start) + " - " + formateDate(end);
  }
}

function renderCats() {
  // TODO check if there are old cats in cookies
  CATS.forEach((cat, num) => {
    if (!prefs.data.catsArr.includes(cat)) {
      prefs.data.catsArr.push(cat);
      prefs.data.catsShowArr.push(true);
    }

    let parent = document.createElement("div");
    parent.className = "d-flex menu-item";

    let form = document.createElement("div");
    form.className = "form-check";

    var check = document.createElement("input");
    check.setAttribute("type", "checkbox");
    check.id = "check-cat-"+num;
    check.className = "form-check-input check-cat";
    if (prefs.data.catsShowArr[prefs.data.catsArr.indexOf(cat)]) {
      check.checked = true;
    }
    check.onchange = function() {
      let number = event.target.getAttribute("id").split("-")[2];
      let cat = document.getElementById("cat-label-"+num).textContent;
      let index = prefs.data.catsArr.indexOf(cat);
      prefs.data.catsShowArr[parseInt(index, 10)] = document.getElementById("check-cat-"+number).checked;
      prefs.save();
      toggleVis();
    };

    let catElement = document.createElement("label");
    catElement.className = "form-check-label";
    catElement.id = "cat-label-"+num;
    catElement.setAttribute("for", "check-cat-"+num);
    catElement.textContent = cat;

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

function renderTags() {
  TAGS.forEach((tag, num) => {
    let parent = document.createElement("div");
    parent.className = "d-flex justify-content-between align-items-center";

    let tagElement = document.createElement("div");
    tagElement.className = "tag-label";
    tagElement.id = "tag-label-"+num;
    tagElement.style = "background-color: " + tag.color;
    tagElement.textContent = tag.name;

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
}

function addBookmark(event) {
  // WARNING
  // UB addBookmark listener is added to all the buttons, not the bookmark only one
  // prevent the bookmark addinf for other buttons
  if (!event.target.id.includes("btn-book") &&
      !event.target.id.includes("a-icon")) {
    return;
  }
  let url = "add_bm";
  let num = event.target.getAttribute("id").split("-")[2];
  let paper = DATA.papers[parseInt(num, 10)];
  // we take paper id w/o version --> do not overload paper DB
  $.post(url, {"title": paper.title,
               "paper_id": paper.id.split("v")[0],
               "author": paper.author,
               "date_up": paper.date_up,
               "abstract": paper.abstract,
               "ref_pdf": paper.ref_pdf,
               "ref_web": paper.ref_web,
               "ref_doi": paper.ref_doi,
               "cats": paper.cats
               })
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
  for(let pId = START; pId < START + PAPERS_TO_RENDER; pId++) {
    if (DATA.papers.length <= pId) {
      break;
    }
    let content = DATA.papers[parseInt(pId, 10)];

    let paperBase = renderPapersBase(content, pId);
    let btnPanel = paperBase[1];

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
  // tag increase
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
  if (sortMethod.includes("date")) {
    DATA.papers.sort((a, b) => {
      let aDate = new Date(a.date_up);
      let bDate = new Date(b.date_up);
      return sortFunction(aDate, bDate,
                          sortMethod === "date-des"? true : false);
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

  // Novelty new-crossref-update
  if (sortMethod.includes("nov")) {
    DATA.papers.sort((a, b) => {
      let novA = a.nov;
      let novB = b.nov;
      return sortFunction(novA, novB,
                          sortMethod === "nov-des"? true : false);
    });
  }
}

// change sort selector
$("#sort-sel").change(() => {
  $("#sorting-proc").css("display", "block");
  sortPapers();
  // dirty fix to throw displayPapers() in the separate thread
  // and not freeze the selector
  setTimeout(function () {
    renderPapers();
    $("#sorting-proc").css("display", "none");
    if (parseTex) {
      MathJax.typesetPromise();
    }
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
    START += PAPERS_TO_RENDER;
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

function addAnchors() {
  // add anchors for click on novelty checkbox
  var anchors = document.getElementsByClassName("check-nov");
  for(let i = 0; i < anchors.length; i++) {
    let anchor = anchors[i];
    anchor.onchange = function(event) {
      let number = event.target.getAttribute("id").split("-")[2];
      prefs.data.showNov[parseInt(number, 10)] = document.getElementById("check-nov-"+number).checked;
      prefs.save();
      toggleVis();
    }
  }
  // add ahchors for click on novelty labels
  anchors = document.getElementsByClassName("item-nov");
  for(let i = 0; i < anchors.length; i++) {
    let anchor = anchors[parseInt(i, 10)];
    anchor.onclick = function(event) {
      let number = event.target.getAttribute("id").split("-")[1];
      document.getElementById("check-nov-"+number).click();
    }
  }
}

window.onload = function() {
  var url = document.location.href;
  url = url.replace("papers", "data");

  // Get paper data from backend
  $.get(url)
  .done(function(data) {
    document.getElementById("loading-papers").style["display"] = "none";
    DATA = data;
    renderCounters();
    renderPapers();
    $("#sort-block").css("display", "block");
  }).fail(function(jqXHR){
    if (jqXHR.status === 404) {
      $("#loading-papers").text("Paper source website is not responding. Is it down?");
    } else if (jqXHR.status === 400) {
      $("#loading-papers").text("Paper source website response with no papers for your request");
    } else {
      $("#loading-papers").text("Oooops, arxivtag experienced an internal error processing your papers. We are working on fixing that. Please try later.");
    }
  });
  renderTitle();
  renderNov();
  renderCats();
  renderTags();

  addAnchors();
};

window.onscroll = function() {
  if (!DONE) {
    scrollIfNeeded();
  }
};
