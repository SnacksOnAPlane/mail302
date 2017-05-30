var LAMBDA_NAME = "ses-forwarder-dev-sesForwarder";
var MAPPING_FILE_BUCKET = "mail.hotdonuts.info";
var MAPPING_FILE_NAME = "mailmap.json";
var IAM_ROLE_FILE_NAME = "role.json";
var IAM_POLICY_FILE_NAME = "policy.json";

var aws = require('aws-sdk');
var fs = require('fs');
var s3 = new aws.S3();
var mappings = { 'test@hotdonuts.info': 'rsmiley+testhd@gmail.com' };
var params = { Bucket: 'mail.hotdonuts.info', Key: 'mailmap.json' };
s3.getObject(params, function(err, data) {
  if (err) {
    uploadS3File();
    return;
  }
  mappings = JSON.parse(data.Body);
});

function uploadS3File() {
  var newParams = Object.assign({ Body: JSON.stringify(mappings), ContentType: 'text/json' }, params);
  s3.putObject(newParams, function(err, data) {
    if (err) {
      console.log("PUT error", err);
    } else {
      console.log("file updated");
    }
  });
}

function createIAMRole() {
  var policyDocument = fs.readFileSync(IAM_ROLE_FILE_NAME, 'utf8');
  var iam = new aws.IAM({apiVersion: '2010-05-08'});
  var params = {
    Path: "/",
    RoleName: "mail302",
    AssumeRolePolicyDocument: policyDocument
  }
  iam.createRole(params, function(err, data) {
    if (!err) {
      params = {
        PolicyDocument: fs.readFileSync(IAM_POLICY_FILE_NAME, 'utf8'),
        PolicyName: 'mail302-policy',
        RoleName: data.Role.RoleName
      };
      iam.putRolePolicy(params, function(err, data) {
        debugger;
      });
    }
  });
}

function setupIAMRoles() {
  var iam = new aws.IAM({apiVersion: '2010-05-08'});
  iam.getRole({ RoleName: 'mail302' }, function(err, data) {
    if (err && err.message == 'Role not found for mail302') {
      createIAMRole();
    }
  });
}

function updateAws() {
  // get or create s3 buckets
  // get or create IAM roles
  setupIAMRoles();
  // get or create triggers
  aws.config.update({ region: 'us-east-1' });
  var lambda = new aws.Lambda({ apiVersion: '2015-03-31' });
  var results = lambda.getFunction({ FunctionName: LAMBDA_NAME }, function(err) { debugger; }, function(err, results) { debugger; });
}

function checkRoute53(domain) {
  var route53 = new aws.Route53({apiVersion: '2013-04-01'});
  var searchDomain = domain + ".";
  route53.listHostedZones({}, function(err, data) {
    for (var i in data.HostedZones) {
      var item = data.HostedZones[i];
      if (item.Name == searchDomain) {
        domainId = item.Id.substr(12);
      }
    }
  });
}

function deleteSetup() {
  var iam = new aws.IAM({apiVersion: '2010-05-08'});
  var params = {
    RoleName: 'mail302',
    PolicyName: 'mail302-policy'
  };
  iam.deleteRolePolicy(params, function(err, data) {
    if (err) {
      debugger;
      return;
    }
    var params = {
      RoleName: 'mail302'
    };
    iam.deleteRole(params, function(err, data) {
      if (err) {
        debugger;
        return;
      }
    });
  });
};

//uploadS3File();
//checkRoute53('hotdonuts.info');
deleteSetup();
setupIAMRoles();

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


