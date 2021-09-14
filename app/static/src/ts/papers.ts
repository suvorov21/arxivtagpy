/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {renderPapersBase, Paper} from "./paper_basic";
import {raiseAlert, cssVar, prefs} from "./layout";

// global pagination vars
let PAGE = 1;
let VISIBLE = 0;
let BOOK_BTN = -1;
const PAPERS_PER_PAGE = 40;

const checkPaperVis = (paper, catsShow: Array<string>, allVisible: boolean, tagsShow: Array<boolean>): boolean => {
    /** Check if the paper passes visibility rules.
     * Logic: if check-box is off --> cut all the affected papers
     */

    if ((prefs.data["showNov"][0] === true || !(paper["nov"] & 1)) &&
        (prefs.data["showNov"][1] === true || !(paper["nov"] & 2)) &&
        (prefs.data["showNov"][2] === true || !(paper["nov"] & 4)) &&
        // filter on categories check boxes
        catsShow.filter((value) => paper["cats"].includes(value)).length > 0 &&
        // filter on tags
        (allVisible || (tagsShow.filter((value, index) => value && paper["tags"].includes(index)).length > 0))
    ) {
        VISIBLE += 1;
        return true;
    } else {

        return false;
    }
};

const sortFunction = (a:number, b:number, order = true, aDate:number, bDate:number): number => {
    if (a !== b) {
        return order? a - b : b - a;
    }
    // secondary sort always for date_up
    return bDate - aDate;
};

