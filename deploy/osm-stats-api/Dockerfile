FROM node:4.2

RUN curl -sSL https://github.com/AmericanRedCross/osm-stats-api/archive/0.2.1.tar.gz \
  | tar -v -C /usr/src -xz

WORKDIR /usr/src/osm-stats-api-0.2.1
RUN npm install

CMD ["npm", "start"]