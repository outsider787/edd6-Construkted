const fs = require('fs');

const State = {
    Unknown: 'Unknown',
    Creating: 'Creating',
    Uploading: 'Uploading',
    Tiling: 'Tiling',
    Downloading: 'Downloading',
    Packaging: 'Packaging',
    Deleting: 'Deleting',
    Finished: 'Finished',
};

const accessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIzNWU3YWY1MS1lNmUyLTRiMzAtYmVhZS1jNGVkMzVkYzU0MzIiLCJpZCI6MjkyMSwic2NvcGVzIjpbImFzbCIsImFzciIsImFzdyIsImdjIl0sImlhdCI6MTU3NTM2OTg5NX0.24GRSi6fRXbilevELFVtUPsuaN-YrU6gjNw63jG4soQ';

exports.State = State;
exports.accessToken = accessToken;
exports.node = 'node';
exports.python = 'python3.7';
exports.downloader = '/home/ec2-user/asset_downloader-v3.py';
exports.downloaderThreadCount = 10;
exports.downloadPath = 'E:/0Source/Edd6/edd6-Construkted/asset_downloader';
exports.tilesToolsPath = '/home/ec2-user/3d-tiles-tools/tools/bin/3d-tiles-tools.js';
exports.s3Location = '/mnt/s3-assets';
exports.s3UploadLocation = '/mnt/s3-uploads';
exports.s3AssetLocation = '/mnt/s3-assets';
exports.WPServerIp = 'edd6b.construkted.com';
exports.WPUpdateProductRESTAPI_EndPoint = '/update_product_api/';

exports.port = 5000;

//The operation completely successfully
const ERROR_SUCCESS = 0;
const ERROR_INVALID_PARAMETER = 1;

exports.ERROR_SUCCESS = ERROR_SUCCESS;
exports.ERROR_INVALID_PARAMETER = ERROR_INVALID_PARAMETER;