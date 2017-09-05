FROM node:6

ENV NPM_CONFIG_LOGLEVEL warn

WORKDIR /opt/app/

COPY package.json /opt/app/

RUN npm install \
  && rm -rf /root/.npm

COPY . /opt/app

CMD ["node", "index.js"]
