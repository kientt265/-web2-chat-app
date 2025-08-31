import AWS from "aws-sdk";
import fs from "fs";

const s3 = new AWS.S3({
  endpoint: "https://s3.cloudfly.vn", 
  accessKeyId: process.env.S3_ACCESS_KEY,
  secretAccessKey: process.env.S3_SECRET_KEY,
  s3ForcePathStyle: true, 
  signatureVersion: "v4",
});

export async function uploadFile(filePath: string, bucketName: string, key: string) {
  const fileContent = fs.createReadStream(filePath);

  const params = {
    Bucket: bucketName,
    Key: key, 
    Body: fileContent,
    ACL: "public-read", 
  };

  try {
    const data = await s3.upload(params).promise();
    console.log("Upload thành công:", data.Location);
    return data.Location; // URL public
  } catch (err) {
    console.error("Lỗi upload:", err);
    throw err;
  }
}

// uploadFile("test.png", "kien", "images/test.png");
