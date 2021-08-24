/*global MathJax, parseTex, DATA, prefs, CATS, TAGS, raiseAlert, renderPapersBase, cssVar*/
/*exported novChange */
/*eslint no-undef: "error"*/

let PAPERS_PER_PAGE = 40;
var titleRendered = false;

var TAGSSHOW = [];
var PAGE = 1;
var VISIBLE = 0;

const checkPaperVis = (paper, catsShow, allVisible, TAGSSHOW) => {
  /** Check if the paper passes visibility rules.
   * Logic: if check-box is off --> cut all the affected papers
   */

  if ((prefs.data.showNov[0] === true || !(paper.nov & 1)) &&
      (prefs.data.showNov[1] === true || !(paper.nov & 2)) &&
      (prefs.data.showNov[2] === true || !(paper.nov & 4)) &&
      // filter on categories check boxes
      catsShow.filter((value) => paper.cats.includes(value)).length > 0 &&
      // filter on tags
      (allVisible || (TAGSSHOW.filter((value, index) => value && paper.tags.includes(index)).length > 0))
      ) {
    VISIBLE += 1;
    return true;
  } else {

    return false;
  }
};

function sortFunction(a, b, order=true) {
  return order? a - b : b - a;
}

function sortPapers() {
  // Completely reset the rendering process
  document.getElementById("loading-papers").style["display"] = "block";
  let sortMethod = $("#sort-sel").val();
  // tags
  if (sortMethod.includes("tag")) {

    DATA.papersVis.sort((a, b) => {
      if (b.tags.length === 0 && a.tags.length !== 0) {
        return sortMethod === "tag-as" ? -1 : 1;
      }
      if (b.tags.length !== 0 && a.tags.length === 0) {
        return sortMethod === "tag-as" ? 1 : -1;
      }
      if (b.tags.length === 0 && a.tags.length === 0) {
        return -1;
      }
      return sortFunction(a.tags[0], b.tags[0],
                          sortMethod === "tag-as"? true : false);
    });
  }
  // dates
  if (sortMethod.includes("date-up")) {
    DATA.papersVis.sort((a, b) => {
      let aDate = new Date(a.date_up);
      let bDate = new Date(b.date_up);
      return sortFunction(aDate, bDate,
                          sortMethod === "date-up_des"? true : false);
    });
  }

  if (sortMethod.includes("date-sub")) {
    DATA.papersVis.sort((a, b) => {
      let aDate = new Date(a.date_sub);
      let bDate = new Date(b.date_sub);
      return sortFunction(aDate, bDate,
                          sortMethod === "date-sub_des"? true : false);
    });
  }

  // caregories
  if (sortMethod.includes("cat")) {
    DATA.papersVis.sort((a, b) => {
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

const cleanPageList = () => {
  /** Clean the displayd papers.
   */
  $("#paper-list-content").empty();
  document.getElementById("loading-papers").style["display"] = "block";
  document.getElementById("no-paper").style["display"] = "none";
};

const cleanPagination = () => {
  /** Remove page links
   * Required when the number of pages is changing e.g. at checkbox click
   */
  document.getElementById("pagination").style["display"] = "none";

  let oldPage = document.getElementsByClassName("pageTmp");
  let len = oldPage.length;
  for (let i = 0; i < len; i++) {
    oldPage[0].remove();
  }
};

function selectActivePage() {
  // clean old pagination artefacts
  let oldPage = document.getElementsByClassName("page-item");
  for (let i = 0; i < oldPage.length; i++) {
    oldPage[parseInt(i, 10)].classList.remove("active");
  }
  document.getElementById("Page1").classList.remove("active");
  document.getElementById("prev").classList.add("disabled");
  document.getElementById("next").classList.add("disabled");

  if (PAGE === 1) {
    document.getElementById("Page1").classList.add("active");
  } else {
    document.getElementById("prev").classList.remove("disabled");
  }

  let nPages = Math.floor(VISIBLE/PAPERS_PER_PAGE) + 1;
  if (PAGE !== nPages) {
    document.getElementById("next").classList.remove("disabled");
  }

  // make the current page active
  document.getElementById("Page" + PAGE.toString()).classList.add("active");
}

const resetPage = (p="1") => {
  /** Go to first page.
   * Only href update. No actual page reload. Should be called manually if needed.
   */
  PAGE = parseInt(p, 10);
  const regex = /page=[0-9]*/i;
  let hrefPage = location.href.replace(regex, "page=" + p);
  // remove focus from page button
  document.activeElement.blur();
  history.pushState({}, document.title, hrefPage);
  pageUpdate();
};

function pageLinkClick(event) {
  /** Listener for the click on page number
   */
  event.preventDefault();

  // do nothing if the link is disabled
  if (event.target.parentElement.classList.contains("disabled")) {
    return;
  }
  cleanPageList();

  let page = event.target.textContent;

  if (page === "Previous") {
    page = PAGE - 1;
  } else if (page === "Next") {
    page = PAGE + 1;
  } else {
    page = parseInt(page, 10);
  }

  resetPage(page);
}

$(".page-link").click((event) => pageLinkClick(event));

function renderPagination() {
  /** Render all the page links at the bottom of the page.
   */

  let nPages = Math.floor(VISIBLE/PAPERS_PER_PAGE) + 1;
  for (let i = 2; i <= nPages; i++) {
    let newPageItem = document.createElement("li");
    newPageItem.className = "page-item pageTmp";
    newPageItem.id = "Page" + i.toString();

    let newPageRef = document.createElement("a");
    newPageRef.className = "page-link";
    newPageRef.textContent = i;
    newPageRef.href = "#";
    newPageRef.addEventListener("click", pageLinkClick);

    newPageItem.appendChild(newPageRef);
    document.getElementById("Page" + (i-1).toString()).after(newPageItem);
  }

  // make pagination visible
  document.getElementById("pagination").style["display"] = "block";
}

function addBookmark(event) {
  /** Listener for add bookmark button.
   */

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

function renderPapers(renderPages=true) {
  if (!titleRendered) {
    $("#paper-list-title").text($("#paper-list-title").text() + DATA.title);
    titleRendered = true;
  }

  let start = PAPERS_PER_PAGE * (PAGE - 1);

  for (let pId = start;
           pId < Math.min(start + PAPERS_PER_PAGE, DATA.papersVis.length);
           pId++) {

    let content = DATA.papersVis[parseInt(pId, 10)];
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

  document.getElementById("loading-papers").style["display"] = "none";

  if (parseTex) {
    MathJax.typesetPromise();
  }

  if (renderPages) {
    renderPagination();
    selectActivePage();
  }
}

const pageUpdate = () => {
  /** Clean the page, update the page number and render new papers
   */
  cleanPageList();
  window.scrollTo(0,0);
  // WARNING not a very accurate parsing
  PAGE = parseInt(location.href.split("page=")[1].split("&")[0], 10);
  selectActivePage();
  renderPapers(false);
};

// toggle the visibility of rendered papers
function filterVisiblePapers() {
  /** Select papers that should be visible.
   * Filter papers from the backend according to visibility settings at the front-end.
   * In case of visibility settings change:
   * call filterVisiblePapers() that will call renderPapers()
   * At any function call return to 1st page.
   *
   * TODO think about promise chaining?
   */

  VISIBLE = 0;
  cleanPageList();
  cleanPagination();

  // create a list of categories that are visible based on checkbox selection
  let catsShow = [];
  for (let key in prefs.data.catsArr) {
    if (prefs.data.catsArr[`${key}`]) {
      catsShow.push(key);
    }
  }

  let allVisible = TAGSSHOW.every((x) => x);

  DATA.papersVis = DATA.papers.filter((paper) => checkPaperVis(paper,
                                                                 catsShow,
                                                                 allVisible,
                                                                 TAGSSHOW
                                                                 )
  );

  let nPages = Math.floor(VISIBLE/PAPERS_PER_PAGE + 1);
  let plural = nPages > 1 ? "s" : "";
  $("#passed").text(VISIBLE + " results (" + nPages + " page" + plural + ")");

  if (!VISIBLE) {
    $("#paper-list-content").empty();
    document.getElementById("loading-papers").style["display"] = "none";
    document.getElementById("pagination").style["display"] = "none";
    document.getElementById("no-paper").style["display"] = "block";
    return;
  }

  setTimeout(function() {
    sortPapers();
  }, 0);

  setTimeout(function() {
    renderPapers();
  }, 0);
}

// ****************** Checkbox click listeners ***************************

function checkCat(event) {
  /** Click on category checkbox.
   */
  let number = event.target.getAttribute("id").split("-")[2];
  let cat = document.getElementById("cat-label-" + number).textContent;
  prefs.data.catsArr[`${cat}`] = document.getElementById("check-cat-" + number).checked;
  // save the cookies
  prefs.save();
  resetPage();
  setTimeout(function () {
    filterVisiblePapers();
  }, 0);
}

const tagBorder = (num, border) => {
  TAGSSHOW[parseInt(num, 10)] = border;

  $("#tag-label-" + num).css("border-color",
                             border ? cssVar("--tag_border_color") : "transparent"
                             );
};

const checkTag = (event) => {
  /** Click on tag.
   */
  let number = event.target.getAttribute("id").split("-")[2];
  let thisVisible = TAGSSHOW[parseInt(number, 10)];
  let allVisible = TAGSSHOW.every((x) => x);

  // if this tag is selected
  if (thisVisible) {
    if (allVisible) {
      // select only this tag
      // make all others invisible
      TAGSSHOW = TAGSSHOW.map(() => false);

      // but this one visible
      tagBorder(number, true);
    } else {
      // hide this tag
      TAGSSHOW[parseInt(number, 10)] = false;
      // if this was the only left tag
      if (TAGSSHOW.filter((value) => value).length === 0) {
        // make all tags visible
        TAGSSHOW = TAGSSHOW.map(() => true);
      }
      // remove border
      $("#tag-label-" + number).css("border-color", "transparent");
    }
  // if this tag is UNselected
  } else {
    // make this tag selected
    tagBorder(number, true);
  }
  resetPage();
  setTimeout(function () {
    filterVisiblePapers();
  }, 0);
};

function novChange(number) {
  /** CLick on novelty checkbox.
   */
  prefs.data.showNov[parseInt(number, 10)] = document.getElementById("check-nov-"+number).checked;
  prefs.save();
  resetPage();
  setTimeout(function () {
    filterVisiblePapers();
  }, 0);
}

// ********************** RENDERS  ***************************

function renderCats() {
  // clean unused categories from cookies
  let unusedCats = Object.keys(prefs.data.catsArr).filter((x) => !CATS.includes(x));
  unusedCats.forEach((cat) => delete prefs.data.catsArr[`${cat}`]);

  CATS.forEach((cat, num) => {
    // if category not in cookies visibility dictionary --> add it
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

  // save cookies
  prefs.save();
}

function renderTags() {
  TAGS.forEach((tag, num) => {
    // store tag in settings for visibility control
    // do NOT store this values in cookies
    // keep it just for the current session

    // TODO think about storage in cookies?
    TAGSSHOW.push(true);

    let parent = document.createElement("div");
    parent.className = "d-flex justify-content-between align-items-center";

    let tagElement = document.createElement("div");
    tagElement.className = "tag-label";
    tagElement.id = "tag-label-"+num;
    tagElement.style = "background-color: " + tag.color;
    tagElement.textContent = tag.name;

    tagElement.addEventListener("click", checkTag);

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

// change sort selector
$("#sort-sel").change(() => {
  $("#sorting-proc").css("display", "block");
  sortPapers();
  // clean paper list before display new sorted list
  cleanPageList();
  PAGE = 1;
  setTimeout(function () {
    renderPapers(false);
    $("#sorting-proc").css("display", "none");
  }, 0);
});

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
  // a fix that prevent browser scrolling on "back" button
  // essential for nice work of window.onpopstate
  history.scrollRestoration = "manual";

  var url = document.location.href;
  url = url.replace("papers", "data");

  PAGE = url.split("page=")[1];
  PAGE = parseInt(PAGE.split("&")[0]);

  // Get paper data from backend
  $.get(url)
  .done(function(data) {
    DATA = data;
    renderCounters();
    filterVisiblePapers();
    $("#sort-block").css("display", "block");
  }).fail(function() {
    $("#loading-papers").text("Oooops, arxivtag experienced an internal error processing your papers. We are working on fixing that. Please, try later.");
  });
  renderNov();
  renderCats();
  renderTags();
};

window.onpopstate = function() {
  /** catch the "back" button usage for page switch
   */
  pageUpdate();
}
