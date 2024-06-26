/* eslint no-console: ["error", { allow: ["warn", "error"] }] */

export interface Tag {
    /**
     * Tag information served to front-end
     */
    name: string;
    id?: number;
    color?: string;
    rule?: string;
    vis?: boolean;
    order?: number;
    bookmark?: boolean;
    email?: boolean;
    public?: boolean;
    userss?: boolean;
}

export interface Cats {
    /**
     * Category visibility stored in cookies
     */
    [name: string]: boolean;
}

export class Preference {
    /**
     * Class for working with cookies
     */

    catsArr: Cats;
    tagsArr: Array<Tag>;
    novArr: Array<boolean>;

    constructor() {
        this.catsArr = {};
        this.tagsArr = [];
        this.novArr = [true, true, true];
    }


    load(name = "prefs"): void {
        /**
         * Load cookies from browser
         */
        const cookieDecoded = decodeURIComponent(document.cookie).split(";");
        const cname = name + "=";
        for (let i = 0; i < cookieDecoded.length; i++) {
            let cook = cookieDecoded[`${i}`];
            while (cook.startsWith(" ")) {
                cook = cook.slice(1);
            }
            if (cook.startsWith(cname)) {
                const parsedJSON = JSON.parse(cook.substring(cname.length, cook.length));
                if ("catsArr" in parsedJSON) {
                    this.catsArr = parsedJSON["catsArr"];
                }
                if ("tagsArr" in parsedJSON) {
                    this.tagsArr = parsedJSON["tagsArr"];
                }
                if ("novArr" in parsedJSON) {
                    this.novArr = parsedJSON["novArr"];
                }
            }
        }
    }

    save(expires: Date = null, path: string = null): void {
        /**
         * Write cookies to browser
         */
        const d = expires || new Date(2100, 2, 2);
        const p = path || "/";
        const data = {
            catsArr: this.catsArr,
            tagsArr: this.tagsArr,
            novArr: this.novArr,
        }
        document.cookie = "prefs=" + encodeURIComponent(JSON.stringify(data))
            + ";expires=" + d.toUTCString()
            + ";path=" + p;
    }
}

// ************************** UTILS ********************************************
type alertType = "success" | "danger";
export function raiseAlert(text = "Text", type: alertType="success"): void {
    const parent = document.createElement("div");
    parent.setAttribute("class", "alert alert-dismissible fade show alert-" + type);
    parent.setAttribute("role", "alert");

    const content = document.createElement("span");
    content.textContent = text;

    const close = document.createElement("button");
    close.className = "btn-close";
    close.setAttribute("data-bs-dismiss", "alert");
    close.setAttribute("aria-label", "Close");

    document.getElementById("inner-message").appendChild(parent);
    parent.appendChild(content);
    parent.appendChild(close);

    setTimeout(() => {
        (<any>$(".alert")).alert("close");
    } , 4000);
}

// utility function to access css var
export function cssVar(name: string, value: string = null): string {
    if (!name.startsWith("-")) {
        name = "--" + name; //allow passing with or without --
    }
    if (value) {
        document.documentElement.style.setProperty(name, value);
    }
    return getComputedStyle(document.documentElement).getPropertyValue(name);
}
