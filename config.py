#!/usr/bin/python

import boto3
from botocore.exceptions import ClientError
import pdb
import json
import zipfile
import os
import StringIO


LAMBDA_NAME = "ses-forwarder-dev-sesForwarder";
MAPPING_FILE_BUCKET = "mail.hotdonuts.info";
MAPPING_FILE_NAME = "mailmap.json";
IAM_ROLE_FILE_NAME = "role.json";
IAM_POLICY_FILE_NAME = "policy.json";

mappings = { 'test@hotdonuts.info': 'rsmiley+testhd@gmail.com' };

s3 = boto3.resource('s3')
iam = boto3.client('iam')
ses = boto3.client('ses')
lam = boto3.client('lambda')

def loadAddressesFromServer():
  global mappings
  object = s3.Object('mail.hotdonuts.info', 'mailmap.json')
  raw = object.get()['Body'].read()
  mappings = json.loads(raw)

def loadAddressesFromFile():
  global mappings
  with open(MAPPING_FILE_NAME) as data_file:
    mappings = json.load(data_file)

def putAddresses():
  global mappings
  object = s3.Object('mail.hotdonuts.info', 'mailmap.json')
  data = json.dumps(mappings)
  object.put(Body=data)

def createIAMRole():
  print "Creating IAM roles..."
  policyDocument = open(IAM_ROLE_FILE_NAME).read()
  params = {
    'Path': "/",
    'RoleName': "mail302",
    'AssumeRolePolicyDocument': policyDocument
  }
  role = iam.create_role(**params)
  params = {
    'RoleName': "mail302",
    'PolicyDocument': open(IAM_POLICY_FILE_NAME).read(),
    'PolicyName': "mail302-policy"
  }
  iam.put_role_policy(**params)
  return role

def findIAMRole():
  roles = iam.list_roles()["Roles"]
  for role in roles:
    if role['RoleName'] == 'mail302':
      return role

def deleteSetup():
  print "Deleting setup..."
  try:
    params = {
      'RoleName': 'mail302',
      'PolicyName': 'mail302-policy'
    };
    iam.delete_role_policy(**params)
    params = {
      'RoleName': 'mail302'
    }
    iam.delete_role(**params)
  except ClientError as err:
    print err

def uploadS3Config():
  print "Uploading email mappings..."
  global mappings
  params = {
      'Body': json.dumps(mappings),
      'ContentType': 'text/json'
      }
  s3.put_object(params)

def domainsList():
  global mappings
  domains = set()
  for recipient in mappings:
    user, domain = recipient.split("@")
    domains.add(domain)
  return list(domains)

def createSESReceiptRule(lambda_arn):
  print "Creating SES Receipt rule..."
  ses.create_receipt_rule_set(RuleSetName = 'mail302-set')
  ses.create_receipt_rule(
      RuleSetName='mail302-set',
      Rule={
        'Name': 'mail302',
        'Enabled': True,
        'Recipients': domainsList(),
        'Actions': [
          {
            'S3Action': {
              'BucketName': 'mail.hotdonuts.info'
              }
          }, {
            'LambdaAction': {
              'FunctionArn': lambda_arn
            }
          }
        ]
      }
    )
  ses.set_active_receipt_rule_set(RuleSetName = 'mail302-set')

def findForwarderLambda():
  funcs = lam.list_functions()['Functions']
  for func in funcs:
    if func['FunctionName'] == 'mail302-dev-sesForwarder':
      return func

def zipFile():
  dir_path = os.path.dirname(os.path.realpath(__file__))
  handler_dir = os.path.join(dir_path, "handler")
  cwdpath = os.getcwd()
  os.chdir(handler_dir)
  fl_obj = StringIO.StringIO()
  with zipfile.ZipFile(fl_obj, mode="w", compression = zipfile.ZIP_DEFLATED) as zf:
    for dirname, subdirs, files in os.walk("./"):
      zf.write(dirname)
      for filename in files:
        zf.write(os.path.join(dirname, filename))
  val = fl_obj.getvalue()
  os.chdir(cwdpath)
  return val

def createForwarderLambda(role_arn):
  print "Creating Lambda function..."
  result = lam.create_function(
      FunctionName = "mail302-dev-sesForwarder",
      Runtime = "nodejs6.10",
      Role = role_arn,
      Handler = "handler.sesForwarder",
      Code = {
        "ZipFile": zipFile()
        },
      Timeout = 10,
      Publish = True
      )
  lam.add_permission(
      Action = "lambda:InvokeFunction",
      FunctionName = "mail302-dev-sesForwarder",
      Principal = "ses.amazonaws.com",
      StatementId = "GiveSESPermissionToInvokeFunction"
      )
  return result

#deleteSetup()
#createIAMRole()
loadAddressesFromFile()
role = findIAMRole()
if not role:
  role = createIAMRole()['Role']
forwarder = findForwarderLambda()
if not forwarder:
  forwarder = createForwarderLambda(role["Arn"])
createSESReceiptRule(forwarder['FunctionArn'])


"""

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

"""
