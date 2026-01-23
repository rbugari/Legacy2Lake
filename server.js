var http = require('http');
var fs = require('fs');
var path = require('path');

var port = 3000;
var root = './apps/web/out'; // Adjust if build output is elsewhere, assuming Next.js static export or similar

// Basic static file server
http.createServer(function (request, response) {
    console.log('request ', request.url);

    var filePath = root + request.url;
    if (filePath == root + '/')
        filePath = root + '/index.html';

    var extname = path.extname(filePath);
    var contentType = 'text/html';
    switch (extname) {
        case '.js':
            contentType = 'text/javascript';
            break;
        case '.css':
            contentType = 'text/css';
            break;
        case '.json':
            contentType = 'application/json';
            break;
        case '.png':
            contentType = 'image/png';
            break;
        case '.jpg':
            contentType = 'image/jpg';
            break;
        case '.wav':
            contentType = 'audio/wav';
            break;
    }

    fs.readFile(filePath, function (error, content) {
        if (error) {
            if (error.code == 'ENOENT') {
                // Spa fallback
                fs.readFile(root + '/index.html', function (error, content) {
                    response.writeHead(200, { 'Content-Type': contentType });
                    response.end(content, 'utf-8');
                });
            }
            else {
                response.writeHead(500);
                response.end('Sorry, check with the site admin for error: ' + error.code + ' ..\n');
                response.end();
            }
        }
        else {
            response.writeHead(200, { 'Content-Type': contentType });
            response.end(content, 'utf-8');
        }
    });

}).listen(port);
console.log('Server running at http://127.0.0.1:' + port + '/');
