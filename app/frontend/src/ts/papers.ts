/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {renderPapersBase, Paper, List, Data} from "./paper_basic";
import {raiseAlert, cssVar, Tag, Preference} from "./layout";
import {sortPapers} from "./paper_sorts";

declare const MathJax;
declare const __parseTex__: boolean;

declare const __TAGS__: Array<Tag>;
declare const __CATS__: Array<string>;

// global pagination vars
let PAGE = 1;
let VISIBLE = 0;
let BOOK_BTN = -1;
const PAPERS_PER_PAGE = 40;

// global DATA var
// Contain the information about the papers
// The var will be filled after the AJAX request just after page load
let DATA: Data;

const PREF = new Preference();

const checkPaperVis = (paper: Paper,
                       catsShow: Array<string>,
                       allVisible: boolean,
                       tagsShow: Array<boolean>
                        ): boolean => {
    /** Check if the paper passes visibility rules.
     * Logic: if check-box is off --> cut all the affected papers
     */

    if ((PREF.novArr[0] === true || !(paper.nov & 1)) &&
        (PREF.novArr[1] === true || !(paper.nov & 2)) &&
        (PREF.novArr[2] === true || !(paper.nov & 4)) &&
        // filter on categories check boxes
        catsShow.filter((value: string) => paper.cats.includes(value)).length > 0 &&
        // filter on tags
        (allVisible ||
            (tagsShow.filter((value: boolean,
                              index: number
                             ) => value && paper.tags.includes(index)).length > 0))
    ) {
        VISIBLE += 1;
        return true;
    } else {

        return false;
    }
};

const cleanPageList = (): void => {
    /** Clean the displayed papers. Display "loading" wheel
     */
    document.getElementById("paper-list-content").innerHTML = "";
    document.getElementById("loading-papers").style["display"] = "block";
    document.getElementById("no-paper").style["display"] = "none";
};

const cleanPagination = (): void => {
    /** Remove page links
     * Required when the number of pages is changing e.g. at checkbox click
     */
    document.getElementById("pagination").style["display"] = "none";

    const oldPage = document.getElementsByClassName("pageTmp");
    const len = oldPage.length;
    for (let i = 0; i < len; i++) {
        oldPage[0].remove();
    }
};

const selectActivePage = (): void => {
    // clean old pagination artefacts
    const oldPage = document.getElementsByClassName("page-item");
    for (let i = 0; i < oldPage.length; i++) {
        oldPage[`${i}`].classList.remove("active");
    }
    document.getElementById("Page1").classList.remove("active");
    document.getElementById("prev").classList.add("disabled");
    document.getElementById("next").classList.add("disabled");

    if (PAGE === 1) {
        document.getElementById("Page1").classList.add("active");
    } else {
        document.getElementById("prev").classList.remove("disabled");
    }

    const nPages = Math.floor((VISIBLE-1)/PAPERS_PER_PAGE) + 1;
    if (PAGE !== nPages) {
        document.getElementById("next").classList.remove("disabled");
    }

    // make the current page active
    document.getElementById("Page" + PAGE.toString()).classList.add("active");
};

const pageChange = (p = 1, push = true): void => {
    /** Go to a given  page.
     * p == -1 force to read the page number from href
     * do NOT load the new content. Should be called separately
     */
    // clean all the previous content
    cleanPageList();
    PAGE = p;
    if (PAGE === -1) {
        // WARNING not a very accurate parsing
        PAGE = parseInt(location.href.split("page=")[1].split("&")[0], 10);
    }

    // scroll to top
    window.scrollTo(0,0);

    // remove focus from page button
    (document.activeElement as HTMLElement).blur();

    if (push) {
        const regex = /page=\d*/i;
        const hrefPage = location.href.replace(regex, "page=" + p);
        history.pushState({}, document.title, hrefPage);
    }
};

const hideListPopup = (): void => {
    const popupContent = document.getElementById("lists-popup");
    popupContent.classList.remove("full-width");
    setTimeout(() => {
        // check for the case of extremely fast clickes
        // prevent hiding the border around new drawing of the popup
        if (!popupContent.classList.contains("full-width")) {
            popupContent.style.borderStyle = "none";
        }
    }, 200);
};

