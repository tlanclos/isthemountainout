import request from "request";
import fs from "fs";
import cron from "node-cron";
import express from "express";
import moment from "moment";

const app = express();

cron.schedule("0 0,15,30,45 * * * *", () => {
  const uri = "http://backend.roundshot.com/cams/241/original";
  downloadOne(uri, { outputDir: "TrainingData" });
});

app.listen(3128);

function downloadOne(uri: string, options: Options) {
  const now = moment();
  const filename = `MountRainier_${now.format("YYYY-MM-DDTHHmmss")}.jpg`;
  const fullFilename = `${options.outputDir}/${filename}`;

  fs.mkdir(options.outputDir, { recursive: true }, (err) => {
    if (err) {
      throw err;
    } else {
      request(uri)
        .pipe(fs.createWriteStream(fullFilename))
        .on("close", () => {
          console.log(`Saved ${fullFilename}`);
        });
    }
  });
}

interface Options {
  outputDir: string;
}
