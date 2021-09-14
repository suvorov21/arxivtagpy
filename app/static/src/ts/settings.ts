/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {raiseAlert} from "./layout";

// API call for settings modifications
export const submitSetting = (url: string, set: JSON): Promise<boolean> => {
    return new Promise((resolve, reject) => {
        $.post(url, JSON.stringify(set))
        .done(function () {
            raiseAlert("Settings are saved", "success");
            resolve(true);
        }).fail(function () {
            raiseAlert("Settings were not saved. Please try later", "danger");
            reject(false);
        });
    });
};

export const setDefaultListeners = (): void => {
    setTimeout(() => {
    const btnCollection = document.getElementsByClassName("btn-cancel");
    for (let i = 0; i < btnCollection.length; i++) {
        btnCollection[`${i}`].addEventListener("click", () => {
            const target = document.getElementsByClassName(
                "btn-cancel")[0] as HTMLElement;
            if (target && !target.classList.contains("disabled")) {
                location.reload();
            }
        });
    }
    }, 1000)
    const btnCollection = document.getElementsByClassName("nav-link");
    for (let i = 0; i < btnCollection.length; i++) {
        btnCollection[`${i}`].addEventListener("click", (event: MouseEvent) => {
            const target = document.getElementsByClassName("btn-cancel")[0] as HTMLElement;
            if (target &&
                !target.classList.contains("disabled")) {
                if (!confirm("Settings will not be saved. Continue?")) {
                    event.preventDefault();
                }
            }
        });
    }

    const formCollection = document.getElementsByClassName("form-check-input");
    for (let i = 0; i < formCollection.length; i++) {
        formCollection[`${i}`].addEventListener("change", () => {
            document.getElementsByClassName("btn-cancel")[0].classList.remove("disabled");
        });
    }
};

export const dropElement = (event: DragEvent, arrayToSwap: Array<JSON>, dragTarget: number): void => {
    event.preventDefault();
    let moved = parseInt(event.dataTransfer.getData("Text"), 10);
    // insert transferred element at new place
    arrayToSwap.splice(dragTarget, 0, arrayToSwap[`${moved}`]);

    if (moved > dragTarget) {
        moved += 1;
    }

    // delete transferred element at old place
    arrayToSwap.splice(moved, 1);
    const btnCollection = document.getElementsByClassName("btn");
    for (let i = 0; i < btnCollection.length; i++) {
        btnCollection[`${i}`].classList.remove("disabled");
    }
};
