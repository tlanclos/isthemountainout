FROM node:16

ADD . /App
ADD ./isthemountainout-credentials.json /App/.
WORKDIR /App

RUN npm --prefix frontend install
RUN npm --prefix frontend run build

RUN npm install
RUN npm run build

CMD ["npm", "run", "start"]