const addBookmark = (event: MouseEvent): void => {
    /** Listener for add bookmark button.
     */

    let target = event.target as HTMLElement;

    if (!target.id.includes("btn-book") &&
        !target.id.includes("a-icon")) {
        return;
    }

    if (target.id.includes("a-icon")) {
        target = target.parentElement;
    }

    const top = target.getBoundingClientRect().top;
    const left = target.getBoundingClientRect().left;
    const popup = document.getElementById("lists-popup-wrap");
    const popupContent = document.getElementById("lists-popup");

    let sleep = false;
    // if already visible around this button --> hide
    if (popupContent.classList.contains("full-width")) {
        hideListPopup();
        sleep = true;
        // if the button is the same --> interrupt
        if (BOOK_BTN === parseInt(target.id.split("-")[2], 10)) {
            return;
        }
    }

    setTimeout((): void => {
        // put on the left from button

        if (window.innerWidth - 60 - window.scrollX - left < 200) {
            // on small screen put popup on the left bottom
            popup.style.top = String(top + window.scrollY + 50) + "px";
            popup.style.left = String(left - 100 + window.scrollX) + "px";
        } else {
            // im the other case put popup on the right
            popup.style.top = String(top + window.scrollY) + "px";
            popup.style.left = String(left + 60 + window.scrollX) + "px";
        }
        popupContent.style.borderStyle = "solid";
        popupContent.classList.add("full-width");
        BOOK_BTN = parseInt(target.id.split("-")[2], 10);
    }, sleep ? 200 : 0);
};

document.onclick = (event: MouseEvent) => {
    /** Fix to hide popup when click outside the popup window
     * Click on the button is handled by the button click event
     * Could not use "focusout" listener as it prevents
     * firing popup content click event.
     */
    const target = event.target as HTMLElement;
    const popupContent = document.getElementById("lists-popup");
    if (!target.classList.contains("list-name") &&
        !target.id.includes("btn-book") &&
        !target.id.includes("a-icon") &&
        popupContent.classList.contains("full-width")) {
        hideListPopup();
    }
};

const renderPapers = (): void => {

    let start = PAPERS_PER_PAGE * (PAGE - 1);

    // prevent UB in case of pressing "back" button,
    // If number of visible papers if too low to go to s specified page,
    // then go to 1st one
    if (DATA.papersVis === undefined || start >= DATA.papersVis.length) {
        pageChange(1, true);
        start = 0;
    }

    for (let pId = start;
         pId < Math.min(start + PAPERS_PER_PAGE, DATA.papersVis.length);
         pId++) {

        const content = DATA.papersVis[`${pId}`];
        const paperBase = renderPapersBase(content, pId);
        const btnPanel = paperBase[1];

        // add bookmark button
        const btnBook = document.createElement("button");
        btnBook.className = "btn btn-primary";
        btnBook.id = "btn-book-" + pId;
        btnBook.innerHTML = "<i class='fa fa-bookmark' aria-hidden='true' id='a-icon-" + pId + "'></i>";
        btnBook.onclick = addBookmark;

        const btnGroup4 = document.createElement("div");
        btnGroup4.className = "btn-group mr-2";
        btnPanel.appendChild(btnGroup4);
        btnGroup4.appendChild(btnBook);
    }

    document.getElementById("loading-papers").style["display"] = "none";

    selectActivePage();

    if (__parseTex__) {
        MathJax.typesetPromise();
    }
};

const pageLinkClick = (event: MouseEvent) => {
    /** Listener for the click on page number
     */
    event.preventDefault();

    const target = event.target as HTMLElement;
    // do nothing if the link is disabled
    if (target.parentElement.classList.contains("disabled")) {
        return;
    }

    const pageStr = target.textContent;
    let page: number;

    if (pageStr === "Previous") {
        page = PAGE - 1;
    } else if (pageStr === "Next") {
        page = PAGE + 1;
    } else {
        page = parseInt(pageStr, 10);
    }

    pageChange(page);
    renderPapers();
};

