/*global MathJax, parseTex, DATA, prefs, CATS, TAGS, raiseAlert, renderPapersBase, cssVar*/
/*exported novChange */
/*eslint no-undef: "error"*/

let PAPERS_PER_PAGE = 40;

var PAGE = 1;
var VISIBLE = 0;

var BOOK_BTN = -1;

const checkPaperVis = (paper, catsShow, allVisible, tagsShow) => {
  /** Check if the paper passes visibility rules.
   * Logic: if check-box is off --> cut all the affected papers
   */

  if ((prefs.data.showNov[0] === true || !(paper.nov & 1)) &&
      (prefs.data.showNov[1] === true || !(paper.nov & 2)) &&
      (prefs.data.showNov[2] === true || !(paper.nov & 4)) &&
      // filter on categories check boxes
      catsShow.filter((value) => paper.cats.includes(value)).length > 0 &&
      // filter on tags
      (allVisible || (tagsShow.filter((value, index) => value && paper.tags.includes(index)).length > 0))
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
  /** Sort the papers.
   * Only papers marked as visible will be sorted.
   */
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
  /** Clean the displayd papers. Display "loading" wheel
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

const pageChange = (p="1", push=true) => {
  /** Go to a given  page.
   * p == -1 force to read the page number from href
   * do NOT load the new content. Should be called separately
   */
  // clean all the previous content
  cleanPageList();
  PAGE = parseInt(p, 10);
  if (PAGE === -1) {
    // WARNING not a very accurate parsing
    PAGE = parseInt(location.href.split("page=")[1].split("&")[0], 10);
  }

  // scroll to top
  window.scrollTo(0,0);

  // remove focus from page button
  document.activeElement.blur();

  if (push) {
    const regex = /page=[0-9]*/i;
    let hrefPage = location.href.replace(regex, "page=" + p);
    history.pushState({}, document.title, hrefPage);
  }
};

const hideListPopup = () => {
  let popupContent = document.getElementById("lists-popup");
  popupContent.classList.remove("full-width");
    setTimeout(() => {
      // check for the case of extremely fast clickes
      // prevent hiding the border around new drawing of the popup
      if (!popupContent.classList.contains("full-width")) {
        popupContent.style.borderStyle = "none";
      }
    }, 200);
};

const addBookmark = (event) => {
  /** Listener for add bookmark button.
   */

  if (!event.target.id.includes("btn-book") &&
      !event.target.id.includes("a-icon")) {
    return;
  }

   let target = event.target;
   if (event.target.id.includes("a-icon")) {
    target = target.parentElement;
   }

   let top = target.getBoundingClientRect().top;
   let left = target.getBoundingClientRect().left;
   let popup = document.getElementById("lists-popup-wrap");
   let popupContent = document.getElementById("lists-popup");

   let sleep = false;
   // if already visible around this button --> hide
   if (popupContent.classList.contains("full-width")) {
    hideListPopup();
    sleep = true;
    // if the button is the same --> interupt
    if (BOOK_BTN === target.id.split("-")[2]) {
      return;
    }
   }

   setTimeout(() => {
     // put on the left from button
     popup.style.top = String(top + window.scrollY) + "px";
     popup.style.left = String(left + 60 + window.scrollX) + "px";
     popupContent.style.borderStyle = "solid";
     popupContent.classList.add("full-width");
     BOOK_BTN = target.id.split("-")[2];
   }, sleep ? 200 : 0);
};

document.onclick = (event) => {
  /** Fix to hide popup when click outside the popup window
   * Click on the button is handled by the button click event
   * Could not use "focusout" listener as it prevents
   * firing popup content click event.
   */
  let popupContent = document.getElementById("lists-popup");
  if (!event.target.classList.contains("list-name") &&
      !event.target.id.includes("btn-book") &&
      !event.target.id.includes("a-icon") &&
      popupContent.classList.contains("full-width")) {
    hideListPopup();
  }
}

function renderPapers() {

  let start = PAPERS_PER_PAGE * (PAGE - 1);

  // prevent UB in case of pressing "back" button,
  // If number of visible papers if too low to go to s specified page,
  // then go to 1st one
  if (start >= DATA.papersVis.length) {
    pageChange(1, true);
    start = 0;
  }

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
    // btnBook.onclick = addEventListener("focusout", hideListPopup);

    let btnGroup4 = document.createElement("div");
    btnGroup4.className = "btn-group mr-2";
    btnGroup4.role = "group";
    btnPanel.appendChild(btnGroup4);
    btnGroup4.appendChild(btnBook);
  }

  document.getElementById("loading-papers").style["display"] = "none";

  selectActivePage();

  if (parseTex) {
    MathJax.typesetPromise();
  }
}

