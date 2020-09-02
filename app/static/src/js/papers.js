let PAPERS_TO_RENDER = 20;
let START = 0;
let DONE = false;
var VISIBLE = 0;

function scrollIfNeeded() {
  if (START > PAPERS.length) {
    DONE = true;
    return;
  }

  var scrollTop = window.scrollY;
  var windowHeight = window.innerHeight;
  var bodyHeight = document.body.clientHeight - windowHeight;
  var scrollPercentage = (scrollTop / bodyHeight);

  if(scrollPercentage > 0.9 || bodyHeight < 0) {
    START += PAPERS_TO_RENDER;
    renderPapers();
  }
}

function renderTitle() {
  title = document.getElementById("paper-list-title");
  date = new Date();
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
    title.textContent += ": " +formateDate(start) + " - " + formateDate(end)
  } else if (title.textContent.includes("month")) {
    let end = new Date;
    let start = new Date(date.setDate(date.getDate() - date.getDate() + 1));

    // TODO it's a dirty fix. Need proper treatment
    if (dateNew.getDate() === 1) {
      start = new Date(dateNew.setDate(dateNew.getDate() - 1));
    }
    title.textContent += ": " +formateDate(start) + " - " + formateDate(end);
  } else if (dateType === 4) {
    // title.textContent += ": " +formateDate(new Date(prefs.data.lastVisit));
  }
}

function renderNov() {
  prefs.data.showNov.forEach((show, num) => {
    document.getElementById("check-nov-" + num).checked = show;
  });
}

function renderCats() {
  // TODO check if there are old cats in cookies
  CATS.cats.forEach((cat, num) => {
    if (!prefs.data.catsArr.includes(cat)) {
      prefs.data.catsArr.push(cat);
      prefs.data.catsShowArr.push(true);
    }

    var parent = document.createElement("div");
    parent.setAttribute("class", "menu-item");

    var check = document.createElement("input");
    check.setAttribute("type", "checkbox");
    check.setAttribute("id", "check-cat-"+num);
    check.setAttribute("class", "check-cat");
    if (prefs.data.catsShowArr[prefs.data.catsArr.indexOf(cat)]) {
      check.checked = true;
    }
    check.onchange = function() {
      var number = event.target.getAttribute("id").split("-")[2];
      let cat = document.getElementById("cat-label-"+num).textContent;
      let index = prefs.data.catsArr.indexOf(cat);
      prefs.data.catsShowArr[parseInt(index, 10)] = document.getElementById("check-cat-"+number).checked;
      prefs.save();
      toggleVis();
    };

    var catElement = document.createElement("div");
    catElement.setAttribute("class", "menu-line-left item-cat");
    catElement.setAttribute("id", "cat-label-"+num);
    catElement.textContent = cat;
    catElement.onclick = function(event) {
      var number = event.target.getAttribute("id").split("-")[2];
      document.getElementById("check-cat-" + number).click();
    };

    var counter = document.createElement("div");
    counter.setAttribute("class", "menu-line-right");
    counter.setAttribute("id", "cat-count-"+num);
    counter.textContent = CATS.count[parseInt(num, 10)];

    document.getElementById("cats").appendChild(parent);
    parent.appendChild(check);
    parent.appendChild(catElement);
    parent.appendChild(counter);
  });
}

function renderTags() {
  TAGS.forEach((tag, num) => {
    var parent = document.createElement("div");
    parent.setAttribute("class", "menu-item");

    var tagElement = document.createElement("div");
    tagElement.setAttribute("class", "menu-line-left tag-label");
    tagElement.setAttribute("id", "tag-label-"+num);
    tagElement.setAttribute("style", "background-color: " + tag.color + "; margin: 0;");
    tagElement.textContent = tag.name;

    var counter = document.createElement("div");
    counter.setAttribute("class", "menu-line-right");
    counter.setAttribute("id", "tag-count-"+num);
    counter.textContent = tag.n_papers;

    document.getElementById("tags").appendChild(parent);
    parent.appendChild(tagElement);
    parent.appendChild(counter);
  });
}