const sortPapers = () => {
    /** Sort the papers.
     * Only papers marked as visible will be sorted.
     */
    const sortMethod = String((document.getElementById("#sort-sel") as HTMLInputElement).value);
    // tags
    if (sortMethod.includes("tag")) {

        window["DATA"]["papersVis"].sort((a, b) => {
            if (b["tags"].length === 0 && a["tags"].length !== 0) {
                return sortMethod === "tag-as" ? -1 : 1;
            }
            if (b["tags"].length !== 0 && a["tags"].length === 0) {
                return sortMethod === "tag-as" ? 1 : -1;
            }
            if (b["tags"].length === 0 && a["tags"].length === 0) {
                return -1;
            }
            return sortFunction(a["tags"][0], b["tags"][0],
                sortMethod === "tag-as",
                (new Date(a["date_up"]).getTime()),
                (new Date(b["date_up"]).getTime())
            );
        });
    }
    // dates
    if (sortMethod.includes("date-up")) {
        window["DATA"]["papersVis"].sort((a, b) => {
            const aDate = new Date(a["date_up"]);
            const bDate = new Date(b["date_up"]);
            return sortFunction(aDate.getTime(), bDate.getTime(),
                sortMethod === "date-up_des",
                aDate.getTime(), bDate.getTime());
        });
    }

    if (sortMethod.includes("date-sub")) {
        window["DATA"]["papersVis"].sort((a, b) => {
            const aDateSub = new Date(a["date_sub"]);
            const bDateSub = new Date(b["date_sub"]);
            return sortFunction(aDateSub.getTime(), bDateSub.getTime(),
                sortMethod === "date-sub_des",
                aDateSub.getTime(),
                bDateSub.getTime()
            );
        });
    }

    // categories
    if (sortMethod.includes("cat")) {
        window["DATA"]["papersVis"].sort((a, b) => {
            let catA = "";
            let catB = "";
            for (let id = 0; id < a["cats"].length; id++) {
                if (window["CATS"].includes(a["cats"][`${id}`])) {
                    catA = a["cats"][`${id}`];
                    break;
                }
            }
            for (let id = 0; id < b["cats"].length; id++) {
                if (window["CATS"].includes(b["cats"][`${id}`])) {
                    catB = b["cats"][`${id}`];
                    break;
                }
            }
            return sortFunction(window["CATS"].indexOf(catA), window["CATS"].indexOf(catB),
                sortMethod === "cat-as",
                (new Date(a["date_up"]).getTime()),
                (new Date(b["date_up"]).getTime())
            );
        });
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

    const nPages = Math.floor(VISIBLE/PAPERS_PER_PAGE) + 1;
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
        const regex = /page=[0-9]*/i;
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

    return;
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
    if (start >= window["DATA"]["papersVis"].length) {
        pageChange(1, true);
        start = 0;
    }

    for (let pId = start;
         pId < Math.min(start + PAPERS_PER_PAGE, window["DATA"]["papersVis"].length);
         pId++) {

        const content = window["DATA"]["papersVis"][`${pId}`];
        const paperBase = renderPapersBase(content as Paper, pId);
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

    if (window["parseTex"]) {
        window["MathJax"].typesetPromise();
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
    // cleanPageList();

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

    const nPages = Math.floor(VISIBLE/PAPERS_PER_PAGE) + 1;
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
    for (const key in prefs.data["catsArr"]) {
        if (prefs.data["catsArr"][`${key}`]) {
            catsShow.push(key);
        }
    }

    const tagsShow = [];
    prefs.data["tagsArr"].forEach((tag) => {
        tagsShow.push(tag.vis);
    });

    const allVisible = prefs.data["tagsArr"].every((x) => x.vis);

    window["DATA"]["papersVis"] = window["DATA"]["papers"].filter((paper) => checkPaperVis(paper,
            catsShow,
            allVisible,
            tagsShow
        )
    );

    let text = String(VISIBLE) + " result";
    text += VISIBLE > 1 ? "s" : "";
    text += " over " + String(window["DATA"]["papers"].length);
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
    prefs.data["catsArr"][`${cat}`] = (document.getElementById("check-cat-" + number) as HTMLInputElement).checked;
    // save the cookies
    prefs.save();
    pageChange();
    setTimeout(function () {
        filterVisiblePapers();
    }, 0);
};

const tagBorder = (num: number, border: boolean): void => {
    prefs.data["tagsArr"][num].vis = border;
    document.getElementById("tag-label-" + String(num)).style.borderColor = border ? cssVar("--tag_border_color") : "transparent";
};

const checkTag = (event: MouseEvent) => {
    /** Click on tag.
     */
    let target = event.target as HTMLElement;
    while (target.id === null) {
        target = target.parentElement;
    }
    const number = parseInt(target.id.split("-")[2], 10);
    const thisVisible = prefs.data["tagsArr"][number].vis;
    const allVisible = prefs.data["tagsArr"].every((x) => x.vis);

    // if this tag is selected
    if (thisVisible) {
        if (allVisible &&
            (target.style.borderColor === "transparent" ||
                typeof target.style.borderColor === "undefined")) {
            // select only this tag
            // make all others invisible
            prefs.data["tagsArr"].forEach((tag) => {tag.vis = false;});

            // but this one visible
            tagBorder(number, true);
        } else {
            // hide this tag
            prefs.data["tagsArr"][number].vis = false;
            // if this was the only left tag
            if (prefs.data["tagsArr"].filter((value) => value.vis).length === 0) {
                // make all tags visible
                prefs.data["tagsArr"].forEach((tag) => {tag.vis = true;});
            }
            // remove border
            document.getElementById("tag-label-" + number).style.borderColor = "transparent";
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

const novChange = (event: MouseEvent): void => {
    /** CLick on novelty checkbox.
     */
    const number = parseInt((event.target as HTMLElement).id.split("-")[2], 10);
    prefs.data["showNov"][`${number}`] = (document.getElementById("check-nov-"+number) as HTMLInputElement).checked;
    prefs.save();
    pageChange();
    setTimeout(function () {
        filterVisiblePapers();
    }, 0);
};

// ********************** RENDERS  ***************************

const renderCats = (): void => {
    // clean unused categories from cookies
    const unusedCats = Object.keys(prefs.data["catsArr"]).filter((x) => !window["CATS"].includes(x));
    unusedCats.forEach((cat) => delete prefs.data["catsArr"][`${cat}`]);

    window["CATS"].forEach((cat, num) => {
        // if category not in cookies visibility dictionary --> add it
        if (!(cat in prefs.data["catsArr"])) {
            prefs.data["catsArr"][`${cat}`] = true;
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
        check.checked = prefs.data["catsArr"][`${cat}`];
        check.addEventListener("click", checkCat);

        // category name
        const catElement = document.createElement("label");
        catElement.className = "form-check-label";
        catElement.id = "cat-label-"+num;
        catElement.setAttribute("for", "check-cat-"+num);
        catElement.textContent = cat;

        // number of papers of given category
        const counter = document.createElement("div");
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
};

const renderTags = (): void => {
    const tagNames = window["TAGS"].map((x) => x.name);
    const unusedTags = [];

    window["TAGS"].forEach((tag, num) => {

        if (!prefs.data["tagsArr"].map((x) => x.name).includes(tag.name)) {
            prefs.data["tagsArr"].push({"name": tag.name,
                "vis": true,
                "color": tag.color,
                "order": num
            });
        } else {
            const cookTag = prefs.data["tagsArr"].find((tagC) => tagC.name === tag.name);
            if (cookTag.order !== num) {
                cookTag.order = num;
            }
        }
    });

    prefs.data["tagsArr"].sort((a, b) => {return a.order - b.order;});

    const allVisible = prefs.data["tagsArr"].every((x) => x.vis);

    let num = 0;
    for (let tagIter = 0; tagIter < prefs.data["tagsArr"].length; tagIter++) {
        const tag = prefs.data["tagsArr"][`${tagIter}`];
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

    if (window["parseTex"]) {
        window["MathJax"].typesetPromise();
    }
    unusedTags.forEach((num) => prefs.data["tagsArr"].splice(num, 1));
    prefs.save();
}

const renderNov = (): void =>  {
    prefs.data["showNov"].forEach((show, num) => {
        (document.getElementById("check-nov-" + num) as HTMLInputElement).checked = show;
    });
}

const renderCounters = (): void => {
    const nCats = window["CATS"].length;
    if (typeof window["DATA"]["ncat"] === "undefined") {
        return;
    }
    for(let catId = 0; catId < nCats; catId++) {
        document.getElementById("cat-count-" + String(catId)).textContent = window["DATA"]["ncat"][`${catId}`];
    }

    for(let novId = 0; novId < 3; novId++) {
        document.getElementById("nov-count-" + String(novId)).textContent = window["DATA"]["nnov"][`${novId}`];
    }

    const nTags = window["TAGS"].length;
    for (let tagId = 0; tagId < nTags; tagId++) {
        document.getElementById("tag-count-" + String(tagId)).textContent = window["DATA"]["ntag"][`${tagId}`];
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
        sortPapers();
        // render the main page content
        // #pages is still the same, so no point of rendering from scratch
        renderPapers();
    }, 0);
};

document.getElementById("filter-button").onclick = function() {
    if (document.getElementById("menu-col").classList.contains("d-none")) {
        document.getElementById("menu-col").classList.remove("d-none");
        document.getElementById("menu-main").classList.remove("ml-auto");
    } else {
        document.getElementById("menu-col").classList.add("d-none");
        document.getElementById("menu-main").classList.add("ml-auto");
    }
};

const listClick = (event: MouseEvent): void => {
    const url = "add_bm";
    let target = event.target as HTMLElement;
    while (!target.classList.contains("list-name")) {
        target = target.parentElement;
    }
    const num = target.getAttribute("id");
    const paper = window["DATA"]["papers"][`${BOOK_BTN}`];
    // we take paper id w/o version --> do not overload paper DB
    $.post(url, {"paper_id": paper.id.split("v")[0],
        "list_id": num
    })
        .done(function(data, textStatus, jqXHR) {
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
    // eslint-disable-next-line no-prototype-builtins
    if (!window["DATA"].hasOwnProperty("lists")) {
        return;
    }
    window["DATA"]["lists"].forEach((list) => {
        const listDom = document.createElement("div");
        listDom.textContent = list.name;
        listDom.className = "list-name";
        listDom.id = String(list.id);
        listDom.addEventListener("click", listClick);
        document.getElementById("lists-popup").appendChild(listDom);
    });
};

window.onload = () => {
    prefs.load();
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
            window["DATA"] = data;
            renderCounters();
            // update page title with detailed dates
            const element = $("#paper-list-title");
            element.text(element.text() + window["DATA"]["title"]);
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
