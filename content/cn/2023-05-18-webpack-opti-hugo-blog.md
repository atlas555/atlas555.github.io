---
title: "webpack5 基础概念、操作以及hugo博客js、css 优化"
date: 2023-05-18
author: "张晓龙"
slug: webpack5-optimize-hugo-js-css
draft: false
show_toc: true
keywords:
- webpack5
- hugo
- js优化
- css优化
description : "webpack5 基础概念、操作以及hugo博客js、css 优化"
categories: hugo折腾
tags: 
- hugo折腾
---

为了博客的改造和优化，尤其是 javascript 和 css 的优化，作为一个后端大数据工程师，啥都得学（折腾是最大的乐趣）。

目前博客的一个问题，是采用[Yihui Xie]大佬的 js、css 的技术架构设计方案，js 和 css 在 github 构建 repo，然后通过[jsdelivr：A free CDN for open source projects](https://www.jsdelivr.com/) CDN 分发，combine 加载，这个方案非常优雅。但是国内网络环境的问题，jsdelivr 经常被墙，js 和 css 加载不出来，另外 js 和 css 文件较多，挨个加载影响网站响应速度。

国内免费 cdn 没有自己贡献github源的（有的也必须申请提交，不灵活），所以打算`自己合并、压缩 js 和 css 文件，放到自己博客加载（ali oss 加载）`(目标)。

和前端大佬请教，压缩、合并、最小化 js、css 需要 webpack 工具。学习webpack官网资料[^1]，将基础的内容整理到这，够用就好。

学习新技术，有方法套路：`学习基本概念，然后理清其基本关系，做组合变化`。

## 基础概念

webpack is a static module bundler for modern JavaScript applications. `Webpack 5 runs on Node.js version 10.13.0+.`

webpack 构建项目依赖，打包项目。个人理解和 java 领域的 maven 相似。首先理清基本概念。

1. Entry
2. Output
3. Loaders
4. Plugins
5. Mode
6. Browser Compatibility

### Entry

代表打包的入口，默认是<code>./src/index.js</code>，可以如下自定义设置。

config 文件：webpack.config.js

``` javascript
module.exports = {
  entry: './path/to/my/entry/file.js',
};

// 或者 multi-main entry
module.exports = {
  entry: ['./src/file_1.js', './src/file_2.js'],
  output: {
    filename: 'bundle.js',
  },
};
```

### Output

代表打包输出的路径。js 默认输出`./dist/main.js `到`./dist`目录。当然也可以自主配置。

config 文件：webpack.config.js

``` javascript
const path = require('path');

module.exports = {
  entry: './path/to/my/entry/file.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'my-first-webpack.bundle.js',
  },
};
```

其中`the path module` 是 Node.js 的底层库。

针对多重入口，且需要多个 chunk

``` javascript
module.exports = {
  entry: {
    app: './src/app.js',
    search: './src/search.js',
  },
  output: {
    filename: '[name].js',
    path: __dirname + '/dist',
  },
};

// writes to disk: ./dist/app.js, ./dist/search.js
```

### Loaders

webpack 只认识  JavaScript and JSON files，Loaders 可以让 webpack 认识其他类型文件以及打包进项目中。

在顶层抽象中，loaders 在 webpackage configuration 有两个参数

> The `test` property identifies which file or files should be transformed.
> The `use` property indicates which loader should be used to do the transforming.

config 文件：webpack.config.js

``` javascript
const path = require('path');

module.exports = {
  output: {
    filename: 'my-first-webpack.bundle.js',
  },
  module: {
    rules: [{ test: /\.txt$/, use: 'raw-loader' }],
  },
};
```

rule：在给定的 path 中发现.txt类型的文件，再被打包进项目前使用 raw-loader 进行处理。

`module.rules` 允许多个 loaders 处理，比如

``` javascript
module.exports = {
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          { loader: 'style-loader' },
          {
            loader: 'css-loader',
            options: {
              modules: true,
            },
          },
          { loader: 'sass-loader' },
        ],
      },
    ],
  },
};
```

loader 提供了一种方法去自定义 output，它还有的一些特性：

1. Loaders can be chained.
2. Loaders can be synchronous or asynchronous.
3. Loaders run in Node.js and can do everything that’s possible there.
4. Loaders can be configured with an options object
5. Loaders can emit additional arbitrary files.

### Plugins

loader 可以转换确定类型的module，plugins 可以承担更宽泛的任务：打包优化、注入环境变量、资源管理等等。

使用plugins 需要`require()`，添加到 `plugins 数组中`。另外 plugin 使用需要 new 操作。

config 文件：webpack.config.js

``` javascript
const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack'); //to access built-in plugins

module.exports = {
  module: {
    rules: [{ test: /\.txt$/, use: 'raw-loader' }],
  },
  plugins: [new HtmlWebpackPlugin({ template: './src/index.html' })],
};
```

`html-webpack-plugin` 生成一个 html 文件，然后自动将所有生成的包注入到这个 html 中。

一个 webpack plugin 是一个包含 `apply`方法的 JavaScript 对象。这个 apply 方法被 webpack 编译器调用。

一个 plugin 的例子：

``` javascript
const pluginName = 'ConsoleLogOnBuildWebpackPlugin';

class ConsoleLogOnBuildWebpackPlugin {
  apply(compiler) {
    compiler.hooks.run.tap(pluginName, (compilation) => {
      console.log('The webpack build process is starting!');
    });
  }
}

module.exports = ConsoleLogOnBuildWebpackPlugin;
```

plugins 配置使用方法，`需要注意必须 new instance`

1. 通过Configuration文件：webpack.config.js

``` js
const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack'); //to access built-in plugins
const path = require('path');

module.exports = {
  entry: './path/to/my/entry/file.js',
  output: {
    filename: 'my-first-webpack.bundle.js',
    path: path.resolve(__dirname, 'dist'),
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        use: 'babel-loader',
      },
    ],
  },
  plugins: [
    new webpack.ProgressPlugin(),
    new HtmlWebpackPlugin({ template: './src/index.html' }),
  ],
};
```

2. 通过 Node API 的方式 :some-node-script.js

``` js
const webpack = require('webpack'); //to access webpack runtime
const configuration = require('./webpack.config.js');

let compiler = webpack(configuration);

new webpack.ProgressPlugin().apply(compiler);

compiler.run(function (err, stats) {
  // ...
});
```

### Mode

设置打包坏境`development, production or none`，

config 文件：webpack.config.js

``` javascript
module.exports = {
  mode: 'production',
};
```

### Browser Compatibility

Webpack supports all browsers that are ES5-compliant (IE8 and below are not supported). 

### Manifest

webpack 打包典型的应用或者网站，都需要以下三种类型的 code

- `The source code` you, and maybe your team, have written.
- Any `third-party library` or "vendor" code your source is dependent on.
- A `webpack runtime and manifest` that conducts the interaction of all modules.

## webpack 打包应用

可以通过官方的 [Live Preview](https://stackblitz.com/github/webpack/webpack.js.org/tree/main/examples/getting-started?file=README.md&terminal=)演练。

demo 项目结构：

``` js
webpack-demo
|- package.json
|- package-lock.json
|- webpack.config.js
|- /dist
  |- main.js
  |- index.html
|- /src
  |- index.js
|- /node_modules
```

## hugo 博客 js、css 打包优化

这个是我的项目结构

![webpack结构](https://media.techwhims.com/techwhims/2023/2023-05-18-08-30-18.png)

merge js 和 css 主要在 `webpack.config.js` 文件，通过`webpack-merge-and-include-globally` 插件完成。

```js
const path = require('path');
const MergeIntoSingle = require('webpack-merge-and-include-globally');
const TerserPlugin = require("terser-webpack-plugin");


module.exports = {
  entry: {
  },
  mode: 'production',
  output: {
    filename: '[name]',
    path: path.resolve(__dirname, 'dist'),
    clean: true,
  },
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin(),
    ],
  },
  plugins: [
    new MergeIntoSingle({
        files:{
            'bundle.js': [
                './js/comment-utils.min.js',
                './js/fix-toc.min.js',
                './js/center-img.min.js',
                './js/right-quote.min.js',
                './js/fix-footnote.min.js',
                './js/math-code.min.js',
                './js/hash-notes.min.js',
                './js/toggle-notes.min.js',
                './js/post-nav.min.js',
                './js/external-link.min.js',
                './js/alt-title.min.js',
                './js/header-link.min.js',
                './js/key-buttons.min.js',
            ],
            'bundle.css': [
                './css/key-buttons.min.css',
                '/.css/katex.min.css'
            ]
        },
        transform:{
            // 'vendor.js': code => uglifyJS.minify(code).code,
            // 'style.css': code => new CleanCSS({}).minify(code).styles,
        }
    }),
  ],
};
```

通过这种方式，可以将多次 js 加载，变为一次！减少网络请求。

------

2023.5.16 线上博客系统尝试该方法 ，有效果！

[^1](https://webpack.js.org/concepts/)

