/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {renderPapersBase, Paper} from "./paper_basic";
import {raiseAlert, cssVar} from "./layout";

let unseenCurrentList = 0;

const renderLists = (): void => {
    // WARNING very inaccurate parsing
    // TODO replace with regex
    const hrefBase = document.location.href.split("=")[0];
    window["LISTS"].forEach((listName) => {
        const listItem = document.createElement("li");
        listItem.className = "nav-item";
        const link = document.createElement("a");
        link.href = hrefBase + "=" + listName.id;
        link.className = "nav-link";
        if (listName.id === window["displayList"]) {
            link.className += " active";
            unseenCurrentList = listName["not_seen"];
        }
        link.textContent = listName.name;
        if (listName["not_seen"] !== 0) {
            link.textContent += " ";
            const badge = document.createElement("span");
            badge.className = "badge badge-light";
            badge.textContent = listName["not_seen"];
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
    const num = parseInt(target.id.split("-")[2], 10);
    const paper = window["DATA"]["papers"][num - (window["page"] - 1) * window["paperPage"]];
    $.post(url, {
        "paper_id": paper.id.split("v")[0],
        "list_id": window["displayList"]
    })
    .done((data, textStatus, jqXHR) => {
        const status = jqXHR.status;
        if (status === 201) {
            raiseAlert("Paper has been deleted", "success");
        }
        $("#paper-"+num).css("display", "none");
        window["DATA"]["papers"][`${num}`]["hide"] = true;
        let visible = 1;
        window["DATA"]["papers"].forEach((paper) => {
            if (!paper["hide"]) {
                const numEl = document.getElementById("paper-num-" + parseInt(paper["num"], 10));
                numEl.textContent = String(visible);
                visible += 1;
            }
        });
        if (visible === 1) {
            document.getElementById("no-paper").style.display = "block";
        }
    }).fail(() => {
        raiseAlert("Paper is not deleted due to server error", "danger");
    });
}

const renderPapers = (): void => {
    window["DATA"]["papers"].forEach((paper, num) => {
        num += window["paperPage"] * (window["page"] - 1);
        const paperBase = renderPapersBase(paper as Paper, num);

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

    if (window["DATA"]["papers"].length === 0) {
        document.getElementById("no-paper").style.display = "block";
    }

    if (window["parseTex"]) {
        window["MathJax"].typesetPromise();
    }
    document.getElementById("loading-papers").style.display = "none";
}

window.onload = () => {
    renderLists();
    renderPapers();
};