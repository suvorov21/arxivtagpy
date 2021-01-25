/*global MathJax, parseTex, DATA, prefs, CATS, TAGS*/
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
    parent.setAttribute("class", "d-flex menu-item");

    let form = document.createElement("div");
    form.setAttribute("class", "form-check");

    var check = document.createElement("input");
    check.setAttribute("type", "checkbox");
    check.setAttribute("id", "check-cat-"+num);
    check.setAttribute("class", "form-check-input check-cat");
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
    catElement.setAttribute("class", "form-check-label");
    catElement.setAttribute("id", "cat-label-"+num);
    catElement.setAttribute("for", "check-cat-"+num);
    catElement.textContent = cat;

    let counter = document.createElement("div");
    counter.setAttribute("class", "ml-auto counter");
    counter.setAttribute("id", "cat-count-"+num);
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
    parent.setAttribute("class", "d-flex justify-content-between align-items-center");

    let tagElement = document.createElement("div");
    tagElement.setAttribute("class", "tag-label");
    tagElement.setAttribute("id", "tag-label-"+num);
    tagElement.setAttribute("style", "background-color: " + tag.color);
    tagElement.textContent = tag.name;

    let counter = document.createElement("div");
    counter.setAttribute("class", "counter");
    counter.setAttribute("id", "tag-count-"+num);
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