const doRenderPagination = (): void => {
    /** Render all the page links at the bottom of the page.
     */

    const nPages = Math.floor((VISIBLE-1)/PAPERS_PER_PAGE) + 1;
    for (let i = 2; i <= nPages; i++) {
        const newPageItem = document.createElement("li");
        newPageItem.className = "page-item pageTmp";
        newPageItem.id = "Page" + i.toString();

        const newPageRef = document.createElement("a");
        newPageRef.className = "page-link";
        newPageRef.textContent = String(i);
        newPageRef.href = "#";
        newPageRef.addEventListener("click", pageLinkClick);

        newPageItem.appendChild(newPageRef);
        document.getElementById("Page" + (i-1).toString()).after(newPageItem);
    }

    // make pagination visible
    document.getElementById("pagination").style["display"] = "block";
};

// toggle the visibility of rendered papers
const filterVisiblePapers = (): void => {
    /** Select papers that should be visible.
     * Filter papers from the backend according to visibility settings at the front-end.
     * At any function call return to 1st page.
     */

    VISIBLE = 0;
    cleanPagination();

    // create a list of categories that are visible based on checkbox selection
    const catsShow = [];
    for (const key in PREF.catsArr) {
        if (PREF.catsArr[`${key}`]) {
            catsShow.push(key);
        }
    }

    const tagsShow = [];
    PREF.tagsArr.forEach((tag: Tag) => {
        tagsShow.push(tag.vis);
    });

    const allVisible = PREF.tagsArr.every((x: Tag) => x.vis) &&
        (document.getElementById("tag-label-0") === null ||
        document.getElementById("tag-label-0").style.borderColor === "transparent");

    if (DATA == null || DATA.papers == null || DATA.papers.length === 0) {
        console.warn("No papers in DATA.papers during filterVisiblePapers() call");
        document.getElementById("no-paper").style["display"] = "block";
        document.getElementById("loading-papers").style["display"] = "none";
        return;
    }

    DATA.papersVis = DATA.papers.filter((paper: Paper) => checkPaperVis(paper,
            catsShow,
            allVisible,
            tagsShow
        )
    );

    let text = String(VISIBLE) + " result";
    text += VISIBLE > 1 ? "s" : "";
    text += " over " + String(DATA.papers.length);
    document.getElementById("passed").textContent = text;

    if (!VISIBLE) {
        document.getElementById("paper-list-content").innerHTML = "";
        document.getElementById("loading-papers").style["display"] = "none";
        document.getElementById("pagination").style["display"] = "none";
        document.getElementById("no-paper").style["display"] = "block";
        return;
    }

    setTimeout(() => {
        renderPapers();
        doRenderPagination();
    }, 0);
};

// ****************** Checkbox click listeners ***************************

const checkCat = (event: MouseEvent): void => {
    /** Click on category checkbox.
     */
    const number = (event.target as HTMLElement).id.split("-")[2];
    const cat = document.getElementById("cat-label-" + number).textContent;
    PREF.catsArr[`${cat}`] = (document.getElementById("check-cat-" + number) as HTMLInputElement).checked;
    // save the cookies
    PREF.save();
    pageChange();
    setTimeout(function () {
        filterVisiblePapers();
    }, 0);
};

const tagBorder = (num: number, border: boolean): void => {
    PREF.tagsArr[num].vis = border;
    document.getElementById("tag-label-" + String(num)).style.borderColor = border ? cssVar("--tag_border_color") : "transparent";
};

const checkTag = (event: MouseEvent) => {
    /** Click on tag.
     */
    let target = event.target as HTMLElement;
    while (target.className !== "tag-label") {
        target = target.parentElement;
    }
    const number = parseInt(target.id.split("-")[2], 10);
    const thisVisible = PREF.tagsArr[number].vis;
    const allVisible = PREF.tagsArr.every((x: Tag) => x.vis);

    // if this tag is selected
    if (thisVisible) {
        if (allVisible &&
            (target.style.borderColor === "transparent" ||
                typeof target.style.borderColor === "undefined")) {
            // select only this tag
            // make all others invisible
            PREF.tagsArr.forEach((tag: Tag) => {tag.vis = false;});

            // but this one visible
            tagBorder(number, true);
        } else {
            // hide this tag
            PREF.tagsArr[number].vis = false;
            // if this was the only left tag
            if (PREF.tagsArr.filter((value: Tag) => value.vis).length === 0) {
                // make all tags visible
                PREF.tagsArr.forEach((tag: Tag) => {tag.vis = true;});
            }
            // remove border
            document.getElementById("tag-label-" + number).style.borderColor = "transparent";
        }
        // if this tag is UNselected
    } else {
        // make this tag selected
        tagBorder(number, true);
    }
    PREF.save();
    pageChange();
    setTimeout(function () {
        filterVisiblePapers();
    }, 0);
};