// toggle the visibility of rendered papers
function toggleVis(start=0) {
  if (start === 0) {
    VISIBLE = 0;
  }
  for(let pId = start; pId < START + PAPERS_TO_RENDER; pId ++) {
    if (pId >= PAPERS.length) {
      break;
    }
    let paper = PAPERS[pId];
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
        let cat = prefs.data.catsArr[catId];
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

function renderPapers() {
  for(let pId = START; pId < START + PAPERS_TO_RENDER; pId ++) {
    if (PAPERS.length <= pId) {
      break;
    }
    content = PAPERS[parseInt(pId, 10)];
    var paper = document.createElement("div");
    paper.setAttribute("class", "paper");
    paper.setAttribute("id", "paper-"+pId);
    document.getElementById("paper-list-content").appendChild(paper);

    let ocoins_span = document.createElement("span");
    ocoins_span.setAttribute("class", "Z3988");
    ocoins_span.setAttribute("title", render_ocoins(content));
    document.getElementById("paper-"+pId).appendChild(ocoins_span);

    let title = document.createElement("div");
    title.setAttribute("class", "paper-title");
    title.setAttribute("id", "paper-title-"+pId);

    document.getElementById("paper-"+pId).appendChild(title);

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
    var tags = [];
    content.tags.forEach(function(tag, tagId) {
      var tagDiv = document.createElement("div");
      tagDiv.setAttribute("class", "tag-panel-item");
      tagDiv.setAttribute("style", "background-color:" + TAGS[parseInt(tag, 10)].color);
      tagDiv.textContent = TAGS[parseInt(tag, 10)].name;
      tags.push(tagDiv);
    });
    document.getElementById("paper-"+pId).appendChild(tagPanel);
    tags.forEach(function(tag){
      document.getElementById("tag-panel-"+pId).appendChild(tag);
    });
    if (tags.length === 0) {
      tagPanel.setAttribute("style", "display: none");
    }

    let au = document.createElement("div");
    au.setAttribute("class", "paper-au");
    au.textContent = content.author.join(", ");
    document.getElementById("paper-"+pId).appendChild(au);

    let date = document.createElement("div");
    date.setAttribute("id", "paper-date-"+pId);
    date.setAttribute("class", "paper-date");
    date.textContent = content.date_up

    if (content.date_sub) {
      date.textContent += " (v1: " + content.date_sub + ")";
    }
    document.getElementById("paper-"+pId).appendChild(date);

    if (content.ref_doi) {
      let ref = document.createElement("a");
      ref.setAttribute("class", "paper-doi");
      ref.setAttribute("href", content.ref_doi);
      ref.setAttribute("id", "paper-doi-"+pId);
      // BUG this stuff is not working.
      ref.innerHTML = "doi" + "\u{0020}";
      document.getElementById("paper-date-"+pId).appendChild(ref);

      let doi = document.createElement("span");
      doi.setAttribute("class", "label");
      doi.textContent = " " + content.ref_doi.split(".org/")[1];
      document.getElementById("paper-doi-"+pId).appendChild(doi);
    }

    let cat = document.createElement("div");
    cat.setAttribute("class", "paper-cat");
    cat.innerHTML = "[<strong>" + content.cats[0] + "</strong>";
    if (content.cats.length > 1) {
      cat.innerHTML += ", ";
    }
    cat.innerHTML += content.cats.slice(1).join(", ");
    cat.innerHTML += "]";
    document.getElementById("paper-"+pId).appendChild(cat);

    let btnPanel = document.createElement("div");
    btnPanel.setAttribute("class", "btn-panel");
    btnPanel.setAttribute("id", "btn-panel-"+pId);
    document.getElementById("paper-"+pId).appendChild(btnPanel);

    let btnAbs = document.createElement("button");
    btnAbs.setAttribute("class", "btn btn-paper");
    btnAbs.setAttribute("id", "btn-abs-"+pId);
    btnAbs.textContent = "Abstract";
    btnAbs.onclick = function(event) {
      let name =  "abs-" + event.target.id.split("-")[2];;
      let absBlock = document.getElementById(name);
      if (absBlock.style.display === "none" || absBlock.style.display === "") {
        absBlock.style.display = "block";
      } else {
        absBlock.style.display = "none";
      }
    }
    document.getElementById("btn-panel-"+pId).appendChild(btnAbs);

    let btnPdf = document.createElement("a");
    btnPdf.setAttribute("class", "btn btn-paper");
    btnPdf.setAttribute("id", "btn-pdf-"+pId);
    btnPdf.setAttribute("href", content.ref_pdf);
    btnPdf.setAttribute("target", "_blank");
    btnPdf.innerHTML = "<i class='fa fa-file-pdf-o' aria-hidden='true' style='font-weight:600'></i>&nbsp; PDF";
    document.getElementById("btn-panel-"+pId).appendChild(btnPdf);

    let btnArxiv = document.createElement("a");
    btnArxiv.setAttribute("class", "btn btn-paper");
    btnArxiv.setAttribute("id", "btn-arxiv-"+pId);
    btnArxiv.setAttribute("href", content.ref_web);
    btnArxiv.setAttribute("target", "_blank");
    btnArxiv.textContent = "arXiv";
    document.getElementById("btn-panel-"+pId).appendChild(btnArxiv);

    let abs = document.createElement("div");
    abs.setAttribute("class", "paper-abs");
    abs.setAttribute("id", "abs-"+pId);
    abs.textContent = content.abstract;
    document.getElementById("paper-"+pId).appendChild(abs);
  }

  toggleVis(START);

  if (parseTex) {
    MathJax.typesetPromise();
  }
  if (!DONE) {
    scrollIfNeeded();
  }
}

function render_ocoins(paper) {
  let ocoins = {
    "ctx_ver": "Z39.88-2004",
    "rft_val_fmt": encodeURIComponent("info:ofi/fmt:kev:mtx:journal"),
    // "rfr_id": encodeURIComponent("info:sid/arxivtagger.com:arxivtagger"),

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

  ocoins += paper.author.map((au) => {return "&rft.au=" + encodeURIComponent(au)}).join();

  return ocoins;
}

function formateDate(date) {
  let dateArray = date.toString().split(" ");
  return dateArray[2] + " " + dateArray[1] + " " + dateArray[3];
}

window.onload = function(event) {
  renderTitle();
  renderNov();
  renderCats();
  renderTags();
  renderPapers();

  var anchors = document.getElementsByClassName("check-nov");
  for(var i = 0; i < anchors.length; i++) {
    let anchor = anchors[i];
    anchor.onchange = function(event) {
      let number = event.target.getAttribute("id").split("-")[2];
      prefs.data.showNov[parseInt(number, 10)] = document.getElementById("check-nov-"+number).checked;
      prefs.save();
      toggleVis();
    }
  }
  anchors = document.getElementsByClassName("item-nov");
  for(var i = 0; i < anchors.length; i++) {
    let anchor = anchors[i];
    anchor.onclick = function(event) {
      let number = event.target.getAttribute("id").split("-")[1];
      document.getElementById("check-nov-"+number).click();
    }
  }
}

window.onscroll = function(event) {
  if (!DONE) {
    scrollIfNeeded();
  }
}