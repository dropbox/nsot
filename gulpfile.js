/**
 * Build file for NSoT's Frontend dependencies.
 *
 * Build tasks are broken up as either top-level tasks, for example `build`,
 * or sub-tasks, namespaced with a top-level task name and a color as a prefix,
 * for example, `build:js`
 *
 * You'll likely want to have gulp installed globally if you're using it regularly
 * though you'll be able to run it fron `node_modules/.bin/gulp` if you don't
 * use it often.
 *
 * Top Level Tasks
 * ---------------
 * gulp clean - Remove built assets
 * gulp build - Build all static assets for distribution
 * gulp lint - Lint JavaScript and CSS files
 */

var gulp = require('gulp');

// Plugin Imports
var jshint = require('gulp-jshint');
var concat = require('gulp-concat');
var ngAnnotate = require('gulp-ng-annotate');
var templateCache = require('gulp-angular-templatecache');
var addStream = require('add-stream');
var uglify = require('gulp-uglify');
var rename = require('gulp-rename');
var minifyCss = require('gulp-minify-css');
var csslint = require('gulp-csslint');
var sort = require('gulp-sort');
var del = require('del');
var path = require('path');

var SRC_ROOT = './nsot/static/src/';
var BUILD_DEST = './nsot/static/build/';

var JS_SRC = SRC_ROOT + 'js/**/*.js';
var STYLE_SRC = SRC_ROOT + 'style/**/*.css';
var TEMPLATE_SRC = SRC_ROOT + 'templates/**/*.html';
var IMAGE_SRC = SRC_ROOT + 'images/**';
var VENDOR_SRC = './node_modules/';

var VENDOR_FILES = [
    'angular/angular.min.js',
    'angular/angular.min.js.map',
    'angular-chart.js/dist/angular-chart.min.css',
    'angular-chart.js/dist/angular-chart.min.js',
    'angular-chart.js/dist/angular-chart.min.js.map',
    'angular-resource/angular-resource.min.js',
    'angular-resource/angular-resource.min.js.map',
    'angular-route/angular-route.min.js',
    'angular-route/angular-route.min.js.map',
    'chart.js/Chart.min.js',
    'bootstrap/dist/js/bootstrap.min.js',
    'bootstrap/dist/css/bootstrap.min.css',
    'font-awesome/fonts/*',
    'font-awesome/css/font-awesome.min.css',
    'jquery/dist/jquery.min.js',
    'jquery/dist/jquery.min.map',
    'lodash/chain/lodash.js',
    'moment/min/moment.min.js',
    'ng-tags-input/build/ng-tags-input.bootstrap.min.css',
    'ng-tags-input/build/ng-tags-input.min.js',
    'ng-tags-input/build/ng-tags-input.min.css',
]

/**
 * Task to lint JavaScript files.
 */
gulp.task('lint:js', function() {
    return gulp.src(JS_SRC)
        .pipe(jshint())
        .pipe(jshint.reporter('jshint-stylish'));
});


/**
 * Task to lint CSS files.
 */
gulp.task('lint:style', function() {
    return gulp.src(STYLE_SRC)
        .pipe(csslint())
        .pipe(csslint.reporter());
});


/**
 * Top level Task to run all lint tasks.
 */
gulp.task('lint', ['lint:js', 'lint:style']);


/**
 * Finds angular templates and compiles them to JavaScript
 * To be included in another stream.
 */
function buildTemplateJs() {
    return gulp.src(TEMPLATE_SRC)
        .pipe(templateCache('compiled-templates.js', {
            module: 'nsotTemplates'
        }));
}


/**
 * Task to build JavaScript files.
 */
gulp.task('build:js', function() {
    return gulp.src(JS_SRC)
        .pipe(ngAnnotate())
        .pipe(addStream.obj(buildTemplateJs()))
        .pipe(sort())
        .pipe(concat('app.js'))
        .pipe(gulp.dest((BUILD_DEST + 'js')))
        .pipe(uglify())
        .pipe(rename('app.min.js'))
        .pipe(gulp.dest((BUILD_DEST + 'js')));
});


/**
 * Task to build CSS files.
 */
gulp.task('build:style', function() {
    return gulp.src(STYLE_SRC)
        .pipe(sort())
        .pipe(concat('nsot.css'))
        .pipe(gulp.dest((BUILD_DEST + 'style')))
        .pipe(minifyCss())
        .pipe(rename('nsot.min.css'))
        .pipe(gulp.dest((BUILD_DEST + 'style')));
});


/**
 * Task to "build" images. While we're not doing anything interesting
 * now this opens up the option for building sprites if needed. This
 * also keeps our src separate from our build where we'll do things like
 * hash built files eventually.
 */
gulp.task('build:images', function() {
    return gulp.src(IMAGE_SRC)
        .pipe(gulp.dest((BUILD_DEST + 'images')))
});


/**
 * Install the "main" files into our build. In most cases
 * the "main" files are manually specified in the `overrides` section
 * of package.json
 */
gulp.task('build:3rdparty', function() {
    return gulp.src(
        VENDOR_FILES.map(f => path.join(VENDOR_SRC, f)),
        {base: VENDOR_SRC}
    ).pipe(gulp.dest(BUILD_DEST + 'vendor'))
});


/**
 * Create a hashed version of all built files. This is currently
 * just a placeholder and hasn't been finished yet.
 */
gulp.task('build:revisions', ['build:js', 'build:style', 'build:images', 'build:3rdparty'], function() {
    // TODO(gary): Do.
    return gulp.src(BUILD_DEST);
});


/**
 * Super task to build everything.
 */
gulp.task('build', ['build:revisions']);


/**
 * Remove the build directory
 */
gulp.task('clean', function(cb) {
    del([BUILD_DEST], cb);
});
