const path = require("path");
// const webpack = require("webpack");

module.exports = {
    mode: "production",
    entry: {
        "papers": "./ts/papers.ts",
        "bookshelf": "./ts/bookshelf.ts",
        "settings_tag": "./ts/settings_tag.ts",
        "settings_cat": "./ts/settings_cat.ts",
        "settings_pref": "./ts/settings_pref.ts",
        "settings_book": "./ts/settings_book.ts",
        "about": "./less/about.less",
        "vars": "./less/vars.less",
        "vars_dark": "./less/vars_dark.less",
        "papers_style": "./less/papers.less",
        "settings_style": "./less/settings.less"
    },
    devtool: "inline-source-map",
    module: {

        rules: [
            {
                test: /\.tsx?$/,
                use: "ts-loader",
                exclude: /node_modules/,
            },
            {
                test: /\.less$/,
                use: [
                    "style-loader",
                    "css-loader",
                    "less-loader"
                ],
            },
            {
                test: /\.css$/,
                use: [
                    "style-loader",
                    "css-loader",
                ],
            },
        ],
    },
    resolve: {
        extensions: [".tsx", ".ts", ".js"],
    },
    output: {
        path: path.resolve(__dirname, "../dist/js/"),
        filename: "[name].bundle.js",
    },
};

// new webpack.ProvidePlugin({
//    $: "jquery",
// })
