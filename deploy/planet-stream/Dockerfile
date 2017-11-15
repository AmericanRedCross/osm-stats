FROM node:6

ARG NODE_ENV=production
ENV NPM_CONFIG_LOGLEVEL warn

WORKDIR /opt/app/

COPY package.json /opt/app/

RUN npm install \
  && rm -rf /root/.npm

COPY . /opt/app

ENV PATH /opt/app/node_modules/.bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

CMD ["node", "index.js"]