const novChange = (event: MouseEvent): void => {
    /** CLick on novelty checkbox.
     */
    const number = parseInt((event.target as HTMLElement).id.split("-")[2], 10);
    PREF.novArr[number] = (document.getElementById("check-nov-"+number) as HTMLInputElement).checked;
    PREF.save();
    pageChange();
    setTimeout(function () {
        filterVisiblePapers();
    }, 0);
};

// ********************** RENDERS  ***************************

const renderCats = (): void => {
    // clean unused categories from cookies
    const unusedCats = Object.keys(PREF.catsArr).filter((x: string) => !__CATS__.includes(x));
    unusedCats.forEach((cat: string) => delete PREF.catsArr[`${cat}`]);

    __CATS__.forEach((cat: string, num: number) => {
        // if category not in cookies visibility dictionary --> add it
        if (!(cat in PREF.catsArr)) {
            PREF.catsArr[`${cat}`] = true;
        }

        const parent = document.createElement("div");
        parent.className = "d-flex menu-item";

        const form = document.createElement("div");
        form.className = "form-check";

        const check = document.createElement("input");
        check.setAttribute("type", "checkbox");
        check.id = "check-cat-"+num;
        check.className = "form-check-input check-cat";
        // read visibility from cookies
        check.checked = PREF.catsArr[`${cat}`];
        check.addEventListener("click", checkCat);

        // category name
        const catElement = document.createElement("label");
        catElement.className = "form-check-label";
        catElement.id = "cat-label-"+num;
        catElement.setAttribute("for", "check-cat-"+num);
        catElement.textContent = cat;

        // number of papers of given category
        const counter = document.createElement("div");
        counter.className = "ms-auto counter";
        counter.id = "cat-count-"+num;
        counter.textContent = "0";

        document.getElementById("cats").appendChild(parent);
        parent.appendChild(form);
        form.appendChild(check);
        form.appendChild(catElement);
        parent.appendChild(counter);
    });

    // save cookies
    PREF.save();
};

const renderTags = (): void => {
    const tagNames = __TAGS__.map((x: Tag) => x.name);
    const unusedTags = [];

    __TAGS__.forEach((tag: Tag, tagNum: number) => {

        if (!PREF.tagsArr.map((x: Tag) => x.name).includes(tag.name)) {
            PREF.tagsArr.push({"name": tag.name,
                "vis": true,
                "color": tag.color,
                "order": tagNum
            });
        } else {
            const cookTag = PREF.tagsArr.find((tagC: Tag) => tagC.name === tag.name);
            if (cookTag.order !== tagNum) {
                cookTag.order = tagNum;
            }
        }
    });

    PREF.tagsArr.sort((a: Tag, b: Tag) => {return a.order - b.order;});

    const allVisible = PREF.tagsArr.every((x: Tag) => x.vis);

    let num = 0;
    for (let tagIter = 0; tagIter < PREF.tagsArr.length; tagIter++) {
        const tag = PREF.tagsArr[`${tagIter}`];
        // check if the unused tag is stored in cookies
        if (!tagNames.includes(tag.name)) {
            unusedTags.push(num);
            continue;
        }

        const parent = document.createElement("div");
        parent.className = "d-flex justify-content-between align-items-center";

        const tagElement = document.createElement("div");
        tagElement.className = "tag-label";
        tagElement.id = "tag-label-"+num;
        tagElement.style.backgroundColor = tag.color;
        tagElement.textContent = tag.name;

        tagElement.addEventListener("click", checkTag);

        tagElement.style.borderColor =
            tag.vis && !allVisible ? cssVar("--tag_border_color") : "transparent";

        const counter = document.createElement("div");
        counter.className = "counter";
        counter.id = "tag-count-"+num;
        counter.textContent = "0";

        document.getElementById("tags").appendChild(parent);
        parent.appendChild(tagElement);
        parent.appendChild(counter);

        num++;
    }

    if (__parseTex__) {
        MathJax.typesetPromise();
    }
    unusedTags.forEach((numTag) => PREF.tagsArr.splice(numTag, 1));
    PREF.save();
}

