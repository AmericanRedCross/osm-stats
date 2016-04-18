FROM node:4.2

RUN curl -sSL https://github.com/AmericanRedCross/osm-stats-api/archive/0.31.tar.gz \
  | tar -v -C /usr/src -xz

WORKDIR /usr/src/osm-stats-api-0.31
RUN npm install

CMD ["npm", "start"]
