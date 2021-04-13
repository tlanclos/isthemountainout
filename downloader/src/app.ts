import axios from 'axios';
import fs from "fs";
import cron from "node-cron";
import express from "express";
import bodyParser from "body-parser";
import moment from "moment";
import path from "path";

const app = express();

app.use(bodyParser.json());

cron.schedule("0 0,15,30,45 * * * *", async () => {
  const uri = "http://backend.roundshot.com/cams/241/original";
  await downloadOne(uri, { outputDir: "TrainingData" });
});

app.post("/download-prior", async (request, response) => {
  for (
    let date = moment(request.body.start);
    date < moment(request.body.end);
    date = date.add(1, "days")
  ) {
    for (
      let datetime = date.clone();
      datetime < date.clone().add(19, "hours");
      datetime = datetime.add(60, "minutes")
    ) {
      await downloadOnePrior(datetime, { outputDir: "TrainingDataPrior" });
    }
  }
  response.send("complete");
});

app.listen(3128);

async function downloadOnePrior(
  datetime: moment.Moment,
  options: Options
): Promise<void> {
  const uri = `https://ismtrainierout.com/timelapse/${datetime.format(
    "YYYY_MM_DD"
  )}/${datetime.format("HHmm")}.jpg`;
  const filename = `MountRainier_${datetime.format("YYYY-MM-DDTHHmmss")}.jpg`;

  await fs.promises.mkdir(options.outputDir, { recursive: true });

  const fullFilename = path.join(options.outputDir, filename);
  // check if file exists and if it does not, then download it
  return fs.promises.access(fullFilename, fs.constants.F_OK).catch(async () => {
    console.log(`Downloading ${uri} -> ${fullFilename}`);

    try {
      const response = await axios.get(uri, {responseType: 'stream'});
      if (response.status !== 200) {
        console.log(`Error receiving ${fullFilename}`);
        return;
      }
      response.data.pipe(fs.createWriteStream(fullFilename)).on('close', () => {
        console.log(`Saved Prior ${fullFilename}`);
      });
    } catch (e: unknown) {
      console.log(`Error receiving ${fullFilename}: ${e}`);
    }
  });
}

async function downloadOne(uri: string, options: Options): Promise<void> {
  const now = moment();
  const filename = `MountRainier_${now.format("YYYY-MM-DDTHHmmss")}.jpg`;
  const fullFilename = `${options.outputDir}/${filename}`;

  return fs.promises.mkdir(options.outputDir, { recursive: true }).then(() => {
    return new Promise((resolve) => {
      axios.get(uri)
        .then(response => {
          return response.data
            .pipe(fs.createWriteStream(fullFilename))
            .on("close", () => {
              console.log(`Saved ${fullFilename}`);
              resolve();
            });
        });
    });
  });
}

interface Options {
  outputDir: string;
}
