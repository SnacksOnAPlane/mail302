var LAMBDA_NAME = "ses-forwarder-dev-sesForwarder";
var MAPPING_FILE_BUCKET = "mail.hotdonuts.info";
var MAPPING_FILE_NAME = "mailmap.json";

function updateAws() {
  var aws = require('aws-sdk');
  aws.config.update({ region: 'us-east-1' });
  var lambda = new aws.Lambda({ apiVersion: '2015-03-31' });
  var results = lambda.getFunction({ FunctionName: LAMBDA_NAME }, function(err) { debugger; }, function(err, results) { debugger; });
  debugger;
}

updateAws();

function showMenu() {
  var Menu = require('terminal-menu');
  var menu = Menu({ width: 29, x: 4, y: 2 });
  menu.reset();
  menu.write('MAIL302\n');
  menu.write('-------------------------\n');

  menu.add('MANAGE EMAIL ADDRESSES');
  menu.add('SYNC FROM AWS');
  menu.add('UPDATE AWS');
  menu.add('EXIT');

  menu.on('select', function (label) {
      menu.close();
      if (label == "SYNC FROM AWS") {
        syncFromAws();
      }
  });
  process.stdin.pipe(menu.createStream()).pipe(process.stdout);

  process.stdin.setRawMode(true);
  menu.on('close', function () {
      process.stdin.setRawMode(false);
      process.stdin.end();
  });
}


