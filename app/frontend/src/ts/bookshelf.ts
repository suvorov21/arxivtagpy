/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {renderPapersBase, Paper, List, Data} from "./paper_basic";
import {raiseAlert, cssVar} from "./layout";

let unseenCurrentList = 0;

declare const __DATA__: Data;

declare const __PAGE__: number;
declare const __PAGE_SIZE__: number;
declare const __DISPLAY_LIST__: number;

declare const MathJax;
declare const __parseTex__: boolean;

const renderLists = (): void => {
    // WARNING very inaccurate parsing
    // TODO replace with regex
    const hrefBase = document.location.href.split("=")[0];
    __DATA__.lists.forEach((list: List) => {
        const listItem = document.createElement("li");
        listItem.className = "nav-item";
        const link = document.createElement("a");
        link.href = hrefBase + "=" + list.id;
        link.className = "nav-link";
        if (list.id === __DISPLAY_LIST__) {
            link.className += " active";
            unseenCurrentList = list.not_seen;
        }
        link.textContent = list.name;
        if (list.not_seen !== 0) {
            link.textContent += " ";
            const badge = document.createElement("span");
            badge.className = "badge bg-light text-dark";
            badge.textContent = String(list.not_seen);
            link.appendChild(badge);
        }
        listItem.appendChild(link);

        document.getElementById("menu-list").append(listItem);
        const clone = listItem.cloneNode(true);
        document.getElementById("menu-list-mob").append(clone);
    });
};

const deleteBookmark = (event: MouseEvent): void => {
    // WARNING
    // UB addBookmark listener is added to all the buttons, not the bookmark only one
    // prevent the bookmark adding for other buttons
    const target = event.target as HTMLElement;
    if (!target.id.includes("btn-del") &&
        !target.id.includes("a-icon")) {
        return;
    }
    const url = "del_bm";
    const cssId = parseInt(target.id.split("-")[2], 10);
    const arrayId = cssId - (__PAGE__ - 1) * __PAGE_SIZE__
    const paper = __DATA__.papers[arrayId];
    $.post(url, {
        "paper_id": paper.id.split("v")[0],
        "list_id": __DISPLAY_LIST__
    })
    .done((_data, _textStatus, jqXHR) => {
        const status = jqXHR.status;
        if (status === 201) {
            raiseAlert("Paper has been deleted", "success");
        }
        $("#paper-"+cssId).css("display", "none");
        __DATA__.papers[`${arrayId}`].hide = true;
        const counterStart = (__PAGE__ - 1) * __PAGE_SIZE__;
        let visible = counterStart;
        for (let i = 0; i < __DATA__.papers.length; i++) {
            if (!__DATA__.papers[`${i}`].hide) {
                visible += 1;
                const numEl = document.getElementById("paper-num-" + String(counterStart + i));
                numEl.textContent = String(visible);
            }
        }
        if (visible === counterStart) {
            document.getElementById("no-paper").style.display = "block";
        }
    }).fail(() => {
        raiseAlert("Paper is not deleted due to server error", "danger");
    });
}

const renderPapers = (): void => {
    __DATA__.papers.forEach((paper: Paper, num: number) => {
        num += __PAGE_SIZE__ * (__PAGE__ - 1);
        const paperBase = renderPapersBase(paper, num);

        // highlight new papers
        const paperElement = paperBase[0];
        if (num < unseenCurrentList) {
            paperElement.style.backgroundColor = cssVar("--unseen-paper-bg");
        }

        // removal button
        const btnPanel = paperBase[1];

        const btnDel = document.createElement("button");
        btnDel.className = "btn btn-danger";
        btnDel.id = "btn-del-"+num;
        btnDel.innerHTML = "<i class='fa fa-trash-o' aria-hidden='true' id='a-icon-" + num + "'></i>";
        btnDel.addEventListener("click", deleteBookmark);


        const btnGroup4 = document.createElement("div");
        btnGroup4.className = "btn-group mr-2";
        btnPanel.appendChild(btnGroup4);
        btnGroup4.appendChild(btnDel);

    });

    if (__DATA__.papers.length === 0) {
        document.getElementById("no-paper").style.display = "block";
    }

    if (__parseTex__) {
        MathJax.typesetPromise();
    }
    document.getElementById("loading-papers").style.display = "none";
}

window.onload = () => {
    renderLists();
    renderPapers();
};