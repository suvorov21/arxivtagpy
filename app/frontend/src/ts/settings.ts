/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {raiseAlert, Tag} from "./layout";
import {List} from "./paper_basic";

type settings = (List | string | Tag)[]

declare const bootstrap;

export const toggleEditState = (): void => {
    const btnCollection = document.getElementsByClassName("btn");
    for (let i = 0; i < btnCollection.length; i++) {
        btnCollection[`${i}`].classList.remove("disabled");
    }
}

// API call for settings modifications
export const submitSetting = (url: string, set: settings): Promise<boolean> => {
    return new Promise((resolve, reject) => {
        $.post(url, JSON.stringify(set))
        .done(function () {
            raiseAlert("Settings are saved", "success");
            resolve(true);
        }).fail(function (xhr, _textStatus: string) {
            if (xhr.status === 400) {
                // consider CSRF token expiration
                raiseAlert("Your page is outdated, please refresh and try again.",
                    "danger");
            } else {
                raiseAlert("Settings were not saved. Please try later",
                    "danger");
            }
            reject(new Error('Error on settings save'));
        });
    });
};

export const raiseModal = (event: Event,
                           questionText: string,
                           btnClass: string,
                           confirmHref: string,
                           formAction: string
                           ): void => {
    /**
     * Raise modal window with confirmation request
     */
    if (formAction !== "" && confirmHref !== "") {
        console.error("raiseModal error. both formAction and confirmHref are specified");
        return;
    }
    event.preventDefault();

    const modal = new bootstrap.Modal(document.getElementById("confirmModal"));
    document.getElementById("form-confirm").setAttribute("action", formAction);
    modal.show();
    document.getElementById("modal-text").innerHTML = questionText;

    const btn = document.getElementById("btn-confirm") as HTMLLinkElement;
    btn.addEventListener("click", () => {document.location.href = confirmHref;})
    btn.className = btnClass;

    if (formAction !== "") {
        btn.type = "submit";
    } else {
        btn.type = "button";
    }
}

export const setDefaultListeners = (): void => {
    let btnCollection = document.getElementsByClassName("btn-cancel");
    for (let i = 0; i < btnCollection.length; i++) {
        btnCollection[`${i}`].addEventListener("click", () => {
            const target = document.getElementsByClassName(
                "btn-cancel")[0] as HTMLElement;
            if (target && !target.classList.contains("disabled")) {
                location.reload();
            }
        });
    }

    btnCollection = document.getElementsByClassName("nav-link");
    for (let i = 0; i < btnCollection.length; i++) {
        btnCollection[`${i}`].addEventListener("click", (event: MouseEvent) => {
            const target = document.getElementsByClassName("btn-cancel")[0] as HTMLElement;
            if (target &&
                !target.classList.contains("disabled")) {
                raiseModal(event,
                    "Settings will not be saved, continue?",
                    "btn btn-primary",
                    (event.target as HTMLLinkElement).href,
                    ""
                );
            }
        });
    }

    const formCollection = document.getElementsByClassName("form-check-input");
    for (let i = 0; i < formCollection.length; i++) {
        formCollection[`${i}`].addEventListener("change", () => {
            const btnCollection2 = document.getElementsByClassName("btn-save");
            for (let j = 0; j < btnCollection2.length; j++) {
                btnCollection2[`${j}`].classList.remove("disabled");
            }
        });
    }
};

export const dropElement = (event: DragEvent, arrayToSwap: settings, dragTarget: number): void => {
    event.preventDefault();
    let moved = parseInt(event.dataTransfer.getData("Text"), 10);
    // insert transferred element at new place
    arrayToSwap.splice(dragTarget, 0, arrayToSwap[`${moved}`]);

    if (moved > dragTarget) {
        moved += 1;
    }

    // delete transferred element at old place
    arrayToSwap.splice(moved, 1);
    toggleEditState();
};