function renderOcoins(paper) {
  let ocoins = {
    "ctx_ver": "Z39.88-2004",
    "rft_val_fmt": encodeURIComponent("info:ofi/fmt:kev:mtx:journal"),
    "rft_id": encodeURIComponent(paper.ref_web),
    "rft_id": encodeURIComponent(paper.ref_doi),
    "rft.atitle": encodeURIComponent(paper.title),
    "rft.jtitle": encodeURIComponent("arXiv:" + paper.id + " [" + paper.cats[0] + "]"),
    "rft.date": encodeURIComponent(paper.date_up),
    "rft.artnum": encodeURIComponent(paper.id),
    "rft.genre": encodeURIComponent("preprint"),
    "rft.description": encodeURIComponent(paper.abstract),
  };

  ocoins = JSON.stringify(ocoins);
  ocoins = ocoins.replace(/\"/g, "");
  ocoins = ocoins.replace(/,/g, "&");
  ocoins = ocoins.replace(/:/g, "=");
  ocoins = ocoins.slice(1, ocoins.length - 1);

  ocoins += paper.author.map((au) => {return "&rft.au=" + encodeURIComponent(au);}).join();

  return ocoins;
}

function renderPapers() {
  for(let pId = START; pId < START + PAPERS_TO_RENDER; pId ++) {
    if (DATA.papers.length <= pId) {
      break;
    }
    let content = DATA.papers[parseInt(pId, 10)];
    let paper = document.createElement("div");
    paper.setAttribute("class", "paper");
    paper.setAttribute("id", "paper-"+pId);
    document.getElementById("paper-list-content").appendChild(paper);

    let ocoinsSpan = document.createElement("span");
    ocoinsSpan.setAttribute("class", "Z3988");
    ocoinsSpan.setAttribute("title", renderOcoins(content));
    paper.appendChild(ocoinsSpan);

    let title = document.createElement("div");
    title.setAttribute("class", "paper-title");
    title.setAttribute("id", "paper-title-"+pId);

    paper.appendChild(title);

    let number = document.createElement("span");
    number.setAttribute("id", "paper-num-"+pId);
    number.textContent = String(pId);

    let titleText = document.createElement("span");
    titleText.textContent = ". " + content.title;
    title.appendChild(number);
    title.appendChild(titleText);

    var tagPanel = document.createElement("div");
    tagPanel.setAttribute("class", "tag-panel");
    tagPanel.setAttribute("id", "tag-panel-"+pId);
    paper.appendChild(tagPanel);

    content.tags.forEach(function(tag) {
      var tagDiv = document.createElement("div");
      tagDiv.setAttribute("class", "tag-panel-item");
      tagDiv.setAttribute("style", "background-color:" + TAGS[parseInt(tag, 10)].color);
      tagDiv.textContent = TAGS[parseInt(tag, 10)].name;
      tagPanel.appendChild(tagDiv);
    });

    if (content.tags.length === 0) {
      tagPanel.setAttribute("style", "display: none");
    }

    let au = document.createElement("div");
    au.setAttribute("class", "paper-au");
    au.textContent = content.author.join(", ");
    paper.appendChild(au);

    let date = document.createElement("div");
    date.setAttribute("id", "paper-date-"+pId);
    date.setAttribute("class", "paper-date");
    date.textContent = content.date_up;

    if (content.date_sub !== content.date_up) {
      date.textContent += " (v1: " + content.date_sub + ")";
    }
    paper.appendChild(date);

    if (content.ref_doi) {
      let ref = document.createElement("div");
      ref.setAttribute("class", "ref");

      let dark = document.createElement("span");
      dark.setAttribute("class", "dark paper-doi");
      dark.textContent = " doi:";

      let light = document.createElement("span");
      light.setAttribute("class", "light paper-doi");

      let link = document.createElement("a");
      link.setAttribute("href", content.ref_doi);
      link.setAttribute("target", "_blank");
      link.textContent = content.ref_doi.split(".org/")[1];

      paper.appendChild(ref);
      ref.appendChild(dark);
      ref.appendChild(light);
      light.appendChild(link);
    }

    let cat = document.createElement("div");
    cat.setAttribute("class", "paper-cat");
    cat.innerHTML = "[<strong>" + content.cats[0] + "</strong>";
    if (content.cats.length > 1) {
      cat.innerHTML += ", ";
    }
    cat.innerHTML += content.cats.slice(1).join(", ");
    cat.innerHTML += "]";
    paper.appendChild(cat);

    let btnPanel = document.createElement("div");
    btnPanel.setAttribute("class", "btn-toolbar");
    btnPanel.setAttribute("id", "btn-toolbar-"+pId);

    let btnGroup1 = document.createElement("div");
    btnGroup1.setAttribute("class", "btn-group mr-2");
    btnGroup1.setAttribute("role", "group");

    paper.appendChild(btnPanel);
    btnPanel.appendChild(btnGroup1);

    let btnAbs = document.createElement("button");
    btnAbs.setAttribute("class", "btn btn-primary");
    btnAbs.setAttribute("data-toggle", "collapse");
    btnAbs.setAttribute("data-target", "#abs-"+pId);
    btnAbs.setAttribute("id", "btn-abs-"+pId);
    btnAbs.textContent = "Abstract";
    btnGroup1.appendChild(btnAbs);

    let btnPdf = document.createElement("a");
    btnPdf.setAttribute("class", "btn btn-primary");
    btnPdf.setAttribute("id", "btn-pdf-"+pId);
    btnPdf.setAttribute("href", content.ref_pdf);
    btnPdf.setAttribute("target", "_blank");
    btnPdf.innerHTML = "<i class='fa fa-file-pdf-o' aria-hidden='true' style='font-weight:600'></i>&nbsp; PDF";

    let btnGroup2 = document.createElement("div");
    btnGroup2.setAttribute("class", "btn-group mr-2");
    btnGroup2.setAttribute("role", "group");
    btnPanel.appendChild(btnGroup2);
    btnGroup2.appendChild(btnPdf);

    let btnArxiv = document.createElement("a");
    btnArxiv.setAttribute("class", "btn btn-primary");
    btnArxiv.setAttribute("id", "btn-arxiv-"+pId);
    btnArxiv.setAttribute("href", content.ref_web);
    btnArxiv.setAttribute("target", "_blank");
    btnArxiv.textContent = "arXiv";

    let btnGroup3 = document.createElement("div");
    btnGroup3.setAttribute("class", "btn-group mr-2");
    btnGroup3.setAttribute("role", "group");
    btnPanel.appendChild(btnGroup3);
    btnGroup3.appendChild(btnArxiv);

    let abs = document.createElement("div");
    abs.setAttribute("class", "collapse paper-abs");
    abs.setAttribute("id", "abs-"+pId);
    abs.textContent = content.abstract;
    paper.appendChild(abs);
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
      let aDate = new Date(a.date_sub);
      let bDate = new Date(b.date_sub);
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

window.onload = function() {
  var url = document.location.href;
  url = url.replace("papers", "data");

  $.get(url)
  .done(function(data) {
    document.getElementById("loading-papers").style["display"] = "none";
    DATA = data;
    renderCounters();
    renderPapers();
    $("#sort-block").css("display", "block");
  }).fail(function(jqXHR){
    // alert("Error during paper load. Please try later.");
    $("#loading-papers").text("Error during paper loading. Please try later.");
  });
  renderTitle();
  renderNov();
  renderCats();
  renderTags();

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
};

window.onscroll = function() {
  if (!DONE) {
    scrollIfNeeded();
  }
};