function pageLinkClick(event) {
  /** Listener for the click on page number
   */
  event.preventDefault();

  // do nothing if the link is disabled
  if (event.target.parentElement.classList.contains("disabled")) {
    return;
  }
  // cleanPageList();

  let page = event.target.textContent;

  if (page === "Previous") {
    page = PAGE - 1;
  } else if (page === "Next") {
    page = PAGE + 1;
  } else {
    page = parseInt(page, 10);
  }

  pageChange(page);
  renderPapers();
}

$(".page-link").click((event) => pageLinkClick(event));

function doRenderPagination() {
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

// toggle the visibility of rendered papers
function filterVisiblePapers() {
  /** Select papers that should be visible.
   * Filter papers from the backend according to visibility settings at the front-end.
   * At any function call return to 1st page.
   */

  VISIBLE = 0;
  cleanPagination();

  // create a list of categories that are visible based on checkbox selection
  let catsShow = [];
  for (let key in prefs.data.catsArr) {
    if (prefs.data.catsArr[`${key}`]) {
      catsShow.push(key);
    }
  }

  let tagsShow = [];
  prefs.data.tagsArr.forEach((tag) => {
    tagsShow.push(tag.vis);
  });

  let allVisible = prefs.data.tagsArr.every((x) => x.vis);

  DATA.papersVis = DATA.papers.filter((paper) => checkPaperVis(paper,
                                                               catsShow,
                                                               allVisible,
                                                               tagsShow
                                                               )
  );

  let text = String(VISIBLE) + " result";
  text += VISIBLE > 1 ? "s" : "";
  text += " over " + String(DATA.papers.length);
  $("#passed").text(text);

  if (!VISIBLE) {
    $("#paper-list-content").empty();
    document.getElementById("loading-papers").style["display"] = "none";
    document.getElementById("pagination").style["display"] = "none";
    document.getElementById("no-paper").style["display"] = "block";
    return;
  }

  setTimeout(() => {
    renderPapers();
    doRenderPagination();
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
  pageChange();
  setTimeout(function () {
    filterVisiblePapers();
  }, 0);
}

const tagBorder = (num, border) => {
  prefs.data.tagsArr[parseInt(num, 10)].vis = border;

  $("#tag-label-" + num).css("border-color",
                             border ? cssVar("--tag_border_color") : "transparent"
                             );
};

const checkTag = (event) => {
  /** Click on tag.
   */
  let target = event.target;
  while (target.getAttribute("id") === null) {
    target = target.parentElement;
  }
  let number = target.getAttribute("id").split("-")[2];
  let thisVisible = prefs.data.tagsArr[parseInt(number, 10)].vis;
  let allVisible = prefs.data.tagsArr.every((x) => x.vis);

  // if this tag is selected
  if (thisVisible) {
    if (allVisible &&
       (target.style.borderColor === "transparent" ||
        target.style.borderColor === undefined)) {
      // select only this tag
      // make all others invisible
      prefs.data.tagsArr.forEach((tag) => {tag.vis = false;});

      // but this one visible
      tagBorder(number, true);
    } else {
      // hide this tag
      prefs.data.tagsArr[parseInt(number, 10)].vis = false;
      // if this was the only left tag
      if (prefs.data.tagsArr.filter((value) => value.vis).length === 0) {
        // make all tags visible
        prefs.data.tagsArr.forEach((tag) => {tag.vis = true;});
      }
      // remove border
      $("#tag-label-" + number).css("border-color", "transparent");
    }
  // if this tag is UNselected
  } else {
    // make this tag selected
    tagBorder(number, true);
  }
  prefs.save();
  pageChange();
  setTimeout(function () {
    filterVisiblePapers();
  }, 0);
};

function novChange(number) {
  /** CLick on novelty checkbox.
   */
  prefs.data.showNov[parseInt(number, 10)] = document.getElementById("check-nov-"+number).checked;
  prefs.save();
  pageChange();
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
  let tagNames = TAGS.map((x) => x.name);
  let unusedTags = [];

  TAGS.forEach((tag, num) => {

    if (!prefs.data.tagsArr.map((x) => x.name).includes(tag.name)) {
      prefs.data.tagsArr.push({"name": tag.name,
                               "vis": true,
                               "color": tag.color,
                               "order": num
                              })
    } else {
      let cookTag = prefs.data.tagsArr.find((tagC) => tagC.name === tag.name);
      if (cookTag.order !== num) {
        cookTag.order = num;
      }
    }
  });

  prefs.data.tagsArr.sort((a, b) => {return a.order - b.order;});

  let allVisible = prefs.data.tagsArr.every((x) => x.vis);

  let num = 0;
  for (let tagIter = 0; tagIter < prefs.data.tagsArr.length; tagIter++) {
    let tag = prefs.data.tagsArr[parseInt(tagIter, 10)];
    if (!tagNames.includes(tag.name)) {
      unusedTags.push(num);
      continue;
    }

    let parent = document.createElement("div");
    parent.className = "d-flex justify-content-between align-items-center";

    let tagElement = document.createElement("div");
    tagElement.className = "tag-label";
    tagElement.id = "tag-label-"+num;
    tagElement.style = "background-color: " + tag.color;
    tagElement.textContent = tag.name;

    tagElement.addEventListener("click", checkTag);

    tagElement.style.borderColor =
                    tag.vis && !allVisible ? cssVar("--tag_border_color") : "transparent";

    let counter = document.createElement("div");
    counter.className = "counter";
    counter.id = "tag-count-"+num;
    counter.textContent = "0";

    document.getElementById("tags").appendChild(parent);
    parent.appendChild(tagElement);
    parent.appendChild(counter);

    num++;
  }

  if (parseTex) {
    MathJax.typesetPromise();
  }
  unusedTags.forEach((num) => prefs.data.tagsArr.splice(num, 1));
  prefs.save();
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
  // clean the content
  cleanPageList();
  // got to first page
  pageChange();
  setTimeout(() => {
    // sort the papers that are supposed to be visible.
    sortPapers();
    // render the main page content
    // #pages is still the same, so no point of rendering from scratch
    renderPapers();
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

const listClick = (event) => {
  let url = "add_bm";
  let target = event.target;
  while (!target.classList.contains("list-name")) {
    target = target.parentElement;
  }
  let num = target.getAttribute("id");
  let paper = DATA.papers[parseInt(BOOK_BTN, 10)];
  // we take paper id w/o version --> do not overload paper DB
  $.post(url, {"paper_id": paper.id.split("v")[0],
               "list_id": num
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

  hideListPopup();
};

const renderLists = () => {
 /** Render pop-up window with page lists
  */
  DATA.lists.forEach((list) => {
    let listDom = document.createElement("div");
    listDom.textContent = list.name;
    listDom.classList = "list-name";
    listDom.id = String(list.id);
    listDom.addEventListener("click", listClick);
    document.getElementById("lists-popup").appendChild(listDom);
  });
};

window.onload = function() {
  // a fix that prevent browser scrolling on "back" button
  // essential for nice work of window.onpopstate
  history.scrollRestoration = "manual";

  var url = document.location.href;
  url = url.replace("papers", "data");

  PAGE = url.split("page=")[1];
  PAGE = parseInt(PAGE.split("&")[0], 10);

  // Get paper data from backend
  $.get(url)
  .done(function(data) {
    DATA = data;
    renderCounters();
    // update page title with detailed dates
    $("#paper-list-title").text($("#paper-list-title").text() + DATA.title);
    filterVisiblePapers();
    renderLists();
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
  pageChange(-1, false);
  renderPapers();
};