const renderNov = (): void =>  {
    PREF.novArr.forEach((show: boolean, num: number) => {
        (document.getElementById("check-nov-" + num) as HTMLInputElement).checked = show;
    });
}

const renderCounters = (): void => {
    const nCats = __CATS__.length;
    if (DATA.ncat === undefined || DATA.ncat === null || DATA.ncat.length !== nCats) {
        return;
    }
    for(let catId = 0; catId < nCats; catId++) {
        document.getElementById("cat-count-" + String(catId)).textContent = String(DATA.ncat[`${catId}`]);
    }

    for(let novId = 0; novId < 3; novId++) {
        document.getElementById("nov-count-" + String(novId)).textContent = String(DATA.nnov[`${novId}`]);
    }

    const nTags = __TAGS__.length;
    for (let tagId = 0; tagId < nTags; tagId++) {
        document.getElementById("tag-count-" + String(tagId)).textContent = String(DATA.ntag[`${tagId}`]);
    }
}

// change sort selector
document.getElementById("sort-sel").onchange = () => {
    // clean the content
    cleanPageList();
    // got to first page
    pageChange();
    setTimeout(() => {
        // sort the papers that are supposed to be visible.
        sortPapers(DATA.papersVis);
        // render the main page content
        // #pages is still the same, so no point of rendering from scratch
        renderPapers();
    }, 0);
};

document.getElementById("filter-button").onclick = function() {
    if (document.getElementById("menu-col").classList.contains("d-none")) {
        document.getElementById("menu-col").classList.remove("d-none");
        document.getElementById("menu-main").classList.remove("ms-auto");
    } else {
        document.getElementById("menu-col").classList.add("d-none");
        document.getElementById("menu-main").classList.add("ms-auto");
    }
};

const listClick = (event: MouseEvent): void => {
    const url = "add_bm";
    let target = event.target as HTMLElement;
    while (!target.classList.contains("list-name")) {
        target = target.parentElement;
    }
    const num = target.getAttribute("id");
    const paper = DATA.papersVis[`${BOOK_BTN}`];
    // paper ID w/o version is a unique identifier of the paper record in DB
    $.post(url, {"paper_id": paper.id.split("v")[0],
        "list_id": num
    })
        .done((_data, _textStatus, jqXHR) => {
            const status = jqXHR.status;
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

const renderLists = (): void => {
    /** Render pop-up window with page lists
     */
    if (DATA.lists === undefined || DATA.lists.length === 0) {
        return;
    }
    DATA.lists.forEach((list: List) => {
        const listDom = document.createElement("div");
        listDom.textContent = list.name;
        listDom.className = "list-name";
        listDom.id = String(list.id);
        listDom.addEventListener("click", listClick);
        document.getElementById("lists-popup").appendChild(listDom);
    });
};

window.onload = () => {
    PREF.load();

    // a fix that prevent browser scrolling on "back" button
    // essential for nice work of window.onpopstate
    history.scrollRestoration = "manual";

    let url = document.location.href;
    url = url.replace("papers", "data");

    const pageStr = url.split("page=")[1];
    PAGE = parseInt(pageStr.split("&")[0], 10);

    // Get paper data from backend
    $.get(url)
        .done((data) => {
            DATA = data as Data;
            renderCounters();
            // update page title with detailed dates
            const elem = $("#paper-list-title");
            elem.text(elem.text() + DATA["title"]);
            filterVisiblePapers();
            renderLists();
        }).fail(() => {
        const el = document.getElementById("loading-papers");
        el.textContent = "Oooops, arxivtag experienced an internal error processing your papers. We are working on fixing that. Please, try later.";
    });
    renderNov();
    renderCats();
    renderTags();

    const element = document.getElementsByClassName("page-link");
    for (let i = 0; i < element.length; i++) {
        element[`${i}`].addEventListener("click", pageLinkClick);
    }

    const element2 = document.getElementsByClassName("check-nov");
    for (let i = 0; i < element2.length; i++) {
        element2[`${i}`].addEventListener("click", novChange);
    }
};

window.onpopstate = () => {
    /** catch the "back" button usage for page switch
     */
    pageChange(-1, false);
    renderPapers();
};
