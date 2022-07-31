/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {setDefaultListeners, submitSetting, dropElement, toggleEditState} from "./settings";
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
    /**
     * Delete a list
     */
    const name = (event.target as HTMLElement).getAttribute("id").split("_")[1];
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

const dragStart = (event: DragEvent) => {
    const target = event.target as HTMLElement;
    const moved = target.id.split("-")[2];
    const movedStr = findListNumById(moved);
    event.dataTransfer.setData("Text", movedStr);
}

const confirmEdit = (event: MouseEvent) => {
    /**
     * Finish editing list name
     */

    const target = event.target as HTMLElement;
    if (target.id === "") {
        event.preventDefault();
        return;
    }

    const num = parseInt(target.id.split("-")[2], 10);
    const field = document.getElementById("field-list-" + num) as HTMLInputElement;

    if (__LISTS__.filter(e => e.name === field.value).length > 0 &&
    field.value !== __LISTS__[findListNumById(String(num))].name) {
        raiseAlert("List with this name already exists", "danger");
        return;
    }

    __LISTS__[findListNumById(String(num))].name = field.value;
    renderBookshelf();
    // Toggle "edited" state
    toggleEditState();
};

const editListName = (event: MouseEvent) => {
    /**
     * Start editing list name
     */
    const target = event.target as HTMLElement;
    if (target.id === "") {
        event.preventDefault();
        return;
    }

    const num = parseInt(target.id.split("-")[2], 10);

    $(".btn-edit").css("display", "none");

    const confirmBtn = document.createElement("i");
    confirmBtn.className = "ps-2 fa fa-check btn-confirm";
    confirmBtn.id = "confirm-btn-" + num;
    confirmBtn.addEventListener("click", confirmEdit);

    // hide label with list name
    const listName =  document.getElementById("list-name-" + num);
    listName.style.display = "none";

    const field = document.createElement("input");
    field.className = "ms-2";
    field.type = "text";
    field.id = "field-list-" + num;
    field.value = __LISTS__[findListNumById(String(num))].name

    const parentEle = document.getElementById("par-list-" + num);
    parentEle.appendChild(field);
    parentEle.appendChild(confirmBtn);
    parentEle.draggable = false;
    field.focus();

    $(".btn-cancel").removeClass("disabled");
};

const renderBookshelf = (): void => {
    /**
     * Main render function
     */
    $("#book-list").empty();
    __LISTS__.forEach((list: List) => {
        const listName = list.name;
        const parent = document.createElement("div");
        parent.className = "cat-parent";
        parent.id = "par-list-" + list.id;
        parent.draggable = true;

        parent.addEventListener("dragstart", dragStart);

        parent.ondragover = (event: DragEvent) => {
            const target = event.target as HTMLElement;
            const targetStr = target.id.split("-")[2];
            dragTarget = findListNumById(targetStr);
        };

        const close = document.createElement("div");
        close.id = "close_" + list.id;
        close.className = "close-btn align-middle";
        close.innerHTML = "&times";

        close.addEventListener("click", delListClick);

        const listElement = document.createElement("div");
        listElement.className = "ps-2 align-middle";
        listElement.id = "list-name-" + list.id;
        listElement.style.display = "inline";
        listElement.textContent = listName;

        if (list.auto) {
            listElement.innerHTML += " <i class=\"fa fa-android\" aria-hidden=\"true\"></i>";
        }

        const editBtn = document.createElement("i");
        editBtn.className = "ps-2 fa fa-pencil btn-edit";
        editBtn.id = "list-edit-" + list.id;
        editBtn.addEventListener("click", editListName);

        document.getElementById("book-list").appendChild(parent);
        parent.appendChild(close);
        parent.appendChild(listElement);
        parent.appendChild(editBtn);
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
    /**
     * Add a new list
     */
    if (document.forms["add-book-form"]["new-list"].value === "") {
        raiseAlert("Fill the list name", "danger");
        return;
    }

    // list names should be unique per user
    if (__LISTS__.filter(e => e.name === document.forms["add-book-form"]["new-list"].value).length > 0) {
        raiseAlert("List with this name already exists", "danger");
        return;
    }
    const url = "add_list";
    const dataSet = {"name": document.forms["add-book-form"]["new-list"].value};
    $.post(url, dataSet)
    .done(function() {
        renderBookshelf();
        $(".btn-save").addClass("disabled");
        raiseAlert("Settings are saved", "success");
        window.location.reload();
        return false;
    }).fail(function() {
        raiseAlert("Settings were not saved. Please try later", "danger");
        return false;
    });
};

const submitList = (event: Event): void => {
    /**
     * Settings saver
     */
    event.preventDefault();
    if ($(".btn-cancel").hasClass("disabled")) {
        return;
    }
    const url = "mod_lists";
    submitSetting(url, __LISTS__).then(() => {
        const btnCollection = document.getElementsByClassName("btn-save");
        for (let i = 0; i < btnCollection.length; i++) {
            btnCollection[`${i}`].classList.add("disabled");
        }
    }, () => {
        console.warn("Token is outdated. Refresh the page");
    });
};

window.onload = () => {
    renderBookshelf();
    setDefaultListeners();
     (document.getElementById("mod-list") as HTMLFormElement).addEventListener("submit", submitList);
};