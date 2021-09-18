/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {setDefaultListeners, submitSetting, dropElement} from "./settings";
import {raiseAlert} from "./layout";
import {List} from "./paper_basic";

declare const __LISTS__: Array<List>;

declare const MathJax;
declare const __parseTex__: boolean;

let dragTarget;

const findListNumById = (id: string): string => {
    for (let listId = 0; listId < __LISTS__.length; listId++) {
        if (__LISTS__[`${listId}`]["id"] === parseInt(id, 10)) {
            return String(listId);
        }
    }
    return "-1";
};

const delListClick = (event: MouseEvent): void => {
    const name = (event.target as HTMLElement).getAttribute("id").split("_")[1];
    document.getElementById("par-list-" + name).classList.remove("d-flex");
    $("#par-list-" + name).fadeOut();
    $(".btn").removeClass("disabled");
    const listId = parseInt(findListNumById(name), 10);
    if (listId > -1) {
        __LISTS__.splice(listId, 1);
    }
};

const dropList = (event: DragEvent) => {
    dropElement(event, __LISTS__, dragTarget);
    renderBookshelf();
};

const renderBookshelf = (): void => {
    $("#book-list").empty();
    __LISTS__.forEach((list: List) => {
        const listName = list.name;
        const parent = document.createElement("div");
        parent.className = "d-flex cat-parent";
        parent.id = "par-list-" + list.id;
        parent.draggable = true;

        parent.ondragstart = (event: DragEvent) => {
            const target = event.target as HTMLElement;
            const moved = target.id.split("-")[2];
            const movedStr = findListNumById(moved);
            event.dataTransfer.setData("Text", movedStr);
        };

        parent.ondragover = (event: DragEvent) => {
            const target = event.target as HTMLElement;
            const targetStr = target.id.split("-")[2];
            dragTarget = findListNumById(targetStr);
        };

        const close = document.createElement("button");
        close.id = "close_" + list.id;
        close.className = "close close-btn";
        close.innerHTML = "&times";

        close.addEventListener("click", delListClick);

        const listElement = document.createElement("div");
        listElement.className = "pl-2";
        listElement.id = "list-name-" + list.id;
        listElement.textContent = listName;

        document.getElementById("book-list").appendChild(parent);
        parent.appendChild(close);
        parent.appendChild(listElement);
    });
    document.getElementById("book-list").ondragover = (event: DragEvent) => {
        event.preventDefault();
    };
    document.getElementById("book-list").removeEventListener("drop", dropList);
    document.getElementById("book-list").addEventListener("drop", dropList);
    if (__parseTex__) {
        MathJax.typesetPromise();
    }
};

document.getElementById("add-book-btn").onclick = (): void => {
    const url = "add_list";
    const dataSet = {"name": document.forms["add-book-form"]["new-list"].value};
    $.post(url, JSON.stringify(dataSet))
        .done(function() {
            renderBookshelf();
            $(".btn-save").addClass("disabled");
            raiseAlert("Settings are saved", "success");
            window.location.reload();
            return false;
        }).fail(function(){
        raiseAlert("Settings were not saved. Please try later", "danger");
        return false;
    });
};

window.onload = () => {
    renderBookshelf();
    setDefaultListeners();
     (document.getElementById("mod-list") as HTMLFormElement).addEventListener("submit", (event: Event) => {
        event.preventDefault();
        if ($(".btn-cancel").hasClass("disabled")) {
            return false;
        }
        const url = "mod_lists";
        submitSetting(url, __LISTS__).then(() => {
            const btnCollection = document.getElementsByClassName("btn-save");
            for (let i = 0; i < btnCollection.length; i++) {
                btnCollection[`${i}`].classList.add("disabled");
            }
        });
        return false;
    });
};