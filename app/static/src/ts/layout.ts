/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
export const prefs = {

    data: {},

    load(name = "prefs"): JSON {
        const cookieDecoded = decodeURIComponent(document.cookie).split(";");
        const cname = name + "=";
        for (let i = 0; i < cookieDecoded.length; i++) {
            let cook = cookieDecoded[`${i}`];
            while (cook[0] === " ") {
                cook = cook.slice(1);
            }
            if (cook.indexOf(cname) === 0) {
                this.data = JSON.parse(cook.substring(cname.length, cook.length));
            }
        }

        if (!prefs.data.hasOwnProperty("catsArr")) {
            prefs.data["catsArr"] = {};
        }

        if (!prefs.data.hasOwnProperty("tagsArr")) {
            prefs.data["tagsArr"] = [];
        }

        if (!prefs.data.hasOwnProperty("showNov")) {
            prefs.data["showNov"] = [true, true, true];
        }


        return this.data;
    },

    save(expires: Date = null, path: string = null): void {
        const d = expires || new Date(2100, 2, 2);
        const p = path || "/";
        document.cookie = "prefs=" + encodeURIComponent(JSON.stringify(this.data))
            + ";expires=" + d.toUTCString()
            + ";path=" + p;
    }
};

// ************************** UTILS ********************************************
type alertType = "success" | "danger";
export function raiseAlert(text = "Text", type: alertType="success"): void {
    const parent = document.createElement("div");
    parent.setAttribute("class", "alert alert-dismissible fade show alert-" + type);
    parent.setAttribute("role", "alert");

    const content = document.createElement("span");
    content.textContent = text;

    const close = document.createElement("button");
    close.setAttribute("class", "close");
    close.setAttribute("data-dismiss", "alert");
    close.setAttribute("aria-label", "Close");

    const time = document.createElement("span");
    time.innerHTML = "&times;";

    document.getElementById("inner-message").appendChild(parent);
    parent.appendChild(content);
    parent.appendChild(close);
    close.appendChild(time);

    setTimeout(() => {
        (<any>$(".alert")).alert("close");
    } , 3000);
}

// utility function to access css var
export function cssVar(name: string, value: string = null): string {
    if (name[0] !=="-") {
        name = "--" + name; //allow passing with or without --
    }
    if (value) {
        document.documentElement.style.setProperty(name, value);
    }
    return getComputedStyle(document.documentElement).getPropertyValue(name);
}
